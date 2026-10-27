"""Kaggle inference only: frozen V-JEPA2 features and the existing facility head.

Untrimmed windows are review candidates, never cheese increments or tank totals.
No fit, optimizer, model selection, or threshold tuning is performed on test data.
"""
import os,json,pathlib,subprocess,hashlib,time,collections,csv
os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
import numpy as np
import torch
from torch import nn
import joblib
from PIL import Image,ImageDraw
from transformers import AutoModelForVideoClassification
from transformers.image_utils import IMAGENET_DEFAULT_MEAN,IMAGENET_DEFAULT_STD

assert torch.cuda.is_available(),'Enable GPU T4 x2.'
OUT=pathlib.Path('/kaggle/working/unseen_camera11_test');OUT.mkdir(exist_ok=True)
TMP=pathlib.Path('/kaggle/temp/unseen_camera11_test');TMP.mkdir(parents=True,exist_ok=True)
manifests=list(pathlib.Path('/kaggle/input').rglob('unseen_test_manifest.json'))
assert len(manifests)==1,'Attach private September26 test dataset.'
ROOT=manifests[0].parent
rows=json.loads(manifests[0].read_text())
assert len(rows)==308 and not any(r['already_in_original_dataset'] for r in rows)
sources=sorted(json.loads((ROOT/'video_index.json').read_text()),key=lambda r:r['basename'])
heads=list(pathlib.Path('/kaggle/input').rglob('facility_action_head.joblib'))
assert len(heads)==1,'Attach completed reviewed-hand-action-training version 361529122 output.'
head=joblib.load(heads[0])
head_sha=hashlib.sha256(heads[0].read_bytes()).hexdigest()
labels=['whole_block_transfer','separator_handling','other_or_idle']
assert list(head.classes_)==[0,1,2]
MODEL_ID='facebook/vjepa2-vitl-fpc16-256-ssv2'
model=AutoModelForVideoClassification.from_pretrained(MODEL_ID,torch_dtype=torch.float16,attn_implementation='sdpa').cuda().eval()
for p in model.parameters():p.requires_grad=False
class Features(nn.Module):
    def __init__(self,m):super().__init__();self.m=m
    def forward(self,x):return self.m.pooler(self.m.vjepa2(pixel_values_videos=x,skip_predictor=True).last_hidden_state)
extractor=Features(model).eval()
ngpu=torch.cuda.device_count()
runner=nn.DataParallel(extractor) if ngpu>1 else extractor
mean=torch.tensor(IMAGENET_DEFAULT_MEAN).view(1,1,3,1,1).cuda()
std=torch.tensor(IMAGENET_DEFAULT_STD).view(1,1,3,1,1).cuda()
WINDOW=4.;STRIDE=2.;FPS=4
contract={'test_only':True,'inference_only':True,'training_on_test':False,'model_id':MODEL_ID,
 'head_sha256':head_sha,'head_source_version':361529122,'window_s':WINDOW,'stride_s':STRIDE,
 'frames_per_window':16,'workers':['filling_left','filling_right'],
 'threshold_tuned_on_test':False,'quantity_prediction':False,'tank_counts':None,
 'interpretation':'Window classification on untrimmed video. Neighboring windows may describe the same movement. Never sum windows as actions or multiply by two.',
 'coverage':'All supplied videos processed independently in encoded timeline; file gaps/overlaps and camera overlay clocks are not yet resolved.',
 'wall_clock_verified':False,'accuracy':None,'manual_ground_truth_complete':False}
(OUT/'inference_contract.json').write_text(json.dumps(contract,indent=2))
predfile=OUT/'window_predictions.jsonl'
audit=[];failures=[];counts=collections.Counter();total=0;started=time.time();review_candidates=[]
focuses={'filling_left':(0,80,420,360),'filling_right':(180,0,640,330)}
def infer(batch):
    x=torch.from_numpy(np.stack(batch)).permute(0,1,4,2,3).to('cuda',dtype=torch.float16)/255
    with torch.inference_mode():features=runner((x-mean)/std).float().cpu().numpy()
    return head.predict_proba(features)
