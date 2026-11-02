"""Frozen, source-disjoint event/quantity diagnostic, not a production counter.

Train only C01 and assistant proposals C03-C06. C02 and the 12 historical
October benchmark segments are excluded from every optimizer update. Native
frames are retained. Unannotated time is unknown, never fabricated background.
"""
import os
os.environ['YOLO_AUTOINSTALL'] = 'false'
import argparse
import hashlib
import json
import time
from pathlib import Path
import cv2
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'outputs/facility_dataset/temporal_pipeline'
REVIEW = BASE / 'sequence_annotation_v4/assistant_visual_review'
OUT = BASE / 'placement_counter_v4/event_quantity_diagnostic'
CONFIG = dict(seed=2810, epochs=240, learning_rate=.001, weight_decay=.03,
    channels=48, dilations=[1, 2, 4, 8, 16], dropout=.25,
    encoder='frozen generic yolo26n, no facility-trained weights',
    pools=[[6, 10], [3, 5], [2, 3]], train_clips=['C01','C03','C04','C05','C06'],
    held_out_new_source='C02', feature_batch=8,
    sampling='all native decoded frames, original PTS, no temporal resampling',
    heads=['carrying_probability', 'deposit_probability', 'quantity_1_2_3'],
    release_supervision='one positive peak somewhere within each bounded release interval',
    background_supervision='explicit negative intervals only; missing entries masked',
    human_weight=1., assistant_weight=.5, release_threshold=.5,
    carry_threshold=.5, quantity_threshold=.55, rearm_low_seconds=.20,
    carry_history_seconds=6., minimum_carry_frames=2,
    benchmark_gate=dict(positive_exact_min=6, negative_false_counts_max=0, count_mae_max=1.),
    gate_scope='research progression screen only, not production acceptance',
    no_hyperparameter_search=True, september_used=False, october3_used=False)

def digest(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding='utf-8')
    # Windows readers/AV can momentarily deny ReplaceFile while progress is read.
    # Keep the previous complete JSON and retry the atomic replacement.
    for attempt in range(30):
        try:
            tmp.replace(path)
            return
        except PermissionError:
            if attempt==29:raise
            time.sleep(.1)

def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def interval_mask(t, bounds):
    return (t >= bounds[0]) & (t <= bounds[1])

