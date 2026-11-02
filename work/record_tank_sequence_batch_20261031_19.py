"""Persist visually reviewed 13/15Oct tank sequences; no model training."""
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read, save, merge, evidence

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'outputs/tank_transfer_training_v1'
OUT = BASE / 'dataset_v1'
RUN = 'sequence_review_20261031_19'


def main():
    state = read(OUT / 'continuation_state.json')
    if RUN in state.get('completed_curation_runs', []):
        print('Already recorded', RUN)
        return
    stamp = dt.datetime.now(dt.timezone.utc).isoformat()
    windows = {
        'origin15': ('20261015', 'next_origin_1001_cam11', 75),
        'store15': ('20261015', 'next_context_1008_cam15', 8),
        'after15a': ('20261015', 'next_context_1009a_cam15', 8),
        'after15b': ('20261015', 'next_context_1009b_cam15', 8),
        'origin13': ('20261013', 'next_origin_0915_cam11', 57),
        'route13': ('20261013', 'next_route_0916_cam15', 63),
        'scale13': ('20261013', 'next_scale_0922_cam15', 12),
        'store13': ('20261013', 'next_storage_0923_cam15', 62),
        'entry13': ('20261013', 'next_entry_boundary_0919_cam15', 20),
        'depart13': ('20261013', 'next_departure_boundary_0919_cam11', 28),
        'dense13': ('20261013', 'next_storage_boundary_0925_cam15', 46),
    }
    paths = {k: OUT / 'sequence_review' / d / w / 'frames.json' for k, (d,w,n) in windows.items()}
    metas = {k: read(p) for k,p in paths.items()}
    for k,m in metas.items():
        assert len(m['samples']) == windows[k][2]
        assert m['source']['date'] == windows[k][0] and m['source']['split'] == 'train'
    # All anchors read from displayed camera-clock pixels, not calculated from filenames/PTS.
    clocks = {
        'origin15': {0:'10:01:31',7:'10:02:27',8:'10:02:35',9:'10:02:43',12:'10:03:07',13:'10:03:15',14:'10:03:23',15:'10:03:31',16:'10:03:39',17:'10:03:47',23:'10:04:35',24:'10:04:43',26:'10:04:59',49:'10:08:03',50:'10:08:12',51:'10:08:19',61:'10:09:40',62:'10:09:48',63:'10:09:56',74:'10:11:24'},
        'store15': {0:'10:08:38',1:'10:08:59',2:'10:09:01',3:'10:09:03',4:'10:09:05',5:'10:09:07',6:'10:09:09',7:'10:09:11'},
        'after15a': {0:'10:09:03',1:'10:09:18',2:'10:09:20',3:'10:09:22',4:'10:09:24',5:'10:09:26',6:'10:09:28',7:'10:09:30'},
        'after15b': {0:'10:09:22',1:'10:09:35',2:'10:09:37',3:'10:09:39',4:'10:09:41',5:'10:09:43',6:'10:09:45',7:'10:09:47'},
        'origin13': {0:'09:15:12',6:'09:16:00',14:'09:17:04',21:'09:18:00',28:'09:18:56',29:'09:19:04',30:'09:19:13',31:'09:19:21',32:'09:19:29',33:'09:19:37',34:'09:19:45',39:'09:20:25',40:'09:20:33',41:'09:20:41',42:'09:20:49',56:'09:22:41'},
        'route13': {0:'09:16:19',1:'09:16:26',6:'09:16:56',17:'09:18:02',27:'09:19:02',28:'09:19:09',30:'09:19:21',31:'09:19:27',32:'09:19:33',39:'09:20:15',40:'09:20:21',41:'09:20:27',42:'09:20:33',43:'09:20:39',44:'09:20:45',45:'09:20:51',54:'09:21:45',60:'09:22:21',62:'09:22:33'},
        'scale13': {0:'09:22:23',1:'09:22:41',2:'09:22:45',3:'09:22:48',4:'09:22:50',5:'09:22:51',6:'09:22:54',7:'09:22:55',8:'09:22:58',9:'09:23:00',10:'09:23:02',11:'09:23:04'},
        'store13': {0:'09:23:02',1:'09:23:08',2:'09:23:12',3:'09:23:15',4:'09:23:19',5:'09:23:24',9:'09:23:40',10:'09:23:44',11:'09:23:48',12:'09:23:52',13:'09:23:56',14:'09:24:00',15:'09:24:04',16:'09:24:08',17:'09:24:12',24:'09:24:40',25:'09:24:44',26:'09:24:48',27:'09:24:52',28:'09:24:56',29:'09:25:00',30:'09:25:03',31:'09:25:08',32:'09:25:12',33:'09:25:16',34:'09:25:20',35:'09:25:24',36:'09:25:28',39:'09:25:39',42:'09:25:52',43:'09:25:55',44:'09:26:00',60:'09:27:04',61:'09:27:08'},
        'entry13': {0:'09:19:19',3:'09:19:22',4:'09:19:23',5:'09:19:24',6:'09:19:25',7:'09:19:26',8:'09:19:27',9:'09:19:28',10:'09:19:29',11:'09:19:30',12:'09:19:31',14:'09:19:33',19:'09:19:38'},
        'depart13': {0:'09:19:11',6:'09:19:17',8:'09:19:19',10:'09:19:21',12:'09:19:23',13:'09:19:24',14:'09:19:25',15:'09:19:26',16:'09:19:27',17:'09:19:28',18:'09:19:29',19:'09:19:30',20:'09:19:31',27:'09:19:38'},
        'dense13': {0:'09:24:44',1:'09:24:45',4:'09:24:47',5:'09:24:48',6:'09:24:49',7:'09:24:51',8:'09:24:52',10:'09:24:54',12:'09:24:56',13:'09:24:57',15:'09:24:58',16:'09:24:59',17:'09:25:00',18:'09:25:01',20:'09:25:03',22:'09:25:05',24:'09:25:08',26:'09:25:10',28:'09:25:11',29:'09:25:13',30:'09:25:14',32:'09:25:16',35:'09:25:18',36:'09:25:19',37:'09:25:21',38:'09:25:22',39:'09:25:23',41:'09:25:24',42:'09:25:25',44:'09:25:28',45:'09:25:29'},
    }
    notes = {
        'origin15': 'Gray station tank continues fresh filling10:01:31-02:27, covered02:35. Operator gets jack03:15, engages03:23, pulls03:31, tank gone03:39; precise door crossing falls between sparse samples. Empty gray return02:43 is the first return already labelled in batch18, not a new negative. Beige return is inside11 by03:07; further gray present03:15 and moved to station03:31-39, fresh filling from03:47. Through doorway scale is clear04:35; gray appears04:43, settled04:59 and stays through08:03; offscale08:12, platform clear08:19. Empty jack returns09:40-48 and engages next station tank09:56; no next loaded departure through11:24.',
        'store15': 'Initial08:38 stale. First usable08:59 gray tank already off scale in aisle; moved left and pushed into front/left end of storage group09:03-11. No entry, scale departure or final fork release here. Same-load identity to fresh03-minute origin not established across missing entry and40-second route gap from11 platform-clear08:19.',
        'after15a': 'Initial09:03 stale. First usable09:18 tank already parked and unloaded forks already withdrawn, seven seconds after prior last storage approach09:11. Empty jack heads back toward blue bins; stored tank remains. Retain final-release gap.',
        'after15b': 'Initial09:22 stale. Empty jack and operator return through shared doorway09:35-39; person walks near scale wall39-45 and back toward door47. No tank accompanies this return. Stored gray tank unchanged.',
        'origin13': 'Same gray station tank receives fresh cheese15:12-19:04 then cover by19:13. Operator pulls19:21; door passage19:29; gone19:37. A different visibly empty gray tank moves from local waiting row to station19:29-37 and starts filling19:45. Scale through door clear20:25; gray load approaches20:33-41, settled20:49 and remains through22:41. Fixed scrap tank is separate.',
        'route13': 'One low gray tank with white top arrives through door19:21-33 and stays in staging immediately left of doorway. Operator handles liner/cover. Same tank moves to scale20:21-45 and stays through22:33. Foreground cylindrical metal containers and existing tank rows are not new tank entries. Exact crossing refined in separate dense window; initial16:19 not used for alignment.',
        'scale13': 'Initial22:23 stale and earlier than preceding reviewed source22:33. First usable22:41 has same low gray tank still on same scale, operator alongside; dwell through23:04. Previous camera11 context also reaches22:41 on occupied platform. Eight-second sampled join retained, not claimed full native continuity.',
        'store13': 'Initial23:02 stale; next usable23:08 continues scale dwell, four-second sampled join from23:04. Operator engages jack23:44-56; load leaves scale24:00-08, stages by door without crossing24:12-44, then moves left24:48-25:08. Parked at left end of rear row25:12-20; forks clearly withdrawn25:24, tank stays through27:08. Empty jack returns through door25:39-55. Another load appears at doorway27:04-08, outside accepted cycle scope; origin not yet reviewed.',
        'entry13': 'Low gray tank approaches19:22-23, crosses threshold19:24-29, then turns left into staging19:30-33. Same short/low gray geometry, white top, liner and operator/jack route as camera11 departure. Foreground blue tanks occlude base, so entry interval retained rather than an exact instant. Separate empty gray replacement visible farther inside11 at19:27.',
        'depart13': 'Fresh filled low gray tank pulled from station19:17-23, first threshold intersection19:25, last body at threshold19:29, gone by19:31. Separate empty gray tank pushed from local row toward filling station19:25-31. Match to15 by shared passage, geometry and continuous route, not timestamps alone.',
        'dense13': 'Same low gray load moves from door staging24:45-52, turns in open aisle24:56-25:00 and proceeds left25:01-10. Parked alongside rear row25:11-21. Unloaded forks emerge25:22-23, fully clear25:24-25 and retreat25:28-29; tank stationary. No second production increment for staging or storage.',
    }
    for k,m in metas.items():
        initial = m['requested_window']['start'] == 0
        merge(OUT / 'screening_source_reviews.json', [dict(
            review_id=windows[k][0]+'/'+windows[k][1], reviewed_at=stamp, reviewer='assistant_visual_review',
            date=windows[k][0], camera=m['source']['camera'], split='train', source_member=m['source']['member'],
            source_sha256=m['source_sha256'], frames_manifest=str(paths[k].relative_to(ROOT)),
            sampled_frames_visually_reviewed=len(m['samples']), reviewed_sheets=m['sheets'],
            review_scope='All chronological contact-sheet samples inspected; selected native frames and separate box overlays inspected. Sample presentations are not exhaustive native-frame viewing.',
            observation=notes[k], accepted_complete_cycle=False,
            clock_warning='Camera-clock intervals retained. Source-initial stale images excluded; filenames/PTS do not establish synchronization.',
            visible_clock_anchors=[dict(sample_index=i, source_pts_seconds=m['samples'][i]['source_pts_seconds'],
                relative_pts_seconds=m['samples'][i]['relative_pts_seconds'], visible_camera_clock=t,
                clock_read_uncertainty_seconds=1, image=m['samples'][i]['image'],
                usable_for_clock_alignment=not(initial and i==0)) for i,t in clocks[k].items()])], 'review_id')

    def ev(k,a,b): return evidence(metas[k],a,b,paths[k])
    oldpath = OUT / 'sequence_review/20261015/early_storage_1002_cam15/frames.json'
    oldmeta = read(oldpath)
    old_beige_return = evidence(oldmeta,12,16,oldpath)
    shared = dict(split='train',reviewer='assistant_visual_review',reviewed_at=stamp,dataset_release_accepted=False)
    def neg(ident,day,cam,cls,times,proof,note,scope,tanks):
        return dict(shared, sequence_id=ident, date=day, camera=cam, camera_track_id=ident, cycle_id=None,
            review_status='accepted_negative_sequence',production_entry_count_target=0,negative_class=cls,
            tracked_tank_count=tanks,visible_camera_clock_interval=times,clock_uncertainty_seconds=2,
            evidence=proof,observation=note,label_scope=scope)
    additions = [
        neg('20261013_empty_gray_replacement_0919','20261013',11,'empty_tank_internal_reposition',['09:19:25','09:19:37'],
            [ev('depart13',14,22),ev('origin13',31,33)], 'One visibly empty gray tank moved from local waiting row to station.',
            'This empty replacement only; simultaneous fresh filled gray departure is a separate positive cycle.',1),
        neg('20261013_unloaded_jack_after_storage_0925','20261013',15,'pallet_jack_without_tank',['09:25:24','09:25:55'],
            [ev('dense13',41,45),ev('store13',35,43)],'Unloaded forks clear newly parked tank then jack returns through door; tank remains stored.',
            'Only unloaded jack after completed storage. Later27-minute arriving load is excluded.',0),
        neg('20261015_unloaded_jack_after_storage_1009','20261015',15,'pallet_jack_without_tank',['10:09:18','10:09:39'],
            [ev('after15a',1,7),ev('after15b',1,3),ev('origin15',61,62)],'Empty jack travels from storage area back through doorway; no tank accompanies it.',
            'Unloaded return only. Seven-second gap before09:18 prevents accepting preceding exact fork release.',0),
        neg('20261015_empty_beige_return_1002','20261015',15,'empty_crossing',['10:02:53','10:03:01'],
            [old_beige_return], 'Visibly empty beige tank is moved from left waiting group through shared doorway into11.',
            'Only beige return. First gray return is already labelled in batch18; further gray movement is not a second count here.',1),
    ]
    additions.append(dict(shared,date='20261015',sequence_id='20261015_fresh_gray_departure_partial_1003',
        review_status='reviewed_partial_sequence',cycle_id=None,production_entry_count_target=None,
        camera_track_id={'11':'gray_station_1001_1003','15':'unlinked_gray_scale_storage_1008_1009'},
        partial_reason='Fresh filling and station departure observed; direct15 entry missing. Later scale-to-storage identity unresolved across40-second route and7-second final-release gaps.',
        stages=[
            dict(stage='filling_observed',visible_camera_clock_interval=['10:01:31','10:02:27'],clock_uncertainty_seconds=8,
                content_evidence='Direct fresh cheese placement before cover02:35; earlier filling already visible in batch18. Initial contents unknown.',evidence=[ev('origin15',0,8)]),
            dict(stage='loaded_departure_11',visible_camera_clock_interval=['10:03:23','10:03:39'],clock_uncertainty_seconds=8,
                exact_door_crossing=None,observation='Pulled from station03:31; gone03:39. Crossing between sparse samples, not assigned an exact time.',evidence=[ev('origin15',14,16)])],
        unlinked_followup=dict(status='missing_entry_and_storage_identity_gap',direct_entry15=None,numeric_weight_kg=None,
            observation='Gray scale appearance04:43, settled04:59; off08:12, platform clear08:19 in11.15 first usable08:59 already offscale; storage approach09:03-11, parked by09:18. Do not infer origin identity across gaps.',
            scale_departure_camera11_interval=['10:08:03','10:08:19'],storage_approach_camera15_interval=['10:08:59','10:09:11'],
            parked_by_camera15='10:09:18',evidence=[ev('origin15',23,51),ev('store15',1,7),ev('after15a',1,7),ev('after15b',1,7)]),
        limitations=['No complete-cycle target or entry total assigned.','No clock offset inferred.','Next station tank fills03:47-11:24; do not confuse it with departing load.']))
    additions.append(dict(shared,date='20261013',sequence_id='20261013_gray_filling_to_storage_0919',
        review_status='accepted_complete_cycle',cycle_id='20261013_gray_0919',
        camera_track_id={'11':'gray_station_0915_0919','15':'gray_entry_scale_storage_0919_0925'},
        cross_camera_identity='assistant_visual_correspondence_reviewed_with_occlusion',
        clock_alignment='shared_crossing_visually_checked_timestamp_uncertainty_retained',camera_clock_offset_seconds=None,
        entry_camera=15,entry_clock_interval=['09:19:24','09:19:29'],production_entry_count_target=1,
        origin_content='Fresh cheese placement observed before covering; a white cover alone is not load evidence.',
        counting_rule='One room15 entry, finalized after scale visit and storage. Staging, scale movement and parking do not increment.',
        stages=[
            dict(stage='filling_observed',visible_camera_clock_interval=['09:15:12','09:19:04'],clock_uncertainty_seconds=8,
                content_evidence='Workers place cheese into same low gray station tank, covered by19:13.',evidence=[ev('origin13',0,30)]),
            dict(stage='loaded_departure_11',visible_camera_clock_interval=['09:19:17','09:19:31'],
                doorway_crossing_camera11_interval=['09:19:25','09:19:30'],clock_uncertainty_seconds=1,
                evidence=[ev('origin13',29,33),ev('depart13',6,20)]),
            dict(stage='entry_15',visible_camera_clock_interval=['09:19:24','09:19:29'],clock_uncertainty_seconds=2,
                observation='Same low gray body, white top, loose liner, jack and operator cross shared doorway then turn left. Base partly obscured by fixed bins; interval retained.',
                evidence=[ev('entry13',3,14),ev('depart13',12,20)]),
            dict(stage='scale_visit',visible_camera_clock_interval=['09:20:21','09:24:08'],
                scale_approach_interval=['09:20:21','09:20:45'],scale_departure_clock_interval=['09:24:00','09:24:08'],
                clock_uncertainty_seconds=6,numeric_weight_kg=None,measurement_success_verified=False,
                source_join_review=[
                    dict(preceding_clock='09:22:33',next_noninitial_clock='09:22:41',sampled_gap_seconds=8,
                        evidence='Tank remains in same scale position, operator alongside;11 also shows occupied platform through22:41. Initial22:23 stale.'),
                    dict(preceding_clock='09:23:04',next_noninitial_clock='09:23:08',sampled_gap_seconds=4,
                        evidence='Same scale load and position before and after join. Initial23:02 stale.')],
                evidence=[ev('route13',32,62),ev('origin13',39,56),ev('scale13',1,11),ev('store13',1,16)]),
            dict(stage='storage_placement',visible_camera_clock_interval=['09:24:44','09:25:25'],
                parking_approach_interval=['09:25:01','09:25:11'],unloaded_fork_withdrawal_interval=['09:25:22','09:25:25'],
                clock_uncertainty_seconds=2,observation='Same tank leaves post-scale staging, turns in aisle, moves left and parks by rear row. Empty forks withdrawn; tank remains through27:08.',
                evidence=[ev('store13',14,61),ev('dense13',0,45)])],
        limitations=['Sampled visual review, not all native frames.','Scale dwell joins retain8-second and4-second sampling gaps; no scalar clock offset asserted.',
            'No numeric weight, initial tank inventory or block count inferred.','Following27-minute doorway load is outside this cycle.']))
    merge(OUT / 'reviewed_sequence_labels.json', additions, 'sequence_id')
    # Extend the earlier first-gray-return evidence without counting it again.
    labels = read(OUT / 'reviewed_sequence_labels.json')
    prior = next(r for r in labels if r['sequence_id']=='20261015_empty_gray_return_1002')
    hist = OUT / 'review_history/first_gray_return1002_before_20261031_19.json'
    if not hist.exists(): save(hist,copy.deepcopy(prior))
    prior['evidence'].append(ev('origin15',8,10))
    prior['camera11_followup'] = 'First gray return appears inside11 at10:02:43. Later beige and second gray arrivals are different tracks.'
    prior['prior_annotation'] = str(hist.relative_to(ROOT))
    save(OUT / 'reviewed_sequence_labels.json', labels)
    merge(OUT / 'sequence_followup_queue.json', [dict(
        candidate_id='20261015_gray_1003_entry_storage_gap',date='20261015',split='train',cycle_id=None,
        production_entry_count_target=None,status='partial_entry_and_storage_identity_gap',reviewed_at=stamp,
        observation='Direct15 entry absent.11 platform clear08:19 to15 first aisle08:59:40 seconds. Final storage approach09:11 toalreadyparked09:18:7 seconds.',
        next_action='Do not repeat these unchanged source windows. New media needed for entry and trajectory gaps. Next gray station load continues filling through11:24.',
        evidence=[ev('origin15',14,51),ev('store15',1,7),ev('after15a',1,7)]),dict(
        candidate_id='20261013_next_arrival_0927',date='20261013',split='train',cycle_id=None,
        production_entry_count_target=None,status='candidate_origin_not_reviewed',reviewed_at=stamp,
        observation='Another low gray load appears in doorway09:27:04-08 after previous load was stored.',
        next_action='Inspect paired11 source after09:22:41 and15 next source092652-093249; do not reuse previous cycle identity.',
        evidence=[ev('store13',60,61)])], 'candidate_id')
    save(OUT / 'gap_search_20261031_19.json',dict(reviewed_at=stamp,
        findings=['15Oct direct15 entry after03-minute fresh departure not available in reviewed source; previous15 last03:07 and next first usable08:59.',
            '15Oct11 scale clear08:19 to15 aisle08:59 leaves40-second route gap; storage approach09:11 toparked09:18 leaves7-second release gap.',
            '13Oct scale dwell joins22:33-41 and23:04-08 keep matching load/position. Initial22:23 and23:02 stale frames excluded from alignment.'],
        action='15Oct remains partial.13Oct full cycle accepted with explicit interval and sampling limitations.'))

    registry = read(OUT / 'object_review_decisions.json')
    hist = OUT / 'review_history/object_decisions_before_20261031_19.json'
    if not hist.exists(): save(hist,registry)
    decisions = {r['id']:r for r in registry['reviews']}
    drafts = {r['id']:r for r in read(BASE / 'detector_v1/visual_annotation_draft.json')['records']}
    descriptions = {'158':'Fresh covered low gray departure, full tank body.', '159':'Visibly empty low gray internal replacement.',
        '161':'Gray station tank during fresh cheese filling; worker occlusion and crop truncation retained.',
        '163':'Separate beige scrap receptacle; worker/conveyor occlusion and crop edge retained.'}
    for ident,note in descriptions.items():
        assert ident not in decisions
        r = drafts[ident]
        decisions[ident] = dict(id=ident,image_sha256=r['sha256'],
            boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',
            load_state_reviewed=False,sequence_reviewed=False,
            instance_attributes=[dict(box_index=0,truncated=ident in ('161','163'),occluded=ident in ('159','161','163'),load_state='unknown_not_annotated')],
            evidence=[r['source_frame'],r['frames_manifest'],f'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_{17 if ident=="158" else 18}.jpg'],note=note)
    registry['reviews'] = list(decisions.values())
    for ident in ('160','162'):
        r=drafts[ident]
        registry.setdefault('excluded_roi_reviews',[]).append(dict(id=ident,image_sha256=r['sha256'],reviewed_at=stamp,
            reviewer='assistant_visual_review',decision='exclude_whole_roi_not_an_empty_image',
            reason='Main tank visible; cropped background tank fragments have ambiguous instance extent. Entire ROI excluded.',
            evidence=[r['image'],r['source_frame'],r['frames_manifest']]))
    registry.setdefault('corrections',[]).append('Batch19:158/159/161/163 accepted after separate overlay review;160/162 excluded as whole uncertain ROIs. Prior accepted annotations preserved.')
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
        f'Batch19 inspected{added} chronological sample presentations in11 windows on13/15Oct; {total} total across{len({r["source_sha256"] for r in reviews})} sources and{len(reviews)} windows. All extractions completed;25/28Oct untouched.',
        'Fourth complete cycle accepted:13Oct fresh gray filling/departure,15 entry09:19:24-29, scale20:21-24:08, storage25:11-25 with empty-fork withdrawal22-25. Scale dwell source joins8/4seconds retained; no scalar clock offset or weight inferred.',
        '15Oct fresh gray departure10:03 retained partial:missing15 entry,40-second scale-to-aisle and7-second final-release gaps. Four negatives added(empty replacement13Oct,empty jack returns13/15Oct,beige empty return15Oct). Earlier first gray return enriched without duplicate counting. Totals4 complete,47 negatives,17 partials.',
        'Six native ROI candidates158-163 appended; four images/four boxes separately approved,160/162 excluded. Totals164 candidates,111 accepted images,164 boxes,53 exclusions,zero drafts. Dataset remains unreleased.'
    ]
    state['priority_next'] = [
        'Batch19 all11 windows recorded.13Oct0919 cycle accepted; next arrival09:27:04-08 queued. Inspect paired11 after09:22:41 and15 source092652-093249 to follow next distinct cycle.',
        '15Oct1003 gray partial cannot bridge absent direct entry or08:19-59 route/09:11-18 release with inspected sources. Do not repeat. Next station tank fills03:47-11:24; remaining11 relativePTS1200 onward unreviewed.',
        '4 complete cycles still all13Oct. Need cycle day diversity and real same-load reentry/post-storage relocation negatives; easy negatives do not solve this.',
        '13Oct102139-102912 long15 source remains unreviewed and may retain another full route.',
    ] + [p for p in state['priority_next'] if p.startswith('Known gaps') or p.startswith('25/28') or p.startswith('Old21Oct')]
    state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    state['scripts'] += [s for s in ['work/append_tank_roi_batch_20261031_19.py','work/record_tank_sequence_batch_20261031_19.py'] if s not in state['scripts']]
    save(OUT / 'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_samples=added,total_presentations=total,additional_complete_cycles=1,
        additional_partial_sequences=1,additional_negative_sequences=4,training_started=False)))


if __name__ == '__main__':
    main()
