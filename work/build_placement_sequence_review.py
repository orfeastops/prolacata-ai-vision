"""Prepare October sequence annotation material, never training/test predictions.
Existing assistant annotations are provisional. Unknown stages stay unknown.
"""
import json,pathlib,subprocess,collections
from PIL import Image,ImageDraw
ROOT=pathlib.Path(__file__).resolve().parents[1]
T=ROOT/'outputs/facility_dataset/temporal_pipeline'
OUT=T/'sequence_annotation_v2';OUT.mkdir(exist_ok=True)
TMP=ROOT/'work/sequence_annotation_v2';TMP.mkdir(exist_ok=True)
FF=ROOT/'work/video_decoder/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
index=json.loads((T/'temporal_media_index.json').read_text())
bysha={r['sha256']:r for r in index}
batch=json.loads((T/'review_batch_01/batch_manifest.json').read_text())
oldhashes={r['source_sha256'] for r in batch}
tasks=[]
for cid in ['B004','B006','B007','B019','B020','B021','B022','B023']:
    prior=json.loads((T/'review_batch_01'/cid/'reviewed_events.json').read_text())
    s=prior['source'];r=bysha[s['source_sha256']]
    start=max(0,s['source_relative_start_s']-8)
    tasks.append(dict(id=cid,source=r,start_s=start,duration_s=min(32,r['probed_duration_s']-start),
                      prior=prior,role='development_only' if cid=='B019' else 'training_candidate',
                      selection='Existing difficult October sequence with additional before/after context'))
for day in ['2026-10-01','2026-10-21']:
    eligible=sorted([r for r in index if r['camera']==11 and r['date']==day and r['sha256'] not in oldhashes
                     and r['probed_duration_s']>=45],key=lambda r:r['filename_start'])
    for j in range(6):
        r=eligible[round((j+.5)*len(eligible)/6-.5)]
        start=max(0,r['probed_duration_s']*.5-10)
        tasks.append(dict(id=f'N{day[-2:]}_{j+1:02}',source=r,start_s=start,duration_s=20,
                          prior=None,role='training_candidate',selection='New source, time-stratified sample; contents not yet reviewed'))
assert len({t['source']['sha256'] for t in tasks})==len(tasks)
assert all(t['source']['date'] in ['2026-10-01','2026-10-21'] for t in tasks)
rows=[]
def run(args):
    p=subprocess.run([str(FF),'-hide_banner','-loglevel','error',*args],capture_output=True)
    if p.returncode:raise RuntimeError(p.stderr.decode(errors='replace')[-2000:])