def dataset():
    proposed=load(REVIEW/'assistant_annotations.json')
    rows=[]
    for clip in ['C01','C02','C03','C04','C05','C06']:
        meta=load(REVIEW/clip/'frames.json')
        assert any(d in Path(meta['source_file']).name for d in ('20261001','20261021'))
        t=np.asarray(meta['relative_times_s'], dtype=np.float64)
        ids=np.asarray(meta['source_frame_indices'])
        assert np.all(np.diff(t)>0) and np.all(np.diff(ids)==1)
        row=dict(id=clip, source_sha256=meta['source_sha256'],
            source_file=meta['source_file'], role='train' if clip in CONFIG['train_clips'] else 'new_source_check',
            timestamps=t.tolist(), source_frame_indices=ids.tolist(), events=[], negatives=[], masks=[],
            original_end_s=load(BASE/'sequence_annotation_v4'/clip/'annotation.json')['native_relative_timestamps_s'][-1],
            image_files=[str(REVIEW/clip/f) for f in meta['files']], reference_count=None)
        if clip in ('C01','C02'):
            path=ROOT/'work/project_handoff'/f'EXPERT_FEEDBACK_{clip}.json'
            data=load(path)
            assert data['source_sha256']==row['source_sha256']
            row['annotation_sha256']=digest(path)
            for e in data['events']:
                side=['left','right'].index(e['position'])
                lift=e.get('lift_time_s'); release=e.get('release_time_s')
                if e.get('training_eligible') is False or e.get('annotation_conflict'):
                    row['masks'].append(dict(side=side, interval=[lift if lift is not None else t[0],release if release is not None else t[-1]],reason='conflict_or_censored'))
                    continue
                if e['destination']=='filling_tank' and release is not None:
                    releases=e.get('release_events') or [dict(time_s=release,quantity=e['quantity'])]
                    remaining=e['quantity']; previous=lift+.15
                    for n,r in enumerate(releases):
                        # Sub-releases retain their actual quantities and shared transfer ID.
                        row['events'].append(dict(id=e['event_id']+f'_R{n+1}', parent=e['event_id'],side=side,
                            quantity=r['quantity'], carry_quantity=remaining,
                            pickup_interval=[lift-.12,lift+.15], carry_interval=[previous,r['time_s']-.20],
                            release_interval=[r['time_s']-.20,r['time_s']+.20],
                            provenance='expert_quantity_approximate_timing', weight=1.))
                        previous=r['time_s']+.20;remaining-=r['quantity']
                elif e['destination']!='filling_tank':
                    a=lift if lift is not None else e.get('nearest_release_time_s')
                    b=release if release is not None else a
                    if a is not None:
                        if b==a:a-=.12;b+=.12
                        row['negatives'].append(dict(id=e['event_id'], side=side,interval=[a,b],action=e['destination'],weight=1.))
        else:
            data=next(c for c in proposed['clips'] if c['clip_id']==clip)
            row['annotation_sha256']=digest(REVIEW/'assistant_annotations.json')
            for e in data['events']:
                side=['left','right'].index(e['side'])
                if not e['candidate_for_silver_training']:
                    bounds=e.get('interval_s') or [e['pickup_interval_s'][0],e['deposit_interval_s'][1]]
                    row['masks'].append(dict(side=side,interval=bounds,reason=e['event_id']))
                elif e['action']=='whole_block_transfer':
                    row['events'].append(dict(id=e['event_id'],parent=e['event_id'],side=side,quantity=e['quantity'],
                        carry_quantity=e['quantity'],pickup_interval=e['pickup_interval_s'],
                        carry_interval=e['carry_window_s'],release_interval=e['deposit_interval_s'],
                        provenance='assistant_proposal',weight=.5))
                else:
                    row['negatives'].append(dict(id=e['event_id'],side=side,interval=e['interval_s'],action=e['action'],weight=.5))
        rows.append(row)
    # Historical complete-clip count references are used only after the model is frozen.
    old=load(BASE/'placement_counter_v3/interval_supervision.json')['segments']
    for r in old:
        assert r['date'] in ('2026-10-01','2026-10-21')
        path=BASE/'placement_counter_v3/native_frames'/(r['segment_id']+'.npz')
        with np.load(path) as f:
            assert str(f['source_sha256'])==r['source_sha256']
            t=f['timestamps']-r['source_encoded_interval_s'][0]
            ids=f['source_frame_indices']
        rows.append(dict(id=r['segment_id'],source_sha256=r['source_sha256'],role='historical_source_check',
            timestamps=t.tolist(),source_frame_indices=ids.tolist(),native_npz=str(path),
            original_end_s=r['duration_s'],reference_count=r['confirmed_count'],
            events=[],negatives=[],masks=[]))
    tr={r['source_sha256'] for r in rows if r['role']=='train'}
    te={r['source_sha256'] for r in rows if r['role']!='train'}
    assert not tr & te, 'Source leakage'
    assert len(tr)==5
    manifest=dict(rows=rows,train_sources=sorted(tr),excluded_sources=sorted(te),
        no_train_test_source_overlap=True,unannotated_frames_are_unknown=True,
        unresolved_intervals_masked=True,training_release_events=sum(len(r['events']) for r in rows if r['role']=='train'),
        training_negative_intervals=sum(len(r['negatives']) for r in rows if r['role']=='train'))
    if (OUT/'dataset.json').exists():
        assert load(OUT/'dataset.json')==manifest, 'Existing experiment inputs changed; use a new experiment directory'
    else:save(OUT/'dataset.json',manifest)
    return rows

