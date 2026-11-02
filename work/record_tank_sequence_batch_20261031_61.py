import datetime as dt
from pathlib import Path
from record_tank_boundary_review_20261031 import read,save,merge,evidence
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'outputs/tank_transfer_training_v1';OUT=BASE/'dataset_v1';RUN='sequence_review_20261031_61'
def main():
 state=read(OUT/'continuation_state.json')
 if RUN in state.get('completed_curation_runs',[]):return
 stamp=dt.datetime.now(dt.timezone.utc).isoformat();evs=[];sources={}
 windows=[('seventh_scale1331_cam15',['13:31:39','13:32:00','13:32:03','13:32:06','13:32:09']),('seventh_route1332_cam15',['13:32:43','13:32:47','13:32:50','13:32:53','13:32:56','13:32:59','13:33:02','13:33:05','13:33:08'])]
 for w,clocks in windows:
  p=OUT/'sequence_review/20261015'/w/'frames.json';m=read(p);assert len(m['samples'])==len(clocks);sources[m['source']['member']]=m['source_sha256'];evs.append(evidence(m,1,len(clocks)-1,p))
  merge(OUT/'screening_source_reviews.json',[dict(review_id='20261015/'+w,date='20261015',split='train',camera=15,reviewer='assistant_visual_review',reviewed_at=stamp,source_member=m['source']['member'],source_sha256=m['source_sha256'],frames_manifest=str(p.relative_to(ROOT)),sampled_frames_visually_reviewed=len(clocks),reviewed_sheets=m['sheets'],accepted_complete_cycle=False,review_scope='All extracted chronological sample tiles inspected; no exhaustive native-frame claim.',observation='Beige tank already at scale beside wall/display, remains in place while worker handles top. Stored beige by left row is a separate stationary instance. People traverse aisle/door in second window; no tank route or storage placement observed. Initial-frame clock jumps retained; no guessed synchronization or numeric weight.',visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],visible_camera_clock=t,clock_read_uncertainty_seconds=1,image=m['samples'][i]['image'],usable_for_clock_alignment=False) for i,t in enumerate(clocks)])],'review_id')
 labels=read(OUT/'reviewed_sequence_labels.json');save(OUT/'review_history/sequence_labels_before_20261031_61.json',labels)
 row=next(r for r in labels if r['sequence_id']=='20261015_seventh_beige_departure1328_partial');row['reviewed_at']=stamp;row['unlinked_followup'].update(room15_scale_evidence=evs,observation='Beige at room15 scale32:00-09 and32:47-33:08, already present initial31:39. No direct incoming crossing or storage movement. Left-row beige remains a distinct stored instance; not the scale tank. Keep missing entry and34-second sampled gap32:09-43 explicit.',numeric_weight_kg=None,measurement_success_verified=False);save(OUT/'reviewed_sequence_labels.json',labels)
 inv=read(BASE/'archive_inventory.json')
 for r in inv['records']:
  if r['member'] in sources:r.update(pixel_inspected=True,sha256=sources[r['member']])
 assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test');save(BASE/'archive_inventory.json',inv)
 state['last_completed'].append('Batch61:14 camera15 samples across two sources reviewed. Beige scale dwell confirmed32:00-09 and32:47-33:08, kept unlinked to seventh origin. Distinct left-row stored beige separated; no route/storage or complete-cycle claim.')
 state['priority_next']=['Batch61 seventh_scale1331_cam15 and seventh_route1332_cam15 fully reviewed; no repeat. Scale beige still present33:08; later15 sources needed for local storage, entry remains missing.','Prioritize object ROI annotation from already reviewed15Oct windows with native context and separate overlays; none added since batch47. Then expand complete-cycle coverage where both cameras have continuous evidence.']+[x for x in state['priority_next'] if x.startswith('Known gaps') or x.startswith('25/28')]
 state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False);state.setdefault('completed_curation_runs',[]).append(RUN);state['scripts'].append('work/record_tank_sequence_batch_20261031_61.py');save(OUT/'continuation_state.json',state)
 print('Recorded14 samples and extended unlinked scale evidence')
if __name__=='__main__':main()
