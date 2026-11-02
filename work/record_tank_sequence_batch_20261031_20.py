"""Persist the visually inspected 13Oct 09:27 transfer; no training."""
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read, save, merge, evidence

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'outputs/tank_transfer_training_v1'
OUT = BASE / 'dataset_v1'
RUN = 'sequence_review_20261031_20'


def main():
    state = read(OUT / 'continuation_state.json')
    if RUN in state.get('completed_curation_runs', []):
        print('Already recorded', RUN)
        return
    stamp = dt.datetime.now(dt.timezone.utc).isoformat()
    windows = {
        'origin': ('origin_0927_cam11', 68),
        'route': ('route_0927_cam15', 68),
        'storage': ('storage_0932_cam15', 26),
        'entry_a': ('entry_0927a_cam15', 17),
        'entry_b': ('entry_0927b_cam15', 19),
        'departure': ('departure_0927_cam11', 33),
        'tail': ('storage_0932_tail_cam15', 24),
    }
    paths = {k: OUT / 'sequence_review/20261013' / w / 'frames.json' for k, (w,n) in windows.items()}
    metas = {k: read(p) for k,p in paths.items()}
    for k,m in metas.items():
        assert len(m['samples']) == windows[k][1]
        assert m['source']['date'] == '20261013' and m['source']['split'] == 'train'
    # Anchors were read from visible camera-clock pixels during inspection.
    # PTS and filenames are provenance, not substitutes for camera synchronization.
    clocks = {
        'origin': {0:'09:22:30',1:'09:22:52',9:'09:23:56',10:'09:24:04',23:'09:25:48',30:'09:26:44',31:'09:26:52',32:'09:27:00',33:'09:27:08',34:'09:27:16',35:'09:27:24',40:'09:28:04',41:'09:28:12',42:'09:28:20',43:'09:28:28',66:'09:31:32',67:'09:31:40'},
        'route': {0:'09:26:52',1:'09:27:15',3:'09:27:25',10:'09:28:00',11:'09:28:05',12:'09:28:10',13:'09:28:15',14:'09:28:20',15:'09:28:25',16:'09:28:30',52:'09:31:30',53:'09:31:35',54:'09:31:40',55:'09:31:45',63:'09:32:25',64:'09:32:30',65:'09:32:35',66:'09:32:40',67:'09:32:45'},
        'storage': {0:'09:32:38',1:'09:32:50',2:'09:32:52',3:'09:32:54',4:'09:32:56',5:'09:32:58',6:'09:33:00',8:'09:33:04',14:'09:33:16',15:'09:33:18',17:'09:33:22',19:'09:33:26',20:'09:33:29',21:'09:33:31',22:'09:33:33',25:'09:33:39'},
        'entry_a': {0:'09:26:52',6:'09:26:58',9:'09:27:01',11:'09:27:03',12:'09:27:04',13:'09:27:05',14:'09:27:06',15:'09:27:07',16:'09:27:08'},
        'entry_b': {0:'09:26:52',1:'09:27:10',2:'09:27:11',4:'09:27:12',6:'09:27:13',8:'09:27:14',10:'09:27:15',11:'09:27:16',13:'09:27:17',15:'09:27:18',17:'09:27:19',18:'09:27:19'},
        'departure': {0:'09:26:52',6:'09:26:58',8:'09:27:00',12:'09:27:04',14:'09:27:06',15:'09:27:07',16:'09:27:08',17:'09:27:09',18:'09:27:10',19:'09:27:11',24:'09:27:16',32:'09:27:24'},
        'tail': {0:'09:32:25',6:'09:32:31',7:'09:32:32',12:'09:32:37',15:'09:32:40',16:'09:32:41',20:'09:32:45',23:'09:32:48'},
    }
    notes = {
        'origin': 'Initial22:30 stale. Same low gray station tank receives fresh cheese22:52-26:44, covered26:52 and pulled27:00; threshold27:08, gone27:16. A separate empty gray waiting tank is moved to station27:08-16 and starts filling27:24. Through doorway new load approaches scale28:12-28, stays through31:32 and moves off31:40. Older load on scale through23:56 and empty jack return25:48 were already reviewed in batch19; do not duplicate them.',
        'route': 'Initial26:52 stale. First usable27:15 shows low gray load already inside left doorway staging. Liner/cover handling through28:05. Same load moves right toward scale28:10-25, settles28:25 and stays through31:30. Leaves scale31:35-45, stages beside door without recrossing31:45-32:25, then turns left into storage aisle32:30-45. Foreground workers and cylindrical containers are separate activity.',
        'storage': 'Initial32:38 stale. First usable32:50 has same tank at rear-row placement. Jack still engaged through32:54; unloaded forks visibly withdraw32:56-58. Tank stays through33:39. Empty jack travels toward doorway33:04-16, turns18-22, crosses26-31 and clears33. Two-second sampled join from previous source32:48 to32:50 retained.',
        'entry_a': 'Operator approaches26:58-27:03. Low gray tank front first intersects doorway at27:04; body follows27:05-08. Fixed blue bins partly occlude base. Last sample27:08 still at threshold. Exact next crossing frames fall across source boundary.',
        'entry_b': 'Initial26:52 stale, not an earlier entry. First usable27:10 shows same short gray tank just clear of threshold, then turning left27:11-14 and staging27:15. Same liner, geometry and operator/jack route as preceding27:08 and camera11 departure; two-second sampled source join retained.',
        'departure': 'Covered fresh-filled gray tank pulled26:58, clears station27:00-04, first threshold intersection27:06, body passes27:07-10, gone by27:11. Different visibly empty gray tank moves from local left waiting row27:07-16 to station; not a new room15 entry.',
        'tail': 'Same low gray load leaves post-scale staging32:25-31, turns in aisle32:32-40 and is pushed into rear storage row32:41-48. Forks still engaged at last sample32:48; next source first usable32:50 continues same position/operator before fork withdrawal56-58. No extra entry for this movement.',
    }
    for k,m in metas.items():
        initial = m['requested_window']['start'] == 0
        merge(OUT / 'screening_source_reviews.json', [dict(
            review_id='20261013/'+windows[k][0], reviewed_at=stamp, reviewer='assistant_visual_review',
            date='20261013', camera=m['source']['camera'], split='train', source_member=m['source']['member'],
            source_sha256=m['source_sha256'], frames_manifest=str(paths[k].relative_to(ROOT)),
            sampled_frames_visually_reviewed=len(m['samples']), reviewed_sheets=m['sheets'],
            review_scope='All chronological contact-sheet samples inspected; selected native frames and separate object-box overlays inspected. Sample presentations are not exhaustive native-frame viewing.',
            observation=notes[k], accepted_complete_cycle=False,
            clock_warning='Camera-clock intervals retained. Source-initial stale images excluded; filenames/PTS do not establish synchronization.',
            visible_clock_anchors=[dict(sample_index=i, source_pts_seconds=m['samples'][i]['source_pts_seconds'],
                relative_pts_seconds=m['samples'][i]['relative_pts_seconds'], visible_camera_clock=t,
                clock_read_uncertainty_seconds=1, image=m['samples'][i]['image'],
                usable_for_clock_alignment=not(initial and i==0)) for i,t in clocks[k].items()])], 'review_id')

    def ev(k,a,b): return evidence(metas[k],a,b,paths[k])
    shared = dict(date='20261013',split='train',reviewer='assistant_visual_review',reviewed_at=stamp,dataset_release_accepted=False)
    cycle_id = '20261013_gray_0927'
    sequence_id = '20261013_gray_filling_to_storage_0927'
    additions = [dict(shared,sequence_id=sequence_id,
        review_status='accepted_complete_cycle',cycle_id=cycle_id,
        camera_track_id={'11':'gray_station_0922_0927','15':'gray_entry_scale_storage_0927_0933'},
        cross_camera_identity='assistant_visual_correspondence_reviewed_with_occlusion',
        clock_alignment='shared_crossing_visually_checked_timestamp_uncertainty_retained',camera_clock_offset_seconds=None,
        entry_camera=15,entry_clock_interval=['09:27:04','09:27:10'],production_entry_count_target=1,
        origin_content='Fresh cheese placement observed before covering; a white cover alone is not load evidence.',
        counting_rule='One room15 entry finalized after scale visit and storage. Post-scale staging and parking do not increment.',
        stages=[
            dict(stage='filling_observed',visible_camera_clock_interval=['09:22:52','09:26:44'],clock_uncertainty_seconds=8,
                content_evidence='Workers place cheese into the same low gray station tank. Covered by26:52; initial contents unknown.',
                evidence=[ev('origin',1,31)]),
            dict(stage='loaded_departure_11',visible_camera_clock_interval=['09:26:58','09:27:11'],
                doorway_crossing_camera11_interval=['09:27:06','09:27:10'],clock_uncertainty_seconds=1,
                evidence=[ev('origin',30,34),ev('departure',6,19)]),
            dict(stage='entry_15',visible_camera_clock_interval=['09:27:04','09:27:10'],clock_uncertainty_seconds=2,
                observation='Same short gray tank, white top, loose liner and operator/jack route cross shared doorway then turn left. Foreground bins partly obscure base.',
                source_join_review=[dict(preceding_clock='09:27:08',next_noninitial_clock='09:27:10',sampled_gap_seconds=2,
                    evidence='Matching tank at threshold before and just clear after join; no competing tank at doorway. Initial26:52 is stale.')],
                evidence=[ev('entry_a',11,16),ev('entry_b',1,10),ev('departure',12,19)]),
            dict(stage='scale_visit',visible_camera_clock_interval=['09:28:10','09:31:45'],
                scale_approach_interval=['09:28:10','09:28:25'],scale_departure_clock_interval=['09:31:35','09:31:45'],
                clock_uncertainty_seconds=5,numeric_weight_kg=None,measurement_success_verified=False,
                observation='Same entry tank moves right onto platform, remains in position through31:30, then returns to near-door staging without crossing out.',
                evidence=[ev('route',1,63),ev('origin',40,67)]),
            dict(stage='storage_placement',visible_camera_clock_interval=['09:32:25','09:32:58'],
                parking_approach_interval=['09:32:41','09:32:54'],unloaded_fork_withdrawal_interval=['09:32:54','09:32:58'],
                clock_uncertainty_seconds=2,
                observation='Same gray load moves left along aisle, parks in rear row, and remains there while unloaded forks retreat. Tank stays through33:39.',
                source_join_review=[dict(preceding_clock='09:32:48',next_noninitial_clock='09:32:50',sampled_gap_seconds=2,
                    evidence='Same rear-row tank position, operator and engaged jack before and after join. Initial32:38 stale.')],
                evidence=[ev('route',63,67),ev('tail',0,23),ev('storage',1,25)])],
        limitations=['Sampled visual review, not all native frames.',
            'Two-second sampled joins at entry and final storage retained; no scalar camera offset asserted.',
            'No numeric weight, initial tank inventory or block count inferred.',
            'Separate empty replacement and next filling cycle are not part of this load.']),
        dict(shared,sequence_id='20261013_empty_gray_replacement_0927',camera=11,
            camera_track_id='20261013_empty_gray_replacement_0927',cycle_id=None,
            review_status='accepted_negative_sequence',production_entry_count_target=0,
            negative_class='empty_tank_internal_reposition',tracked_tank_count=1,
            visible_camera_clock_interval=['09:27:07','09:27:16'],clock_uncertainty_seconds=2,
            evidence=[ev('departure',15,24),ev('origin',33,35)],
            observation='One visibly empty gray tank moves from local waiting row to filling station, then new filling begins27:24.',
            label_scope='Only the empty replacement movement through27:16. Simultaneous filled-tank departure is the separate positive cycle; later filling is outside negative scope.'),
        dict(shared,sequence_id='20261013_unloaded_jack_after_storage_0933',camera=15,
            camera_track_id='20261013_unloaded_jack_after_storage_0933',cycle_id=None,
            review_status='accepted_negative_sequence',production_entry_count_target=0,
            negative_class='pallet_jack_without_tank',tracked_tank_count=0,
            visible_camera_clock_interval=['09:32:56','09:33:33'],clock_uncertainty_seconds=2,
            evidence=[ev('storage',4,22)],
            observation='Unloaded forks withdraw from newly stored tank, then empty jack returns through doorway. Stored tank remains.',
            label_scope='Only unloaded jack after completed storage; other stationary tanks and foreground activity are excluded.')]
    merge(OUT / 'reviewed_sequence_labels.json', additions, 'sequence_id')

    # Preserve the original candidate, then mark it resolved without treating a
    # follow-up queue record as a second production target.
    queue_path = OUT / 'sequence_followup_queue.json'
    queue = read(queue_path)
    prior = next(r for r in queue if r['candidate_id']=='20261013_next_arrival_0927')
    hist = OUT / 'review_history/arrival0927_before_20261031_20.json'
    if not hist.exists(): save(hist,copy.deepcopy(prior))
    prior.update(status='resolved_in_reviewed_complete_cycle',reviewed_at=stamp,
        resolved_sequence_id=sequence_id,prior_annotation=str(hist.relative_to(ROOT)),
        observation='Fresh origin, shared crossing, scale and storage reviewed in batch20. Accepted sequence is the sole production target.',
        next_action='Resolved. Do not recount this candidate or rerun the same extraction.',
        evidence=[ev('entry_a',12,16),ev('entry_b',1,10),ev('storage',1,5)])
    save(queue_path,queue)
    merge(queue_path,[dict(candidate_id='20261013_next_station_load_after0927',date='20261013',split='train',
        cycle_id=None,production_entry_count_target=None,status='candidate_next_departure_not_reviewed',reviewed_at=stamp,
        observation='Different gray replacement receives cheese at station27:24-31:40; no departure from this load in reviewed window.',
        next_action='For next13Oct cycle inspect11 sources093135-093311 and093311-094655, with matching15 sources after093339. Prioritize day diversity first.',
        evidence=[ev('origin',35,67)])],'candidate_id')
    save(OUT / 'gap_search_20261031_20.json',dict(reviewed_at=stamp,
        findings=['Entry source join09:27:08 to09:27:10 retains matching tank/operator at doorway; initial26:52 stale.',
            'Storage source join09:32:48 to09:32:50 retains tank placement and engaged jack; initial32:38 stale.',
            'Empty replacement in11 is separate from freshly filled load entering15.'],
        action='Accept one visually matched cycle with interval uncertainty. No exact scalar clock offset or measured weight inferred.'))

    registry = read(OUT / 'object_review_decisions.json')
    hist = OUT / 'review_history/object_decisions_before_20261031_20.json'
    if not hist.exists(): save(hist,registry)
    decisions = {r['id']:r for r in registry['reviews']}
    drafts = {r['id']:r for r in read(BASE / 'detector_v1/visual_annotation_draft.json')['records']}
    descriptions = {'164':'Covered fresh gray departure, full visible body.',
        '165':'Separate empty gray replacement tank; worker behind rim.',
        '167':'Separate scrap receptacle; conveyor occludes lower right.',
        '168':'Gray tank on scale viewed through doorway; post and worker occlusion.',
        '169':'Same gray storage transit tank, top truncated by crop. Bottom-right fragment is a person, not another tank, checked in native frame.',
        '170':'Three distinct empty waiting tanks. Rear and middle lower bodies partly hidden by nearer tanks; floor electronics are not tanks.'}
    for ident,note in descriptions.items():
        assert ident not in decisions
        r = drafts[ident]
        attrs = [dict(box_index=i,truncated=ident=='169',
            occluded=ident in ('165','167','168') or (ident=='170' and i<2),load_state='unknown_not_annotated')
            for i in range(len(r['boxes_xyxy']))]
        decisions[ident] = dict(id=ident,image_sha256=r['sha256'],
            boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',
            load_state_reviewed=False,sequence_reviewed=False,instance_attributes=attrs,
            evidence=[r['source_frame'],r['frames_manifest'],f'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_{18 if ident in ("164","165","167") else 19}.jpg'],note=note)
    registry['reviews'] = list(decisions.values())
    r=drafts['166']
    registry.setdefault('excluded_roi_reviews',[]).append(dict(id='166',image_sha256=r['sha256'],reviewed_at=stamp,
        reviewer='assistant_visual_review',decision='exclude_whole_roi_not_an_empty_image',
        reason='Workers and conveyor obscure filling-tank extent. Whole ROI excluded rather than guessing a boundary.',
        evidence=[r['image'],r['source_frame'],r['frames_manifest']]))
    registry.setdefault('corrections',[]).append('Batch20:164/165/167/168/169/170 accepted after separate overlay review;166 excluded due to uncertain filling-tank extent. Prior annotations preserved.')
    save(OUT / 'object_review_decisions.json',registry)
    inv=read(BASE / 'archive_inventory.json')
    inspected={m['source']['member']:m['source_sha256'] for m in metas.values()}
    for r in inv['records']:
        if r['member'] in inspected: r.update(pixel_inspected=True,sha256=inspected[r['member']])
    assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test')
    save(BASE / 'archive_inventory.json',inv)
    reviews=read(OUT / 'screening_source_reviews.json')
    total=sum(r['sampled_frames_visually_reviewed'] for r in reviews)
    added=sum(len(m['samples']) for m in metas.values())
    state['last_completed'] += [
        f'Batch20 inspected {added} chronological sample presentations in7 windows on13Oct; {total} total across {len({r["source_sha256"] for r in reviews})} sources and {len(reviews)} windows. All extractions completed;25/28Oct untouched.',
        'Fifth complete cycle accepted:13Oct fresh gray filling/departure,15 entry09:27:04-10, scale28:10-31:45, storage32:41-58 with empty-fork withdrawal54-58. Two-second entry/storage source joins retained; no scalar clock offset or weight inferred.',
        'Two negatives added:empty gray internal replacement and unloaded jack return after storage. Totals5 complete,49 negatives,17 partials. Resolved arrival0927 queue record preserved in review_history without duplicate count.',
        'Seven native ROI candidates164-170 appended; six images/eight boxes approved,166 excluded. Totals171 candidates,117 accepted images,172 boxes,54 exclusions,zero drafts. Dataset remains unreleased.'
    ]
    state['priority_next'] = [
        'Batch20 complete.5 full cycles still all13Oct. Prioritize complete-cycle day diversity and actual same-load reentry/post-storage relocation negatives; easy negatives do not solve these missing cases.',
        '15Oct next station tank fills10:03:47-11:24 in next_origin_1001_cam11. Remaining relativePTS1200 onward of11 source095128-103726 unreviewed; inspect next fresh departure and paired15 route without repeating earlier gaps.',
        '13Oct0927 full cycle accepted. Next distinct gray load fills27:24-31:40;11 sources093135-093311 and093311-094655 plus15 sources after093339 can extend it.',
        '13Oct102139-102912 long15 source unreviewed;11 source gap10:00:12-25:11 may leave missing origin.',
    ] + [p for p in state['priority_next'] if p.startswith('Known gaps') or p.startswith('25/28') or p.startswith('Old21Oct')]
    state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    state['scripts'] += [s for s in ['work/append_tank_roi_batch_20261031_20.py','work/record_tank_sequence_batch_20261031_20.py'] if s not in state['scripts']]
    save(OUT / 'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_samples=added,total_presentations=total,
        additional_complete_cycles=1,additional_negative_sequences=2,training_started=False)))


if __name__=='__main__':
    main()
