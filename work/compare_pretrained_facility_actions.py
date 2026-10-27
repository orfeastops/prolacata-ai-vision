import os,json,pathlib,subprocess,random
os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
import numpy as np
import torch
from transformers import AutoModelForVideoClassification
from transformers.image_utils import IMAGENET_DEFAULT_MEAN,IMAGENET_DEFAULT_STD
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score,classification_report,confusion_matrix
import joblib
random.seed(42);np.random.seed(42);torch.manual_seed(42)
assert torch.cuda.is_available(),'Enable the free GPU accelerator.'
OUT=pathlib.Path('/kaggle/working/pretrained_action_comparison');OUT.mkdir(exist_ok=True)
TMP=pathlib.Path('/kaggle/temp/pretrained_action_comparison');TMP.mkdir(parents=True,exist_ok=True)
labels=['whole_block_transfer','separator_handling','other_or_idle'];class_ids={v:i for i,v in enumerate(labels)}
groups={s:{r['source_sha256'] for r in EXAMPLES if r['split']==s} for s in ('train','val','test')}
assert not(groups['train']&groups['val'] or groups['train']&groups['test'] or groups['val']&groups['test'])
assert all(r['date']=='2026-10-03' for r in EXAMPLES if r['split']=='test')
roots=list(pathlib.Path('/kaggle/input').rglob('bundle_manifest.json'))
assert len(roots)==1,'Attach the original private facility camera dataset.'
ROOT=roots[0].parent
(OUT/'examples.json').write_text(json.dumps(EXAMPLES,indent=2))
(OUT/'dataset_review.json').write_text(json.dumps(DATASET_REVIEW,indent=2))
print('REVIEWED CLIPS',len(EXAMPLES),DATASET_REVIEW['counts'],flush=True)
indexed={};arrays=[];decode_review=[]
for i,r in enumerate(EXAMPLES):
    sha=r['source_sha256']
    if sha not in indexed:
        indexed[sha]=TMP/(sha+'.mp4')
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(ROOT/r['media_path']),
            '-map','0:v:0','-an','-c:v','copy',str(indexed[sha])],capture_output=True,check=True,timeout=180)
    start=r['source_start_s'];duration=r['source_end_s']-start
    focus={'filling_left':(0,80,420,360),'filling_right':(180,0,640,330)}.get(r['worker_track'],(0,0,640,360))
    x1,y1,x2,y2=focus
    vf=f'crop=640:360:800:720,crop={x2-x1}:{y2-y1}:{x1}:{y1},fps={16/duration:.9f},scale=256:256:force_original_aspect_ratio=decrease,pad=256:256:(ow-iw)/2:(oh-ih)/2'
    result=subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-ss',str(start),'-i',str(indexed[sha]),
        '-t',str(duration),'-vf',vf,'-frames:v','16','-threads','2','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],
        capture_output=True,check=True,timeout=120)
    assert len(result.stdout)%(256*256*3)==0,'Malformed decoder output'
    frames=np.frombuffer(result.stdout,dtype=np.uint8).reshape(-1,256,256,3).copy()
    assert len(frames)>0,f'No frames for {r["example_id"]}'
    actual=len(frames)
    if actual<16:frames=np.concatenate([frames,np.repeat(frames[-1:],16-actual,axis=0)])
    arrays.append(frames[:16]);decode_review.append({'example_id':r['example_id'],'decoded_frames':actual,'tail_padding':max(0,16-actual)})
    if i%10==0:print('SUPERVISION CLIPS',i+1,'/',len(EXAMPLES),flush=True)
(OUT/'decode_review.json').write_text(json.dumps(decode_review,indent=2))

