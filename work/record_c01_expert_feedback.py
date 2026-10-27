"""Preserve the C01 form export and explicitly reviewed English normalization.

This is a one-off import for the ten entries submitted on 2026-10-27, not a
general parser that guesses quantities from arbitrary free text.
"""
import argparse,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/facility_dataset/temporal_pipeline/sequence_annotation_v4'
NOTES=[
 'Picks up three together and puts them into the tank.',
 'Picks up three together and puts them into the tank.',
 'Carries three and releases three.',
 'Releases two, but the video cuts off. Completion relative to the clip boundary needs clarification.',
 'Lifts one and puts one into the tank.',
 'Lifts two and puts them into the tank.',
 'Picks up two and places two.',
 'Picks up two and places two.',
 'Lifts two and drops them into the tank from higher up, without bending all the way inside.',
 'Adjusts the cheese already dropped inside; does not lift or add new cheese.'
]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('input',type=Path);args=parser.parse_args()
    raw=args.input.read_bytes();data=json.loads(raw)
    source=json.loads((BASE/'C01/annotation.json').read_text(encoding='utf-8'))
    assert len(data['events'])==10 and all(e['clip_id']=='C01' and e['source_sha256']==source['source_sha256'] for e in data['events'])
    assert [e['lift_time_s'] for e in data['events']]==[8.56,13.74,21.4,28.28,2.88,7.96,12.08,20.2,25.28,29.96]
    out=BASE/'expert_feedback';out.mkdir(exist_ok=True)
    rawname='C01_form_export_20261027.json';path=out/rawname
    if path.exists():assert path.read_bytes()==raw,'Keep distinct reviewer submissions separately'
    else:path.write_bytes(raw)
    times=source['native_relative_timestamps_s'];events=[]
    for i,(e,note) in enumerate(zip(data['events'],NOTES)):
        q=e['quantity'];basis='Reviewer quantity field'
        if i==8:
            assert q is None and 'σηκωνει 2' in e['notes'];q=2;basis='Reviewer explicitly says two in the note; quantity field was blank'
        if i==9:
            assert e['destination']=='no_deposit';q=0;basis='Reviewer explicitly reports no newly lifted or placed cheese'
        a=e['lift_time_s'];b=e['release_time_s'];assert 0<=a<=b<=times[-1]+.01
        ia=min(range(len(times)),key=lambda k:abs(times[k]-a));ib=min(range(len(times)),key=lambda k:abs(times[k]-b))
        assert abs(times[ia]-a)<=.125 and abs(times[ib]-b)<=.125
        event=dict(event_id=f'C01_U{i+1:02d}',source_sha256=e['source_sha256'],position=e['position'],
            quantity=q,quantity_basis=basis,expert_quantity_confirmed=True,destination=e['destination'],
            english_note=note,original_entry_index=i,original_submission_file=rawname,
            lift_time_s=a if i!=9 else None,release_time_s=b if i!=9 else None,
            carry_duration_s=round(b-a,3) if i!=9 else None,
            nearest_lift_frame=ia if i!=9 else None,nearest_release_frame=ib,
            nearest_lift_time_s=times[ia] if i!=9 else None,nearest_release_time_s=times[ib],
            reviewer_timing_is_exact_release_frame_verified=False,
            complete_release_boundary_uncertain=i==3,
            note_type='instantaneous_no_new_block_observation' if i==9 else 'reviewer_reported_transfer',
            actual_object_boxes_and_tracks_verified=False)
        events.append(event)
    report=dict(schema_version=4,clip_id='C01',review_date='2026-10-27',
        source_sha256=source['source_sha256'],raw_submission_sha256=hashlib.sha256(raw).hexdigest(),
        user_confirmed_submission_in_chat=True,events=events,
        summary=dict(reviewer_entries=10,unambiguous_completed_transfer_rows=8,
            blocks_in_those_rows=18,three_block_transfer_rows=3,
            boundary_uncertain_transfer_rows=1,boundary_uncertain_quantity=2,
            no_new_block_observations=1,whole_clip_total_confirmed=None),
        requires_context_check=['The final two-block left-side release is at the last frame and described as cut off.',
            'No exhaustive negative labels are inferred from gaps between entries.'],
        training_on_this_submission_started=False,exhaustive_coverage_confirmed=False,
        physical_object_annotations_complete=False,
        important_semantic_correction='A valid drop into the tank can occur from above without deep bending. Bending is not mandatory count evidence.')
    (out/'C01_expert_review_EN.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report['summary']))

if __name__=='__main__':main()
