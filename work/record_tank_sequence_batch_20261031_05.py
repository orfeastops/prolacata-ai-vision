"""Persist the completed visual review of three source windows and ROI batch05.

Observations are manual, source-backed and intentionally keep gaps unresolved.
This script records curation only; it cannot release or start training.
"""
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read, save, merge, evidence

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'outputs/tank_transfer_training_v1'
OUT = BASE/'dataset_v1'
RUN = 'sequence_review_20261031_05'


def main():
    state = read(OUT/'continuation_state.json')
    if RUN in state.get('completed_curation_runs', []):
        print('Already recorded:', RUN)
        return
    stamp = dt.datetime.now(dt.timezone.utc).isoformat()
    windows = {
        'before6': ('20261006', 'blue_before_departure_0935', 14),
        'return15': ('20261015', 'gray_return_1117_review', 45),
        'next13': ('20261013', 'after_storage_next_load_1054', 51),
    }
    paths = {k: OUT/'sequence_review'/d/n/'frames.json' for k, (d, n, _) in windows.items()}
    metas = {k: read(p) for k, p in paths.items()}
    for k, m in metas.items():
        assert len(m['samples']) == windows[k][2]
        assert m['source']['date'] == windows[k][0] and m['source']['split'] == 'train'
        assert all((ROOT/s['image']).is_file() for s in m['samples'])
    # These anchors were read from the camera overlay, not calculated from filenames.
    clocks = {
        'before6': {0:'09:35:06',1:'09:35:19',2:'09:35:22',3:'09:35:25',4:'09:35:28',5:'09:35:31',6:'09:35:34',7:'09:35:37',8:'09:35:40',9:'09:35:43',10:'09:35:46',11:'09:35:49',12:'09:35:52',13:'09:35:55'},
        'return15': {0:'11:16:46',1:'11:17:05',6:'11:17:15',11:'11:17:25',16:'11:17:35',21:'11:17:45',23:'11:17:49',24:'11:17:51',25:'11:17:53',26:'11:17:55',27:'11:17:57',28:'11:17:59',29:'11:18:01',30:'11:18:03',31:'11:18:05',32:'11:18:07',36:'11:18:15',37:'11:18:17',38:'11:18:19',39:'11:18:21',40:'11:18:23',41:'11:18:25',42:'11:18:27',43:'11:18:29',44:'11:18:31'},
        'next13': {0:'10:53:56',1:'10:54:00',2:'10:54:04',3:'10:54:08',8:'10:54:28',13:'10:54:48',16:'10:55:00',21:'10:55:20',26:'10:55:40',31:'10:56:00',36:'10:56:20',37:'10:56:24',38:'10:56:28',39:'10:56:32',40:'10:56:36',41:'10:56:40',42:'10:56:44',43:'10:56:48',44:'10:56:52',45:'10:56:56',46:'10:57:00',47:'10:57:04',48:'10:57:08',49:'10:57:12',50:'10:57:16'},
    }
    notes = {
        'before6': 'Room15 scale is empty. Fixed blue bins and covered storage rows remain stationary. One person crosses from room11 into room15 at09:35:19-22 and walks away by09:35:25 without a tank. A forklift approaches the doorway09:35:43-55 without a visible tank on its forks. First frame reads09:35:06, next09:35:19. Source ends09:35:55 and therefore does not show the room15 counterpart of the loaded room11 crossing09:36:05-11. This reviewed earlier export does not resolve the blue-tank entry/staging gap.',
        'return15': 'Camera11 doorway is clear of tank movements11:17:05-49. One visibly empty gray tank on a manual jack crosses room15-to11 at11:17:51-55; liner and empty bottom are visible. It moves left out of this ROI, and the operator returns with empty jack11:18:01-07. Later a person-only doorway passage toward15 occurs11:18:17-21 and a return toward11 at11:18:27-29. The preceding room15 gray internal movement ended11:17:36; the approximately15-second gap prevents a certified same-tank match. Keep the earlier internal negative and this later empty return as potentially the same episode, without adding another distinct tank/negative count. The first source frame11:16:46 is stale relative to the next11:17:05.',
        'next13': 'The beige tank accepted as stored in the earlier13Oct cycle remains stationary at the left end of the rear row throughout10:53:56-10:57:16; do not count it again. An unloaded yellow powered jack leaves the foreground around10:53:56-10:54:08. Foreground workers handle cylindrical cans and their pallets, which are not large tank transfers. Door-side activity increases10:56:20-24. By10:56:32 and through10:57:16, a partially occluded light/gray tank-shaped body and white top are visible beside the doorway behind the fixed blue bins, with two operators handling the area. Origin, exact crossing and payload are not established at this wide sampling. Queue a closer camera11/15 review; no new complete cycle or production-entry target is assigned. No new scale departure or storage is visible in this window.',
    }
    reviews = []
    for k, m in metas.items():
        day, name, _ = windows[k]
        reviews.append(dict(review_id=day+'/'+name, reviewed_at=stamp, reviewer='assistant_visual_review',
            source_member=m['source']['member'], source_sha256=m['source_sha256'], date=day,
            camera=m['source']['camera'], split='train', frames_manifest=str(paths[k].relative_to(ROOT)),
            sampled_frames_visually_reviewed=len(m['samples']), reviewed_sheets=m['sheets'],
            review_scope='All chronological contact-sheet samples visually inspected, with full native context where needed; not exhaustive native-frame viewing.',
            visible_clock_anchors=[dict(sample_index=i, source_pts_seconds=m['samples'][i]['source_pts_seconds'],
                relative_pts_seconds=m['samples'][i]['relative_pts_seconds'], visible_camera_clock=t,
                clock_read_uncertainty_seconds=1, image=m['samples'][i]['image'],
                usable_for_clock_alignment=not(i==0 and k in ['before6','return15'])) for i,t in clocks[k].items()],
            observation=notes[k], accepted_complete_cycle=False,
            clock_warning='Read from visible clock pixels. Initial source jumps and occlusion remain explicit; no synchronization is derived from filename or PTS.'))
    merge(OUT/'screening_source_reviews.json', reviews, 'review_id')

    def ev(k, a, b):
        return evidence(metas[k], a, b, paths[k])

    seqpath = OUT/'reviewed_sequence_labels.json'
    labels = {s['sequence_id']:s for s in read(seqpath)}
    p6 = labels['20261006_blue_filling_departure_partial_0936']
    gray = labels['20261015_gray_empty_internal_move_111716']
    hp = OUT/'review_history/sequence_labels_before_20261031_05.json'
    if not hp.exists():
        save(hp, dict(saved_at=stamp, reason='Preserve partial and negative versions before adding gap-search results and an unlinked return.',
                      records=[copy.deepcopy(p6), copy.deepcopy(gray)]))
    p6['reviewed_at'] = stamp
    p6['entry_gap_search'] = dict(status='earlier_source_reviewed_gap_unresolved', evidence=[ev('before6',0,13)],
        visible_camera_clock_interval=['09:35:06','09:35:55'], observation=notes['before6'])
    p6['next_review'] = 'Do not repeat the09:35 export: its final visible clock is09:35:55. Current sources do not bridge the09:36:05-11 loaded departure to the room15 candidate first seen09:36:42. Preserve partial status. Scale/storage follow-up may be reviewed as an unlinked track, or expand better-covered training cycles.'
    gray['reviewed_at'] = stamp
    gray['unlinked_followup'] = dict(status='empty_return_observed_same_tank_identity_unresolved',
        camera=11, camera_track_id='cam11_empty_gray_return_111751', negative_class='empty_crossing',
        visible_camera_clock_interval=['11:17:51','11:17:55'], clock_uncertainty_seconds=2,
        production_entry_count_target=0, distinct_negative_sequence_increment=0, identity_with_parent_track='unresolved',
        evidence=[ev('return15',23,28)],
        observation='One visibly empty gray tank passes15-to11 at11:17:51-55. This could be the earlier gray internal movement, but the intervening route is unobserved. Retain as an unlinked follow-up rather than inventing identity or counting an additional distinct negative episode. Parent label remains the observed internal movement only.')
    common = dict(split='train', reviewer='assistant_visual_review', reviewed_at=stamp,
        review_status='accepted_negative_sequence', cycle_id=None, production_entry_count_target=0,
        dataset_release_accepted=False, negative_class='people_without_tank')
    people6 = dict(common, sequence_id='20261006_person_without_tank_093519', date='20261006', camera=15,
        camera_track_id='cam15_person_only_crossing_093519', visible_camera_clock_interval=['09:35:19','09:35:25'],
        clock_uncertainty_seconds=3, tracked_tank_count=0, evidence=[ev('before6',0,4)],
        observation='A person walks through the shared doorway into15 and continues left without moving a tank.',
        label_scope='Only this person-only doorway passage. Stationary tanks in the room and later forklift motion are separate; not a whole-frame absence label.')
    people15 = dict(common, sequence_id='20261015_person_without_tank_111817', date='20261015', camera=11,
        camera_track_id='cam11_person_only_door_episode_111817', visible_camera_clock_interval=['11:18:17','11:18:29'],
        clock_uncertainty_seconds=2, observed_person_passages=2, tracked_tank_count=0, evidence=[ev('return15',36,44)],
        observation='Person-only doorway passages occur toward15 at11:18:17-21 and toward11 at11:18:27-29. No tank accompanies either passage. Do not infer a personal identity across occlusion.',
        label_scope='One short negative doorway episode containing two person-only passages; zero production tank entries. Earlier empty-gray return is excluded from this time interval.')
    labels.update({s['sequence_id']:s for s in [people6,people15]})
    save(seqpath, list(labels.values()))
    merge(OUT/'sequence_followup_queue.json', [dict(candidate_id='20261013_door_activity_105632', date='20261013', split='train',
        status='needs_origin_and_entry_review_not_a_cycle_label', reviewed_at=stamp,
        production_entry_count_target=None, cycle_id=None, evidence=[ev('next13',36,50)], observation=notes['next13'],
        next_source_camera11='13.10/Camera_11_DVR_DVR_20261030171248/Camera_11_DVR_20261013104601_20261013110052_11549117.mp4',
        next_source_camera15='13.10/Camera_15_DVR_DVR_20261030171248/Camera_15_DVR_20261013105715_20261013105746_11619421.mp4')], 'candidate_id')

    context_path = OUT/'roi_context_batch05/manifest.json'
    context = {r['id']:r for r in read(context_path)}
    registry = read(OUT/'object_review_decisions.json')
    decisions = {r['id']:r for r in registry['reviews']}
    draft = {r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
    notes_roi = {
        '066':'Full native context resolves the tiny room11 tank sliver at the upper right and the inverted tank corner at lower left. All four visible instances labeled, then overlay reviewed.',
        '067':'Full native context resolves two separate room11 background tanks, two fixed blue tanks and the left-edge gray tank. All five instances labeled, then overlay reviewed.',
        '088':'Narrow validation ROI isolates a single blue tank from a crowded room. Full source context and rendered overlay both inspected.',
        '089':'Validation ROI isolates a visibly empty foreground beige tank. Lower body is image-truncated; it is an object annotation only, not a transfer/entry label.',
    }
    for ident, sourceid in [('066','066'),('067','067'),('088','072'),('089','073')]:
        r = draft[ident]
        c = context[sourceid]
        assert ident not in decisions
        assert hashlib.sha256((ROOT/c['native_image']).read_bytes()).hexdigest() == c['source_sha256']
        sheet = BASE/'detector_v1/sheets'/('labels_06.jpg' if ident in ['066','067'] else 'labels_09.jpg')
        decisions[ident] = dict(id=ident, image_sha256=r['sha256'],
            boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review', review_date='2026-10-31', decision='accepted_for_roi_tank_detection',
            load_state_reviewed=False, sequence_reviewed=False,
            instance_attributes=[dict(box_index=j, truncated=(b[0]==0 or b[1]==0 or b[2]==r['width'] or b[3]==r['height']),
                occluded=(ident in ['066','067']), load_state='unknown_not_annotated') for j,b in enumerate(r['boxes_xyxy'])],
            evidence=[c['native_image'], str(context_path.relative_to(ROOT)), str(sheet.relative_to(ROOT))],
            source_provenance=dict(source_member=c['source_member'], source_sha256=c['source_sha256'],
                native_source_image=c['native_image'], context_manifest=str(context_path.relative_to(ROOT))),
            note=notes_roi[ident])
    registry['reviews'] = list(decisions.values())
    rejected = {r['id']:r for r in registry.get('excluded_roi_reviews',[])}
    reasons = {
        '060':'Crowded storage row and border fragments cannot yet be exhaustively separated with confident instance boundaries.',
        '061':'Crowded storage row and border fragments cannot yet be exhaustively separated with confident instance boundaries.',
        '062':'Crowded storage row and border fragments cannot yet be exhaustively separated with confident instance boundaries.',
        '069':'Nested tank stack has top truncation and person occlusion; do not label the whole stack as one tank.',
        '072':'Tray stacks obscure tank body edges and small border fragments. Cleaner isolated validation ROI088 retained separately.',
        '073':'Tray stacks and border fragments prevent confident exhaustive boxes for this ROI. Cleaner foreground validation ROI089 retained separately.',
        '074':'Tray stacks obscure body edges and border fragments; exhaustive instance annotation remains uncertain.',
    }
    for ident, reason in reasons.items():
        r = draft[ident]
        assert r['annotation_status'] == 'excluded_uncertain_instance_boundaries'
        rejected[ident] = dict(id=ident, image_sha256=r['sha256'], reviewed_at=stamp,
            reviewer='assistant_visual_review', decision='exclude_whole_roi_not_an_empty_image', reason=reason,
            evidence=[context[ident]['native_image'],str(context_path.relative_to(ROOT))])
    registry['excluded_roi_reviews'] = list(rejected.values())
    registry.setdefault('corrections',[]).append('Batch05: full-context review adds omitted border instances to066/067 and accepts them after overlay review; isolated validation ROIs088/089 accepted. Seven uncertain crowded ROIs excluded, not used as empty negatives. Previous47 accepted decisions preserved.')
    save(OUT/'object_review_decisions.json',registry)
    inventory = read(BASE/'archive_inventory.json')
    inspected = {m['source']['member']:m['source_sha256'] for m in metas.values()}
    inspected.update({c['source_member']:c['source_sha256'] for c in context.values()})
    for r in inventory['records']:
        if r['member'] in inspected:
            r['pixel_inspected'] = True
            r['sha256'] = inspected[r['member']]
    assert not any(r['pixel_inspected'] for r in inventory['records'] if r['split']=='test')
    save(BASE/'archive_inventory.json',inventory)
    state['last_completed'] += [
        'Batch05 reviewed110 additional chronological sample presentations across three source windows:950 total across19 source videos and27 windows. No extraction remains active.',
        '6Oct earlier room15 export ends09:35:55 and does not bridge the09:36:05-11 loaded departure. The blue cycle stays partial; the unsuccessful gap search is recorded to avoid repeating it.',
        '15Oct one visibly empty gray tank returns15-to11 at11:17:51-55. It remains an unlinked follow-up to the earlier internal negative because its15-second trajectory gap prevents identity confirmation; no extra distinct tank/negative count assigned.',
        'Added two track-scoped people-without-tank negative episodes. Totals remain1 accepted complete cycle and3 partials; negative sequences now7.',
        '13Oct stored beige tank remains stationary through10:57:16. A later occluded doorway candidate is queued for origin/entry review without a new production label.',
        'Native context and separate overlays completed for066/067/088/089.90 ROI candidates,51 accepted images and84 accepted boxes;33 excluded and6 drafts remain. Validation-day images stay validation. Training remains unreleased.'
    ]
    state['priority_next'] = [
        'Batch05 is complete; do not repeat its three windows.950 temporal presentations and all extraction completed. Latest source reviews and sequence_followup_queue.json hold the next source references.',
        '13Oct next candidate: inspect camera11 around10:55-10:57 in20261013104601_20261013110052_11549117 and camera15 doorway/next sources after10:57:15. Existing beige storage-row tank stays stationary; do not count it again. Confirm fresh filling, load origin and crossing before assigning a new cycle.',
        '6Oct arrival gap remains unresolved: room15 earlier export ends09:35:55; next candidate begins09:36:42. Do not repeat either window or infer match from blue color. Preserve partial and prioritize other complete coverage; review later scale/storage only as an unlinked track.',
        '15Oct beige scale-to-storage trajectory gap11:15:46-11:16:23 remains unresolved. Later storage is confirmed only for the later track. Gray empty return11:17:51-55 is recorded without cross-camera identity or another distinct negative count.',
        'Six object drafts remain002/003/006/007/010/011. Seven new crowded uncertain ROIs060-062/069/072-074 were excluded with reasons, not converted into empty negatives. Expand representative clear object images on other training days.',
        'Expand complete cycles on other training days and same-load reentry/already-stored relocation negatives.17Oct validation still lacks reviewed complete cycles.25/28Oct remain locked without pixels. No training or uploads.'
    ]
    state.update(updated_at=stamp, active_extraction_processes=[], dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    for p in ['work/append_tank_validation_rois_20261031_05.py','work/record_tank_sequence_batch_20261031_05.py','work/verify_tank_dataset_curation_v1.py']:
        if p not in state['scripts']:
            state['scripts'].append(p)
    save(OUT/'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_temporal_samples=110,additional_negative_sequences=2,
        additional_approved_images=4,additional_approved_boxes=11,training_started=False)))


if __name__=='__main__':
    main()