MODEL_ID='facebook/vjepa2-vitl-fpc16-256-ssv2'
print('DOWNLOADING OFFICIAL MIT MODEL',MODEL_ID,flush=True)
model=AutoModelForVideoClassification.from_pretrained(MODEL_ID,torch_dtype=torch.float16,attn_implementation='sdpa').cuda().eval()
for p in model.parameters():p.requires_grad=False
mean=torch.tensor(IMAGENET_DEFAULT_MEAN).view(1,3,1,1)
std=torch.tensor(IMAGENET_DEFAULT_STD).view(1,3,1,1)
features=[]
with torch.inference_mode():
    for i,frames in enumerate(arrays):
        x=torch.from_numpy(frames).permute(0,3,1,2).float()/255
        x=((x-mean)/std).unsqueeze(0).to('cuda',dtype=torch.float16)
        z=model.vjepa2(pixel_values_videos=x,skip_predictor=True).last_hidden_state
        pooled=model.pooler(z)
        assert pooled.ndim==2 and pooled.shape[0]==1,pooled.shape
        features.append(pooled[0].float().cpu().numpy())
        if i%10==0:print('PRETRAINED FEATURES',i+1,'/',len(arrays),flush=True)
features=np.stack(features)
np.save(OUT/'features.npy',features)
y=np.array([class_ids[r['label']] for r in EXAMPLES])
ids={s:np.array([i for i,r in enumerate(EXAMPLES) if r['split']==s]) for s in groups}
trials=[];best=None
# Select regularization on validation only; keep the same held-out sources.
for c in [.001,.01,.1,1.,10.,100.]:
    classifier=make_pipeline(StandardScaler(),LogisticRegression(C=c,class_weight='balanced',max_iter=3000,random_state=42))
    classifier.fit(features[ids['train']],y[ids['train']])
    pred=classifier.predict(features[ids['val']])
    f=float(f1_score(y[ids['val']],pred,labels=[0,1,2],average='macro',zero_division=0))
    trials.append({'C':c,'validation_macro_f1':f})
    if best is None or f>best[0]:best=(f,c,classifier)
classifier=best[2]
testpred=classifier.predict(features[ids['test']])
testscore=float(f1_score(y[ids['test']],testpred,labels=[0,1,2],average='macro',zero_division=0))
report={'model_id':MODEL_ID,'license':'MIT','feature_extractor_frozen':True,'preprocessing':'same worker crops, aspect-preserving 256 square padding, 16 uniform frames, ImageNet default mean/std',
 'selection':'Regularization selected by validation macro F1 only; no refit on validation.',
 'validation_trials':trials,'selected_C':best[1],'validation_macro_f1':best[0],'test_macro_f1':testscore,
 'test_confusion_matrix_true_rows':confusion_matrix(y[ids['test']],testpred,labels=[0,1,2]).tolist(),
 'test_classification_report':classification_report(y[ids['test']],testpred,labels=[0,1,2],target_names=labels,zero_division=0,output_dict=True),
 'prior_scratch_videomae_pilot':{'run_version':361524639,'selected_validation_macro_f1':0.4296296296296296,'selected_test_macro_f1':0.4444444444444445},
 'limitations':['Only 76 assistant-reviewed clips; no independent expert verification.','Validation has one source; test 18 clips, including 5 whole-block transfers.','Trimmed action classification is not block-counting accuracy.','Quantity is never inferred from the gesture label or a standard tank capacity.','Continuous video detection, camera association and end-to-end tank counts remain unevaluated.'],
 'production_counter_ready':False}
(OUT/'comparison_results.json').write_text(json.dumps(report,indent=2))
joblib.dump(classifier,OUT/'facility_action_head.joblib')
predictions=[{'example_id':EXAMPLES[int(i)]['example_id'],'true_label':labels[int(y[i])],'predicted_label':labels[int(p)]} for i,p in zip(ids['test'],testpred)]
(OUT/'test_predictions.json').write_text(json.dumps(predictions,indent=2))
(OUT/'inference_contract.json').write_text(json.dumps({'purpose':'offline action candidate review only','model_id':MODEL_ID,'quantity_prediction':False,'automatic_tank_counts':False,'continuous_state':'External persistent tank and hand tracking required; windows never reset counts.'},indent=2))
print('COMPARISON COMPLETE',json.dumps(report),flush=True)
