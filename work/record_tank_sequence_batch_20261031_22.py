"""Persist inspected 15Oct sources without inventing missing entry/storage links."""
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read, save, merge, evidence

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'outputs/tank_transfer_training_v1'
OUT = BASE / 'dataset_v1'
RUN = 'sequence_review_20261031_22'


def main():
    state = read(OUT/'continuation_state.json')
    if RUN in state.get('completed_curation_runs', []):
        print('Already recorded', RUN)
        return
    stamp = dt.datetime.now(dt.timezone.utc).isoformat()
    windows = {
        'origin': ('next_origin_1021_cam11', 96),
        'beige_storage': ('beige_storage_1026_cam15', 11),
        'beige_release': ('beige_release_1027_cam15', 10),
        'before': ('next_staging_1028_cam15', 7),
        'empty': ('next_scale_1028_cam15', 10),
        'scale1': ('next_entry_1030_cam15', 18),
        'scale2': ('next_staging_1031_cam15', 15),
        'scale3': ('next_scale_1031_cam15', 18),
        'route': ('next_storage_1035_cam15', 8),
    }
    paths = {k: OUT/'sequence_review/20261015'/w/'frames.json' for k,(w,n) in windows.items()}
    metas = {k:read(p) for k,p in paths.items()}
    for k,m in metas.items():
        assert m['source']['date']=='20261015' and m['source']['split']=='train'
        assert len(m['samples'])==windows[k][1]
    # Clock readings were inspected in rendered pixels, not generated from PTS.
    clocks = {
        'origin': {0:'10:21:31',1:'10:21:41',2:'10:21:51',20:'10:24:51',21:'10:25:01',22:'10:25:11',23:'10:25:21',
            36:'10:27:31',40:'10:28:11',41:'10:28:21',42:'10:28:31',43:'10:28:41',44:'10:28:51',45:'10:29:01',46:'10:29:11',47:'10:29:21',48:'10:29:31',
            51:'10:30:01',52:'10:30:11',53:'10:30:21',54:'10:30:31',77:'10:34:21',78:'10:34:31',79:'10:34:41',85:'10:35:41',86:'10:35:51',88:'10:36:11',92:'10:36:51',93:'10:37:01',94:'10:37:11',95:'10:37:21'},
        'beige_storage': {0:'10:26:26',1:'10:26:30',2:'10:26:32',3:'10:26:34',4:'10:26:36',5:'10:26:38',6:'10:26:40',7:'10:26:42',8:'10:26:44',9:'10:26:46',10:'10:26:48'},
        'beige_release': {0:'10:26:54',1:'10:27:06',2:'10:27:08',3:'10:27:10',4:'10:27:12',5:'10:27:14',6:'10:27:16',7:'10:27:18',8:'10:27:20',9:'10:27:22'},
        'before': {0:'10:28:10',1:'10:28:29',2:'10:28:31',3:'10:28:33',4:'10:28:35',5:'10:28:37',6:'10:28:39'},
        'empty': {0:'10:28:32',1:'10:28:42',2:'10:28:44',3:'10:28:46',4:'10:28:48',5:'10:28:50',6:'10:28:52',7:'10:28:54',8:'10:28:56',9:'10:28:58'},
        'scale1': {0:'10:30:25',1:'10:30:35',2:'10:30:37',3:'10:30:39',4:'10:30:41',5:'10:30:43',6:'10:30:45',7:'10:30:47',8:'10:30:49',9:'10:30:51',10:'10:30:53',11:'10:30:55',12:'10:30:57',13:'10:30:59',14:'10:31:01',15:'10:31:03',16:'10:31:05',17:'10:31:07'},
        'scale2': {0:'10:30:59',1:'10:31:08',2:'10:31:09',3:'10:31:10',4:'10:31:11',5:'10:31:12',6:'10:31:13',7:'10:31:14',8:'10:31:15',9:'10:31:16',10:'10:31:17',11:'10:31:18',12:'10:31:19',13:'10:31:20',14:'10:31:21'},
        'scale3': {0:'10:31:32',1:'10:31:35',2:'10:31:37',3:'10:31:39',4:'10:31:41',5:'10:31:43',6:'10:31:45',7:'10:31:47',8:'10:31:49',9:'10:31:51',10:'10:31:53',11:'10:31:55',12:'10:31:57',13:'10:31:59',14:'10:32:01',15:'10:32:03',16:'10:32:05',17:'10:32:07'},
        'route': {0:'10:35:21',1:'10:35:39',2:'10:35:40',3:'10:35:43',4:'10:35:44',5:'10:35:46',6:'10:35:49',7:'10:35:50'},
    }
    notes = {
        'origin': 'Gray fresh tank filling continues21:31-28:21, covered28:31, pulled28:41, near door28:51, threshold29:01, gone29:11. Empty beige replacement arrives station29:01-21, fresh filling29:31-36:51, covered37:01, pulled37:11, gone37:21; exact second crossing not sampled. Fixed scrap tank separate. Through doorway prior beige scale approach21:41, settled21:51 through24:51, engaged25:01-11, platform clear25:21. Later gray platform occupied30:11-34:21, moves off34:31, clear34:41; gray edge remains at right staging through35:41, gone35:51. These are sampled clock observations, not continuous native-frame tracking.',
        'beige_storage': 'Initial26:26 early image excluded from alignment. Beige already parked in rear row first usable26:30. Unloaded forks withdrawn into aisle26:30-34; operator approaches door26:36-48. Beige stays parked. No scale-to-parking route in this source; platform clear in11 at25:21 to first usable15 parked view26:30 leaves69 seconds. Do not link to fresh20min departure as complete.',
        'beige_release': 'Initial26:54 early image. Operator at blue bins/door with unloaded jack27:06-20, begins return27:22. Beige rear tank remains stationary. No new entry. Operator already inside11 at27:31, leaving9-second sampled trajectory gap.',
        'before': 'Initial28:10 early image. Worker walks toward left waiting empty tanks28:29-39. No tank movement to15 in this window; rear stored row remains stationary.',
        'empty': 'Initial28:32 early image. Visibly empty beige tank moves from left waiting row28:42-48, approaches door28:50, passes28:52-54, out28:56. No gray entry visible through last28:58. Next usable15 sample30:35 already has gray on platform, a97-second reviewed15 sample gap.',
        'scale1': 'Initial30:25 early image. Gray covered tank already on far-right platform behind blue bins30:35; operator attends it, no entry shown. Foreground powered jack moves inverted upper gray atop upright lower tank30:43-49; empty forks retreat30:51-53. Only upper inversion supports empty state; lower contents unknown.',
        'scale2': 'Initial30:59 early image. Gray stays on platform31:08-21, operator handles doorway/wall. One-second usable source join31:07-08. Newly relocated foreground inverted stack stays put; no new production entry.',
        'scale3': 'Initial31:32 early image. Gray remains on platform31:35-32:07.14-second gap from last usable prior source31:21;11 retains sampled platform occupancy. Separate second inverted upper gray atop upright lower arrives on powered jack31:43-49, empty forks retreat31:51-55. Lower contents unknown, upper-only negative scope.',
        'route': 'Initial35:21 early image. Covered gray emerges from doorway staging35:39, pulled35:40-43, turns35:44-46, moves left in aisle35:49-50. No final parking or fork withdrawal in source.11 platform clear34:41 to first usable15 route35:39 is58 seconds;11 gray edge stays in staging through35:41. Entry remains unobserved, origin identity not promoted.',
    }
    for k,m in metas.items():
        merge(OUT/'screening_source_reviews.json',[dict(
            review_id='20261015/'+windows[k][0],reviewed_at=stamp,reviewer='assistant_visual_review',
            date='20261015',camera=m['source']['camera'],split='train',source_member=m['source']['member'],source_sha256=m['source_sha256'],
            frames_manifest=str(paths[k].relative_to(ROOT)),sampled_frames_visually_reviewed=len(m['samples']),reviewed_sheets=m['sheets'],
            review_scope='All chronological contact-sheet samples inspected, selected native images and separate ROI overlays reviewed. Not exhaustive native-frame viewing.',
            observation=notes[k],accepted_complete_cycle=False,
            clock_warning='Initial early/stale frames retained but excluded from alignment. No clock offset inferred from filenames or PTS.',
            visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],
                visible_camera_clock=t,clock_read_uncertainty_seconds=1,image=m['samples'][i]['image'],usable_for_clock_alignment=not(k!='origin' and i==0)) for i,t in clocks[k].items()])],'review_id')
    def ev(k,a,b): return evidence(metas[k],a,b,paths[k])
    oldpath=OUT/'sequence_review/20261015/next_origin_1011_cam11/frames.json'
    old=read(oldpath)
    assert old['source_sha256']==metas['origin']['source_sha256']
    shared=dict(date='20261015',split='train',reviewer='assistant_visual_review',reviewed_at=stamp,dataset_release_accepted=False)
    labels=read(OUT/'reviewed_sequence_labels.json')
    history=OUT/'review_history/sequence_labels_before_20261031_22.json'
    if not history.exists(): save(history,labels)
    beige=copy.deepcopy(next(r for r in labels if r['sequence_id']=='20261015_fresh_beige_departure_partial_1020'))
    beige.update(reviewed_at=stamp,missing_stages=['linked_entry_15','linked_scale_visit','linked_storage_placement'])
    beige['unlinked_followup'].update(
        scale_approach_camera11_interval=['10:21:41','10:21:51'],scale_occupancy_camera11_interval=['10:21:51','10:24:51'],
        platform_departure_camera11_interval=['10:25:01','10:25:21'],first_usable_already_parked_camera15='10:26:30',
        unloaded_fork_withdrawal_camera15_interval=['10:26:30','10:26:34'],scale_to_first_stored_view_gap_seconds=69,
        observation='Scale occupancy and later already parked beige are now reviewed; direct entry gap19 seconds and missing69-second scale-to-park route prevent full identity confirmation.')
    beige['unlinked_followup']['evidence'] += [ev('origin',0,23),ev('beige_storage',1,10),ev('beige_release',1,9)]
    beige.setdefault('revision_notes',[]).append('Batch22 extends later scale/storage observations without accepting a complete matched cycle. Original batch21 record archived.')
    gray=dict(shared,sequence_id='20261015_fresh_gray_departure_partial_1029',review_status='reviewed_partial_sequence',
        cycle_id=None,production_entry_count_target=None,camera_track_id={'11':'fresh_gray_station_1020_1029','15':'unlinked_gray_scale_route_1030_1035'},
        cross_camera_identity='unresolved_direct_entry_gap',camera_clock_offset_seconds=None,
        stages=[dict(stage='filling_observed',camera=11,visible_camera_clock_interval=['10:20:43','10:28:21'],clock_uncertainty_seconds=10,
            content_evidence='Distinct gray replacement receives cheese at station; fixed scrap receptacle separate.',evidence=[evidence(old,69,74,oldpath),ev('origin',0,41)]),
            dict(stage='loaded_departure_11',camera=11,visible_camera_clock_interval=['10:28:41','10:29:11'],doorway_intersection_observed_at='10:29:01',clock_uncertainty_seconds=10,evidence=[ev('origin',42,46)])],
        missing_stages=['linked_entry_15','linked_scale_visit','linked_storage_placement'],
        unlinked_followup=dict(last_camera15_before_entry_gap='10:28:58',first_usable_gray_on_platform_camera15='10:30:35',sampled_entry_gap_seconds=97,
            scale_camera11_interval=['10:30:11','10:34:21'],platform_departure_camera11_interval=['10:34:31','10:34:41'],
            later_gray_aisle_camera15_interval=['10:35:39','10:35:50'],platform_clear_to_first_route_sample_seconds=58,
            same_camera11_staging_edge_visible_through='10:35:41',storage_placement_observed=False,numeric_weight_kg=None,
            evidence=[ev('empty',8,9),ev('origin',51,86),ev('scale1',1,17),ev('scale2',1,14),ev('scale3',1,17),ev('route',1,7)],
            observation='Gray later on scale and in aisle; no direct room15 arrival and no parking/fork withdrawal in current source. Keep stage observations unlinked to fresh11 origin.'),
        limitations=['No production entry count or exact entry time assigned.','No camera clock offset or measured weight inferred.','White cover does not alone prove cheese.'])
    empty=dict(shared,sequence_id='20261015_empty_beige_return_1028',review_status='accepted_negative_sequence',
        cycle_id=None,production_entry_count_target=0,camera=15,camera_track_id='empty_beige_return_1028',negative_class='empty_crossing',tracked_tank_count=1,
        direction='15_to_11',visible_camera_clock_interval=['10:28:42','10:28:56'],clock_uncertainty_seconds=2,
        evidence=[ev('empty',1,9),ev('origin',45,47)],
        observation='Visibly empty beige return from15 waiting row throughdoor52-54, out56;beige replacement arrives at11 station29:01-21.',
        label_scope='Only empty return, excludes concurrent gray loaded departure and beige fresh filling beginning29:31.')
    inverted=dict(shared,sequence_id='20261015_inverted_upper_internal_two_trips_1030_1031',review_status='accepted_negative_sequence',
        cycle_id=None,production_entry_count_target=0,camera=15,negative_class='empty_tank_internal_reposition',tracked_tank_count=2,trip_count=2,
        camera_track_id=['inverted_upper_gray_trip_103043','inverted_upper_gray_trip_103143'],
        visible_camera_clock_interval=['10:30:43','10:31:55'],clock_uncertainty_seconds=2,
        evidence=[ev('scale1',5,10),ev('scale3',5,11)],
        tracks=[dict(track_id='inverted_upper_gray_trip_103043',movement_interval=['10:30:43','10:30:49'],unloaded_fork_retreat=['10:30:51','10:30:53']),
            dict(track_id='inverted_upper_gray_trip_103143',movement_interval=['10:31:43','10:31:49'],unloaded_fork_retreat=['10:31:51','10:31:55'])],
        observation='Two separate powered-jack internal trips place inverted upper gray tanks in foreground. Upright lower tank load states remain unknown.',
        label_scope='Only the two visibly inverted upper empty tanks. Not a zero label for lower tanks, room15 scale load or whole scene.')
    merge(OUT/'reviewed_sequence_labels.json',[beige,gray,empty,inverted],'sequence_id')

    queuepath=OUT/'sequence_followup_queue.json'
    queue=read(queuepath)
    history=OUT/'review_history/followup_queue_before_20261031_22.json'
    if not history.exists(): save(history,queue)
    revised=[]
    for r in queue:
        if r['candidate_id']=='20261015_beige_1020_entry_gap':
            r=copy.deepcopy(r)
            r.update(reviewed_at=stamp,status='reviewed_unresolved_coverage_gap',resolved_sequence_id=beige['sequence_id'],
                observation='Entry gap20:18-37 remains. Later platform21:41-25:21 and already parked26:30 reviewed;69-second route missing.',
                next_action='Retain partial; do not repeat unchanged entry/route windows without new coverage.')
            r['evidence'] += [ev('origin',0,23),ev('beige_storage',1,10)]
            revised.append(r)
        elif r['candidate_id']=='20261015_next_gray_after1020':
            r=copy.deepcopy(r)
            r.update(reviewed_at=stamp,status='resolved_to_reviewed_partial',resolved_sequence_id=gray['sequence_id'],
                observation='Fresh gray departure29:01 reviewed;15 direct entry lies in28:58-30:35 sample gap. Later scale/aisle retained unlinked.',
                next_action='Continue15 sources103623-103651 and103635-103704 for parking context only; missing direct entry remains explicit.')
            r['evidence'] += [ev('origin',40,46),ev('route',1,7)]
            revised.append(r)
    revised.append(dict(candidate_id='20261015_next_beige_departure_1037',date='20261015',split='train',cycle_id=None,production_entry_count_target=None,
        status='partial_followup_pending',reviewed_at=stamp,
        observation='Separate beige replacement receives cheese29:31-36:51, covered37:01,pulled37:11,gone37:21. Exact doorway intersection not sampled,15 counterpart not yet inspected.',
        next_action='Review adjacent11 source103726-104134 plus15 sources103715-103736 and103805-103827 onward. Do not infer camera linkage from filenames.',
        evidence=[ev('origin',48,95)]))
    merge(queuepath,revised,'candidate_id')
    save(OUT/'gap_search_20261031_22.json',dict(reviewed_at=stamp,day='20261015',split='train',findings=[
        'Beige20min origin remains partial:19-second direct15 arrival gap and69-second platform-clear to first already-stored view.',
        'Gray29min origin departs11 around29:01;15 sampled gap28:58-30:35 is97 seconds, no observed arrival.',
        'Gray platform clear34:41, right staging edge remains visible from11 through35:41;15 route first usable35:39 through35:50 shows no parking or fork withdrawal.',
        'Two foreground inverted-upper internal trips are separate from the scale load. Lower upright contents unknown.'],
        action='Keep incomplete/unlinked observations separate. No invented full cycle, clock offset or production entry total.'))

    registry=read(OUT/'object_review_decisions.json')
    history=OUT/'review_history/object_decisions_before_20261031_22.json'
    if not history.exists(): save(history,registry)
    decisions={r['id']:r for r in registry['reviews']}
    drafts={r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
    descriptions={
        '176':'Gray covered departure tank, isolated body; temporal native context inspected.',
        '177':'Visibly empty beige waiting tank, isolated ROI.',
        '178':'Covered beige fresh departure, isolated tank body.',
        '179':'Moving empty beige return; top-truncated ROI excludes rear storage row. Worker partly occludes left rim.',
        '180':'Gray aisle transit, top-truncated body-only ROI excludes rear storage tanks; slight operator occlusion on right.',
        '181':'Fixed beige scrap receptacle. Lower/right boundary partly occluded by conveyor; individual tank labelled without load-class inference.'}
    for ident,note in descriptions.items():
        assert ident not in decisions
        r=drafts[ident]
        decisions[ident]=dict(id=ident,image_sha256=r['sha256'],boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',load_state_reviewed=False,sequence_reviewed=False,
            instance_attributes=[dict(box_index=0,truncated=ident in ('179','180'),occluded=ident in ('179','180','181'),load_state='unknown_not_annotated')],
            evidence=[r['source_frame'],r['frames_manifest'],f'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_{20 if int(ident)<180 else 21}.jpg'],note=note)
    registry['reviews']=list(decisions.values())
    registry.setdefault('corrections',[]).append('Batch22:176-181 separately overlay-reviewed, six ROIs/six boxes. No prior decisions changed.')
    save(OUT/'object_review_decisions.json',registry)
    inv=read(BASE/'archive_inventory.json')
    inspected={m['source']['member']:m['source_sha256'] for m in metas.values()}
    for r in inv['records']:
        if r['member'] in inspected: r.update(pixel_inspected=True,sha256=inspected[r['member']])
    assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test')
    save(BASE/'archive_inventory.json',inv)
    reviews=read(OUT/'screening_source_reviews.json')
    total=sum(r['sampled_frames_visually_reviewed'] for r in reviews)
    added=sum(len(m['samples']) for m in metas.values())
    state['last_completed'] += [
        f'Batch22 inspected {added} chronological presentations in9 windows on15Oct; {total} total across {len({r["source_sha256"] for r in reviews})} sources and {len(reviews)} windows. Extractions complete;25/28Oct untouched.',
        '15Oct beige20min partial extended with scale and already-stored observations;69-second route gap retained. Fresh gray29min departure added as partial:97-second15 arrival gap; later scale/aisle unlinked and parking not shown. Totals5 complete,20 partials.',
        'Two negative episodes added:empty beige15-to11 return and two internal trips of inverted upper gray tanks. Lower upright tank contents unknown. Total54 negatives. Fresh beige37min departure queued separately.',
        'Six native ROI images176-181 and6 boxes approved after separate overlay review. Totals182 candidates,128 approved images,183 boxes,54 exclusions,zero drafts. Dataset unreleased.'
    ]
    state['priority_next']=[
        'Batch22 complete.5 complete cycles all13Oct; full-cycle day diversity and actual same-load reentry/post-storage relocation coverage still missing. Avoid accumulating only easy negatives.',
        '15Oct remaining1035 gray storage: inspect15 sources103623-103651/103635-103704 for parking, but97-second direct entry gap is unresolved. New beige37min departure:11 source103726-104134 and15 sources103715-103736/103805-103827 onward. Do not re-extract reviewed windows.',
        '13Oct next distinct load:11 sources093135-093311/093311-094655 and15 after093339 could support another full cycle, but prioritize day diversity.',
        '13Oct102139-102912 long15 source unreviewed;11 source gap10:00:12-25:11 may leave missing origin.'
    ]+[p for p in state['priority_next'] if p.startswith('Known gaps') or p.startswith('25/28') or p.startswith('Old21Oct')]
    state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    state['scripts'] += [s for s in ['work/append_tank_roi_batch_20261031_22.py','work/record_tank_sequence_batch_20261031_22.py'] if s not in state['scripts']]
    save(OUT/'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_samples=added,total_presentations=total,additional_complete_cycles=0,additional_partial_sequences=1,additional_negative_sequences=2,training_started=False)))


if __name__=='__main__': main()
