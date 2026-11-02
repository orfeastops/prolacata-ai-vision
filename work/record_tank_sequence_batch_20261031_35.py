"""Preserve visually inspected 6Oct evidence without bridging missing camera15 routes."""
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read, save, merge, evidence

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'outputs/tank_transfer_training_v1'
OUT = BASE / 'dataset_v1'
RUN = 'sequence_review_20261031_35'


def main():
    state = read(OUT / 'continuation_state.json')
    if RUN in state.get('completed_curation_runs', []):
        print('Already recorded', RUN)
        return
    stamp = dt.datetime.now(dt.timezone.utc).isoformat()
    windows = {
        'broad': ('morning_route_0904_cam11', 76),
        'early': ('morning_route_0910_cam15', 23),
        'staging': ('morning_staging_0915_cam15', 21),
        'storage': ('morning_storage_0920_cam15', 15),
        'departure': ('morning_departure_0915_cam11', 38),
    }
    paths = {k: OUT / 'sequence_review/20261006' / w / 'frames.json' for k, (w, _) in windows.items()}
    metas = {k: read(p) for k, p in paths.items()}
    for k, m in metas.items():
        assert m['source']['date'] == '20261006' and m['source']['split'] == 'train'
        assert len(m['samples']) == windows[k][1]

    # These clocks were read from the image pixels, not derived from PTS.
    clocks = {
        'broad': ['09:04:46','09:05:12','09:05:27','09:05:42','09:05:57','09:06:12','09:06:27','09:06:43','09:06:58','09:07:13','09:07:27','09:07:43','09:07:57','09:08:12','09:08:27','09:08:42','09:08:58','09:09:13','09:09:28','09:09:43','09:09:58','09:10:13','09:10:28','09:10:43','09:10:58','09:11:13','09:11:28','09:11:43','09:11:58','09:12:13','09:12:28','09:12:43','09:12:58','09:13:13','09:13:28','09:13:43','09:13:58','09:14:12','09:14:27','09:14:42','09:14:57','09:15:12','09:15:27','09:15:42','09:15:57','09:16:12','09:16:27','09:16:42','09:16:57','09:17:12','09:17:27','09:17:42','09:17:57','09:18:12','09:18:27','09:18:42','09:18:57','09:19:12','09:19:27','09:19:42','09:19:57','09:20:12','09:20:27','09:20:42','09:20:57','09:21:12','09:21:27','09:21:42','09:21:57','09:22:12','09:22:27','09:22:42','09:22:57','09:23:12','09:23:27','09:23:42'],
        'early': ['09:10:12','09:10:31','09:10:34','09:10:37','09:10:40','09:10:43','09:10:46','09:10:49','09:10:52','09:10:55','09:10:58','09:11:01','09:11:04','09:11:07','09:11:10','09:11:13','09:11:16','09:11:19','09:11:22','09:11:25','09:11:28','09:11:31','09:11:34'],
        'staging': ['09:15:35','09:15:44','09:15:46','09:15:46','09:15:47','09:15:48','09:15:50','09:15:51','09:15:52','09:15:53','09:15:54','09:15:55','09:15:56','09:15:57','09:15:58','09:15:59','09:16:00','09:16:01','09:16:02','09:16:03','09:16:04'],
        'storage': ['09:20:24','09:20:38','09:20:39','09:20:40','09:20:41','09:20:42','09:20:43','09:20:44','09:20:45','09:20:46','09:20:47','09:20:48','09:20:49','09:20:50','09:20:51'],
        'departure': ['09:14:56','09:14:57','09:14:58','09:14:59','09:15:00','09:15:01','09:15:02','09:15:03','09:15:04','09:15:05','09:15:06','09:15:07','09:15:08','09:15:09','09:15:10','09:15:11','09:15:12','09:15:13','09:15:14','09:15:15','09:15:16','09:15:17','09:15:18','09:15:19','09:15:20','09:15:21','09:15:22','09:15:23','09:15:24','09:15:25','09:15:26','09:15:27','09:15:28','09:15:29','09:15:30','09:15:31','09:15:32','09:15:33'],
    }
    notes = {
        'broad': 'All76 chronological samples inspected. Station blue-lined gray body receives cheese from04:46 through14:57, departs15:12. Initial contents unknown. Separate beige covered body appears on scale05:27-42, remains08:42 then clear08:58; its origin is not in this window. Empty replacement at15:27/42 is a different tank, receives cheese by16:12 and through23:42. Fixed scrap tank at right remains distinct. Later blue-covered gray body on scale16:27-19:27 moves off19:42, clear19:57. Its entry/staging trajectory is hidden, so it is not asserted to be the fresh station load. Empty jack at21:27 is screening only. Native16:27 inspected.',
        'early': 'All23 chronological samples inspected. Initial10:12 then10:31. Fixed tank rows remain; no tank passage visible in the sampled doorway region. Native11:10 and11:22 also inspected: powered pallet truck moves without tank at foreground left, partly outside cropped sheets. This scoped observation is not a zero label for all room activity. No fresh-production identity established.',
        'staging': 'All21 chronological samples inspected. Initial15:35 then15:44 onward; stage begins after observed11 doorway crossing15:10-15. Operator handles staged body/hose near back-right doorway, mostly hidden behind fixed empty tanks, another person walks away44-48. Ends16:04 before platform visit visible from11 at16:27. Neither entry nor continuous staged-to-scale path established. Do not identify a new production entry from timing or color alone.',
        'storage': 'All15 chronological samples inspected. Initial20:24 then20:38. Gray covered body already moving by back row38-42, turns43-45 and approaches row46. Operator bends46-49; body/operator move again50-51. Native20:40 inspected. No empty-fork withdrawal or final parking completion observed. Earlier11 scale departure19:42 is separated by an unobserved route. Retain storage/repositioning candidate without same-load link, full-cycle target or already-stored-negative label.',
        'departure': 'All38 one-second samples inspected, displayed clocks14:56-15:33. White cheese surface visible14:56-59, workers position white panels15:00-02. Body pulled03, turns05-09, reaches doorway10, crosses11-14 and is absent15. Native15:05 and15:10 inspected. Distinct empty blue-lined replacement comes from left18, moves18-30 and is at station31-33; native15:27 shows empty lined bottom. Later cheese additions are outside this negative label. Both physical tanks are kept separate from fixed scrap tank and waiting stock.',
    }
    for k, m in metas.items():
        assert len(clocks[k]) == len(m['samples'])
        merge(OUT / 'screening_source_reviews.json', [dict(
            review_id='20261006/' + windows[k][0], reviewed_at=stamp, reviewer='assistant_visual_review',
            date='20261006', camera=m['source']['camera'], split='train',
            source_member=m['source']['member'], source_sha256=m['source_sha256'], frames_manifest=str(paths[k].relative_to(ROOT)),
            sampled_frames_visually_reviewed=len(m['samples']), reviewed_sheets=m['sheets'],
            review_scope='All chronological sample sheets inspected, selected native frames inspected, object crops separately overlay-reviewed. Not exhaustive native-frame viewing.',
            observation=notes[k], accepted_complete_cycle=False,
            clock_warning='Only transcribed pixel clocks. Initial jumps, filenames and PTS are not synchronization evidence.',
            visible_clock_anchors=[dict(sample_index=i, source_pts_seconds=m['samples'][i]['source_pts_seconds'],
                relative_pts_seconds=m['samples'][i]['relative_pts_seconds'], visible_camera_clock=t,
                clock_read_uncertainty_seconds=1, image=m['samples'][i]['image'], usable_for_clock_alignment=False)
                for i, t in enumerate(clocks[k])])], 'review_id')

    def ev(k, a, b):
        return evidence(metas[k], a, b, paths[k])

    save(OUT / 'review_history/sequence_labels_before_20261031_35.json', read(OUT / 'reviewed_sequence_labels.json'))
    shared = dict(date='20261006', split='train', reviewer='assistant_visual_review', reviewed_at=stamp,
        dataset_release_accepted=False, cycle_id=None, camera_clock_offset_seconds=None)
    partial = dict(shared, sequence_id='20261006_blue_station_departure0915_partial',
        review_status='reviewed_partial_sequence', production_entry_count_target=None,
        camera_track_id={'11': 'blue_station_load0915', '15': None},
        stages=[
            dict(stage='filling_observed', camera=11, visible_camera_clock_interval=['09:04:46','09:14:57'],
                initial_contents_unknown=True, evidence=[ev('broad',0,40)]),
            dict(stage='loaded_departure_11', camera=11, visible_camera_clock_interval=['09:15:03','09:15:15'],
                evidence=[ev('departure',7,19)]),
            dict(stage='entry_15', camera=11, visible_camera_clock_interval=['09:15:10','09:15:15'],
                room15_clock_interval=None, clock_basis='Physical passage seen from11 only; room15 clock is not calibrated.',
                evidence=[ev('departure',14,19)])],
        reviewed_followup_observations=[
            dict(stage='staging_observation', camera=15, visible_camera_clock_interval=['09:15:35','09:16:04'],
                same_load_identity_confirmed=False, observation='Partly hidden staged tank, entry and scale approach missing.',
                evidence=[ev('staging',0,20)]),
            dict(stage='scale_visit', camera=11, placement_interval=['09:16:12','09:16:27'],
                visible_camera_clock_interval=['09:16:27','09:19:27'], departure_interval=['09:19:27','09:19:57'],
                same_load_identity_confirmed=False, numeric_weight_kg=None,
                observation='Gray covered body moves off platform19:42; same-load origin unverified.', evidence=[ev('broad',45,60)]),
            dict(stage='storage_repositioning_candidate', camera=15, visible_camera_clock_interval=['09:20:24','09:20:51'],
                same_load_identity_confirmed=False, storage_completion_confirmed=False,
                observation='Gray body near storage row; no final park/empty-fork withdrawal seen. Not a completed storage label.',
                evidence=[ev('storage',0,14)])],
        missing_stages=['calibrated_room15_entry_timestamp','verified_entry_to_scale_identity',
            'verified_scale_to_storage_identity','confirmed_storage_completion'],
        limitations=['Room15 source ends09:11:35 then next starts09:15:36, after doorway crossing. Initial usable staged motion15:44.',
            'Room15 next clips are09:18:11-09:18:40,09:20:24-09:20:51 and09:28:28-09:28:45; none bridge19:42 scale departure.',
            'Unlinked same-color tanks are not extra production counts. No inferred weight or complete-cycle target.'])
    negative = dict(shared, sequence_id='20261006_empty_blue_station_replacement0915',
        review_status='accepted_negative_sequence', production_entry_count_target=0, camera=11,
        negative_class='empty_tank_internal_reposition', tracked_tank_count=1, direction='room11_waiting_area_to_station',
        visible_camera_clock_interval=['09:15:18','09:15:33'],
        observation='Separate empty blue-lined body moved from waiting area to station; lined bottom visible in native15:27.',
        label_scope='Only this empty replacement. Excludes prior filled departure, stationary scrap tank and later cheese additions.',
        evidence=[ev('departure',22,37)])
    merge(OUT / 'reviewed_sequence_labels.json', [partial,negative], 'sequence_id')
    qp = OUT / 'sequence_followup_queue.json'
    save(OUT / 'review_history/followup_queue_before_20261031_35.json', read(qp))
    merge(qp, [dict(candidate_id='20261006_blue_morning0915', date='20261006', split='train', reviewed_at=stamp,
        status='resolved_as_partial_missing_route', resolved_sequence_id=partial['sequence_id'], cycle_id=None,
        production_entry_count_target=None, observation='Fresh station filling and exit15:10-15 verified, subsequent staging, scale and storage candidate unlinked.',
        next_action='Do not resample absent09:15 entry or09:19:42 scale-to-storage route without new media. Storage completion also unseen.',
        evidence=[ev('departure',14,19),ev('broad',46,60),ev('storage',0,14)]),
        dict(candidate_id='20261006_second_blue_after0915', date='20261006', split='train', reviewed_at=stamp,
            status='needs_future_departure_context', cycle_id=None, production_entry_count_target=None,
            observation='Distinct replacement filled by09:16:12 and still receiving cheese through09:23:42.',
            next_action='Check peer coverage before extraction. Next11 metadata092349-092437.15 has092024-092051 then092828-092845; neither implies continuous route coverage.',
            evidence=[ev('broad',45,75)])], 'candidate_id')

    registry = read(OUT / 'object_review_decisions.json')
    save(OUT / 'review_history/object_decisions_before_20261031_35.json', registry)
    decisions = {r['id']: r for r in registry['reviews']}
    drafts = {r['id']: r for r in read(BASE / 'detector_v1/visual_annotation_draft.json')['records']}
    objnotes = {
        '239': 'Station load during departure; entire physical body and feet visible.',
        '240': 'Physical tank at doorway threshold before passage; rim partly overlapped by door equipment.',
        '241': 'Distinct empty local replacement body; hands overlap back rim.',
        '242': 'Scale body seen through doorway; left and upper parts occluded by door frame. Load and cross-camera identity are not inferred.',
        '243': 'Separate fixed scrap tank; conveyor partly occludes front body. Physical tank box only.',
    }
    for ident, note in objnotes.items():
        assert ident not in decisions
        r = drafts[ident]
        decisions[ident] = dict(id=ident, image_sha256=r['sha256'],
            boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review', review_date='2026-10-31', decision='accepted_for_roi_tank_detection',
            load_state_reviewed=False, sequence_reviewed=False,
            instance_attributes=[dict(box_index=0,truncated=False,occluded=ident!='239',load_state='unknown_not_annotated')],
            evidence=[r['source_frame'],r['frames_manifest'],'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_30.jpg'],
            note=note+' Native context and separate rendered overlay both inspected. Dataset release remains pending.')
    registry['reviews'] = list(decisions.values())
    registry.setdefault('corrections', []).append('Batch35: five6Oct ROI images/five boxes separately overlay-reviewed. Existing approvals preserved. No inferred load attributes or training release.')
    save(OUT / 'object_review_decisions.json', registry)
    inv = read(BASE / 'archive_inventory.json')
    inspected = {m['source']['member']:m['source_sha256'] for m in metas.values()}
    for r in inv['records']:
        if r['member'] in inspected:
            r.update(pixel_inspected=True,sha256=inspected[r['member']])
    assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test')
    save(BASE / 'archive_inventory.json', inv)
    reviews = read(OUT / 'screening_source_reviews.json')
    total = sum(r['sampled_frames_visually_reviewed'] for r in reviews)
    added = sum(len(m['samples']) for m in metas.values())
    state['last_completed'] += [
        f'Batch35 reviewed {added} sample presentations in five6Oct windows; {total} total across {len({r["source_sha256"] for r in reviews})} sources and {len(reviews)} windows. All extraction finished; test pixels untouched.',
        '6Oct09:15:10-15 fresh departure added as partial.15 staging,11 scale16:27-19:27 and15 storage candidate20:24-51 remain unlinked; storage completion unobserved. Five complete cycles unchanged;32 partials.',
        'Empty blue replacement09:15:18-33 added as scoped negative.78 negatives total. Prior09:05 beige scale visit and11min empty jack remain screening only.',
        'Five ROI images/five boxes approved:244 candidates,186 approved,247 boxes,58 exclusions,zero drafts. No training release.',
    ]
    state['priority_next'] = [
        'Batch35 complete. Prioritise fresh complete routes on training days other than13Oct and17Oct validation. Easy negatives already78; do not repeat known missing routes.',
        '6Oct09:15 partial retained:11 doorway15:10-15,15 first staged clip15:35/44-16:04,11 scale16:27-19:27 off19:42 clear19:57,15 storage candidate20:24/38-51 without final park. Missing identity trajectory; do not resample absent clips.',
        '6Oct secondblue after09:15: filled16:12-23:42. Next11 metadata092349-092437;15 next092828-092845 after092024-092051. Check coverage before new extraction.',
    ] + [p for p in state['priority_next'] if not p.startswith('Batch34')]
    state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    state['scripts'] += [s for s in ['work/append_tank_roi_batch_20261031_35.py','work/record_tank_sequence_batch_20261031_35.py'] if s not in state['scripts']]
    save(OUT / 'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_samples=added,total_presentations=total,
        additional_complete_cycles=0,additional_negative_sequences=1,additional_partial_sequences=1,training_started=False)))


if __name__ == '__main__':
    main()
