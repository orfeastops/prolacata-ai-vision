import datetime as dt
from pathlib import Path
from record_tank_boundary_review_20261031 import read,save,merge,evidence
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/tank_transfer_training_v1/dataset_v1';RUN='sequence_review_20261031_60'
def main():
 state=read(OUT/'continuation_state.json')
 if RUN in state.get('completed_curation_runs',[]):return
 stamp=dt.datetime.now(dt.timezone.utc).isoformat();w='seventh_departure1328_dense_cam11';p=OUT/'sequence_review/20261015'/w/'frames.json';m=read(p);assert len(m['samples'])==17
 clocks=['13:27:54','13:27:57']+['13:28:'+str(x).zfill(2) for x in range(0,43,3)]
 obs='Cheese blocks visible27:54-57; cover applied28:00-03, tank begins leaving station06, travels09-15, crosses threshold18-21, clear24. No empty replacement movement in this window. Separate right-hand curd container remains; not counted as fresh production.'
 merge(OUT/'screening_source_reviews.json',[dict(review_id='20261015/'+w,date='20261015',split='train',camera=11,reviewer='assistant_visual_review',reviewed_at=stamp,source_member=m['source']['member'],source_sha256=m['source_sha256'],frames_manifest=str(p.relative_to(ROOT)),sampled_frames_visually_reviewed=17,reviewed_sheets=m['sheets'],accepted_complete_cycle=False,review_scope='All17 chronological sample tiles/three sheets inspected.',observation=obs,visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],visible_camera_clock=t,clock_read_uncertainty_seconds=1,image=m['samples'][i]['image'],usable_for_clock_alignment=False) for i,t in enumerate(clocks)])],'review_id')
 labels=read(OUT/'reviewed_sequence_labels.json');save(OUT/'review_history/sequence_labels_before_20261031_60.json',labels)
 row=next(r for r in labels if r['sequence_id']=='20261015_seventh_beige_departure1328_partial');row.update(reviewed_at=stamp,observation=obs,partial_reason='Dense11 threshold reviewed; direct15 entry and subsequent scale/storage identity unverified. Inventoried15 filenames end13:27:59 then resume13:31:39; filename gap is not camera synchronization evidence.')
 stage=next(s for s in row['stages'] if s['stage']=='loaded_departure_11');stage.update(visible_camera_clock_interval=['13:28:06','13:28:24'],doorway_crossing_camera11_interval=['13:28:18','13:28:24'],clock_uncertainty_seconds=3,observation='Leaves station06, travels09-15, doorway18-21, clear24.');stage['evidence'].append(evidence(m,3,10,p));row['evidence'].append(evidence(m,0,10,p));save(OUT/'reviewed_sequence_labels.json',labels)
 state['last_completed'].append('Batch60:17 dense15Oct11 samples reviewed. Seventh beige threshold narrowed28:18-24; top cover applied00-03 after visible cheese. No replacement or full cycle invented. Metadata-only15 inventory shows neighboring filename endpoints27:59/31:39; actual clock coverage remains unverified.')
 state['priority_next']=['Batch60 seventh_departure1328_dense_cam11 fully reviewed; no repeat extraction. Seventh doorway28:18-24 retained partial.','Next inspect15 source13:31:39-32:11 and13:32:43-33:10 for scale/storage, preserving missing direct entry. Prior15 filename ends27:59, next31:39; do not treat filename/PTS as synchronization. Add object ROIs from reviewed frames with independent overlays.']+[x for x in state['priority_next'] if x.startswith('Known gaps') or x.startswith('25/28')]
 state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False);state.setdefault('completed_curation_runs',[]).append(RUN);state['scripts'].append('work/record_tank_sequence_batch_20261031_60.py');save(OUT/'continuation_state.json',state)
 print('Recorded17 samples and refined seventh partial')
if __name__=='__main__':main()