def extract(rows):
    from ultralytics import YOLO
    encpath=ROOT/'outputs/feta_training/yolo26n.pt'
    encsha=digest(encpath)
    encoder=YOLO(str(encpath)).model.eval()
    for p in encoder.parameters():p.requires_grad=False
    captured=[]
    def hook(_module,args):
        captured.clear()
        captured.extend(F.adaptive_avg_pool2d(x,tuple(pool)).flatten(1)
            for x,pool in zip(args[0],CONFIG['pools']))
    handle=encoder.model[-1].register_forward_pre_hook(hook)
    arrays=[]
    for i,row in enumerate(rows):
        cache=OUT/'features'/(row['id']+'.npz');cache.parent.mkdir(exist_ok=True)
        fingerprint=hashlib.sha256(json.dumps(dict(source=row['source_sha256'],ids=row['source_frame_indices'],
            pools=CONFIG['pools'],encoder=encsha),sort_keys=True).encode()).hexdigest()
        if cache.exists():
            with np.load(cache) as f:
                assert str(f['fingerprint'])==fingerprint
                z=f['features'].astype(np.float32)
        else:
            if 'native_npz' in row:
                with np.load(row['native_npz']) as f: frames=f['frames'].copy()
            else:
                frames=[cv2.imread(p) for p in row['image_files']]
            zz=[]
            for start in range(0,len(frames),CONFIG['feature_batch']):
                ims=frames[start:start+CONFIG['feature_batch']]
                assert all(im is not None and im.shape==(360,640,3) for im in ims)
                batch=[cv2.copyMakeBorder(cv2.cvtColor(im,cv2.COLOR_BGR2RGB),12,12,0,0,
                    cv2.BORDER_CONSTANT,value=(114,114,114)) for im in ims]
                x=torch.from_numpy(np.stack(batch)).permute(0,3,1,2).float()/255
                with torch.inference_mode():
                    encoder(x);zz.append(torch.cat(captured,dim=1).numpy())
                if start%80==0:
                    save(OUT/'progress.json',dict(stage='native_visual_features',clip=row['id'],
                        completed_clips=i,total_clips=len(rows),clip_frames_done=start+len(ims),clip_frames=len(frames)))
            z=np.concatenate(zz).astype(np.float32)
            np.savez_compressed(cache,features=z.astype(np.float16),fingerprint=fingerprint)
            # Always train/infer on the identical cached precision, including first run.
            z=z.astype(np.float16).astype(np.float32)
            del frames
        assert len(z)==len(row['timestamps'])
        arrays.append(z)
        print(f'Features {i+1}/{len(rows)} {row["id"]}: {z.shape}',flush=True)
    handle.remove()
    return arrays,encsha

class CausalBlock(nn.Module):
    def __init__(self,c,d):
        super().__init__();self.pad=2*d
        self.conv=nn.Conv1d(c,c,3,dilation=d);self.dropout=nn.Dropout(CONFIG['dropout'])
    def forward(self,x):return x+self.dropout(F.gelu(self.conv(F.pad(x,(self.pad,0)))))

class EventQuantityNet(nn.Module):
    def __init__(self,dim):
        super().__init__();c=CONFIG['channels']
        self.project=nn.Conv1d(dim,c,1)
        self.layers=nn.Sequential(*[CausalBlock(c,d) for d in CONFIG['dilations']])
        self.output=nn.Conv1d(c,10,1)
    def forward(self,x):
        y=self.output(self.layers(F.gelu(self.project(x))))
        return y.reshape(len(x),2,5,x.shape[-1])

def normalized_features(z,t,mean,scale):
    z=(z-mean)/scale
    delta=np.zeros_like(z);delta[1:]=z[1:]-z[:-1]
    dt=np.r_[1/15,np.diff(t)].astype(np.float32)[:,None]
    # No random feature projection. Spatial detail remains available to the learned head.
    return np.concatenate([z,delta,dt],axis=1).astype(np.float32)

