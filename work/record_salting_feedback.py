"""Record user-confirmed action semantics without inventing frame-level timing."""
import json,pathlib
R=pathlib.Path(__file__).resolve().parents[1]/'outputs/facility_dataset/temporal_pipeline/sequence_annotation_v2'
feedback_path=R/'expert_feedback.json'
feedback=json.loads(feedback_path.read_text(encoding='utf-8')) if feedback_path.exists() else []
event=dict(event_id='B019_user_confirmed_salting',clip_id='B019',action='salt_pickup_and_sprinkle',
    actor_scope='filling_right_only',source='white_bucket_behind_worker',destination='cheese_layer_in_filling_tank',
    material='salt',whole_feta_block_increment=0,
    review_clip='first_questions/side_motion.mp4',user_question_interval_s=[2,4],
    sequence_annotation_interval_s=[15,17],interval_basis='Approximate interval identified in question, not exact action boundaries',
    exact_contact_lift_release_times_verified=False,semantic_label_confirmed=True,
    confirmed_by='user',user_statement_el='εκει παιρνει αλατι και το τιναζει πανω στην στρωση με τα τυρια',
    role='development_only',training_eligible=False,
    scope_note='Zero applies to this worker salting, not other concurrent worker actions or the whole clip.')
feedback=[e for e in feedback if e['event_id']!=event['event_id']]+[event]
feedback_path.write_text(json.dumps(feedback,ensure_ascii=False,indent=2),encoding='utf-8')
p=R/'B019/annotation.json';a=json.loads(p.read_text(encoding='utf-8'))
a['expert_confirmed_actions']=[e for e in feedback if e['clip_id']=='B019']
for u in a['unresolved_drafts']:
    if u.get('worker_track')=='filling_right' and u.get('window_s')==[15.125,16.875]:
        u.update(semantic_resolution_event_id=event['event_id'],semantic_status='resolved_as_salting',timing_status='still_requires_frame_review')
p.write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf-8')
p=R/'first_questions/pending_question.json';q=json.loads(p.read_text(encoding='utf-8'))
q.update(status='answered',event_type='salt_pickup_and_sprinkle',quantity=0,
         quantity_unit='whole_feta_blocks_added_by_this_action_only',answer_el=event['user_statement_el'],feedback_event_id=event['event_id'])
p.write_text(json.dumps(q,ensure_ascii=False,indent=2),encoding='utf-8')
p=R/'annotation_contract.json';c=json.loads(p.read_text(encoding='utf-8'))
if 'salt_pickup_and_sprinkle' not in c['negative_classes']:c['negative_classes'].append('salt_pickup_and_sprinkle')
c['salting_rule']='Salt taken from bucket and sprinkled over cheese adds zero whole blocks, even when hands enter the filling tank. Do not suppress simultaneous whole-block deposits by another hand.'
p.write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf-8')
assert a['expert_confirmed_actions'][0]['whole_feta_block_increment']==0
assert a['eligible_for_training'] is False and a['role']=='development_only'
print('Recorded user-confirmed salting; only this action has zero block increment. Model and test untouched.')
