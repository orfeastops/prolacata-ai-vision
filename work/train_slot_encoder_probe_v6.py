"""Second fixed appearance probe: generic frozen YOLO features + trained head.

Uses exactly the same manually cropped slots and source split as the HOG probe.
The first probe's results motivated comparing representations; this is therefore
a development comparison, not a new independent test or a deployable counter.
"""
import os
os.environ['YOLO_AUTOINSTALL']='false';os.environ['YOLO_OFFLINE']='true'
os.environ['OMP_NUM_THREADS']='4'
import json,time
import cv2,numpy as np,torch
from torch.nn import functional as F
from ultralytics import YOLO
from prepare_slot_probe_v6 import ROOT,OUT as DATA
from train_slot_probe_v6 import digest,save

OUT=DATA/'generic_encoder_probe'
CONFIG=dict(method='Frozen generic YOLO26n multi-scale features + L2 logistic head',
    input_size=224,pool_sizes=[[2,2],[2,2],[2,2]],steps=500,learning_rate=.03,l2=.01,
    score_minimum=.8,normalization_floor=.03,batch=8,seed=291026,
    backbone_trainable=False,no_hyperparameter_search=True)

def main():
    OUT.mkdir(exist_ok=True)
    if (OUT/'training_complete.json').exists():raise RuntimeError('Frozen encoder probe exists')
    torch.set_num_threads(4);cv2.setNumThreads(2)
    manifest=json.loads((DATA/'manifest.json').read_text());rows=manifest['rows']
    train=[r for r in rows if r['split']=='train' and r['label'] is not None]
    test=[r for r in rows if r['split']=='development_test']
    assert not {r['source_sha256'] for r in train}&{r['source_sha256'] for r in test}
    encoder_path=ROOT/'outputs/feta_training/yolo26n.pt'
    save(OUT/'frozen_before_training.json',dict(config=CONFIG,manifest_sha256=digest(DATA/'manifest.json'),
        code_sha256=digest(__file__),encoder_sha256=digest(encoder_path),created_unix=time.time(),
        manual_localization=True,independent_acceptance=False,september_used=False))
    encoder=YOLO(str(encoder_path)).model.eval()
    for p in encoder.parameters():p.requires_grad=False
    captured=[]
    def hook(module,args):
        captured.clear()
        captured.extend(F.adaptive_avg_pool2d(x,tuple(pool)).flatten(1)
                        for x,pool in zip(args[0],CONFIG['pool_sizes']))
    handle=encoder.model[-1].register_forward_pre_hook(hook)
    inputs=[dict(id=r['id'],patch=r['patch']) for r in train+test]
    features=[];start=time.time()
    for i in range(0,len(inputs),CONFIG['batch']):
        images=[]
        for r in inputs[i:i+CONFIG['batch']]:
            im=cv2.imread(r['patch']);im=cv2.cvtColor(im,cv2.COLOR_BGR2RGB)
            im=cv2.resize(im,(192,224),interpolation=cv2.INTER_LINEAR)
            im=cv2.copyMakeBorder(im,0,0,16,16,cv2.BORDER_CONSTANT,value=(114,114,114))
            images.append(im)
        x=torch.from_numpy(np.stack(images)).permute(0,3,1,2).float()/255.
        with torch.inference_mode():
            encoder(x);features.append(torch.cat(captured,dim=1).numpy())
        print('features',min(i+len(images),len(inputs)),'/',len(inputs),flush=True)
    handle.remove();z=np.concatenate(features)
    np.savez_compressed(OUT/'features.npz',features=z,ids=np.array([r['id'] for r in inputs]))
    x=z[:len(train)];y=np.array([r['label'] for r in train])
    mean=x.mean(axis=0);std=np.maximum(x.std(axis=0),CONFIG['normalization_floor'])
    train_x=np.column_stack([(x-mean)/std,np.ones(len(x))]).astype(np.float64)
    weights=np.zeros(train_x.shape[1]);moment=np.zeros_like(weights);variance=np.zeros_like(weights)
    sample_weight=np.array([len(y)/(2*sum(y==v)) for v in y]);losses=[]
    for step in range(1,CONFIG['steps']+1):
        p=1/(1+np.exp(-np.clip(train_x@weights,-40,40)))
        penalty=CONFIG['l2']*weights;penalty[-1]=0
        gradient=train_x.T@((p-y)*sample_weight)/len(y)+penalty
        moment=.9*moment+.1*gradient;variance=.999*variance+.001*gradient**2
        weights-=CONFIG['learning_rate']*(moment/(1-.9**step))/(np.sqrt(variance/(1-.999**step))+1e-8)
        if step%50==0:losses.append(dict(step=step,training_log_loss=float(-np.mean(sample_weight*(y*np.log(p+1e-12)+(1-y)*np.log(1-p+1e-12))))))
    checkpoint=OUT/'slot_encoder_head.npz';np.savez_compressed(checkpoint,weights=weights,mean=mean,std=std)
    with np.load(checkpoint) as saved:
        logits=((z[len(train):]-saved['mean'])/saved['std'])@saved['weights'][:-1]+saved['weights'][-1]
    ps=1/(1+np.exp(-np.clip(logits,-40,40)));predictions=[]
    for r,p in zip(inputs[len(train):],ps):
        hard=int(p>=.5);share=float(max(p,1-p))
        predictions.append(dict(id=r['id'],hard_prediction=hard,
            predicted_class=hard if share>=CONFIG['score_minimum'] else None,
            maximum_class_score=share,cheese_score=float(p)))
    save(OUT/'predictions_frozen.json',dict(predictions=predictions,head_sha256=digest(checkpoint),encoder_sha256=digest(encoder_path)))
    refs={r['id']:r for r in test};scored=[];confusion=np.zeros((2,2),int)
    for p in predictions:
        r=refs[p['id']]
        if r['label'] is not None:confusion[r['label'],p['hard_prediction']]+=1
        scored.append(dict(**p,reference_class=r['label'],frame_id=r['frame_id'],patch=r['patch']))
    clear=[r for r in scored if r['reference_class'] is not None]
    confident=[r for r in clear if r['predicted_class'] is not None]
    unknown=[r for r in scored if r['reference_class'] is None]
    metrics=dict(clear_slots=len(clear),hard_predictions_correct=sum(r['hard_prediction']==r['reference_class'] for r in clear),
        confident_slots=len(confident),confident_correct=sum(r['predicted_class']==r['reference_class'] for r in confident),
        abstained_slots=len(clear)-len(confident),confusion_rows_truth_columns_hard_prediction=confusion.tolist(),
        obstructed_challenges=len(unknown),obstructed_confident_predictions=sum(r['predicted_class'] is not None for r in unknown))
    save(OUT/'results.json',dict(metrics=metrics,rows=scored,manual_localization=True,production_ready=False,
        independent_acceptance=False,interpretation='Development comparison against assistant labels on manually cropped positions, not a production count or full detector.'))
    save(OUT/'training_complete.json',dict(config=CONFIG,metrics=metrics,elapsed_s=time.time()-start,
        training_loss=losses,training_patch_count=len(train),training_source_files=1,test_source_files=1,
        encoder_sha256=digest(encoder_path),head_sha256=digest(checkpoint),backbone_updated=False,
        september_used=False,production_ready=False))
    print(json.dumps(metrics,indent=2),flush=True)
if __name__=='__main__':main()
