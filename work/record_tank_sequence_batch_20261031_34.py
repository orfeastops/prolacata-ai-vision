"""Persist inspected17Oct validation evidence, explicitly retaining route gaps."""
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read,save,merge,evidence

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/tank_transfer_training_v1'
OUT=BASE/'dataset_v1'
RUN='sequence_review_20261031_34'

def main():
    state=read(OUT/'continuation_state.json')
    if RUN in state.get('completed_curation_runs',[]):
        print('Already recorded',RUN);return
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    windows={'route':('noon_route_1209_cam15',23),'filling':('noon_filling_1202_cam11',38),
             'departure':('noon_departure_1203_cam11',37),'scale':('noon_scale_1209_cam11',31)}
    paths={k:OUT/'sequence_review/20261017'/w/'frames.json' for k,(w,n) in windows.items()}
    metas={k:read(p) for k,p in paths.items()}
    for k,m in metas.items():
        assert m['source']['date']=='20261017' and m['source']['split']=='validation'
        assert len(m['samples'])==windows[k][1]
    # Clocks transcribed from inspected sheet pixels, not calculated from PTS.
    clocks={
        'route':['12:09:49','12:10:11','12:10:15','12:10:17','12:10:20','12:10:24','12:10:26','12:10:29','12:10:32','12:10:35','12:10:38','12:10:41','12:10:44','12:10:47','12:10:50','12:10:53','12:10:56','12:11:00','12:11:02','12:11:05','12:11:08','12:11:12','12:11:14'],
        'filling':['12:02:34','12:03:02','12:03:12','12:03:22','12:03:32','12:03:42','12:03:52','12:04:02','12:04:12','12:04:22','12:04:32','12:04:42','12:04:52','12:05:02','12:05:13','12:05:23','12:05:33','12:05:43','12:05:53','12:06:03','12:06:13','12:06:23','12:06:33','12:06:43','12:06:53','12:07:03','12:07:13','12:07:23','12:07:33','12:07:43','12:07:53','12:08:03','12:08:13','12:08:23','12:08:33','12:08:43','12:08:53','12:09:03'],
        'departure':['12:03:20','12:03:21','12:03:22','12:03:23','12:03:24','12:03:25','12:03:26','12:03:27','12:03:28','12:03:29','12:03:30','12:03:31','12:03:32','12:03:33','12:03:34','12:03:35','12:03:36','12:03:37','12:03:38','12:03:39','12:03:40','12:03:41','12:03:42','12:03:43','12:03:44','12:03:45','12:03:46','12:03:47','12:03:48','12:03:49','12:03:50','12:03:51','12:03:52','12:03:53','12:03:54','12:03:55','12:03:56'],
        'scale':['12:09:01','12:09:16','12:09:21','12:09:26','12:09:31','12:09:36','12:09:41','12:09:46','12:09:51','12:09:56','12:10:01','12:10:06','12:10:11','12:10:16','12:10:21','12:10:26','12:10:31','12:10:36','12:10:41','12:10:46','12:10:51','12:10:56','12:11:01','12:11:06','12:11:11','12:11:16','12:11:21','12:11:26','12:11:31','12:11:36','12:11:41'],
    }
    notes={
        'route':'All23 samples inspected. Initial09:49 then10:11. Covered gray body already moving from scale-side area11-20, turns24-29 and is pushed into front-left end of back storage row32-35. Empty jack withdraws38-41, gray stays parked through11:14. Native10:20 inspected. Unseen onset and missing earlier trajectory prevent identifying this body as the03:40 departing load. Distinct beige empty body is collected from left by10:56, turned11:00-02 and moved toward room11 doorway05-08, partly hidden12-14. Native11:00 confirms empty interior. This is not a new production entry. Fixed covered stock remains distinct; white tops alone are not cheese labels.',
        'filling':'All38 samples inspected. Initial02:34 then03:02. Station gray tank contains visible cheese and receives additions before it is covered03:22-32 and departs03:42. Native03:02 inspected; initial contents unknown. A distinct empty gray returns through doorway03:12 and waits left; same replacement is moved to station03:44-49 in dense follow-up, then filled from03:50 onward through09:03. Do not merge the two loads. Platform through doorway clear04:52; covered gray on it05:02 through09:03. Its route from the earlier departure is hidden, so scale visit remains unlinked. Fixed beige scrap tank at right is separate.',
        'departure':'All37 one-second samples inspected, pixel clocks03:20-56. Station gray covered at20; jack approaches26-32, pulls body33-39, reaches threshold40, passes41-43 and is absent44. Native38 inspected. Distinct empty gray at left is moved44-48, parked49; cheese starts being added50 onward. Native46 confirms empty bottom. Negative label ends49 and does not include later filling. Room15 metadata ends03:16 then next source starts09:50; no unseen entry or clock offset invented.',
        'scale':'All31 samples inspected. Initial09:01 then09:16. Covered gray remains on platform through21, moves off right26, clear31 onward. Later room15 first usable10:11 is after an unobserved route; no cross-camera identity asserted. Station replacement continues filling through10:56, with a white panel placed11:01-06. First empty beige returns through doorway11:16 and moves left21; native16 confirms empty lined bottom. Separate pair of empty beige bodies returns36 and is left41; this later pair is screening only. Station gray remains in place through41 with jack approaching; its future departure not inspected.',
    }
    for k,m in metas.items():
        assert len(clocks[k])==len(m['samples'])
        merge(OUT/'screening_source_reviews.json',[dict(review_id='20261017/'+windows[k][0],reviewed_at=stamp,
            reviewer='assistant_visual_review',date='20261017',camera=m['source']['camera'],split='val',
            source_member=m['source']['member'],source_sha256=m['source_sha256'],frames_manifest=str(paths[k].relative_to(ROOT)),
            sampled_frames_visually_reviewed=len(m['samples']),reviewed_sheets=m['sheets'],
            review_scope='All chronological sampled sheets inspected with selected native frames and separate ROI overlays. Not exhaustive native-frame viewing. Validation only; no training or tuning.',
            observation=notes[k],accepted_complete_cycle=False,
            clock_warning='Only transcribed pixel clocks. Initial frame jumps, filenames and PTS do not establish synchronization.',
            visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],
                visible_camera_clock=t,clock_read_uncertainty_seconds=1,image=m['samples'][i]['image'],usable_for_clock_alignment=False) for i,t in enumerate(clocks[k])])],'review_id')
    def ev(k,a,b):return evidence(metas[k],a,b,paths[k])
    save(OUT/'review_history/sequence_labels_before_20261031_34.json',read(OUT/'reviewed_sequence_labels.json'))
    shared=dict(date='20261017',split='val',reviewer='assistant_visual_review',reviewed_at=stamp,dataset_release_accepted=False,cycle_id=None,camera_clock_offset_seconds=None)
    partial=dict(shared,sequence_id='20261017_gray_noon_departure1203_partial',review_status='reviewed_partial_sequence',production_entry_count_target=None,
        camera_track_id={'11':'gray_station_load1203','15':None},
        stages=[dict(stage='filling_observed',camera=11,visible_camera_clock_interval=['12:02:34','12:03:02'],initial_contents_unknown=True,evidence=[ev('filling',0,1)]),
            dict(stage='loaded_departure_11',camera=11,visible_camera_clock_interval=['12:03:33','12:03:44'],evidence=[ev('departure',13,24)]),
            dict(stage='entry_15',camera=11,visible_camera_clock_interval=['12:03:40','12:03:44'],room15_clock_interval=None,
                clock_basis='Physical doorway passage seen from11 only; no calibrated room15 timestamp.',evidence=[ev('departure',20,24)])],
        reviewed_followup_observations=[dict(stage='scale_visit',camera=11,placement_interval=['12:04:52','12:05:02'],visible_camera_clock_interval=['12:05:02','12:09:21'],
            departure_interval=['12:09:21','12:09:31'],same_load_identity_confirmed=False,numeric_weight_kg=None,
            observation='Covered gray scale body; hidden origin prevents linking it to03:40 departure.',evidence=[ev('filling',12,37),ev('scale',0,4)]),
            dict(stage='storage_placement',camera=15,visible_camera_clock_interval=['12:10:11','12:10:41'],placement_interval=['12:10:32','12:10:41'],
                same_load_identity_confirmed=False,observation='Gray body is parked and empty forks withdraw. Onset already underway at first usable sample; no verified link to scale or fresh03:40 load.',evidence=[ev('route',1,11)])],
        missing_stages=['calibrated_room15_entry_timestamp','verified_entry_to_scale_identity','verified_scale_to_storage_identity'],
        limitations=['15 inventory ends12:03:16 then resumes filename12:09:50; pixel initial09:49 and first usable10:11. This is not continuous coverage.',
            'Covered gray scale and storage bodies remain unlinked observations, not extra counted loads. No full-cycle target or weight.'])
    replacement=dict(shared,sequence_id='20261017_empty_gray_station_replacement1203',review_status='accepted_negative_sequence',production_entry_count_target=0,
        camera=11,negative_class='empty_tank_internal_reposition',tracked_tank_count=1,direction='room11_waiting_area_to_station',
        visible_camera_clock_interval=['12:03:44','12:03:49'],observation='Empty lined bottom visible during local replacement. Cheese additions begin50 and are excluded.',
        label_scope='Only empty replacement, not simultaneous departing filled tank or subsequent filling.',evidence=[ev('departure',24,29)])
    returning=dict(shared,sequence_id='20261017_empty_beige_return1211',review_status='accepted_negative_sequence',production_entry_count_target=0,
        negative_class='empty_crossing',tracked_tank_count=1,direction='room15_to_room11',
        camera_track_id={'15':'empty_beige_return1211','11':'empty_beige_return1211'},visible_camera_clock_intervals={'15':['12:10:56','12:11:14'],'11':['12:11:11','12:11:21']},
        cross_camera_identity='Corresponding single beige body, direction, empty interior, order and operator approach/exit support correspondence; no exact offset fitted.',
        observation='Single empty beige returns and is pulled left. Separate later pair at11:36 is not part of this track.',
        label_scope='Only this return. Simultaneous station load and existing stored tanks are separate.',evidence=[ev('route',16,22),ev('scale',24,26)])
    merge(OUT/'reviewed_sequence_labels.json',[partial,replacement,returning],'sequence_id')
    qp=OUT/'sequence_followup_queue.json';queue=read(qp);save(OUT/'review_history/followup_queue_before_20261031_34.json',queue)
    for r in queue:
        if r['candidate_id']=='20261021_gray_station_departure1051':
            r.update(reviewed_at=stamp,status='no_peer_gap_bridge_in_old_collection',
                metadata_search='Older Facility_Camera_Videos/2026-10-21/Camera_15 also ends105007-105040 then resumes110239-110325. Metadata only; no old-collection pixels inspected.',
                next_action='Do not resample absent1051 route. Dense11 departure may support a partial, but available15 collection cannot establish the complete cycle.')
    save(qp,queue)
    merge(qp,[dict(candidate_id='20261017_noon_gray1203',date='20261017',split='val',reviewed_at=stamp,status='resolved_as_partial_missing_route',
        resolved_sequence_id=partial['sequence_id'],cycle_id=None,production_entry_count_target=None,
        observation='Fresh filling/exit03:40-44 verified; scale05:02-09:21 and storage10:32-41 unlinked across missing route.',
        next_action='Retain validation partial. Do not repeat missing03min entry or09min scale-to-storage search without new media.',evidence=[ev('departure',20,24),ev('scale',0,4),ev('route',1,11)]),
        dict(candidate_id='20261017_second_gray_noon1211',date='20261017',split='val',reviewed_at=stamp,status='needs_future_departure_context',cycle_id=None,production_entry_count_target=None,
            observation='Distinct gray replacement filled from03:50 through10:56, covered11:01-06; jack approaches11:41.',
            next_action='Next bounded11 source120901-121455 afterPTS150 may show departure. Check15 available coverage first: source121115-121138 then121519-121551 then121737-121800. Validation only.',
            evidence=[ev('departure',30,36),ev('scale',5,30)])],'candidate_id')
    registry=read(OUT/'object_review_decisions.json');save(OUT/'review_history/object_decisions_before_20261031_34.json',registry)
    decisions={r['id']:r for r in registry['reviews']};drafts={r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
    objnotes={'234':'Top-truncated gray physical body in15 aisle. Initial storage and load identity are not encoded in object class.',
        '236':'Gray tank departing station toward doorway; complete body and feet visible.',
        '237':'Separate empty gray local replacement; hands partially occlude upper rim.',
        '238':'Single empty beige returning through doorway; arm and doorpost partly occlude right edge.'}
    for ident,note in objnotes.items():
        assert ident not in decisions;r=drafts[ident]
        decisions[ident]=dict(id=ident,image_sha256=r['sha256'],boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',load_state_reviewed=False,sequence_reviewed=False,
            instance_attributes=[dict(box_index=0,truncated=ident=='234',occluded=ident in ['234','237','238'],load_state='unknown_not_annotated')],
            evidence=[r['source_frame'],r['frames_manifest'],'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_'+('30' if ident=='238' else '29')+'.jpg'],note=note+' Validation only; no training/tuning.')
    registry['reviews']=list(decisions.values());r=drafts['235']
    registry.setdefault('excluded_roi_reviews',[]).append(dict(id='235',image_sha256=r['sha256'],reviewed_at=stamp,reviewer='assistant_visual_review',
        decision='exclude_whole_roi_not_an_empty_image',reason='Uncertain stationary background-stock sliver at upper crop edge; exclude whole ROI instead of omitting an instance.',evidence=[r['image'],r['source_frame'],r['frames_manifest']]))
    registry.setdefault('corrections',[]).append('Batch34: four validation ROI images/four boxes separately overlay-reviewed;235 excluded. Existing approvals preserved. No load attributes inferred from white covers.')
    save(OUT/'object_review_decisions.json',registry)
    inv=read(BASE/'archive_inventory.json');inspected={m['source']['member']:m['source_sha256'] for m in metas.values()}
    for r in inv['records']:
        if r['member'] in inspected:r.update(pixel_inspected=True,sha256=inspected[r['member']])
    assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test');save(BASE/'archive_inventory.json',inv)
    reviews=read(OUT/'screening_source_reviews.json');total=sum(r['sampled_frames_visually_reviewed'] for r in reviews);added=sum(len(m['samples']) for m in metas.values())
    state['last_completed'] += [
        f'Batch34 reviewed {added} sample presentations in four17Oct validation windows; {total} total across {len({r["source_sha256"] for r in reviews})} sources and {len(reviews)} windows. All extraction finished; test pixels untouched.',
        '17Oct03:40-44 gray departure added as validation partial. Covered scale visit05:02-09:21 and storage10:32-41 remain unlinked. Five complete cycles unchanged;31 partials.',
        'Two scoped validation negatives added:03:44-49 empty replacement and11min single beige return.77 negatives total; later empty pair screening only.',
        'Older21Oct collection metadata confirms1051 peer gap, so do not repeat that search. Four ROI images/four boxes approved,235 excluded:239 candidates,181 approved,242 boxes,58 exclusions,zero drafts. No training release.',
    ]
    state['priority_next']=[
        'Batch34 complete. Prioritise fresh complete routes on training days other than13Oct and17Oct validation. Easy negatives already77; do not repeat known missing routes.',
        '17Oct noon03min partial:11 departure03:40-44, scale05:02-09:21 clears09:31;15 onlyfirstusable10:11 thenstorage10:32-41. Missing entry and scale-to-storage trajectory prevent full-cycle identity. Do not resample absent media.',
        '17Oct secondgrayload: filled03:50-10:56 and covered11:01-06; jackapproaches11:41. Remaining11 source120901-121455 afterPTS150 uninspected.15 metadata121115-121138 then121519-121551 and121737-121800. Check peer coverage before extraction; validation only.',
        '21Oct oldcollection search now also fails1051 bridge: ends105040, resumes110239. Avoid repeating metadata search.11 dense boundary still uninspected but can at most support partial without new media.',
    ]+[p for p in state['priority_next'] if p.startswith('Known gaps') or p.startswith('25/28') or p.startswith('6Oct') or p.startswith('8Oct11') or p.startswith('17Oct17min') or p.startswith('21Oct beige')]
    state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    state['scripts'] += [s for s in ['work/append_tank_roi_batch_20261031_34.py','work/record_tank_sequence_batch_20261031_34.py'] if s not in state['scripts']]
    save(OUT/'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_samples=added,total_presentations=total,additional_complete_cycles=0,additional_negative_sequences=2,additional_partial_sequences=1,training_started=False)))

if __name__=='__main__':main()
