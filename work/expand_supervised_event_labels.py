from pathlib import Path
import json
R=Path('outputs/facility_dataset/temporal_pipeline');B=R/'review_batch_01'
def save(cid,entries,negatives,pending):
 source=json.loads((B/cid/'annotation.json').read_text());events=[]
 for eid,worker,pick,release in entries:
  events.append({'event_id':cid+'_'+eid,'worker_track':worker,'pickup_window_s':pick,'release_window_s':release,
  'quantity':2,'action':'whole_cheese_blocks_to_filling_tank','destination':'filling_tank','tray_cycle_id':cid+'_local_cycle',
  'quantity_basis':'assistant visual observation of two separate whole blocks, one in each hand',
  'review_status':'assistant_annotated; not independently expert verified','boundary_precision':'interval from 4 fps review'})
 out={'source':source,'reviewed_dense_frames':64,'sampling_fps_for_review':4,'events':events,
 'non_placement_events':negatives,'unresolved':pending,'reviewed_event_block_sum':sum(e['quantity'] for e in events),
 'whole_clip_count':None,'tank_total':None,'capacity_used_to_invent_labels':False,
 'approved_for_production_evaluation':False,'reviewer':'assistant visual review'}
 (B/cid/'reviewed_events.json').write_text(json.dumps(out,indent=2))
 return out
save('B004',[('L1','filling_left',[8.625,11.375],[11.875,12.625])],
 [{'action':'large_grid_separator_to_rack','worker_track':'filling_left','window_s':[.125,5.125],'whole_blocks_placed':0}],
 [{'window_s':[13.375,16],'reason':'Next pickup visible; complete release falls outside clip.'}])
save('B007',[('L1','filling_left',[2.625,3.875],[4.125,4.875]),('R1','filling_right',[2.875,4.625],[4.875,5.625])],
 [{'action':'large_grid_separator_to_rack','worker_track':'filling_right','window_s':[.125,1.625],'whole_blocks_placed':0},
 {'action':'adjust_existing_tank_contents','worker_track':'filling_left','window_s':[5.125,6.625],'whole_blocks_placed':0},
 {'action':'liner_or_cover_handling','worker_track':'filling_left','window_s':[10.625,13.375],'whole_blocks_placed':0}],
 [{'window_s':[14.125,16],'reason':'Next pickups at end; complete releases not established.'}])
save('B021',[('R1','filling_right',[.125,.625],[.875,2.375]),('L1','filling_left',[1.625,2.625],[2.875,3.625])],
 [{'action':'large_grid_separator_to_rack','worker_track':'filling_right','window_s':[3.125,7.125],'whole_blocks_placed':0},
 {'action':'waiting','worker_track':'both','window_s':[8.125,15.875],'whole_blocks_placed':0}],
 [{'window_s':[0,1.625],'worker_track':'filling_left','reason':'Initial transfer already underway at start; original pickup not observed.'}])
r=save('B022',[('R1','filling_right',[4.375,11.875],[13.125,14.125])],
 [{'action':'large_grid_separator_to_rack','worker_track':'filling_right','window_s':[2.125,4.125],'whole_blocks_placed':0}],
 [{'window_s':[14.125,16],'reason':'New pickups near clip end; release completion not established.'}])
r['events'][0]['hand_pickups']=[{'hand_track':'early_pickup_hand','quantity':1,'pickup_window_s':[4.375,4.875]},
 {'hand_track':'late_pickup_hand','quantity':1,'pickup_window_s':[11.125,11.875]}]
r['events'][0]['note']='First block is held while tank is absent; second is picked later. Count only after both are placed in arriving empty tank. Neither pickup nor separator motion adds production.'
(B/'B022/reviewed_events.json').write_text(json.dumps(r,indent=2))
save('B023',[('L1','filling_left',[4.875,6.125],[6.375,7.125]),('R1','filling_right',[5.875,7.125],[7.625,8.625]),
 ('L2','filling_left',[7.125,8.375],[8.625,9.375]),('R2','filling_right',[9.125,10.125],[10.375,11.625]),
 ('L3','filling_left',[9.625,11.125],[11.625,12.375])],
 [{'action':'waiting','worker_track':'both','window_s':[.125,4.125],'whole_blocks_placed':0},
 {'action':'large_grid_separator_to_rack','worker_track':'filling_right','window_s':[12.625,14.875],'whole_blocks_placed':0}],
 [{'window_s':[15.375,16],'reason':'Next tray appears; no completed new transfer reviewed.'}])
labels=[json.loads(p.read_text()) for p in B.glob('B*/reviewed_events.json')]
events=[e for r in labels for e in r.get('events',[]) if e.get('action')=='whole_cheese_blocks_to_filling_tank']
progress=json.loads((R/'supervision_progress.json').read_text());progress.update({
 'dense_event_reviewed_sources':['B004','B006','B007','B009','B011','B019','B020','B021','B022','B023'],
 'dense_block_event_labelled_sources':[r['source']['clip_id'] for r in labels if r.get('events')],
 'remaining_sources_for_dense_event_review':14,'manually_annotated_complete_two_block_transfers':len(events),
 'manual_blocks_in_selected_events':sum(e['quantity'] for e in events),
 'quantity_policy':'Actual observed placements only. No fixed total per tank and no fixed quantity per gesture.',
 'pretraining_completed':True,'supervised_action_model_trained':False,
 'note':'Expanded manual labels. Partial clip counts are not complete tank counts. Event-proposal training is next; no automatic production measurements claimed.'})
(R/'supervision_progress.json').write_text(json.dumps(progress,indent=2));print('Complete reviewed transfers',len(events),'blocks in those events',sum(e['quantity'] for e in events))