def prepare_constraints(rows,indices,maxlen):
    events=[];negatives=[]
    for j,i in enumerate(indices):
        r=rows[i];t=np.asarray(r['timestamps'])
        unknown=np.zeros((2,len(t)),bool)
        for m in r['masks']:unknown[m['side']] |= interval_mask(t,m['interval'])
        for e in r['events']:
            s=e['side'];rel=interval_mask(t,e['release_interval']) & ~unknown[s]
            if not rel.any():raise ValueError(('No visible release frames',r['id'],e))
            carry=np.zeros(len(t),bool)
            if e['carry_interval'] and e['carry_interval'][1]>e['carry_interval'][0]:
                carry=interval_mask(t,e['carry_interval']) & ~unknown[s] & ~rel
            events.append((j,s,e,torch.tensor(np.flatnonzero(rel)),torch.tensor(np.flatnonzero(carry))))
        for n in r['negatives']:
            s=n['side'];mask=interval_mask(t,n['interval']) & ~unknown[s]
            # Inclusive interval endpoints may meet the preceding deposit. Remove overlap.
            for e in r['events']:
                if e['side']==s:
                    mask &= ~interval_mask(t,[e['pickup_interval'][0],e['release_interval'][1]])
            if mask.any():negatives.append((j,s,n,torch.tensor(np.flatnonzero(mask))))
    return events,negatives

def fit(rows,arrays):
    ix=[i for i,r in enumerate(rows) if r['role']=='train']
    joined=np.concatenate([arrays[i] for i in ix])
    mean=joined.mean(0);scale=np.maximum(joined.std(0),.05)
    fs=[normalized_features(arrays[i],np.asarray(rows[i]['timestamps']),mean,scale) for i in ix]
    maxlen=max(map(len,fs));x=torch.zeros(len(ix),fs[0].shape[1],maxlen)
    for j,f in enumerate(fs):x[j,:,:len(f)]=torch.from_numpy(f.T)
    events,negatives=prepare_constraints(rows,ix,maxlen)
    torch.manual_seed(CONFIG['seed']);model=EventQuantityNet(x.shape[1])
    opt=torch.optim.AdamW(model.parameters(),lr=CONFIG['learning_rate'],weight_decay=CONFIG['weight_decay'])
    logs=[]
    for epoch in range(CONFIG['epochs']):
        model.train();opt.zero_grad();y=model(x)
        pos=[];car=[];qty=[];neg=[]
        for j,s,e,rel,carry in events:
            w=e['weight'];lr=y[j,s,1,rel]
            peak=lr.argmax();pos.append(w*F.softplus(-lr[peak]))
            # Release interval only says where a completed group can occur. Never
            # assign its full quantity to every frame or invent exact release truth.
            qty.append(w*F.cross_entropy(y[j,s,2:,rel[peak]][None],torch.tensor([e['quantity']-1])))
            if len(carry):
                car.append(w*F.softplus(-y[j,s,0,carry]).mean())
                neg.append(w*F.softplus(y[j,s,1,carry]).mean())
                qty.append(w*F.cross_entropy(y[j,s,2:,carry].T,torch.full((len(carry),),e['carry_quantity']-1)))
        for j,s,n,mask in negatives:
            neg.append(n['weight']*F.softplus(y[j,s,:2,mask]).mean())
        loss=torch.stack(pos).mean()+torch.stack(car).mean()+torch.stack(qty).mean()+2*torch.stack(neg).mean()
        loss.backward();nn.utils.clip_grad_norm_(model.parameters(),2.);opt.step()
        if epoch%20==0 or epoch+1==CONFIG['epochs']:
            entry=dict(epoch=epoch+1,loss=float(loss.detach()),release=float(torch.stack(pos).mean().detach()),
                carry=float(torch.stack(car).mean().detach()),quantity=float(torch.stack(qty).mean().detach()),
                negative=float(torch.stack(neg).mean().detach()))
            logs.append(entry);print(json.dumps(entry),flush=True)
            save(OUT/'progress.json',dict(stage='training',**entry,total_epochs=CONFIG['epochs']))
    return model.eval(),mean,scale,logs

