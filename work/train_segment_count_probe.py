"""Weak segment-count experiment. NOT object tracking or a production counter.

Uses local frozen YOLO image features, temporal differences, and count-sum loss.
No per-frame labels are fabricated. Leave-one-source-out evaluation has no
hyperparameter selection; all settings fixed before reading fold results.
"""
import os
os.environ['YOLO_AUTOINSTALL']='false'
import json, pathlib, hashlib, time
import cv2, numpy as np, torch
from ultralytics import YOLO

R=pathlib.Path(__file__).resolve().parents[1]
D=R/'outputs/facility_dataset/temporal_pipeline/sequence_annotation_v2/count_checkpoint_v2'
O=R/'outputs/facility_dataset/temporal_pipeline/placement_counter_v2/segment_count_probe'
O.mkdir(parents=True,exist_ok=True)
torch.set_num_threads(4);cv2.setNumThreads(2)
rows=json.loads((D/'segments.json').read_text())
assert all(r['date'] in ('2026-10-01','2026-10-21') for r in rows)
config=dict(sample_fps=4,projection_dim=64,epochs=600,learning_rate=.015,
    weight_decay=.01,seed=2401,validation='leave_one_original_source_out',
    supervision='segment totals only',no_hyperparameter_search=True,
    architecture='frozen generic image backbone + temporal differences + softplus linear count density',
    not_a_block_detector=True,production_ready=False)
(O/'config.json').write_text(json.dumps(config,indent=2))
weight=R/'outputs/feta_training/yolo26n.pt'
encoder_hash=hashlib.sha256(weight.read_bytes()).hexdigest()
model=YOLO(str(weight)).model.eval()
for p in model.parameters():p.requires_grad=False
captured=[]
def hook(_module,args):
    captured.clear()
    for z in args[0]:
        captured.append(torch.nn.functional.adaptive_avg_pool2d(z,(2,2)).flatten(1))
handle=model.model[-1].register_forward_pre_hook(hook)
projection=None;arrays=[];started=time.time()
for ri,row in enumerate(rows):
    path=pathlib.Path(row['media_path'])
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    cache=O/(row['segment_id']+'_features.npz')
    if cache.exists():
        saved=np.load(cache)
        if str(saved['video_hash'])==digest and str(saved['encoder_hash'])==encoder_hash:
            arrays.append(torch.from_numpy(saved['features']).float());continue
    cap=cv2.VideoCapture(str(path));fps=cap.get(cv2.CAP_PROP_FPS)
    assert fps==16
    features=[];batch=[];index=0
    def flush():
        global projection
        if not batch:return
        x=torch.from_numpy(np.stack(batch)).permute(0,3,1,2).float()/255
        with torch.inference_mode():
            model(x)
            z=torch.cat(captured,dim=1)
            if projection is None:
                generator=torch.Generator().manual_seed(config['seed'])
                projection=torch.randn(z.shape[1],config['projection_dim'],generator=generator)/np.sqrt(z.shape[1])
            features.extend((z@projection).cpu().numpy())
        batch.clear()
    while True:
        ok,bgr=cap.read()
        if not ok:break
        if index%4==0:
            # Original 640x360 crop, padded without changing aspect or size.
            rgb=cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB)
            batch.append(cv2.copyMakeBorder(rgb,12,12,0,0,cv2.BORDER_CONSTANT,value=(114,114,114)))
            if len(batch)==8:flush()
        index+=1
    flush();cap.release()
    x=np.stack(features).astype('float32')
    delta=np.zeros_like(x);delta[1:]=x[1:]-x[:-1]
    x=np.concatenate([x,delta,np.abs(delta)],axis=1)
    np.savez_compressed(cache,features=x,video_hash=digest,encoder_hash=encoder_hash)
    arrays.append(torch.from_numpy(x))
    print(f'Features {ri+1}/{len(rows)}: {row["segment_id"]} {len(x)} frames',flush=True)
    (O/'progress.json').write_text(json.dumps(dict(stage='features',completed=ri+1,total=len(rows),elapsed_s=time.time()-started)))
handle.remove();del model

