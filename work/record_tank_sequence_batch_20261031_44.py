"""Record reviewed 6 October 09:27 departure and separate negative tracks."""
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read, save, merge, evidence

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'outputs/tank_transfer_training_v1'
OUT = BASE / 'dataset_v1'
RUN = 'sequence_review_20261031_44'


def main():
    state = read(OUT/'continuation_state.json')
    if RUN in state.get('completed_curation_runs', []):
        print('Already recorded', RUN)
        return
    stamp = dt.datetime.now(dt.timezone.utc).isoformat()
    windows = {
        'wait': ('morning_departure0924_cam11', 18),
        'broad': ('morning_route0924_cam11', 37),
        'scale': ('morning_scale0928_cam15', 8),
        'store': ('morning_storage0932_cam15', 25),
        'after': ('morning_storage0933_cam15', 36),
        'dep': ('morning_departure0927_cam11', 36),
    }
    paths = {k: OUT/'sequence_review/20261006'/w/'frames.json' for k, (w, _) in windows.items()}
    metas = {k: read(p) for k, p in paths.items()}
    # All anchors below were read from the inspected sample pixels, not inferred
    # from nominal sampling, source names or source PTS.
    clocks = {
        'wait': ['09:23:49','09:24:04','09:24:06','09:24:08','09:24:10','09:24:12',
                 '09:24:14','09:24:16','09:24:18','09:24:20','09:24:22','09:24:24',
                 '09:24:26','09:24:28','09:24:30','09:24:32','09:24:34','09:24:36'],
        'broad': ['09:24:28','09:24:56','09:25:11','09:25:26','09:25:41','09:25:56',
                  '09:26:11','09:26:26','09:26:41','09:26:56','09:27:11','09:27:26',
                  '09:27:41','09:27:56','09:28:11','09:28:26','09:28:41','09:28:56',
                  '09:29:11','09:29:26','09:29:41','09:29:56','09:30:11','09:30:26',
                  '09:30:41','09:30:56','09:31:11','09:31:26','09:31:41','09:31:56',
                  '09:32:11','09:32:26','09:32:41','09:32:56','09:33:11','09:33:26','09:33:41'],
        'scale': ['09:28:27','09:28:31','09:28:33','09:28:35','09:28:37','09:28:39','09:28:41','09:28:43'],
        'store': ['09:32:17','09:32:21','09:32:23','09:32:25','09:32:27','09:32:29',
                  '09:32:31','09:32:33','09:32:35','09:32:37','09:32:39','09:32:41',
                  '09:32:43','09:32:45','09:32:47','09:32:49','09:32:51','09:32:53',
                  '09:32:55','09:32:57','09:32:59','09:33:01','09:33:03','09:33:05','09:33:07'],
        'after': ['09:33:06','09:33:13','09:33:15','09:33:17','09:33:19','09:33:21',
                  '09:33:23','09:33:25','09:33:27','09:33:29','09:33:31','09:33:33',
                  '09:33:35','09:33:37','09:33:39','09:33:41','09:33:43','09:33:45',
                  '09:33:47','09:33:49','09:33:51','09:33:53','09:33:55','09:33:57',
                  '09:33:59','09:34:01','09:34:03','09:34:05','09:34:07','09:34:09',
                  '09:34:11','09:34:13','09:34:15','09:34:17','09:34:19','09:34:21'],
        'dep': ['09:27:06','09:27:08','09:27:10','09:27:12','09:27:14','09:27:16',
                '09:27:18','09:27:20','09:27:22','09:27:24','09:27:26','09:27:28',
                '09:27:30','09:27:32','09:27:34','09:27:36','09:27:38','09:27:40',
                '09:27:42','09:27:44','09:27:46','09:27:48','09:27:50','09:27:52',
                '09:27:54','09:27:56','09:27:58','09:28:00','09:28:02','09:28:04',
                '09:28:06','09:28:08','09:28:10','09:28:12','09:28:14','09:28:16'],
    }
    notes = {
        'wait': 'All18 samples/three sheets inspected. Initial23:49 then24:04 leaves15-second jump. Filled station body stays in position. Operator leaves jack24:08, walks towards doorway14-16 and returns18-26 without a tank. No departure observed in these samples; this is not a whole-room zero label.',
        'broad': 'All37 samples/seven sheets inspected. Initial24:28 then24:56 jump retained. Fresh station filling continues through27:11, loaded departure27:26, separate empty replacement27:41 and subsequent filling through33:41. Independent beige covered body with blue fittings moves from door staging towards scale28:41-56, platform occupancy29:11-31:41, moves off31:56-32:11 and platform clear32:26. No origin match to27min departure from appearance alone.',
        'scale': 'All8 samples/two sheets inspected. Initial28:27 then28:31. Beige covered body already in room15 staging; operator pulls left slightly35 then pushes right37-43 onto platform. Direct entry not visible. Prior available15 file ends20:51; no matched room15 crossing for27min origin. Independent clock intervals retained. No weight read.',
        'store': 'All25 samples/five sheets and native32:33/55 inspected. Initial32:17 then21. Covered beige body already off platform in staging, moves left47-57, turns to rear row59-33:07. No direct scale-to-staging route in this source. Empty forklift approaches foreground row32:29-33, bare forks visible; stored tanks stay distinct. Final jack release not visible before clip end.',
        'after': 'All36 samples/six sheets and native33:15/43 inspected. Initial33:06 overlaps previous33:07; next usable33:13 leaves six-second sampled gap. Beige body now parked rear row and empty manual jack withdrawn13-15, moving across aisle through31. Separate visibly empty gray tank collected from empty row35-37, moved39-47, staged near doorway49-57, then crosses15-to11 at33:59-34:05. Native43 confirms one physical tank and visible empty lined bottom, not a two-tank stack. Parked beige tank stays separate. Exact prior release time and origin identity not inferred.',
        'dep': 'All36 samples/six sheets, native27:28/36, three candidate crops and separate label overlays inspected. Fresh cheese placements through27:20; cover22, jack pull24, filled light body across room26-30, door crossing32-36 and gone38. Distinct empty gray replacement moves30-38, empty bottom through40; new cheese placement begins42-44 and filling continues28:16. Candidate273 depicts this empty replacement at27:36, not the outgoing covered load. No room15 event clock or exact camera offset invented.',
    }
    for k, m in metas.items():
        w, n = windows[k]
        assert len(m['samples']) == len(clocks[k]) == n
        assert m['source']['date'] == '20261006' and m['source']['split'] == 'train'
        merge(OUT/'screening_source_reviews.json', [dict(
            review_id='20261006/'+w, reviewed_at=stamp, reviewer='assistant_visual_review',
            date='20261006', camera=m['source']['camera'], split='train',
            source_member=m['source']['member'], source_sha256=m['source_sha256'],
            frames_manifest=str(paths[k].relative_to(ROOT)), sampled_frames_visually_reviewed=n,
            reviewed_sheets=m['sheets'], observation=notes[k], accepted_complete_cycle=False,
            review_scope='All chronological sample presentations viewed; selected native contexts and separate object overlays. Not exhaustive native-frame review.',
            clock_warning='Pixel clocks retained independently; initial jumps and source gaps do not establish synchronization.',
            visible_clock_anchors=[dict(sample_index=i, source_pts_seconds=m['samples'][i]['source_pts_seconds'],
                relative_pts_seconds=m['samples'][i]['relative_pts_seconds'], visible_camera_clock=t,
                clock_read_uncertainty_seconds=1, image=m['samples'][i]['image'], usable_for_clock_alignment=False)
                for i, t in enumerate(clocks[k])])], 'review_id')
    for k, w in [('earlier','morning_route_0904_cam11'), ('empty','morning_departure_0915_cam11')]:
        paths[k] = OUT/'sequence_review/20261006'/w/'frames.json'
        metas[k] = read(paths[k])
        assert any(r['frames_manifest'] == str(paths[k].relative_to(ROOT)) for r in read(OUT/'screening_source_reviews.json'))
    def ev(k, a, b):
        return evidence(metas[k], a, b, paths[k])
    labels = read(OUT/'reviewed_sequence_labels.json')
    save(OUT/'review_history/sequence_labels_before_20261031_44.json', labels)
    shared = dict(date='20261006', split='train', reviewer='assistant_visual_review', reviewed_at=stamp,
                  dataset_release_accepted=False, cycle_id=None, camera_clock_offset_seconds=None)
    partial = dict(shared, sequence_id='20261006_light_departure0927_partial',
        review_status='reviewed_partial_sequence', production_entry_count_target=None,
        observed_loaded_departure_count=1, camera_track_id={'11':'fresh_light_body0927','15':None},
        stages=[
            dict(stage='filling_observed', camera=11, visible_camera_clock_interval=['09:16:12','09:27:20'],
                initially_empty_observed=True, initial_empty_evidence_sequence_id='20261006_empty_blue_station_replacement0915',
                observation='Empty replacement previously reviewed at15:18-33; fresh cheese added through27:20. Sampled file joins23:42-to49,49-to24:04 and24:36-to56 retained; no uninterrupted native-frame claim. Blue liner is not a unique identity marker.',
                evidence=[ev('empty',22,37),ev('earlier',45,75),ev('wait',0,17),ev('broad',1,10),ev('dep',0,7)]),
            dict(stage='loaded_departure_11', camera=11, visible_camera_clock_interval=['09:27:22','09:27:38'],
                doorway_interval=['09:27:32','09:27:38'], room15_clock_interval=None,
                observation='Covered freshly filled tank leaves station and crosses doorway; room15 counterpart entry is not recorded in the available sources.',
                evidence=[ev('dep',8,16)])],
        reviewed_followup_observations=[
            dict(stage='scale_approach', camera=15, visible_camera_clock_interval=['09:28:27','09:28:43'],
                same_load_identity_confirmed=False, numeric_weight_kg=None,
                observation='Independent beige covered tank already inside staging moves towards platform35-43; missing doorway entry prevents linking origin.', evidence=[ev('scale',0,7)]),
            dict(stage='scale_visit', camera=11, visible_camera_clock_interval=['09:28:41','09:31:41'],
                departure_interval=['09:31:41','09:32:26'], same_load_identity_confirmed=False, numeric_weight_kg=None,
                observation='Independent platform approach, dwell and later clearance seen through doorway. No origin identity asserted.', evidence=[ev('broad',16,31)]),
            dict(stage='storage_approach', camera=15, visible_camera_clock_interval=['09:32:47','09:33:07'],
                same_load_identity_confirmed=False, storage_completion_confirmed=False,
                observation='Independent covered body moves left and turns to rear row. Parked body and empty jack seen33:13 after six-second gap; exact release and prior origin/scale identity remain unverified.',
                evidence=[ev('store',14,24),ev('after',0,10)])],
        missing_stages=['matched_room15_entry','verified_origin_to_scale_identity','verified_scale_to_storage_identity','origin_linked_storage_completion'],
        limitations=['Room15 earlier available source ends09:20:51; next starts09:28:27/31 after27min camera11 departure. No matching entry pixels exist in the reviewed available interval.',
            'Scale-to-staging route is absent from15; 15-second room11 samples and similar appearance do not prove cross-camera identity.',
            'Storage source initial33:06 overlaps previous33:07; next33:13 leaves six-second release gap. No precise release timestamp, measured weight or complete-cycle target.',
            'Later27min replacement starts a separate fill; keep its precursor evidence separate from prior09:36 partial until source join checked.'])
    negatives = [
        dict(shared, sequence_id='20261006_empty_gray_replacement0927', review_status='accepted_negative_sequence', camera=11,
            production_entry_count_target=0, negative_class='empty_tank_internal_reposition', tracked_tank_count=1,
            direction='room11_waiting_area_to_filling_station', visible_camera_clock_interval=['09:27:30','09:27:40'],
            observation='One distinct empty lined gray tank moves to station; empty bottom visible. New cheese42-44 is outside negative interval.',
            label_scope='Only empty replacement before filling, not simultaneous outgoing covered tank or stationary scrap tank.', evidence=[ev('dep',12,17)]),
        dict(shared, sequence_id='20261006_empty_gray_return0934', review_status='accepted_negative_sequence', camera=15,
            production_entry_count_target=0, negative_class='empty_crossing', tracked_tank_count=1,
            direction='room15_to_room11', visible_camera_clock_interval=['09:33:35','09:34:05'],
            doorway_interval=['09:33:59','09:34:05'],
            observation='One visibly empty gray tank collected from left row, carried to door and returned to11. Native33:43 shows one lined empty body. Distinct from covered beige tank parked in rear row.',
            label_scope='Only tracked empty return, not parked inventory or later productive filling.', evidence=[ev('after',12,27)]),
        dict(shared, sequence_id='20261006_empty_manual_jack0933', review_status='accepted_negative_sequence', camera=15,
            production_entry_count_target=0, negative_class='pallet_jack_without_tank',
            visible_camera_clock_interval=['09:33:13','09:33:31'],
            observation='Already withdrawn empty manual jack moves through aisle; prior stored load identity remains unknown.',
            label_scope='Only unloaded manual jack. Ends before next empty-tank pickup.', evidence=[ev('after',1,10)]),
        dict(shared, sequence_id='20261006_empty_forklift0932', review_status='accepted_negative_sequence', camera=15,
            production_entry_count_target=0, negative_class='pallet_jack_without_tank', vehicle_type='forklift',
            visible_camera_clock_interval=['09:32:29','09:32:33'],
            observation='Forklift approaches foreground stored row with bare forks; native33 verifies no tank on forks.',
            label_scope='Only short unloaded forklift approach; stationary foreground tanks and simultaneous covered tank staging excluded.', evidence=[ev('store',5,7)])]
    merge(OUT/'reviewed_sequence_labels.json', [partial,*negatives], 'sequence_id')
    qp = OUT/'sequence_followup_queue.json'
    save(OUT/'review_history/followup_queue_before_20261031_44.json', read(qp))
    merge(qp, [dict(candidate_id='20261006_second_blue_after0915', date='20261006', split='train', reviewed_at=stamp,
        status='resolved_as_partial_departure0927_missing_entry_route', resolved_sequence_id=partial['sequence_id'],
        cycle_id=None, production_entry_count_target=None,
        observation='Fresh station filling and27min loaded departure reviewed. Independent later scale/storage observations cannot establish matching origin.',
        next_action='Do not repeat these six reviewed windows. Camera15 gap20:51-to28:27 prevents direct27min entry; revisit only with new coverage. Prioritise complete cycles on other paired training sources.',
        evidence=[ev('dep',8,16),ev('scale',0,7),ev('store',14,24),ev('after',0,10)])], 'candidate_id')
    registry = read(OUT/'object_review_decisions.json')
    save(OUT/'review_history/object_decisions_before_20261031_44.json', registry)
    decisions = {r['id']:r for r in registry['reviews']}
    drafts = {r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
    for ident, occluded, note in [
        ('272',False,'Covered outgoing filled body; content context remains in temporal annotation.'),
        ('273',True,'Distinct empty local replacement at27:36; small hand occlusion at rear rim.'),
        ('274',True,'One empty return tank at33:43; operator partly occludes left edge. No stacked second body.')]:
        assert ident not in decisions
        r = drafts[ident]
        assert r['split']=='train' and len(r['boxes_xyxy'])==1
        decisions[ident] = dict(id=ident, image_sha256=r['sha256'],
            boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review', review_date='2026-10-31', decision='accepted_for_roi_tank_detection',
            load_state_reviewed=False, sequence_reviewed=False,
            instance_attributes=[dict(box_index=0,truncated=False,occluded=occluded,load_state='unknown_not_annotated')],
            evidence=[r['source_frame'],r['frames_manifest'],'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_35.jpg'],
            note=note+' Native context, candidate crop and separate rendered overlay inspected. ROI detection only.')
    registry['reviews'] = list(decisions.values())
    registry.setdefault('corrections',[]).append('Batch44:272/273/274 accepted after separate overlay review.273 is the empty replacement, not the outgoing tank. Previous reviews preserved.')
    save(OUT/'object_review_decisions.json', registry)
    inv = read(BASE/'archive_inventory.json')
    inspected = {m['source']['member']:m['source_sha256'] for m in metas.values()}
    for r in inv['records']:
        if r['member'] in inspected:
            r.update(pixel_inspected=True, sha256=inspected[r['member']])
    assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test')
    save(BASE/'archive_inventory.json', inv)
    reviews = read(OUT/'screening_source_reviews.json')
    total = sum(r['sampled_frames_visually_reviewed'] for r in reviews)
    state['last_completed'] += [
        f'Batch44 inspected160 further training sample presentations in6 windows on6Oct;{total} total across{len({r["source_sha256"] for r in reviews})} sources/{len(reviews)} windows. Extractions completed;25/28Oct unseen.',
        '6Oct fresh09:27 loaded departure recorded as partial. Direct15 entry missing; later scale and storage remain unlinked.41 partials,5 complete cycles unchanged.',
        'Four scoped negatives added: empty local replacement, one empty15-to11 return, empty manual jack and unloaded forklift approach.96 negatives total; no whole-room zero labels.',
        'Three native ROI images accepted after separate overlays.275 candidates,216 approved images,281 boxes,59 exclusions,zero drafts. Dataset remains unreleased.',
    ]
    state['priority_next'] = [
        'Batch44 complete.6Oct09:27 departure is partial:15 missing20:51-to28:27 entry coverage. Independent scale28:35-43 and storage32:47-33:07/parked13 cannot resolve origin. Do not repeat six reviewed windows or assume same-color identity.',
        'Prioritise unreviewed paired13/15Oct sources with entry-to-storage coverage for additional complete cycles. Check metadata and existing review records first; negative sequences already exceed planning target while complete-cycle diversity remains insufficient.',
        '6Oct empty27:30-40 replacement followed by new filling42-44 through33:41 is reviewed precursor context. Prior09:36 partial begins33:52; do not silently merge or replace initial-content metadata without checking join.',
    ] + [p for p in state['priority_next'] if not p.startswith('Batch43') and not p.startswith('Prioritise next6Oct station load')]
    state.update(updated_at=stamp, active_extraction_processes=[], dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    state['scripts'] += ['work/append_tank_roi_batch_20261031_44.py','work/record_tank_sequence_batch_20261031_44.py']
    save(OUT/'continuation_state.json', state)
    print(json.dumps(dict(recorded=RUN,additional_samples=160,total_presentations=total,
        additional_complete_cycles=0,additional_negative_sequences=4,additional_partial_sequences=1,training_started=False)))


if __name__=='__main__':
    main()
