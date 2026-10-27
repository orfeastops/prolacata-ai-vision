"""Apply the user's explicit C01 boundary clarification, preserving the first review."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'outputs/facility_dataset/temporal_pipeline/sequence_annotation_v4'

def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def main():
    folder = BASE / 'expert_feedback'
    path = folder / 'C01_expert_review_EN.json'
    report = json.loads(path.read_text(encoding='utf-8'))
    prior = folder / 'C01_expert_review_before_boundary_EN.json'
    if not prior.exists():
        prior.write_bytes(path.read_bytes())
    feedback = {
        'origin': 'Explicit user chat reply on 2026-10-27 after reviewing boundary_context.webm',
        'original_text': 'στο 28.20 ξεκιναει την μεταφορα, στο 30 φτ;ανει πανω απο την δεξαμενη και ξεκιναει να τα αφηνει, αφηνει το πρωτο στο 30.74 και το δευτερο στο 33.30',
        'english_translation': 'Transfer begins at 28.20. At 30.00 the carrier reaches above the tank and begins releasing. The first block is released at 30.74 and the second at 33.30.',
        'time_basis': 'Seconds relative to original C01, as burned into boundary_context.webm',
        'event_id': 'C01_U04', 'position': 'left', 'quantity': 2,
        'transfer_start_time_s': 28.20, 'above_tank_time_s': 30.00,
        'release_events': [{'time_s': 30.74, 'quantity': 1}, {'time_s': 33.30, 'quantity': 1}],
        'original_clip_last_frame_time_s': 29.96,
        'deposited_blocks_within_original_clip_for_this_transfer': 0,
        'deposited_blocks_in_extended_context_for_this_transfer': 2,
        'timing_basis': 'Expert approximate video timing; not verified exact source frame',
    }
    save(folder / 'C01_boundary_chat_confirmation_20261027.json', feedback)
    event = next(e for e in report['events'] if e['event_id'] == 'C01_U04')
    assert event['quantity'] == 2 and event['position'] == 'left'
    event.update(lift_time_s=28.20, release_time_s=33.30, carry_duration_s=5.10,
        release_events=feedback['release_events'], nearest_lift_frame=None,
        nearest_lift_time_s=None, nearest_release_frame=None, nearest_release_time_s=None,
        complete_release_boundary_uncertain=False, release_is_outside_original_clip=True,
        original_clip_deposited_quantity=0, extended_context_deposited_quantity=2,
        timing_superseded_by='C01_boundary_chat_confirmation_20261027.json',
        english_note=feedback['english_translation'])
    report['summary'].update(boundary_uncertain_transfer_rows=0, boundary_uncertain_quantity=0,
        context_resolved_transfer_rows=1, blocks_released_after_original_clip=2,
        annotated_blocks_released_within_original_clip=18)
    report['requires_context_check'] = ['No exhaustive negative labels or independent whole-clip total are inferred from gaps between entries.']
    report['boundary_feedback_file'] = 'C01_boundary_chat_confirmation_20261027.json'
    save(path, report)
    handoff = ROOT / 'work/project_handoff'
    save(handoff / 'EXPERT_FEEDBACK_C01.json', report)
    state = json.loads((handoff / 'CURRENT_STATE.json').read_text(encoding='utf-8'))
    state['C01_feedback_summary'] = report['summary']
    state['C01_boundary_resolved'] = True
    state['next_task'] = 'Collect C02-C06 feedback; link expert transfers to visible object/group annotations before new training. C01 final two releases are at 30.74 and 33.30, outside its original clip.'
    save(handoff / 'CURRENT_STATE.json', state)
    print(json.dumps(report['summary']))

if __name__ == '__main__':
    main()
