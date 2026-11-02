"""Record inspected13Oct empty returns and link earlier filling to an existing cycle."""
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read, save, merge, evidence

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'outputs/tank_transfer_training_v1'
OUT = BASE / 'dataset_v1'
RUN = 'sequence_review_20261031_36'


def main():
    state = read(OUT / 'continuation_state.json')
    if RUN in state.get('completed_curation_runs', []):
        print('Already recorded', RUN)
        return
    stamp = dt.datetime.now(dt.timezone.utc).isoformat()
    windows = {
        'route': ('morning_route_1021_cam15', 46),
        'origin': ('morning_origin_1025_cam11', 11),
        'restart': ('morning_restart_1037_cam11', 19),
        'gray15': ('empty_gray_return_1026_cam15', 18),
        'beige15': ('empty_beige_return_1028_cam15', 18),
        'gray11': ('empty_gray_return_1026_cam11', 15),
        'beige11': ('empty_beige_return_1028_cam11', 16),
        'bridge': ('morning_filling_bridge_1041_cam11', 30),
        'tail': ('morning_filling_join_tail1046_cam11', 14),
        'head': ('morning_filling_join_head1046_cam11', 7),
    }
    paths = {k: OUT / 'sequence_review/20261013' / w / 'frames.json' for k, (w, _) in windows.items()}
    metas = {k: read(p) for k, p in paths.items()}
    for k, m in metas.items():
        assert m['source']['date'] == '20261013' and m['source']['split'] == 'train'
        assert len(m['samples']) == windows[k][1]
    # Manually transcribed visible camera clocks; never derived from PTS.
    clocks = {
        'route': ['10:21:38','10:21:53','10:22:03','10:22:13','10:22:23','10:22:33','10:22:43','10:22:53','10:23:03','10:23:13','10:23:23','10:23:33','10:23:43','10:23:53','10:24:03','10:24:13','10:24:23','10:24:33','10:24:43','10:24:53','10:25:03','10:25:13','10:25:23','10:25:33','10:25:43','10:25:53','10:26:04','10:26:13','10:26:24','10:26:33','10:26:44','10:26:54','10:27:04','10:27:14','10:27:24','10:27:34','10:27:44','10:27:54','10:28:04','10:28:14','10:28:24','10:28:34','10:28:44','10:28:54','10:29:04','10:29:14'],
        'origin': ['10:25:11','10:25:20','10:25:25','10:25:30','10:25:35','10:25:40','10:25:45','10:25:50','10:25:55','10:26:00','10:26:05'],
        'restart': ['10:37:58','10:38:20','10:38:30','10:38:46','10:38:56','10:39:05','10:39:16','10:39:25','10:39:36','10:39:45','10:39:56','10:40:06','10:40:16','10:40:26','10:40:36','10:40:45','10:40:56','10:41:05','10:41:15'],
        'gray15': ['10:26:28','10:26:30','10:26:32','10:26:34','10:26:36','10:26:38','10:26:40','10:26:42','10:26:44','10:26:46','10:26:48','10:26:51','10:26:53','10:26:54','10:26:56','10:26:59','10:27:00','10:27:02'],
        'beige15': ['10:27:57','10:27:59','10:28:01','10:28:03','10:28:05','10:28:07','10:28:09','10:28:11','10:28:13','10:28:15','10:28:17','10:28:19','10:28:21','10:28:23','10:28:25','10:28:27','10:28:29','10:28:32'],
        'gray11': ['10:26:42','10:26:50','10:26:52','10:26:54','10:26:56','10:26:58','10:27:00','10:27:02','10:27:04','10:27:06','10:27:08','10:27:10','10:27:12','10:27:14','10:27:16'],
        'beige11': ['10:27:53','10:28:14','10:28:17','10:28:20','10:28:24','10:28:27','10:28:29','10:28:32','10:28:35','10:28:38','10:28:41','10:28:44','10:28:47','10:28:51','10:28:54','10:28:57'],
        'bridge': ['10:41:00','10:41:27','10:41:37','10:41:47','10:41:57','10:42:07','10:42:17','10:42:27','10:42:37','10:42:47','10:42:57','10:43:07','10:43:17','10:43:27','10:43:37','10:43:47','10:43:57','10:44:07','10:44:17','10:44:27','10:44:37','10:44:47','10:44:57','10:45:07','10:45:17','10:45:27','10:45:37','10:45:47','10:45:57','10:46:07'],
        'tail': ['10:46:03','10:46:04','10:46:05','10:46:07','10:46:08','10:46:09','10:46:10','10:46:11','10:46:12','10:46:13','10:46:14','10:46:15','10:46:16','10:46:17'],
        'head': ['10:46:01','10:46:18','10:46:19','10:46:20','10:46:21','10:46:22','10:46:23'],
    }
    notes = {
        'route': 'All46 chronological samples inspected. People package small white cans; yellow powered truck takes a pallet of cans left21:38-22:13, not a tank. Fixed stored covered tanks at rear and empty tanks at left are distinct. Two empty gray tanks move left-to-door26:33-54; two empty beige tanks follow28:04-24. Both routes received dense paired-camera follow-up. No claim of zero production across the whole room or unsampled gaps.',
        'origin': 'All11 samples inspected. Filling-station tank absent, empty white trays on conveyor and fixed scrap tank at right. Door opens25:20 and person walks without a tank. Screening only; no full production cycle inferred from inactivity.',
        'restart': 'All19 samples inspected. Beige station tank stays in place; workers prepare conveyor and jack. At37:58 some small white rectangular items are visible at bottom-right: do not call this a certified empty starting load. Cheese/trays appear40:06, placements40:26 onward. Empty gray stock row remains left and fixed scrap tank right. Native initial/final images inspected. Retained as earlier context without extending the accepted cycle across the not-densely-reviewed41:15-27 source join.',
        'gray15': 'All18 samples inspected. Two separate empty gray lined bodies pushed together from left, turn26:40-46, cross doorway26:48-53 and clear54-56. Empty interiors visible. Native26:40 inspected. Both bodies and one passage episode kept distinct from fixed stock.',
        'beige15': 'All18 samples inspected. Two separate empty beige lined bodies move from left27:57-28:05, turn07-13, cross doorway15-19, clear21. Native28:07 inspected. Empty interiors distinguish these returns from covered stored loads.',
        'gray11': 'All15 samples inspected. Initial26:42 then26:50. Pair of gray empty lined bodies enters50-54, moves toward left wall56-27:04 and parks04. Operator returns to doorway06-10. Native26:54 inspected. Paired doorway order, colors, body arrangement, operator and direction support same empty-return episode; no numerical clock offset certified.',
        'beige11': 'All16 samples inspected. Initial27:53 then28:14. Pair of beige empty tanks enters17, turns20, parks beside gray stock24-27. Operator then draws front beige tank toward station38-44; second stays at waiting area. Native28:17 inspected. This subsequent same-body local movement is not another crossing or new production entry. No link across unobserved28:57-37:58 to the later filling load asserted.',
        'bridge': 'All30 chronological samples inspected. Initial41:00 then41:27; same beige station tank receives cheese and remains in the same location through46:07, without a sampled replacement. Left waiting row and right fixed scrap tank remain distinct. This continuous source contains the previously unlinked42:45-43:03 partial. Dense source-tail and next-source-head inspected to connect with the existing47min cycle. Earlier restart source join remains outside certified linked interval.',
        'tail': 'All14 one-second chronological samples inspected, visible clock46:03-17. Same beige station tank and cheese surface remain, with two workers beside it and a third waiting on jack handle; no tank movement. Last sample46:17 directly precedes next-source usable46:18. Not an extra production cycle.',
        'head': 'All7 samples inspected. Initial stale/out-of-order frame reads46:01, then usable46:18-23. Same station tank, cheese layer, worker and jack positions bridge prior-source46:17. Source clock jump preserved and rejected for timing. Prior camera11_counterpart sheet000 separately rechecked; these frames join its46:21 onward filling evidence. No scalar camera15 clock offset inferred.',
    }
    for k, m in metas.items():
        assert len(clocks[k]) == len(m['samples'])
        merge(OUT / 'screening_source_reviews.json', [dict(
            review_id='20261013/' + windows[k][0], reviewed_at=stamp, reviewer='assistant_visual_review',
            date='20261013', camera=m['source']['camera'], split='train',
            source_member=m['source']['member'], source_sha256=m['source_sha256'], frames_manifest=str(paths[k].relative_to(ROOT)),
            sampled_frames_visually_reviewed=len(m['samples']), reviewed_sheets=m['sheets'],
            review_scope='All chronological sample sheets inspected; selected native frames and separate object overlays inspected. Not exhaustive native-frame viewing.',
            observation=notes[k], accepted_complete_cycle=False,
            clock_warning='Transcribed pixel clocks only. Initial jumps, filenames and PTS are not clock synchronization.',
            visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],
                relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],visible_camera_clock=t,
                clock_read_uncertainty_seconds=1,image=m['samples'][i]['image'],usable_for_clock_alignment=False)
                for i,t in enumerate(clocks[k])])], 'review_id')

    def ev(k,a,b):
        return evidence(metas[k],a,b,paths[k])

    labels = read(OUT / 'reviewed_sequence_labels.json')
    save(OUT / 'review_history/sequence_labels_before_20261031_36.json', labels)
    by_id = {r['sequence_id']:r for r in labels}
    full = by_id['20261013_beige_filling_to_storage_candidate_01']
    old = by_id['20261013_cam11_filling_partial_104245']
    assert full['review_status']=='accepted_complete_cycle' and old['review_status']=='reviewed_partial_sequence'
    old_evidence = copy.deepcopy(old['evidence'])
    filling = next(s for s in full['stages'] if s['stage']=='filling_observed')
    filling['visible_camera_clock_interval'] = ['10:41:27','10:47:26']
    filling['clock_uncertainty_seconds'] = 10
    filling['evidence'] = [ev('bridge',1,29),ev('tail',0,13),ev('head',1,6)] + old_evidence + filling['evidence']
    filling['initial_contents_unknown'] = True
    filling['observation'] = 'Same station beige body receives cheese across the inspected41:27-47:26 interval. Ten-second broad samples plus one-second46min source join and existing exact departure review. No observed tank exchange. Earlier filling beginnings and total contents remain unknown.'
    filling['source_join_review'] = dict(preceding_visible_clock='10:46:17',next_noninitial_sample_clock='10:46:18',
        rejected_initial_clock='10:46:01',identity_evidence='Same stationary tank geometry, cheese layer, adjacent worker positions and waiting jack operator at the join.',
        limitation='Sampled visual continuity, not exhaustive native-frame review. Earlier37-41min source remains context, not certified zero-start filling.')
    full['reviewed_at'] = stamp
    full.setdefault('review_history',[]).append(dict(run=RUN,previous_labels='outputs/tank_transfer_training_v1/dataset_v1/review_history/sequence_labels_before_20261031_36.json',
        change='Linked prior42:45 partial and extended filling evidence to41:27. All later cycle stages and single-entry target preserved.'))
    # A linked context record has no independent count target or second cycle ID.
    old.update(review_status='reviewed_context_existing_cycle',reviewed_at=stamp,cycle_id=None,
        linked_cycle_id=full['cycle_id'],linked_sequence_id=full['sequence_id'],
        camera_track_id=full['camera_track_id']['11'],production_entry_count_target=None,
        partial_reason='Bounded filling context now linked through the inspected source and dense46min join; no independent cycle/count target.',
        observation='Earlier42:45-43:03 station filling belongs to existing20261013_beige_1047 cycle. Original evidence and prior unlinked annotation preserved in review history.',
        label_scope='Context only: count once using the linked complete-cycle record, never once per clip or source.',
        relation_to_other_sequences='Resolved by stationary same-body source continuity and46:17-to46:18 dense join; not by beige color or filename alone.',
        linkage_evidence=[ev('bridge',1,29),ev('tail',0,13),ev('head',1,6)])
    negative = dict(sequence_id='20261013_empty_bulk_returns1026_1028',date='20261013',split='train',
        reviewer='assistant_visual_review',reviewed_at=stamp,review_status='accepted_negative_sequence',
        dataset_release_accepted=False,cycle_id=None,production_entry_count_target=0,camera_clock_offset_seconds=None,
        negative_class='empty_crossing',tracked_object_count=4,trip_count=2,direction='room15_to_room11',
        observation='One bulk empty-return episode: gray pair followed by beige pair. Four physical empty lined tanks; two doorway trips. Both camera views inspected.',
        label_scope='Zero new production entries for these four empty returns and the same beige body then moved to station. Not a whole-room zero label, and not four separate negative sequences.',
        trips=[
            dict(tank_count=2,appearance='gray',room15_door_interval=['10:26:48','10:26:56'],room11_door_interval=['10:26:50','10:26:54'],
                room11_parking_observed_by='10:27:04',evidence=[ev('gray15',0,17),ev('gray11',1,14)]),
            dict(tank_count=2,appearance='beige',room15_door_interval=['10:28:15','10:28:21'],room11_door_interval=['10:28:17','10:28:24'],
                room11_parking_interval=['10:28:24','10:28:27'],same_body_local_reposition_interval=['10:28:38','10:28:44'],
                evidence=[ev('beige15',0,17),ev('beige11',1,15)])],
        correspondence_basis='Same ordered pair colors/body arrangement, visible empty interiors, operator and adjacent doorway direction; camera intervals retained separately, not a certified scalar offset.',
        evidence=[ev('gray15',0,17),ev('gray11',1,14),ev('beige15',0,17),ev('beige11',1,15)])
    merge(OUT / 'reviewed_sequence_labels.json',[full,old,negative],'sequence_id')
    qp = OUT / 'sequence_followup_queue.json'
    save(OUT / 'review_history/followup_queue_before_20261031_36.json',read(qp))
    merge(qp,[dict(candidate_id='20261013_prior_filling104245',date='20261013',split='train',reviewed_at=stamp,
        status='resolved_as_context_existing_cycle',resolved_sequence_id=old['sequence_id'],linked_cycle_id=full['cycle_id'],
        cycle_id=None,production_entry_count_target=None,
        observation='Previously isolated42:45-43:03 filling linked to existing47min cycle. No additional production count.',
        next_action='No further resampling of the resolved46min join required. Preserve earlier restart uncertainty and initial contents unknown.',
        evidence=[ev('bridge',1,29),ev('tail',0,13),ev('head',1,6)])],'candidate_id')

    registry = read(OUT / 'object_review_decisions.json')
    save(OUT / 'review_history/object_decisions_before_20261031_36.json',registry)
    decisions = {r['id']:r for r in registry['reviews']}
    drafts = {r['id']:r for r in read(BASE / 'detector_v1/visual_annotation_draft.json')['records']}
    objnotes = {
        '244': ('Two physical empty-return gray tanks at camera11 doorway. Rear body partly occluded by front body/operator.',[(False,True),(False,True)]),
        '245': ('Two physical beige return tanks at camera11 doorway. Rear body partly occluded by front body/operator.',[(False,True),(False,True)]),
        '246': ('Two gray return bodies in camera15. Front truncated at left; rear at upper edge. Operator/body overlap.',[(True,True),(True,True)]),
        '247': ('Two beige return bodies in camera15. Front truncated at left, both partly occluded by operator/other body.',[(True,True),(False,True)]),
        '248': ('Single station beige body at37:58. Right/bottom truncation and conveyor overlap. Small white bottom items remain ambiguous; no empty-load label.',[(True,True)]),
        '249': ('Single station beige body at41:15. Right/bottom truncation and worker/conveyor overlap. Object box only.',[(True,True)]),
    }
    for ident,(note,attrs) in objnotes.items():
        assert ident not in decisions
        r = drafts[ident]
        assert len(r['boxes_xyxy'])==len(attrs)
        decisions[ident] = dict(id=ident,image_sha256=r['sha256'],
            boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',
            load_state_reviewed=False,sequence_reviewed=False,
            instance_attributes=[dict(box_index=i,truncated=tr,occluded=oc,load_state='unknown_not_annotated') for i,(tr,oc) in enumerate(attrs)],
            evidence=[r['source_frame'],r['frames_manifest'],'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_31.jpg'],
            note=note+' Native context and separate rendered overlay inspected. Dataset release remains pending.')
    registry['reviews'] = list(decisions.values())
    registry.setdefault('corrections',[]).append('Batch36: six13Oct ROI images/ten boxes separately overlay-reviewed. Previous approvals preserved; no object load attributes inferred.')
    save(OUT / 'object_review_decisions.json',registry)
    inv = read(BASE / 'archive_inventory.json')
    inspected = {m['source']['member']:m['source_sha256'] for m in metas.values()}
    for r in inv['records']:
        if r['member'] in inspected:
            r.update(pixel_inspected=True,sha256=inspected[r['member']])
    assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test')
    save(BASE / 'archive_inventory.json',inv)
    reviews = read(OUT / 'screening_source_reviews.json')
    total = sum(r['sampled_frames_visually_reviewed'] for r in reviews)
    added = sum(len(m['samples']) for m in metas.values())
    state['last_completed'] += [
        f'Batch36 reviewed {added} sample presentations in ten13Oct windows; {total} total across {len({r["source_sha256"] for r in reviews})} sources and {len(reviews)} windows. No active extraction; test pixels untouched.',
        '13Oct42:45 partial linked to existing47min beige cycle through source-wide stationary filling and dense46:17-to46:18 join. Five full cycles unchanged;31 partials and one linked context record. Earliest linked filling41:27, no inferred zero starting contents.',
        '13Oct two empty-return pairs(4 tanks,2 trips) added as one scoped negative episode;79 negatives. Same beige tank local reposition is not an extra crossing. Earlier37min station context remains outside certified linkage.',
        'Six ROI images/ten boxes approved:250 candidates,192 approved,257 boxes,58 exclusions,zero drafts. No training release.',
    ]
    state['priority_next'] = [
        'Batch36 complete. Prioritise fresh complete routes on training days other than13Oct and17Oct validation. Easy negatives79; do not resample known recording gaps.',
        '13Oct earlier42:45 filling resolved as context of20261013_beige_1047;46min join reviewed. Filling certified from41:27 only, earlier37:58-41:15 remains context with ambiguous initial white items, not a zero-start load.',
    ] + [p for p in state['priority_next'] if not p.startswith('Batch35')]
    state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    state['scripts'] += [s for s in ['work/append_tank_roi_batch_20261031_36.py','work/record_tank_sequence_batch_20261031_36.py'] if s not in state['scripts']]
    save(OUT / 'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_samples=added,total_presentations=total,
        additional_complete_cycles=0,additional_negative_sequences=1,partials_resolved_to_existing_cycle_context=1,training_started=False)))


if __name__=='__main__':
    main()
