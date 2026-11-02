import datetime as dt
from pathlib import Path
from record_tank_boundary_review_20261031 import read,save,merge,evidence
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/tank_transfer_training_v1/dataset_v1'
RUN='sequence_review_20261031_51'
def main():
 state=read(OUT/'continuation_state.json')
 if RUN in state.get('completed_curation_runs',[]):return
 stamp=dt.datetime.now(dt.timezone.utc).isoformat();w='fourth_departure1303_dense_cam11';p=OUT/'sequence_review/20261015'/w/'frames.json';m=read(p)
 assert len(m['samples'])==21 and m['source']['split']=='train'
 clocks=['13:02:52','13:02:54','13:02:56','13:02:58']+['13:03:'+str(i).zfill(2) for i in range(0,33,2)]
 merge(OUT/'screening_source_reviews.json',[dict(review_id='20261015/'+w,date='20261015',camera=11,split='train',reviewer='assistant_visual_review',reviewed_at=stamp,source_member=m['source']['member'],source_sha256=m['source_sha256'],frames_manifest=str(p.relative_to(ROOT)),sampled_frames_visually_reviewed=21,reviewed_sheets=m['sheets'],accepted_complete_cycle=False,review_scope='All21 sampled presentations/four sheets visually inspected, not exhaustive native-frame review.',observation='Covered load engaged02:54-03:02; moving from station04, across room06-08, near threshold10, crosses12-14, clear16. Distinct empty replacement starts moving10, reaches station16-18, interior empty through28; cheese placement visible30-32. Previous broad first-fill bound03:42 refined; no extra tank count. No room15 entry timestamp inferred.',visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],visible_camera_clock=t,clock_read_uncertainty_seconds=1,image=m['samples'][i]['image'],usable_for_clock_alignment=False) for i,t in enumerate(clocks)])],'review_id')
 def ev(a,b):return evidence(m,a,b,p)
 labels=read(OUT/'reviewed_sequence_labels.json');save(OUT/'review_history/sequence_labels_before_20261031_51.json',labels)
 row=next(r for r in labels if r['sequence_id']=='20261015_fourth_gray_departure1303_partial')
 row['reviewed_at']=stamp;row['partial_reason']='Dense11 departure reviewed; room15 incoming crossing, scale/staging identity and storage remain unverified.'
 row['observation']='Fresh filling evidence preserved; covered load moves from station03:04 and clears doorway by03:16. Doorway crossing bounded03:10-16. Independent room15 timestamp not inferred.'
 stage=next(s for s in row['stages'] if s['stage']=='loaded_departure_11')
 stage.update(visible_camera_clock_interval=['13:03:04','13:03:16'],doorway_crossing_camera11_interval=['13:03:10','13:03:16'],clock_uncertainty_seconds=2,observation='Across room04-08; near threshold10, crosses12-14, clear16. Sampled interval, not exact instant.',evidence=stage['evidence']+[ev(6,12)])
 row['evidence'].append(ev(0,12))
 neg=next(r for r in labels if r['sequence_id']=='20261015_empty_replacement1303');neg.update(reviewed_at=stamp,visible_camera_clock_interval=['13:03:10','13:03:28'],observation='Distinct empty gray replacement moved10-18 then remains visibly empty through28. First cheese visible30-32; negative ends before filling.',evidence=neg['evidence']+[ev(9,18)])
 save(OUT/'reviewed_sequence_labels.json',labels)
 state['last_completed']+=['Batch51:21 dense15Oct11 samples reviewed. Fourth departure refined03:04-16, doorway03:10-16. Existing empty replacement negative refined03:10-28; first subsequent cheese visible30-32. Previous label versions preserved; no duplicate negatives or complete-cycle promotion.']
 state['priority_next']=['Batch51 fourth_departure1303_dense_cam11 fully screened: departure03:04-16, threshold03:10-16, next filling03:30-32. Do not re-extract this window. Room15 entry remains unavailable in inspected sources.','Next15 sources13:09:32-10:13 and13:10:24-11:00 can extend scale/storage but cannot alone recover missing03-minute entry. Fifth fill continues through07:42; next11 source13:07:34-31:55 available.']+[p for p in state['priority_next'] if p.startswith('Known gaps') or p.startswith('25/28')]
 state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False);state.setdefault('completed_curation_runs',[]).append(RUN);state['scripts'].append('work/record_tank_sequence_batch_20261031_51.py');save(OUT/'continuation_state.json',state)
 print('Recorded21 dense samples; refined existing partial and negative')
if __name__=='__main__':main()