def probabilities(model,z,t,mean,scale):
    f=normalized_features(z,t,mean,scale)
    with torch.inference_mode():
        y=model(torch.from_numpy(f.T)[None])[0]
        phase=torch.sigmoid(y[:,:2]).permute(2,0,1).numpy()
        qty=torch.softmax(y[:,2:],dim=1).permute(2,0,1).numpy()
    return phase,qty

def decode(t,phase,quantity):
    """Streaming-style hysteresis; no labels, clip totals or event windows as input."""
    accepted=[];unresolved=[]
    for side in range(2):
        active=[];low_since=None;last_used_carry=-1
        def finish(indices,confirmation_time,censored=False):
            nonlocal last_used_carry
            if not indices:return
            peak=max(indices,key=lambda k:phase[k,side,1])
            before=np.flatnonzero((t>=t[peak]-CONFIG['carry_history_seconds']) & (t<t[peak]) &
                (phase[:,side,0]>=CONFIG['carry_threshold']))
            before=before[before>last_used_carry]
            q=quantity[peak,side];k=int(q.argmax())
            reasons=[]
            if len(before)<CONFIG['minimum_carry_frames']:reasons.append('no_new_carry_support')
            if q[k]<CONFIG['quantity_threshold']:reasons.append('quantity_ambiguous')
            if censored:reasons.append('release_episode_cut_off')
            event=dict(side=['left','right'][side],time_s=float(t[peak]),
                emitted_at_s=float(confirmation_time),predicted_quantity=k+1,
                quantity_scores=q.tolist(),release_score=float(phase[peak,side,1]),
                carry_support_frames=len(before),reasons=reasons)
            if reasons:unresolved.append(event)
            else:
                accepted.append(event);last_used_carry=int(before[-1])
        for i,ts in enumerate(t):
            if phase[i,side,1]>=CONFIG['release_threshold']:
                active.append(i);low_since=None
            elif active:
                if low_since is None:low_since=ts
                if ts-low_since>=CONFIG['rearm_low_seconds']:
                    finish(active,ts);active=[];low_since=None
        finish(active,t[-1],censored=True)
    return sorted(accepted,key=lambda e:e['time_s']),sorted(unresolved,key=lambda e:e['time_s'])

