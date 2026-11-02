"""Persist reviewed 15Oct partial transfers and track-scoped negatives."""
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read, save, merge, evidence

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'outputs/tank_transfer_training_v1'
OUT = BASE / 'dataset_v1'
RUN = 'sequence_review_20261031_21'


def main():
    state = read(OUT / 'continuation_state.json')
    if RUN in state.get('completed_curation_runs', []):
        print('Already recorded', RUN)
        return
    stamp = dt.datetime.now(dt.timezone.utc).isoformat()
    windows = {
        'origin': ('next_origin_1011_cam11', 75),
        'staging': ('next_route_1012_cam15', 16),
        'scale': ('next_route_1013_cam15', 17),
        'dwell': ('next_scale_1014_cam15', 8),
        'storage': ('next_storage_1016_cam15', 12),
        'release': ('storage_release_1017_cam15', 16),
        'beige': ('beige_entry_1020_cam15', 22),
        'jack': ('empty_jack_1017_cam15', 25),
        'before': ('before_beige_1019_cam15', 14),
    }
    paths = {k: OUT / 'sequence_review/20261015' / w / 'frames.json' for k,(w,n) in windows.items()}
    metas = {k: read(p) for k,p in paths.items()}
    for k,m in metas.items():
        assert m['source']['date']=='20261015' and m['source']['split']=='train'
        assert len(m['samples'])==windows[k][1]
    # Direct readings from displayed camera clocks, not calculated from PTS.
    clocks = {
        'origin': {0:'10:11:31',1:'10:11:39',2:'10:11:47',3:'10:11:55',4:'10:12:03',9:'10:12:43',10:'10:12:51',13:'10:13:15',33:'10:15:55',34:'10:16:03',35:'10:16:11',45:'10:17:31',49:'10:18:03',50:'10:18:11',51:'10:18:19',65:'10:20:11',66:'10:20:19',67:'10:20:27',68:'10:20:35',69:'10:20:43',74:'10:21:23'},
        'staging': {0:'10:12:00',1:'10:12:09',4:'10:12:15',6:'10:12:19',8:'10:12:23',9:'10:12:25',15:'10:12:37'},
        'scale': {0:'10:12:52',1:'10:12:56',2:'10:12:58',3:'10:13:00',7:'10:13:09',10:'10:13:14',16:'10:13:26'},
        'dwell': {0:'10:14:41',1:'10:14:48',2:'10:14:49',3:'10:14:51',4:'10:14:53',5:'10:14:56',6:'10:14:57',7:'10:14:59'},
        'storage': {0:'10:16:32',1:'10:16:50',2:'10:16:52',4:'10:16:56',6:'10:17:00',7:'10:17:02',11:'10:17:10'},
        'release': {0:'10:16:53',1:'10:17:12',2:'10:17:13',3:'10:17:14',6:'10:17:17',9:'10:17:20',10:'10:17:21',15:'10:17:26'},
        'beige': {0:'10:20:19',1:'10:20:37',2:'10:20:39',3:'10:20:39',4:'10:20:41',5:'10:20:42',6:'10:20:42',7:'10:20:44',8:'10:20:45',9:'10:20:46',10:'10:20:46',11:'10:20:47',12:'10:20:49',13:'10:20:50',14:'10:20:51',15:'10:20:52',16:'10:20:53',17:'10:20:54',18:'10:20:55',19:'10:20:55',20:'10:20:57',21:'10:20:58'},
        'jack': {0:'10:17:38',1:'10:17:42',6:'10:17:52',7:'10:17:54',8:'10:17:56',9:'10:17:58',10:'10:18:00',14:'10:18:08',19:'10:18:18',24:'10:18:28'},
        'before': {0:'10:19:46',1:'10:19:54',4:'10:20:00',6:'10:20:04',9:'10:20:10',11:'10:20:14',13:'10:20:18'},
    }
    notes = {
        'origin': 'Fresh gray station load from prior reviewed10:03:47-11:24 filling is covered and pulled11:39, crosses threshold11:47 and is gone11:55. Separate visibly empty beige replacement moves from local waiting row11:47-55 and receives cheese12:03-20:11. Through doorway scale clear12:43, gray load on platform12:51, settled13:15 through15:55, moves off16:03-11. Stack of small metal containers occupies platform17:31-18:03, not a tank. Empty jack already inside11 at18:11. Fresh beige load pulled20:19, threshold20:27, gone20:35. Different empty gray tank goes from local row to station20:19-35; new filling begins20:43 through21:23. Fixed scrap receptacle is separate.',
        'staging': 'Initial12:00 stale. First usable12:09 gray tank already in left doorway staging; operator handles top/liner. No entry crossing visible. Foreground people move tall stack of small rectangular metal containers with round lids12:15-37. This cargo is not a tank. Gray tank stays in staging within this window.',
        'scale': 'Initial12:52 stale. First usable12:56 gray load already on platform behind blue bins. Operator attends it; stack of metal containers and walking people are separate. Previous source last12:37 to first12:56 leaves19 seconds in15 approach coverage. Camera11 shows platform occupancy12:51 but does not establish a full cross-camera origin/entry identity.',
        'dwell': 'Initial14:41 stale. Gray load remains on platform14:48-59, partly occluded by blue bins. Metal cargo stays in foreground. No entry or tank departure in this window.',
        'storage': 'Initial16:32 stale. Gray tank already off platform in doorway staging16:50, pulled left16:52-17:00 then pushed into rear storage row17:02-10. Forks still near/under load at last17:10. Camera11 platform clear16:11 to first usable15 staging16:50 leaves39-second route gap; identity to origin remains unlinked.',
        'release': 'Initial16:53 stale. First usable17:12 shows unloaded forks already extended into aisle, gray tank parked in rear row. Operator pivots unloaded jack17:17-20; tank remains. Final withdrawal falls across2-second sample join17:10-12, not directly observed. Metal-container stack separately moves toward scale17:21-26.',
        'beige': 'Initial20:19 stale. First usable20:37 beige tank already in doorway staging, operator handles top/liner through20:58. Last preceding usable15 frame20:18 is clear;19-second gap covers arrival. No direct15 entry or subsequent scale/storage in this window.',
        'jack': 'Initial17:38 excluded from alignment. Empty jack waits near stored gray tank17:42-52, returns17:54, approaches doorway17:56-58 and crosses18:00-08. Gray remains parked throughout through18:28. Concurrent stack of metal containers moves off scale18:08-18; not a new tank.',
        'before': 'Initial19:46 stale. Door/staging clear19:54-20:18; person walks20:04-10, operator approaches from11 at20:14-18. No beige body visible before last20:18. Next usable15 frame20:37 already has beige in staging; preserve19-second gap.',
    }
    for k,m in metas.items():
        initial = m['requested_window']['start']==0
        merge(OUT/'screening_source_reviews.json', [dict(
            review_id='20261015/'+windows[k][0],reviewed_at=stamp,reviewer='assistant_visual_review',
            date='20261015',camera=m['source']['camera'],split='train',source_member=m['source']['member'],
            source_sha256=m['source_sha256'],frames_manifest=str(paths[k].relative_to(ROOT)),
            sampled_frames_visually_reviewed=len(m['samples']),reviewed_sheets=m['sheets'],
            review_scope='Chronological contact-sheet samples inspected; selected native frames and separate object overlays checked. Sampled review is not exhaustive native-frame viewing.',
            observation=notes[k],accepted_complete_cycle=False,
            clock_warning='Initial stale images excluded. Camera-clock intervals retained; filenames/PTS do not establish synchronization.',
            visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],
                relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],visible_camera_clock=t,
                clock_read_uncertainty_seconds=1,image=m['samples'][i]['image'],
                usable_for_clock_alignment=not(initial and i==0)) for i,t in clocks[k].items()])], 'review_id')
    oldpath=OUT/'sequence_review/20261015/next_origin_1001_cam11/frames.json'
    old=read(oldpath)
    assert old['source_sha256']==metas['origin']['source_sha256']
    def ev(k,a,b): return evidence(metas[k],a,b,paths[k])
    shared=dict(date='20261015',split='train',reviewer='assistant_visual_review',reviewed_at=stamp,dataset_release_accepted=False)
    additions=[
        dict(shared,sequence_id='20261015_fresh_gray_departure_partial_1011',review_status='reviewed_partial_sequence',
            cycle_id=None,production_entry_count_target=None,camera_track_id={'11':'gray_fresh_station_1003_1011','15':'unlinked_gray_scale_storage_1012_1017'},
            cross_camera_identity='unresolved_due_to_missing_entry_and_route',camera_clock_offset_seconds=None,
            stages=[
                dict(stage='filling_observed',camera=11,visible_camera_clock_interval=['10:03:47','10:11:24'],clock_uncertainty_seconds=8,
                    content_evidence='Workers place fresh cheese into gray replacement tank before covering. Initial contents not inferred.',
                    evidence=[evidence(old,17,74,oldpath),ev('origin',0,1)]),
                dict(stage='loaded_departure_11',camera=11,visible_camera_clock_interval=['10:11:39','10:11:55'],
                    doorway_intersection_observed_at='10:11:47',clock_uncertainty_seconds=8,evidence=[ev('origin',0,3)])],
            missing_stages=['linked_entry_15','linked_scale_visit','linked_storage_placement'],
            unlinked_followup=dict(
                staging_first_usable_camera15='10:12:09',scale_visible_camera11_interval=['10:12:51','10:15:55'],
                platform_departure_camera11_interval=['10:16:03','10:16:11'],
                later_gray_storage_camera15_interval=['10:16:50','10:17:12'],
                trajectory_gap_seconds=39,final_release_sample_join_seconds=2,numeric_weight_kg=None,
                observation='Gray later seen on scale and moving to rear storage. Direct arrival and scale-to-staging route are missing; do not promote these observations to a full matched cycle.',
                evidence=[ev('staging',1,15),ev('scale',1,16),ev('dwell',1,7),ev('origin',9,35),ev('storage',1,11),ev('release',1,15),ev('jack',1,24)]),
            limitations=['No room15 production total assigned.','White top alone is not evidence of cheese.','Two-second final fork-release join is an interval, not observed exact release.','No scalar camera-clock offset or measured weight inferred.']),
        dict(shared,sequence_id='20261015_fresh_beige_departure_partial_1020',review_status='reviewed_partial_sequence',
            cycle_id=None,production_entry_count_target=None,camera_track_id={'11':'beige_fresh_station_1012_1020','15':'unlinked_beige_staging_1020'},
            cross_camera_identity='unresolved_direct_entry_gap',camera_clock_offset_seconds=None,
            stages=[
                dict(stage='filling_observed',camera=11,visible_camera_clock_interval=['10:12:03','10:20:11'],clock_uncertainty_seconds=8,
                    content_evidence='Separate empty beige local replacement receives cheese before being pulled.',evidence=[ev('origin',2,65)]),
                dict(stage='loaded_departure_11',camera=11,visible_camera_clock_interval=['10:20:19','10:20:35'],
                    doorway_intersection_observed_at='10:20:27',clock_uncertainty_seconds=8,evidence=[ev('origin',65,68)])],
            missing_stages=['linked_entry_15','scale_visit','storage_placement'],
            unlinked_followup=dict(last_camera15_clear='10:20:18',first_usable_beige_staging='10:20:37',
                sampled_entry_gap_seconds=19,numeric_weight_kg=None,
                observation='Beige already inside15 after source gap. Handling top at staging through20:58; subsequent route not reviewed.',
                evidence=[ev('before',1,13),ev('beige',1,21)]),
            limitations=['No entry time or full production count invented.','Gray replacement filling after20:43 is another tank.','Initial20:19 frame of15 source is stale.']),
        dict(shared,sequence_id='20261015_empty_beige_replacement_1011',review_status='accepted_negative_sequence',
            cycle_id=None,production_entry_count_target=0,camera=11,camera_track_id='empty_beige_local_1011',
            negative_class='empty_tank_internal_reposition',tracked_tank_count=1,
            visible_camera_clock_interval=['10:11:47','10:11:55'],clock_uncertainty_seconds=8,evidence=[ev('origin',1,4)],
            observation='Visibly empty beige tank moves from local waiting row to filling station; fresh filling starts12:03.',
            label_scope='Only empty local replacement movement. Concurrent loaded gray exit and later beige filling are separate.'),
        dict(shared,sequence_id='20261015_empty_gray_replacement_1020',review_status='accepted_negative_sequence',
            cycle_id=None,production_entry_count_target=0,camera=11,camera_track_id='empty_gray_local_1020',
            negative_class='empty_tank_internal_reposition',tracked_tank_count=1,
            visible_camera_clock_interval=['10:20:19','10:20:35'],clock_uncertainty_seconds=8,evidence=[ev('origin',65,69)],
            observation='Visibly empty gray tank moves from local waiting row into station. Fresh filling begins20:43.',
            label_scope='Only empty replacement movement, excluding simultaneous loaded beige exit and later gray filling.'),
        dict(shared,sequence_id='20261015_unloaded_jack_return_1018',review_status='accepted_negative_sequence',
            cycle_id=None,production_entry_count_target=0,camera=15,camera_track_id='empty_jack_return_1018',
            negative_class='pallet_jack_without_tank',tracked_tank_count=0,
            visible_camera_clock_interval=['10:17:54','10:18:08'],clock_uncertainty_seconds=2,
            evidence=[ev('jack',6,14),ev('origin',50,51)],
            observation='Unloaded jack travels from storage aisle to room11 through doorway. Stored gray remains in15; operator is already inside11 at18:11.',
            label_scope='Only unloaded jack return. Simultaneous metal-container cargo and stationary tanks are excluded.')]
    merge(OUT/'reviewed_sequence_labels.json',additions,'sequence_id')
    queue=[]
    for ident,observation,next_action,refs in [
        ('20261015_gray_1011_entry_route_gap','Direct15 arrival missing; first usablegray12:09. Scale clear16:11 to15 firststaging16:50 leaves39 seconds. Final storage release falls between17:10 and12.',
         'Retain partial. Do not repeat unchanged windows without additional source coverage.',[ev('origin',0,35),ev('staging',1,15),ev('storage',1,11),ev('release',1,3)]),
        ('20261015_beige_1020_entry_gap','11 freshbeige crosses20:27.15 lastclear20:18 thenalreadybeigestaged20:37;19-second gap.',
         'Continue later11 relativePTS1800+ and15 sources102626-102649/102654-102723 for scale/storage context; direct entry remains unavailable in these reviewed sources.',[ev('origin',65,74),ev('before',11,13),ev('beige',1,21)]),
        ('20261015_next_gray_after1020','Different gray replacement startsfreshfilling20:43 through21:23, no departure yet.',
         'Remaining11 relativePTS1800-2750 may show next departure. Check paired15 coverage before extraction, preserve preceding gaps.',[ev('origin',69,74)])]:
        queue.append(dict(candidate_id=ident,date='20261015',split='train',cycle_id=None,production_entry_count_target=None,
            status='partial_followup_pending',reviewed_at=stamp,observation=observation,next_action=next_action,evidence=refs))
    merge(OUT/'sequence_followup_queue.json',queue,'candidate_id')
    save(OUT/'gap_search_20261031_21.json',dict(reviewed_at=stamp,day='20261015',split='train',
        findings=['Gray entry not shown:11 exits11:47-55,15 first usable12:09 already staged.',
            '15 gray staging12:37 toscale12:56 leaves19-second approach gap;11 platform already occupied12:51.',
            '11 platform clear16:11 to15 staging16:50 leaves39-second route gap. Final release join17:10-12 retained.',
            'Beige15 direct entry missing betweenlastclear20:18 andfirstusablealready-staged20:37.11 crossing20:27 lieswithin gap.',
            'Stack of small rectangular metal containers is not a tank; its scale visit and aisle movement are separate cargo.'],
        action='Keep two fresh departures as partials. No guessed cross-camera identity, entry second or production total.'))

    registry=read(OUT/'object_review_decisions.json')
    history=OUT/'review_history/object_decisions_before_20261031_21.json'
    if not history.exists(): save(history,registry)
    decisions={r['id']:r for r in registry['reviews']}
    drafts={r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
    descriptions={
        '171':'Covered gray departure; right lower body occluded by person, native context inspected.',
        '172':'Covered beige departure, isolated tank body.',
        '173':'Two distinct visibly empty waiting tanks; rear beige partially occluded by front gray, worker behind rim.',
        '174':'True zero-tank ROI: people and tall stack of small metal containers, cropped away from actual background/foreground tanks. Not an empty tank label or whole-room absence label.',
        '175':'Moving gray tank body in15. Top and right cropped; small left occlusion by jack. No background storage tank inside declared ROI.'}
    for ident,note in descriptions.items():
        assert ident not in decisions
        r=drafts[ident]
        attrs=[dict(box_index=i,truncated=ident=='175',occluded=ident in ('171','173','175'),load_state='unknown_not_annotated') for i in range(len(r['boxes_xyxy']))]
        decisions[ident]=dict(id=ident,image_sha256=r['sha256'],
            boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',
            load_state_reviewed=False,sequence_reviewed=False,instance_attributes=attrs,
            negative_roi_verified=ident=='174',
            evidence=[r['source_frame'],r['frames_manifest'],f'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_{19 if ident in ("171","172","173") else 20}.jpg'],note=note)
    registry['reviews']=list(decisions.values())
    registry.setdefault('corrections',[]).append('Batch21:171-175 separately overlay-reviewed. Five accepted ROIs, five tank boxes;174 is genuine no-tank cargo crop. Prior decisions preserved.')
    save(OUT/'object_review_decisions.json',registry)
    inv=read(BASE/'archive_inventory.json')
    inspected={m['source']['member']:m['source_sha256'] for m in metas.values()}
    for r in inv['records']:
        if r['member'] in inspected:r.update(pixel_inspected=True,sha256=inspected[r['member']])
    assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test')
    save(BASE/'archive_inventory.json',inv)
    reviews=read(OUT/'screening_source_reviews.json')
    total=sum(r['sampled_frames_visually_reviewed'] for r in reviews)
    added=sum(len(m['samples']) for m in metas.values())
    state['last_completed'] += [
        f'Batch21 inspected {added} chronological presentations in9 windows on15Oct; {total} total across {len({r["source_sha256"] for r in reviews})} sources and {len(reviews)} windows. All extractions completed;25/28Oct untouched.',
        '15Oct two fresh departures added as partials:gray11:47-55 lacks direct15 entry and39-second scale-to-staging route;beige20:27 falls in19-second15 entry gap. No new full cycle. Totals5 complete,19 partials.',
        'Three track-scoped negatives added:empty beige and gray local replacements, unloaded jack return18min. Total52 negative sequences. Moving stack of small metal containers is separate non-tank cargo.',
        'Five native ROIs171-175 approved after separate overlays:five tank boxes includingtwo in173, zero in174 metal-cargo crop. Totals176 candidates,122 accepted images,177 boxes,54 exclusions,zero drafts. Dataset unreleased.'
    ]
    state['priority_next']=[
        'Batch21 complete.5 full cycles all13Oct; need complete-cycle day diversity and actual same-load reentry/post-storage relocation negatives, not more easy negatives alone.',
        '15Oct next gray station tank fills20:43-21:23.11 source095128-103726 relativePTS1800+ unreviewed; later15 sources102626-102649/102654-102723 can extend beige partial or nextgray route. Do not repeat missing15 entry20:18-37 orgray16:11-50 route without new media.',
        '13Oct next distinct gray load fills27:24-31:40;11 sources093135-093311 and093311-094655 plus15 sources after093339 may cover next full cycle, but prioritize day diversity.',
        '13Oct102139-102912 long15 source unreviewed;11 source gap10:00:12-25:11 may leave missing origin.'
    ]+[p for p in state['priority_next'] if p.startswith('Known gaps') or p.startswith('25/28') or p.startswith('Old21Oct')]
    state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    state['scripts'] += [s for s in ['work/append_tank_roi_batch_20261031_21.py','work/record_tank_sequence_batch_20261031_21.py'] if s not in state['scripts']]
    save(OUT/'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_samples=added,total_presentations=total,additional_complete_cycles=0,additional_partial_sequences=2,additional_negative_sequences=3,training_started=False)))


if __name__=='__main__':main()
