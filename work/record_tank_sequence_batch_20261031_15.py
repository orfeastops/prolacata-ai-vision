"""Record23Oct preparation negatives and resolve six old object drafts."""
import datetime as dt
import hashlib,json
from pathlib import Path
from record_tank_boundary_review_20261031 import read,save,merge,evidence
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'outputs/tank_transfer_training_v1';OUT=BASE/'dataset_v1';RUN='sequence_review_20261031_15'

def main():
 state=read(OUT/'continuation_state.json')
 if RUN in state.get('completed_curation_runs',[]):print('Already recorded',RUN);return
 stamp=dt.datetime.now(dt.timezone.utc).isoformat()
 windows={'early':('origin_0605_cam11',19),'late':('origin_0616_cam11',24),'room15':('activity_0613_cam15',21)}
 paths={k:OUT/'sequence_review/20261023'/w/'frames.json' for k,(w,n) in windows.items()};metas={k:read(p) for k,p in paths.items()}
 for k,m in metas.items():
  assert len(m['samples'])==windows[k][1] and m['source']['date']=='20261023' and m['source']['split']=='train'
 clocks={
  'early':{0:'06:05:10',1:'06:05:24',3:'06:05:30',4:'06:05:33',5:'06:05:36',6:'06:05:39',7:'06:05:42',8:'06:05:45',10:'06:05:51',11:'06:05:54',13:'06:06:00',18:'06:06:15'},
  'late':{0:'06:16:54',1:'06:17:06',2:'06:17:09',5:'06:17:18',9:'06:17:30',13:'06:17:42',17:'06:17:54',19:'06:18:00',20:'06:18:03',21:'06:18:06',22:'06:18:09',23:'06:18:12'},
  'room15':{0:'06:13:29',1:'06:13:37',2:'06:13:38',3:'06:13:40',7:'06:13:48',8:'06:13:51',9:'06:13:52',11:'06:13:56',12:'06:13:58',13:'06:14:01',14:'06:14:03',15:'06:14:04',16:'06:14:06',17:'06:14:08',18:'06:14:10',19:'06:14:13',20:'06:14:14'}
 }
 notes={
  'early':'First usable06:05:24 after stale05:10. Room11 is in preparation: many lined empty gray tanks already arranged in rows, both station-side tanks empty, no cheese on conveyor and no filling. People walk through shared door05:33-45 and return05:54 without tanks. A stationary jack carries sacks near wall; do not label it as an empty-jack movement. No production-tank departure in the inspected sample sequence.',
  'late':'First usable06:17:06 after stale16:54. Same room11 preparation layout and empty station tanks, no cheese arrivals or filling in this window. Two people stand, gesture and walk near doorway17:06-18:00, then go through toward15 at18:03-12 without a tank. Gaps from earlier05-minute sequence remain; no same-person identity or whole-day zero inferred.',
  'room15':'First usable06:13:37 after stale13:29. Several tanks/containers already present: paired beige near door, a single beige foreground, gray beside scale and inverted stacks in lower full-frame view. People walk from left toward door13:51-14:08 without tanks. Apron operator then pulls the visibly empty gray container from beside scale into room centre14:10-14; movement still in progress at source end. This is internal movement of a starting container, not new entry. Nothing is inferred about unseen production later in the day.'
 }
 reviews=[]
 for k,m in metas.items():
  reviews.append(dict(review_id='20261023/'+windows[k][0],reviewed_at=stamp,reviewer='assistant_visual_review',source_member=m['source']['member'],source_sha256=m['source_sha256'],date='20261023',camera=m['source']['camera'],split='train',frames_manifest=str(paths[k].relative_to(ROOT)),sampled_frames_visually_reviewed=len(m['samples']),reviewed_sheets=m['sheets'],review_scope='Every chronological contact-sheet sample inspected; three native full frames and new ROI overlay sheet inspected separately. Not exhaustive native-frame viewing.',visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],visible_camera_clock=t,clock_read_uncertainty_seconds=1,image=m['samples'][i]['image'],usable_for_clock_alignment=i!=0) for i,t in clocks[k].items()],observation=notes[k],accepted_complete_cycle=False,clock_warning='Initial source images excluded from synchronization. Filename and PTS ranges do not prove cross-camera alignment.'))
 merge(OUT/'screening_source_reviews.json',reviews,'review_id')
 def ev(k,a,b):return evidence(metas[k],a,b,paths[k])
 shared=dict(date='20261023',split='train',reviewer='assistant_visual_review',reviewed_at=stamp,cycle_id=None,dataset_release_accepted=False,review_status='accepted_negative_sequence',production_entry_count_target=0)
 labels=[
  dict(shared,sequence_id='20261023_people_only_preparation_0605',camera=11,camera_track_id='people_only_preparation_multisegment',negative_class='people_without_tank',tracked_tank_count=0,visible_camera_clock_interval=['06:05:30','06:18:12'],clock_uncertainty_seconds=3,evidence=[ev('early',3,11),ev('room15',8,17),ev('late',1,23)],observation='People walk, stand and gesture near shared doorway in three inspected preparation segments. No tank travels with these people in those segments.',label_scope='Only the explicitly listed sample intervals, one composite negative example. Unobserved intervening minutes are not labeled. No cross-gap person identity or whole-day absence claim.'),
  dict(shared,sequence_id='20261023_empty_station_starting_inventory',camera=11,camera_track_id='two_station_tanks_initially_empty',negative_class='opening_inventory',tracked_tank_count=2,visible_camera_clock_interval=['06:05:24','06:18:12'],clock_uncertainty_seconds=3,evidence=[ev('early',1,18),ev('late',1,23)],observation='Two separate gray tanks adjacent to the conveyor are visibly empty and already present at both inspected windows. Perforated bottoms/liners visible, no cheese arrivals.',label_scope='These two stationary starting tanks only, within listed windows. Not a count of all row tanks, and no claim about later production.'),
  dict(shared,sequence_id='20261023_empty_gray_internal_0614',camera=15,camera_track_id='gray_scale_side_container_internal_move',negative_class='empty_tank_internal_reposition',tracked_tank_count=1,visible_camera_clock_interval=['06:14:08','06:14:14'],clock_uncertainty_seconds=2,evidence=[ev('room15',1,7),ev('room15',17,20)],observation='Operator pulls one visibly empty gray container from its initial position beside scale into room centre. No threshold crossing; motion continues at source end.',label_scope='Only this empty internal movement. No complete-cycle or measured weight inference.'),
 ]
 merge(OUT/'reviewed_sequence_labels.json',labels,'sequence_id')
 registry=read(OUT/'object_review_decisions.json');history=OUT/'review_history/object_decisions_before_20261031_15.json'
 if not history.exists():save(history,registry)
 decisions={r['id']:r for r in registry['reviews']};draft={r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
 roi_notes={'136':'Empty front station tank; right/bottom crop truncation and conveyor occlusion. Generic tank detection only.','137':'Separate empty station-side tank, conveyor partly occludes front. Generic tank box only.','138':'Isolated beige room15 container with visible empty interior; generic object annotation only, not a production entry.'}
 for ident,note in roi_notes.items():
  assert ident not in decisions;r=draft[ident];assert r['date']=='20261023' and r['split']=='train'
  decisions[ident]=dict(id=ident,image_sha256=r['sha256'],boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',load_state_reviewed=False,sequence_reviewed=False,instance_attributes=[dict(box_index=j,truncated=(b[0]==0 or b[1]==0 or b[2]==r['width'] or b[3]==r['height']),occluded=ident!='138',load_state='unknown_not_annotated') for j,b in enumerate(r['boxes_xyxy'])],evidence=[r['source_frame'],r['frames_manifest'],'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_15.jpg'],note=note)
 registry['reviews']=list(decisions.values());exclusions={r['id']:r for r in registry.get('excluded_roi_reviews',[])}
 contexts={'002':'entry_0709_cam15','003':'entry_0709_cam15','006':'entry_scale_0725_cam15','007':'entry_scale_0725_cam15','010':'second_entry_0732_cam15','011':'second_entry_0732_cam15'}
 for ident,window in contexts.items():
  assert ident not in decisions
  mp=OUT/'sequence_review/20261021'/window/'frames.json';m=read(mp)
  exclusions[ident]=dict(id=ident,image_sha256=draft[ident]['sha256'],reviewed_at=stamp,reviewer='assistant_visual_review',decision='exclude_whole_roi_not_an_empty_image',reason='Low-resolution crowded doorway crop: overlapping moving tank, stationary blue pair and background/border tanks lack confident complete extents. Native context confirms additional instances; do not accept incomplete boxes or treat excluded crop as empty.',evidence=[draft[ident]['image'],m['samples'][1]['image'],str(mp.relative_to(ROOT))],prior_draft='outputs/tank_transfer_training_v1/dataset_v1/review_history/old_six_roi_drafts_before_20261031_15.json',context_limitation='Native same-date source context, not a claimed byte-identical frame correspondence between separate exports. No timestamp retiming or source hash invented.')
 exclusions['139']=dict(id='139',image_sha256=draft['139']['sha256'],reviewed_at=stamp,reviewer='assistant_visual_review',decision='exclude_whole_roi_not_an_empty_image',reason='Main gray container visible, but adjacent upper-left blue container fragment has uncertain extent. Exclude whole ROI from clean detection targets.',evidence=[draft['139']['image'],draft['139']['source_frame'],draft['139']['frames_manifest']])
 registry['excluded_roi_reviews']=list(exclusions.values());registry.setdefault('corrections',[]).append('Batch15: three native23Oct ROIs136-138 approved;139 excluded. Six old unresolved drafts002/003/006/007/010/011 excluded with original boxes preserved in review_history. No accepted boxes were removed or changed.');save(OUT/'object_review_decisions.json',registry)
 inv=read(BASE/'archive_inventory.json');inspected={m['source']['member']:m['source_sha256'] for m in metas.values()}
 for r in inv['records']:
  if r['member'] in inspected:r.update(pixel_inspected=True,sha256=inspected[r['member']])
 assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test');save(BASE/'archive_inventory.json',inv)
 # Metadata range observation only; it is not a claim that all intervening
 # recordings are continuous or that all early footage was viewed.
 coverage=[]
 for day in ['20261005','20261008','20261023']:
  for camera in [11,15]:
   rs=[r for r in inv['records'] if r['date']==day and r['camera']==camera and r['media_type']=='video']
   coverage.append(dict(date=day,camera=camera,video_files=len(rs),filename_min_start=min(r['filename_start'] for r in rs),filename_max_end=max(r['filename_end'] for r in rs),policy='Filename extent only, not verified continuous duration or synchronization.'))
 save(OUT/'coverage_followup_20261031_15.json',dict(created_at=stamp,records=coverage,visual_observation='23Oct sampled11 windows06:05 and06:17 show preparation and empty tanks. Archive11 latest filename ends06:19:12. No reviewed production cycle from23Oct; do not assume all-day zero.',test_pixels_used=0))
 allreviews=read(OUT/'screening_source_reviews.json');total=sum(r['sampled_frames_visually_reviewed'] for r in allreviews)
 state['last_completed'] += [f'Batch15 inspected64 chronological samples in3 new23Oct windows; {total} total. All extractions completed;25/28Oct remain unseen.',
  '23Oct sampled11 material06:05/06:17 shows preproduction empty station tanks;15 has empty internal gray movement06:14. Added3 track/interval-scoped negatives. Totals2 complete cycles,32 negative examples,13 partial tracks; no production cycle inferred from setup.',
  'Three native23Oct ROIs136-138 accepted with3 boxes,139 excluded. Six old drafts002/003/006/007/010/011 resolved as exclusions with previous proposed boxes archived. Totals140 candidates,94 accepted images,143 boxes,46 exclusions,zero unresolved object drafts. Dataset still unreleased.',
  'Metadata audit: camera11 latest filename ends05:48:49 on5Oct,05:56:22 on8Oct,06:19:12 on23Oct; corresponding15 extends later. These are filename extents, not verified whole-day continuity.23Oct inspected late11 sample is still preparation.'
 ]
 state['priority_next']=[
  'Batch15 all3 new23Oct windows reviewed and recorded. No fresh filling observed. Do not repeatedly inspect early23Oct prep for complete cycles without later11 media.',
  'Old six ROI drafts are now excluded, not pending. Preserve review_history. Need more object images with defensible boundaries, positive complete cycles on multiple training days, and same-load/post-storage relocation negatives.',
  'Prioritize training days6/10/15/21 with existing production footage.13Oct unreviewed15 long windows090821-091619 and102139-102912 can add cycles but not training-day diversity.5/8/23 archive11 coverage is early by filename; metadata cannot supply missing production origin.',
 ]+[p for p in state['priority_next'] if p.startswith('Known gaps') or p.startswith('25/28')]
 state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False);state.setdefault('completed_curation_runs',[]).append(RUN)
 for s in ['work/append_tank_roi_batch_20261031_15.py','work/record_tank_sequence_batch_20261031_15.py']:
  if s not in state['scripts']:state['scripts'].append(s)
 save(OUT/'continuation_state.json',state)
 print(json.dumps(dict(recorded=RUN,additional_temporal_samples=64,additional_negatives=3,additional_accepted_images=3,training_started=False)))
if __name__=='__main__':main()
