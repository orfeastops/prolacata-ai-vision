import datetime as dt
from record_tank_boundary_review_20261031 import read,save,merge,evidence,ROOT,BASE,OUT
run='sequence_review_20261101_75'
state=read(OUT/'continuation_state.json')
if run in state.get('completed_curation_runs',[]):raise SystemExit('Already recorded')
stamp=dt.datetime.now(dt.timezone.utc).isoformat()
windows=[
 ('follow133745_cam11',['13:37:45','13:38:09','13:38:14','13:38:19','13:38:24','13:38:29','13:38:34'],'Worker walks from doorway to rear wall fixtures and returns. Open left-wall tank remains stationary; tank beyond doorway partly visible. No new filling or sampled tank crossing.'),
 ('follow133910_cam11',['13:39:10','13:39:17','13:39:22','13:39:27','13:39:32','13:39:37','13:39:42','13:39:47','13:39:52','13:39:57'],'Worker handles hose at rear wall and returns toward doorway. Left-wall tank stationary, another tank partly visible through doorway. No sampled tank transport or fresh filling.'),
 ('follow134140_cam11',['13:41:40','13:41:58','13:42:03','13:42:08','13:42:13','13:42:18','13:42:23','13:42:28','13:42:33'],'Unloaded pallet jack brought from doorway into room11 and parked beside left-wall tank; both forks visibly unloaded. Workers then attend right-wall hose/foreground machinery. No fresh fill or new productive entry. Earlier tank beyond doorway no longer visible; disappearance across unobserved interval is not a matched movement.')]
inv=read(BASE/'archive_inventory.json')
for name,clocks,obs in windows:
 p=OUT/'sequence_review/20261015'/name/'frames.json';m=read(p);assert len(m['samples'])==len(clocks)
 merge(OUT/'screening_source_reviews.json',[dict(review_id='20261015/'+name,date='20261015',split='train',camera=11,reviewer='assistant_visual_review',reviewed_at=stamp,source_member=m['source']['member'],source_sha256=m['source_sha256'],frames_manifest=str(p.relative_to(ROOT)),sampled_frames_visually_reviewed=len(clocks),reviewed_sheets=m['sheets'],accepted_complete_cycle=False,review_scope='All chronological full-field-of-view sample tiles and clock strips inspected; not exhaustive native frames.',observation=obs+' Initial clock anomaly retained; PTS not used as wall-clock or camera synchronization.',visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=s['source_pts_seconds'],relative_pts_seconds=s['relative_pts_seconds'],visible_camera_clock=clocks[i],clock_read_uncertainty_seconds=1,image=s['image'],usable_for_clock_alignment=False) for i,s in enumerate(m['samples'])])],'review_id')
 for r in inv['records']:
  if r['member']==m['source']['member']:r.update(pixel_inspected=True,sha256=m['source_sha256'])
labels=read(OUT/'reviewed_sequence_labels.json');save(OUT/'review_history/sequence_labels_before_20261101_75.json',labels)
labels.append(dict(sequence_id='20261015_emptyjack1342_cam11',date='20261015',split='train',camera=11,reviewer='assistant_visual_review',reviewed_at=stamp,review_status='accepted_negative_sequence',cycle_id=None,production_entry_count_target=0,dataset_release_accepted=False,negative_class='pallet_jack_without_tank',tracked_tank_count=0,visible_camera_clock_interval=['13:41:58','13:42:13'],label_scope='Unloaded manual pallet jack track only; stationary tanks and off-camera activity excluded.',observation='Both unloaded forks visible as worker brings jack from doorway across aisle and parks beside stationary left-wall tank.',evidence=[evidence(m,1,4,p)]))
save(OUT/'reviewed_sequence_labels.json',labels);save(BASE/'archive_inventory.json',inv)
state['last_completed'].append('Batch75:26 new full-field sample tiles reviewed in three15Oct camera11 windows through13:42:33. One unloaded manual-jack negative added; no new complete cycle. Full-context batch74 did not increase sample counts.')
state['priority_next']=['Continue15Oct camera11 next inventoried source13:42:39-13:43:10 and later files. Reviewed through13:42:33; no fresh fill in these follow-up windows. Preserve unobserved gaps.']+[x for x in state['priority_next'] if x.startswith('25/28')]
state['completed_curation_runs'].append(run);state['updated_at']=stamp;save(OUT/'continuation_state.json',state)
