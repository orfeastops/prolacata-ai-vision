import datetime as dt
from pathlib import Path
from record_tank_boundary_review_20261031 import read,save,merge,evidence
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/tank_transfer_training_v1'
OUT=BASE/'dataset_v1'
RUN='sequence_review_20261031_49'
def main():
 state=read(OUT/'continuation_state.json')
 if RUN in state.get('completed_curation_runs',[]):return
 stamp=dt.datetime.now(dt.timezone.utc).isoformat()
 windows=[('third_storage1300_cam15',['13:00:59']+['13:01:'+str(i).zfill(2) for i in range(9,33,2)]),('third_park1301_cam15',['13:01:'+str(i).zfill(2) for i in range(33,56,2)])]
 evs=[];sources={}
 for w,clocks in windows:
  p=OUT/'sequence_review/20261015'/w/'frames.json';m=read(p)
  assert len(m['samples'])==len(clocks) and m['source']['split']=='train'
  sources[m['source']['member']]=m['source_sha256']
  evs.append(evidence(m,1,len(clocks)-1,p))
  merge(OUT/'screening_source_reviews.json',[dict(review_id='20261015/'+w,reviewed_at=stamp,reviewer='assistant_visual_review',date='20261015',camera=15,split='train',source_member=m['source']['member'],source_sha256=m['source_sha256'],frames_manifest=str(p.relative_to(ROOT)),sampled_frames_visually_reviewed=len(clocks),reviewed_sheets=m['sheets'],accepted_complete_cycle=False,review_scope='All extracted chronological samples visually inspected; no exhaustive native-frame claim.',observation=('All13 samples viewed. Initial00:59 then01:09: covered gray already away from scale, moved from doorway-side staging across aisle09-19, rotated21-25, pushed into front of storage row27-31. Origin and scale departure missing; do not infer new production entry.' if '1300' in w else 'All12 samples viewed. Same gray tank at row01:33; bare forks withdrawn35, jack moves away37-43. Tank stays parked through55. Two-second sampled source join31-33 retained; no competing tank on this local route. Empty jack is a separate negative track.'),visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],visible_camera_clock=t,clock_read_uncertainty_seconds=1,image=m['samples'][i]['image'],usable_for_clock_alignment=False) for i,t in enumerate(clocks)])],'review_id')
 labels=read(OUT/'reviewed_sequence_labels.json');save(OUT/'review_history/sequence_labels_before_20261031_49.json',labels)
 row=next(r for r in labels if r['sequence_id']=='20261015_third_gray_departure1253_partial')
 row['reviewed_at']=stamp
 row['unlinked_followup']['storage_observation']=dict(observation='Covered gray moved from staging to front-row storage13:01:09-33; empty forks visible35. Local track continuous across sampled31-33 source join. Scale-to-staging and origin identities remain unconfirmed.',evidence=evs,parking_interval=['13:01:27','13:01:35'],identity_with_fresh_departure_confirmed=False)
 row['partial_reason']='Incoming15 crossing and linkage to later storage remain missing. Scale last59:47; next source initial13:00:59 already in staging, noninitial01:09. Covered storage trajectory does not resolve missing entry or scale departure.'
 labels.append(dict(sequence_id='20261015_empty_jack_after_storage1301',date='20261015',split='train',reviewer='assistant_visual_review',reviewed_at=stamp,review_status='accepted_negative_sequence',cycle_id=None,production_entry_count_target=0,dataset_release_accepted=False,camera=15,negative_class='pallet_jack_without_tank',tracked_tank_count=0,visible_camera_clock_interval=['13:01:35','13:01:41'],observation='Bare forks withdraw from parked gray tank, empty manual jack moves across aisle. Stored tank remains still.',label_scope='Unloaded jack only; no whole-room negative and no new tank entry.',evidence=[evidence(m,1,4,p)]))
 save(OUT/'reviewed_sequence_labels.json',labels)
 inv=read(BASE/'archive_inventory.json')
 for r in inv['records']:
  if r['member'] in sources:r.update(pixel_inspected=True,sha256=sources[r['member']])
 assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test')
 save(BASE/'archive_inventory.json',inv)
 state['last_completed']+=['Batch49:25 additional samples in two15Oct camera15 windows visually reviewed. Local covered-gray staging-to-storage route and empty-fork withdrawal13:01:33-35 confirmed. Route kept unlinked from fresh1253 departure and earlier scale occupancy because intervening movement is missing. One track-scoped empty-jack negative added; no new complete cycle.']
 state['priority_next']=['Batch49 third_storage1300_cam15 and third_park1301_cam15 fully screened. Local storage confirmed01:33-35 but unlinked from earlier scale/origin. Do not promote1253 partial without missing entry/scale-to-staging coverage.','Continue15Oct fourth fresh load:11 source13:02:10-07:34 follows reviewed filling through13:02:15;15 source13:07:49-08:21 not yet inspected.']+[p for p in state['priority_next'] if p.startswith('Known gaps') or p.startswith('25/28')]
 state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
 state.setdefault('completed_curation_runs',[]).append(RUN)
 state['scripts'].append('work/record_tank_sequence_batch_20261031_49.py')
 save(OUT/'continuation_state.json',state)
 print('Recorded25 temporal samples, storage evidence, one empty-jack negative')
if __name__=='__main__':main()
