"""Persist visual curation of the second13Oct filling-to-storage cycle.

The observations below were read from chronological source images. Nothing in
this recorder performs detection, training, timing inference or test evaluation.
"""
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read, save, merge, evidence

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/tank_transfer_training_v1'
OUT=BASE/'dataset_v1'
RUN='sequence_review_20261031_06'

def main():
    state=read(OUT/'continuation_state.json')
    if RUN in state.get('completed_curation_runs',[]):
        print('Already recorded:',RUN);return
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    windows={
        'origin':('next_origin_1055_cam11',65),
        'departure':('gray_departure_1056_cam11',23),
        'entry':('gray_entry_1056_cam15',29),
        's57':('next_scale_1057_cam15',14),
        's58':('next_scale_1058_cam15',13),
        's5831':('next_scale_105831_cam15',10),
        's5841':('next_scale_105841_cam15',6),
        's5901':('next_scale_105901_cam15',5),
        's5913':('next_scale_105913_cam15',8),
        's0050':('next_storage_110050_cam15',6),
        'scale11':('gray_scale_cam11_1057',52),
        's0057':('next_storage_110057_cam15',6),
        's0137':('next_storage_110137_cam15',6),
        's0159':('next_storage_110159_cam15',22),
        's0253':('next_storage_110253_cam15',33),
        'bridge':('gray_storage_bridge_110148',11),
        'settle':('gray_storage_settle_1102',34),
    }
    paths={k:OUT/'sequence_review/20261013'/name/'frames.json' for k,(name,_) in windows.items()}
    metas={k:read(p) for k,p in paths.items()}
    for k,m in metas.items():
        assert len(m['samples'])==windows[k][1]
        assert m['source']['date']=='20261013' and m['source']['split']=='train'
        assert all((ROOT/s['image']).is_file() for s in m['samples'])
    # Sparse anchor ledger: every value was visually read, never interpolated
    # from a filename or PTS. All contact-sheet images were inspected.
    clocks={
        'origin':{0:'10:53:27',9:'10:54:04',10:'10:54:08',11:'10:54:12',12:'10:54:16',30:'10:55:28',38:'10:56:00',40:'10:56:08',41:'10:56:12',42:'10:56:16',43:'10:56:20',44:'10:56:24',45:'10:56:28',46:'10:56:31',47:'10:56:36',48:'10:56:40',49:'10:56:44',64:'10:57:44'},
        'departure':{0:'10:56:15',5:'10:56:20',9:'10:56:24',10:'10:56:25',13:'10:56:28',14:'10:56:29',15:'10:56:30',22:'10:56:37'},
        'entry':{0:'10:56:16',4:'10:56:20',6:'10:56:22',7:'10:56:23',8:'10:56:24',10:'10:56:26',12:'10:56:28',15:'10:56:31',17:'10:56:33',28:'10:56:44'},
        's57':{0:'10:57:15',1:'10:57:21',6:'10:57:31',8:'10:57:35',10:'10:57:39',13:'10:57:45'},
        's58':{0:'10:58:00',1:'10:58:07',12:'10:58:29'},
        's5831':{0:'10:58:31',1:'10:58:37',9:'10:58:53'},
        's5841':{0:'10:58:41',1:'10:58:58',2:'10:59:01',5:'10:59:10'},
        's5901':{0:'10:59:00',1:'10:59:13',4:'10:59:22'},
        's5913':{0:'10:59:13',1:'10:59:27',7:'10:59:45'},
        's0050':{0:'11:00:50',1:'11:00:54',2:'11:00:57',3:'11:01:00',5:'11:01:06'},
        'scale11':{0:'10:57:37',1:'10:57:41',4:'10:57:54',5:'10:57:57',7:'10:58:06',21:'10:59:02',24:'10:59:14',29:'10:59:33',30:'10:59:37',31:'10:59:42',32:'10:59:45',33:'10:59:50',36:'11:00:02',42:'11:00:26',45:'11:00:37',46:'11:00:41',47:'11:00:46',48:'11:00:49',49:'11:00:53',50:'11:00:57',51:'11:01:01'},
        's0057':{0:'11:00:57',1:'11:01:14',2:'11:01:17',5:'11:01:26'},
        's0137':{0:'11:01:37',1:'11:01:45',2:'11:01:48',3:'11:01:51',4:'11:01:54',5:'11:01:57'},
        's0159':{0:'11:01:59',1:'11:02:10',2:'11:02:13',3:'11:02:17',4:'11:02:20',5:'11:02:23',6:'11:02:26',15:'11:02:53',21:'11:03:10'},
        's0253':{0:'11:02:53',1:'11:03:15',12:'11:03:48',16:'11:04:00',20:'11:04:12',21:'11:04:15',24:'11:04:24',32:'11:04:48'},
        'bridge':{0:'11:01:48',1:'11:01:58',2:'11:01:59',3:'11:02:00',4:'11:02:01',5:'11:02:02',6:'11:02:03',7:'11:02:04',8:'11:02:05',9:'11:02:06',10:'11:02:07'},
        'settle':{0:'11:01:59',1:'11:02:08',2:'11:02:09',4:'11:02:10',6:'11:02:11',8:'11:02:12',10:'11:02:13',12:'11:02:14',14:'11:02:15',17:'11:02:17',23:'11:02:20',29:'11:02:23',33:'11:02:25'},
    }
    notes={
        'origin':'Fresh gray tank at filling station visibly receives cheese blocks10:53:27-10:56:08. Separate fixed scrap tank is visible on the right. An empty manual jack comes15-to11 at10:54:08-12 and is engaged beneath the filling tank. White boards/cover are placed10:56:12-16. Loaded tank is pulled away10:56:20, passes door10:56:24-30, then disappears. Another visibly empty gray tank is moved from the room11 left row to the filling station10:56:20-31; later new filling begins around10:56:40-44. These are distinct tank tracks. Later through-door view shows the first gray tank being maneuvered by the scale.',
        'departure':'Gray tank just covered at the filling station approaches the doorway10:56:20, crosses10:56:24-29, and clears the visible camera11 threshold by10:56:30. One loaded departure; partial occlusion at the doorpost. No second crossing in this window.',
        'entry':'Door initially clear. Operator appears10:56:20; gray tank with white top appears at the doorway10:56:22-24, passes behind fixed blue bins and becomes fully room-side by10:56:31. Tank is staged beside the door; two operators handle top fittings10:56:33-44. Entry time retained as an occlusion interval, not an exact timestamp.',
        's57':'Same gray tank staged near door with two operators handling fittings. Operator takes jack handle; tank moves toward scale10:57:35-45. Initial frame10:57:15 then10:57:21. Adjacent previous long source reaches10:57:16; matching body, cover and position support join.',
        's58':'Gray covered tank stays at scale, mostly hidden behind fixed blue bins; operator handles upper area. First frame10:58:00 then10:58:07; camera11 long view supplies complementary dwell context. No numeric scale readout verified.',
        's5831':'Same gray covered tank stays at scale. Clock begins10:58:31 then10:58:37. No additional entry or displacement.',
        's5841':'First clock10:58:41 is stale relative to next10:58:58. Gray tank remains at scale through10:59:10; overlapping earlier export reaches10:58:53. Preserve original sample order and timing discontinuity.',
        's5901':'Gray tank stays at scale while operator handles hoses/wall area. Clock starts10:59:00 then10:59:13 and reaches10:59:22, beyond nominal filename end. No displacement or measured kilograms inferred.',
        's5913':'First clock10:59:13 then10:59:27. Same gray tank at scale through10:59:45. Camera11 long view checks the source gaps and unchanging tank identity.',
        's0050':'Gray tank remains in the scale/door area11:00:50-11:01:06 while the operator handles the jack. Scale body is partly hidden in this view. Do not infer exact scale clearance from these wide images.',
        'scale11':'Gray tank being maneuvered on scale10:57:37-49. By10:57:54 tank is on the platform; forks withdrawn10:57:57-10:58:06. Tank remains on scale through11:00:49; operator handles top/hoses, with brief person-only crossings. At11:00:53-57 jack is inserted;11:01:01 tank angle changes during handling. This sample does not establish final clearance from scale. This continuous source provides complementary identity/dwell evidence across short camera15 exports, not a scalar clock calibration.',
        's0057':'First frame11:00:57 then11:01:14. Operator handles jack in the partly occluded scale/door area11:01:14-26. Gray tank remains in that vicinity; exact platform clearance is not visible from this crop.',
        's0137':'Gray tank in scale/door area at11:01:37. At11:01:45-48 gray tank with distinctive upstanding white liner/fittings is pulled out from behind blue bins and taken toward foreground11:01:51-57. No new doorway arrival accompanies this motion.',
        's0159':'Same gray tank is in central aisle11:01:59. Next coarse sample11:02:10 shows it at left end of front storage row next to earlier beige tank. Dense bridge and settle windows cover this apparent coarse jump. Empty forks are withdrawn11:02:13-14; empty jack moves away11:02:15-26. Tank stays parked through11:03:10, beyond nominal filename end.',
        's0253':'First frame11:02:53 then11:03:15. Newly stored gray tank remains stationary next to the earlier beige tank through11:04:48. People handle cylindrical cans and their pallets, not the large cheese tank. Later operator handles doorway area11:04:15-48; no second incoming tank identity is established in these samples. Do not reuse static storage count as arrivals.',
        'bridge':'Initial frame11:01:48 then11:01:58. Gray tank travels across aisle11:01:58-11:02:07 with the same cover folds, body and jack. This source supplies the movement absent between coarse samples of the next export, whose first noninitial dense sample is11:02:08.',
        'settle':'First frame11:01:59 is stale; next11:02:08 follows bridge ending11:02:07. Same gray tank is pushed against storage row11:02:08-11. Operator lowers and withdraws empty forks11:02:13-14; tank remains stationary while jack travels away11:02:15-25. One storage completion, no new production entry.',
    }
    reviews=[]
    initial_jump=set(windows)-{'origin','departure','entry','scale11'}
    for k,m in metas.items():
        name,_=windows[k]
        reviews.append(dict(review_id='20261013/'+name,reviewed_at=stamp,reviewer='assistant_visual_review',
            source_member=m['source']['member'],source_sha256=m['source_sha256'],date='20261013',camera=m['source']['camera'],split='train',
            frames_manifest=str(paths[k].relative_to(ROOT)),sampled_frames_visually_reviewed=len(m['samples']),reviewed_sheets=m['sheets'],
            review_scope='All chronological contact-sheet samples visually inspected; native context checked for object crops. Not exhaustive native-frame viewing.',
            visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],
                relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],visible_camera_clock=t,clock_read_uncertainty_seconds=1,
                image=m['samples'][i]['image'],usable_for_clock_alignment=not(i==0 and k in initial_jump)) for i,t in clocks[k].items()],
            observation=notes[k],accepted_complete_cycle=False,
            clock_warning='Clock pixels read manually. First-frame jumps remain explicit; no clock offset or full cycle is inferred from filename/PTS alone. See joined sequence label.'))
    merge(OUT/'screening_source_reviews.json',reviews,'review_id')
    def ev(k,a,b):return evidence(metas[k],a,b,paths[k])
    def stage(name,times,uncertainty,refs,observation,**extra):
        return dict(stage=name,visible_camera_clock_interval=times,clock_uncertainty_seconds=uncertainty,
                    evidence=[ev(*ref) for ref in refs],observation=observation,**extra)
    cycle=dict(sequence_id='20261013_gray_filling_to_storage_1056',date='20261013',split='train',
        reviewer='assistant_visual_review',reviewed_at=stamp,review_status='accepted_complete_cycle',dataset_release_accepted=False,
        cycle_id='20261013_gray_1056',camera_track_id={'11':'gray_filling_departure_1056','15':'gray_entry_scale_storage_1056'},
        cross_camera_identity='assistant_visual_correspondence_reviewed_with_occlusion',
        clock_alignment='shared_crossing_visually_checked_timestamp_uncertainty_retained',camera_clock_offset_seconds=None,
        origin_content='Cheese blocks visible and additional placements observed in the gray filling tank before the white cover is fitted.',
        production_entry_count_target=1,entry_camera=15,entry_clock_interval=['10:56:22','10:56:31'],
        counting_rule='One production-load entry, finalized after scale visit and storage. Do not increment at scale removal, storage or empty-jack return.',
        stages=[
            stage('filling_observed',['10:53:27','10:56:08'],4,[('origin',0,40)],'Cheese blocks placed into this gray tank. Fill already underway; initial content and block count are unknown.'),
            stage('loaded_departure_11',['10:56:20','10:56:30'],1,[('origin',40,46),('departure',5,15)],'Fresh filling tank covered and pulled through shared door.',doorway_crossing_camera11_interval=['10:56:24','10:56:30']),
            stage('entry_15',['10:56:22','10:56:31'],5,[('departure',7,15),('entry',4,17)],'Gray white-top tank crosses into15 behind fixed blue bins and is staged by doorway.',timestamp_precision='interval_only',occlusion='Body partly hidden by stationary blue bins and doorpost.',correspondence_basis='Same gray body/white cover, manual jack, single observed crossing, immediate adjacent-door chronology and subsequent staged trajectory. Not a color-only match.'),
            stage('scale_visit',['10:57:37','11:01:48'],4,
                  [('s57',6,13),('scale11',0,51),('s58',0,12),('s5831',0,9),('s5841',1,5),('s5901',1,4),('s5913',1,7),('s0050',0,5),('s0057',1,5),('s0137',0,2)],
                  'Platform placement and subsequent dwell visible from camera11, with complementary room15 views. Jack reengagement at11:00:53-11:01:01 precedes final movement into room15 aisle by11:01:45-48. Exact platform clearance is not resolved.',
                  numeric_weight_kg=None,measurement_success_verified=False,scale_departure_clock_interval=['11:00:49','11:01:48'],
                  stationary_on_platform_observed_interval_camera11=['10:57:54','11:00:49'],
                  source_join_review='Short camera15 exports start with stale frames and jump forward. Complementary long camera11 source shows the same tank on the platform across dwell gaps. Initial stale samples are not timing anchors. No scalar inter-camera clock calibration claimed.'),
            stage('storage_placement',['11:01:45','11:02:14'],1,
                  [('s0137',1,5),('bridge',1,10),('settle',1,14),('s0159',1,21),('s0253',1,32)],
                  'Gray tank pulled from scale/door area through the aisle, pushed against front row beside earlier beige load, lowered and left while empty forks withdraw.',
                  parked_and_jack_withdrawal_interval=['11:02:13','11:02:14'],
                  location='Left end of the front stored-tank row, adjacent to earlier beige tank.',
                  confirmation='Gray tank stays parked through11:04:48. Bridge export reaches11:02:07; next noninitial dense sample reads11:02:08. Continuous visible same-tank movement connects the apparent coarse sampling jump.')
        ],limitations=[
            'Assistant-reviewed annotation, not a model prediction or independently user-certified production count.',
            'No initial contents, cheese-block total or kilograms are inferred. Scale visit does not verify a measured weight.',
            'Entry is occluded; retain nine-second camera15 interval rather than an invented exact timestamp or scalar camera offset.',
            'Exact scale clearance remains broadly bounded during jack handling; this does not change the once-only entry target.',
            'All stages are evidenced but every wall-clock instant is not guaranteed recorded. Source-order jumps and original PTS are retained.',
            'Global dataset coverage and release checks remain incomplete. No training export released.'
        ])
    common=dict(date='20261013',split='train',reviewer='assistant_visual_review',reviewed_at=stamp,
        review_status='accepted_negative_sequence',cycle_id=None,production_entry_count_target=0,dataset_release_accepted=False)
    replacement=dict(common,sequence_id='20261013_empty_gray_replacement_105620',camera=11,
        camera_track_id='cam11_empty_gray_from_left_row_105620',negative_class='empty_tank_internal_reposition',tracked_tank_count=1,
        visible_camera_clock_interval=['10:56:20','10:56:31'],clock_uncertainty_seconds=4,evidence=[ev('origin',42,47)],
        observation='One visibly empty gray tank is pulled from the existing left row into the filling station. Empty interior/liner visible while moving. Later filling is a separate stage outside this negative interval.',
        label_scope='This replacement tank only. Simultaneous loaded departure belongs to gray_1056 positive cycle and must not be labeled negative.')
    jack=dict(common,sequence_id='20261013_empty_jack_after_storage_110214',camera=15,
        camera_track_id='cam15_empty_jack_after_gray_storage_110214',negative_class='pallet_jack_without_tank',tracked_tank_count=0,
        visible_camera_clock_interval=['11:02:14','11:02:26'],clock_uncertainty_seconds=1,evidence=[ev('settle',12,33),ev('s0159',3,6)],
        observation='After gray load is stored, clearly empty forks are withdrawn and jack moves back toward doorway without a tank.',
        label_scope='Only empty-jack return after parking. The stored tank remains visible and does not create another production event.')
    merge(OUT/'reviewed_sequence_labels.json',[cycle,replacement,jack],'sequence_id')
    queue=read(OUT/'sequence_followup_queue.json')
    candidate=next(r for r in queue if r['candidate_id']=='20261013_door_activity_105632')
    prior=OUT/'review_history/followup_before_20261031_06.json'
    if not prior.exists():save(prior,dict(saved_at=stamp,records=[copy.deepcopy(candidate)]))
    candidate.update(status='resolved_in_reviewed_sequence',resolved_sequence_id=cycle['sequence_id'],reviewed_at=stamp,
        resolution='Fresh gray filling origin, loaded exit, occluded room15 entry, platform visit and storage connected by source-backed visual review. See reviewed_sequence_labels.json. Queue itself is not an additional label/count.')
    save(OUT/'sequence_followup_queue.json',queue)
    registry=read(OUT/'object_review_decisions.json')
    decisions={r['id']:r for r in registry['reviews']}
    drafts={r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
    roi_notes={
        '090':'Gray filling tank visibly contains cheese blocks. Bottom is truncated and operator occludes the body; one tank only, not individual conveyor trays.',
        '091':'Covered gray body crossing doorway. Separate native-source context and rendered overlay checked; the doorway occludes part of the body.',
        '092':'Gray body with fittings on the scale visible through camera11 door. Doorpost occlusion retained; this is not another arrival.',
        '093':'Moving empty replacement tank plus three separate background/border tank fragments. All four recognizable instances labeled; no whole-row box.'
    }
    for ident,note in roi_notes.items():
        assert ident not in decisions
        r=drafts[ident]
        overlay=BASE/'detector_v1/sheets'/('labels_10.jpg' if ident=='093' else 'labels_09.jpg')
        decisions[ident]=dict(id=ident,image_sha256=r['sha256'],
            boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',
            load_state_reviewed=False,sequence_reviewed=False,
            instance_attributes=[dict(box_index=j,truncated=(b[0]==0 or b[1]==0 or b[2]==r['width'] or b[3]==r['height']),
                occluded=(ident!='093' or j in [1,2]),load_state='unknown_not_annotated') for j,b in enumerate(r['boxes_xyxy'])],
            evidence=[r['source_frame'],r['frames_manifest'],str(overlay.relative_to(ROOT))],note=note)
    registry['reviews']=list(decisions.values())
    registry.setdefault('corrections',[]).append('Batch06 adds090-093 after native-context and separate overlay review; four images and seven boxes. Existing decisions unchanged; load attributes not released.')
    save(OUT/'object_review_decisions.json',registry)
    inventory=read(BASE/'archive_inventory.json')
    inspected={m['source']['member']:m['source_sha256'] for m in metas.values()}
    for r in inventory['records']:
        if r['member'] in inspected:r.update(pixel_inspected=True,sha256=inspected[r['member']])
    assert not any(r['pixel_inspected'] for r in inventory['records'] if r['split']=='test')
    save(BASE/'archive_inventory.json',inventory)
    allreviews=read(OUT/'screening_source_reviews.json')
    total=sum(r['sampled_frames_visually_reviewed'] for r in allreviews)
    additional=sum(len(m['samples']) for m in metas.values())
    state['last_completed'] += [
        f'Batch06 reviewed {additional} further chronological sample presentations in17 source windows; {total} presentations total. All extraction sessions have finished. No test pixels inspected.',
        '13Oct second gray cycle accepted after fresh filling, loaded door crossing, scale dwell and storage trajectory review. Entry15 interval10:56:22-31; storage confirmed by empty-fork withdrawal11:02:13-14. Total2 accepted complete cycles.',
        'The apparent storage movement gap was bridged by adjacent source reaching11:02:07 and next noninitial dense frame11:02:08. Source initial stale frames retained and excluded from timing alignment. Exact platform clearance remains broadly bounded11:00:49-11:01:48.',
        'Added empty-gray internal replacement and empty-jack-after-storage negatives, each track-scoped. Total9 accepted negatives and3 reviewed partials; previous unresolved6/15Oct tracks unchanged.',
        'Four native ROI images090-093 and7 boxes added after separate overlay review. Totals94 candidates,55 accepted ROI images,91 accepted boxes;6 drafts and33 excluded. Training remains unreleased.'
    ]
    state['priority_next']=[
        'Batch06 is complete. Do not repeat its17 windows. The queued13Oct10:56 gray load is resolved; second complete cycle stored11:02:13-14. New gray and prior beige tanks remain stationary through11:04:48.',
        'Prioritize another training day (8/10 or10/10) and representative object crops to diversify beyond13Oct. Select paired sources via archive_inventory.json; inspect actual camera clocks and chronological continuity before matching. No new extraction is currently active.',
        '6Oct entry gap09:35:55-09:36:42 and15Oct scale-to-storage gap11:15:46-11:16:23 remain unresolved; do not repeat completed failed gap searches. Keep both partial and later tracks unlinked.',
        'Six object drafts002/003/006/007/010/011 remain. Expand clear views on other train days and17Oct validation without changing day partitions.',
        'Need complete cycles on more days, same-load reentry and already-stored relocation negatives, plus validation-day cycles.25/28Oct remain locked without pixels. No training or uploads.'
    ]
    state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    for name in ['work/append_tank_roi_batch_20261031_06.py','work/record_tank_sequence_batch_20261031_06.py']:
        if name not in state['scripts']:state['scripts'].append(name)
    save(OUT/'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_temporal_samples=additional,additional_complete_cycles=1,
        additional_negatives=2,additional_accepted_images=4,training_started=False)))

if __name__=='__main__':main()
