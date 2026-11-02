"""Record visually inspected5/6Oct sequences and native ROI overlay decisions.

No missing stage or load content is inferred. All annotations stay unreleased.
"""
import datetime as dt
import hashlib,json
from pathlib import Path
from record_tank_boundary_review_20261031 import read,save,merge,evidence
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/tank_transfer_training_v1';OUT=BASE/'dataset_v1'
RUN='sequence_review_20261031_14'

def main():
 state=read(OUT/'continuation_state.json')
 if RUN in state.get('completed_curation_runs',[]):print('Already recorded',RUN);return
 stamp=dt.datetime.now(dt.timezone.utc).isoformat()
 windows={
  'five':('20261005','activity_1044_cam15',29),
  'stacks15':('20261006','activity_0943_cam15',43),
  'origin':('20261006','forklift_context_0942_cam11',50),
  'departure':('20261006','loaded_followup_0945_cam11',68),
  'staging':('20261006','blue_entry_0946_cam15',16),
  'entry':('20261006','blue_entry_prior_0945_cam15',43),
  'scale':('20261006','blue_scale_0946_cam15',24),
  'storage':('20261006','blue_storage_0951_cam15',17),
 }
 paths={k:OUT/'sequence_review'/v[0]/v[1]/'frames.json' for k,v in windows.items()}
 metas={k:read(p) for k,p in paths.items()}
 for k,m in metas.items():
  assert len(m['samples'])==windows[k][2] and m['source']['date']==windows[k][0] and m['source']['split']=='train'
  assert all((ROOT/s['image']).exists() for s in m['samples'])
 clocks={
  'five':{0:'10:44:22',1:'10:44:38',2:'10:44:41',4:'10:44:47',7:'10:44:56',8:'10:44:59',11:'10:45:08',13:'10:45:14',17:'10:45:26',20:'10:45:35',22:'10:45:40',25:'10:45:49',28:'10:45:58'},
  'stacks15':{0:'09:43:06',1:'09:43:13',3:'09:43:19',5:'09:43:25',8:'09:43:34',12:'09:43:46',15:'09:43:55',27:'09:44:31',30:'09:44:40',31:'09:44:43',32:'09:44:46',35:'09:44:55',36:'09:44:58',38:'09:45:04',42:'09:45:16'},
  'origin':{0:'09:42:15',5:'09:42:35',12:'09:43:03',13:'09:43:07',14:'09:43:11',15:'09:43:16',24:'09:43:51',25:'09:43:55',26:'09:43:59',33:'09:44:27',34:'09:44:31',35:'09:44:35',36:'09:44:40',45:'09:45:16',46:'09:45:20',49:'09:45:32'},
  'departure':{0:'09:45:35',2:'09:45:46',6:'09:46:06',7:'09:46:10',8:'09:46:16',9:'09:46:21',10:'09:46:26',11:'09:46:31',18:'09:47:06',21:'09:47:21',23:'09:47:31',30:'09:48:06',39:'09:48:51',45:'09:49:21',52:'09:49:56',65:'09:51:01',66:'09:51:06',67:'09:51:11'},
  'staging':{0:'09:46:06',1:'09:46:26',5:'09:46:30',10:'09:46:35',15:'09:46:40'},
  'entry':{0:'09:45:40',1:'09:45:42',5:'09:45:46',10:'09:45:51',15:'09:45:56',19:'09:46:00',25:'09:46:06',30:'09:46:11',32:'09:46:13',34:'09:46:15',35:'09:46:16',36:'09:46:17',37:'09:46:18',38:'09:46:19',39:'09:46:20',40:'09:46:21',41:'09:46:22',42:'09:46:23'},
  'scale':{0:'09:46:30',1:'09:46:52',4:'09:46:58',5:'09:47:00',6:'09:47:02',7:'09:47:04',8:'09:47:06',9:'09:47:08',10:'09:47:10',11:'09:47:12',12:'09:47:14',13:'09:47:16',18:'09:47:26',20:'09:47:30',23:'09:47:36'},
  'storage':{0:'09:51:38',1:'09:51:51',2:'09:51:52',3:'09:51:52',4:'09:51:54',5:'09:51:54',6:'09:51:56',7:'09:51:57',8:'09:51:57',9:'09:51:59',10:'09:52:00',11:'09:52:00',12:'09:52:02',13:'09:52:03',14:'09:52:03',15:'09:52:05',16:'09:52:05'},
 }
 notes={
  'five':'Room15 has many starting tanks, including inverted gray upper tanks on beige lower tanks. Operator pushes one such pair internally44:38-47. Upper inverted tank is empty; lower contents are occluded and not inferred. Unloaded powered pallet jack moves44:56-45:08. Apron-clad person walks from doorway without a tank44:59-45:14; another person walks to and from doorway45:26-49 without a tank. These actions do not establish a production entry. No matching camera11 export found at this interval. First source frame44:22 is stale; first usable44:38.',
  'stacks15':'Forklift brings two stacks through11-to15 door: beige inverted upper over gray upright lower43:13-19, then gray inverted upper over gray lower44:31-43. Stacks move to foreground. Inverted upper tanks are empty; lower contents and origin remain unknown. The forklift returns unloaded43:46-55 and45:04-16. Other workers handle covers on already-present row tanks. No whole-room zero label. First source image43:06 is stale.',
  'origin':'A blue-lined cheese tank remains at filling station while forklift stacks pass from left of room11 crop through the doorway. First beige-over-gray stack43:03-16, second gray-over-gray44:27-35. Neither is picked up from the active filling station. Upper tanks are inverted; lower contents not visible. Unloaded forklift returns42:35,43:55-59 and45:16-20. Empty blue-lined replacement waits locally left; separate scrap receptacle stays right. This is a bounded middle window of a long source; first sample42:15 is a valid chronology sample, not a source-start alignment anchor.',
  'departure':'Fresh blue-lined station tank is filled then covered by46:06, pulled away46:10 and crosses door46:16-21. Separate empty blue-lined replacement moves from local left waiting area to station46:16-26, with filling resumed46:31. The departed tank approaches scale47:06-21, remains on platform through51:01, starts departure51:06 and clears by51:11. Further forklift stacks45:46,48:06,49:21 and unloaded returns are distinct from this production load. Original filling start and cheese amount unknown; no kilograms inferred.',
  'staging':'First usable46:26 shows newly arrived blue-lined tank staged just left of the doorway, with operator handling liner/fittings through46:40. Actual entry is in the preceding reviewed source. Initial46:06 frame is stale. The adjacent scale source begins with usable46:52, leaving12 seconds of staging unobserved; compatible tank/location retained with this limitation.',
  'entry':'Native sampled sequence45:42-46:23. Forklift carries an inverted beige upper over gray lower tank45:46-46:13; that stack is separate from fresh load. Apron operator comes through doorway46:13-16 and draws blue-lined station tank through46:16-21, then stages it left of door by46:23. Doorpost/person and stationary bins occlude parts of crossing. Entry is bracketed46:13-21, not assigned an invented exact second. Camera11 contemporaneous station departure and15 entry order support correspondence; no exact clock offset calibrated.',
  'scale':'First usable46:52 after stale46:30. Blue-lined tank remains left-of-door staging through47:04, then operator draws it rightward across doorway toward platform47:06-12; platform occupied by47:14-16. Operator adjusts liner/fittings through47:36. Forklift passes back unloaded47:26-30, a separate track.12-second gap from earlier46:40 staging retained, though no competing same-position exchange observed in available samples.',
  'storage':'Initial51:38 image is stale. First usable51:51 already shows a blue-lined gray-body tank near back row, away from scale. Operator pulls it toward centre51:52-54, turns51:56-59 and pushes it leftward into back storage-row position52:00-05. Fork/jack withdrawal is not visible before source end. Camera11 scale departure51:06-11 is separated by40 seconds from first usable51:51; do not assert this is the same fresh load. Repeated displayed seconds kept literally, not inferred from PTS.',
 }
 reviews=[]
 for k,m in metas.items():
  reviews.append(dict(review_id=windows[k][0]+'/'+windows[k][1],reviewed_at=stamp,reviewer='assistant_visual_review',source_member=m['source']['member'],source_sha256=m['source_sha256'],date=windows[k][0],camera=m['source']['camera'],split='train',frames_manifest=str(paths[k].relative_to(ROOT)),sampled_frames_visually_reviewed=len(m['samples']),reviewed_sheets=m['sheets'],review_scope='Every chronological contact-sheet sample inspected. Selected full native frames and separate ROI overlays also inspected. Not exhaustive native-frame viewing.',visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],visible_camera_clock=t,clock_read_uncertainty_seconds=1,image=m['samples'][i]['image'],usable_for_clock_alignment=i!=0) for i,t in clocks[k].items()],observation=notes[k],accepted_complete_cycle=False,clock_warning='No exact cross-camera offset inferred. Initial source images excluded from synchronization; native PTS are positions only.'))
 merge(OUT/'screening_source_reviews.json',reviews,'review_id')
 def ev(k,a,b):return evidence(metas[k],a,b,paths[k])
 def base(day):return dict(date=day,split='train',reviewer='assistant_visual_review',reviewed_at=stamp,cycle_id=None,dataset_release_accepted=False)
 def neg(ident,day,camera,cls,times,proof,note,scope,tanks=None):
  return dict(base(day),sequence_id=ident,camera=camera,camera_track_id=ident,review_status='accepted_negative_sequence',production_entry_count_target=0,negative_class=cls,tracked_tank_count=tanks,visible_camera_clock_interval=times,clock_uncertainty_seconds=3,evidence=proof,observation=note,label_scope=scope)
 labels=[
  neg('20261005_empty_powered_jack_1044','20261005',15,'pallet_jack_without_tank',['10:44:56','10:45:08'],[ev('five',7,11)],'Powered pallet jack moves through room15 with visibly unloaded forks.','Only this unloaded jack segment; nearby tanks and other activity are not zero-labeled.',0),
  neg('20261005_people_without_tank_1045','20261005',15,'people_without_tank',['10:44:59','10:45:49'],[ev('five',8,13),ev('five',17,25)],'Two people walk to/from shared doorway in separate segments without transporting a tank.','One people-only episode with two evidence intervals. Not a tank inventory or whole-room absence target.',0),
  neg('20261006_unloaded_forklift_returns_0943','20261006',15,'pallet_jack_without_tank',['09:43:46','09:45:20'],[ev('stacks15',12,15),ev('stacks15',38,42),ev('origin',24,26),ev('origin',45,46)],'Two forklift returns from15 to11 have visibly unloaded forks after dropping stacks in15.','Only unloaded return segments; intervening stack-carrying trips are excluded from this zero target.',0),
  neg('20261006_inverted_upper_tanks_0943','20261006',15,'empty_crossing',['09:43:03','09:44:43'],[ev('origin',12,15),ev('stacks15',1,8),ev('origin',33,36),ev('stacks15',27,35)],'Two inverted upper tanks, beige then gray, cross11-to15 on separate forklift stacks while active cheese tank stays at filling station. Inverted feet/bottoms are visible.','ONLY the two inverted upper tanks. Upright lower tanks have unknown contents and must remain unlabelled for production eligibility. One episode, two upper-tank tracks; never apply zero to the full stack or frame.',2),
  neg('20261006_empty_blue_replacement_0946','20261006',11,'empty_tank_internal_reposition',['09:46:16','09:46:26'],[ev('origin',0,0),ev('departure',7,10)],'One visibly empty blue-lined tank waits locally left and moves to filling station after fresh load is removed. Empty lined bottom visible46:21.','Only the replacement before new filling. Simultaneous fresh loaded departure is a different tracked action.',1),
 ]
 fresh=dict(base('20261006'),sequence_id='20261006_fresh_blue_entry_scale_partial_0946',camera=11,camera_track_id='cam11_blue_station_0942_0946',review_status='reviewed_partial_sequence',production_entry_count_target=None,observed_loaded_departure_count=1,entry15_camera_clock_interval=['09:46:13','09:46:21'],partial_reason='Filling, loaded departure, occluded entry and scale visit observed. Storage movement51:51 onward is separated from scale departure by a trajectory gap and remains unlinked; no complete-cycle target.',observation=notes['departure'],evidence=[ev('origin',0,49),ev('departure',0,67),ev('entry',32,42),ev('staging',1,15),ev('scale',1,23)],
  stages=[
   dict(stage='filling_observed',visible_camera_clock_interval=['09:42:15','09:46:06'],clock_uncertainty_seconds=5,content_evidence='Cheese visible and placements at station observed; cover placed before departure. Initial tank contents and quantity unknown.',evidence=[ev('origin',0,49),ev('departure',0,6)]),
   dict(stage='loaded_departure_11',visible_camera_clock_interval=['09:46:10','09:46:21'],doorway_crossing_camera11_interval=['09:46:16','09:46:21'],clock_uncertainty_seconds=5,evidence=[ev('departure',7,9)]),
   dict(stage='entry_15',visible_camera_clock_interval=['09:46:13','09:46:21'],clock_uncertainty_seconds=4,content_evidence='Blue-lined tank pulled from filling station by apron operator; partially hidden by operator and door. Same crossing supported by reviewed11 chronology; no exact offset fitted.',evidence=[ev('entry',32,42),ev('departure',7,9)]),
   dict(stage='scale_visit',visible_camera_clock_interval=['09:47:06','09:51:11'],platform_occupied_by='09:47:16',scale_departure_interval=['09:51:01','09:51:11'],clock_uncertainty_seconds=5,content_evidence='Tank drawn from left doorway staging onto platform; later dwell and clearance visible through door in11. No measured weight inferred.12-second staging source gap retained.',evidence=[ev('staging',1,15),ev('scale',1,23),ev('departure',18,67)]),
  ],unlinked_followup=dict(status='storage_approach_after_trajectory_gap_identity_unresolved',production_entry_count_target=None,visible_camera_clock_interval=['09:51:51','09:52:05'],observation=notes['storage'],evidence=[ev('storage',1,16)]),limitations=['No fresh production label for lower tanks in forklift stacks.','No exact camera offset, initial cheese quantity or measured kilograms.','Partial trajectory evidence only. No accepted complete cycle until storage identity is established.','Later storage approach still has engaged jack at end; final release not observed.'])
 labels.append(fresh)
 merge(OUT/'reviewed_sequence_labels.json',labels,'sequence_id')
 merge(OUT/'sequence_followup_queue.json',[dict(candidate_id='20261006_blue_scale_to_storage_after0951',date='20261006',split='train',cycle_id=None,production_entry_count_target=None,status='partial_storage_identity_gap',reviewed_at=stamp,reviewed_partial_sequence_id=fresh['sequence_id'],observation=fresh['partial_reason'],next_action='Retain partial. Source filenames15 end095044 then next095139, whose usable frames begin095151.11 scale departure095106-11 lies in this gap. Do not repeat without new bridging footage. Later095215-095257 may show jack release but cannot itself resolve missing identity.',new_evidence=[ev('departure',65,67),ev('storage',1,16)])],'candidate_id')
 registry=read(OUT/'object_review_decisions.json');decisions={r['id']:r for r in registry['reviews']};draft={r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
 roi_notes={'131':'Waiting empty tank fully visible; generic tank detection only.','133':'Covered departure; isolated tank body visible. White cover is not a load-state label.','134':'Empty replacement at station; right and bottom crop truncation, worker/conveyor occlusion.','135':'Separate stationary scrap receptacle; lower body occluded by worker/conveyor. Object-only label.'}
 for ident,note in roi_notes.items():
  assert ident not in decisions;r=draft[ident];assert r['split']=='train' and r['date']=='20261006';sheet='16' if ident=='135' else '15'
  decisions[ident]=dict(id=ident,image_sha256=r['sha256'],boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',load_state_reviewed=False,sequence_reviewed=False,instance_attributes=[dict(box_index=j,truncated=(b[0]==0 or b[1]==0 or b[2]==r['width'] or b[3]==r['height']),occluded=ident in ('134','135'),load_state='unknown_not_annotated') for j,b in enumerate(r['boxes_xyxy'])],evidence=[r['source_frame'],r['frames_manifest'],f'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_{sheet}.jpg'],note=note)
 registry['reviews']=list(decisions.values());registry.setdefault('corrections',[]).append('Batch14:131/133/134/135 accepted after native context and separate overlays;134 bottom extent and135 right extent refined before approval.132 excluded because body boundary is hidden. No previous annotation changed.');save(OUT/'object_review_decisions.json',registry)
 inventory=read(BASE/'archive_inventory.json');inspected={m['source']['member']:m['source_sha256'] for m in metas.values()}
 for r in inventory['records']:
  if r['member'] in inspected:r.update(pixel_inspected=True,sha256=inspected[r['member']])
 assert not any(r['pixel_inspected'] for r in inventory['records'] if r['split']=='test');save(BASE/'archive_inventory.json',inventory)
 allreviews=read(OUT/'screening_source_reviews.json');total=sum(r['sampled_frames_visually_reviewed'] for r in allreviews);nsource=len({r['source_member'] for r in allreviews})
 state['last_completed'] += [f'Batch14 reviewed290 chronological sample presentations in8 windows on5/6Oct; {total} total across{nsource} source videos and{len(allreviews)} windows. All extractions finished;25/28Oct untouched.',
  '6Oct fresh blue-lined filling/departure/entry09:46:13-21 and scale visit retained as partial. Later51:51-52:05 storage approach is unlinked across trajectory gap from51:06-11 scale departure. No complete-cycle target invented.',
  'Five negatives added:5Oct unloaded jack and people-only episode;6Oct unloaded forklift returns, two inverted UPPER tanks only, and empty blue replacement. Upright lower tanks in stacks remain unknown. Totals2 complete,29 negatives,13 partials.',
  'Five ROI candidates131-135 appended:four accepted with4 boxes,132 excluded. Totals136 candidates,91 accepted ROI images,140 accepted boxes,6 old drafts,39 exclusions. Training remains unreleased.'
 ]
 state['priority_next']=[
  'Batch14 all8 windows on5/6Oct recorded; do not repeat. New6Oct0946 partial has reviewed entry/scale but missing continuous scale-to-storage track51:06-51. Later52:15 footage may establish storage release only, not missing identity.',
  'Need complete-cycle training-day diversity and true post-storage relocation/same-load reentry negatives.5Oct11 lacks10:38-50 overlap;8Oct11 lacks09:40-50 overlap. Inspect archive metadata to prioritize windows with overlapping native coverage; do not infer continuity from filenames.',
  'Six old object drafts002/003/006/007/010/011 still need native context or exclusion. Existing planning/release targets remain unmet.13Oct long15 windows090821-091619 and102139-102912 uninspected, but both accepted complete cycles already from13Oct.',
 ]+state['priority_next'][2:]
 state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False);state.setdefault('completed_curation_runs',[]).append(RUN)
 for name in ['work/append_tank_roi_batch_20261031_14.py','work/record_tank_sequence_batch_20261031_14.py']:
  if name not in state['scripts']:state['scripts'].append(name)
 save(OUT/'continuation_state.json',state)
 print(json.dumps(dict(recorded=RUN,additional_temporal_samples=290,additional_negatives=5,additional_partials=1,additional_accepted_images=4,total_presentations=total,training_started=False)))

if __name__=='__main__':main()
