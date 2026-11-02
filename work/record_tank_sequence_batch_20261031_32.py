"""Record visually inspected6Oct morning evidence, retaining unseen stages."""
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read, save, merge, evidence

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/tank_transfer_training_v1'
OUT=BASE/'dataset_v1'
RUN='sequence_review_20261031_32'

def main():
    state=read(OUT/'continuation_state.json')
    if RUN in state.get('completed_curation_runs',[]):
        print('Already recorded',RUN);return
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    windows={
        'filling':('early_production_0729_cam11',66),
        'earlier15':('early_context_0737_cam15',38),
        'departure':('early_departure_0745_cam11',44),
        'after15':('early_after_departure_0745_cam15',27),
        'scale':('early_scale_0746_cam11',52),
    }
    paths={k:OUT/'sequence_review/20261006'/w/'frames.json' for k,(w,n) in windows.items()}
    metas={k:read(p) for k,p in paths.items()}
    for k,m in metas.items():
        assert m['source']['date']=='20261006' and m['source']['split']=='train'
        assert len(m['samples'])==windows[k][1]
    clocks={
        'filling':{0:'07:29:37',1:'07:29:54',5:'07:30:54',6:'07:31:09',9:'07:31:54',10:'07:32:09',11:'07:32:24',14:'07:33:09',17:'07:33:54',18:'07:34:09',23:'07:35:24',24:'07:35:39',25:'07:35:54',29:'07:36:54',30:'07:37:09',31:'07:37:24',35:'07:38:24',36:'07:38:39',41:'07:39:54',42:'07:40:09',47:'07:41:24',48:'07:41:39',49:'07:41:55',53:'07:42:54',54:'07:43:09',57:'07:43:55',58:'07:44:10',59:'07:44:25',60:'07:44:39',61:'07:44:55',62:'07:45:10',63:'07:45:24',64:'07:45:40',65:'07:45:55'},
        'earlier15':{0:'07:37:11',1:'07:37:25',5:'07:37:33',6:'07:37:35',11:'07:37:45',12:'07:37:47',17:'07:37:57',18:'07:37:59',23:'07:38:09',24:'07:38:11',29:'07:38:21',30:'07:38:23',31:'07:38:25',32:'07:38:27',33:'07:38:29',37:'07:38:37'},
        'departure':{0:'07:44:52',1:'07:44:53',5:'07:44:57',6:'07:44:58',7:'07:44:59',8:'07:45:00',11:'07:45:03',12:'07:45:04',14:'07:45:06',15:'07:45:07',16:'07:45:08',17:'07:45:09',18:'07:45:10',19:'07:45:11',20:'07:45:12',23:'07:45:15',24:'07:45:16',25:'07:45:17',26:'07:45:18',27:'07:45:19',28:'07:45:20',29:'07:45:21',30:'07:45:22',31:'07:45:23',32:'07:45:24',33:'07:45:25',38:'07:45:30',39:'07:45:31',43:'07:45:35'},
        'after15':{0:'07:45:51',1:'07:45:53',5:'07:45:57',6:'07:45:58',7:'07:45:59',8:'07:46:00',11:'07:46:03',12:'07:46:04',17:'07:46:09',18:'07:46:10',23:'07:46:15',26:'07:46:18'},
        'scale':{0:'07:45:54',1:'07:46:10',4:'07:46:25',5:'07:46:30',6:'07:46:35',8:'07:46:45',9:'07:46:50',11:'07:47:00',17:'07:47:30',23:'07:48:00',29:'07:48:30',35:'07:49:00',41:'07:49:30',42:'07:49:35',43:'07:49:40',44:'07:49:45',45:'07:49:50',46:'07:49:55',47:'07:50:00',51:'07:50:20'},
    }
    notes={
        'filling':'All66 chronological15s samples inspected. One station tank receives cheese throughout29:37-44:55, initially partly filled; initial quantity unknown. Separate scrap tank remains at right. Earlier covered tank is already on the scale29:37-30:54 and disappears by31:09; its origin is not this station load. Electric jack enters31:54; waiting empty tanks are repositioned32:09-33:09. Unloaded manual jack approaches35:54. Station load departs45:10 and separate empty replacement is at station45:24-40, receiving blocks by45:55. Departure boundary reviewed densely in a separate window. These are sampled observations, not frame-exhaustive continuity.',
        'earlier15':'All38 samples inspected. Initial37:11 is early, usable37:25-38:37. Yellow electric jack moves through room without a tank; native38:25 confirms unloaded forks. Operator at doorway handles surrounding containers; stationary covered foreground inventory and open left rows are not new entries. Blue tank visible beyond doorway is a room11 background tank, NOT a confirmed scale tank: paired11 views show scale clear at this time. No new-tank entry is established in this window. Do not use scene-wide zero labels.',
        'departure':'All44 one-second samples inspected. Cheese visible through45:03; workers place a broad white panel04-06. Same station body moves07-16, crosses doorway17-23 and is no longer visible24. A distinct visibly empty tank is pulled from waiting row16-23 and placed at filling station24-31; later filling is separate. Native45:04,12,17,23 inspected. Separate overlays approved for loaded body, threshold body, empty replacement and fixed scrap tank.',
        'after15':'All27 one-second samples inspected. Initial45:51 then usable45:53-46:18. Operator stands in occluded door staging behind fixed blue bins; pedestrian crosses46:00-09. Fresh load body/entry is not visible enough to verify identity. This source begins after11 crossing45:17-24. No actual room15 entry timestamp or new-entry count assigned. This is not a whole-room negative.',
        'scale':'All52 five-second samples inspected. Initial45:54 is early; next sample reads46:10. Scale clear through46:25, covered blue tank moves onto it46:30-35 and remains46:50-49:45. It moves off49:50, platform clear49:55. Content and identity cannot be established from blue cover alone. Station replacement independently receives cheese. Final camera-clock50:20 differs from filename end50:11, so filenames/PTS are explicitly not used as synchronization. Camera15 archive metadata has no following source until54:43, leaving storage route unverified.',
    }
    for k,m in metas.items():
        merge(OUT/'screening_source_reviews.json',[dict(review_id='20261006/'+windows[k][0],reviewed_at=stamp,
            reviewer='assistant_visual_review',date='20261006',camera=m['source']['camera'],split='train',
            source_member=m['source']['member'],source_sha256=m['source_sha256'],frames_manifest=str(paths[k].relative_to(ROOT)),
            sampled_frames_visually_reviewed=len(m['samples']),reviewed_sheets=m['sheets'],
            review_scope='All chronological sample sheets inspected, with selected native context and separately reviewed ROI overlays; not exhaustive native-frame viewing.',
            observation=notes[k],accepted_complete_cycle=False,
            clock_warning='Pixel clocks only; early initial frames, filenames and PTS do not establish camera synchronization or unseen trajectories.',
            visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],
                relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],visible_camera_clock=t,clock_read_uncertainty_seconds=1,
                image=m['samples'][i]['image'],usable_for_clock_alignment=False) for i,t in clocks[k].items()])],'review_id')
    def ev(k,a,b):return evidence(metas[k],a,b,paths[k])
    save(OUT/'review_history/sequence_labels_before_20261031_32.json',read(OUT/'reviewed_sequence_labels.json'))
    shared=dict(date='20261006',split='train',reviewer='assistant_visual_review',reviewed_at=stamp,dataset_release_accepted=False)
    partial=dict(shared,sequence_id='20261006_fresh_blue_departure_partial_0745',review_status='reviewed_partial_sequence',cycle_id=None,
        production_entry_count_target=None,camera_track_id={'11':'blue_station_departure0745'},camera_clock_offset_seconds=None,
        cross_camera_identity='Room11 fresh filling and departure verified; later blue scale body is not linked through the occluded/missing room15 entry and staging.',
        stages=[dict(stage='filling_observed',camera=11,visible_camera_clock_interval=['07:29:37','07:45:03'],
            content_evidence='Repeated visible cheese additions at station. Initial quantity unknown. Broad white panel placed45:04-06 after filling.',
            evidence=[ev('filling',0,61),ev('departure',0,14)]),
            dict(stage='loaded_departure_11',camera=11,visible_camera_clock_interval=['07:45:07','07:45:24'],doorway_interval=['07:45:17','07:45:24'],
                observation='Same station body pulled through threshold. Distinct empty station replacement tracked separately.',evidence=[ev('departure',15,32)]),
            dict(stage='entry_15',camera=11,visible_camera_clock_interval=['07:45:17','07:45:24'],room15_clock_interval=None,
                clock_basis='Physical passage from11 only; no calibrated camera15 entry timestamp.',evidence=[ev('departure',25,32)])],
        reviewed_followup_observations=[dict(stage='scale_visit',camera=11,visible_camera_clock_interval=['07:46:25','07:49:55'],
            placement_interval=['07:46:25','07:46:35'],departure_interval=['07:49:45','07:49:55'],same_load_identity_confirmed=False,numeric_weight_kg=None,
            observation='Covered blue tank appears on platform and later leaves. Fresh-origin identity is unverified across earlier hidden route; no weight read.',
            evidence=[ev('scale',4,46)])],
        missing_stages=['calibrated_room15_entry_timestamp','verified_entry_to_scale_identity','verified_scale_to_storage_identity','storage_placement'],
        limitations=['Room15 source starts45:51 after observed11 doorway crossing. Next inventoried15 source starts54:43 after platform departure; metadata is not continuous coverage.',
            'No full-cycle target, assumed camera offset, numeric weight or model-accuracy claim.'])
    negative=dict(shared,sequence_id='20261006_empty_blue_station_replacement_0745',review_status='accepted_negative_sequence',cycle_id=None,
        production_entry_count_target=0,camera=11,negative_class='empty_tank_internal_reposition',tracked_tank_count=1,
        direction='room11_waiting_area_to_station',visible_camera_clock_interval=['07:45:16','07:45:31'],evidence=[ev('departure',24,39)],
        observation='Empty lined body with visible bottom moves from waiting row to station while filled body exits. Later cheese additions excluded.',
        label_scope='Only the tracked empty local movement, not simultaneous loaded departure or later filling.')
    merge(OUT/'reviewed_sequence_labels.json',[partial,negative],'sequence_id')
    qp=OUT/'sequence_followup_queue.json';save(OUT/'review_history/followup_queue_before_20261031_32.json',read(qp))
    merge(qp,[dict(candidate_id='20261006_early_blue_departure0745',date='20261006',split='train',cycle_id=None,production_entry_count_target=None,
        status='resolved_as_partial_missing_entry_storage',reviewed_at=stamp,resolved_sequence_id=partial['sequence_id'],
        observation='Fresh station filling and11 departure45:17-24 verified.46:30-49:55 blue scale visit remains unlinked;15 source ends46:18 then next metadata starts54:43.',
        next_action='Retain partial. Do not repeatedly re-extract missing45min entry or49min storage from this archive; prioritise another paired source interval.',
        evidence=[ev('filling',0,61),ev('departure',15,32),ev('after15',0,26),ev('scale',4,46)]),
        dict(candidate_id='20261006_second_blue_filling_after0745',date='20261006',split='train',cycle_id=None,production_entry_count_target=None,
            status='needs_future_departure_context',reviewed_at=stamp,
            observation='Distinct replacement empty45:31, additions by45:55 and through50:20. Do not merge with departed45min load.',
            next_action='Only pursue if paired15 coverage is promising. Next11 source filename075011-080216 is not a reliable clock conversion.',
            evidence=[ev('departure',39,43),ev('filling',65,65),ev('scale',0,51)])],'candidate_id')
    registry=read(OUT/'object_review_decisions.json');save(OUT/'review_history/object_decisions_before_20261031_32.json',registry)
    decisions={r['id']:r for r in registry['reviews']}
    drafts={r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
    objnotes={'225':'Isolated station load moving toward door; physical body and feet visible.',
        '226':'Same loaded body at threshold; edge partly occluded by doorpost and foreground person.',
        '227':'Distinct empty station replacement, empty liner/bottom visible; bucket partly occludes right edge.',
        '228':'Separate fixed scrap tank; person and conveyor occlude lower/front body. Object class tank only, no productive-entry target.'}
    for ident,note in objnotes.items():
        assert ident not in decisions
        r=drafts[ident]
        decisions[ident]=dict(id=ident,image_sha256=r['sha256'],boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',load_state_reviewed=False,sequence_reviewed=False,
            instance_attributes=[dict(box_index=0,truncated=False,occluded=ident in ['226','227','228'],load_state='unknown_not_annotated')],
            evidence=[r['source_frame'],r['frames_manifest'],'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_28.jpg'],note=note)
    registry['reviews']=list(decisions.values())
    registry.setdefault('corrections',[]).append('Batch32:225-228 independently overlay-reviewed, four train images/four boxes. Physical body labels only; no load-state supervision inferred. Prior approvals preserved.')
    save(OUT/'object_review_decisions.json',registry)
    inv=read(BASE/'archive_inventory.json');inspected={m['source']['member']:m['source_sha256'] for m in metas.values()}
    for r in inv['records']:
        if r['member'] in inspected:r.update(pixel_inspected=True,sha256=inspected[r['member']])
    assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test')
    save(BASE/'archive_inventory.json',inv)
    reviews=read(OUT/'screening_source_reviews.json');total=sum(r['sampled_frames_visually_reviewed'] for r in reviews);added=sum(len(m['samples']) for m in metas.values())
    state['last_completed'] += [
        f'Batch32 inspected {added} chronological sample presentations in five6Oct morning windows; {total} total across {len({r["source_sha256"] for r in reviews})} sources and {len(reviews)} windows. Extractions finished; test pixels untouched.',
        'Fresh morning station load followed through45:17-24 doorway crossing. Blue scale visit46:30-49:55 not linked across unseen entry/staging/storage; one partial added. Five full cycles remain.',
        'One scoped empty station replacement added.73 negatives,30 partials. Native15 context confirms that stationary background tank visible through door is not the scale tank; no erroneous scale label saved.',
        'Four ROI images225-228/four boxes approved.229 candidates,173 approved images,232 boxes,56 exclusions and zero drafts. Dataset not released; no training.',
    ]
    state['priority_next']=[
        'Batch32 complete. Prioritise21Oct paired routes with longer15 coverage: metadata cluster10:40:41-10:44:41 contains seven source videos, still uninspected. Find corresponding11 filling/departure before accepting any route.',
        '21Oct15 prefix21.10/Camera_15_DVR_DVR_20261030172803/: sources104041_104100_12517961;104048_104112_12518713;104121_104154_12519711;104141_104208_12520450;104217_104309_12521455;104314_104354_12522232;104404_104441_12522985. Full filenames begin Camera_15_DVR_20261021 and include20261021 before end time. Metadata only, not continuity evidence.',
        '6Oct0745 partial retained:11 crossing45:17-24;15 only45:51-46:18 then54:43 onward.46:30-49:55 scale visit seen from11 but origin/storage identity unverified. Do not resample known gap.',
        '6Oct second blue station tank fills45:55-50:20; next11 source075011-080216 remains uninspected. Consider only with paired15 coverage; filename end of prior file differs from observed clock.',
    ]+[p for p in state['priority_next'] if p.startswith('Known gaps') or p.startswith('25/28') or p.startswith('Old21Oct') or p.startswith('6Oct17min') or p.startswith('8Oct11') or p.startswith('17Oct17min')]
    state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    state['scripts'] += [s for s in ['work/append_tank_roi_batch_20261031_32.py','work/record_tank_sequence_batch_20261031_32.py'] if s not in state['scripts']]
    save(OUT/'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_samples=added,total_presentations=total,additional_complete_cycles=0,additional_negative_sequences=1,additional_partial_sequences=1,training_started=False)))

if __name__=='__main__':main()
