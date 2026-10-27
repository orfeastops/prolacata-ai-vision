"""Private Kaggle pilot: reviewed action proposals, not an automatic counter.

EXAMPLES and DATASET_REVIEW are embedded by the notebook builder.
"""
import os,json,pathlib,subprocess,random,time,copy,collections,zipfile
os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader,Dataset
from transformers import VideoMAEForPreTraining
from transformers.image_utils import IMAGENET_DEFAULT_MEAN,IMAGENET_DEFAULT_STD
from sklearn.metrics import classification_report,confusion_matrix,f1_score

SEED=42;random.seed(SEED);np.random.seed(SEED);torch.manual_seed(SEED)
assert torch.cuda.is_available(),'Enable GPU before supervised training.'
OUT=pathlib.Path('/kaggle/working/reviewed_action_pilot');OUT.mkdir(exist_ok=True)
TMP=pathlib.Path('/kaggle/temp/reviewed_action_pilot');TMP.mkdir(parents=True,exist_ok=True)
labels=['whole_block_transfer','separator_handling','other_or_idle'];class_ids={v:i for i,v in enumerate(labels)}
groups={s:{r['source_sha256'] for r in EXAMPLES if r['split']==s} for s in ('train','val','test')}
assert not(groups['train']&groups['val'] or groups['train']&groups['test'] or groups['val']&groups['test'])
assert all(r['date']=='2026-10-03' for r in EXAMPLES if r['split']=='test')
(OUT/'dataset_review.json').write_text(json.dumps(DATASET_REVIEW,indent=2))
(OUT/'examples.json').write_text(json.dumps(EXAMPLES,indent=2))
roots=list(pathlib.Path('/kaggle/input').rglob('bundle_manifest.json'))
assert len(roots)==1,'Attach the original private facility dataset.'
ROOT=roots[0].parent
checkpoints=[p.parent for p in pathlib.Path('/kaggle/input').rglob('config.json') if p.parent.name=='latest_model']
assert len(checkpoints)==1,'Attach output of completed facility temporal video pretraining, version 361412417.'
PRETRAINED=checkpoints[0]
print('PRETRAINED',str(PRETRAINED),'LABELS',len(EXAMPLES),'SPLITS',DATASET_REVIEW['counts'],flush=True)

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
    vf=f'crop=640:360:800:720,crop={x2-x1}:{y2-y1}:{x1}:{y1},fps={16/duration:.9f},scale=224:224:force_original_aspect_ratio=decrease,pad=224:224:(ow-iw)/2:(oh-ih)/2'
    result=subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-ss',str(start),'-i',str(indexed[sha]),
        '-t',str(duration),'-vf',vf,'-frames:v','16','-threads','2','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],
        capture_output=True,check=True,timeout=120)
    assert len(result.stdout)%(224*224*3)==0,'Malformed decoder output'
    frames=np.frombuffer(result.stdout,dtype=np.uint8).reshape(-1,224,224,3).copy()
    assert len(frames)>0,f'No frames for {r["example_id"]}'
    actual=len(frames)
    if actual<16:frames=np.concatenate([frames,np.repeat(frames[-1:],16-actual,axis=0)])
    arrays.append(frames[:16]);decode_review.append({'example_id':r['example_id'],'decoded_frames':actual,'tail_padding':max(0,16-actual)})
    if i%10==0:print('SUPERVISION CLIPS',i+1,'/',len(EXAMPLES),flush=True)
(OUT/'decode_review.json').write_text(json.dumps(decode_review,indent=2))
mean=torch.tensor(IMAGENET_DEFAULT_MEAN).view(1,3,1,1)
std=torch.tensor(IMAGENET_DEFAULT_STD).view(1,3,1,1)

class Clips(Dataset):
    def __init__(self,split,augment=False):self.ids=[i for i,r in enumerate(EXAMPLES) if r['split']==split];self.augment=augment
    def __len__(self):return len(self.ids)
    def __getitem__(self,j):
        i=self.ids[j];x=torch.from_numpy(arrays[i]).permute(0,3,1,2).float()/255
        if self.augment:x=(x*random.uniform(.9,1.1)).clamp(0,1)
        return (x-mean)/std,class_ids[EXAMPLES[i]['label']],i

