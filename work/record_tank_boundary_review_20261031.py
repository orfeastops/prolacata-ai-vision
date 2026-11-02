"""Record the completed visual boundary and native-context review.

All observations below were made from the referenced image sequences. This is
dataset curation, not a model prediction, weight measurement or training run.
"""
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'outputs/tank_transfer_training_v1'
OUT = BASE / 'dataset_v1'
RUN = 'boundary_review_20261031_02'


def read(p):
    return json.loads(p.read_text(encoding='utf8'))


def save(p, x):
    tmp = p.with_suffix('.tmp')
    tmp.write_text(json.dumps(x, indent=2, ensure_ascii=False), encoding='utf8')
    tmp.replace(p)


def merge(path, incoming, key):
    rows = {r[key]: r for r in read(path)} if path.exists() else {}
    rows.update({r[key]: r for r in incoming})
    save(path, list(rows.values()))


def evidence(meta, a, b, manifest):
    sa, sb = meta['samples'][a], meta['samples'][b]
    return dict(source_member_or_path=meta['source']['member'],
                source_sha256=meta['source_sha256'], camera=meta['source']['camera'],
                source_pts_interval=[sa['source_pts_seconds'], sb['source_pts_seconds']],
                relative_pts_interval=[sa['relative_pts_seconds'], sb['relative_pts_seconds']],
                sample_index_interval=[a,b], frames_manifest=str(manifest.relative_to(ROOT)),
                image_evidence=[sa['image'], sb['image']])


