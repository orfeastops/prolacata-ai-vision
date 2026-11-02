"""Persist visually reviewed 6 October relocation and incomplete fresh cycles."""
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read, save, merge, evidence

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'outputs/tank_transfer_training_v1'
OUT = BASE / 'dataset_v1'
RUN = 'sequence_review_20261031_25'


def main():
    state = read(OUT / 'continuation_state.json')
    if RUN in state.get('completed_curation_runs', []):
        print('Already recorded', RUN)
        return
    stamp = dt.datetime.now(dt.timezone.utc).isoformat()
    windows = {
        'relocation': ('blue_context_0956_cam15', 27),
        'storage': ('blue_context_1013_cam15', 25),
        'screen': ('production_screen_0956_cam11', 85),
        'origin': ('blue_departure_scale_1008_cam11', 87),
        'entry': ('arrival_context_1008_cam15', 21),
        'staging': ('blue_scale_1008_cam15', 6),
        'scale': ('blue_scale_1009_cam15', 11),
    }
    paths = {k: OUT / 'sequence_review/20261006' / w / 'frames.json' for k, (w, n) in windows.items()}
    metas = {k: read(p) for k, p in paths.items()}
    for k, m in metas.items():
        assert m['source']['date'] == '20261006' and m['source']['split'] == 'train'
        assert len(m['samples']) == windows[k][1]
    # Anchors below were read from the sampled image clocks, not derived from
    # filename times or PTS. Only explicitly inspected anchors are recorded.
    clocks = {
        'relocation': {0:'09:56:11',1:'09:56:20',3:'09:56:26',7:'09:56:38',8:'09:56:41',9:'09:56:44',10:'09:56:47',12:'09:56:53',17:'09:57:08',18:'09:57:11',19:'09:57:14',21:'09:57:20',22:'09:57:23',26:'09:57:35'},
        'storage': {0:'10:13:03',1:'10:13:25',3:'10:13:31',5:'10:13:37',6:'10:13:40',9:'10:13:49',10:'10:13:52',11:'10:13:55',12:'10:13:58',13:'10:14:01',14:'10:14:04',15:'10:14:07',16:'10:14:10',17:'10:14:13',18:'10:14:16',20:'10:14:22',21:'10:14:25',24:'10:14:34'},
        'screen': {0:'09:56:29',1:'09:56:52',11:'09:59:22',12:'09:59:37',13:'09:59:52',14:'10:00:07',18:'10:01:07',29:'10:03:52',30:'10:04:07',31:'10:04:22',47:'10:08:22',48:'10:08:37',52:'10:09:37',54:'10:10:07',65:'10:12:52',66:'10:13:07',70:'10:14:07',72:'10:14:37',73:'10:14:52',82:'10:17:07',83:'10:17:22',84:'10:17:37'},
        'origin': {0:'10:07:52',6:'10:08:16',7:'10:08:20',8:'10:08:24',9:'10:08:28',10:'10:08:32',11:'10:08:36',12:'10:08:40',18:'10:09:04',27:'10:09:40',28:'10:09:44',29:'10:09:48',73:'10:12:43',74:'10:12:47',75:'10:12:52',76:'10:12:55',77:'10:13:00',78:'10:13:03',79:'10:13:07',80:'10:13:11',82:'10:13:19',86:'10:13:36'},
        'entry': {0:'10:08:03',1:'10:08:16',5:'10:08:24',6:'10:08:26',7:'10:08:28',8:'10:08:30',9:'10:08:32',12:'10:08:38',20:'10:08:54'},
        'staging': {0:'10:08:40',1:'10:08:57',2:'10:08:59',3:'10:09:01',4:'10:09:03',5:'10:09:05'},
        'scale': {0:'10:09:17',1:'10:09:38',2:'10:09:40',3:'10:09:42',4:'10:09:44',5:'10:09:46',6:'10:09:48',8:'10:09:52',10:'10:09:56'},
    }
    notes = {
        'relocation': 'Two gray tanks with blue covers are already in the foreground storage group at 09:56:20-23. A forklift approaches at26-35, lifts one at38-41 and lowers it onto the second at44-47. Forks withdraw50-53; the pair remains stacked. The forklift turns, reengages and lifts the pair at09:57:11, then carries it left14-23. Initial source image56:11 is early. This is a tracked relocation of existing stored tanks, not a new doorway arrival. Covered contents and original production dates are unknown.',
        'storage': 'Three concurrent tracks must remain distinct. A gray covered tank is already at rear-door staging at first usable10:13:25, moves to rear storage31-58, remains parked14:01, and its manual jack withdraws04-10. Its fresh origin is unlinked. Separately a forklift selects two tanks already in the foreground row, lifts one13:52-55, stacks it58-14:01, reengages07-10 and carries the pair13-25; this is a stored-tank relocation. A third, visibly empty blue-lined tank is taken from the left waiting row13:37, moved40-55 and returned through the door14:01-07, gone10. Camera11 shows an empty tank inside at14:07. The source initial13:03 image is early and not a route bridge.',
        'screen': 'Blue-lined production tank receives cheese at09:56:52-59:22, is covered and departing at59:37. A different local empty replacement is filled from59:52 to10:08:22; the dense origin window resolves its departure. Subsequent replacement receives cheese from08:37 through17:07 and departs17:22-37. Previous load is on scale through room11 doorway01:07-03:52, pulled off04:07 and clear04:22. The08min load is near scale09:37, settled10:07, present12:52, platform clear13:07. Empty return already inside14:07, parked14:37, operator approaches station14:52. Fixed scrap tank is separate. This is coarse chronological screening, not exact threshold timing or continuous native-frame tracking.',
        'origin': 'Fresh station filling continues07:52-08:20. White cover set24, tank pulled clear28, at door32 and gone36. A separate empty local replacement is positioned32-40 and then filled. Through the doorway the earlier load approaches scale09:40-44, settles48 and remains to12:43. Jack engages47-52, tank pulled55, platform clear13:00; narrow right staging edge persists03, fully out of view07. Camera15 first usable later route13:25 does not bridge the25-second platform-to-route interval. No scalar camera clock offset asserted.',
        'entry': 'Initial08:03 image early. Operator and white top first emerge at doorway08:26; blue-lined body edge28 and crossing30 are occluded by the operator and fixed bins. Tank is inside/staging by32 and remains beside rear doorway through54. Keep entry interval26-32, not a fabricated exact second. Room11 corresponding load is at its doorway32 and gone36; clocks are not calibrated.',
        'staging': 'Initial08:40 image early; usable08:57-09:05 shows loaded tank still staged beside the doorway, partly behind people and fixed bins. Previous usable source ends08:54: a three-second sample join. Next usable scale source starts09:38: a33-second sampled staging gap, not continuous route evidence.',
        'scale': 'Initial09:17 image early; first usable09:38 shows tank moving from staging toward the right-hand platform. Movement40-46, settled48, forks withdrawn50-52 and attendant beside tank54-56. The room11 doorway view also shows transition40-48 and subsequent dwell. No numeric weight inferred; later storage origin remains unresolved.',
    }
    for k, m in metas.items():
        merge(OUT / 'screening_source_reviews.json', [dict(
            review_id='20261006/' + windows[k][0], reviewed_at=stamp,
            reviewer='assistant_visual_review', date='20261006', camera=m['source']['camera'], split='train',
            source_member=m['source']['member'], source_sha256=m['source_sha256'], frames_manifest=str(paths[k].relative_to(ROOT)),
            sampled_frames_visually_reviewed=len(m['samples']), reviewed_sheets=m['sheets'],
            review_scope='All chronological sampled sheets inspected; selected native frames and separate object overlays reviewed. Not exhaustive native-frame tracking.',
            observation=notes[k], accepted_complete_cycle=False,
            clock_warning='Initial early frames excluded from alignment; filename times and PTS do not establish camera synchronization.',
            visible_clock_anchors=[dict(sample_index=i, source_pts_seconds=m['samples'][i]['source_pts_seconds'],
                relative_pts_seconds=m['samples'][i]['relative_pts_seconds'], visible_camera_clock=t,
                clock_read_uncertainty_seconds=1, image=m['samples'][i]['image'],
                usable_for_clock_alignment=not(i == 0 and k != 'origin')) for i, t in clocks[k].items()]
        )], 'review_id')

    def ev(k, a, b):
        return evidence(metas[k], a, b, paths[k])

    labels = read(OUT / 'reviewed_sequence_labels.json')
    save(OUT / 'review_history/sequence_labels_before_20261031_25.json', labels)
    shared = dict(date='20261006', split='train', reviewer='assistant_visual_review', reviewed_at=stamp, dataset_release_accepted=False)
    partials = [dict(shared,
        sequence_id='20261006_fresh_blue_departure_partial_0959', review_status='reviewed_partial_sequence',
        cycle_id=None, production_entry_count_target=None, camera_track_id={'11':'blue_filling_0956_departure0959'},
        camera_clock_offset_seconds=None, cross_camera_identity='unresolved_missing_room15_entry',
        stages=[dict(stage='filling_observed', camera=11, visible_camera_clock_interval=['09:56:52','09:59:22'],
                content_evidence='Visible cheese placement into production tank, separate from fixed scrap tank.', evidence=[ev('screen',1,11)]),
            dict(stage='loaded_departure_11', camera=11, visible_camera_clock_interval=['09:59:22','09:59:52'],
                observation='Covered departing tank at59:37; local replacement already receiving cheese59:52. Coarse15-second samples, no exact crossing time.', evidence=[ev('screen',11,13)])],
        missing_stages=['linked_entry_15','linked_scale_visit','linked_storage_placement'],
        unlinked_followup=dict(observation='Later scale occupancy seen through room11 door01:07-03:52, pulled off04:07 and platform clear04:22. Direct room15 entry missing; do not bridge it with similar appearance.', evidence=[ev('screen',18,31)])),
        dict(shared, sequence_id='20261006_fresh_blue_departure_partial_1008', review_status='reviewed_partial_sequence',
        cycle_id=None, production_entry_count_target=None,
        camera_track_id={'11':'blue_filling_0959_departure1008','15':'candidate_blue_entry1008_scale1009'},
        camera_clock_offset_seconds=None, cross_camera_identity='consistent_departure_arrival_candidate_with_uncalibrated_clocks',
        stages=[dict(stage='filling_observed', camera=11, visible_camera_clock_interval=['09:59:52','10:08:20'],
                content_evidence='Local visibly empty replacement receives successive cheese layers; fixed scrap tank is separate.', evidence=[ev('screen',13,47),ev('origin',0,7)]),
            dict(stage='loaded_departure_11', camera=11, visible_camera_clock_interval=['10:08:24','10:08:36'],
                doorway_interval=['10:08:32','10:08:36'], clock_uncertainty_seconds=4,
                observation='Covered at24, pulled28, at doorway32 and gone36.', evidence=[ev('origin',8,11)]),
            dict(stage='entry_15', camera=15, visible_camera_clock_interval=['10:08:26','10:08:32'],
                clock_uncertainty_seconds=2, identity_status='candidate_cross_camera_match',
                observation='One blue-lined tank arrives behind operator; body and threshold partly occluded. Separate uncalibrated camera clocks retained.', evidence=[ev('entry',5,12)]),
            dict(stage='scale_visit', camera=15, visible_camera_clock_interval=['10:09:38','10:09:56'],
                numeric_weight_kg=None, observation='Staging-to-platform movement38-48, jack withdraws50-52. Room11 view retains later dwell to12:43. Prior09:05-38 staging gap remains explicit.',
                evidence=[ev('staging',1,5),ev('scale',1,10),ev('origin',27,79)])],
        missing_stages=['linked_storage_placement','continuous_staging_route'],
        unlinked_followup=dict(platform_clear_camera11='10:13:00', first_usable_later_gray_storage_route_camera15='10:13:25',
            nominal_cross_camera_interval_seconds=25, interval_is_clock_calibrated=False,
            storage_local_camera15_interval=['10:13:31','10:14:10'], storage_observed_but_origin_unlinked=True,
            evidence=[ev('origin',74,79),ev('storage',1,16)],
            observation='Gray tank already at rear staging in first usable13:25, then parks at rear row and jack withdraws. Do not infer same-load identity across missing route; simultaneous forklift pair belongs to existing foreground inventory.'),
        limitations=['White cover alone is not cheese evidence.', 'Camera clock offset unresolved.', 'Partial cycle has no production entry target.'])]
    negatives = []
    for k, ident, interval, end in [
        ('relocation','20261006_stored_gray_pair_relocation_0956',['09:56:20','09:57:23'],22),
        ('storage','20261006_stored_gray_pair_relocation_1013',['10:13:25','10:14:25'],21),
    ]:
        negatives.append(dict(shared, sequence_id=ident, review_status='accepted_negative_sequence',
            cycle_id=None, production_entry_count_target=0, camera=15,
            negative_class='already_stored_tank_relocation', tracked_tank_count=2,
            direction='storage_row_to_internal_left_aisle', visible_camera_clock_interval=interval,
            clock_uncertainty_seconds=3, evidence=[ev(k,1,end)],
            observation='Two tanks are already parked in the foreground storage group before the forklift approaches. One is placed on the other; forklift subsequently carries the stack away. Count two physical tank bodies but zero new production entries. Original fill dates, contents under covers and final downstream destination are not established.',
            label_scope='Only the selected foreground pair and its forklift trajectory. Excludes simultaneous rear doorway, scale, storage-placement or empty-return activity.'))
    negatives.append(dict(shared, sequence_id='20261006_empty_blue_return_1014', review_status='accepted_negative_sequence',
        cycle_id=None, production_entry_count_target=0, camera=15, negative_class='empty_crossing', tracked_tank_count=1,
        direction='15_to_11', visible_camera_clock_interval=['10:13:37','10:14:10'], clock_uncertainty_seconds=3,
        evidence=[ev('storage',5,16),ev('screen',70,73)],
        observation='One visibly empty blue-lined tank from the left waiting row is returned through the door14:01-07, gone from15 by10. Camera11 separately shows it already inside14:07 and parked14:37. No calibrated offset or scalar crossing second.',
        label_scope='Only this empty return; the forklift pair and rear gray storage placement are different tracks.'))
    merge(OUT / 'reviewed_sequence_labels.json', partials + negatives, 'sequence_id')
    queuepath = OUT / 'sequence_followup_queue.json'
    save(OUT / 'review_history/followup_queue_before_20261031_25.json', read(queuepath))
    merge(queuepath, [dict(candidate_id='20261006_next_blue_departure_1017', date='20261006', split='train',
        cycle_id=None, production_entry_count_target=None, status='partial_followup_pending', reviewed_at=stamp,
        observation='Different replacement receives cheese08:37-17:07, covered load at doorway17:22 and gone17:37. No corresponding room15 entry or subsequent complete route inspected yet.',
        next_action='Review existing archive15 source16:42-18:01 and following18:47-19:45 against11 screen; keep gaps explicit. No new extraction currently running.',
        evidence=[ev('screen',48,84)])], 'candidate_id')
    save(OUT / 'gap_search_20261031_25.json', dict(reviewed_at=stamp, day='20261006',
        findings=['10:08 fresh departure and candidate room15 entry are visible with uncalibrated clocks.',
            'Room15 staging09:05 to09:38 has33-second sampled gap; camera11 shows later scale arrival and dwell.',
            'Camera11 platform clear13:00 to first usable room15 storage route13:25 is nominally25 seconds, without calibrated offset. Initial13:03 frame is early and cannot bridge the route.',
            'Two genuine already-stored foreground-pair relocations confirmed independently of new-load rear storage.'],
        action='Retain partial fresh cycles and three scoped negatives; no invented complete cycle.'))

    registry = read(OUT / 'object_review_decisions.json')
    save(OUT / 'review_history/object_decisions_before_20261031_25.json', registry)
    decisions = {r['id']:r for r in registry['reviews']}
    drafts = {r['id']:r for r in read(BASE / 'detector_v1/visual_annotation_draft.json')['records']}
    object_notes = {
        '191':'Two distinct gray bodies in a forklift stack. Lower tank feet truncated by ROI; lower top partly occluded by upper tank.',
        '192':'Two gray bodies in a second forklift stack. Upper cover truncated by ROI; lower top occluded by upper tank. No background tank fragment retained.',
        '193':'Single visibly empty blue-lined waiting tank; body clear.',
        '194':'Fixed scrap tank, conveyor and person occlude lower body. Load class not part of this object-box annotation.',
        '195':'Single covered blue-lined production departure, isolated clear body.',
    }
    for ident, note in object_notes.items():
        assert ident not in decisions
        r = drafts[ident]
        attrs = [dict(box_index=i, truncated=(ident=='191' and i==1) or (ident=='192' and i==0),
            occluded=(ident in ['191','192'] and i==1) or ident=='194', load_state='unknown_not_annotated') for i in range(len(r['boxes_xyxy']))]
        sheet = 'labels_22.jpg' if ident in ['191','192'] else 'labels_23.jpg'
        decisions[ident] = dict(id=ident, image_sha256=r['sha256'],
            boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review', review_date='2026-10-31', decision='accepted_for_roi_tank_detection',
            load_state_reviewed=False, sequence_reviewed=False, instance_attributes=attrs,
            evidence=[r['source_frame'],r['frames_manifest'],'outputs/tank_transfer_training_v1/detector_v1/sheets/'+sheet], note=note)
    registry['reviews'] = list(decisions.values())
    registry.setdefault('corrections', []).append('Batch25:191-195 separately overlay reviewed; five ROIs and seven tank boxes. Prior decisions unchanged.')
    save(OUT / 'object_review_decisions.json', registry)
    inv = read(BASE / 'archive_inventory.json')
    inspected = {m['source']['member']:m['source_sha256'] for m in metas.values()}
    for r in inv['records']:
        if r['member'] in inspected:
            r.update(pixel_inspected=True, sha256=inspected[r['member']])
    assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test')
    save(BASE / 'archive_inventory.json', inv)
    reviews = read(OUT / 'screening_source_reviews.json')
    total = sum(r['sampled_frames_visually_reviewed'] for r in reviews)
    added = sum(len(m['samples']) for m in metas.values())
    state['last_completed'] += [
        f'Batch25 inspected {added} chronological presentations in7 windows on6Oct; {total} total across {len({r["source_sha256"] for r in reviews})} sources and {len(reviews)} windows. Extractions complete;25/28Oct untouched.',
        'Two stored foreground gray-pair forklift relocations added as track-scoped negatives, two physical tanks each. Separate empty blue15-to11 return added. Totals60 negatives; post-storage movement now represented.',
        'Fresh blue09:59 and10:08 departures retained as partials.08min candidate entry and scale visible, but staging and storage route gaps retained. Totals5 complete cycles,24 partials. Next17min load queued.',
        'Five native ROI images191-195 and seven tank boxes approved after separate overlays. Totals196 candidates,141 approved images,199 boxes,55 exclusions,zero drafts. No training release.'
    ]
    state['priority_next'] = [
        'Batch25 complete.5 complete cycles all13Oct; diversify complete cycles on other train days.60 negatives now include2 true already-stored pair relocation episodes. Same-load reentry remains unrepresented.',
        '6Oct next distinct blue departure17:22-37 is queued. Existing11 screening covers fresh fill08:37-17:07. Review15 source16:42-18:01 and18:47-19:45, then later route only if needed. Check extraction before starting.',
        '6Oct09:59 and10:08 remain partial. Do not repeat missing13:00-25 route search without new coverage; early initial13:03 frame is not continuous route evidence.',
        '13Oct later sources may provide further full cycles, but prioritise training-day diversity and validation complete-cycle coverage.17Oct remains validation only.'
    ] + [p for p in state['priority_next'] if p.startswith('Known gaps') or p.startswith('25/28') or p.startswith('Old21Oct')]
    state.update(updated_at=stamp, active_extraction_processes=[], dataset_ready=False)
    state.setdefault('completed_curation_runs', []).append(RUN)
    state['scripts'] += [s for s in ['work/append_tank_roi_batch_20261031_25.py','work/record_tank_sequence_batch_20261031_25.py'] if s not in state['scripts']]
    save(OUT / 'continuation_state.json', state)
    print(json.dumps(dict(recorded=RUN, additional_samples=added, total_presentations=total,
        additional_complete_cycles=0, additional_partial_sequences=2, additional_negative_sequences=3, training_started=False)))


if __name__ == '__main__':
    main()
