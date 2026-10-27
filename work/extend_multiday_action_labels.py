from pathlib import Path
import json
root=Path('outputs/facility_dataset/temporal_pipeline');batch=root/'review_batch_01'
rows=json.loads((batch/'batch_manifest.json').read_text())
notes={
'B001':('no_filling_activity','Person passes; filling station empty.'),
'B002':('empty_containers','Two visibly empty blue-lined bins; conveyor empty.'),
'B003':('empty_container_preparation','Empty bin liner preparation; no whole blocks on conveyor.'),
'B004':('separator_and_block_handling','Large grid separator handling and subsequent hand transfers; precise event review pending.'),
'B005':('station_interruption','Block-loaded conveyor and covered/white-topped tank; worker adjusts equipment, then leaves.'),
'B006':('block_transfers','Two workers transfer visible whole blocks, then separator moved and next tray arrives.'),
'B007':('block_transfers_and_pause','Block transfer activity followed by pause at conveyor; precise count pending.'),
'B008':('separator_handling','Worker repeatedly lifts large grid separators; second worker works at side crumb bin.'),
'B009':('block_transfers','Selected five paired transfers already annotated at 4 fps.'),
'B010':('waiting','Workers wait beside filled/white-topped tank; conveyor empty.'),
'B011':('tank_exchange','White-topped tank removed; visibly empty blue-lined replacement arrives; filling resumes.'),
'B012':('block_transfers_and_separator','Paired block transfers and large grid separator handling.'),
'B013':('station_pause','Worker steps away; whole blocks already in tank; conveyor empty.'),
'B014':('waiting_then_block_transfers','Pause followed by next tray and paired block transfer activity.'),
'B015':('station_cleanup','No filling tank; workers handle/clean conveyor area.'),
'B016':('no_filling_activity','Station has no filling tank, no workers and no visible cheese blocks.'),
'B017':('empty_container_preparation','Empty containers/liners; no block-loaded tray.'),
'B018':('empty_containers','Empty unlined bins; workers enter near end.'),
'B019':('block_transfers','Paired transfers; separate hand movement toward side/back needs destination review.'),
'B020':('block_transfers_and_separator','One active worker transfers pairs; separator moved; next layer transferred.'),
'B021':('block_transfers_then_waiting','Transfers near start, separator handling, then empty conveyor and waiting.'),
'B022':('separator_handling_and_empty_tank_arrival','Separator handling while no filling tank, then empty bin arrives and filling starts.'),
'B023':('waiting_then_block_transfers','Conveyor empty initially; new tray arrives and both workers transfer blocks.'),
'B024':('waiting','White-topped tank at station; workers waiting, empty conveyor.'),
}
negative_ids={'B001','B002','B003','B016','B017','B018'}
for r in rows:
 cid=r['clip_id'];category,note=notes[cid]
 review={'clip_id':cid,'source_sha256':r['source_sha256'],'date':r['date'],
 'reviewer':'assistant visual review','review_kind':'coarse sequential-context triage',
 'sample_fps':1,'frames_viewed':len(list((batch/cid).glob('s_*.jpg'))),
 'reviewed_sample_centers_s':[i+.5 for i in range(len(list((batch/cid).glob('s_*.jpg'))))],
 'activity':category,'observation':note,'exact_event_boundaries_reviewed':False,
 'whole_clip_block_count':0 if cid in negative_ids else None,
 'negative_count_basis':'No visible whole block source or placement at sampled contexts; not native-frame exhaustive verification.' if cid in negative_ids else None,
 'clock_verified':False,'production_report_approved':False}
 (batch/cid/'context_review.json').write_text(json.dumps(review,indent=2))
 r['context_review_status']='assistant reviewed at 1 fps; not exact event annotation'
 r['split']='test' if r['date']=='2026-10-03' else 'train_candidate'
(batch/'batch_manifest.json').write_text(json.dumps(rows,indent=2))

def save_events(cid,entries,non_events,pending):
 events=[]
 for eid,worker,pick,release,cycle in entries:
  events.append({'event_id':cid+'_'+eid,'worker_track':worker,'pickup_window_s':pick,'release_window_s':release,
   'action':'whole_cheese_blocks_to_filling_tank','quantity':2,'destination':'filling_tank','tray_cycle_id':cid+'_'+cycle,
   'quantity_basis':'assistant visual review: one visible whole block carried in each of two hands',
   'boundary_precision':'interval from 4 fps review, not exact native-frame boundary',
   'review_status':'assistant annotated, not independently expert verified'})
 result={'source':next(r for r in rows if r['clip_id']==cid),'reviewed_dense_frames':64,'sampling_fps_for_review':4,
 'reviewer':'assistant visual review','events':events,'non_placement_events':non_events,'unresolved':pending,
 'reviewed_event_block_sum':sum(e['quantity'] for e in events),'whole_clip_count':None,'tank_total':None,
 'tray_capacity_prior':10,'capacity_used_to_invent_labels':False,'approved_for_production_evaluation':False}
 (batch/cid/'reviewed_events.json').write_text(json.dumps(result,indent=2))
 return result
