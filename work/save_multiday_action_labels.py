import pathlib,json,importlib.util,sys
ROOT=pathlib.Path('outputs/facility_dataset/temporal_pipeline');BATCH=ROOT/'review_batch_01'
annotation=json.loads((BATCH/'B009/annotation.json').read_text())
# Reviewed 64 sequential frames at 4 fps. Timing windows preserve uncertainty;
# the quantities are assistant visual annotations, not an automatic model output.
transfers=[
 ('L1','filling_left',3.875,4.625,[4.875,5.875]),
 ('R1','filling_right',4.375,5.125,[5.625,6.375]),
 ('L2','filling_left',6.375,7.375,[7.875,8.625]),
 ('R2','filling_right',7.125,8.125,[8.625,9.375]),
 ('L3','filling_left',9.125,10.375,[10.375,11.125]),
]
events=[]
for id,worker,start,carrying,release in transfers:
 events.append({'event_id':'B009_'+id,'worker_track':worker,'pickup_window_s':[start,carrying],
  'release_window_s':release,'action':'whole_cheese_blocks_to_filling_tank','quantity':2,
  'quantity_basis':'assistant visual review of both hands carrying whole white blocks',
  'destination':'filling_tank','tray_cycle_id':'B009_visible_tray_cycle_01',
  'hand_assignment_status':'two visible carrying hands; anatomical left/right labels not assigned',
  'boundary_precision':'interval, not exact native-frame boundary',
  'review_status':'assistant_annotated; not independently expert verified'})
label={'source':annotation,'reviewed_dense_frames':64,'sampling_fps_for_review':4,
 'reviewer':'assistant visual review','events':events,
 'non_placement_events':[{'action':'empty_separator_tray_removal','window_s':[10.875,13.875],'quantity':0}],
 'reviewed_cycle_window_s':[3.875,11.125],'reviewed_cycle_block_sum':sum(e['quantity'] for e in events),
 'tray_capacity_prior':10,'count_is_for_one_selected_cycle':True,'whole_clip_count':None,'tank_total':None,
 'tray_slot_labels':'Individual slot identities/levels remain unlabelled; capacity was not used to assign event quantities.',
 'approved_for_production_evaluation':False,
 'split':'unassigned; reserve complete source/recording groups before training'}
(BATCH/'B009/reviewed_events.json').write_text(json.dumps(label,indent=2))
negatives=[]
for clip_id,action in [('B003','empty_tank_liner_preparation'),('B017','empty_container_preparation_and_movement')]:
 source=json.loads((BATCH/clip_id/'annotation.json').read_text())
 r={'source':source,'reviewer':'assistant visual review of 12 sequential one-second context frames',
  'window_s':[0,12],'action':action,'whole_cheese_blocks_placed':0,
  'review_basis':'The filling tank and conveyor remain visibly empty of whole blocks; lining/moving empty bins is not a cheese placement.',
  'timing_precision':'coarse negative interval; native-frame transitions not annotated',
  'status':'assistant_reviewed_negative; not independently expert verified'}
 (BATCH/clip_id/'reviewed_events.json').write_text(json.dumps(r,indent=2));negatives.append(r)
spec=importlib.util.spec_from_file_location('facility_counter',ROOT/'event_counter.py');m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
ledger=m.ProductionLedger()
for e in events:
 for hand in ['visible_hand_1','visible_hand_2']:
  transfer=m.HandTransfer(event_id=e['event_id']+'_'+hand,worker_track=e['worker_track'],hand_track=hand,
    tray_cycle_id=e['tray_cycle_id'],tank_id='B009_local_filling_tank',picked_quantity=1,
    pickup_object='whole_cheese_block',release_object='whole_cheese_block',destination='filling_tank',
    pickup_observed=True,release_observed=True,release_relative_s=sum(e['release_window_s'])/2,
    quantity_basis='visually_reviewed',pickup_episode_id=e['event_id'])
  ledger.ingest(transfer);ledger.ingest(transfer)
report=ledger.report();assert report['confirmed_blocks_by_tank']=={'B009_local_filling_tank':10}
report.update({'input_basis':'manual reviewed event labels; no image model inference',
 'reference_cycle_block_sum':10,'whole_clip_or_day_total':False,
 'tray_check':ledger.corroborate_tray('B009_visible_tray_cycle_01',None)})
(ROOT/'multiday_reference_replay.json').write_text(json.dumps(report,indent=2))
summary={'user_confirmed_example':'21 October A028 H4/H5: two-block pickup, release visually reviewed',
 'additional_reviewed_source':'3 October B009: five annotated two-block transfer episodes in one selected cycle',
 'additional_negative_sources':['1 October B003, first 12s','21 October B017, first 12s'],
 'reviewed_batch_sources':3,'prepared_batch_sources':24,'remaining_batch_sources':21,
 'trained_model':False,'reference_counts_are_manual_annotations':True}
(ROOT/'supervision_progress.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
