"""Preserve reviewed 21 October midday observations without bridging missing video."""
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read, save, merge, evidence

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'outputs/tank_transfer_training_v1'
OUT = BASE / 'dataset_v1'
RUN = 'sequence_review_20261031_27'


def main():
    state = read(OUT / 'continuation_state.json')
    if RUN in state.get('completed_curation_runs', []):
        print('Already recorded', RUN)
        return
    stamp = dt.datetime.now(dt.timezone.utc).isoformat()
    windows = {
        'origin': ('midday_origin_1130_cam11',39),
        'context': ('midday_context_1135_cam11',26),
        'storage': ('midday_storage_1137_cam15',22),
        'detail': ('midday_door_detail_1131_cam11',33),
        'scale': ('midday_scale_1132_cam15',11),
        'empty15': ('midday_empty_return_1138_cam15',18),
        'empty11': ('midday_empty_return_1137_cam11',29),
    }
    paths = {k:OUT/'sequence_review/20261021'/w/'frames.json' for k,(w,n) in windows.items()}
    metas = {k:read(p) for k,p in paths.items()}
    for k,m in metas.items():
        assert m['source']['date']=='20261021' and m['source']['split']=='train'
        assert len(m['samples'])==windows[k][1]
    clocks = {
        'origin': {0:'11:30:05',1:'11:30:22',2:'11:30:30',3:'11:30:38',4:'11:30:46',5:'11:30:54',6:'11:31:02',7:'11:31:10',8:'11:31:18',9:'11:31:26',10:'11:31:34',11:'11:31:42',12:'11:31:50',13:'11:31:58',14:'11:32:06',17:'11:32:30',23:'11:33:18',30:'11:34:14',38:'11:35:18'},
        'context': {0:'11:35:47',1:'11:35:56',2:'11:36:00',3:'11:36:04',4:'11:36:08',5:'11:36:12',6:'11:36:16',7:'11:36:20',8:'11:36:24',9:'11:36:28',10:'11:36:33',11:'11:36:36',12:'11:36:40',16:'11:36:56',17:'11:37:01',21:'11:37:16',22:'11:37:20',23:'11:37:25',25:'11:37:33'},
        'storage': {0:'11:36:57',1:'11:37:17',2:'11:37:20',3:'11:37:23',4:'11:37:26',5:'11:37:29',6:'11:37:32',7:'11:37:35',8:'11:37:38',9:'11:37:41',10:'11:37:44',11:'11:37:47',12:'11:37:50',13:'11:37:53',14:'11:37:56',15:'11:37:59',16:'11:38:02',17:'11:38:05',18:'11:38:08',19:'11:38:11',20:'11:38:14',21:'11:38:17'},
        'detail': {0:'11:31:20',5:'11:31:25',6:'11:31:26',7:'11:31:27',8:'11:31:28',9:'11:31:29',10:'11:31:30',11:'11:31:31',12:'11:31:32',13:'11:31:33',14:'11:31:34',15:'11:31:35',20:'11:31:40',21:'11:31:41',22:'11:31:42',23:'11:31:43',24:'11:31:44',25:'11:31:45',26:'11:31:46',27:'11:31:47',28:'11:31:48',29:'11:31:49',30:'11:31:50',31:'11:31:51',32:'11:31:52'},
        'scale': {0:'11:32:02',1:'11:32:10',2:'11:32:12',3:'11:32:14',4:'11:32:16',5:'11:32:18',6:'11:32:20',7:'11:32:22',8:'11:32:24',9:'11:32:26',10:'11:32:28'},
        'empty15': {0:'11:38:20',1:'11:38:34',2:'11:38:36',3:'11:38:38',4:'11:38:40',5:'11:38:42',6:'11:38:44',7:'11:38:46',8:'11:38:48',9:'11:38:50',10:'11:38:52',11:'11:38:54',12:'11:38:56',13:'11:38:58',14:'11:39:00',15:'11:39:02',16:'11:39:04',17:'11:39:06'},
        'empty11': {0:'11:37:34',1:'11:37:37',2:'11:37:40',5:'11:37:49',8:'11:37:58',9:'11:38:01',12:'11:38:10',15:'11:38:19',18:'11:38:28',21:'11:38:37',23:'11:38:43',24:'11:38:46',25:'11:38:49',28:'11:38:58'},
    }
    notes = {
        'origin':'Initial30:05 frame precedes usable30:22. Beige production tank at filling station receives visible cheese pieces through31:18, then its top is covered and it is pulled away31:26. Another visibly empty beige basket is moved from left waiting area to the filling station31:26-34 and starts receiving cheese31:50 onward. First load appears on platform through door31:42-50 and stays through35:18. Yellow powered jack enters11 empty32:22-30 and remains parked by doorway. Fixed scrap tank is separate. Native samples9/10 confirm the two beige bodies and their different roles.',
        'detail':'Dense one-second samples of the31-minute departure, extracted from the same source as origin. Covered beige body approaches door31:27-29, crosses30-34, gone35. Platform still clear40; tank emerges from right inside15 at41-43, rolls onto platform44-48, settles49-50; empty forks withdrawn51-52. This is not a return crossing to11. Native sample11 also shows a different empty replacement moving within11. Clock is camera11, not a measured room15 entry timestamp.',
        'context':'Initial35:47 frame is early. Platform occupied by covered beige load at35:56 through36:24. It moves off platform36:28 and to right edge33; platform clear36:36 onward. Yellow jack remains stationary in11 until37:20, then moves empty into15 by25. Second beige tank continues filling in11 throughout. Missing camera15 route between scale departure and later storage movement is not supplied by this view.',
        'storage':'Initial36:57 frame is early; first usable37:17 already shows a covered beige tank emerging near the rear row/door. It travels across open aisle20-26, turns toward far-left end of rear storage row29-38, parked41; empty manual forks withdrawn44 and operator returns47-53. Native samples3/6/9/10 show the complete local storage motion and empty forks, including destination outside sheet crop. No identity bridge to earlier scale load is asserted across unobserved route. The yellow powered jack passes independently and carries no tank. Operator next selects an empty beige tank38:02-05 and moves it08-17 beside the separate empty blue-lined waiting tank; native17/19 show open interiors. Both remain in15; no doorway return is observed.',
        'scale':'Initial32:02 frame early. Usable32:10-28 shows operator working over the largely concealed far-right scale load. White panel is lifted10-12, operator continues at scale14-28. No readable numerical weight. Empty yellow powered jack crosses15-to11 at22-26, corresponding to independent jack seen in11. Foreground open blue-lined tank and empty gray/beige waiting baskets remain stationary.',
        'empty15':'Initial38:20 frame early. At usable38:34 the earlier empty beige and blue-lined baskets are stationary near foreground package stack. Operator moves a different empty gray waiting basket36-40 into the space beside the right wall/package stack, lowers it42-48, withdraws empty forks50-54, then walks toward door39:00-06 with no tank. This is internal repositioning, not new production and not a tank return through door. Name empty_return is search intent only. Native sample4 confirms distinct stationary beige/blue pair and largely occluded gray destination.',
        'empty11':'Camera11 continues37:34-38:58 with the second beige load being filled. Platform remains clear; later an empty gray body is visible behind the right doorway edge38:43 onward, consistent with internal15 repositioning, without crossing into11. No departure of the second filling tank during this window. Thus neither window name nor empty-looking doorway inventory is a new transfer event.',
    }
    for k,m in metas.items():
        merge(OUT/'screening_source_reviews.json',[dict(
            review_id='20261021/'+windows[k][0],reviewed_at=stamp,reviewer='assistant_visual_review',
            date='20261021',camera=m['source']['camera'],split='train',source_member=m['source']['member'],
            source_sha256=m['source_sha256'],frames_manifest=str(paths[k].relative_to(ROOT)),
            sampled_frames_visually_reviewed=len(m['samples']),reviewed_sheets=m['sheets'],
            review_scope='All chronological sampled sheets inspected, selected native full frames and separately rendered ROI overlays. Not exhaustive native-frame tracking.',
            observation=notes[k],accepted_complete_cycle=False,
            clock_warning='Early source-initial frames do not bridge missing footage. PTS and filenames do not calibrate the two clocks.',
            visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],
                relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],visible_camera_clock=t,
                clock_read_uncertainty_seconds=1,image=m['samples'][i]['image'],
                usable_for_clock_alignment=not(i==0 and k not in ['detail','empty11'])) for i,t in clocks[k].items()]
        )],'review_id')

    def ev(k,a,b):return evidence(metas[k],a,b,paths[k])
    labels=read(OUT/'reviewed_sequence_labels.json')
    save(OUT/'review_history/sequence_labels_before_20261031_27.json',labels)
    shared=dict(date='20261021',split='train',reviewer='assistant_visual_review',reviewed_at=stamp,dataset_release_accepted=False)
    partial=dict(shared,sequence_id='20261021_fresh_beige_departure_partial_1131',
        review_status='reviewed_partial_sequence',cycle_id=None,production_entry_count_target=None,
        camera_track_id={'11':'beige_filling_departure1131_scale1136','15':'unlinked_beige_storage1137'},
        camera_clock_offset_seconds=None,
        cross_camera_identity='Storage observation is explicitly unlinked; no complete-cycle identity assigned.',
        stages=[dict(stage='filling_observed',camera=11,visible_camera_clock_interval=['11:30:22','11:31:18'],
            content_evidence='Visible cheese handling into beige station tank before covering/departure. Starting contents and final mass unknown.',evidence=[ev('origin',1,8)]),
            dict(stage='loaded_departure_11',camera=11,visible_camera_clock_interval=['11:31:26','11:31:35'],
                doorway_interval=['11:31:30','11:31:35'],clock_uncertainty_seconds=1,
                observation='Loaded body passes through door; separate empty local replacement is excluded.',evidence=[ev('origin',6,10),ev('detail',6,15)]),
            dict(stage='entry_15',camera=11,visible_camera_clock_interval=['11:31:30','11:31:35'],
                clock_basis='Observed from camera11; room15 clock at crossing unavailable.',room15_clock_interval=None,
                observation='Physical room boundary crossed in direction11-to15. Do not report this camera11 interval as a calibrated camera15 entry time.',evidence=[ev('detail',9,15)]),
            dict(stage='scale_visit',camera=11,visible_camera_clock_interval=['11:31:41','11:36:33'],numeric_weight_kg=None,
                placement_interval=['11:31:44','11:31:52'],departure_interval=['11:36:24','11:36:36'],
                observation='Dense arrival onto scale and empty-fork withdrawal; later scale occupancy retained. Missing35:18-56 source boundary is not fabricated as continuous viewing. Camera15 operator work is partly concealed.',
                evidence=[ev('detail',21,32),ev('origin',12,38),ev('context',1,11),ev('scale',1,10)])],
        missing_stages=['linked_storage_placement','calibrated_room15_entry_timestamp'],
        unlinked_followup=dict(camera=15,visible_camera_clock_interval=['11:37:17','11:37:44'],
            storage_placement_observed=True,storage_confirmed_interval=['11:37:41','11:37:44'],
            cross_camera_same_load_confirmed=False,
            observation='Covered beige body is parked at far-left rear row and empty forks withdrawn. Earlier11 scale body leaves view36:33; usable15 sequence begins37:17. These different-camera clock readings are44 seconds apart nominally, not a calibrated elapsed time or proof of identity. No reviewed15 source bridges the route.',
            evidence=[ev('context',8,11),ev('storage',1,10)]),
        limitations=['No full-cycle production target assigned.', 'White cover alone does not prove cheese.', 'Initial stale images cannot fill the trajectory gap.'])
    negatives=[
        dict(shared,sequence_id='20261021_empty_beige_station_replacement_1131',review_status='accepted_negative_sequence',cycle_id=None,
            production_entry_count_target=0,camera=11,negative_class='empty_tank_internal_reposition',tracked_tank_count=1,
            direction='room11_waiting_area_to_filling_station',visible_camera_clock_interval=['11:31:26','11:31:34'],
            evidence=[ev('origin',9,10),ev('detail',9,14)],
            observation='Empty beige basket with visible perforated bottom is moved to station while a different loaded beige tank leaves.',
            label_scope='Only the empty replacement move; subsequent fresh filling and simultaneous loaded departure are not zero-labelled.'),
        dict(shared,sequence_id='20261021_empty_beige_internal_move_1138',review_status='accepted_negative_sequence',cycle_id=None,
            production_entry_count_target=0,camera=15,negative_class='empty_tank_internal_reposition',tracked_tank_count=1,
            direction='right_waiting_area_to_foreground_beside_blue_tank',visible_camera_clock_interval=['11:38:02','11:38:17'],
            evidence=[ev('storage',16,21)],
            observation='Open beige basket is pulled from waiting area and moved within15. Blue-lined tank is a separate pre-existing body.',
            label_scope='Selected beige body only, no doorway crossing and no new production entry.'),
        dict(shared,sequence_id='20261021_empty_gray_internal_move_1138',review_status='accepted_negative_sequence',cycle_id=None,
            production_entry_count_target=0,camera=15,negative_class='empty_tank_internal_reposition',tracked_tank_count=1,
            direction='waiting_area_to_right_wall_beside_package_stack',visible_camera_clock_interval=['11:38:34','11:38:54'],
            evidence=[ev('empty15',1,11)],
            observation='Visibly open gray basket moved36-40, lowered near wall42-48, empty forks withdrawn50-54. Destination partly occluded.',
            label_scope='Only this gray internal movement. Stationary beige/blue pair and all earlier production are excluded.'),
    ]
    merge(OUT/'reviewed_sequence_labels.json',[partial]+negatives,'sequence_id')
    queuepath=OUT/'sequence_followup_queue.json'
    save(OUT/'review_history/followup_queue_before_20261031_27.json',read(queuepath))
    merge(queuepath,[dict(candidate_id='20261021_midday_beige_storage_identity_gap',date='20261021',split='train',cycle_id=None,production_entry_count_target=None,
        status='resolved_to_reviewed_partial',reviewed_at=stamp,resolved_sequence_id=partial['sequence_id'],
        observation='Dense11 departure and scale evidence established.37min15 storage observed but route from scale missing. No full-cycle label.',
        next_action='Do not repeat this gap search without additional source coverage. Prioritise unreviewed8Oct paired sources and validation.',
        evidence=[ev('detail',6,32),ev('context',8,11),ev('storage',1,10)]),
        dict(candidate_id='20261021_next_beige_filling_after1131',date='20261021',split='train',cycle_id=None,production_entry_count_target=None,
        status='needs_future_departure_context',reviewed_at=stamp,
        observation='Second beige tank starts empty at31:34 and receives cheese through38:58; departure not in reviewed window.',
        next_action='If extending21Oct, inspect subsequent113858-115140 camera11 source with adjacent15 coverage; do not invent eventual departure.',
        evidence=[ev('origin',10,38),ev('context',1,25),ev('empty11',0,28)])],'candidate_id')
    save(OUT/'gap_search_20261031_27.json',dict(reviewed_at=stamp,day='20261021',
        findings=['Dense camera11 crossing31:30-35 and scale placement31:44-52 observed.',
            'Camera15 first usable scale context32:10; no inspected15 crossing at31min.',
            'Scale leaves11 view36:33; first usable15 storage transit37:17, clocks not calibrated.',
            'Native15 destination and empty-fork withdrawal37:41-44 proven, but same-load connection remains unknown.'],
        action='Preserve one partial and three scoped empty internal movements; no new complete-cycle target.'))

    registry=read(OUT/'object_review_decisions.json')
    save(OUT/'review_history/object_decisions_before_20261031_27.json',registry)
    decisions={r['id']:r for r in registry['reviews']}
    drafts={r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
    obj_notes={
        '201':'Covered production tank in open11 aisle, isolated clear body.',
        '202':'Different empty replacement basket at station; right edge and lower body occluded by worker/conveyor. Bottom crop reaches visible body edge.',
        '203':'Loaded doorway body partly occluded at right by door post.',
        '204':'Stationary open blue-lined waiting tank in15, distinct from moving beige tank.',
        '205':'Fixed gray scrap receptacle; worker and conveyor obscure lower/front edges. Only tank class annotated.',
    }
    for ident,note in obj_notes.items():
        assert ident not in decisions
        r=drafts[ident]
        decisions[ident]=dict(id=ident,image_sha256=r['sha256'],
            boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',
            load_state_reviewed=False,sequence_reviewed=False,
            instance_attributes=[dict(box_index=0,truncated=ident=='202',occluded=ident in ['202','203','205'],load_state='unknown_not_annotated')],
            evidence=[r['source_frame'],r['frames_manifest'],'outputs/tank_transfer_training_v1/detector_v1/sheets/'+('labels_25.jpg' if ident=='205' else 'labels_24.jpg')],note=note)
    registry['reviews']=list(decisions.values())
    registry.setdefault('corrections',[]).append('Batch27:201-205 separately overlay reviewed;202 lower boundary extended before acceptance. Five images/five boxes. Prior approvals preserved.')
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
        f'Batch27 inspected {added} chronological presentations in7 windows on21Oct; {total} total across {len({r["source_sha256"] for r in reviews})} sources and {len(reviews)} windows. All extraction finished;25/28Oct untouched.',
        '21Oct fresh beige31min crossing and scale placement/departure refined with one-second doorway samples.37min storage observed but unlinked across missing route. Totals5 complete cycles and26 partials; no guessed15 entry clock.',
        'Three internal empty movements accepted:11 replacement beige,15 beige waiting move,15 gray wall-side move. Totals65 negatives. No observed tank return in the two windows named empty_return.',
        'Five ROI images201-205 and five boxes separately approved. Totals206 candidates,151 approved images,210 boxes,55 exclusions,zero drafts. Training remains unreleased.'
    ]
    state['priority_next']=[
        'Batch27 complete.5 full cycles remain all13Oct; prioritise day-diverse full cycles and complete validation examples.65 negatives already cover many easy moves.',
        'Metadata-only8Oct candidate:8.10/Camera_15_DVR_DVR_20261030170333/Camera_15_DVR_20261008073700_20261008073824_10968527.mp4. Inspect paired11 and adjacent15 chronology for day-diverse production route. Other unreviewed8Oct15 candidates:114106-114229_11053253 and110350-110447_11041357. Filename spans/bytes do not prove continuity.',
        '21Oct11:31 beige partial: crossing31:30-35, scale placement44-52, scale departure36:24-36.37:17-44 storage is unlinked; do not repeat missing route search without additional media. Second beige filling31:34-38:58 may be followed later.',
    ]+[p for p in state['priority_next'] if p.startswith('Known gaps') or p.startswith('25/28') or p.startswith('Old21Oct') or p.startswith('6Oct17min')]
    state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    state['scripts'] += [s for s in ['work/append_tank_roi_batch_20261031_27.py','work/record_tank_sequence_batch_20261031_27.py'] if s not in state['scripts']]
    save(OUT/'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_samples=added,total_presentations=total,
        additional_complete_cycles=0,additional_partial_sequences=1,additional_negative_sequences=3,training_started=False)))


if __name__=='__main__':main()
