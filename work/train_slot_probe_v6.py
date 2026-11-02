"""Train one small slot-appearance baseline; all localization is supplied.

This model cannot detect a tray, count a full tray, identify a pickup or a release.
It isolates whether manually localized appearance distinguishes cheese/base.
No hyperparameter search or reference-count feedback is performed.
"""
import json,hashlib,time
from collections import Counter
from pathlib import Path
import numpy as np,cv2
from prepare_slot_probe_v6 import OUT

CONFIG=dict(seed=291026,method='L2-regularized logistic appearance classifier',steps=500,
    learning_rate=.03,l2=.01,features='HOG64 implemented in numpy + Lab16',score_minimum=.8,
    note='Classifier scores are not calibrated probabilities. No full-image localization or temporal logic.')

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,obj):p.write_text(json.dumps(obj,indent=2),encoding='utf-8')

def hog(im):
    gray=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY).astype(np.float32)/255.
    gy,gx=np.gradient(gray);magnitude=np.hypot(gx,gy)
    bins=np.floor(np.mod(np.arctan2(gy,gx),np.pi)/(np.pi/9)).astype(int)%9
    cells=np.zeros((8,8,9),np.float32)
    for y in range(8):
        for x in range(8):
            cells[y,x]=np.bincount(bins[y*8:y*8+8,x*8:x*8+8].ravel(),
                weights=magnitude[y*8:y*8+8,x*8:x*8+8].ravel(),minlength=9)
    blocks=[]
    for y in range(7):
        for x in range(7):
            b=cells[y:y+2,x:x+2].ravel();b=b/np.sqrt(np.dot(b,b)+1e-6)
            b=np.minimum(b,.2);blocks.append(b/np.sqrt(np.dot(b,b)+1e-6))
    return np.concatenate(blocks)

def features(patch):
    im=cv2.resize(patch,(64,64),interpolation=cv2.INTER_LINEAR)
    h=hog(im)
    lab=cv2.resize(cv2.cvtColor(im,cv2.COLOR_BGR2LAB),(16,16),interpolation=cv2.INTER_AREA).reshape(-1)/255.
    return np.concatenate([h,lab]).astype(np.float32)


def main():
    if (OUT/'training_complete.json').exists():raise RuntimeError('Frozen slot experiment already exists')
    cv2.setNumThreads(2)
    manifest=json.loads((OUT/'manifest.json').read_text())
    train=[r for r in manifest['rows'] if r['split']=='train' and r['label'] is not None]
    test=[r for r in manifest['rows'] if r['split']=='development_test']
    assert not {r['source_sha256'] for r in train}&{r['source_sha256'] for r in test}
    # No test labels are passed to feature extraction or prediction.
    test_inputs=[{k:r[k] for k in ('id','patch','frame_id','bbox','image')} for r in test]
    save(OUT/'frozen_before_training.json',dict(config=CONFIG,manifest_sha256=digest(OUT/'manifest.json'),
        code_sha256=digest(__file__),created_unix=time.time(),september_used=False,
        labels='Assistant proposals, not human ground truth',
        train_frames=len({r['frame_id'] for r in train}),test_frames=len({r['frame_id'] for r in test}),
        train_patch_counts=dict(Counter(str(r['label']) for r in train)),
        manual_localization=True,automatic_counting=False))
    x=np.stack([features(cv2.imread(r['patch'])) for r in train]);y=np.asarray([r['label'] for r in train],np.int32)
    mean=x.mean(axis=0);std=np.maximum(x.std(axis=0),.03)
    z=np.column_stack([(x-mean)/std,np.ones(len(x))]).astype(np.float64)
    weights=np.zeros(z.shape[1]);moment=np.zeros_like(weights);variance=np.zeros_like(weights)
    sample_weight=np.array([len(y)/(2*sum(y==v)) for v in y])
    started=time.time();losses=[]
    for step in range(1,CONFIG['steps']+1):
        scores=1/(1+np.exp(-np.clip(z@weights,-40,40)))
        penalty=CONFIG['l2']*weights;penalty[-1]=0
        gradient=z.T@((scores-y)*sample_weight)/len(y)+penalty
        moment=.9*moment+.1*gradient;variance=.999*variance+.001*gradient**2
        weights-=CONFIG['learning_rate']*(moment/(1-.9**step))/(np.sqrt(variance/(1-.999**step))+1e-8)
        if step%50==0:
            loss=-np.mean(sample_weight*(y*np.log(scores+1e-12)+(1-y)*np.log(1-scores+1e-12)))
            losses.append(dict(step=step,training_log_loss=float(loss)))
    checkpoint=OUT/'slot_appearance_linear.npz'
    np.savez_compressed(checkpoint,weights=weights,mean=mean,std=std)
    test_x=np.stack([features(cv2.imread(r['patch'])) for r in test_inputs])
    with np.load(checkpoint) as saved:
        logits=((test_x-saved['mean'])/saved['std'])@saved['weights'][:-1]+saved['weights'][-1]
    scores=1/(1+np.exp(-np.clip(logits,-40,40)));predictions=[]
    for r,p in zip(test_inputs,scores):
        hard=int(p>=.5);share=float(max(p,1-p))
        predictions.append(dict(id=r['id'],predicted_class=hard if share>=CONFIG['score_minimum'] else None,
            hard_prediction=hard,maximum_class_score=share,cheese_score=float(p),
            localization='manual crop',source_count_not_available=True))
    save(OUT/'predictions_frozen.json',dict(predictions=predictions,model_sha256=digest(checkpoint)))
    # Join reference labels only after predictions have been written.
    references={r['id']:r for r in test};rows=[]
    confusion=np.zeros((2,2),dtype=int)
    for p in predictions:
        r=references[p['id']];ref=r['label']
        if ref is not None:confusion[ref,p['hard_prediction']]+=1
        rows.append(dict(**p,reference_class=ref,frame_id=r['frame_id'],patch=r['patch']))
    clear=[r for r in rows if r['reference_class'] is not None]
    covered=[r for r in clear if r['predicted_class'] is not None]
    challenge=[r for r in rows if r['reference_class'] is None]
    metrics=dict(clear_slots=len(clear),hard_predictions_correct=sum(r['hard_prediction']==r['reference_class'] for r in clear),
        confident_slots=len(covered),confident_correct=sum(r['predicted_class']==r['reference_class'] for r in covered),
        abstained_slots=len(clear)-len(covered),confusion_rows_truth_columns_hard_prediction=confusion.tolist(),
        obstructed_challenges=len(challenge),obstructed_confident_predictions=sum(r['predicted_class'] is not None for r in challenge))
    save(OUT/'results.json',dict(metrics=metrics,rows=rows,manual_localization=True,
        independent_acceptance=False,production_ready=False,source_disjoint=True,
        interpretation='Agreement with assistant labels on selected manually cropped positions from one other source. Not tank-counting accuracy. Repeated frames share tray appearance.'))
    save(OUT/'training_complete.json',dict(config=CONFIG,elapsed_s=time.time()-started,train_patches=len(train),
        train_frames=len({r['frame_id'] for r in train}),test_patches=len(test),
        checkpoint=str(checkpoint),checkpoint_sha256=digest(checkpoint),training_loss=losses,
        metrics=metrics,no_automatic_localization=True,september_used=False))
    print(json.dumps(metrics,indent=2))

if __name__=='__main__':main()
