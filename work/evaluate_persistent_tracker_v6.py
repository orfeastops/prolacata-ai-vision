"""One frozen association experiment on saved October detector outputs.

No model fitting. Reference counts are joined only after prediction artifacts
are frozen. These are historically reviewed development clips, not acceptance.
"""
import hashlib,json,time
from pathlib import Path
from persistent_payload_tracker_v6 import PersistentCounter, CONFIG

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/facility_dataset/temporal_pipeline'
V5=BASE/'placement_counter_v5/object_expansion'
OUT=BASE/'placement_counter_v6/association_experiment'


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2),encoding='utf-8')


def main():
    if (OUT/'predictions_frozen.json').exists():raise RuntimeError('Frozen run exists; do not overwrite or tune against it')
    files=sorted((V5/'predictions').glob('*.json'))
    inputs=[]
    for p in files:
        r=json.loads(p.read_text())
        inputs.append(dict(id=r['id'],source_sha256=r['source_sha256'],original_end_s=r['original_end_s'],
            frames=[dict(time_s=f['time_s'],detections=[{k:d[k] for k in ('bbox','confidence','quantity')}
                    for d in f['detections']]) for f in r['frame_outputs']]))
    frozen=dict(config=CONFIG,created_unix=time.time(),
        code_sha256={n:digest(ROOT/'work'/n) for n in ['persistent_payload_tracker_v6.py','evaluate_persistent_tracker_v6.py']},
        input_files_sha256={p.name:digest(p) for p in files},
        detector_sha256=json.loads((V5/'training_complete.json').read_text())['checkpoint_sha256'],
        september_used=False,training=False,inventory_gate_used=False,
        scope='Association-only development experiment; no inventory model exists yet')
    save(OUT/'frozen_before_evaluation.json',frozen)
    predictions=[]
    for r in inputs:
        c=PersistentCounter();linked=[]
        for f in r['frames']:
            linked.append(dict(time_s=f['time_s'],detections=c.step(f['time_s'],f['detections'])))
        c.finish(r['frames'][-1]['time_s'])
        events=[e for e in c.events if 0<=e['time_s']<=r['original_end_s']]
        pred=dict(id=r['id'],source_sha256=r['source_sha256'],native_frames=len(r['frames']),
            candidate_additions=sum(e['predicted_quantity'] for e in events),
            candidate_events=events,rejected_tracks=c.rejected,
            total_tracks=len(c.events)+len(c.rejected),
            bridged_tracks=sum(e['bridged_gaps']>0 for e in c.events+c.rejected),
            confirmed_additions=None,release_verification_available=False)
        save(OUT/'predictions'/f"{r['id']}.json",dict(**pred,frame_outputs=linked))
        predictions.append(pred)
    save(OUT/'predictions_frozen.json',dict(predictions=predictions,config_sha256=digest(OUT/'frozen_before_evaluation.json')))
    # Only scoring below this line can access reference counts.
    refs={r['id']:r for r in json.loads((V5/'count_results.json').read_text())['predictions']}
    rows=[]
    for p in predictions:
        ref=refs[p['id']]
        rows.append(dict(id=p['id'],reference_count=ref['reference_count'],
            v5_candidate_additions=ref['accepted_additions'],v6_candidate_additions=p['candidate_additions'],
            v5_tracks=len(ref['accepted_events'])+len(ref['unresolved_tracks']),v6_tracks=p['total_tracks'],
            bridged_tracks=p['bridged_tracks']))
    metrics={}
    for variant in ['v5','v6']:
        scored=[r for r in rows if r['reference_count'] is not None]
        positives=[r for r in scored if r['reference_count']>0];negatives=[r for r in scored if r['reference_count']==0]
        key=variant+'_candidate_additions'
        metrics[variant]=dict(scored_clips=len(scored),positive_clips=len(positives),
            positive_exact=sum(r[key]==r['reference_count'] for r in positives),negative_clips=len(negatives),
            negative_false_counts=sum(r[key]>0 for r in negatives),
            mean_absolute_count_error=sum(abs(r[key]-r['reference_count']) for r in scored)/len(scored),
            reference_sum=sum(r['reference_count'] for r in scored),candidate_sum=sum(r[key] for r in scored))
    result=dict(rows=rows,metrics=metrics,prediction_sha256=digest(OUT/'predictions_frozen.json'),
        native_frames=sum(p['native_frames'] for p in predictions),training=False,
        september_used=False,independent_acceptance=False,production_ready=False,
        interpretation='Count comparison of trajectory candidates only. Inventory consistency and physical release are not supplied. Historical October diagnostics; not event precision or live readiness.')
    save(OUT/'comparison.json',result)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