with predfile.open('w') as stream:
  for si,r in enumerate(sources):
    input_path=ROOT/r['media_path'];indexed=TMP/'indexed.mp4'
    try:
      subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(input_path),'-map','0:v:0','-an','-c:v','copy',str(indexed)],capture_output=True,check=True,timeout=180)
      # Verify upload contents while processing, without exposing filenames as labels.
      assert hashlib.file_digest(input_path.open('rb'),'sha256').hexdigest()==r['sha256']
      for worker,(x1,y1,x2,y2) in focuses.items():
        raw=TMP/(worker+'.rgb')
        vf=f'crop=640:360:800:720,crop={x2-x1}:{y2-y1}:{x1}:{y1},fps=4,scale=256:256:force_original_aspect_ratio=decrease,pad=256:256:(ow-iw)/2:(oh-ih)/2'
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(indexed),'-vf',vf,'-threads','2','-an','-f','rawvideo','-pix_fmt','rgb24',str(raw)],capture_output=True,check=True,timeout=900)
        n=raw.stat().st_size//(256*256*3);assert n>0
        frames=np.memmap(raw,dtype=np.uint8,mode='r',shape=(n,256,256,3))
        starts=list(range(0,max(1,n-15),int(STRIDE*FPS)))
        if n>=16 and (n-16) not in starts:starts.append(n-16)
        pending=[];metadata=[];saved_for_worker=0
        for wi,fi in enumerate(starts):
          clip=np.array(frames[fi:min(fi+16,n)])
          padded=max(0,16-len(clip))
          if padded:clip=np.concatenate([clip,np.repeat(clip[-1:],padded,axis=0)])
          pending.append(clip);metadata.append((fi,padded))
          if len(pending)==2*ngpu or wi==len(starts)-1:
            probs=infer(pending)
            for video,(start,pad),p in zip(pending,metadata,probs):
              best=int(p.argmax());confidence=float(p[best]);total+=1;counts[labels[best]]+=1
              row={'window_id':r['sha256'][:16]+f'_{worker}_{start:07d}',
               'source_sha256':r['sha256'],'basename':r['basename'],'worker':worker,
               'source_start_s':start/FPS,'source_end_s':min(n/FPS,(start+16)/FPS),
               'tail_padding_frames':pad,'predicted_class':labels[best],
               'probabilities':{label:float(p[j]) for j,label in enumerate(labels)},
               'confidence_not_calibrated':confidence,'block_increment':None,'camera_clock_verified':False}
              stream.write(json.dumps(row)+'\n')
              # Save distributed review examples including high-confidence and
              # uncertain windows. No truth labels are inferred from predictions.
              if start==0 or best!=2 or confidence<.6:
                if saved_for_worker<2:
                  saved_for_worker+=1
                  reviewdir=OUT/'review_windows';reviewdir.mkdir(exist_ok=True)
                  sheet=Image.new('RGB',(1024,1080),(15,15,15));draw=ImageDraw.Draw(sheet)
                  draw.text((6,6),f'{row["window_id"]} | {labels[best]} {confidence:.3f} | NOT a block count',fill='white')
                  for j,img in enumerate(video):sheet.paste(Image.fromarray(img),((j%4)*256,45+(j//4)*256))
                  rel='review_windows/'+row['window_id']+'.jpg';sheet.save(OUT/rel,quality=85)
                  review_candidates.append({**row,'contact_sheet':rel,'manual_label':None})
            pending=[];metadata=[]
        audit.append({'sha256':r['sha256'],'worker':worker,'decoded_frames_4fps':n,'windows':len(starts)})
        del frames;raw.unlink()
      stream.flush()
    except Exception as e:
      failures.append({'sha256':r['sha256'],'error':str(e)})
      (OUT/'failures.json').write_text(json.dumps(failures,indent=2))
    progress={'completed_sources':si+1,'total_sources':len(sources),'windows':total,'elapsed_s':round(time.time()-started,1),'failed_sources':len(failures)}
    (OUT/'progress.json').write_text(json.dumps(progress,indent=2))
    print('UNSEEN TEST PROGRESS',json.dumps(progress),flush=True)
(OUT/'decode_audit.json').write_text(json.dumps(audit,indent=2))
(OUT/'review_manifest.json').write_text(json.dumps(review_candidates,indent=2))
result={**contract,'completed':True,'sources_supplied':len(sources),'sources_failed':len(failures),
 'windows_classified':total,'predicted_window_class_histogram_not_event_counts':dict(counts),
 'runtime_s':round(time.time()-started,1),'review_sheets':len(review_candidates),
 'next_step':'Independent manual event/release/quantity annotations and comparison; no accuracy or tank total yet.'}
(OUT/'test_results.json').write_text(json.dumps(result,indent=2))
print('UNSEEN TEST COMPLETE',json.dumps(result),flush=True)
