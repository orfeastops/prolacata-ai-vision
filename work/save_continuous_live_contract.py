import datetime
import json
from pathlib import Path

root = Path('outputs/facility_dataset')
contract_path = root/'temporal_pipeline/per_tank_reporting_contract.json'
contract = json.loads(contract_path.read_text())
contract['deployment_input'] = 'Continuous live camera11 and camera15 streams after acceptable independent evaluation; cameras are not yet connected.'
contract['processing_windows'] = 'Internal overlapping inference windows only; window boundaries and source-file changes never reset a tank, hand transfer, or cumulative count.'
contract['tank_lifecycle'] = 'Keep a persistent physical tank ID from confirmed arrival at the filling station, through actual placements, departure, camera15 weighing and storage. A new tank requires a physical tank change, never a timer or assumed capacity.'
contract['persistence'] = 'SQLite live_state.py preserves accepted releases, pending events, tank transitions and coverage across processing restarts. Stable physical-event identities must be supplied by the upstream tracker.'
contract['buffer_overlap_rule'] = 'The same physical release observed in overlapping inference windows contributes once.'
contract['interruption_rule'] = 'If a real acquisition gap occurs, preserve the count and mark coverage uncertain; never replace missing observations with a fixed tank total.'
contract['timestamp_rule'] = 'Use capture timestamps with timezone, preserving per-camera alignment; processing time is not the event time.'
contract['validation_status'] = 'Bookkeeping logic tested; live ingestion, automatic stable-event identities, block quantities and cross-camera identity are not yet validated.'
contract_path.write_text(json.dumps(contract,indent=2),encoding='utf-8')
status_path = root/'transfer_status.json'
status = json.loads(status_path.read_text())
status.update({'state':'Self-supervised pretraining and first supervised action pilot completed; pretrained video comparison prepared. Production counting still under development.',
 'supervised_training_started':True,'reviewed_action_pilot_complete':True,
 'reviewed_action_pilot_url':'https://www.kaggle.com/code/orfeastops/facility-reviewed-hand-action-training?scriptVersionId=361524639',
 'reviewed_action_pilot_runtime_s':462.8,'reviewed_action_pilot_examples':76,
 'reviewed_action_pilot_selected':'frozen_feature_baseline',
 'reviewed_action_pilot_validation_macro_f1':0.4296296296296296,
 'reviewed_action_pilot_test_macro_f1':0.4444444444444445,
 'reviewed_action_pilot_metric_scope':'Trimmed action clips only, not block counting accuracy.',
 'counter_logic_tests_passed':12,'live_persistence_tests_passed':11,
 'new_action_review_clips_dense_reviewed':10,'manual_complete_block_transfer_events':29,
 'manual_block_sum_for_selected_events':58,'future_input':'continuous live camera11 and camera15',
 'live_camera_connected':False,'production_counter_ready':False,
 'updated_at_local':datetime.datetime.now().astimezone().isoformat()})
status_path.write_text(json.dumps(status,indent=2),encoding='utf-8')
print('Saved continuous live requirement and observed pilot status.')
