"""Record 6 October 10:17 fresh departure and two stored-pair relocations."""
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read, save, merge, evidence

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'outputs/tank_transfer_training_v1'
OUT = BASE / 'dataset_v1'
RUN = 'sequence_review_20261031_26'


def main():
    state = read(OUT / 'continuation_state.json')
    if RUN in state.get('completed_curation_runs', []):
        print('Already recorded', RUN)
        return
    stamp = dt.datetime.now(dt.timezone.utc).isoformat()
    windows = {
        'entry': ('blue_entry_1017_cam15', 21),
        'scale': ('blue_scale_1019_cam15', 19),
        'stored': ('blue_storage_1024_cam15', 12),
        'departure': ('blue_departure_1017_cam11', 18),
        'scale11': ('blue_scale_view_1018_cam11', 11),
        'late11': ('blue_scale_view_1021_cam11', 6),
        'clear11': ('blue_scale_clear_1023_cam11', 10),
    }
    paths = {k: OUT / 'sequence_review/20261006' / w / 'frames.json' for k, (w, n) in windows.items()}
    metas = {k: read(p) for k, p in paths.items()}
    for k, m in metas.items():
        assert m['source']['date'] == '20261006' and m['source']['split'] == 'train'
        assert len(m['samples']) == windows[k][1]
    clocks = {
        'entry': {0:'10:16:42',1:'10:17:03',3:'10:17:09',4:'10:17:12',5:'10:17:15',6:'10:17:18',7:'10:17:21',8:'10:17:24',9:'10:17:27',10:'10:17:30',11:'10:17:33',12:'10:17:36',13:'10:17:39',14:'10:17:42',15:'10:17:45',16:'10:17:48',17:'10:17:51',20:'10:18:00'},
        'scale': {0:'10:18:47',1:'10:18:52',2:'10:18:55',3:'10:18:58',4:'10:19:01',5:'10:19:04',6:'10:19:07',7:'10:19:10',8:'10:19:13',9:'10:19:16',10:'10:19:19',11:'10:19:22',12:'10:19:25',13:'10:19:28',14:'10:19:31',15:'10:19:34',18:'10:19:43'},
        'stored': {0:'10:24:38',1:'10:24:53',2:'10:24:55',3:'10:24:56',4:'10:24:59',5:'10:25:01',6:'10:25:03',7:'10:25:04',8:'10:25:07',9:'10:25:09',10:'10:25:11',11:'10:25:13'},
        'departure': {0:'10:17:06',1:'10:17:08',2:'10:17:10',3:'10:17:12',4:'10:17:14',5:'10:17:16',6:'10:17:18',7:'10:17:20',8:'10:17:22',9:'10:17:24',10:'10:17:26',11:'10:17:28',12:'10:17:30',13:'10:17:32',14:'10:17:34',17:'10:17:40'},
        'scale11': {0:'10:18:13',1:'10:18:36',2:'10:18:40',3:'10:18:45',4:'10:18:48',5:'10:18:52',6:'10:18:57',7:'10:19:01',8:'10:19:04',9:'10:19:09',10:'10:19:13'},
        'late11': {0:'10:21:17',1:'10:21:28',2:'10:21:31',3:'10:21:34',4:'10:21:37',5:'10:21:40'},
        'clear11': {0:'10:23:12',1:'10:23:24',2:'10:23:27',3:'10:23:30',4:'10:23:33',5:'10:23:36',6:'10:23:39',7:'10:23:42',8:'10:23:45',9:'10:23:48'},
    }
    notes = {
        'entry': 'Initial16:42 image is early; usable17:03 onward. Fresh arriving blue-lined tank: operator at door18, white top/body visible21-24, inside at27, staged beside doorway30-18:00. Threshold/body partly occluded by people and fixed bins. Concurrent forklift movement is separate: two covered gray tanks are already parked in foreground row at03-09. Forklift approaches12-18, lifts one21-24, stacks it on the adjacent tank27-30, withdraws33, reengages36, carries pair39-48. Neither selected foreground tank arrived through the doorway in this episode.',
        'scale': 'Tank already on far-right scale at first usable18:52 and stays through19:43. Initial18:47 frame is early. Operator attends it; no measured kilograms visible. A separate forklift arrives empty18:58-19:01, lifts the previously parked foreground gray07-10, places it on a previously parked beige13-16, withdraws19, reengages22-25 and carries the mixed-color pair28-31. Full native samples1,7,9,11,13 confirm the right-edge beige origin and stacking, which cropped sheets partly omit.',
        'stored': 'Initial24:38 frame early. At first usable24:53 another gray blue-covered tank is already parked in front of the rear storage row; remains through25:13. Its trajectory from scale and final parking were not captured in this source. A person walks out of door53-55, across aisle56-59 and exits left25:01. No same-load link from19min scale to this parked tank is asserted. Window name storage denotes search intent, not a confirmed placement.',
        'departure': 'Existing filling sequence continues into final covering: cheese layer visible17:06, sheet laid08, covered10. Tank pulled from filling station12-16, approach door18-20, crossing22-26, small edge28 and gone30. Different empty tank stays in left waiting position; it is not moved into filling station during this window. Workers leave area afterwards, with no new station tank through40. Fixed scrap tank remains separate.',
        'scale11': 'Initial18:13 image early and platform clear, but first usable18:36 already shows blue-covered load on platform through doorway; present through19:13. This does not capture the transition to scale. Empty waiting tank and scrap receptacle remain stationary in11. Door-frame occlusion retained.',
        'late11': 'Initial21:17 early image; usable21:28-40 retains the same platform position through doorway. A person moves from doorway into11; no tank return during these samples. Filling station still unoccupied, empty waiting tank and scrap tank remain.',
        'clear11': 'Initial23:12 early image. First usable23:24 has platform clear; no tank on it through48. Person walks15-to11 at27-33. Last inspected scale occupancy21:40 to first usable clear23:24 leaves104 seconds without a reviewed route; do not infer a storage trajectory. Initial23:12 is not a contiguous boundary frame.',
    }
    for k, m in metas.items():
        merge(OUT / 'screening_source_reviews.json', [dict(
            review_id='20261006/' + windows[k][0], reviewed_at=stamp, reviewer='assistant_visual_review',
            date='20261006', camera=m['source']['camera'], split='train', source_member=m['source']['member'],
            source_sha256=m['source_sha256'], frames_manifest=str(paths[k].relative_to(ROOT)),
            sampled_frames_visually_reviewed=len(m['samples']), reviewed_sheets=m['sheets'],
            review_scope='All chronological sampled sheets inspected, with selected native frames and separate object overlays. Not exhaustive native-frame tracking.',
            observation=notes[k], accepted_complete_cycle=False,
            clock_warning='Early source-initial images are not continuous temporal bridges; camera clocks are not calibrated from PTS or filenames.',
            visible_clock_anchors=[dict(sample_index=i, source_pts_seconds=m['samples'][i]['source_pts_seconds'],
                relative_pts_seconds=m['samples'][i]['relative_pts_seconds'], visible_camera_clock=t,
                clock_read_uncertainty_seconds=1, image=m['samples'][i]['image'],
                usable_for_clock_alignment=not(i == 0 and k != 'departure')) for i, t in clocks[k].items()]
        )], 'review_id')

    def ev(k, a, b):
        return evidence(metas[k], a, b, paths[k])

    labels = read(OUT / 'reviewed_sequence_labels.json')
    save(OUT / 'review_history/sequence_labels_before_20261031_26.json', labels)
    fillpath = OUT / 'sequence_review/20261006/production_screen_0956_cam11/frames.json'
    fill = read(fillpath)
    shared = dict(date='20261006', split='train', reviewer='assistant_visual_review', reviewed_at=stamp, dataset_release_accepted=False)
    partial = dict(shared, sequence_id='20261006_fresh_blue_departure_partial_1017',
        review_status='reviewed_partial_sequence', cycle_id=None, production_entry_count_target=None,
        camera_track_id={'11':'blue_filling_1008_departure1017','15':'candidate_blue_entry1017_scale1018'},
        camera_clock_offset_seconds=None, cross_camera_identity='consistent_departure_arrival_candidate_with_uncalibrated_clocks',
        stages=[dict(stage='filling_observed', camera=11, visible_camera_clock_interval=['10:08:37','10:17:06'],
                content_evidence='Previously empty local replacement receives cheese layers; final layer visible before covering. Fixed scrap receptacle distinct.',
                evidence=[evidence(fill,48,82,fillpath),ev('departure',0,1)]),
            dict(stage='loaded_departure_11', camera=11, visible_camera_clock_interval=['10:17:12','10:17:30'],
                doorway_interval=['10:17:22','10:17:30'], clock_uncertainty_seconds=2,
                observation='Covered load pulled from station12, crosses22-28 and gone30. Not the empty waiting tank.', evidence=[ev('departure',2,12)]),
            dict(stage='entry_15', camera=15, visible_camera_clock_interval=['10:17:21','10:17:27'],
                clock_uncertainty_seconds=3, identity_status='candidate_cross_camera_match',
                observation='White-topped blue-lined tank visible behind operator at doorway21-24, inside27, staged30 onward. No scalar cross-camera offset assigned.', evidence=[ev('entry',6,20)]),
            dict(stage='scale_visit', camera=15, visible_camera_clock_interval=['10:18:52','10:19:43'], numeric_weight_kg=None,
                arrival_time_unobserved=True, observation='Already on platform in first usable15 frame;11 sees it18:36-19:13 and again21:28-40. Last usable staging18:00 to first usable11 scale18:36 is an unresolved transition interval with separate clocks.',
                evidence=[ev('scale',1,18),ev('scale11',1,10),ev('late11',1,5)])],
        missing_stages=['observed_staging_to_scale_transition','linked_storage_placement'],
        unlinked_followup=dict(last_usable_scale_occupancy_camera11='10:21:40', first_usable_clear_platform_camera11='10:23:24',
            camera11_scale_clearance_sample_gap_seconds=104, last_usable_camera15_scale='10:19:43',
            first_usable_already_stored_camera15='10:24:53', camera15_route_sample_gap_seconds=310,
            storage_placement_observed=False, evidence=[ev('late11',5,5),ev('clear11',1,9),ev('stored',1,11)],
            observation='A gray tank is already parked by rear row24:53. Do not assign it to this fresh cycle across missing scale departure and storage route.'),
        limitations=['Incomplete cycle has no production count target.', 'White cover alone is not cheese evidence.', 'Camera clocks uncalibrated; source-initial stale images excluded from alignment.'])
    negatives = []
    for k, ident, interval, end, detail in [
        ('entry','20261006_stored_gray_pair_relocation_1017',['10:17:03','10:17:48'],16,
            'Two gray tanks already in foreground row. Forklift lifts one21-24, stacks27-30, withdraws33 and carries the pair39-48.'),
        ('scale','20261006_stored_gray_beige_pair_relocation_1019',['10:18:52','10:19:31'],14,
            'Gray and beige both already in right foreground row in native frame18:52. Gray lifted19:07-10, stacked onto beige13-16. Forks withdrawn19, reengaged22-25; mixed-color pair carried28-31. Native samples7,9,11,13 clarify movement partly outside sheet crop.'),
    ]:
        negatives.append(dict(shared, sequence_id=ident, review_status='accepted_negative_sequence', cycle_id=None,
            production_entry_count_target=0, camera=15, negative_class='already_stored_tank_relocation', tracked_tank_count=2,
            direction='foreground_storage_to_internal_left_aisle', visible_camera_clock_interval=interval,
            clock_uncertainty_seconds=3, evidence=[ev(k,1,end)], observation=detail,
            label_scope='Only the selected foreground pair and forklift movement. Simultaneous fresh doorway/scale load is excluded. Two physical bodies, zero new production entries; contents and original fill dates unknown.'))
    merge(OUT / 'reviewed_sequence_labels.json', [partial] + negatives, 'sequence_id')
    queuepath = OUT / 'sequence_followup_queue.json'
    queue = read(queuepath)
    save(OUT / 'review_history/followup_queue_before_20261031_26.json', queue)
    old = next(r for r in queue if r['candidate_id']=='20261006_next_blue_departure_1017')
    q = copy.deepcopy(old)
    q.update(reviewed_at=stamp, status='resolved_to_reviewed_partial', resolved_sequence_id=partial['sequence_id'],
        observation='Fresh17min departure and candidate15 entry confirmed; scale subsequently occupied. Staging-to-scale transition and later storage route missing. Tank already parked24:53 cannot complete the cycle.',
        next_action='Keep partial; do not repeat absent route searches without new coverage. Prioritise day diversity and remaining unreviewed sources.')
    q['evidence'] += [ev('departure',0,17),ev('entry',6,20),ev('scale',1,18),ev('stored',1,11)]
    merge(queuepath, [q], 'candidate_id')
    save(OUT / 'gap_search_20261031_26.json', dict(reviewed_at=stamp, day='20261006', findings=[
        'Fresh load reaches15 staging17:21-27; usable staging ends18:00. First usable11 scale18:36 and15 scale18:52 are already occupied.',
        'Last inspected11 scale21:40 to clear23:24 is104 seconds.15 last usable19:43 to already stored24:53 is310 seconds.',
        'No source-initial stale frame used to fabricate a route; no same-load storage identity assigned.',
        'Two independent forklift relocations proven from previously parked foreground pairs, including mixed gray/beige stack.'],
        action='One reviewed partial and two scoped negatives; no new complete cycle.'))

    registry = read(OUT / 'object_review_decisions.json')
    save(OUT / 'review_history/object_decisions_before_20261031_26.json', registry)
    decisions = {r['id']:r for r in registry['reviews']}
    drafts = {r['id']:r for r in read(BASE / 'detector_v1/visual_annotation_draft.json')['records']}
    obj_notes = {
        '196':'Covered production departure, isolated body at medium distance.',
        '197':'Same production load at doorway, far right body partly hidden by door frame.',
        '198':'Small scale tank seen through room11 doorway; left body occluded by door frame.',
        '199':'Visibly empty waiting tank, single clear instance.',
        '200':'Gray upper and beige lower are separate physical tanks. Lower tank cropped at bottom and occluded by upper tank; native chronological context confirms its extent and identity.',
    }
    for ident, note in obj_notes.items():
        assert ident not in decisions
        r = drafts[ident]
        attrs = [dict(box_index=i, truncated=ident=='200' and i==1,
            occluded=ident in ['197','198'] or (ident=='200' and i==1), load_state='unknown_not_annotated') for i in range(len(r['boxes_xyxy']))]
        sheet = 'labels_23.jpg' if ident in ['196','197','198'] else 'labels_24.jpg'
        decisions[ident] = dict(id=ident, image_sha256=r['sha256'],
            boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review', review_date='2026-10-31', decision='accepted_for_roi_tank_detection',
            load_state_reviewed=False, sequence_reviewed=False, instance_attributes=attrs,
            evidence=[r['source_frame'],r['frames_manifest'],'outputs/tank_transfer_training_v1/detector_v1/sheets/'+sheet], note=note)
    registry['reviews'] = list(decisions.values())
    registry.setdefault('corrections', []).append('Batch26:196-200 independently overlay reviewed. Five ROI images and six boxes; earlier decisions unchanged.')
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
        f'Batch26 inspected {added} chronological presentations in7 windows on6Oct; {total} total across {len({r["source_sha256"] for r in reviews})} sources and {len(reviews)} windows. Extractions complete;25/28Oct untouched.',
        'Fresh blue17min departure/entry and later scale occupancy retained as partial; staging transition missing,104-second11 scale-clearance and310-second15 storage-route gaps. Totals5 complete cycles and25 partials.',
        'Two additional stored-pair forklift relocations confirmed, including a gray-over-beige stack with native right-edge context. Totals62 negatives,4 post-storage relocation episodes. No new-production targets assigned to these tracks.',
        'Five native ROI images196-200 and six boxes separately approved. Totals201 candidates,146 approved images,205 boxes,55 exclusions,zero drafts. Training remains unreleased.'
    ]
    state['priority_next'] = [
        'Batch26 complete.5 full cycles remain all13Oct; prioritise day diversity and complete validation sequences.62 negatives include4 genuine post-storage pair relocations; do not spend another batch only on easy negatives.',
        'Metadata-only scan: unreviewed21Oct15 source113657-113819_12543381 has82-second filename span. Inspect adjacent11/15 chronology for possible day-diverse full cycle; filename span does not prove decoded continuity.',
        '6Oct17min fresh cycle now resolved to partial.11 scale occupancy21:40 then clear23:24;15 last usable19:43 then already parked24:53. Do not repeat route search without additional media.',
        '6Oct09:59/10:08 and15Oct repeated partials preserve observed stages but remain incomplete.13Oct later continuous sources can expand positives after day-diverse review.'
    ] + [p for p in state['priority_next'] if p.startswith('Known gaps') or p.startswith('25/28') or p.startswith('Old21Oct')]
    state.update(updated_at=stamp, active_extraction_processes=[], dataset_ready=False)
    state.setdefault('completed_curation_runs', []).append(RUN)
    state['scripts'] += [s for s in ['work/append_tank_roi_batch_20261031_26.py','work/record_tank_sequence_batch_20261031_26.py'] if s not in state['scripts']]
    save(OUT / 'continuation_state.json', state)
    print(json.dumps(dict(recorded=RUN, additional_samples=added, total_presentations=total,
        additional_complete_cycles=0, additional_partial_sequences=1, additional_negative_sequences=2, training_started=False)))


if __name__ == '__main__':
    main()
