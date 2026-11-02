"""Persist only observations made during the assistant's visual review.

No learned labels, cross-camera synchronization, or training is inferred here.
Existing reviews outside this batch are preserved.
"""
import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'outputs/tank_transfer_training_v1'
OUT = BASE / 'dataset_v1'


def read(p):
    return json.loads(p.read_text(encoding='utf8'))


def save(p, value):
    tmp = p.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf8')
    tmp.replace(p)


def merge_list(path, incoming, key):
    rows = read(path) if path.exists() else []
    by_id = {r[key]: r for r in rows}
    by_id.update({r[key]: r for r in incoming})
    save(path, list(by_id.values()))


def main():
    stamp = dt.datetime.now(dt.timezone.utc).isoformat()
    # Only the two unambiguous camera15 ROI images pass this batch's final
    # overlay review. Six other new drafts retain their unaccepted status.
    draft = read(BASE / 'detector_v1/visual_annotation_draft.json')['records']
    registry = read(OUT / 'object_review_decisions.json')
    decisions = {r['id']: r for r in registry['reviews']}
    for r in draft:
        if r['id'] not in ('070', '071'):
            continue
        decisions[r['id']] = dict(id=r['id'], image_sha256=r['sha256'],
            boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'], separators=(',', ':')).encode()).hexdigest(),
            reviewer='assistant_visual_review', review_date='2026-10-31',
            decision='accepted_for_roi_tank_detection', load_state_reviewed=False, sequence_reviewed=False,
            instance_attributes=[dict(box_index=0, truncated=False, occluded=False),
                                 dict(box_index=1, truncated=True, occluded=False)],
            evidence=['outputs/tank_transfer_training_v1/dataset_v1/object_full_context/070_detail.jpg',
                      'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_07.jpg'],
            note='Foreground gray bin and left-truncated beige bin are separate instances. No load label is accepted.')
    registry['reviews'] = list(decisions.values())
    registry['corrections'] = list(dict.fromkeys(registry['corrections'] + [
        'Eight additional camera15 ROI images received draft boxes;070 and071 passed rendered-overlay review. Other six drafts remain unaccepted.'
    ]))
    save(OUT / 'object_review_decisions.json', registry)

    paths = ['20261006', '20261013', '20261015', '20261013/entry_detail',
             '20261013/camera11_counterpart', '20261013/storage_context']
    meta = {key: read(OUT / 'sequence_review' / key / 'frames.json') for key in paths}
    notes = {
        '20261006': 'Forklift moves stacked rigid containers through the room; workers handle items on stationary covered tanks. The sampled view alone does not establish a fresh camera11 production load. Keep forklift movements separate from production entries.',
        '20261013': 'Foreground staff handle pallets of small white metal containers. A beige tank transfer near the rear doorway was selected for closer review with both cameras. Existing pallets and stationary stock must not become new production-tank entries.',
        '20261015': 'Handling around a beige tank already at the scale at clip start, yellow pallet truck carrying a stack of blue containers, and later people/empty truck movements. No full origin-to-storage cycle accepted from this clip.',
        '20261013/entry_detail': 'Native-source doorway detail reviewed every2seconds. Beige tank is strongly occluded by stationary blue bins after arrival; a narrow white vertical shape is insufficient to label a tank by itself. Full-frame context and camera11 support the candidate. Empty blue pallet jack later moves into the open room.',
        '20261013/camera11_counterpart': 'Cheese blocks visibly added to beige tank; white surface covering applied, then same tank taken from filling station to door. A gray empty tank replaces it. A separate blue pallet jack approaches and crosses without a tank.',
        '20261013/storage_context': 'Beige tank remains on scale, is moved off, then brought along front of stored row to a place near its left end. Full native context was additionally reviewed for samples24-27 and36-44 because doorway-only crops omit final placement.'
    }
    clocks = {
        '20261006': {0:'09:43:06',1:'09:43:14',8:'09:43:42',16:'09:44:14',24:'09:44:46',32:'09:45:18'},
        '20261013': {0:'10:41:40',1:'10:41:53',16:'10:42:53',32:'10:43:57',48:'10:45:01',64:'10:46:06',80:'10:47:10',96:'10:48:14',112:'10:49:18',134:'10:50:46'},
        '20261015': {0:'11:12:12',1:'11:12:19',8:'11:12:47',16:'11:13:19',22:'11:13:43'},
        '20261013/entry_detail': {0:'10:47:45',6:'10:47:57',7:'10:47:59',8:'10:48:01',9:'10:48:03',10:'10:48:05',30:'10:48:45',35:'10:48:55',39:'10:49:03',41:'10:49:07',42:'10:49:09',44:'10:49:13'},
        '20261013/camera11_counterpart': {0:'10:46:01',1:'10:46:21',18:'10:47:30',22:'10:47:46',23:'10:47:50',24:'10:47:54',25:'10:47:58',26:'10:48:02',31:'10:48:22',38:'10:48:50',39:'10:48:54',42:'10:49:06',54:'10:49:54'},
        '20261013/storage_context': {0:'10:50:40',1:'10:50:50',24:'10:52:22',25:'10:52:26',26:'10:52:30',27:'10:52:34',36:'10:53:10',37:'10:53:14',38:'10:53:18',39:'10:53:22',40:'10:53:26',41:'10:53:30',42:'10:53:34',43:'10:53:38',44:'10:53:42'}
    }
    reviews = []
    for key, m in meta.items():
        anchors = []
        for index, clock in clocks[key].items():
            s = m['samples'][index]
            anchors.append(dict(sample_index=index, source_pts_seconds=s['source_pts_seconds'],
                relative_pts_seconds=s['relative_pts_seconds'], visible_camera_clock=clock,
                clock_read_uncertainty_seconds=1, image=s['image']))
        reviews.append(dict(review_id=key.replace('/', '_'), reviewed_at=stamp, reviewer='assistant_visual_review',
            source_member=m['source']['member'], source_sha256=m['source_sha256'],
            date=m['source']['date'], camera=m['source']['camera'], split='train',
            frames_manifest=str((OUT/'sequence_review'/key/'frames.json').relative_to(ROOT)),
            sampled_frames_visually_reviewed=len(m['samples']), reviewed_sheets=m['sheets'],
            review_scope='All contact-sheet samples viewed chronologically; not every native frame and not final temporal boundary certification.',
            visible_clock_anchors=anchors, observation=notes[key],
            clock_warning='Several files show a visible-clock jump near their beginning. Do not convert filename start plus PTS into camera time or treat these anchors as cross-camera calibration.',
            accepted_complete_cycle=False))
    merge_list(OUT / 'screening_source_reviews.json', reviews, 'review_id')

    def evidence(key, first, last):
        m = meta[key]
        a, b = m['samples'][first], m['samples'][last]
        return dict(source_member_or_path=m['source']['member'], source_sha256=m['source_sha256'],
            camera=m['source']['camera'], source_pts_interval=[a['source_pts_seconds'], b['source_pts_seconds']],
            relative_pts_interval=[a['relative_pts_seconds'], b['relative_pts_seconds']],
            sample_index_interval=[first,last], frames_manifest=str((OUT/'sequence_review'/key/'frames.json').relative_to(ROOT)),
            image_evidence=[a['image'],b['image']])

    candidate = dict(sequence_id='20261013_beige_filling_to_storage_candidate_01',date='20261013',split='train',
        reviewer='assistant_visual_review', reviewed_at=stamp,
        review_status='candidate_complete_cycle_needs_boundary_and_clock_review',
        dataset_release_accepted=False, cycle_id=None, candidate_cycle_id='20261013_beige_1047',
        camera_track_id={'11':'beige_filling_tank_01','15':'beige_door_scale_storage_candidate_01'},
        cross_camera_identity='visually_supported_candidate_not_finalized', clock_alignment='not_calibrated',
        origin_content='Cheese blocks visible at filling station and placements observed before the white top is covered.',
        production_entry_count_target=None,
        stages=[
            dict(stage='filling_observed',visible_camera_clock_interval=['10:46:01','10:47:46'],clock_uncertainty_seconds=4,
                 evidence=[evidence('20261013/camera11_counterpart',0,22)]),
            dict(stage='loaded_departure_11',visible_camera_clock_interval=['10:47:50','10:48:02'],clock_uncertainty_seconds=4,
                 evidence=[evidence('20261013/camera11_counterpart',23,26)]),
            dict(stage='entry_15',visible_camera_clock_interval=['10:47:57','10:48:05'],clock_uncertainty_seconds=2,
                 evidence=[evidence('20261013/entry_detail',6,10)],occlusion='Stationary blue bins hide most of the tank body.'),
            dict(stage='scale_visit',visible_camera_clock_interval=['10:48:55','10:52:26'],clock_uncertainty_seconds=4,
                 evidence=[evidence('20261013/entry_detail',35,44),evidence('20261013',112,134),evidence('20261013/storage_context',0,25)],
                 numeric_weight_kg=None,measurement_success_verified=False),
            dict(stage='storage_placement_candidate',visible_camera_clock_interval=['10:53:18','10:53:42'],clock_uncertainty_seconds=4,
                 evidence=[evidence('20261013/storage_context',38,44)],
                 location='Near left end of the rear stored-tank row; verified in full native frames, not the narrow doorway crop.')],
        limitations=[
            'Retain this as a candidate, not an accepted complete training cycle, until denser departure/placement review and shared doorway clock calibration.',
            'Source starts during filling; beginning of fill is not visible. No block or mass total is inferred.',
            'Camera15 adjacent source has a beginning clock jump; inspect native join before certifying continuous identity across it.',
            'Covered stored tanks visible at start are opening inventory. The new beige tank is the only proposed production load in this candidate.'
        ])
    negative = dict(sequence_id='20261013_cam15_empty_blue_pallet_jack_01',date='20261013',split='train',
        reviewer='assistant_visual_review', reviewed_at=stamp,review_status='accepted_negative_sequence',
        negative_class='pallet_jack_without_tank',camera_track_id='cam15_blue_pallet_jack_104903',cycle_id=None,
        production_entry_count_target=0, label_scope='This tracked pallet-jack movement only; not a room-wide negative label.',
        visible_camera_clock_interval=['10:49:03','10:49:13'],clock_uncertainty_seconds=2,
        evidence=[evidence('20261013/entry_detail',39,44)],
        observation='Worker pulls blue powered pallet jack away from doorway and left into room. Its forks are visible without a tank. Previously arrived beige tank stays separate near scale.',
        dataset_release_accepted=False, release_note='Negative track annotation accepted; global dataset release remains blocked by incomplete coverage and QA.')
    merge_list(OUT/'reviewed_sequence_labels.json', [candidate,negative], 'sequence_id')

    inv = read(BASE/'archive_inventory.json')
    seen = {m['source']['member'] for m in meta.values()}
    for r in inv['records']:
        if r['member'] in seen:
            r['pixel_inspected']=True
    assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test')
    save(BASE/'archive_inventory.json',inv)

    state=read(OUT/'continuation_state.json')
    state['updated_at']=stamp
    state['last_completed'] += [
        'All191 initial temporal samples on6,13,15/10 were visually screened, with source-backed observations and manually read clock anchors saved.',
        'Additional145 samples on13/10 were extracted and visually inspected: camera11 counterpart55, camera15 doorway detail45, adjacent scale/storage context45. All extraction completed.',
        'A source-backed candidate beige-tank cycle on13/10 now links visible filling, door departure, strongly occluded arrival, scale dwell and final storage. It is NOT yet an accepted complete cycle: dense boundary/clock review remains.',
        'One tracked blue pallet-jack movement without a tank is accepted as a negative sequence; it is not a whole-room absence label.',
        'Eight additional camera15 image drafts with18 boxes were added;070/071 passed overlay review, raising accepted ROI images from30 to32.'
    ]
    state['priority_next']=[
        'Read reviewed_sequence_labels.json and screening_source_reviews.json. Do not repeat completed screening of336 temporal samples.',
        'Finalize the13/10 beige candidate: refine camera11 counterpart PTS88-106 at0.5-1s, camera15 original PTS364-382, and storage_context source PTS96-180. Check native clock transitions; compare shared doorway action. Keep explicit timestamp intervals until calibrated.',
        'For storage detail use the FULL native frame or crop x300..960 on the960x540 reference. The doorway-only crop omits the tank final placement. The tank is parked at the left end of the rear row near10:53:34-42.',
        'Review camera15 boxes063-068 with visible-instance geometry.066 has a tiny lower-left fragment requiring a decision.060-062,069 and072-074 remain pending; do not infer stacks as a single tank.',
        'Find further positive camera15 sources on6 and15 using archive inventory. Current longest examples mostly show forklift/internal handling; avoid forcing them into positive production-cycle labels.',
        'Expand training images, completed cycles and hard negatives across days.17/10 validation;25/28 locked. No training or external upload.'
    ]
    state['scripts']=list(dict.fromkeys(state['scripts']+['work/refine_tank_sequence_evidence_v1.py','work/record_tank_visual_review_20261031.py']))
    state['active_extraction_processes']=[]
    state['dataset_ready']=False
    save(OUT/'continuation_state.json',state)
    print(json.dumps(dict(reviewed_temporal_sample_presentations=sum(len(m['samples']) for m in meta.values()),
        new_roi_approvals=2,accepted_complete_cycles=0,accepted_negative_tracks=1)))


if __name__=='__main__':
    main()
