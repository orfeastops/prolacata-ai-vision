"""Record inspected15Oct sequences; no fabricated links across source gaps."""
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read, save, merge, evidence

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/tank_transfer_training_v1'
OUT=BASE/'dataset_v1'
RUN='sequence_review_20261031_30'

def main():
    state=read(OUT/'continuation_state.json')
    if RUN in state.get('completed_curation_runs',[]):
        print('Already recorded',RUN);return
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    windows={
        'origin':('late_origin_1230_cam11',56),
        'production':('late_production_1234_cam11',62),
        'before':('late_entry_1233_cam15',17),
        'entry':('late_entry_1234_cam15',24),
        'staging':('late_staging_1234_cam15',7),
        'scale':('late_scale_1235_cam15',9),
        'departure':('late_departure_1234_cam11',25),
        'transfer1':('late_transfer_1239_cam15',19),
        'transfer2':('late_transfer_1240_cam15',9),
        'storage':('late_storage_1241_cam15',24),
    }
    paths={k:OUT/'sequence_review/20261015'/w/'frames.json' for k,(w,n) in windows.items()}
    metas={k:read(p) for k,p in paths.items()}
    for k,m in metas.items():
        assert m['source']['date']=='20261015' and m['source']['split']=='train'
        assert len(m['samples'])==windows[k][1]
    clocks={
        'origin':{0:'12:29:42',5:'12:30:07',12:'12:30:42',18:'12:31:12',19:'12:31:17',20:'12:31:22',21:'12:31:27',24:'12:31:42',27:'12:31:57',30:'12:32:12',36:'12:32:42',40:'12:33:02',41:'12:33:07',42:'12:33:12',48:'12:33:42',51:'12:33:57',52:'12:34:02',53:'12:34:07',54:'12:34:12',55:'12:34:17'},
        'production':{0:'12:34:22',5:'12:35:02',12:'12:35:57',13:'12:36:05',14:'12:36:13',18:'12:36:46',24:'12:37:34',30:'12:38:22',36:'12:39:10',39:'12:39:34',40:'12:39:42',41:'12:39:50',48:'12:40:46',51:'12:41:10',55:'12:41:42',56:'12:41:50',57:'12:41:58',58:'12:42:06',61:'12:42:30'},
        'before':{0:'12:33:32',1:'12:33:48',7:'12:33:54',11:'12:33:58',16:'12:34:03'},
        'entry':{0:'12:34:14',1:'12:34:21',5:'12:34:25',10:'12:34:30',15:'12:34:35',20:'12:34:40',23:'12:34:43'},
        'staging':{0:'12:34:45',1:'12:34:53',2:'12:34:55',3:'12:34:57',4:'12:34:59',5:'12:35:01',6:'12:35:03'},
        'scale':{0:'12:35:36',1:'12:35:57',2:'12:35:59',3:'12:36:01',4:'12:36:03',5:'12:36:05',6:'12:36:07',7:'12:36:09',8:'12:36:11'},
        'departure':{0:'12:34:03',1:'12:34:03',2:'12:34:05',3:'12:34:06',4:'12:34:07',5:'12:34:08',6:'12:34:09',7:'12:34:10',8:'12:34:11',9:'12:34:11',10:'12:34:13',11:'12:34:14',12:'12:34:14',13:'12:34:16',14:'12:34:17',15:'12:34:17',16:'12:34:19',17:'12:34:20',18:'12:34:21',19:'12:34:22',20:'12:34:23',21:'12:34:24',22:'12:34:25',23:'12:34:26',24:'12:34:27'},
        'transfer1':{0:'12:39:22',1:'12:39:33',2:'12:39:36',3:'12:39:39',4:'12:39:42',5:'12:39:45',6:'12:39:48',10:'12:40:00',14:'12:40:12',17:'12:40:21',18:'12:40:24'},
        'transfer2':{0:'12:40:16',1:'12:40:30',2:'12:40:33',3:'12:40:36',4:'12:40:39',5:'12:40:42',6:'12:40:45',7:'12:40:48',8:'12:40:51'},
        'storage':{0:'12:40:53',1:'12:40:58',2:'12:41:00',3:'12:41:02',4:'12:41:04',8:'12:41:12',12:'12:41:20',15:'12:41:26',16:'12:41:28',17:'12:41:30',18:'12:41:32',19:'12:41:34',20:'12:41:36',21:'12:41:38',22:'12:41:40',23:'12:41:42'},
    }
    notes={
        'origin':'Gray production tank visibly receives cheese at foreground station29:42-34:02, then is covered and pulled away34:07-12; reaches doorway34:17. Different empty gray replacement moves from left waiting area into station at same time. Older covered gray already occupies scale29:42-31:17 and leaves31:22-27; this earlier scale body must not be merged with34min production. Empty manual jack returns33:02-12. Native54/55 show full departure body, separate empty replacement and fixed scrap tank.',
        'production':'This window begins after34min departure: foreground gray is the NEW replacement tank, which receives cheese34:22 onward. Scale clear34:22-35:57, covered gray moves onto scale36:05-13 and remains in sampled views through39:34; departing39:42, clear39:50. Native36:13 confirms scale body through doorway. Second filling tank stays at station through42:30. Returned empty gray appears left waiting area41:50 and empty jack is withdrawn41:58. Native41:58 confirms empty liner/interior and distinct foreground cheese-filled body. Earlier wording referring to one continuous foreground tank across34:17 would be incorrect; two physical loads are explicitly separated.',
        'before':'Initial33:32 is early. Usable33:48-34:03 shows no tank crossing; people move through doorway. This window precedes the actual34:14-19 crossing seen in11. It is an unsuccessful origin search, not a labelled negative whole-room interval.',
        'entry':'Initial34:14 is retained but early. First usable34:21 shows operator already beside largely occluded staged load beyond doorway. It remains there as operator works34:21-43. No direct room15 threshold crossing is available in usable sequence. Do not substitute camera11 clock for a calibrated camera15 entry timestamp.',
        'staging':'Initial34:45 precedes usable34:53. Operator works over largely hidden doorway-staged gray body34:53-35:03. Other people walk independently. Foreground inverted gray baskets and open blue-lined waiting basket are existing inventory. This is not another entry.',
        'scale':'Initial35:36 precedes usable35:57. Covered gray starts beside doorway, then is pushed to scale36:01-11, settling at far right. Movement visible behind blue bins. No numerical weight readable. Earlier staging ends35:03, so missing35:03-57 trajectory is retained rather than asserted as continuous identity.',
        'departure':'Dense one-second sampled review: cheese visible34:03-05, panel lowered06-07, loaded gray pulled away08-13. Body crosses room boundary14-17, fully disappears into15 by19. Different visibly empty gray replacement enters station14-21, first cheese placed22-27. Clock repeats03,11,14,17 across distinct PTS samples; preserve pixel readings and one-second read uncertainty instead of synthesizing a perfect clock.',
        'transfer1':'Initial39:22 early; usable39:33 onward. Gray scale body is pulled back toward doorway staging39:39-45, then waits partly occluded39:48-40:21. Other people cross aisle. At40:24 covered gray starts emerging toward open aisle. Static blue bins are not transferred tanks. Next source first usable40:30 leaves a six-second sampled join requiring denser review before uninterrupted identity claim.',
        'transfer2':'Initial40:16 early. Covered gray moves left through open aisle40:30-36, turns39-42, pushed toward open front end of rear storage row45-51. Native40:36 confirms visible body and white cover; cover alone is not proof of cheese. Next usable source40:58 starts after placement approach; native destination context is retained separately.',
        'storage':'Initial40:53 early. Covered gray parked at front-left end of rear row by40:58; operator withdraws empty forks41:00-02. Native41:00/02 confirms location outside prior sheet crop. Operator next collects DIFFERENT empty gray from waiting area, moves toward door41:26-36, partially concealed at doorway38-42. Native41:26 shows distinct moving body. Camera11 later41:50-58 shows empty waiting-body placement. No double production entry or same-load reentry is assigned.',
    }
    for k,m in metas.items():
        merge(OUT/'screening_source_reviews.json',[dict(review_id='20261015/'+windows[k][0],reviewed_at=stamp,
            reviewer='assistant_visual_review',date='20261015',camera=m['source']['camera'],split='train',
            source_member=m['source']['member'],source_sha256=m['source_sha256'],frames_manifest=str(paths[k].relative_to(ROOT)),
            sampled_frames_visually_reviewed=len(m['samples']),reviewed_sheets=m['sheets'],
            review_scope='All chronological sampled sheets inspected, selected native context and separate ROI overlays. Not exhaustive native-frame viewing.',
            observation=notes[k],accepted_complete_cycle=False,
            clock_warning='Visible pixel clocks only; initial early frames, filename overlaps and PTS do not prove continuous trajectories or synchronize cameras.',
            visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],
                relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],visible_camera_clock=t,clock_read_uncertainty_seconds=1,
                image=m['samples'][i]['image'],usable_for_clock_alignment=not(i==0 and m['source']['camera']==15)) for i,t in clocks[k].items()])],'review_id')
    def ev(k,a,b):return evidence(metas[k],a,b,paths[k])
    save(OUT/'review_history/sequence_labels_before_20261031_30.json',read(OUT/'reviewed_sequence_labels.json'))
    shared=dict(date='20261015',split='train',reviewer='assistant_visual_review',reviewed_at=stamp,dataset_release_accepted=False)
    partial=dict(shared,sequence_id='20261015_fresh_gray_departure_partial_1234',review_status='reviewed_partial_sequence',cycle_id=None,
        production_entry_count_target=None,camera_track_id={'11':'gray_filling_departure1234','15':'candidate_gray_staging_scale_storage1241'},
        camera_clock_offset_seconds=None,cross_camera_identity='Physical exit into15 observed from11. Later15 staging/scale/storage candidate retained without a full-cycle identity claim across gaps.',
        stages=[dict(stage='filling_observed',camera=11,visible_camera_clock_interval=['12:29:42','12:34:05'],
            content_evidence='Cheese blocks visibly placed into gray station tank before panel and departure. Starting contents/mass unknown.',evidence=[ev('origin',0,52),ev('departure',0,2)]),
            dict(stage='loaded_departure_11',camera=11,visible_camera_clock_interval=['12:34:08','12:34:19'],doorway_interval=['12:34:14','12:34:19'],
                observation='Same gray filling body pulled to threshold and disappears into15; empty replacement is separate.',evidence=[ev('departure',5,16)]),
            dict(stage='entry_15',camera=11,visible_camera_clock_interval=['12:34:14','12:34:19'],room15_clock_interval=None,
                clock_basis='Pixel clock on camera11; not a calibrated room15 timestamp.',evidence=[ev('departure',11,16)])],
        reviewed_followup_observations=[
            dict(stage='staging_candidate',camera=15,visible_camera_clock_interval=['12:34:21','12:35:03'],same_load_identity_confirmed=False,
                observation='Usable15 sequence starts after the physical crossing and staged load is mostly hidden.',evidence=[ev('entry',1,23),ev('staging',1,6)]),
            dict(stage='scale_visit',camera=15,visible_camera_clock_interval=['12:35:57','12:36:11'],same_load_identity_confirmed=False,numeric_weight_kg=None,
                placement_interval=['12:36:01','12:36:11'],observation='Staged covered gray body moves onto scale; prior staging route gap35:03-57 remains.',evidence=[ev('scale',1,8)]),
            dict(stage='scale_dwell_and_departure',camera=11,visible_camera_clock_interval=['12:36:13','12:39:50'],same_load_identity_confirmed=False,
                departure_interval=['12:39:34','12:39:50'],observation='Platform body occupied through39:34, moving39:42, clear39:50. Camera15 also shows departure39:39-45, with no assumed exact offset.',evidence=[ev('production',14,41),ev('transfer1',1,6)]),
            dict(stage='storage_placement',camera=15,visible_camera_clock_interval=['12:40:30','12:41:02'],same_load_identity_confirmed=False,
                storage_confirmed_interval=['12:40:58','12:41:02'],observation='Gray body approaches rear row and is parked; empty forks withdraw.40:24-30 and40:51-58 joins not yet reviewed densely; no full-cycle target assigned.',evidence=[ev('transfer1',17,18),ev('transfer2',1,8),ev('storage',1,3)]),
        ],missing_stages=['calibrated_room15_entry_timestamp','verified_staging_to_scale_identity','verified_scale_to_storage_joins'],
        limitations=['White panel is not cheese evidence by itself.','Initial early frames do not fill missing intervals.','No numeric weight or complete-cycle production target.'])
    negatives=[
        dict(shared,sequence_id='20261015_empty_gray_station_replacement_1234',review_status='accepted_negative_sequence',cycle_id=None,production_entry_count_target=0,
            camera=11,negative_class='empty_tank_internal_reposition',tracked_tank_count=1,direction='room11_waiting_area_to_station',
            visible_camera_clock_interval=['12:34:14','12:34:21'],evidence=[ev('departure',12,18),ev('origin',54,55)],
            observation='Distinct visibly empty lined basket moved locally to station while filled tank exits. Subsequent filling starts22-27.',
            label_scope='Empty local movement only, not simultaneous departure or subsequent cheese filling.'),
        dict(shared,sequence_id='20261015_empty_gray_waiting_placement_1241',review_status='accepted_negative_sequence',cycle_id=None,production_entry_count_target=0,
            camera=11,negative_class='empty_tank_internal_reposition',tracked_tank_count=1,direction='room11_aisle_to_waiting_position',
            visible_camera_clock_interval=['12:41:50','12:41:58'],evidence=[ev('production',56,57)],
            observation='Open empty lined gray tank lowered beside left wall; empty forks withdraw58. It is different from cheese-filled station tank.',
            label_scope='This local empty placement only. Earlier15 return candidate retained as context, not an independently counted second negative.'),
    ]
    merge(OUT/'reviewed_sequence_labels.json',[partial]+negatives,'sequence_id')
    qp=OUT/'sequence_followup_queue.json';save(OUT/'review_history/followup_queue_before_20261031_30.json',read(qp))
    merge(qp,[dict(candidate_id='20261015_gray1234_route_gaps',date='20261015',split='train',cycle_id=None,production_entry_count_target=None,
        status='reviewed_partial_with_boundary_joins_pending',reviewed_at=stamp,resolved_sequence_id=partial['sequence_id'],
        observation='Fresh11 departure14-19 and later15 staging/scale/storage observed.35:03-57 staging gap unresolved;40:24-30 and40:51-58 sampled source joins may be refined.',
        next_action='Check source coverage before further extraction. Adjacent file names alone do not fill the35min gap. Preserve all existing labels if gap cannot be closed.',
        evidence=[ev('departure',5,16),ev('staging',1,6),ev('scale',1,8),ev('transfer1',17,18),ev('transfer2',1,8),ev('storage',1,3)]),
        dict(candidate_id='20261015_next_gray_filling_after1234',date='20261015',split='train',cycle_id=None,production_entry_count_target=None,
            status='needs_future_departure_context',reviewed_at=stamp,
            observation='New gray starts empty34:21, receives cheese34:22-42:30 and remains at station. A jack is parked beside it42:06-14.',
            next_action='If continuing15Oct, inspect the next11 source and paired15 coverage after42:30; do not merge this load with34min departure.',
            evidence=[ev('departure',18,24),ev('production',0,61)])],'candidate_id')
    registry=read(OUT/'object_review_decisions.json');save(OUT/'review_history/object_decisions_before_20261031_30.json',registry)
    decisions={r['id']:r for r in registry['reviews']}
    drafts={r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
    obj_notes={'215':'Covered gray leaving filling station, isolated body.','216':'Different empty lined replacement; worker partly overlaps upper rim.',
        '217':'Gray scale tank through doorway; indicator/doorpost partly occlude left/front edges.',
        '218':'Covered gray in15 storage transit; top clipped by declared ROI, jack partly occludes lower-left body.',
        '219':'Returned empty gray waiting body in11, separate from filled station tank.'}
    for ident,note in obj_notes.items():
        assert ident not in decisions
        r=drafts[ident]
        decisions[ident]=dict(id=ident,image_sha256=r['sha256'],boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',load_state_reviewed=False,sequence_reviewed=False,
            instance_attributes=[dict(box_index=0,truncated=ident=='218',occluded=ident in ['216','217','218'],load_state='unknown_not_annotated')],
            evidence=[r['source_frame'],r['frames_manifest'],'outputs/tank_transfer_training_v1/detector_v1/sheets/'+('labels_26.jpg' if int(ident)<217 else 'labels_27.jpg')],note=note)
    registry['reviews']=list(decisions.values());registry.setdefault('corrections',[]).append('Batch30:215-219 separately overlay-reviewed; five train images/five boxes.218 top truncated. Prior approvals unchanged.')
    save(OUT/'object_review_decisions.json',registry)
    inv=read(BASE/'archive_inventory.json');inspected={m['source']['member']:m['source_sha256'] for m in metas.values()}
    for r in inv['records']:
        if r['member'] in inspected:r.update(pixel_inspected=True,sha256=inspected[r['member']])
    assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test')
    save(BASE/'archive_inventory.json',inv)
    reviews=read(OUT/'screening_source_reviews.json');total=sum(r['sampled_frames_visually_reviewed'] for r in reviews);added=sum(len(m['samples']) for m in metas.values())
    state['last_completed'] += [
        f'Batch30 inspected{added} chronological sample presentations in10 windows on15Oct; {total} total across{len({r["source_sha256"] for r in reviews})} sources and{len(reviews)} windows. Extractions finished;25/28Oct untouched.',
        '15Oct fresh gray34min departure refined to14-19. Later staged/scale/storage candidate retains explicit missing and unreviewed joins; one partial added, complete cycles remain5. Distinguish previous31min scale load and next station filling34:22 onward.',
        'Two scoped empty11 movements added:34min station replacement and41min waiting placement. Totals70 negatives,28 partials; no duplicate negative for candidate15 return.',
        'Five train ROI images215-219 and five boxes independently approved.220 candidates,165 approved images,224 boxes,55 exclusions,zero drafts. No training release.',
    ]
    state['priority_next']=[
        'Batch30 complete. Five full cycles remain all13Oct. Prioritise day-diverse full routes and validation; do not pad easy negatives.',
        '15Oct gray1234 partial:11 boundary14-19, usable15 starts21.35:03-57 staging gap; local storage parked40:58 with empty forks41:00-02. Source joins40:24-30 and40:51-58 can be densified if completing this candidate, but must not invent the35min route.',
        '15Oct second gray fills34:22-42:30. Read archive metadata for following11 source after124232 and paired15 sources; source names/PTS cannot establish synchronization.',
    ]+[p for p in state['priority_next'] if p.startswith('Known gaps') or p.startswith('25/28') or p.startswith('Old21Oct') or p.startswith('6Oct17min') or p.startswith('8Oct11') or p.startswith('17Oct17min')]
    state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    state['scripts'] += [s for s in ['work/append_tank_roi_batch_20261031_30.py','work/record_tank_sequence_batch_20261031_30.py'] if s not in state['scripts']]
    save(OUT/'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_samples=added,total_presentations=total,additional_complete_cycles=0,additional_negative_sequences=2,additional_partial_sequences=1,training_started=False)))

if __name__=='__main__':main()