pretrainer=VideoMAEForPreTraining.from_pretrained(PRETRAINED)
encoder=pretrainer.videomae;del pretrainer
encoder=encoder.cuda().eval()
for p in encoder.parameters():p.requires_grad=False
features=[]
with torch.inference_mode():
    for i in range(len(EXAMPLES)):
        x=torch.from_numpy(arrays[i]).permute(0,3,1,2).float()/255;x=((x-mean)/std).unsqueeze(0).cuda()
        with torch.autocast('cuda',dtype=torch.float16):z=encoder(pixel_values=x).last_hidden_state.mean(1)
        features.append(z[0].float().cpu())
        if i%10==0:print('FROZEN FEATURES',i+1,'/',len(EXAMPLES),flush=True)
features=torch.stack(features).cuda();targets=torch.tensor([class_ids[r['label']] for r in EXAMPLES],device='cuda')
ids={s:torch.tensor([i for i,r in enumerate(EXAMPLES) if r['split']==s],device='cuda') for s in groups}

def score(y,probs):
    y=np.asarray(y);pred=np.asarray(probs).argmax(1)
    return {'macro_f1':float(f1_score(y,pred,labels=[0,1,2],average='macro',zero_division=0)),
      'confusion_matrix_true_rows_pred_columns':confusion_matrix(y,pred,labels=[0,1,2]).tolist(),
      'classification_report':classification_report(y,pred,labels=[0,1,2],target_names=labels,zero_division=0,output_dict=True)}

# A frozen-feature baseline tests whether fine-tuning actually helps on reserved
# labels. Quantity and daily production accuracy are deliberately not inferred.
head=nn.Sequential(nn.LayerNorm(encoder.config.hidden_size),nn.Linear(encoder.config.hidden_size,3)).cuda()
opt=torch.optim.AdamW(head.parameters(),lr=1e-3,weight_decay=.05)
weights=torch.bincount(targets[ids['train']],minlength=3).float().clamp_min(1)
weights=weights.sum()/(3*weights)
criterion=nn.CrossEntropyLoss(weight=weights)
best=-1;best_head=None;bad=0
for epoch in range(250):
    head.train();opt.zero_grad();loss=criterion(head(features[ids['train']]),targets[ids['train']]);loss.backward();opt.step()
    head.eval()
    with torch.no_grad():vp=head(features[ids['val']]).softmax(-1).cpu().numpy()
    metric=score(targets[ids['val']].cpu().numpy(),vp)['macro_f1']
    if metric>best+1e-6:best=metric;best_head=copy.deepcopy(head.state_dict());bad=0
    else:bad+=1
    if bad>=35:break
head.load_state_dict(best_head);head.eval()
with torch.no_grad():baseline={s:score(targets[ids[s]].cpu().numpy(),head(features[ids[s]]).softmax(-1).cpu().numpy()) for s in ['val','test']}
torch.save(best_head,OUT/'frozen_feature_head.pt')
(OUT/'frozen_baseline_metrics.json').write_text(json.dumps(baseline,indent=2))
print('FROZEN BASELINE',json.dumps({s:v['macro_f1'] for s,v in baseline.items()}),flush=True)

class ActionModel(nn.Module):
    def __init__(self,encoder,head):super().__init__();self.encoder=encoder;self.head=head
    def forward(self,x):return self.head(self.encoder(pixel_values=x).last_hidden_state.mean(1))
for layer in encoder.encoder.layer[-2:]:
    for p in layer.parameters():p.requires_grad=True
if encoder.layernorm is not None:
    for p in encoder.layernorm.parameters():p.requires_grad=True
for p in head.parameters():p.requires_grad=True
model=ActionModel(encoder,head).cuda();ngpu=torch.cuda.device_count()
runner=nn.DataParallel(model) if ngpu>1 else model
optimizer=torch.optim.AdamW([{'params':[p for p in encoder.parameters() if p.requires_grad],'lr':1e-5},
 {'params':head.parameters(),'lr':3e-4}],weight_decay=.05)
scaler=torch.amp.GradScaler('cuda')
loaders={s:DataLoader(Clips(s,augment=s=='train'),batch_size=2*ngpu if s=='train' else ngpu,
  shuffle=s=='train',num_workers=0,pin_memory=True) for s in ['train','val','test']}
