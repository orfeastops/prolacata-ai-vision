"""Consolidate source-backed annotations and expose release gaps honestly."""
import collections, json, html, os, re,hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/tank_transfer_training_v1'
OUT=BASE/'dataset_v1'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def save(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False),encoding='utf8')

def main():
    OUT.mkdir(exist_ok=True)
    draft=read(BASE/'detector_v1/visual_annotation_draft.json')
    records=draft['records']
    decisions_path=OUT/'object_review_decisions.json'
    review_registry=read(decisions_path) if decisions_path.exists() else {'reviews':[]}
    decisions={r['id']:r for r in review_registry['reviews']}
    excluded_reviews={r['id']:r for r in review_registry.get('excluded_roi_reviews',[])}
    assert len({r['id'] for r in records})==len(records)
    assert not any(r['date'] in ['20261025','20261028'] for r in records)
    assert {r['date'] for r in records if r['split']=='train'}.isdisjoint({r['date'] for r in records if r['split']=='val'})
    assert {r['sha256'] for r in records if r['split']=='train'}.isdisjoint({r['sha256'] for r in records if r['split']=='val'})
    for r in records:
        assert (ROOT/r['image']).is_file()
        r['dataset_release_accepted']=False
        r['load_state']='unknown_not_annotated'
        r['instance_tracking_id']=None
        r['cycle_id']=None
        r['full_context_required_for_load_state']=True
        decision=decisions.get(r['id'])
        excluded=excluded_reviews.get(r['id'])
        if excluded and r['annotation_status']=='excluded_uncertain_instance_boundaries' and excluded['image_sha256']==r['sha256']:
            r['exclusion_review']=excluded
        if decision:
            box_sha=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest()
            if decision['image_sha256']==r['sha256'] and decision['boxes_sha256']==box_sha:
                r['annotation_status']='roi_boxes_reviewed_assistant'
                r['object_review']=decision
            else:r['annotation_status']='changed_since_object_review_requires_recheck'
    save(OUT/'image_annotations_draft.json',dict(records=records,training_ready=False,
          annotation_version='draft-1',test_pixels_used=0,
          limitation='Cropped doorway images cover only object detection. Whole filling, scale and storage views are still required for cycle supervision.'))
    events=read(BASE/'development_event_references.json')
    queue=OUT/'sequence_annotation_queue.json'
    previous={s['sequence_id']:s for s in read(queue)} if queue.exists() else {}
    sequences=[]
    for e in events:
        sid=f'{e["date"]}_{e["proposal_id"]}'
        sequences.append(previous.get(sid) or dict(sequence_id=sid,date=e['date'],split='train',reference=e,
            annotation_status='inherited_visual_reference_requires_sequence_review',training_ready=False,
            cycle_id=None,stage_labels=[],cross_camera_identity='unverified',clock_alignment='unverified',
            missing_stage_is_negative=False))
    save(OUT/'sequence_annotation_queue.json',sequences)
    spec=dict(version=1,objective='One eligible filling-to-storage production-load cycle, counted once at room15 entry.',
        image_annotation=dict(object_class='tank',attributes=['empty','cheese_visible','scrap_visible','covered_unknown','unknown'],
            policy='Label every identifiable instance in the declared image/ROI, including stationary and truncated tanks. Mark occlusion and truncation. Load attributes require visible evidence or reviewed temporal context. A white cover alone never proves cheese.'),
        sequence_annotation=dict(fields=['cycle_id','camera_track_id','source_member_or_path','source_sha256','source_pts',
            'visible_camera_clock','clock_uncertainty_seconds','stage','content_evidence','reviewer','review_status'],
            stages=['filling_observed','loaded_departure_11','entry_15','scale_visit','storage_placement'],
            negative_cases=['empty_crossing','same_load_reentry','already_stored_tank_relocation','people_without_tank','pallet_jack_without_tank','opening_inventory','scrap_transfer','empty_tank_internal_reposition'],
            unknown_cases=['missing_camera_11_origin','entry_occluded','recording_gap','unresolved_cross_camera_identity','unreadable_clock'],
            policy='Keep native sequence order and gaps. Frame labels cannot substitute for direction or a completed cycle. Do not turn an unobserved stage into a negative label.'),
        split_policy=read(BASE/'training_protocol.json')['split_policy'],
        initial_collection_targets=dict(note='Planning targets, not a guarantee of accuracy. Count distinct cycles, not correlated frames.',
            reviewed_image_frames=1000,distinct_complete_transfer_cycles=50,distinct_negative_sequences=50,
            complete_cycle_training_days=4,
            coverage=['both cameras','all observed tank colors','empty and loaded','occluded and clear','early and late production','same-load reentry','post-storage movement']),
        release_gates=[
            'Source provenance, original timestamps and partition recorded for every annotation.',
            'All included object annotations pass a separate rendered-overlay review; uncertain examples remain excluded or queued.',
            'Cross-camera cycle labels reviewed in chronological video context, with clock offsets calibrated or timestamp uncertainty retained.',
            'Complete cycles and partial observations are reported separately; scale visit is not evidence of measured kilograms.',
            'Negative sequences include empty returns and relocation of already stored loads, not just empty-floor pictures.',
            'Validate across a separate day and both cameras; frozen test days remain unopened until final evaluation.',
            'Duplicate checks, label geometry checks and coverage report pass before a training export is released.'
        ])
    save(OUT/'annotation_protocol.json',spec)
    statuses=dict(collections.Counter(r['annotation_status'] for r in records))
    completed_path=OUT/'sequence_review/extraction_complete.json'
    extraction=read(completed_path) if completed_path.exists() else {}
    labels_path=OUT/'reviewed_sequence_labels.json'
    sequence_labels=read(labels_path) if labels_path.exists() else []
    source_reviews_path=OUT/'screening_source_reviews.json'
    source_reviews=read(source_reviews_path) if source_reviews_path.exists() else []
    assert not any(s['date'] in ['20261025','20261028'] for s in source_reviews+sequence_labels)
    assert len({s['sequence_id'] for s in sequence_labels})==len(sequence_labels)
    for r in records:
        for x1,y1,x2,y2 in r.get('boxes_xyxy') or []:
            assert 0<=x1<x2<=r['width'] and 0<=y1<y2<=r['height'],r['id']
    quality=dict(status='dataset_curation_in_progress',training_started=False,training_ready=False,
        candidate_images=len(records),candidate_by_split=dict(collections.Counter(r['split'] for r in records)),
        candidate_by_date=dict(collections.Counter(r['date'] for r in records)),annotation_status_counts=statuses,
        draft_boxes_in_non_excluded_images=sum(len(r['boxes_xyxy'] or []) for r in records if r['annotation_status']!='excluded_uncertain_instance_boundaries'),
        accepted_images=sum(r['annotation_status']=='roi_boxes_reviewed_assistant' for r in records),
        accepted_images_scope='ROI object boxes only; full dataset release remains pending.',
        accepted_complete_cycles=sum(s.get('review_status')=='accepted_complete_cycle' for s in sequence_labels),
        candidate_complete_cycles_requiring_review=sum(s.get('review_status')=='candidate_complete_cycle_needs_boundary_and_clock_review' for s in sequence_labels),
        accepted_negative_sequences=sum(s.get('review_status')=='accepted_negative_sequence' for s in sequence_labels),
        reviewed_partial_sequences=sum(s.get('review_status')=='reviewed_partial_sequence' for s in sequence_labels),
        accepted_complete_cycle_training_days=sorted({s['date'] for s in sequence_labels if s.get('review_status')=='accepted_complete_cycle' and s['split']=='train'}),
        sequence_counts_by_split={split:dict(collections.Counter(s['review_status'] for s in sequence_labels if s['split']==split)) for split in ['train','val']},
        negative_class_counts=dict(collections.Counter(s['negative_class'] for s in sequence_labels if s.get('review_status')=='accepted_negative_sequence')),
        accepted_object_boxes=sum(len(r['boxes_xyxy']) for r in records if r['annotation_status']=='roi_boxes_reviewed_assistant'),
        negative_annotation_scope='Tracked action only when stated; do not apply zero to other simultaneous room activity.',
        inherited_event_references=len(sequences),sequence_screening_frames=extraction.get('sampled_frames',0),
        reviewed_temporal_sample_presentations=sum(s['sampled_frames_visually_reviewed'] for s in source_reviews),
        reviewed_temporal_sample_scope='Chronological sampled-image inspection, not exhaustive native-frame viewing or independent training-image count.',
        reviewed_source_video_count=len({s['source_sha256'] for s in source_reviews}),
        reviewed_source_windows=len(source_reviews),
        tests=dict(day_splits_disjoint=True,image_hash_splits_disjoint=True,all_image_paths_resolve=True,label_geometry_valid=True,
                   sequence_ids_unique=True,reviewed_sequence_test_pixels_used=0,test_pixels_used=0),
        next_work=['Review and refine object boxes with full-frame context.',
                   'Expand video sequences across training days; label loaded exits, empty returns and storage relocation.',
                   'Calibrate camera clocks on visible corresponding crossings before accepting matched cycle timestamps.',
                   'Add exact scale/storage evidence; retain partial sequences when coverage is missing.'])
    save(OUT/'quality_report.json',quality)
    # Explicit example of the temporal review needed: mixed relocation and new
    # transfer in the same minute, with overlapping exported source clips.
    case_path=OUT/'sequence_review_case_20261021_390.json'
    # A rebuild must never overwrite a subsequent native-sequence review.
    if not case_path.exists():save(case_path,dict(reference='20261021_390',split='train',
        status='needs_native_sequence_and_clock_alignment_review',
        observation='The sampled camera11 sequence includes an empty tank moved near the door and a different visibly loaded tank. Camera15 includes relocation of an already covered tank. These actions must not be collapsed into a single new-entry label using filename-plus-PTS ordering.',
        camera11_loaded_exit_reference_interval='13:41:22-13:41:36',
        camera15_new_entry_time=None,scale_visit=None,storage_placement=None,
        evidence=['outputs/tank_door_audit/event_review/20261021/390.jpg',
                  'outputs/tank_door_audit/camera15_matches/20261021/390_detail00.jpg',
                  'outputs/tank_door_audit/camera15_matches/20261021/390_detail01.jpg']))
    # Record what has actually been inspected, while preserving held-out pixels.
    inv=read(BASE/'archive_inventory.json');seen={r['source'] for r in records if '/' in r['source']}
    for r in inv['records']:
        if r['member'] in seen:r['pixel_inspected']=True
    assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test')
    save(BASE/'archive_inventory.json',inv)
    protocol=read(BASE/'training_protocol.json')
    protocol['status']='dataset_annotation_in_progress_training_not_started'
    protocol['next_step']='Build and quality-review the image and full-cycle dataset before releasing a training run.'
    protocol['active_dataset_workspace']=str(OUT.relative_to(ROOT))
    save(BASE/'training_protocol.json',protocol)
    verify=read(BASE/'preparation_verification.json')
    verify['status']='dataset_annotation_in_progress_training_not_started'
    verify['validation_candidate_images_inspected']=sum(r['split']=='val' for r in records)
    verify['test_pixels_inspected']=0
    verify['dataset_quality_report']=str((OUT/'quality_report.json').relative_to(ROOT))
    save(BASE/'preparation_verification.json',verify)
    from render_tank_dataset_review_v1 import render_review
    render_review(ROOT, OUT, quality, records, sequence_labels, source_reviews)
    p=BASE/'inventory_review.html';s=p.read_text(encoding='utf8')
    notice='<!-- dataset-status:start --><section><h2>Δημιουργία dataset σε εξέλιξη</h2><p>Η εκπαίδευση δεν έχει ξεκινήσει. Η πρώτη παρτίδα έχει 75 υποψήφιες εικόνες και ουρά ελέγχου ακολουθιών.</p><a href="dataset_v1/review.html">Άνοιγμα dataset και προόδου ελέγχου</a></section><!-- dataset-status:end -->'
    notice = notice.replace("75 ", str(quality["candidate_images"])+" ")
    if '<!-- dataset-status:start -->' in s:s=re.sub(r'<!-- dataset-status:start -->.*?<!-- dataset-status:end -->',lambda m:notice,s,flags=re.S)
    else:s=s.replace('</h1>','</h1>'+notice,1)
    p.write_text(s,encoding='utf8')
    print(json.dumps(quality,indent=2))
if __name__=='__main__':main()