def fit(train_indices):
    torch.manual_seed(config['seed'])
    joined=torch.cat([arrays[i] for i in train_indices])
    mean=joined.mean(0);scale=joined.std(0).clamp_min(.05)
    xx=torch.cat([(arrays[i]-mean)/scale for i in train_indices])
    group=torch.cat([torch.full((len(arrays[i]),),j,dtype=torch.long) for j,i in enumerate(train_indices)])
    duration=torch.cat([torch.full((len(arrays[i]),),rows[i]['duration_s']/len(arrays[i])) for i in train_indices])
    y=torch.tensor([rows[i]['confirmed_count'] for i in train_indices],dtype=torch.float)
    head=torch.nn.Linear(xx.shape[1],1)
    torch.nn.init.zeros_(head.weight);torch.nn.init.constant_(head.bias,-2.)
    optimizer=torch.optim.Adam(head.parameters(),lr=config['learning_rate'])
    for _ in range(config['epochs']):
        optimizer.zero_grad()
        rates=torch.nn.functional.softplus(head(xx).squeeze(1))
        totals=torch.zeros(len(train_indices)).scatter_add(0,group,rates*duration)
        loss=((totals-y).square()/(1+y)).mean()+config['weight_decay']*head.weight.square().sum()
        loss.backward();optimizer.step()
    return head.eval(),mean,scale

def predict(head,mean,scale,i):
    with torch.inference_mode():
        rates=torch.nn.functional.softplus(head((arrays[i]-mean)/scale).squeeze(1))
        return float(rates.mean()*rows[i]['duration_s'])

sources=sorted({r['source_sha256'] for r in rows});results=[]
for fold,source in enumerate(sources):
    train=[i for i,r in enumerate(rows) if r['source_sha256']!=source]
    test=[i for i,r in enumerate(rows) if r['source_sha256']==source]
    assert not ({rows[i]['source_sha256'] for i in train}&{rows[i]['source_sha256'] for i in test})
    head,mean,scale=fit(train)
    constant_rate=sum(rows[i]['confirmed_count'] for i in train)/sum(rows[i]['duration_s'] for i in train)
    for i in test:
        pred=predict(head,mean,scale,i);target=rows[i]['confirmed_count']
        results.append(dict(segment_id=rows[i]['segment_id'],source_sha256=source,
            confirmed_count=target,predicted_expected_count=pred,
            absolute_error=abs(pred-target),constant_rate_baseline=constant_rate*rows[i]['duration_s']))
    print(f'Cross validation source {fold+1}/{len(sources)} complete',flush=True)
    (O/'progress.json').write_text(json.dumps(dict(stage='source_cross_validation',completed=fold+1,total=len(sources))))
mae=float(np.mean([x['absolute_error'] for x in results]))
baseline=float(np.mean([abs(x['constant_rate_baseline']-x['confirmed_count']) for x in results]))
head,mean,scale=fit(list(range(len(rows))))
torch.save(dict(head=head.state_dict(),mean=mean,scale=scale,config=config,
    encoder_path=str(weight),encoder_sha256=encoder_hash,
    source_hashes=sources,trained_on_all_reviewed_segments=True),O/'experimental_count_head.pt')
report=dict(config=config,segments=len(rows),original_sources=len(sources),
    training_performed=True,encoder_frozen=True,encoder_sha256=encoder_hash,
    leave_source_out_mean_absolute_error=mae,constant_rate_baseline_mae=baseline,
    beats_constant_rate_baseline=mae<baseline,predictions=results,
    release_precision=None,release_recall=None,production_ready=False,
    limitations=['Only 12 count-labelled clips from 10 original sources.',
      'Generic image features, not a trained whole-feta detector.',
      'A sum-of-density loss does not establish individual release timing or block identities.',
      'No per-tank association or live-camera integration.',
      'Source-separated development experiment, not fresh independent acceptance testing.',
      'Final head uses all reviewed segments; cross-validation predictions use excluded-source heads.'])
(O/'results.json').write_text(json.dumps(report,indent=2))
(O/'progress.json').write_text(json.dumps(dict(stage='complete',training_performed=True)))
print(json.dumps({k:v for k,v in report.items() if k not in ('config','predictions','limitations')},indent=2),flush=True)
