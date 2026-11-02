import datetime as dt
from pathlib import Path
from copy import deepcopy
from record_tank_boundary_review_20261031 import read,save,merge,evidence
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'outputs/tank_transfer_training_v1';OUT=BASE/'dataset_v1';RUN='sequence_review_20261031_56'
def main():
 state=read(OUT/'continuation_state.json')
 if RUN in state.get('completed_curation_runs',[]):return
 stamp=dt.datetime.now(dt.timezone.utc).isoformat();metas=[];sources={}
 windows=[('fifth_scale1316_cam15',['13:16:'+s for s in ['08','26','29','32','35','38','41','44']],'Gray tank remains beside wall/display on scale; workers handle top. No incoming crossing. Initial08 then26 discontinuity retained.'),('fifth_route1317_cam15',['13:17:'+s for s in ['30','45','48','51','54','57']]+['13:18:'+s for s in ['00','03','06','09','12','15','18','21','24']],'Initial30 shows scale/staging context; noninitial45 already moving covered gray across aisle. Turns54-18:00, approaches left storage row03-09, remains parked12 onwards. Bare jack withdrawn15 and moves away18-24. No observed continuity from previous scale window to this route; no origin identity established.')]
 for w,clocks,obs in windows:
  p=OUT/'sequence_review/20261015'/w/'frames.json';m=read(p);assert len(m['samples'])==len(clocks);metas.append((m,p));sources[m['source']['member']]=m['source_sha256']
  merge(OUT/'screening_source_reviews.json',[dict(review_id='20261015/'+w,date='20261015',split='train',camera=15,reviewer='assistant_visual_review',reviewed_at=stamp,source_member=m['source']['member'],source_sha256=m['source_sha256'],frames_manifest=str(p.relative_to(ROOT)),sampled_frames_visually_reviewed=len(clocks),reviewed_sheets=m['sheets'],accepted_complete_cycle=False,review_scope='All chronological extracted tiles inspected, not exhaustive native frames.',observation=obs,visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],visible_camera_clock=t,clock_read_uncertainty_seconds=1,image=m['samples'][i]['image'],usable_for_clock_alignment=False) for i,t in enumerate(clocks)])],'review_id')
 labels=read(OUT/'reviewed_sequence_labels.json');save(OUT/'review_history/sequence_labels_before_20261031_56.json',labels)
 row=next(r for r in labels if r['sequence_id']=='20261015_fifth_gray_departure1311_partial');row['reviewed_at']=stamp
 row['unlinked_followup'].update(room15_scale_evidence=[evidence(*[metas[0][0],1,7,metas[0][1]])],room15_storage_evidence=[evidence(metas[1][0],1,14,metas[1][1])],observation='Room15 scale occupancy16:26-44; later covered gray crosses aisle17:45-18:09, parked by18:12, bare jack withdraws15 and departs18-24. Local storage is observed but missing entry11:52-58 and scale-to-route continuity prevent attribution to fifth fresh load.',storage_placement_locally_confirmed=True,numeric_weight_kg=None,measurement_success_verified=False)
 row['partial_reason']='Missing direct room15 entry and unresolved scale-to-storage identity. Later local placement does not establish a complete fresh-production cycle.'
 neg=deepcopy(next(r for r in labels if r['sequence_id']=='20261015_empty_jack_after_storage1301'));neg.update(sequence_id='20261015_empty_jack_after_storage1318',reviewed_at=stamp,visible_camera_clock_interval=['13:18:15','13:18:24'],observation='Bare manual-jack forks withdraw from parked gray tank15 and move away18-24; tank stays in left storage row. Track-scoped unloaded-jack negative.',evidence=[evidence(metas[1][0],11,14,metas[1][1])]);labels.append(neg);save(OUT/'reviewed_sequence_labels.json',labels)
 inv=read(BASE/'archive_inventory.json')
 for r in inv['records']:
  if r['member'] in sources:r.update(pixel_inspected=True,sha256=sources[r['member']])
 assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test');save(BASE/'archive_inventory.json',inv)
 state['last_completed'].append('Batch56:23 camera15 samples on15Oct reviewed. Local covered-gray storage confirmed18:12-24 with empty-jack withdrawal15. One tracked empty-jack negative added; fifth fresh origin remains unlinked because entry and scale-to-route gaps persist. No full-cycle promotion.')
 state['priority_next']=['Batch56 fifth_scale1316_cam15 and fifth_route1317_cam15 fully reviewed; do not repeat. Local storage confirmed, missing entry unchanged.','Continue sixth beige fresh fill in11 long source13:07:34-31:55 after600PTS, last reviewed13:17:34. Examine subsequent departure and available15 counterparts. Object ROI collection also remains below target.']+[p for p in state['priority_next'] if p.startswith('Known gaps') or p.startswith('25/28')]
 state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False);state.setdefault('completed_curation_runs',[]).append(RUN);state['scripts'].append('work/record_tank_sequence_batch_20261031_56.py');save(OUT/'continuation_state.json',state)
 print('Recorded23 samples and one negative; full cycles unchanged')
if __name__=='__main__':main()