def evaluate(split):
    model.eval();truth=[];prob=[];records=[]
    with torch.inference_mode():
        for x,y,ix in loaders[split]:
            with torch.autocast('cuda',dtype=torch.float16):p=runner(x.cuda(non_blocking=True)).float().softmax(-1)
            truth.extend(y.tolist());prob.extend(p.cpu().tolist())
            for i,probs in zip(ix.tolist(),p.cpu().tolist()):records.append({'example_id':EXAMPLES[i]['example_id'],
              'true_label':EXAMPLES[i]['label'],'probabilities':dict(zip(labels,probs)),'automatic_block_increment':None})
    return score(truth,prob),records

best_metric=-1;best_epoch=0;bad=0;history=[];started=time.time()
for epoch in range(30):
    model.train();total=0;n=0
    for x,y,_ in loaders['train']:
        optimizer.zero_grad(set_to_none=True)
        with torch.autocast('cuda',dtype=torch.float16):loss=criterion(runner(x.cuda(non_blocking=True)),y.cuda(non_blocking=True))
        assert torch.isfinite(loss)
        scaler.scale(loss).backward();scaler.unscale_(optimizer)
        nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad],1.)
        scaler.step(optimizer);scaler.update();total+=float(loss.detach())*len(y);n+=len(y)
    val,_=evaluate('val');metric=val['macro_f1']
    row={'epoch':epoch+1,'train_loss':total/n,'val_macro_f1':metric,'elapsed_s':round(time.time()-started,1)}
    history.append(row);(OUT/'training_history.json').write_text(json.dumps(history,indent=2));print('SUPERVISED TRAIN',json.dumps(row),flush=True)
    if metric>best_metric+1e-6:
        best_metric=metric;best_epoch=epoch+1;bad=0
        encoder.save_pretrained(OUT/'finetuned_encoder',safe_serialization=True);torch.save(head.state_dict(),OUT/'finetuned_head.pt')
    else:bad+=1
    if bad>=7:break
# Reload selected parameters. Test labels have never been used for fitting or
# selecting the epoch/model. Small test counts must accompany any reported score.
encoder.load_state_dict(type(encoder).from_pretrained(OUT/'finetuned_encoder').state_dict())
head.load_state_dict(torch.load(OUT/'finetuned_head.pt',weights_only=True))
val,_=evaluate('val');test,predictions=evaluate('test')
chosen='finetuned' if val['macro_f1']>baseline['val']['macro_f1'] else 'frozen_feature_baseline'
result={'stage':'reviewed_action_proposal_pilot','completed':True,'best_finetune_epoch':best_epoch,
 'selected_by_validation_only':chosen,'labels':labels,'dataset':DATASET_REVIEW,
 'frozen_baseline':baseline,'finetuned':{'val':val,'test':test},
 'production_ready':False,'block_quantity_head_trained':False,'automatic_block_counting_enabled':False,
 'clock_alignment_verified':False,'tank_tracking_trained':False,
 'interpretation':'Scores concern pre-trimmed action clips, not block counts or daily production accuracy.'}
(OUT/'pilot_results.json').write_text(json.dumps(result,indent=2));(OUT/'test_predictions.json').write_text(json.dumps(predictions,indent=2))
(OUT/'inference_contract.json').write_text(json.dumps({'labels':labels,'focus_crops':{'filling_left':[0,80,420,360],
 'filling_right':[180,0,640,330]},'original_camera11_crop':[800,720,1440,1080],
 'num_frames':16,'normalization_mean':IMAGENET_DEFAULT_MEAN,'normalization_std':IMAGENET_DEFAULT_STD,
 'role':'Propose candidate actions for review. Never multiply actions by an assumed block quantity.',
 'count_requires':['observed or independently validated block quantity','release into filling tank','persistent tank identity','duplicate-event suppression'],
 'no_fixed_tank_total':True,'production_counting_enabled':False},indent=2))
print('SUPERVISED PILOT SAVED',json.dumps({'chosen':chosen,'finetuned_test_macro_f1':test['macro_f1'],
 'block_counting_ready':False}),flush=True)