save_events('B006',[
 ('R1','filling_right',[.625,1.875],[2.125,2.875],'partial_cycle_01'),
 ('L1','filling_left',[2.625,3.625],[3.875,4.625],'partial_cycle_01'),
 ('R2','filling_right',[3.875,5.125],[5.375,7.375],'partial_cycle_01'),
 ('R3','filling_right',[11.625,12.625],[13.125,13.875],'cycle_02'),
 ('L2','filling_left',[11.875,13.375],[13.625,14.625],'cycle_02')],
 [{'action':'large_grid_separator_to_rack','worker_track':'filling_right','window_s':[8.875,10.375],'whole_blocks_placed':0}],
 [{'window_s':[0,2.375],'worker_track':'filling_left','reason':'Clip starts during existing placement; pickup absent.'},
 {'window_s':[5.375,8.875],'worker_track':'filling_left','reason':'Pointing/repositioning versus transfer not confidently resolved; excluded from event labels.'},
 {'window_s':[14.875,16],'worker_track':'filling_right','reason':'Pickup visible near end; completed release not fully observed.'}])
save_events('B019',[
 ('L1','filling_left',[3.375,4.375],[4.625,5.375],'cycle_01'),
 ('R1','filling_right',[3.875,5.125],[5.625,6.875],'cycle_01'),
 ('L2','filling_left',[5.875,7.125],[7.375,8.125],'cycle_01'),
 ('L3','filling_left',[8.625,9.875],[10.125,10.875],'cycle_01'),
 ('R2','filling_right',[10.125,11.375],[11.875,12.875],'cycle_01')],
 [{'action':'large_grid_separator_to_rack','worker_track':'filling_right','window_s':[13.375,15.125],'whole_blocks_placed':0}],
 [{'window_s':[7.125,8.875],'worker_track':'filling_right','reason':'Separate turn/hand motion toward side/back; exact object and disposal destination unconfirmed.'}])
save_events('B020',[
 ('R1','filling_right',[1.375,2.375],[3.125,4.125],'partial_cycle_01'),
 ('R2','filling_right',[4.625,6.125],[6.375,7.875],'partial_cycle_01'),
 ('R3','filling_right',[10.375,11.875],[12.375,14.625],'cycle_02')],
 [{'action':'large_grid_separator_to_rack','worker_track':'filling_right','window_s':[9.375,10.375],'whole_blocks_placed':0}],
 [{'window_s':[0,1.375],'worker_track':'filling_right','reason':'Placement underway at clip start; pickup not present.'},
 {'window_s':[8.125,9.375],'worker_track':'filling_right','reason':'Hand contact on tray before separator removal; no independently confirmed block transfer.'}])
transfer={'source':next(r for r in rows if r['clip_id']=='B011'),'reviewer':'assistant visual review, 64 frames at 4 fps',
 'events':[{'event_id':'B011_tank_out_01','action':'loaded_tank_leaves_filling_station','window_s':[3.875,8.125],
 'quantity':1,'load_state_basis':'White-covered loaded tank at filling station is moved away; no weight readout or destination visible.',
 'camera15_match':None,'arrival_in_aging_confirmed':False},
 {'event_id':'B011_empty_in_01','action':'empty_tank_arrives_filling_station','window_s':[9.375,13.625],
 'quantity':1,'load_state_basis':'Clearly visible empty blue liner and bin interior.'}],
 'production_day_total':None,'tank_identity_cross_camera':None,'clock_verified':False,'split':'test',
 'block_placements_after_exchange':'Activity visible at end; not fully counted/annotated.'}
(batch/'B011/reviewed_tank_events.json').write_text(json.dumps(transfer,indent=2))
summary={'prepared_batch_sources':24,'context_reviewed_sources':24,'context_review_fps':1,
 'dense_event_reviewed_sources':['B006','B009','B011','B019','B020'],
 'dense_block_event_labelled_sources':['B006','B009','B019','B020'],
 'remaining_sources_for_dense_event_review':19,'manually_annotated_complete_two_block_transfers':18,
 'manual_blocks_in_selected_events':36,'manual_tank_out_events':1,'manual_empty_tank_in_events':1,
 'whole_clip_or_day_counts':False,'trained_model':False,
 'heldout_date':'2026-10-03','independently_expert_verified':False,
 'note':'Context screening is completed; it is not full hand-event labelling. Counts are assistant visual labels, not model predictions.'}
(root/'supervision_progress.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
