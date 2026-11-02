import json, collections
from pathlib import Path
from PIL import Image
from tank_counting_contract import apply_contract

out=Path('outputs/tank_transfer_training_v1')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,r):p.write_text(json.dumps(r,indent=2,ensure_ascii=False),encoding='utf-8')
inv=read(out/'archive_inventory.json')
seen={('20261006',11),('20261006',15),('20261013',11),('20261013',15)}
samples=read(out/'scene_sample_manifest.json')
sample_members={r['member'] for r in samples}
for r in inv['records']:
    if (r['date'],r['camera']) in seen and r['member'] in sample_members:
        r['pixel_inspected']=True
write(out/'archive_inventory.json',inv)
for p in (out/'training_scene_samples').glob('*.jpg'):
    with Image.open(p) as im:
        if im.height==900:im.crop((0,0,1440,600)).save(p)
plan=read(out/'training_protocol.json')
plan['proposed_initial_baseline']['detector']='YOLO26s (yolo26s.pt), fine-tuned on tank boxes. Pin checkpoint SHA256 before first run. No tank checkpoint trained or downloaded during this preparation.'
plan['local_environment']={'ultralytics':'8.4.184','torch':'2.14.1+cpu','cuda_available':False}
plan['visual_survey_observations']=[
    'Camera placement is consistent in sampled6/10 and13/10 images. Samples include darkness, empty tank staging, the filling area and later storage.',
    'Blue/gray/beige tank bodies and different covers are visible. Neither body color nor a white-looking top alone defines a production-cheese transfer.',
    'Camera15 includes many stationary and stacked empty tanks, people/forklift movements and occlusion near the entry. Detecting a tank is not itself a transfer event.',
    '24 training-export stills were visually surveyed. No validation or test pixels were inspected. These stills are unlabelled, not a ready training dataset.'
]
write(out/'training_protocol.json',plan)
apply_contract(out)

events=[]
for date in ['20261001','20261003','20261021']:
    for e in read(Path(f'outputs/tank_door_audit/reviewed_{date}.json'))['events']:
        events.append(dict(date=date,split='train',proposal_id=e['proposal_id'],source=e['source'],
                           camera=11,event_type='production_exit' if e['load']=='production_cheese' else 'repacked_cheese_exit',
                           camera_clock_interval=e['camera_clock_crossing_interval'],
                           candidate_source_pts=[e['candidate_start'],e['candidate_end']],
                           evidence=str(Path('outputs/tank_door_audit')/e['evidence_sheet']),
                           provenance='Existing assistant visual audit;21/10 corrected44to45 on30/10.',
                           supervision_status='event_reference_for_annotation_not_frame_boxes',
                           limitations='Approximate event interval; inspect exact frames for boxes and clip boundaries. Missing events and ID switches have not been independently ruled out.'))
write(out/'development_event_references.json',events)

videos=[r for r in inv['records'] if r['media_type']=='video']
days={name:{r['date'] for r in videos if r['split']==name} for name in ['train','validation','test']}
assert not days['train']&days['validation']
assert not days['train']&days['test']
assert not days['validation']&days['test']
assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test')
assert all(r['split']=='train' for r in samples)
assert all(Path(r['local_path']).is_file() for r in samples)
# CRC/size collision candidates are reported, not automatically treated as proof.
by_crc=collections.defaultdict(list)
for r in videos:by_crc[(r['zip_crc32'],r['uncompressed_bytes'])].append(r)
collisions=[dict(crc32=k[0],bytes=k[1],members=[r['member'] for r in rows])
            for k,rows in by_crc.items() if len({r['split'] for r in rows})>1]
verification=dict(status='preparation_complete_training_not_started',
                  video_count_by_split=dict(collections.Counter(r['split'] for r in videos)),
                  days_by_split={k:sorted(v) for k,v in days.items()},
                  day_partitions_disjoint=True,test_pixels_inspected=0,
                  survey_stills_extracted=len(samples),survey_stills_visually_inspected=24,
                  prior_matching_export_intervals=sum(r['same_camera_time_range_in_prior_inventory'] for r in videos),
                  cross_split_crc_size_candidates=collisions,development_event_references=len(events),
                  pending=['Exact duplicate SHA256 verification before dataset release','Tank image boxes and temporal labels','Model training','Validation and frozen test predictions'])
write(out/'preparation_verification.json',verification)
print(json.dumps(verification,ensure_ascii=False,indent=2))
