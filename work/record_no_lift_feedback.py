"""Preserve user correction and retract a false assistant transfer label."""
import json,pathlib
R=pathlib.Path(__file__).resolve().parents[1]/'outputs/facility_dataset/temporal_pipeline/sequence_annotation_v2'
p=R/'expert_feedback.json';feedback=json.loads(p.read_text(encoding='utf-8'))
base=dict(clip_id='B007',review_clip='first_questions/rearrangement.mp4',
    sequence_annotation_interval_s=[11,18],exact_contact_lift_release_times_verified=False,
    semantic_label_confirmed=True,confirmed_by='user',role='training_candidate',training_eligible=False,
    interval_basis='Entire seven-second review clip; exact sub-event timing still requires frame review')
left=dict(base,event_id='B007_user_left_two_blocks',actor_scope='filling_left_only',
    action='whole_block_deposit_then_unrelated_gestures',whole_feta_block_increment=2,
    description='User confirms two new blocks at beginning, then turns sideways and gestures with no further deposits. Possible conversation is not treated as established fact.',
    confirmed_draft_event_id='B007_L1')
right=dict(base,event_id='B007_user_right_no_lift',actor_scope='filling_right_only',
    action='hand_motion_without_lifting_cheese',whole_feta_block_increment=0,
    description='User confirms no blocks deposited by opposite worker; placement-like hand motion without lifting cheese.',
    supersedes_draft_event_id='B007_R1')
ids={left['event_id'],right['event_id']};feedback=[e for e in feedback if e['event_id'] not in ids]+[left,right]
p.write_text(json.dumps(feedback,ensure_ascii=False,indent=2),encoding='utf-8')
p=R/'B007/annotation.json';a=json.loads(p.read_text(encoding='utf-8'))
a['expert_confirmed_actions']=[e for e in feedback if e['clip_id']=='B007']
for e in a['event_drafts']:
    if e['event_id']=='B007_R1':e.update(review_status='retracted_by_user',expert_quantity=0,superseded_by=right['event_id'],exclude_from_positive_training=True)
    elif e['event_id']=='B007_L1':e.update(expert_quantity=2,quantity_confirmed_by=left['event_id'])
for e in a['nonplacement_drafts']:
    if e.get('action')=='adjust_existing_tank_contents' and e.get('worker_track')=='filling_left':
        e.update(semantic_status='superseded_by_user_unrelated_gestures',superseded_by=left['event_id'],expert_confirmed=False)
p.write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf-8')
p=R/'first_questions/rearrangement_question.json';q=json.loads(p.read_text())
q.update(status='answered',left_whole_blocks_added=2,right_whole_blocks_added=0,total_added_in_review_clip=2,
         action='Left deposits two then gestures; right moves hands without lifting cheese')
p.write_text(json.dumps(q,indent=2))
audit=dict(status='confirmed_label_error',incorrect_example='B007_R1',prior_label='whole_block_transfer',
    corrected_label='other_or_idle',corrected_whole_blocks=0,
    evidence_event_id=right['event_id'],reason='Assistant mistook placement-like motion for an actual lifted block.',
    affected=['Historical supervised action training includes B007_R1 as a positive',
              'B007-derived hand/object crop labels require fresh review'],
    historical_models_updated=False,historical_test_predictions_preserved=True,
    policy='Future dataset builders must apply expert feedback; historical outputs are not silently rewritten.')
(R/'label_correction_audit.json').write_text(json.dumps(audit,indent=2))
print('Recorded left +2, right 0; retracted false B007_R1 draft; historical predictions preserved.')
