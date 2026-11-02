import datetime as dt
from pathlib import Path
from record_tank_boundary_review_20261031 import read,save,merge,evidence
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'outputs/tank_transfer_training_v1';OUT=BASE/'dataset_v1'
RUN='sequence_review_20261031_50'
def main():
 state=read(OUT/'continuation_state.json')
 if RUN in state.get('completed_curation_runs',[]):return
 stamp=dt.datetime.now(dt.timezone.utc).isoformat()
 windows={'fill':('fourth_fill1302_cam11',22,{0:'13:02:10',1:'13:02:42',2:'13:02:57',3:'13:03:12',4:'13:03:27',5:'13:03:42',8:'13:04:27',21:'13:07:42'}),'search':('fourth_search1307_cam15',5,{0:'13:07:48',1:'13:08:08',2:'13:08:11',3:'13:08:14',4:'13:08:17'})}
 paths={k:OUT/'sequence_review/20261015'/w/'frames.json' for k,(w,n,c) in windows.items()};metas={k:read(p) for k,p in paths.items()}
 notes={'fill':'All22 chronological samples/four sheets viewed. Initial02:10 then02:42. Covered station tank still present42/57, at threshold03:12, gone27. Separate empty gray already waiting42, moved toward station03:12, visibly empty at station27, filling starts by42 and continues07:42. Scale through door empty early; covered body appears04:27 and remains through07:42, but staging trajectory and exact entry not sampled. Final actualclock07:42 exceeds filename end.','search':'All5 samples/one sheet viewed. Initial07:48 then08:08,11,14,17. Gray tank already at scale, workers handle liner/top. No new entry crossing or storage observed. No identity assignment solely from similar color or timestamps.'}
 for k,m in metas.items():
  w,n,c=windows[k];assert len(m['samples'])==n and m['source']['split']=='train'
  merge(OUT/'screening_source_reviews.json',[dict(review_id='20261015/'+w,date='20261015',split='train',camera=m['source']['camera'],reviewer='assistant_visual_review',reviewed_at=stamp,source_member=m['source']['member'],source_sha256=m['source_sha256'],frames_manifest=str(paths[k].relative_to(ROOT)),sampled_frames_visually_reviewed=n,reviewed_sheets=m['sheets'],accepted_complete_cycle=False,observation=notes[k],review_scope='Chronological sampled-image inspection; not exhaustive native-frame viewing.',visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],visible_camera_clock=t,clock_read_uncertainty_seconds=1,image=m['samples'][i]['image'],usable_for_clock_alignment=False) for i,t in c.items()])],'review_id')
 paths['origin']=OUT/'sequence_review/20261015/third_gray_after1252_cam11/frames.json';metas['origin']=read(paths['origin'])
 def ev(k,a,b):return evidence(metas[k],a,b,paths[k])
 shared=dict(date='20261015',split='train',reviewer='assistant_visual_review',reviewed_at=stamp,dataset_release_accepted=False,cycle_id=None,camera_clock_offset_seconds=None)
 partial=dict(shared,sequence_id='20261015_fourth_gray_departure1303_partial',review_status='reviewed_partial_sequence',production_entry_count_target=None,partial_reason='Exact entry15 and scale/storage identity need denser trajectory review. Broad11 sampling brackets departure only.',observation='Previously reviewed fresh filling54:15-13:02:15 followed by covered departure02:57-03:27. Initial source02:10 overlaps prior filling, first noninitial42 leaves27-second sampled join; no exact continuity claim.',evidence=[ev('origin',5,37),ev('fill',0,4)],stages=[dict(stage='filling_observed',camera=11,evidence=[ev('origin',5,37)]),dict(stage='loaded_departure_11',camera=11,visible_camera_clock_interval=['13:02:57','13:03:27'],observation='At station02:57, at door03:12, gone03:27; denser evidence needed.',evidence=[ev('fill',2,4)])],unlinked_followup=dict(observation='Gray scale body through11 door04:27-07:42 and in15 at07:48/08:08-17. Identity across entry/staging unresolved; no completed cycle.',evidence=[ev('fill',8,21),ev('search',0,4)]))
 neg=dict(shared,sequence_id='20261015_empty_replacement1303',review_status='accepted_negative_sequence',production_entry_count_target=0,camera=11,negative_class='empty_tank_internal_reposition',tracked_tank_count=1,visible_camera_clock_interval=['13:03:12','13:03:27'],observation='Distinct visibly empty lined gray tank pushed from left waiting area into filling station. Stop before cheese appears03:42.',label_scope='Replacement track only, not departing covered load.',evidence=[ev('fill',3,4)])
 save(OUT/'review_history/sequence_labels_before_20261031_50.json',read(OUT/'reviewed_sequence_labels.json'));merge(OUT/'reviewed_sequence_labels.json',[partial,neg],'sequence_id')
 inv=read(BASE/'archive_inventory.json');src={m['source']['member']:m['source_sha256'] for m in metas.values()}
 for r in inv['records']:
  if r['member'] in src:r.update(pixel_inspected=True,sha256=src[r['member']])
 assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test')
 save(BASE/'archive_inventory.json',inv)
 state['last_completed']+=['Batch50:27 samples from two15Oct sources inspected. Fourth fresh load departure13:02:57-03:27 retained partial pending dense crossing/paired staging/storage. One distinct empty replacement negative added. Later scale observation unlinked; no new complete cycle or test pixels.']
 state['priority_next']=['Batch50 fourth_fill1302_cam11 and fourth_search1307_cam15 screened. Densify11 relative25-65 for03-minute departure/replacement. Available15 prior source13:02:16-02:39 precedes observed03:12 threshold; search alternate coverage before assuming entry.','Next15 sources13:09:32-10:13 and13:10:24-11:00 may show later scale/storage; retain missing entry. Fifth fresh fill starts03:42 and continues07:42; next11 source13:07:34-31:55 available.']+[p for p in state['priority_next'] if p.startswith('Known gaps') or p.startswith('25/28')]
 state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False);state.setdefault('completed_curation_runs',[]).append(RUN);state['scripts'].append('work/record_tank_sequence_batch_20261031_50.py');save(OUT/'continuation_state.json',state)
 print('Recorded27 samples,1 partial,1 negative')
if __name__=='__main__':main()