def main():
    state = read(OUT / 'continuation_state.json')
    if RUN in state.get('completed_curation_runs', []):
        print('Already recorded:', RUN)
        return
    stamp = dt.datetime.now(dt.timezone.utc).isoformat()
    keys = ['departure_boundary_review', 'departure_boundary_review_target',
            'entry_boundary_review', 'storage_boundary_review', 'scale_join_review']
    paths = {k: OUT / 'sequence_review/20261013' / k / 'frames.json' for k in keys}
    metas = {k: read(p) for k,p in paths.items()}
    assert [len(metas[k]['samples']) for k in keys] == [19,19,19,44,16]
    assert all(m['source']['date']=='20261013' and m['source']['split']=='train' for m in metas.values())
    # These anchors were read from rendered camera-clock pixels, not filenames.
    clocks = {
        keys[0]: {0:'10:42:45',1:'10:42:46',6:'10:42:51',12:'10:42:57',15:'10:43:00',18:'10:43:03'},
        keys[1]: {0:'10:47:45',1:'10:47:46',6:'10:47:51',9:'10:47:54',11:'10:47:56',12:'10:47:57',13:'10:47:58',14:'10:47:59',15:'10:48:00',18:'10:48:03'},
        keys[2]: {0:'10:47:53',3:'10:47:56',4:'10:47:57',5:'10:47:58',6:'10:47:59',8:'10:48:01',12:'10:48:05',18:'10:48:11'},
        keys[3]: {0:'10:52:22',2:'10:52:26',3:'10:52:28',4:'10:52:30',6:'10:52:34',24:'10:53:10',26:'10:53:14',28:'10:53:18',30:'10:53:22',34:'10:53:30',36:'10:53:34',39:'10:53:40',40:'10:53:42',43:'10:53:48'},
        keys[4]: {0:'10:50:40',1:'10:50:47',2:'10:50:47',3:'10:50:48',5:'10:50:49',7:'10:50:50',11:'10:50:52',14:'10:50:54',15:'10:50:54'}
    }
    notes = {
        keys[0]: 'Workers place cheese blocks into a beige tank at the filling station. No tank leaves the doorway in this bounded window. The default peer index selected an earlier source; its visible clock is10:42:45-10:43:03. It is preserved as separate partial filling evidence, NOT used as the10:47 transfer counterpart.',
        keys[1]: 'Same beige tank with white top is pulled from filling station to the doorway. Its body crosses during10:47:56-59 and is out of room11 by10:48:00. A different visibly empty gray tank is moved from the local row to the filling station during the same window.',
        keys[2]: 'One arriving beige tank with white top and manual pallet jack is partly visible behind the operator and fixed blue bins. Corresponding movement follows the camera11 departure. Body/centre are occluded: retain10:47:56-10:48:01 as a room15 event interval, not a fabricated exact second. No numeric clock offset is asserted.',
        keys[3]: 'Beige tank leaves the scale between10:52:26 and10:52:30, waits in the occluded door staging area, then emerges10:53:14-18. Same tank moves left, parks near the left end of the rear row, and the manual jack is visibly withdrawn by10:53:42. Tank remains parked through10:53:48. A yellow truck carrying small white packaging containers is a separate concurrent movement.',
        keys[4]: 'Adjacent camera15 file begins with a10:50:40 image, then at relativePTS0.520 already reads10:50:47. The preceding source final inspected frame reads10:50:46. The beige tank remains in the same scale position throughout. Exclude the initial stale/out-of-order clock anchor from synchronization; preserve the source frame and PTS.'
    }
    new_reviews = []
    for k in keys:
        m = metas[k]
        for s in m['samples']:
            assert (ROOT / s['image']).exists()
        new_reviews.append(dict(review_id='20261013/'+k, reviewed_at=stamp,
            reviewer='assistant_visual_review', source_member=m['source']['member'],
            source_sha256=m['source_sha256'], date='20261013', camera=m['source']['camera'], split='train',
            frames_manifest=str(paths[k].relative_to(ROOT)),
            sampled_frames_visually_reviewed=len(m['samples']), reviewed_sheets=m['sheets'],
            review_scope='Every chronological contact-sheet sample viewed. Native frame decoding is not equivalent to exhaustive human review.',
            visible_clock_anchors=[dict(sample_index=i, source_pts_seconds=m['samples'][i]['source_pts_seconds'],
                relative_pts_seconds=m['samples'][i]['relative_pts_seconds'], visible_camera_clock=t,
                clock_read_uncertainty_seconds=1, image=m['samples'][i]['image'],
                usable_for_clock_alignment=not(k==keys[4] and i==0)) for i,t in clocks[k].items()],
            observation=notes[k], clock_warning='Keep explicit event intervals and per-source camera clocks; no filename+PTS time conversion.',
            accepted_complete_cycle=False))
    merge(OUT/'screening_source_reviews.json', new_reviews, 'review_id')

    labels = read(OUT/'reviewed_sequence_labels.json')
    target = next(s for s in labels if s['sequence_id']=='20261013_beige_filling_to_storage_candidate_01')
    # Preserve the previous annotation verbatim before superseding its status.
    history = OUT/'sequence_review_history'
    history.mkdir(exist_ok=True)
    snapshot = history/(RUN+'_prior_cycle.json')
    if not snapshot.exists():
        save(snapshot, copy.deepcopy(target))
    target.update(reviewed_at=stamp, review_status='accepted_complete_cycle',
        cycle_id='20261013_beige_1047', production_entry_count_target=1,
        cross_camera_identity='assistant_visual_correspondence_reviewed_with_occlusion',
        clock_alignment='shared_crossing_visually_checked_timestamp_uncertainty_retained',
        camera_clock_offset_seconds=None, dataset_release_accepted=False,
        entry_camera=15, entry_clock_interval=['10:47:56','10:48:01'],
        counting_rule='One increment for this load at room15 entry, finalized by reviewed scale visit and storage placement; never increment again at scale departure.',
        prior_annotation=str(snapshot.relative_to(ROOT)))
    stages = {s['stage']:s for s in target['stages']}
    c11p = OUT/'sequence_review/20261013/camera11_counterpart/frames.json'
    c11m = read(c11p)
    stages['filling_observed'].update(visible_camera_clock_interval=['10:46:21','10:47:26'],
        evidence=[evidence(c11m,1,17,c11p)], clock_uncertainty_seconds=4,
        observation='Cheese blocks and additional placements are visible. Beginning of the full fill and total contents are not known.')
    stages['loaded_departure_11'].update(visible_camera_clock_interval=['10:47:45','10:48:00'],
        clock_uncertainty_seconds=1,
        doorway_crossing_camera11_interval=['10:47:56','10:47:59'],
        evidence=[evidence(metas[keys[1]],0,15,paths[keys[1]])])
    stages['entry_15'].update(visible_camera_clock_interval=['10:47:56','10:48:01'],
        clock_uncertainty_seconds=3, timestamp_precision='interval_only',
        evidence=[evidence(metas[keys[2]],3,8,paths[keys[2]]),
                  evidence(metas[keys[1]],11,15,paths[keys[1]])],
        correspondence_basis='Matching tank body/top, manual-jack movement, adjacent shared doorway and a single continuous observed departure/arrival. Camera11 supplies the unobscured crossing; camera15 time is retained as an occlusion interval.')
    stages['scale_visit']['evidence'].extend([
        evidence(metas[keys[4]],1,15,paths[keys[4]]),
        evidence(metas[keys[3]],0,4,paths[keys[3]])])
    stages['scale_visit']['scale_departure_clock_interval']=['10:52:26','10:52:30']
    stages['scale_visit']['source_join_review'] = dict(
        preceding_visible_clock='10:50:46', next_noninitial_sample_clock='10:50:47',
        rejected_alignment_anchor='Initial adjacent-source frame reads10:50:40; subsequent samples advance from10:50:47.',
        identity_evidence='Same beige tank stationary on scale in both neighboring sources and in dense join samples.',
        coverage_caveat='Sampled join review, not a claim that every wall-clock millisecond is recorded.')
    storage = stages['storage_placement_candidate']
    storage.update(stage='storage_placement', visible_camera_clock_interval=['10:53:14','10:53:42'],
        clock_uncertainty_seconds=2, parked_and_jack_withdrawal_interval=['10:53:40','10:53:42'],
        evidence=[evidence(metas[keys[3]],26,43,paths[keys[3]])],
        confirmation='Tank stays at left end of rear row; manual pallet jack withdrawn and moved away. No additional production entry at storage placement.')
    target['stages'] = list(stages.values())
    target['limitations'] = [
        'Assistant-reviewed annotation, not a model prediction or independently user-certified count.',
        'The fill is already underway when the origin clip begins. No starting contents, block total or kilograms are inferred.',
        'Room15 arrival and short staging intervals are occluded by fixed bins. Identity is supported by both views and the subsequent scale/storage path; do not use this as an unoccluded localization label.',
        'No scalar inter-camera clock offset is certified. Event timing is an explicit5-second camera15 interval, supported by the corresponding camera11 crossing.',
        'Adjacent export starts with a stale/out-of-order clock image. Its original bytes and PTS remain preserved; that anchor is not used for timing.',
        'Complete means all required cycle stages are evidenced, not uninterrupted visibility of every pixel or verification of a scale reading.',
        'Global dataset coverage and release checks remain incomplete; no training is authorized by this label.'
    ]

    negative = dict(sequence_id='20261013_cam11_empty_gray_to_station_01', date='20261013',split='train',
        reviewer='assistant_visual_review', reviewed_at=stamp, review_status='accepted_negative_sequence',
        negative_class='empty_tank_internal_reposition', camera_track_id='cam11_gray_empty_replacement_104751',
        cycle_id=None, production_entry_count_target=0, dataset_release_accepted=False,
        visible_camera_clock_interval=['10:47:51','10:48:03'],clock_uncertainty_seconds=1,
        evidence=[evidence(metas[keys[1]],6,18,paths[keys[1]])],
        label_scope='Only the empty gray replacement tank. The beige tank simultaneously leaving the room is a separate positive load.',
        observation='Worker moves an empty gray liner-equipped tank from the local stored-empty row into the filling station. The visible bottom/liner is empty. It does not enter room15 and is not a new stored production load.')
    partial = dict(sequence_id='20261013_cam11_filling_partial_104245',date='20261013',split='train',
        reviewer='assistant_visual_review',reviewed_at=stamp,review_status='reviewed_partial_sequence',
        partial_reason='No departure, room15 entry, scale or storage stages inside this bounded source window.',
        cycle_id=None,camera_track_id='cam11_beige_filling_104245_unlinked',
        production_entry_count_target=None,dataset_release_accepted=False,
        visible_camera_clock_interval=['10:42:45','10:43:03'],
        evidence=[evidence(metas[keys[0]],0,18,paths[keys[0]])],
        observation=notes[keys[0]],
        relation_to_other_sequences='Unlinked; a beige color and neighboring filename alone do not establish it is the later10:47 load.')
    save(OUT/'reviewed_sequence_labels.json', labels)
    merge(OUT/'reviewed_sequence_labels.json',[negative,partial],'sequence_id')

    draft = read(BASE/'detector_v1/visual_annotation_draft.json')['records']
    registry = read(OUT/'object_review_decisions.json')
    decisions = {r['id']:r for r in registry['reviews']}
    for r in draft:
        if r['id'] not in ['063','064','065','068','070','071']:
            continue
        old = decisions.get(r['id'])
        if old:
            registry.setdefault('superseded_reviews',[]).append(dict(superseded_at=stamp,reason='Previously omitted background tank visible through doorway.',review=old))
        attrs=[]
        for j,b in enumerate(r['boxes_xyxy']):
            attrs.append(dict(box_index=j,truncated=any([b[0]==0,b[1]==0,b[2]==r['width'],b[3]==r['height']]),
                occluded=(j==1 and r['id'] in ['063','064','065','068']) or (r['id']=='065' and j>=2) or (r['id']=='070' and j==2),
                load_state='unknown_not_annotated'))
        decisions[r['id']] = dict(id=r['id'],image_sha256=r['sha256'],
            boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review',review_date='2026-10-31',
            decision='accepted_for_roi_tank_detection',load_state_reviewed=False,sequence_reviewed=False,
            instance_attributes=attrs,
            evidence=[str((OUT/'object_full_context'/f'{r["id"]}_detail.jpg').relative_to(ROOT)),
                str((BASE/'detector_v1/sheets'/('labels_07.jpg' if r['id'] in ['070','071'] else 'labels_06.jpg')).relative_to(ROOT))],
            note='Rechecked all identifiable visible ROI instances, including truncated beige/gray background tanks in room11. These background boxes do not imply new room15 entries. Fully hidden objects and non-identifiable slivers are not invented.')
    registry['reviews'] = list(decisions.values())
    registry['corrections'] = list(dict.fromkeys(registry['corrections']+[
        '20261031 boundary review corrected omitted background tank instances through the room15 doorway in063-065,068,070,071. Four new images approved; prior070/071 decisions retained in superseded_reviews.',
        '066/067 remain unaccepted: doorway manipulation/person occlusion and edge fragments require more native context. Their existing drafts are not clean supervision.'
    ]))
    save(OUT/'object_review_decisions.json',registry)
    inv = read(BASE/'archive_inventory.json')
    seen = {m['source']['member'] for m in metas.values()}
    for r in inv['records']:
        if r['member'] in seen:
            r['pixel_inspected']=True
    assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test')
    save(BASE/'archive_inventory.json',inv)

    state['last_completed'] += [
        '117 additional temporal samples reviewed in5 bounded windows; total453 presentations from6 source videos. Initial wrong-peer source is explicitly isolated as partial filling evidence, not a matched transfer.',
        '13/10 beige cycle accepted after denser departure/entry/storage and adjacent-file join review. One production entry; room15 clock interval10:47:56-10:48:01 retained, not an invented exact synchronization.',
        'One empty gray internal replacement-tank movement added as a tracked negative. Total2 accepted negatives; simultaneous positive beige departure is separate.',
        'Camera15 object review added omitted room11 background tanks.063,064,065,068 approved;070/071 corrected with prior decisions preserved. Total36 accepted ROI images. All remain unreleased for training.'
    ]
    state['priority_next'] = [
        'Do not repeat the completed13/10 boundary review. Read reviewed_sequence_labels.json:1 accepted complete cycle,2 tracked negatives,1 separate partial filling sequence.',
        'Expand distinct positive cycles on6 and15/10 using additional archive source windows. Initial191 samples on6,13,15 and subsequent13/10 windows are already reviewed.',
        'Review unresolved camera15 object cases002/003/006/007/010/011 and066/067 with native source context, including tanks visible through doorway.060-062/069/072-074 pending;24 ambiguous images remain excluded.',
        'Collect other negative types: empty crossings, same-load re-entry and relocation after storage. Do not substitute internal filling-station motion for coverage of these missing types.',
        '17/10 validation still needs both-camera cycle examples.25/28 remain locked and unopened. Do not train or upload.',
        'Update review page and checks after every accepted batch; current progress is far below dataset release coverage.'
    ]
    state['updated_at']=stamp
    state['active_extraction_processes']=[]
    state.setdefault('completed_curation_runs',[]).append(RUN)
    save(OUT/'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_reviewed_samples=117,accepted_cycle_count=1,training_started=False)))


if __name__=='__main__':
    main()
