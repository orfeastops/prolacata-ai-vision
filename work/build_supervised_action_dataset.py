"""Build a source-separated pilot for action proposals, never assumed block counts."""
import json, pathlib, collections
R=pathlib.Path('outputs/facility_dataset/temporal_pipeline'); B=R/'review_batch_01'
OUT=R/'supervised_actions';OUT.mkdir(exist_ok=True)
batch={r['clip_id']:r for r in json.loads((B/'batch_manifest.json').read_text())}
examples=[]
def split(cid):
    if batch[cid]['date']=='2026-10-03':return 'test'
    if cid=='B019':return 'val'
    return 'train'
def add(cid,eid,worker,start,end,label,quantity=None,basis='assistant reviewed event interval'):
    r=batch[cid]; start=max(0,start);end=min(r['duration_s'],end)
    assert end>start
    examples.append(dict(example_id=eid,clip_id=cid,source_sha256=r['source_sha256'],media_path=r['media_path'],
      date=r['date'],camera=11,worker_track=worker,source_start_s=round(r['source_relative_start_s']+start,3),
      source_end_s=round(r['source_relative_start_s']+end,3),clip_interval_s=[start,end],label=label,
      observed_quantity=quantity,quantity_used_as_training_target=False,split=split(cid),label_basis=basis,
      clock_verified=False))
for p in sorted(B.glob('B*/reviewed_events.json')):
    r=json.loads(p.read_text());cid=r['source']['clip_id']
    for e in r.get('events',[]):
        if e['action']!='whole_cheese_blocks_to_filling_tank':continue
        add(cid,e['event_id'],e['worker_track'],e['pickup_window_s'][0]-.125,e['release_window_s'][1]+.125,
            'whole_block_transfer',e['quantity'])
    for j,e in enumerate(r.get('non_placement_events',[])):
        if 'worker_track' not in e or e['worker_track']=='both':continue
        label='separator_handling' if e['action']=='large_grid_separator_to_rack' else 'other_or_idle'
        add(cid,f'{cid}_nonplacement_{j}',e['worker_track'],*e['window_s'],label)
# These are explicit reviewed idle/empty-conveyor intervals, not automatic labels
# for all unannotated time. Unknown hand movements are never converted to negatives.
idle={'B001':[(4,8),(10,14)],'B002':[(1,5),(9,13)],'B003':[(7,11)],
      'B010':[(2,6),(9,13)],'B013':[(8,12)],'B015':[(4,8)],'B016':[(3,7),(10,14)],
      'B017':[(6,10)],'B018':[(3,7)],'B019':[(.125,2.625)],
      'B021':[(8.125,12.125)],'B023':[(.125,3.625)],'B024':[(2,6),(8,12)]}
for cid,windows in idle.items():
    for j,(start,end) in enumerate(windows):
        for worker in ['filling_left','filling_right']:
            add(cid,f'{cid}_idle_{j}_{worker}',worker,start,end,'other_or_idle',0,
                'assistant visual context review: no new block transfer; waiting, empty source, or station cleanup')
add('B009','B009_reviewed_separator_test','filling_right',10.875,13.875,'separator_handling',0,
    'assistant dense 4 fps visual review of empty separator removal')
# Validation and test must contain examples of all action classes. They remain
# small pilot samples, not estimates of whole-day counting accuracy.
feedback_path=R/'sequence_annotation_v2/expert_feedback.json'
if feedback_path.exists():
    for correction in json.loads(feedback_path.read_text(encoding='utf-8')):
        eid=correction.get('supersedes_draft_event_id')
        if eid and correction.get('semantic_label_confirmed') and correction.get('whole_feta_block_increment')==0:
            for example in examples:
                if example['example_id']==eid:
                    example.update(label='other_or_idle',observed_quantity=0,label_basis='user corrected: '+correction['action'],correction_event_id=correction['event_id'])
groups={s:{e['source_sha256'] for e in examples if e['split']==s} for s in ['train','val','test']}
assert not(groups['train']&groups['val'] or groups['train']&groups['test'] or groups['val']&groups['test'])
assert all(e['date']=='2026-10-03' for e in examples if e['split']=='test')
assert len({e['example_id'] for e in examples})==len(examples)
report={'role':'pilot action proposals; block quantities are not predicted by this classifier',
 'examples':len(examples),'counts':{s:dict(collections.Counter(e['label'] for e in examples if e['split']==s)) for s in groups},
 'source_counts':{s:len(g) for s,g in groups.items()},'heldout_day':'2026-10-03',
 'validation_pretraining_exposure':'B019 source was seen without labels during self-supervised pretraining; supervised labels reserved for validation',
 'test_pretraining_exposure':False,'reviewer':'assistant visual annotations, not independently expert verified',
 'quantity_model_trained':False,'automatic_production_counting_enabled':False,
 'no_fixed_tank_total':True,'no_fixed_blocks_per_gesture':True,
 'limitations':['Small event sample; more one-block, crumb and occlusion examples required.',
 'Classifying an action does not establish block quantity or tank identity.',
 'Untrimmed-video event detection and cross-camera transfers are not validated.']}
(OUT/'examples.json').write_text(json.dumps(examples,indent=2));(OUT/'dataset_review.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
