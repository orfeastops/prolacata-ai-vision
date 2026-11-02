import datetime as dt
from pathlib import Path
from record_tank_boundary_review_20261031 import read,save,merge,evidence
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'outputs/tank_transfer_training_v1';OUT=BASE/'dataset_v1';RUN='sequence_review_20261031_52'
def main():
 state=read(OUT/'continuation_state.json')
 if RUN in state.get('completed_curation_runs',[]):return
 stamp=dt.datetime.now(dt.timezone.utc).isoformat()
 windows=[('fourth_route1309_cam15',['13:09:32','13:09:40','13:09:43','13:09:46','13:09:49','13:09:52','13:09:55','13:09:58','13:10:01','13:10:04','13:10:07','13:10:10']),('fourth_park1310_cam15',['13:10:24','13:10:42','13:10:45','13:10:48','13:10:51','13:10:54','13:10:57','13:11:00'])]
 evs=[];sources={}
 for w,clocks in windows:
  p=OUT/'sequence_review/20261015'/w/'frames.json';m=read(p);assert len(m['samples'])==len(clocks) and m['source']['split']=='train'
  sources[m['source']['member']]=m['source_sha256'];evs.append(evidence(m,1,len(clocks)-1,p))
  note=('All12 samples/two sheets viewed. Initial09:32 then40. Covered gray already at staging; moves across aisle40-55, turns toward left storage row58, leaves selected crop at10:01-04. No fork withdrawal/settled final placement visible in selected crop; do not call storage complete or infer identity from earlier scale.' if '1309' in w else 'All8 samples/two sheets viewed. Initial10:24 then42. No covered gray placement visible in selected crop. A different visibly empty beige tank emerges from left48, crosses aisle51-54, moves through door57-11:00 toward11. This is empty return, zero productive entries; origin of empty tank not assumed.')
  merge(OUT/'screening_source_reviews.json',[dict(review_id='20261015/'+w,date='20261015',camera=15,split='train',reviewer='assistant_visual_review',reviewed_at=stamp,source_member=m['source']['member'],source_sha256=m['source_sha256'],frames_manifest=str(p.relative_to(ROOT)),sampled_frames_visually_reviewed=len(clocks),reviewed_sheets=m['sheets'],accepted_complete_cycle=False,review_scope='All extracted sample tiles inspected; crop does not establish off-crop final placement.',observation=note,visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],visible_camera_clock=t,clock_read_uncertainty_seconds=1,image=m['samples'][i]['image'],usable_for_clock_alignment=False) for i,t in enumerate(clocks)])],'review_id')
 labels=read(OUT/'reviewed_sequence_labels.json');save(OUT/'review_history/sequence_labels_before_20261031_52.json',labels)
 row=next(r for r in labels if r['sequence_id']=='20261015_fourth_gray_departure1303_partial')
 row['reviewed_at']=stamp;row['unlinked_followup']['later_route']=dict(observation='Covered gray from staging09:40 across aisle and toward left row10:01. Leaves selected crop; final placement/fork withdrawal unverified. Cannot link earlier scale and fresh03-minute departure across missing entry/trajectory.',evidence=evs,storage_confirmed=False)
 labels.append(dict(sequence_id='20261015_empty_beige_return1310',date='20261015',split='train',reviewer='assistant_visual_review',reviewed_at=stamp,review_status='accepted_negative_sequence',cycle_id=None,production_entry_count_target=0,dataset_release_accepted=False,camera=15,negative_class='empty_crossing',tracked_tank_count=1,direction='15_to_11',visible_camera_clock_interval=['13:10:48','13:11:00'],observation='Visibly empty beige tank moved from left across aisle and through shared doorway toward11. Distinct from previous covered gray load.',label_scope='Empty beige return track only; existing inventory and covered gray separate.',evidence=[evidence(m,3,7,p)]))
 save(OUT/'reviewed_sequence_labels.json',labels)
 inv=read(BASE/'archive_inventory.json')
 for r in inv['records']:
  if r['member'] in sources:r.update(pixel_inspected=True,sha256=sources[r['member']])
 assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test');save(BASE/'archive_inventory.json',inv)
 state['last_completed']+=['Batch52:20 new15Oct15 sampled tiles reviewed across two sources. Covered gray staging-to-left-row route retained unlinked and storage unconfirmed because selected crop loses tank. Distinct empty beige15-to11 return10:48-11:00 accepted as one negative. No new complete cycle.']
 state['priority_next']=['Batch52 fourth_route1309_cam15/fourth_park1310_cam15 selected tiles screened. Native full frames or wider left crop needed around13:10:01-42 to check covered gray placement; original selected crop loses tank. Do not equate disappearance with storage.','Fifth fill begins03:30-32 and continues07:42; next11 source13:07:34-31:55 available. Fourth entry03:10-16 still missing15 coverage; later storage cannot repair origin gap.']+[p for p in state['priority_next'] if p.startswith('Known gaps') or p.startswith('25/28')]
 state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False);state.setdefault('completed_curation_runs',[]).append(RUN);state['scripts'].append('work/record_tank_sequence_batch_20261031_52.py');save(OUT/'continuation_state.json',state)
 print('Recorded20 temporal samples and1 empty-return negative; incomplete route preserved')
if __name__=='__main__':main()