def evaluate(rows,arrays,model,mean,scale):
    reports=[]
    for row,z in zip(rows,arrays):
        t=np.asarray(row['timestamps']);phase,qty=probabilities(model,z,t,mean,scale)
        accepted,unresolved=decode(t,phase,qty)
        inside=[e for e in accepted if 0<=e['time_s']<=row['original_end_s']]
        predicted=sum(e['predicted_quantity'] for e in inside)
        ref=row['reference_count']
        report=dict(id=row['id'],role=row['role'],source_sha256=row['source_sha256'],
            accepted_additions_in_original_clip=predicted,reference_complete_clip_count=ref,
            absolute_count_error=abs(predicted-ref) if ref is not None else None,
            accepted_events=accepted,unresolved_events=unresolved,
            quantities_come_from_model=True,manual_event_windows_used_for_decoding=False)
        if row['id']=='C02':
            known=[e for e in row['events'] if 0<=e['release_interval'][0]<=row['original_end_s']]
            matched=[];used=set()
            for e in known:
                choices=[(i,p) for i,p in enumerate(inside) if i not in used and p['side']==['left','right'][e['side']] and
                    e['release_interval'][0]-.5<=p['time_s']<=e['release_interval'][1]+.5]
                if choices:
                    i,p=min(choices,key=lambda a:abs(a[1]['time_s']-np.mean(e['release_interval'])))
                    used.add(i);matched.append(dict(reference_id=e['id'],predicted=p['predicted_quantity'],reference=e['quantity']))
            report['expert_event_check']=dict(listed_completed_events=len(known),listed_blocks=sum(e['quantity'] for e in known),
                matched_events=len(matched),matched_correct_quantity=sum(m['predicted']==m['reference'] for m in matched),matches=matched,
                unmatched_predictions_require_review=len(inside)-len(used),
                exhaustive_clip_total_confirmed=False,precision=None,recall=None)
        reports.append(report)
        np.savez_compressed(OUT/(row['id']+'_predictions.npz'),times=t,phase=phase,quantity=qty)
    historical=[r for r in reports if r['role']=='historical_source_check']
    positive=[r for r in historical if r['reference_complete_clip_count']>0]
    negative=[r for r in historical if r['reference_complete_clip_count']==0]
    metrics=dict(clips=len(historical),source_files=len({r['source_sha256'] for r in historical}),
        mean_absolute_count_error=float(np.mean([r['absolute_count_error'] for r in historical])),
        positive_clips=len(positive),positive_exact=sum(r['absolute_count_error']==0 for r in positive),
        negative_clips=len(negative),negative_false_counts=sum(r['accepted_additions_in_original_clip']>0 for r in negative))
    gate=CONFIG['benchmark_gate']
    metrics['screen_passed']=(metrics['mean_absolute_count_error']<=gate['count_mae_max'] and
        metrics['positive_exact']>=gate['positive_exact_min'] and metrics['negative_false_counts']<=gate['negative_false_counts_max'])
    return reports,metrics

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--prepare-only',action='store_true');args=parser.parse_args()
    torch.set_num_threads(4);cv2.setNumThreads(2);OUT.mkdir(parents=True,exist_ok=True)
    if (OUT/'results.json').exists():raise RuntimeError('Frozen experiment already complete; do not overwrite')
    if (OUT/'config.json').exists():assert load(OUT/'config.json')==CONFIG
    else:save(OUT/'config.json',CONFIG)
    rows=dataset()
    if args.prepare_only:
        print(json.dumps({k:v for k,v in load(OUT/'dataset.json').items() if k!='rows'}));return
    started=time.time();arrays,encsha=extract(rows)
    model,mean,scale,logs=fit(rows,arrays)
    checkpoint=OUT/'event_quantity_v4.pt'
    torch.save(dict(model=model.state_dict(),mean=mean,scale=scale,config=CONFIG,
        input_dim=model.project.in_channels,train_sources=sorted({r['source_sha256'] for r in rows if r['role']=='train'}),
        encoder_sha256=encsha,dataset_sha256=digest(OUT/'dataset.json')),checkpoint)
    # Persist the frozen weights and recipe before seeing evaluation output.
    save(OUT/'frozen_before_evaluation.json',dict(checkpoint_sha256=digest(checkpoint),config_sha256=digest(OUT/'config.json'),
        script_sha256=digest(__file__),dataset_sha256=digest(OUT/'dataset.json')))
    reports,metrics=evaluate(rows,arrays,model,mean,scale)
    result=dict(training_performed=True,config=CONFIG,metrics=metrics,predictions=reports,
        training_loss=logs,native_frame_instances=sum(map(len,arrays)),
        checkpoint_sha256=digest(checkpoint),encoder_sha256=encsha,elapsed_seconds=time.time()-started,
        production_ready=False,live_cameras_connected=False,september_used=False,october3_used=False,
        full_september_rerun_authorized_by_gate=metrics['screen_passed'],
        limitations=['Assistant proposals are unverified silver labels, weighted below expert entries.',
            'Only five training source files; quantity-three examples occur in one source.',
            'Generic frozen visual encoder plus learned temporal heads; not individual object tracking.',
            'Historical source benchmark is previously inspected development material, not fresh acceptance data.',
            'C02 has listed expert events but no independently confirmed exhaustive clip total.',
            'Accepted additions and unresolved episodes are separate; abstention is not verified zero production.',
            'No automatic tank boundary detection or cross-camera matching.'])
    save(OUT/'results.json',result);save(OUT/'progress.json',dict(stage='complete',**metrics,elapsed_seconds=time.time()-started))
    print(json.dumps(metrics),flush=True)

if __name__=='__main__':main()