for task in tasks:
    cid=task['id'];r=task['source'];dest=OUT/cid;dest.mkdir(exist_ok=True)
    a=dict(schema_version=2,clip_id=cid,source_sha256=r['sha256'],source_basename=r['basename'],date=r['date'],
           source_encoded_start_s=task['start_s'],duration_s=task['duration_s'],camera_clock_verified=False,
           role=task['role'],selection=task['selection'],expert_review_complete=False,
           eligible_for_training=False,exhaustive_event_coverage=False,whole_clip_added_blocks=None,
           review_questions=['Which separate whole blocks are picked up?',
            'When do those blocks leave the conveyor and travel with the hands?',
            'Which tank receives each block and when is it released?',
            'Is a movement rearrangement, separator handling, crumbs, or uncertain?',
            'Are any pickups/releases outside the clip or occluded?'],
           event_drafts=[],nonplacement_drafts=[],unresolved_drafts=[],new_events=[])
    prior=task['prior']
    if prior:
        offset=prior['source']['source_relative_start_s']-task['start_s']
        for e in prior.get('events',[]):
            a['event_drafts'].append(dict(event_id=e['event_id'],hand_group_hint=e.get('worker_track'),
                object_type='whole_feta_block',provisional_quantity=e.get('quantity'),expert_quantity=None,
                contact_interval_s=None,lift_interval_s=[v+offset for v in e['pickup_window_s']],
                transit_interval_s=None,release_interval_s=[v+offset for v in e['release_window_s']],
                destination='filling_tank',block_tracks=[],hand_tracks=[],verified_release=False,
                annotation_basis='Imported assistant draft; requires object-level and expert verification'))
        for key,target in [('non_placement_events','nonplacement_drafts'),('unresolved','unresolved_drafts')]:
            for e in prior.get(key,[]):
                item=dict(e)
                if 'window_s' in item:item['window_s']=[v+offset for v in item['window_s']]
                item['expert_confirmed']=False;a[target].append(item)
    # Keep user-reviewed semantics separate from regenerable assistant drafts.
    feedback_path=OUT/'expert_feedback.json'
    if feedback_path.exists():
        a['expert_confirmed_actions']=[e for e in json.loads(feedback_path.read_text(encoding='utf-8')) if e['clip_id']==cid]
        for confirmed in a['expert_confirmed_actions']:
            for draft in a['event_drafts']:
                if draft['event_id']==confirmed.get('supersedes_draft_event_id'):
                    draft.update(review_status='retracted_by_user',expert_quantity=confirmed['whole_feta_block_increment'],superseded_by=confirmed['event_id'],exclude_from_positive_training=True)
                elif draft['event_id']==confirmed.get('confirmed_draft_event_id'):
                    draft.update(expert_quantity=confirmed['whole_feta_block_increment'],quantity_confirmed_by=confirmed['event_id'])
            if confirmed['event_id']=='B007_user_left_two_blocks':
                for draft in a['nonplacement_drafts']:
                    if draft.get('action')=='adjust_existing_tank_contents' and draft.get('worker_track')=='filling_left':
                        draft.update(semantic_status='superseded_by_user_unrelated_gestures',superseded_by=confirmed['event_id'],expert_confirmed=False)
        for u in a['unresolved_drafts']:
            if cid=='B019' and u.get('worker_track')=='filling_right' and u.get('window_s')==[15.125,16.875] and any(e['event_id']=='B019_user_confirmed_salting' for e in a['expert_confirmed_actions']):
                u.update(semantic_resolution_event_id='B019_user_confirmed_salting',semantic_status='resolved_as_salting',timing_status='still_requires_frame_review')
    (dest/'annotation.json').write_text(json.dumps(a,indent=2),encoding='utf-8')
    if not (dest/'context.mp4').exists() or not (dest/'hands.mp4').exists():
        indexed=TMP/'indexed_source.mp4'
        run(['-y','-i',r['local_path'],'-map','0:v:0','-an','-c:v','copy',str(indexed)])
        # Keep temporal continuity and 16 fps; no inference labels are painted on video.
        run(['-y','-ss',str(task['start_s']),'-i',str(indexed),'-t',str(task['duration_s']),
             '-vf','scale=960:540,fps=16','-an','-c:v','libx264','-preset','veryfast','-crf','22','-threads','2',str(dest/'context.mp4')])
        run(['-y','-ss',str(task['start_s']),'-i',str(indexed),'-t',str(task['duration_s']),
             '-vf','crop=640:360:800:720,fps=16','-an','-c:v','libx264','-preset','veryfast','-crf','19','-threads','2',str(dest/'hands.mp4')])
    run(['-y','-ss',str(task['duration_s']/2),'-i',str(dest/'hands.mp4'),'-frames:v','1',str(dest/'middle.jpg')])
    rows.append({k:a[k] for k in ['clip_id','source_sha256','source_basename','date','source_encoded_start_s','duration_s','role','selection']})
    (OUT/'manifest.json').write_text(json.dumps(rows,indent=2))
    print(f"Prepared {cid}: {len(rows)}/{len(tasks)}",flush=True)
for page in range((len(rows)+7)//8):
    sheet=Image.new('RGB',(1280,4*390),'white');draw=ImageDraw.Draw(sheet)
    for j,r in enumerate(rows[page*8:(page+1)*8]):
        x=j%2*640;y=j//2*390
        sheet.paste(Image.open(OUT/r['clip_id']/'middle.jpg'),(x,y+30))
        draw.text((x+6,y+8),f"{r['clip_id']} | {r['date']} | {r['role']} | UNVERIFIED",fill='black')
    sheet.save(OUT/f'overview_{page+1}.jpg')
report=dict(clips=len(rows),new_source_clips=12,expanded_existing_clips=8,
    duration_s=sum(r['duration_s'] for r in rows),dates=dict(collections.Counter(r['date'] for r in rows)),
    september_test_used=False,october3_evaluation_used=False,training_started=False,
    clips_expert_verified=0,training_eligible_clips=0,
    known_gaps=['No independently verified single-block or crumb-disposal labels yet',
      'Existing paired-block annotations must not imply a fixed quantity per gesture',
      'Per-object trajectories and release boundaries remain to be annotated'])
(OUT/'preparation_report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2),flush=True)
