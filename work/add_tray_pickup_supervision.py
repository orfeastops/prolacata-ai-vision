import pathlib,json,importlib.util,sys
from PIL import Image,ImageDraw,ImageFont
ROOT=pathlib.Path('outputs/facility_dataset');AUDIT=ROOT/'annotation_audit';OUT=ROOT/'temporal_pipeline';OUT.mkdir(exist_ok=True)
reference=next(r for r in json.loads((AUDIT/'review_sample.json').read_text()) if r['audit_id']=='A028')
clip=json.loads((AUDIT/'action_review/first_temporal_annotations.json').read_text())
truth={
 'annotation_id':'user_A028_H4_H5_two_block_pickup',
 'source_sha256':reference['frame']['source_sha256'],
 'reference_image':reference['view']['image'],
 'source_relative_reference_s':reference['frame']['relative_pts_seconds'],
 'source_clock_verified':False,
 'user_review':{'confirmed_quantity':2,'reference_hand_labels':['H4','H5'],
  'stage':'grasping_before_tank_release','whole_blocks_per_visible_hand':1,
  'tray_capacity_positions':10,'tray_height_cue':'Positions become lower when whole blocks are removed',
  'height_cue_basis':'user description and qualitative visual review; no physical height measurement'},
 'worker_track':'filling_right',
 'tray_track':'tray_21oct_source68cafd_episode_122',
 'pickup_episode_id':'right_worker_pickup_126_127',
 'release_review':{'clip_release_window_s':[5.375,5.875],'source_release_window_s':[127.375,127.875],
  'reviewer':'assistant visual sequence review','destination':'filling_tank','quantity':2,
  'release_timing':'approximate; needs native-frame boundary review'},
 'before_image':'annotation_audit/action_review/t_018.jpg',
 'carrying_image':'annotation_audit/action_review/t_021.jpg',
 'after_image':'annotation_audit/action_review/t_023.jpg',
 'labels':{'pickup_whole_blocks':2,'tank_placement_whole_blocks':2,
  'tray_capacity':10,'tray_occupied_slots_before':None,'tray_occupied_slots_after':None,
  'per_slot_height_before':None,'per_slot_height_after':None,
  'observed_height_change':'qualitative corroborating cue; slot identities not yet aligned'},
 'count_scope':'one reviewed right-worker transfer; not a complete tray, clip, tank or day total',
 'constraints':['Tray identity and camera perspective must be matched before comparing slot surfaces.',
  'Do not automatically label ten occupied positions from tray capacity.',
  'Masked/occluded/off-screen positions stay unknown.',
  'Pickup creates a pending transfer; only release into the filling tank adds production.',
  'Two hands and the same tray change are two views of one event, never two separate additions.',
  'Whole block placements, crumb disposal and separator handling require distinct labels.']}
(OUT/'user_confirmed_tray_example.json').write_text(json.dumps(truth,indent=2))
rules={'tray_capacity':{'value':10,'source':'user'},
 'slot_states':['whole_block_present','lower_exposed_tray','unknown_occluded','unknown_offscreen'],
 'action_states':['reach','grasp_whole_block','carrying_whole_block','release_into_filling_tank','crumb_disposal','separator_handling','return_to_conveyor','unknown'],
 'quantity_target':'whole blocks released into a particular filling tank',
 'height_features':'apparent raised/lower surface and boundary appearance after motion alignment; not metric depth',
 'tray_geometry':'track four tray corners, rectify perspective, preserve visibility masks, assign stable slot IDs',
 'source_of_truth':'reviewed actions and tray-state pairs, including user corrections',
 'mismatch_policy':'retain uncertainty and send conflicting episodes for review; never force capacity 10 or tank standard 228'}
(OUT/'tray_action_label_spec.json').write_text(json.dumps(rules,indent=2))
for e in clip['events']:
 if e['action']=='whole_cheese_blocks_to_filling_tank':
  e['pickup_quantity_basis']='user confirmed A028 H4/H5 plus assistant sequence review'
  e['user_reference_annotation']=truth['annotation_id']
  e['tray_capacity_positions']=10
  e['tray_height_cue']='qualitative corroboration; exact per-slot levels remain unlabelled'
clip['rules']=list(dict.fromkeys(clip['rules']+truth['constraints'][:5]))
(AUDIT/'action_review/first_temporal_annotations.json').write_text(json.dumps(clip,indent=2))
spec=importlib.util.spec_from_file_location('facility_counter',OUT/'event_counter.py');module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
ledger=module.ProductionLedger()
for hand in ['H4','H5']:
 event=module.HandTransfer(event_id=f'{truth["pickup_episode_id"]}_{hand}',worker_track='filling_right',hand_track=hand,
   tray_cycle_id=truth['tray_track'],pickup_episode_id=truth['pickup_episode_id'],tank_id='local_filling_tank_21oct_1122',picked_quantity=1,
   pickup_object='whole_cheese_block',release_object='whole_cheese_block',destination='filling_tank',
   pickup_observed=True,release_observed=False,release_relative_s=None,quantity_basis='user_reviewed')
 ledger.ingest(event)
before=ledger.report()
for hand in ['H4','H5']:
 event=module.HandTransfer(event_id=f'{truth["pickup_episode_id"]}_{hand}',worker_track='filling_right',hand_track=hand,
   tray_cycle_id=truth['tray_track'],pickup_episode_id=truth['pickup_episode_id'],tank_id='local_filling_tank_21oct_1122',picked_quantity=1,
   pickup_object='whole_cheese_block',release_object='whole_cheese_block',destination='filling_tank',
   pickup_observed=True,release_observed=True,release_relative_s=127.625,quantity_basis='user_reviewed')
 ledger.ingest(event);ledger.ingest(event)
result={'scope':truth['count_scope'],'before_release':before,'after_release':ledger.report(),
 'tray_corroboration':ledger.corroborate_tray(truth['tray_track'],None,pickup_episode_ids=[truth['pickup_episode_id']]),
 'important':'Slot change has no numerical value yet; user-confirmed hand quantity and reviewed release provide this example quantity.'}
assert not before['confirmed_blocks_by_tank']
assert list(result['after_release']['confirmed_blocks_by_tank'].values())==[2]
(OUT/'reference_event_replay.json').write_text(json.dumps(result,indent=2))
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17)
panels=[('t_018.jpg','1. Before right-worker pickup | clip ~4.375s'),
 ('t_019.jpg','2. H4/H5 grasp two blocks | user-confirmed quantity'),
 ('t_021.jpg','3. Two blocks being carried | placement still pending'),
 ('t_023.jpg','4. Release reviewed | this transfer adds two blocks')]
canvas=Image.new('RGB',(1280,800),'white');draw=ImageDraw.Draw(canvas)
for i,(name,title) in enumerate(panels):
 x=i%2*640;y=i//2*400
 canvas.paste(Image.open(AUDIT/'action_review'/name),(x,y+40));draw.text((x+5,y+10),title,font=font,fill='black')
canvas.save(OUT/'tray_pickup_to_placement.jpg',quality=95)
print('User correction saved. Replay: pickup=0 confirmed placements; reviewed release=2; duplicates add zero.')
