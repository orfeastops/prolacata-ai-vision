"""Persist inspected21Oct empty returns and resumed filling, without inventing joins."""
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read, save, merge, evidence

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/tank_transfer_training_v1'
OUT=BASE/'dataset_v1'
RUN='sequence_review_20261031_33'

def main():
    state=read(OUT/'continuation_state.json')
    if RUN in state.get('completed_curation_runs',[]):
        print('Already recorded',RUN);return
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    windows={
        'earlier11':('midday_context_1040_cam11',13),
        'pair15':('midday_context_1040_cam15',7),
        'gray15':('midday_context_1042_cam15',21),
        'beige15':('midday_context_1043_cam15',18),
        'pair11':('midday_returns_1041_cam11',20),
        'beige11':('midday_returns_1043_cam11',23),
        'filling':('midday_filling_1044_cam11',39),
    }
    paths={k:OUT/'sequence_review/20261021'/w/'frames.json' for k,(w,n) in windows.items()}
    metas={k:read(p) for k,p in paths.items()}
    for k,m in metas.items():
        assert m['source']['date']=='20261021' and m['source']['split']=='train'
        assert len(m['samples'])==windows[k][1]
    clocks={
        'earlier11':{0:'10:39:55',1:'10:40:08',2:'10:40:12',3:'10:40:16',4:'10:40:20',5:'10:40:24',6:'10:40:28',7:'10:40:32',8:'10:40:36',9:'10:40:40',10:'10:40:44',11:'10:40:48',12:'10:40:52'},
        'pair15':{0:'10:40:47',1:'10:41:01',2:'10:41:03',3:'10:41:05',4:'10:41:07',5:'10:41:09',6:'10:41:11'},
        'gray15':{0:'10:42:17',1:'10:42:29',2:'10:42:31',5:'10:42:37',6:'10:42:39',7:'10:42:41',11:'10:42:49',12:'10:42:51',14:'10:42:55',15:'10:42:57',16:'10:42:59',17:'10:43:01',18:'10:43:03',19:'10:43:05',20:'10:43:07'},
        'beige15':{0:'10:43:13',1:'10:43:20',2:'10:43:22',5:'10:43:28',6:'10:43:30',7:'10:43:32',8:'10:43:34',9:'10:43:36',10:'10:43:38',11:'10:43:40',12:'10:43:42',13:'10:43:44',14:'10:43:46',15:'10:43:48',16:'10:43:50',17:'10:43:52'},
        'pair11':{0:'10:40:50',1:'10:41:10',2:'10:41:12',3:'10:41:14',4:'10:41:16',5:'10:41:18',6:'10:41:20',7:'10:41:22',8:'10:41:24',9:'10:41:26',10:'10:41:28',11:'10:41:30',12:'10:41:32',13:'10:41:34',14:'10:41:36',15:'10:41:38',16:'10:41:40',17:'10:41:42',18:'10:41:44',19:'10:41:46'},
        'beige11':{0:'10:43:14',1:'10:43:34',2:'10:43:36',3:'10:43:38',4:'10:43:40',5:'10:43:42',6:'10:43:44',7:'10:43:46',8:'10:43:48',9:'10:43:50',10:'10:43:52',11:'10:43:54',12:'10:43:56',13:'10:43:58',14:'10:44:00',15:'10:44:02',16:'10:44:04',17:'10:44:06',18:'10:44:08',19:'10:44:10',20:'10:44:12',21:'10:44:14',22:'10:44:16'},
        'filling':{0:'10:44:18',1:'10:44:44',2:'10:44:59',3:'10:45:14',4:'10:45:29',5:'10:45:44',6:'10:45:59',7:'10:46:14',8:'10:46:29',9:'10:46:44',10:'10:46:59',11:'10:47:14',12:'10:47:29',13:'10:47:44',14:'10:47:59',15:'10:48:14',16:'10:48:29',17:'10:48:44',18:'10:48:59',19:'10:49:14',20:'10:49:29',21:'10:49:44',22:'10:49:59',23:'10:50:14',24:'10:50:30',25:'10:50:45',26:'10:51:00',27:'10:51:15',28:'10:51:30',29:'10:51:45',30:'10:52:00',31:'10:52:15',32:'10:52:30',33:'10:52:45',34:'10:53:00',35:'10:53:15',36:'10:53:30',37:'10:53:45',38:'10:54:00'},
    }
    notes={
        'earlier11':'All13 samples inspected. Initial39:55 then40:08. Beige/gray empty pair already emerging through doorway08-12, pushed left12-16; worker repositions gray28 then exits crop32. Station gray body with a white layer/panel remains stationary and nobody fills it. Separate scrap tank remains right. This earlier pair is NOT the later41min pair. Its first crossing boundary is not observed; retain screening only.',
        'pair15':'All7 samples inspected. Initial40:47 then41:01. Beige/gray pair is pushed toward room11 doorway01-09, last gray body partly hidden at11. Stationary covered tanks are opening inventory, not new entries. Counterpart11 shows the distinct empty gray and beige bodies emerging10-14 and pushed left16. No room15 production entry is counted. Clocks are observed intervals, not an assumed synchronized exact time.',
        'gray15':'All21 samples inspected. Initial42:17 then42:29. Worker leaves doorway29-35; gray body at left edge41. Pedestrian walks toward doorway43-51. Two adjacent gray bodies arrive from left55, move toward doorway57-59 and are guided into obscured threshold43:01-07. Camera11 source starts with two gray tanks already at left at43:14, followed by a gap to34; no dense counterpart reviewed. Keep this third movement as screening, without a new accepted sequence or cross-camera identity assertion.',
        'beige15':'All18 samples inspected. Initial43:13 then43:20. Worker walks left20-28, collects two beige bodies30-32, turns them34-38 and pushes toward doorway40-46. Pair passes behind fixed bins48-52. Native32 and40 frames inspected. Camera11 counterpart shows two matching empty beige bodies emerging48-54 and moved to waiting row56-44:04. This is an empty return, not new filling or production. Avoid counting later local repositioning again.',
        'pair11':'All20 samples inspected. Initial40:50 then41:10. Gray/beige pair crosses from15 into11 at10-14, pushed left16 and out of crop18. Native14 confirms both empty lined bottoms. Worker moves trays at station24-34; these actions do not demonstrate a new tank entry. Stationary left waiting row and scrap tank remain distinct. No filling-to-storage cycle here.',
        'beige11':'All23 samples inspected. Initial43:14 shows prior gray pair already left; next sample43:34. Door clear46, beige edge48, first body50, two bodies52, both clear54. Empty bottoms visible as pair turns56-58, moves to waiting row44:00-04; parked through16. Native52 and58 inspected. Returning and locally re-parking this pair is one scoped negative episode, not multiple production entries.',
        'filling':'All39 chronological15s samples inspected. Initial44:18 then44:44. Further empty pairs return at44:44,45:29 and46:29; these sparse observations are screening only. Station gray tank begins receiving visible cheese by45:14, with repeated additions through50:30. Cover/panel is visible50:45-51:00; by51:15 a different empty beige tank is at station, and a covered gray body is seen at scale51:30-54:00. Sparse samples do not establish exact departure, threshold, or continuous same-load identity through the blind interval. Beige replacement receives cheese51:30 onward. Native50:30 and51:15 inspected. Camera15 metadata ends50:40 then resumes11:02:39, leaving entry/storage coverage unresolved; do not invent a full-cycle label.',
    }
    for k,m in metas.items():
        merge(OUT/'screening_source_reviews.json',[dict(review_id='20261021/'+windows[k][0],reviewed_at=stamp,
            reviewer='assistant_visual_review',date='20261021',camera=m['source']['camera'],split='train',
            source_member=m['source']['member'],source_sha256=m['source_sha256'],frames_manifest=str(paths[k].relative_to(ROOT)),
            sampled_frames_visually_reviewed=len(m['samples']),reviewed_sheets=m['sheets'],
            review_scope='All chronological sample sheets inspected, with selected native frames and separate ROI overlays. Sampling is not exhaustive native-frame viewing.',
            observation=notes[k],accepted_complete_cycle=False,
            clock_warning='Pixel clocks only. Early initial frames, filenames and PTS do not establish synchronization or unseen trajectory continuity.',
            visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],
                relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],visible_camera_clock=t,clock_read_uncertainty_seconds=1,
                image=m['samples'][i]['image'],usable_for_clock_alignment=False) for i,t in clocks[k].items()])],'review_id')
    def ev(k,a,b):return evidence(metas[k],a,b,paths[k])
    save(OUT/'review_history/sequence_labels_before_20261031_33.json',read(OUT/'reviewed_sequence_labels.json'))
    shared=dict(date='20261021',split='train',reviewer='assistant_visual_review',reviewed_at=stamp,dataset_release_accepted=False,
        review_status='accepted_negative_sequence',cycle_id=None,production_entry_count_target=0,negative_class='empty_crossing',
        tracked_tank_count=2,direction='room15_to_room11',camera_clock_offset_seconds=None,
        label_scope='Only this tracked returning pair. Not a whole-room zero label, and local repositioning is not counted again.')
    pair=dict(shared,sequence_id='20261021_empty_gray_beige_pair_return_1041',
        camera_track_id={'15':['gray_return1041','beige_return1041'],'11':['gray_return1041','beige_return1041']},
        visible_camera_clock_intervals={'15':['10:41:01','10:41:11'],'11':['10:41:10','10:41:18']},
        cross_camera_identity='Pair composition, direction, order, uninterrupted observed approach/exit and matching operator action support the correspondence; no exact offset fitted.',
        observation='Two empty bodies pushed together from15 into11. Both empty interiors confirmed in native11 frame41:14.',
        evidence=[ev('pair15',1,6),ev('pair11',1,5)])
    beige=dict(shared,sequence_id='20261021_empty_beige_pair_return_1043',
        camera_track_id={'15':['beige_pair43_front','beige_pair43_back'],'11':['beige_pair43_front','beige_pair43_back']},
        visible_camera_clock_intervals={'15':['10:43:30','10:43:52'],'11':['10:43:46','10:44:04']},
        cross_camera_identity='Distinct two-beige pair followed toward15 doorway and out into11 with matching order and operator action. Separate from preceding gray pair; no exact offset fitted.',
        observation='Two visibly empty beige bodies returned and placed in waiting row. Full return movement is negative for new production; later local rearrangement is same episode.',
        evidence=[ev('beige15',6,17),ev('beige11',7,16)])
    merge(OUT/'reviewed_sequence_labels.json',[pair,beige],'sequence_id')
    qp=OUT/'sequence_followup_queue.json';save(OUT/'review_history/followup_queue_before_20261031_33.json',read(qp))
    merge(qp,[dict(candidate_id='20261021_midday1040_context',date='20261021',split='train',reviewed_at=stamp,
        cycle_id=None,production_entry_count_target=None,status='screened_empty_returns_not_positive_cycle',
        observation='10:40-44 cluster consists of empty return movements during a station pause; two paired episodes accepted as negatives. Other sparse trips remain screening only.',
        next_action='Do not search this cluster for a filled11-to15 production route. Prioritise fresh filling after44min or another day.',
        evidence=[ev('earlier11',0,12),ev('pair15',0,6),ev('gray15',0,20),ev('beige15',0,17),ev('pair11',0,19),ev('beige11',0,22)]),
        dict(candidate_id='20261021_gray_station_departure1051',date='20261021',split='train',reviewed_at=stamp,
            cycle_id=None,production_entry_count_target=None,status='needs_dense_departure_and_available_peer_search',
            observation='Gray body receives cheese45:14-50:30, covered50:45-51:00; beige replacement by51:15, gray scale body51:30-54:00. Exact doorway passage not yet reviewed.',
            next_action='Review bounded source11 PTS380-430 for departure if useful. Archive15 has metadata50:07-50:40 then11:02:39-11:03:25; check whether older21Oct collection bridges51min before extraction. If no coverage, retain partial rather than invent a full cycle.',
            evidence=[ev('filling',3,38)]),
        dict(candidate_id='20261021_beige_filling_after1051',date='20261021',split='train',reviewed_at=stamp,
            cycle_id=None,production_entry_count_target=None,status='needs_future_departure_context',
            observation='Beige replacement is empty51:15 and receives cheese51:30-54:00. This is separate from gray load.',
            next_action='Next11 source105401-105607 and subsequent source require review; first check15 coverage around eventual departure. Do not merge with gray1051 load.',
            evidence=[ev('filling',27,38)])],'candidate_id')
    registry=read(OUT/'object_review_decisions.json');save(OUT/'review_history/object_decisions_before_20261031_33.json',registry)
    decisions={r['id']:r for r in registry['reviews']}
    drafts={r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
    objnotes={'229':'Two adjacent empty gray/beige physical bodies; annotate each separately.',
        '230':'Two beige physical bodies at threshold; rear body occluded by front body and doorpost.',
        '232':'Visible station gray tank body receiving cheese. Right edge cropped and front heavily occluded by worker/conveyor; box follows visible body extent, not assumed unseen floor footprint.',
        '233':'Empty beige replacement body at station. Right/bottom ROI boundaries truncate body; hands and conveyor partially occlude it.'}
    for ident,note in objnotes.items():
        assert ident not in decisions
        r=drafts[ident]
        decisions[ident]=dict(id=ident,image_sha256=r['sha256'],boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',load_state_reviewed=False,sequence_reviewed=False,
            instance_attributes=[dict(box_index=i,truncated=ident in ['232','233'],occluded=True,load_state='unknown_not_annotated') for i in range(len(r['boxes_xyxy']))],
            evidence=[r['source_frame'],r['frames_manifest'],'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_'+('28' if ident=='229' else '29')+'.jpg'],note=note)
    registry['reviews']=list(decisions.values())
    r=drafts['231']
    registry.setdefault('excluded_roi_reviews',[]).append(dict(id='231',image_sha256=r['sha256'],reviewed_at=stamp,
        reviewer='assistant_visual_review',decision='exclude_whole_roi_not_an_empty_image',
        reason='Two adjacent bodies are blurred and a stationary background-stock fragment enters upper ROI; exclude entire candidate instead of guessing the fragment boundary.',
        evidence=[r['image'],r['source_frame'],r['frames_manifest']]))
    registry.setdefault('corrections',[]).append('Batch33:229/230/232/233 independently overlay-reviewed, four train ROI images/six boxes.231 excluded. Physical tank boxes only; load attributes and production totals not inferred.')
    save(OUT/'object_review_decisions.json',registry)
    inv=read(BASE/'archive_inventory.json');inspected={m['source']['member']:m['source_sha256'] for m in metas.values()}
    for r in inv['records']:
        if r['member'] in inspected:r.update(pixel_inspected=True,sha256=inspected[r['member']])
    assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test')
    save(BASE/'archive_inventory.json',inv)
    reviews=read(OUT/'screening_source_reviews.json');total=sum(r['sampled_frames_visually_reviewed'] for r in reviews);added=sum(len(m['samples']) for m in metas.values())
    state['last_completed'] += [
        f'Batch33 inspected {added} chronological sample presentations in seven21Oct windows; {total} total across {len({r["source_sha256"] for r in reviews})} sources and {len(reviews)} windows. Extractions finished; test pixels untouched.',
        '10:40-44 cluster resolved as empty returns. Two paired return episodes accepted with four physical tracks, zero new-production entries; local repositioning not double-counted.75 negatives; five complete cycles and30 partials unchanged.',
        'New gray station filling45:14-50:30 and change by51:15 queued for dense boundary review. Later covered scale body not linked by assumption.15 archive metadata has50:40-to11:02:39 gap; older collection coverage not yet checked.',
        'Five ROI candidates appended. Four images/six boxes approved and231 excluded.234 candidates,177 approved images,238 boxes,57 exclusions,zero drafts. No training release.',
    ]
    state['priority_next']=[
        'Batch33 complete. Avoid repeating21Oct10:40-44: it is an empty-return cluster, not a filled production route.',
        '21Oct gray51min candidate:11 source104418-105412 has filling through50:30, panel50:45, different empty beige51:15 and gray scale body51:30-54:00. Dense11 PTS380-430 remains uninspected.15 archive ends50:40 then resumes11:02:39; inspect older21Oct collection metadata for a bridge before further extraction.',
        '21Oct beige replacement starts51:15 and fills51:30-54:00; next11 source105401-105607 uninspected. Check15 coverage around later departure before pursuing a complete cycle.',
        'Prioritise positive cycles on another training day and validation17Oct; already75 negative episodes. More easy negatives do not solve missing full-route coverage.',
    ]+[p for p in state['priority_next'] if p.startswith('Known gaps') or p.startswith('25/28') or p.startswith('Old21Oct') or p.startswith('6Oct') or p.startswith('8Oct11') or p.startswith('17Oct17min')]
    state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    state['scripts'] += [s for s in ['work/append_tank_roi_batch_20261031_33.py','work/record_tank_sequence_batch_20261031_33.py'] if s not in state['scripts']]
    save(OUT/'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_samples=added,total_presentations=total,additional_complete_cycles=0,additional_negative_sequences=2,additional_partial_sequences=0,training_started=False)))

if __name__=='__main__':main()
