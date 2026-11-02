import datetime as dt
from pathlib import Path
from record_tank_boundary_review_20261031 import read,save,merge,evidence
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/tank_transfer_training_v1/dataset_v1';RUN='sequence_review_20261031_55'
def main():
 state=read(OUT/'continuation_state.json')
 if RUN in state.get('completed_curation_runs',[]):return
 stamp=dt.datetime.now(dt.timezone.utc).isoformat();w='fifth_departure1311_dense_cam11';p=OUT/'sequence_review/20261015'/w/'frames.json';m=read(p);assert len(m['samples'])==20
 clocks=['13:11:'+v for v in ['34','37','40','43','45','48','52','55','58']]+['13:12:'+v for v in ['01','04','07','10','13','16','19','22','25','28','31']]
 merge(OUT/'screening_source_reviews.json',[dict(review_id='20261015/'+w,date='20261015',split='train',camera=11,reviewer='assistant_visual_review',reviewed_at=stamp,source_member=m['source']['member'],source_sha256=m['source_sha256'],frames_manifest=str(p.relative_to(ROOT)),sampled_frames_visually_reviewed=20,reviewed_sheets=m['sheets'],accepted_complete_cycle=False,review_scope='All20 chronological sample tiles/four sheets inspected;3-second nominal cadence with camera clock irregularity retained.',observation='Covered gray stationary34-43, moving45-48, near threshold52, crosses55, clears58. Separate empty beige moves52-58, at station12:01; still visibly empty07. Cheese handling10-13 and subsequent fill16 onwards; conservative negative cut07 avoids contaminated label. Prior broad negative through12:14 is narrowed.',visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],visible_camera_clock=t,clock_read_uncertainty_seconds=1,image=m['samples'][i]['image'],usable_for_clock_alignment=False) for i,t in enumerate(clocks)])],'review_id')
 def ev(a,b):return evidence(m,a,b,p)
 labels=read(OUT/'reviewed_sequence_labels.json');save(OUT/'review_history/sequence_labels_before_20261031_55.json',labels)
 row=next(r for r in labels if r['sequence_id']=='20261015_fifth_gray_departure1311_partial');row['reviewed_at']=stamp;row['partial_reason']='Dense11 departure reviewed; exact15 entry and later scale/storage identity remain unresolved.'
 row['observation']='Fresh filling evidence retained. Covered gray leaves station11:45-48, doorway11:52-58. No room15 clock inferred.'
 stage=next(x for x in row['stages'] if x['stage']=='loaded_departure_11');stage.update(visible_camera_clock_interval=['13:11:45','13:11:58'],doorway_crossing_camera11_interval=['13:11:52','13:11:58'],clock_uncertainty_seconds=3,observation='Moving45-48, near threshold52, crosses55, clear58.',evidence=stage['evidence']+[ev(3,8)])
 row['evidence'].append(ev(0,8))
 neg=next(r for r in labels if r['sequence_id']=='20261015_empty_beige_replacement1311');neg.update(reviewed_at=stamp,visible_camera_clock_interval=['13:11:52','13:12:07'],observation='Distinct empty beige moves52-58, set at station12:01, visibly empty07. Stop before handling/placement10-13. Prior broad endpoint12:14 superseded; old evidence retained in review_history only.',evidence=[ev(6,11)])
 save(OUT/'reviewed_sequence_labels.json',labels)
 state['last_completed']+=['Batch55:20 dense15Oct11 samples reviewed. Fifth doorway crossing refined11:52-58. Empty replacement negative narrowed to11:52-12:07, removing broad endpoint12:14 because first cheese handling occurs10-13. Historical annotation saved; no duplicate counts or complete-cycle claim.']
 state['priority_next']=['Batch55 fifth_departure1311_dense_cam11 fully reviewed. Threshold11:52-58; replacement negative stops12:07, new fill begins around12:10-16. Do not repeat dense extraction.','Continue15 scale/storage sources13:16:08-16:45 and13:17:30-18:27; missing11:52-58 room15 entry remains. Sixth beige fill continues17:34;11 remaining after600PTS unreviewed.']+[p for p in state['priority_next'] if p.startswith('Known gaps') or p.startswith('25/28')]
 state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False);state.setdefault('completed_curation_runs',[]).append(RUN);state['scripts'].append('work/record_tank_sequence_batch_20261031_55.py');save(OUT/'continuation_state.json',state)
 print('Recorded20 samples; refined departure and corrected negative endpoint')
if __name__=='__main__':main()
