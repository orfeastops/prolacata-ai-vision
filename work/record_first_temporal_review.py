import json,pathlib
root=pathlib.Path('outputs/facility_dataset/annotation_audit/action_review')
m=json.loads((root/'clip_manifest.json').read_text())
review={'source':m,'reviewer':'assistant visual inspection of 48 temporal frames at 4 fps',
 'review_scope':'initial action taxonomy and negative examples; frame-accurate block counts pending',
 'workers':{'filling_left':'foreground left worker','filling_right':'right side of filling tank',
            'background_observer':'upper left, standing with folded arms'},
 'events':[
  {'clip_start_s':0.0,'clip_end_s':1.05,'worker':'filling_right','action':'remove_large_separator_tray',
   'whole_cheese_blocks_count':0,'status':'assistant_reviewed_non_cheese_action',
   'note':'Large rectangular sheet/tray lifted across conveyor and moved to upper-right rails; beginning is clipped.'},
  {'clip_start_s':10.05,'clip_end_s':11.15,'worker':'filling_right','action':'remove_large_separator_tray',
   'whole_cheese_blocks_count':0,'status':'assistant_reviewed_non_cheese_action',
   'note':'Large rigid rectangle lifted and moved to upper-right rails after a batch is cleared.'},
  {'clip_start_s':0.0,'clip_end_s':12.0,'worker':'background_observer','action':'standing_no_placement',
   'whole_cheese_blocks_count':0,'status':'assistant_reviewed_negative',
   'note':'Both blue gloves visible but this worker does not place cheese in the filling tank.'},
 ],
 'pending_intervals':[
  {'clip_start_s':3.7,'clip_end_s':6.15,'action':'conveyor_to_tank_hand_cycles','whole_cheese_blocks_count':None},
  {'clip_start_s':6.15,'clip_end_s':8.7,'action':'conveyor_to_tank_hand_cycles','whole_cheese_blocks_count':None},
  {'clip_start_s':8.7,'clip_end_s':10.1,'action':'conveyor_to_tank_hand_cycles','whole_cheese_blocks_count':None}],
 'rules':['Count an observed block placement once at completed release into the filling tank.',
          'Track both hands separately for each worker; visible hand count is not placement count.',
          'Crumb disposal and separator handling are distinct non-whole-block actions.',
          'Keep occluded or unresolved quantities null; never substitute 228 per tank.',
          'Do not infer full-tank completion from these 12 seconds. Link full filling cycle and removal.'],
 'tank_completed_in_clip':None,'block_total_for_clip':None,'approved_for_supervised_event_training':False}
(root/'first_temporal_annotations.json').write_text(json.dumps(review,indent=2))
print('Recorded 3 non-cheese/negative intervals; 3 placement intervals pending precise hand and block review.')
