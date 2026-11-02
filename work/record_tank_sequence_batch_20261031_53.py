import datetime as dt
from pathlib import Path
from record_tank_boundary_review_20261031 import read,save,evidence
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/tank_transfer_training_v1/dataset_v1';RUN='sequence_review_20261031_53'
def main():
 state=read(OUT/'continuation_state.json')
 if RUN in state.get('completed_curation_runs',[]):return
 stamp=dt.datetime.now(dt.timezone.utc).isoformat()
 paths=[OUT/'sequence_review/20261015'/w/'frames.json' for w in ['fourth_route1309_cam15','fourth_park1310_cam15']];metas=[read(p) for p in paths]
 inspected=[[8,9,10,11],[0,1,7]]
 reviews=read(OUT/'screening_source_reviews.json');save(OUT/'review_history/screening_reviews_before_20261031_53.json',reviews)
 for p,m,indices in zip(paths,metas,inspected):
  row=next(r for r in reviews if r['frames_manifest']==str(p.relative_to(ROOT)))
  row.setdefault('supplemental_visual_reviews',[]).append(dict(reviewed_at=stamp,reviewer='assistant_visual_review',scope='Full native1920x1080 context; existing samples reused, not added to presentation count.',sample_indices=indices,image_evidence=[m['samples'][i]['image'] for i in indices],observation='Left wall/row now visible. Gray load approaches wall-side slot10:01-10, parked by10:24 with bare jack beside it; remains same position10:42 and11:00. Actual fork withdrawal between10:10 and24 is not recorded by these samples. Different beige empty pair at left wall; one is taken toward shared doorway.'))
 save(OUT/'screening_source_reviews.json',reviews)
 labels=read(OUT/'reviewed_sequence_labels.json');save(OUT/'review_history/sequence_labels_before_20261031_53.json',labels)
 row=next(r for r in labels if r['sequence_id']=='20261015_fourth_gray_departure1303_partial');row['reviewed_at']=stamp
 route=row['unlinked_followup']['later_route'];route.update(observation='Full-frame followup shows covered gray from staging approaching left-wall slot10:01-10. By10:24 tank is parked and jack visibly empty nearby; tank stays through11:00.14-second sampled/source gap10:10-24 includes unseen fork withdrawal. Local parked state confirmed; identity with fresh03-minute departure and earlier scale remains unresolved.',storage_confirmed=True,storage_confirmation_scope='Later local track parked state only; not a complete production cycle.',parking_and_release_interval=['13:10:10','13:10:24'],fork_withdrawal_directly_observed=False,source_join_gap_seconds=14,full_frame_evidence=[evidence(metas[0],8,11,paths[0]),evidence(metas[1],0,1,paths[1]),evidence(metas[1],7,7,paths[1])])
 save(OUT/'reviewed_sequence_labels.json',labels)
 state['last_completed']+=['Batch53:seven existing15Oct frames inspected at full native size, without inflating sample count. Gray load confirmed parked by left wall13:10:24 and still11:00; bare jack visible, but actual withdrawal falls in14-second source/sample gap10:10-24. Local storage state documented, origin/entry still unresolved, no complete-cycle promotion.']
 state['priority_next']=['Batch53 full-frame checks resolved off-crop parked state for later gray route by10:24; source/sample gap10:10-24 and missing03-minute entry retained. Do not repeat these seven full-frame checks.','Prioritise fifth fresh load: starts03:30-32, fills through07:42. Next11 source13:07:34-31:55 can locate next departure; check available15 counterparts. No new cycles from color or clock alone.']+[p for p in state['priority_next'] if p.startswith('Known gaps') or p.startswith('25/28')]
 state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False);state.setdefault('completed_curation_runs',[]).append(RUN);state['scripts'].append('work/record_tank_sequence_batch_20261031_53.py');save(OUT/'continuation_state.json',state)
 print('Seven existing native frames reviewed; local storage state refined, no counts inflated')
if __name__=='__main__':main()
