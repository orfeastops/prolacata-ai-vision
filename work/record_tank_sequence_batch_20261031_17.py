"""Record completed visual review, including one13Oct full-cycle annotation.

Source pixels, visible clock intervals and retained occlusions support labels.
6Oct remains partial; no training, synthetic detections or test inspection.
"""
import copy,datetime as dt,hashlib,json
from pathlib import Path
from record_tank_boundary_review_20261031 import read,save,merge,evidence
ROOT=Path(__file__).resolve().parents[1]; BASE=ROOT/'outputs/tank_transfer_training_v1'; OUT=BASE/'dataset_v1'
RUN='sequence_review_20261031_17'

def main():
 state=read(OUT/'continuation_state.json')
 if RUN in state.get('completed_curation_runs',[]): print('Already recorded',RUN); return
 stamp=dt.datetime.now(dt.timezone.utc).isoformat()
 windows={
  'scale6':('20261006','blue_scale_1131_cam15',11),
  'storage6':('20261006','blue_storage_1134_cam15',16),
  'after6':('20261006','blue_storage_followup_1135_cam15',15),
  'clear6':('20261006','blue_scale_clearance_1133_cam11',60),
  'entry13':('20261013','earlier_entry_0906_cam15',39),
  'route13':('20261013','earlier_cycle_0908_cam15',59),
  'origin13':('20261013','earlier_origin_0903_cam11',90),
  'depart13':('20261013','earlier_departure_boundary_0907_cam11',36),
  'cross13':('20261013','earlier_entry_boundary_0907_cam15',21),
  'join13':('20261013','earlier_scale_join_0908_cam15',33),
  'store13':('20261013','earlier_storage_boundary_0913_cam15',43),
 }
 paths={k:OUT/'sequence_review'/d/w/'frames.json' for k,(d,w,n) in windows.items()}
 metas={k:read(p) for k,p in paths.items()}
 for k,m in metas.items():
  assert len(m['samples'])==windows[k][2] and m['source']['date']==windows[k][0] and m['source']['split']=='train'
  assert all((ROOT/s['image']).exists() for s in m['samples'])
 # Clock values manually read in the reviewed images, not converted from PTS.
 clocks={
  'scale6':{0:'11:31:05',1:'11:31:18',2:'11:31:20',5:'11:31:26',9:'11:31:34',10:'11:31:36'},
  'storage6':{0:'11:34:23',1:'11:34:30',2:'11:34:31',4:'11:34:33',5:'11:34:34',9:'11:34:38',10:'11:34:39',11:'11:34:40',15:'11:34:44'},
  'after6':{0:'11:34:55',1:'11:35:02',5:'11:35:06',8:'11:35:09',13:'11:35:14',14:'11:35:15'},
  'clear6':{0:'11:29:20',6:'11:29:56',7:'11:30:02',8:'11:30:08',11:'11:30:26',19:'11:31:14',23:'11:31:38',40:'11:33:20',41:'11:33:26',42:'11:33:32',43:'11:33:38',51:'11:34:26',59:'11:35:14'},
  'entry13':{0:'09:06:31',1:'09:06:38',5:'09:06:50',11:'09:07:08',12:'09:07:11',16:'09:07:23',18:'09:07:29',19:'09:07:32',20:'09:07:35',21:'09:07:38',29:'09:08:02',36:'09:08:23',37:'09:08:26',38:'09:08:29'},
  'route13':{0:'09:08:21',1:'09:08:39',4:'09:09:03',5:'09:09:11',6:'09:09:19',12:'09:10:07',19:'09:11:03',27:'09:12:07',28:'09:12:15',29:'09:12:23',30:'09:12:32',34:'09:13:04',35:'09:13:12',36:'09:13:20',37:'09:13:28',38:'09:13:36',41:'09:14:00',58:'09:16:16'},
  'origin13':{0:'09:03:03',1:'09:03:20',6:'09:04:00',14:'09:05:04',21:'09:06:00',23:'09:06:16',24:'09:06:24',29:'09:07:04',30:'09:07:12',31:'09:07:20',32:'09:07:28',33:'09:07:36',34:'09:07:44',35:'09:07:52',39:'09:08:24',40:'09:08:32',41:'09:08:40',43:'09:08:56',44:'09:09:04',45:'09:09:12',68:'09:12:16',69:'09:12:24',70:'09:12:32',78:'09:13:36',79:'09:13:44',89:'09:15:04'},
  'depart13':{0:'09:07:12',1:'09:07:13',2:'09:07:14',5:'09:07:17',6:'09:07:18',8:'09:07:20',9:'09:07:21',11:'09:07:23',14:'09:07:26',16:'09:07:28',18:'09:07:30',20:'09:07:32',21:'09:07:33',22:'09:07:34',23:'09:07:35',24:'09:07:36',25:'09:07:37',26:'09:07:38',32:'09:07:44',35:'09:07:47'},
  'cross13':{0:'09:07:25',3:'09:07:28',5:'09:07:30',6:'09:07:31',7:'09:07:32',8:'09:07:33',9:'09:07:34',10:'09:07:35',11:'09:07:36',12:'09:07:37',13:'09:07:38',14:'09:07:39',15:'09:07:40',20:'09:07:45'},
  'join13':{0:'09:08:21',1:'09:08:33',2:'09:08:35',3:'09:08:37',4:'09:08:39',7:'09:08:45',12:'09:08:55',14:'09:08:59',15:'09:09:01',16:'09:09:03',17:'09:09:05',18:'09:09:07',19:'09:09:09',20:'09:09:11',24:'09:09:19',25:'09:09:22',28:'09:09:27',32:'09:09:36'},
  'store13':{0:'09:12:11',5:'09:12:21',6:'09:12:23',7:'09:12:25',8:'09:12:27',9:'09:12:29',10:'09:12:31',12:'09:12:35',18:'09:12:47',24:'09:12:59',25:'09:13:01',26:'09:13:03',27:'09:13:05',28:'09:13:07',29:'09:13:09',30:'09:13:11',31:'09:13:13',32:'09:13:16',33:'09:13:17',34:'09:13:19',35:'09:13:22',36:'09:13:23',37:'09:13:25',38:'09:13:27',39:'09:13:29',40:'09:13:31',41:'09:13:34',42:'09:13:35'},
 }
 notes={
  'scale6':'Blue-lined gray tank stays on scale at far right31:18-36; operator handles it. Separate person walks toward shared doorway31:26-34 without a tank. Three foreground blue containers are stationary, not the scale tank. Source-initial31:05 is stale.',
  'storage6':'First usable34:30 already shows gray blue-lined tank left of stationary foreground bins, off scale. Operator pulls into aisle30-33, turns34-38 and pushes toward storage row39-44. Fork release not reached. Same-load identity from31-minute scale visit is not established across the missing approach interval. Initial34:23 excluded for timing.',
  'after6':'Initial34:55 is stale. First usable35:02 shows tank already parked in row; operator takes unloaded manual jack back toward door02-09. Parked tank stationary through15.18-second gap from preceding34:44 to35:02 prevents exact release-time annotation.',
  'clear6':'View through11 doorway: platform empty29:20-56, blue-lined gray tank drawn onto scale30:02-08, settled30:26, stays until33:26, pulled off33:32 and platform empty33:38. Next15 storage view starts34:30, leaving52 seconds without reviewed route. New station replacement is initially empty and is being filled; no fresh departure in this window.',
  'entry13':'Operator takes unloaded jack toward shared doorway06:50-07:08. Two low empty gray tanks return15-to11 at07:11-23. Separate fresh gray load enters15 around07:31-37, then stays staged left of door with cover/liner work through08:23. It moves right slightly08:26-29 but has NOT reached scale yet. Last sampled camera clock08:29 exceeds filename end08:21; source clock/PTS preserved separately.',
  'route13':'Initial08:21 frame stale. First usable08:39 shows operator near staging then clearing scale area08:43-47. Tank stays left of doorway until drawn onto scale09:01-11. Scale dwell continues until12:23, clears12:25-31. Same tank waits partly behind foreground bins, emerges into aisle13:05-13, is pushed into front edge of rear storage group13:16-22, then empty forks withdrawn13:23-25. Parked tank remains through16:16. Tin/package handling elsewhere is not new production entry.',
  'origin13':'Fresh placements into gray filling-station tank03:20-06:16, covering06:24. First observed fill already underway; initial amount unknown. Tank pulled07:26-28 and crosses doorway07:33-37. Two separate empty returns07:17-23; one moves locally into station07:34-44 and then begins filling07:52 onward. Through doorway scale is empty08:24 and08:40-56; fresh load reaches scale09:04-12, leaves12:24, platform clear12:32. Empty jack returns13:36-44; later floor hosing does not move a tank.',
  'depart13':'Dense1-second frames show unloaded jack returning07:13-18, two separate low empty gray tanks crossing15-to11 at07:17-21 then moved left. Covered freshly filled station load pulled07:26-28, crosses shared door07:33-36 and gone07:37. Internal replacement07:34-44 is one of the returned empty tanks, not another production event.',
  'cross13':'Dense1-second15 frames show unique arriving gray load behind operator07:31-34; crosses behind foreground bins and settles left of door07:35-39. Body is partly occluded. Retain room15 entry07:31-37, paired with11 crossing07:33-37; no exact scalar clock offset asserted. Room11 background empty replacement is a different tank.',
  'join13':'Stale initial08:21 ignored. First noninitial08:33 shows same low gray load in staging left of door, compatible with preceding08:29 position;4-second sampled join retained. Operator removes/adjusts small scale-area item08:43-47 while tank stays staged. Tank moves09:01-11 onto scale, remains09:13-36. Earlier08:26-29 rightward movement was staging, not scale dwell.',
  'store13':'Continuous2-second sampled route: scale tank stationary12:11-23, pulled left12:25-29, platform clear12:31. Tank pauses partly behind fixed bins12:31-13:03. Same cover/body emerges13:05-13, turns and pushes into front edge of rear group13:16-22. Empty jack withdrawal13:23-25 confirms placement; returns toward shared doorway13:27-35. No second crossing or replacement occurs during this track.',
 }
 for k,m in metas.items():
  initial= m['requested_window']['start']==0
  review=dict(review_id=windows[k][0]+'/'+windows[k][1],reviewed_at=stamp,reviewer='assistant_visual_review',source_member=m['source']['member'],source_sha256=m['source_sha256'],date=windows[k][0],camera=m['source']['camera'],split='train',frames_manifest=str(paths[k].relative_to(ROOT)),sampled_frames_visually_reviewed=len(m['samples']),reviewed_sheets=m['sheets'],review_scope='All chronological contact-sheet samples visually inspected; selected native frames and separate detection overlays reviewed. Sampled presentations are not exhaustive native-frame viewing.',observation=notes[k],accepted_complete_cycle=False,clock_warning='Source-initial stale anchors excluded. Visible clock intervals retained; filenames and decoder PTS do not establish synchronization.',visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],visible_camera_clock=t,clock_read_uncertainty_seconds=1,image=m['samples'][i]['image'],usable_for_clock_alignment=not(initial and i==0)) for i,t in clocks[k].items()])
  merge(OUT/'screening_source_reviews.json',[review],'review_id')
 def ev(k,a,b): return evidence(metas[k],a,b,paths[k])
 shared=dict(split='train',reviewer='assistant_visual_review',reviewed_at=stamp,dataset_release_accepted=False)
 def neg(ident,day,cam,cls,times,proof,note,scope,tanks):
  return dict(shared,sequence_id=ident,date=day,camera=cam,camera_track_id=ident,cycle_id=None,review_status='accepted_negative_sequence',production_entry_count_target=0,negative_class=cls,tracked_tank_count=tanks,visible_camera_clock_interval=times,clock_uncertainty_seconds=3,evidence=proof,observation=note,label_scope=scope)
 additions=[
  neg('20261006_empty_manual_jack_1135','20261006',15,'pallet_jack_without_tank',['11:35:02','11:35:09'],[ev('after6',1,8)],'Manual jack returns without tank; storage-row tank remains parked.','Only visible unloaded return. The preceding placement and its origin identity remain unresolved.',0),
  neg('20261013_two_empty_returns_0907','20261013',15,'empty_crossing',['09:07:11','09:07:23'],[ev('entry13',12,16),ev('depart13',5,11),ev('depart13',22,32)],'Two empty low gray tanks return together15-to11; same episode includes subsequent local replacement of one at station.','Two physical empty tank tracks in one return episode, zero new production entries. Fresh loaded departure and later filling are excluded from this negative scope.',2),
  neg('20261013_empty_jack_after_storage_0913','20261013',15,'pallet_jack_without_tank',['09:13:23','09:13:44'],[ev('store13',36,42),ev('route13',37,38),ev('origin13',78,79)],'Visible unloaded fork withdrawal from newly parked gray tank then return through shared door.','Only unloaded jack. The newly stored tank belongs to its own positive cycle; it is not a second entry.',0),
 ]
 cycle=dict(shared,sequence_id='20261013_gray_filling_to_storage_0907',date='20261013',review_status='accepted_complete_cycle',cycle_id='20261013_gray_0907',camera_track_id={'11':'gray_station_0903_0907','15':'gray_entry_scale_storage_0907_0913'},cross_camera_identity='assistant_visual_correspondence_reviewed_with_occlusion',clock_alignment='shared_crossing_visually_checked_timestamp_uncertainty_retained',camera_clock_offset_seconds=None,entry_camera=15,entry_clock_interval=['09:07:31','09:07:37'],production_entry_count_target=1,origin_content='Fresh cheese placement observed into station tank before covering; the cover alone is not the content evidence.',counting_rule='One increment at15 entry, finalized by subsequent reviewed scale visit and storage. Empty returns, scale clearance and final placement do not increment.',stages=[
  dict(stage='filling_observed',visible_camera_clock_interval=['09:03:20','09:06:16'],clock_uncertainty_seconds=8,content_evidence='Fresh cheese placements into station tank, followed by cover06:24; initial contents and quantity unknown.',evidence=[ev('origin13',1,24)]),
  dict(stage='loaded_departure_11',visible_camera_clock_interval=['09:07:26','09:07:37'],doorway_crossing_camera11_interval=['09:07:33','09:07:37'],clock_uncertainty_seconds=1,evidence=[ev('origin13',24,34),ev('depart13',14,25)]),
  dict(stage='entry_15',visible_camera_clock_interval=['09:07:31','09:07:37'],clock_uncertainty_seconds=3,timestamp_precision='interval_only',occlusion='Operator, doorway post and fixed foreground bins partly occlude tank.',correspondence_basis='Same freshly filled low gray tank with white top, same manual-jack path and unique shared crossing after the separate two-empty-return episode. No numeric offset fitted.',evidence=[ev('cross13',6,14),ev('depart13',20,25),ev('entry13',18,29)]),
  dict(stage='scale_visit',visible_camera_clock_interval=['09:09:01','09:12:31'],scale_approach_interval=['09:09:01','09:09:11'],scale_departure_clock_interval=['09:12:23','09:12:31'],clock_uncertainty_seconds=2,numeric_weight_kg=None,measurement_success_verified=False,source_join_review=dict(preceding_visible_clock='09:08:29',next_noninitial_sample_clock='09:08:33',sampled_join_uncertainty_seconds=4,rejected_alignment_anchor='Initial next-source frame reads09:08:21, stale.',identity_evidence='Same low gray tank stays in staging next to left doorpost before and after join; operator and jack remain with it, then observed scale approach. No new entry or tank replacement between these samples.',coverage_caveat='4-second sampled join, not continuous visibility of every native frame.'),evidence=[ev('entry13',21,38),ev('join13',1,32),ev('route13',5,30),ev('origin13',39,70),ev('store13',0,10)]),
  dict(stage='storage_placement',visible_camera_clock_interval=['09:13:05','09:13:25'],clock_uncertainty_seconds=2,parked_and_jack_withdrawal_interval=['09:13:22','09:13:25'],location='Front edge of rear gray stored-tank group, left of shared doorway.',confirmation='Tank routed from scale through occluded staging and into row; forks visibly withdrawn and tank remains stationary through09:16:16.',evidence=[ev('store13',7,42),ev('route13',34,58)]),
 ],limitations=['Assistant-reviewed source annotation, not a model prediction or independently certified production total.','Initial filling has already begun; no starting contents, block total or measured kilograms inferred.','Door/staging occlusions retained. Timing is camera-local intervals, not an exact cross-camera synchronization.','Adjacent source has stale initial image and4-second sampled join; no missing native frames fabricated.','Complete means all required stages evidenced with these limitations. Overall dataset release/coverage remains incomplete.'])
 additions.append(cycle)
 oldlabels=read(OUT/'reviewed_sequence_labels.json'); blue=copy.deepcopy(next(r for r in oldlabels if r['sequence_id']=='20261006_fresh_blue_departure_partial_1129'))
 h=OUT/'review_history/blue1129_before_20261031_17.json'
 if not h.exists(): save(h,blue)
 blue['prior_annotation']=str(h.relative_to(ROOT)); blue['reviewed_at']=stamp
 blue['partial_reason']='Fresh filling/departure observed, but direct15 entry missing. Later scale and storage context reviewed; trajectory identity still unresolved across52-second scale-to-storage and18-second final-placement gaps.'
 blue['unlinked_followup'].update(status='scale_storage_followup_reviewed_identity_gaps',observation='Candidate blue-lined tank on15 scale31:18-36. Camera11 sees scale clearance33:32-38.15 next usable34:30 already shows tank off scale; storage approach34:39-44 and parked row by35:02, empty jack returns02-09. No direct15 entry or continuous identity bridge. No exact placement time inferred.',scale_departure_camera11_interval=['11:33:26','11:33:38'],storage_approach_camera15_interval=['11:34:39','11:34:44'],parked_by_camera15='11:35:02',storage_identity_to_fresh_origin='unresolved',evidence=blue['unlinked_followup']['evidence']+[ev('scale6',1,10),ev('clear6',6,43),ev('storage6',1,15),ev('after6',1,14)])
 additions.append(blue); merge(OUT/'reviewed_sequence_labels.json',additions,'sequence_id')
 queue=read(OUT/'sequence_followup_queue.json'); prior=next(r for r in queue if r['candidate_id']=='20261006_blue_1129_entry_storage_gap')
 h=OUT/'review_history/blue1129_queue_before_20261031_17.json'
 if not h.exists(): save(h,prior)
 prior.update(status='partial_entry_and_storage_identity_gap',reviewed_at=stamp,prior_annotation=str(h.relative_to(ROOT)),observation=blue['partial_reason'],next_action='Later1131/1134/1135 context now reviewed. Do not repeat extraction. Only new media or independently validated identity can resolve28:56 entry,33:38-34:30 route and34:44-35:02 placement gaps.',new_evidence=blue['unlinked_followup']['evidence'])
 save(OUT/'sequence_followup_queue.json',queue)
 save(OUT/'gap_search_20261031_17.json',dict(reviewed_at=stamp,date='20261006',split='train',method='Read existing archive inventory only; no test pixels.',findings=['Beige1120:15 files end11:19:57 then resume11:21:41(initial)/21:43 usable; no direct20:48 entry bridge found.','Blue1129:preceding15 usable ends11:28:53; next first usable11:30:01, with stale11:29:40 initial. No direct crossing bridge found.','Newly inspected11 scale clears11:33:38; next15 usable11:34:30.52-second trajectory gap retained.','Storage approach last11:34:44 then next15 usable11:35:02.18-second gap; actual fork release not observed.'],action='Keep6Oct sequences partial. Stop repeating these same gap searches without new sources.'))
 registry=read(OUT/'object_review_decisions.json'); h=OUT/'review_history/object_decisions_before_20261031_17.json'
 if not h.exists(): save(h,registry)
 decisions={r['id']:r for r in registry['reviews']}; draft={r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
 roi_notes={'147':'Single fresh departing gray tank in aisle. Generic box only; load state belongs to temporal annotation.','148':'Two distinct empty gray return tanks, separately boxed. Empty evidence in temporal label, not a detection-class change.','150':'Departing gray tank at doorway, partly occluded by right doorpost. Generic box covers identifiable tank extent.'}
 for ident,note in roi_notes.items():
  assert ident not in decisions; r=draft[ident]
  decisions[ident]=dict(id=ident,image_sha256=r['sha256'],boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',load_state_reviewed=False,sequence_reviewed=False,instance_attributes=[dict(box_index=j,truncated=False,occluded=(ident!='147'),load_state='unknown_not_annotated') for j,b in enumerate(r['boxes_xyxy'])],evidence=[r['source_frame'],r['frames_manifest'],'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_16.jpg'],note=note)
 registry['reviews']=list(decisions.values()); exclusions={r['id']:r for r in registry.get('excluded_roi_reviews',[])}
 for ident in ('146','149','151'):
  r=draft[ident]; exclusions[ident]=dict(id=ident,image_sha256=r['sha256'],reviewed_at=stamp,reviewer='assistant_visual_review',decision='exclude_whole_roi_not_an_empty_image',reason='Identifiable main tank but uncertain cropped/overlapping storage-row fragments. Entire image excluded; not an empty-image label.',evidence=[r['image'],r['source_frame'],r['frames_manifest']])
 registry['excluded_roi_reviews']=list(exclusions.values()); registry.setdefault('corrections',[]).append('Batch17:147/148/150 accepted after separate overlay16 review,4 boxes.146/149/151 excluded due uncertain background fragments. Previous reviewed decisions unchanged.'); save(OUT/'object_review_decisions.json',registry)
 inv=read(BASE/'archive_inventory.json'); inspected={m['source']['member']:m['source_sha256'] for m in metas.values()}
 for r in inv['records']:
  if r['member'] in inspected:r.update(pixel_inspected=True,sha256=inspected[r['member']])
 assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test'); save(BASE/'archive_inventory.json',inv)
 reviews=read(OUT/'screening_source_reviews.json'); total=sum(r['sampled_frames_visually_reviewed'] for r in reviews)
 state['last_completed'] += [
  f'Batch17 inspected423 chronological sample presentations in11 windows on6/13Oct; {total} total across{len({r["source_sha256"] for r in reviews})} sources and{len(reviews)} windows. All extraction finished;25/28Oct untouched.',
  'Third complete cycle accepted:13Oct fresh gray fill/departure,15 entry09:07:31-37, scale09:09:01-12:31 and storage13:05-25. Dense boundary/route review preserves occlusions and4-second source join; no scalar clock offset or measured weight inferred.',
  '6Oct blue1129 partial refined with later scale/storage context; direct entry and52-second route/18-second release gaps remain. Prior annotation and followup queue versions archived. Three track-scoped negatives added(two-empty return13Oct, unloaded jack returns6/13Oct). Totals3 complete,40 negative,15 partial.',
  'Six native ROI candidates146-151 appended.147/148/150 accepted with4 boxes;146/149/151 excluded for background ambiguity. Totals152 candidates,102 approved images,155 boxes,50 exclusions,zero unresolved drafts. Training remains unreleased.'
 ]
 state['priority_next']=[
  'Batch17 all11 new6/13Oct windows recorded.13Oct0907 gray is accepted complete; no need to re-inspect its full route.3 complete cycles, all13Oct; need more day diversity and true post-storage relocation/same-load reentry negatives.',
  '6Oct1129 now has reviewed1131 scale/1134 storage/1135 empty-jack context, still partial. Missing28:56 entry,33:38-34:30 trajectory and34:44-35:02 release are documented in gap_search_20261031_17.json. Do not repeat searches in unchanged media.',
  '13Oct subsequent091619-092224 and102139-102912 long15 windows remain unreviewed. The11 source090303-092241 was inspected only through09:15:04; later departure may have full paired coverage. Prioritize full overlap windows on other training days when available.',
 ]+[p for p in state['priority_next'] if p.startswith('Known gaps') or p.startswith('25/28')]
 state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False); state.setdefault('completed_curation_runs',[]).append(RUN)
 state['scripts'] += [s for s in ['work/append_tank_roi_batch_20261031_17.py','work/record_tank_sequence_batch_20261031_17.py'] if s not in state['scripts']]
 save(OUT/'continuation_state.json',state)
 print(json.dumps(dict(recorded=RUN,additional_temporal_samples=423,additional_complete_cycles=1,additional_negatives=3,total_presentations=total,training_started=False)))

if __name__=='__main__':main()
