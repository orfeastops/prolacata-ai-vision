import datetime as dt
from pathlib import Path
from record_tank_boundary_review_20261031 import read,save,merge,evidence
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/tank_transfer_training_v1'
OUT=BASE/'dataset_v1'
RUN='sequence_review_20261031_48'
def main():
 state=read(OUT/'continuation_state.json')
 if RUN in state.get('completed_curation_runs',[]):return
 stamp=dt.datetime.now(dt.timezone.utc).isoformat()
 windows=[('third_scale1257_cam15',['12:57:13','12:57:27','12:57:30','12:57:33','12:57:36','12:57:39']),('third_scale1259_cam15',['12:59:31','12:59:35','12:59:37','12:59:39','12:59:41','12:59:43','12:59:45','12:59:47'])]
 evs=[];sources={}
 for w,clocks in windows:
  p=OUT/'sequence_review/20261015'/w/'frames.json';m=read(p)
  assert len(m['samples'])==len(clocks) and m['source']['split']=='train'
  sources[m['source']['member']]=m['source_sha256']
  evs.append(evidence(m,1,len(clocks)-1,p))
  merge(OUT/'screening_source_reviews.json',[dict(review_id='20261015/'+w,reviewed_at=stamp,reviewer='assistant_visual_review',date='20261015',camera=15,split='train',source_member=m['source']['member'],source_sha256=m['source_sha256'],frames_manifest=str(p.relative_to(ROOT)),sampled_frames_visually_reviewed=len(clocks),reviewed_sheets=m['sheets'],accepted_complete_cycle=False,review_scope='All extracted chronological samples visually inspected; no exhaustive native-frame claim.',observation='Gray tank at scale beside wall/display already present; workers handle liner/top. Stationary foreground tanks and stored rows are separate. No incoming crossing or storage movement observed. Initial frame clock discontinuity retained; first noninitial sample used for interval. '+('Initial57:13 then57:27; ends57:39.' if '1257' in w else 'Initial59:31 then59:35; ends59:47. People move around door; tank remains at scale.'),visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],visible_camera_clock=t,clock_read_uncertainty_seconds=1,image=m['samples'][i]['image'],usable_for_clock_alignment=False) for i,t in enumerate(clocks)])],'review_id')
 labels=read(OUT/'reviewed_sequence_labels.json');save(OUT/'review_history/sequence_labels_before_20261031_48.json',labels)
 row=next(r for r in labels if r['sequence_id']=='20261015_third_gray_departure1253_partial')
 row['reviewed_at']=stamp
 row['unlinked_followup'].update(observation='Gray tank beside wall/display at scale confirmed in room15 12:57:27-39 and12:59:35-47. Already present at first available frame57:13. Origin/entry not observed, and gap between short sources remains; do not link by color/time alone.',room15_scale_evidence=evs,numeric_weight_kg=None,measurement_success_verified=False)
 row['partial_reason']='Incoming room15 crossing and storage identity remain missing. Previously inspected15 source ends53:39; next available inspected source starts57:13 (first noninitial57:27). Later scale occupancy does not bridge entry gap.'
 save(OUT/'reviewed_sequence_labels.json',labels)
 inv=read(BASE/'archive_inventory.json')
 for r in inv['records']:
  if r['member'] in sources:r.update(pixel_inspected=True,sha256=sources[r['member']])
 assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test')
 save(BASE/'archive_inventory.json',inv)
 state['last_completed']+=['Batch48:14 additional camera15 samples across two sources on15Oct visually reviewed. Actual clocks establish post-entry search gap53:39-57:13; later scale tank remains explicitly unlinked to fresh departure1253. Initial frame discontinuities retained. No extra complete cycle or negative fabricated.']
 state['priority_next']=['Batch48: third_scale1257_cam15 and third_scale1259_cam15 fully screened. Gray scale occupancy ends59:47; next15 source13:00:59-01:33 may show storage but entry gap persists. Do not repeat search53:39-57:13 without alternate media.','Continue15Oct fourth fresh load:11 source13:02:10-07:34 follows filling through13:02:15. Check15 source13:07:49-08:21 for paired later route; filenames only until pixel review.']+[p for p in state['priority_next'] if p.startswith('Known gaps') or p.startswith('25/28')]
 state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
 state.setdefault('completed_curation_runs',[]).append(RUN)
 state['scripts'].append('work/record_tank_sequence_batch_20261031_48.py')
 save(OUT/'continuation_state.json',state)
 print('Recorded14 temporal samples, revised partial evidence; no new cycle claim')
if __name__=='__main__':main()
