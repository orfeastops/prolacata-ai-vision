"""Save visually reviewed13Oct09:36 entry, scale and storage evidence."""
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read, save, merge, evidence

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'outputs/tank_transfer_training_v1'
OUT = BASE / 'dataset_v1'
RUN = 'sequence_review_20261031_45'


def main():
    state = read(OUT/'continuation_state.json')
    if RUN in state.get('completed_curation_runs', []):
        print('Already recorded', RUN)
        return
    stamp = dt.datetime.now(dt.timezone.utc).isoformat()
    windows = {
        'fill': ('next_fill0931_cam11',24),
        'broad': ('next_route0933_cam11',83),
        'entry': ('route0935_cam15',27),
        'scale': ('scale0936_cam15',15),
        'dwell1': ('scale0937a_cam15',6),
        'dwell2': ('scale0937b_cam15',14),
        'dwell3': ('scale0939a_cam15',11),
        'off': ('scale0939b_cam15',12),
        'stage': ('storage0940a_cam15',8),
        'store': ('storage0940b_cam15',12),
        'after': ('storage0941_cam15',8),
        'dep': ('departure0935_cam11',41),
        'dense': ('entry0935_dense_cam15',30),
        'head': ('join0936_head_cam15',7),
        'tail': ('storage0941_tail_cam15',6),
        'release': ('storage0941_release_cam15',6),
    }
    paths = {k: OUT/'sequence_review/20261013'/w/'frames.json' for k,(w,_) in windows.items()}
    metas = {k: read(p) for k,p in paths.items()}
    # Selected clocks below were read visually from pixels. Unlisted samples
    # remain without clock annotations; neither filenames nor PTS supply clocks.
    clocks = {
        'fill': {0:'09:31:35',1:'09:31:52',8:'09:32:20',17:'09:32:56',18:'09:33:00',23:'09:33:20'},
        'broad': {0:'09:33:11',1:'09:33:34',2:'09:33:44',10:'09:35:04',13:'09:35:34',14:'09:35:44',
            15:'09:35:54',16:'09:36:04',17:'09:36:14',18:'09:36:24',21:'09:36:54',23:'09:37:14',
            39:'09:39:54',40:'09:40:04',41:'09:40:14',50:'09:41:44',51:'09:41:54',
            68:'09:44:44',69:'09:44:54',70:'09:45:04',71:'09:45:14',77:'09:46:14',82:'09:47:04'},
        'entry': {0:'09:34:51',1:'09:35:04',6:'09:35:19',9:'09:35:28',18:'09:35:55',
            19:'09:35:58',20:'09:36:01',21:'09:36:04',26:'09:36:19'},
        'scale': {0:'09:36:06',1:'09:36:27',4:'09:36:42',5:'09:36:47',6:'09:36:52',7:'09:36:57',
            8:'09:37:02',9:'09:37:07',10:'09:37:12',14:'09:37:32'},
        'dwell1': {0:'09:37:28',1:'09:37:40',2:'09:37:44',3:'09:37:48',4:'09:37:52',5:'09:37:56'},
        'dwell2': {0:'09:37:57',1:'09:38:02',6:'09:38:27',12:'09:38:57',13:'09:39:02'},
        'dwell3': {0:'09:39:03',1:'09:39:11',7:'09:39:29',8:'09:39:32',9:'09:39:34',10:'09:39:38'},
        'off': {0:'09:39:34',1:'09:39:49',2:'09:39:52',3:'09:39:55',4:'09:39:58',5:'09:40:01',
            6:'09:40:04',7:'09:40:07',8:'09:40:10',9:'09:40:13',10:'09:40:16',11:'09:40:19'},
        'stage': {0:'09:40:12',1:'09:40:23',2:'09:40:25',3:'09:40:27',4:'09:40:29',5:'09:40:31',6:'09:40:33',7:'09:40:35'},
        'store': {0:'09:40:43',1:'09:40:48',2:'09:40:50',3:'09:40:52',4:'09:40:54',5:'09:40:56',
            6:'09:40:58',7:'09:41:00',8:'09:41:02',9:'09:41:04',10:'09:41:06',11:'09:41:08'},
        'after': {0:'09:41:13',1:'09:41:16',2:'09:41:18',3:'09:41:20',4:'09:41:22',5:'09:41:24',6:'09:41:26',7:'09:41:28'},
        'dep': {0:'09:35:39',5:'09:35:44',8:'09:35:47',9:'09:35:48',10:'09:35:49',11:'09:35:50',
            12:'09:35:51',13:'09:35:52',14:'09:35:53',15:'09:35:54',16:'09:35:55',17:'09:35:56',
            18:'09:35:57',19:'09:35:58',20:'09:35:59',21:'09:36:00',22:'09:36:01',23:'09:36:02',
            24:'09:36:03',25:'09:36:04',26:'09:36:05',27:'09:36:06',30:'09:36:09',35:'09:36:14',40:'09:36:19'},
        'dense': {0:'09:35:51',1:'09:35:52',2:'09:35:53',3:'09:35:54',4:'09:35:55',5:'09:35:56',
            6:'09:35:57',7:'09:35:58',8:'09:35:59',9:'09:36:00',10:'09:36:01',11:'09:36:02',
            12:'09:36:03',13:'09:36:04',14:'09:36:05',15:'09:36:06',16:'09:36:07',17:'09:36:08',
            18:'09:36:09',19:'09:36:10',20:'09:36:11',21:'09:36:12',22:'09:36:13',23:'09:36:14',
            24:'09:36:15',25:'09:36:16',26:'09:36:17',27:'09:36:18',28:'09:36:19',29:'09:36:20'},
        'head': {0:'09:36:06',1:'09:36:23',2:'09:36:24',3:'09:36:25',4:'09:36:26',5:'09:36:27',6:'09:36:28'},
        'tail': {0:'09:41:04',1:'09:41:05',2:'09:41:06',3:'09:41:07',4:'09:41:08',5:'09:41:09'},
        'release': {0:'09:41:13',1:'09:41:15',2:'09:41:16',3:'09:41:17',4:'09:41:18',5:'09:41:19'},
    }
    notes = {
        'fill': 'All24 samples/four sheets inspected; native32:56 and two ROI overlays also viewed. Initial31:35 then31:52 jump retained. Fresh cheese placed into gray station body throughout. Two empty waiting bodies and separate scrap receptacle remain distinct. Prior31:40-to52 gap is not exact continuity or initial inventory proof.',
        'broad': 'All83 samples/14 sheets inspected. Initial33:11 is stale relative to preceding33:20; next33:34 gives14-second sampled join. Same station gray load fills through35:34, is covered35:44, departs35:54. Distinct empty replacement then receives new cheese. Through-door scale occupancy36:54-39:54, moving off40:04 and clear14. Later distinct station load fills through44:44, departs44:54, gone45:04; matching15 entry/storage for this second load is queued, not yet labeled complete. Clock47:04 extends beyond filename end; filenames not used as clocks.',
        'entry': 'All27 samples/five sheets inspected. Initial34:51 stale then35:04. Incoming covered gray load visible35:58-36:04 then staging through19. Base partly hidden by stationary foreground tanks. Separate visibly empty blue tank moves internally35:19-28; this is not an incoming production load. Packaging pallets and unrelated jack movement kept separate.',
        'scale': 'All15 samples/three sheets inspected. Initial36:06 stale, first coarse usable27. Same entry tank in staging27-42; moves right47-57, on scale37:02, operator attends07 and body stationary12-32. Dense preceding/head review reduces source gap to36:20-23. No scale digits read.',
        'dwell1': 'All6 samples/one sheet inspected. Initial37:28 stale relative to preceding32; next40 leaves eight-second sampled join. Same covered gray tank remains on platform; operator attends. No claim of continuous native video.',
        'dwell2': 'All14 samples/three sheets inspected.37:57-to39:02 same tank stationary on platform, following prior37:56. No new entry or measured weight.',
        'dwell3': 'All11 samples/two sheets inspected.39:03 follows prior02; next11 leaves initial jump. Same gray body on scale through38, operator by console29-38. Anchor sample9 clock34 retained as read, not regularized to35.',
        'off': 'All12 samples/two sheets inspected. Initial39:34 stale, next49 leaves11-second sampled dwell join. Same body on scale49-58, pulled40:01, off platform04-10, back in door-side staging13-19. No exit or second production entry.',
        'stage': 'All8 samples/two sheets inspected. Initial40:12 stale, first usable23 follows prior19 with four-second sampled gap. Same covered gray tank in staging through35; operator waits. Next source begins43: eight-second interval explicitly retained.',
        'store': 'All12 samples/two sheets plus native40:43/54 inspected. Same gray body at staging43 then moves left48-56, turns rearward58-41:00 and enters rear-row slot02-08. Native54 shows loose liner/white top and same operator route. Native43 verifies staging before move, not an unrelated load already in aisle. Final withdrawal refined by adjacent sources; no invented exact release.',
        'after': 'All8 samples/two sheets inspected.41:13 body parked in rear-row slot while empty jack already away. Empty forks clear16, continue across aisle18-28 while stored tank stays. Four-second source join from dense prior41:09 to13 bounds completion, not exact instant.',
        'dep': 'All41 one-second samples/seven sheets inspected, native35:52/56 and separate object overlays reviewed. Covered freshly filled body moves from station48-50, through room51-54, crosses threshold55-58, clear59. Distinct visibly empty replacement from waiting row51-57, empty through36:00. Fresh cheese placement into replacement starts01-02, outside negative interval.',
        'dense': 'All30 samples/five sheets inspected. Shared door approach35:55, covered top at56-57, gray body traverses threshold58-36:00 and turns left, staged02-20. Same operator, low gray body, liner and white cover with matching room11 route; no competing loaded crossing. Foreground stationary tanks partly hide base. Different camera clocks kept separate.',
        'head': 'All7 samples/two sheets inspected. Initial36:06 stale, next23 through28. Prior dense20-to23 three-second sampled join has same tank, staging position, operator and liner handling. No invented20-23 frames.',
        'tail': 'All6 samples/one sheet inspected.41:04-09 same gray tank being pushed into rear-row slot; jack remains engaged through09. Source ends before withdrawal. Next source13 shows parked body and bare jack away, retaining four-second completion interval.',
        'release': 'All6 samples/one sheet and native41:13 inspected. Parked tank remains fixed at13; operator and unloaded jack are already separated from it, bare forks obvious16-19. Completion bounded41:09-13 using previous source, not fabricated13-16 engagement.',
    }
    for k,m in metas.items():
        w,n = windows[k]
        assert len(m['samples']) == n
        assert m['source']['date']=='20261013' and m['source']['split']=='train'
        merge(OUT/'screening_source_reviews.json',[dict(
            review_id='20261013/'+w,reviewed_at=stamp,reviewer='assistant_visual_review',
            date='20261013',camera=m['source']['camera'],split='train',
            source_member=m['source']['member'],source_sha256=m['source_sha256'],
            frames_manifest=str(paths[k].relative_to(ROOT)),sampled_frames_visually_reviewed=n,
            reviewed_sheets=m['sheets'],observation=notes[k],accepted_complete_cycle=False,
            review_scope='All chronological sample presentations viewed; selected native contexts and separate overlays. Not exhaustive native-frame review.',
            clock_warning='Independent visible clocks, stale initial frames and source joins retained. No exact camera offset inferred.',
            visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],
                relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],visible_camera_clock=t,
                clock_read_uncertainty_seconds=1,image=m['samples'][i]['image'],usable_for_clock_alignment=False)
                for i,t in clocks[k].items()])],'review_id')
    def ev(k,a,b): return evidence(metas[k],a,b,paths[k])
    labels = read(OUT/'reviewed_sequence_labels.json')
    save(OUT/'review_history/sequence_labels_before_20261031_45.json',labels)
    shared = dict(date='20261013',split='train',reviewer='assistant_visual_review',reviewed_at=stamp,
        dataset_release_accepted=False,camera_clock_offset_seconds=None)
    cycle = dict(shared,sequence_id='20261013_gray_cycle0936',cycle_id='20261013_gray_cycle0936',
        camera_track_id={'11':'gray_station_departure0935','15':'gray_entry0936_scale_storage0941'},
        review_status='accepted_complete_cycle',entry_camera=15,entry_clock_interval=['09:35:56','09:36:02'],
        production_entry_count_target=1,clock_alignment_status='visual_correspondence_with_interval_uncertainty_retained',
        origin_content='Cheese placements observed in station body before cover; initial quantity unknown.',
        counting_rule='One fresh production entry finalized after scale visit and storage. Staging and storage motion do not add entries.',
        stages=[
            dict(stage='filling_observed',camera=11,visible_camera_clock_interval=['09:31:52','09:35:34'],
                initially_empty_observed=False,initial_contents='unknown_in_this_reviewed_window',
                content_evidence='Workers place white cheese blocks into same gray station tank; native32:56 confirms stacked cheese.14-second sampled source join33:20-to34 retains station body and workers.',
                evidence=[ev('fill',1,23),ev('broad',1,13)]),
            dict(stage='loaded_departure_11',camera=11,visible_camera_clock_interval=['09:35:39','09:35:59'],
                doorway_crossing_camera11_interval=['09:35:55','09:35:59'],clock_uncertainty_seconds=1,
                observation='Same covered fresh station load pulled across room and through doorway. Empty replacement is a different track.',
                evidence=[ev('dep',0,20)]),
            dict(stage='entry_15',camera=15,visible_camera_clock_interval=['09:35:56','09:36:02'],clock_uncertainty_seconds=1,
                observation='Same low gray covered tank, loose liner, operator and jack cross shared doorway and turn left into staging. Base partly occluded. No competing load at crossing.',
                source_join_review=[dict(preceding_clock='09:36:20',next_noninitial_clock='09:36:23',sampled_gap_seconds=3,
                    evidence='Same staging position, operator and liner handling on both sides of join; initial36:06 stale.')],
                evidence=[ev('dep',15,20),ev('dense',4,29),ev('head',1,6),ev('scale',1,4)]),
            dict(stage='scale_visit',camera=15,visible_camera_clock_interval=['09:36:47','09:40:10'],
                scale_approach_interval=['09:36:47','09:37:02'],scale_departure_clock_interval=['09:40:01','09:40:10'],
                numeric_weight_kg=None,measurement_success_verified=False,
                observation='Same entry tank moves right onto platform, dwells, then returns left to staging without leaving room15. Stale initial frames excluded from chronology;8/11-second sampled dwell joins retained.',
                evidence=[ev('scale',4,14),ev('dwell1',1,5),ev('dwell2',0,13),ev('dwell3',0,10),ev('off',1,11),ev('broad',21,41)]),
            dict(stage='storage_placement',camera=15,visible_camera_clock_interval=['09:40:13','09:41:28'],
                parking_approach_interval=['09:40:48','09:41:09'],unloaded_fork_withdrawal_interval=['09:41:09','09:41:13'],
                clock_uncertainty_seconds=4,
                observation='Same tank waits near door, moves left across aisle, turns into rear-row slot and remains as unloaded manual jack withdraws. Native43 confirms same pre-move staging; native41:13 confirms empty jack separated.',
                source_join_review=[dict(preceding_clock='09:40:19',next_noninitial_clock='09:40:23',sampled_gap_seconds=4),
                    dict(preceding_clock='09:40:35',next_noninitial_clock='09:40:43',sampled_gap_seconds=8,
                        evidence='Same tank remains at staging next to door with same operator; visible route subsequently proceeds to rear slot. No competing eligible tank.'),
                    dict(preceding_clock='09:41:09',next_noninitial_clock='09:41:13',sampled_gap_seconds=4,
                        evidence='Same rear-row position before and after; engaged jack at09, empty jack separated at13. Exact release unobserved.')],
                evidence=[ev('off',9,11),ev('stage',1,7),ev('store',0,11),ev('tail',0,5),ev('release',0,5),ev('after',0,7)])],
        limitations=['Sampled chronological review, not exhaustive native frames or measured kilograms.',
            'Small source joins retained:14 seconds in filling;3 seconds in staging after entry;8/11-second scale dwell joins;4/8-second post-scale staging joins;4-second final jack-release interval.',
            'Cross-camera correspondence follows the actual door route; neither timestamps nor similar tank color alone establishes identity.',
            'Separate empty replacement and subsequent44:54 departure are different production tracks. No second entry assigned to storage or unloaded return.'])
    negatives = [
        dict(shared,sequence_id='20261013_empty_gray_replacement0935',cycle_id=None,review_status='accepted_negative_sequence',
            camera=11,production_entry_count_target=0,negative_class='empty_tank_internal_reposition',tracked_tank_count=1,
            direction='room11_waiting_row_to_filling_station',visible_camera_clock_interval=['09:35:51','09:36:00'],
            observation='One empty lined gray tank pulled from waiting row and slid into station. Empty bottom visible; new cheese begins36:01-02 outside negative interval.',
            label_scope='Only empty replacement track; outgoing covered production load and scrap receptacle excluded.',evidence=[ev('dep',12,21)]),
        dict(shared,sequence_id='20261013_unloaded_jack_after_storage0941',cycle_id=None,review_status='accepted_negative_sequence',
            camera=15,production_entry_count_target=0,negative_class='pallet_jack_without_tank',tracked_tank_count=0,
            visible_camera_clock_interval=['09:41:13','09:41:28'],
            observation='Empty jack already separated from newly parked load at13; bare forks visible16-28 while tank remains in rear row.',
            label_scope='Only unloaded manual jack after storage; no whole-room negative label.',evidence=[ev('release',0,5),ev('after',0,7)])]
    merge(OUT/'reviewed_sequence_labels.json',[cycle,*negatives],'sequence_id')
    qp = OUT/'sequence_followup_queue.json'
    save(OUT/'review_history/followup_queue_before_20261031_45.json',read(qp))
    merge(qp,[dict(candidate_id='20261013_next_station_load_after0927',date='20261013',split='train',reviewed_at=stamp,
        status='resolved_in_reviewed_complete_cycle',resolved_sequence_id=cycle['sequence_id'],cycle_id=None,production_entry_count_target=None,
        observation='Reviewed continuation fills through35:34, departs35:55-59, enters15 at35:56-36:02, scale and storage through41:13.',
        next_action='Resolved in sole accepted cycle record. Do not count this queue entry separately.',evidence=[ev('dep',15,20),ev('dense',5,11),ev('release',0,2)]),
        dict(candidate_id='20261013_next_station_load_after0936',date='20261013',split='train',reviewed_at=stamp,
        status='candidate_departure0944_needs_room15_route_review',cycle_id=None,production_entry_count_target=None,
        observation='Distinct empty replacement35:51-36:00 then fresh cheese01-02, filling through44:44, departure44:54 and gone45:04. Later platform occupant46:14-47:04 not yet cross-camera linked.',
        next_action='Review13Oct15 sources around09:44-09:50 and dense11 relativePTS680-715 if needed. Do not repeat0936 route or infer15 entry from11 alone.',
        evidence=[ev('dep',21,40),ev('broad',18,82)])],'candidate_id')
    registry = read(OUT/'object_review_decisions.json')
    save(OUT/'review_history/object_decisions_before_20261031_45.json',registry)
    decisions = {r['id']:r for r in registry['reviews']}
    drafts = {r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
    notes_by_id = {'275':'Covered outgoing gray body in room11.',
        '276':'Distinct empty replacement, mild motion blur; four visible boundaries.',
        '277':'Outgoing gray body at door; right edge partly occluded by post.',
        '278':'Isolated empty blue body in room15 aisle, not a production entry label.',
        '279':'Two distinct waiting gray tanks; rear body partly hidden by front tank.',
        '280':'Separate scrap receptacle; worker/conveyor occlusion and bottom crop truncation.'}
    for ident,note in notes_by_id.items():
        assert ident not in decisions
        r=drafts[ident]
        assert r['split']=='train'
        attrs=[dict(box_index=i,truncated=ident=='280',occluded=ident in ('277','280') or (ident=='279' and i==0),
                    load_state='unknown_not_annotated') for i in range(len(r['boxes_xyxy']))]
        decisions[ident]=dict(id=ident,image_sha256=r['sha256'],
            boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',
            load_state_reviewed=False,sequence_reviewed=False,instance_attributes=attrs,
            evidence=[r['source_frame'],r['frames_manifest'],'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_36.jpg'],
            note=note+' Native context, candidate crop and separate overlay inspected; ROI detection only.')
    registry['reviews']=list(decisions.values())
    registry.setdefault('corrections',[]).append('Batch45:275-280 accepted, seven boxes, after native context and separate overlay inspection. Existing reviews preserved.')
    save(OUT/'object_review_decisions.json',registry)
    inv=read(BASE/'archive_inventory.json')
    inspected={m['source']['member']:m['source_sha256'] for m in metas.values()}
    for r in inv['records']:
        if r['member'] in inspected:r.update(pixel_inspected=True,sha256=inspected[r['member']])
    assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test')
    save(BASE/'archive_inventory.json',inv)
    reviews=read(OUT/'screening_source_reviews.json')
    total=sum(r['sampled_frames_visually_reviewed'] for r in reviews)
    added=sum(n for _,n in windows.values())
    state['last_completed'] += [
        f'Batch45 inspected{added} chronological presentations in16 windows on13Oct;{total} total across{len({r["source_sha256"] for r in reviews})} sources/{len(reviews)} windows. All extraction finished;25/28Oct unseen.',
        'Sixth complete cycle accepted:13Oct fresh gray load, entry15 at09:35:56-09:36:02, scale36:47-40:10, storage and jack withdrawal41:09-13. Source gaps and independent clocks retained; no kilograms or initial quantity inferred.',
        'Two scoped negatives added: empty local replacement before new filling, and unloaded jack after storage.98 negatives total.41 partials unchanged.',
        'Six native ROI images/seven boxes accepted after separate overlays.281 candidates,222 accepted images,288 boxes,59 excluded,zero drafts. Dataset remains unreleased and no training started.',
    ]
    state['priority_next'] = [
        'Batch45 complete:13Oct0936 entry resolved through scale and41:09-13 storage. Do not repeat16 reviewed windows. All6 complete cycles still13Oct; day diversity remains required.',
        'Queued13Oct next fresh load departs44:54 (11 broad source already reviewed), counterpart15 around09:44-50 still needs route review. Target additional complete cycles, not more easy negatives.',
        'Prioritise additional complete cycles on15Oct or other paired training days with actual origin/entry/storage coverage. Preserve known missing-source intervals; no identity from same color alone.',
    ]+[p for p in state['priority_next'] if p.startswith('Known gaps') or p.startswith('25/28') or p.startswith('Old21Oct')]
    state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    state['scripts'] += ['work/append_tank_roi_batch_20261031_45.py','work/record_tank_sequence_batch_20261031_45.py']
    save(OUT/'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_samples=added,total_presentations=total,
        additional_complete_cycles=1,additional_negative_sequences=2,training_started=False)))


if __name__=='__main__': main()
