"""Persist the second15Oct gray-load inspection without bridging unseen routes."""
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read, save, merge, evidence

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/tank_transfer_training_v1'
OUT=BASE/'dataset_v1'
RUN='sequence_review_20261031_31'

def main():
    state=read(OUT/'continuation_state.json')
    if RUN in state.get('completed_curation_runs',[]):
        print('Already recorded',RUN);return
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    windows={
        'before':('second_gray_departure_1242_cam11',37),
        'entrysearch':('second_gray_entry_1242_cam15',25),
        'context':('second_gray_context_1244_cam11',41),
        'scale':('second_gray_scale_after1248_cam11',52),
        'transfer':('second_gray_transfer_1250_cam15',30),
        'storage':('second_gray_storage_1251_cam15',33),
        'boundary':('second_gray_boundary_1245_cam11',35),
    }
    paths={k:OUT/'sequence_review/20261015'/w/'frames.json' for k,(w,n) in windows.items()}
    metas={k:read(p) for k,p in paths.items()}
    for k,m in metas.items():
        assert m['source']['date']=='20261015' and m['source']['split']=='train'
        assert len(m['samples'])==windows[k][1]
    clocks={
        'before':{0:'12:42:37',1:'12:42:52',5:'12:43:04',11:'12:43:22',17:'12:43:40',18:'12:43:43',23:'12:43:58',26:'12:44:07',30:'12:44:19',33:'12:44:28',36:'12:44:37'},
        'entrysearch':{0:'12:42:54',1:'12:42:57',3:'12:42:59',6:'12:43:02',12:'12:43:08',18:'12:43:14',24:'12:43:20'},
        'context':{0:'12:44:39',3:'12:44:57',6:'12:45:15',7:'12:45:21',8:'12:45:27',9:'12:45:33',10:'12:45:39',11:'12:45:45',18:'12:46:27',19:'12:46:33',20:'12:46:39',21:'12:46:45',22:'12:46:51',23:'12:46:57',24:'12:47:03',30:'12:47:39',36:'12:48:15',40:'12:48:39'},
        'scale':{0:'12:48:38',1:'12:48:45',3:'12:48:55',4:'12:49:00',10:'12:49:30',16:'12:50:00',19:'12:50:15',20:'12:50:20',21:'12:50:25',28:'12:51:00',32:'12:51:20',40:'12:52:00',44:'12:52:20',45:'12:52:25',46:'12:52:30',47:'12:52:35',48:'12:52:40',49:'12:52:45',51:'12:52:55'},
        'transfer':{0:'12:50:48',1:'12:50:51',3:'12:50:53',6:'12:50:56',9:'12:50:59',10:'12:51:00',14:'12:51:04',18:'12:51:08',22:'12:51:12',26:'12:51:16',29:'12:51:19'},
        'storage':{0:'12:51:16',1:'12:51:21',2:'12:51:22',3:'12:51:23',4:'12:51:24',5:'12:51:25',8:'12:51:28',14:'12:51:34',20:'12:51:40',26:'12:51:46',32:'12:51:52'},
        'boundary':{0:'12:45:14',1:'12:45:15',2:'12:45:16',3:'12:45:17',4:'12:45:18',5:'12:45:19',6:'12:45:20',7:'12:45:21',8:'12:45:22',9:'12:45:23',10:'12:45:24',11:'12:45:25',12:'12:45:26',13:'12:45:27',14:'12:45:28',15:'12:45:29',16:'12:45:30',17:'12:45:31',18:'12:45:32',19:'12:45:33',20:'12:45:34',21:'12:45:35',22:'12:45:36',23:'12:45:37',24:'12:45:38',25:'12:45:39',26:'12:45:40',27:'12:45:41',28:'12:45:42',29:'12:45:43',30:'12:45:44',31:'12:45:45',32:'12:45:46',33:'12:45:47',34:'12:45:48'},
    }
    notes={
        'before':'Search window, not a departure label despite directory name. Initial42:37 is early; usable42:52-44:37. Gray station tank receives cheese; people pause and resume43:43 and44:07. Jack waits nearby. Scale is clear. Operator approaches44:28-37. No tank leaves here.',
        'entrysearch':'Search window, not an entry label despite directory name. Initial42:54 is early. Usable42:57-43:20 shows people crossing42:59-43:08, no moving tank. Stored rows, blue waiting tanks and inverted empties remain. Do not apply zero to the entire room or manufacture a counterpart for the later45min departure.',
        'context':'Station gray continues filling44:39-45:15, panel45:21, loaded departure45:27-39 and clear45:45. Separate empty gray replaces it and later starts filling; this is a third physical station load, not continued filling of the departed tank. Scale remains clear46:33, gray emerges46:39 and settles46:45-51. It stays in sampled views through48:39. Stage-to-scale identity across the hidden45:42-46:39 route is not verified. Native45:27 and46:51 inspected.',
        'scale':'Covered gray remains on scale48:38-50:15. It moves right off platform50:20 and platform is clear50:25. No numerical weight read. Third station tank is being filled throughout. Empty gray appears through door52:25, moves to left waiting area30-40 and operator withdraws empty forks45; this return is not a new productive entry. Native52:25 shows empty liner/bottom.',
        'transfer':'Initial50:48 is early. Operator draws covered gray from obscured doorway staging50:53-59. Body travels down-left51:00-08, rotates09-12, approaches front-left storage row13-19. Native51:04 confirms one moving gray body and separate stored rows. The51:19-to-next-usable51:21 join is two seconds; preserve that sampling boundary rather than claim exhaustive frame continuity.',
        'storage':'Initial51:16 is early and overlaps previous source. Usable51:21 shows gray parked at front-left edge of rear storage row; empty forks visibly withdraw51:22-24. It remains parked through51:52 while another person crosses. Native51:23 confirms placement and separated jack. This is a local storage observation; no complete production identity through the earlier missing entry/scale route.',
        'boundary':'Dense one-second samples: visible cheese14-19; cover placed20-22; jack lifts/prepares23-27; gray moves away28-35. Door crossing36-41, disappears42. Different visibly empty gray moves from left waiting area29-41; later cheese filling46-48 is outside its negative movement label. Native31 shows simultaneous covered departure and distinct empty replacement; native41 shows replacement interior. All anchors are pixel-clock readings, not filename arithmetic.',
    }
    for k,m in metas.items():
        merge(OUT/'screening_source_reviews.json',[dict(review_id='20261015/'+windows[k][0],reviewed_at=stamp,
            reviewer='assistant_visual_review',date='20261015',camera=m['source']['camera'],split='train',
            source_member=m['source']['member'],source_sha256=m['source_sha256'],frames_manifest=str(paths[k].relative_to(ROOT)),
            sampled_frames_visually_reviewed=len(m['samples']),reviewed_sheets=m['sheets'],
            review_scope='All chronological sampled sheets inspected, selected native context and separate ROI overlays; not exhaustive native-frame viewing.',
            observation=notes[k],accepted_complete_cycle=False,
            clock_warning='Visible pixel clocks only. Initial early frames and filename/PTS values cannot prove camera synchronization or unseen trajectories.',
            visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],
                relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],visible_camera_clock=t,clock_read_uncertainty_seconds=1,
                image=m['samples'][i]['image'],usable_for_clock_alignment=False) for i,t in clocks[k].items()])],'review_id')
    def ev(k,a,b):return evidence(metas[k],a,b,paths[k])
    oldpath=OUT/'sequence_review/20261015/late_production_1234_cam11/frames.json'
    old=read(oldpath)
    oldfill=evidence(old,0,61,oldpath)
    save(OUT/'review_history/sequence_labels_before_20261031_31.json',read(OUT/'reviewed_sequence_labels.json'))
    shared=dict(date='20261015',split='train',reviewer='assistant_visual_review',reviewed_at=stamp,dataset_release_accepted=False)
    partial=dict(shared,sequence_id='20261015_fresh_gray_departure_partial_1245',review_status='reviewed_partial_sequence',cycle_id=None,
        production_entry_count_target=None,camera_track_id={'11':'gray_filling_departure1245','15':'candidate_gray_storage1251'},
        camera_clock_offset_seconds=None,cross_camera_identity='Physical departure into15 observed in11; later scale and15 storage remain candidate followups across unseen route segments.',
        stages=[dict(stage='filling_observed',camera=11,visible_camera_clock_interval=['12:34:22','12:45:19'],
            content_evidence='Gray replacement receives cheese after34min departure and before45min cover. Prior reviewed filling referenced, not counted again as newly viewed samples. Initial contents and mass unknown.',
            evidence=[oldfill,ev('before',1,36),ev('context',0,6),ev('boundary',0,5)]),
            dict(stage='loaded_departure_11',camera=11,visible_camera_clock_interval=['12:45:28','12:45:42'],doorway_interval=['12:45:36','12:45:42'],
                observation='Same observed filling body pulled to doorway, then disappears into15. Different empty station replacement is kept separate.',evidence=[ev('boundary',14,28)]),
            dict(stage='entry_15',camera=11,visible_camera_clock_interval=['12:45:36','12:45:42'],room15_clock_interval=None,
                clock_basis='Pixel clock on11 only; no calibrated15 entry timestamp.',evidence=[ev('boundary',22,28)])],
        reviewed_followup_observations=[
            dict(stage='scale_visit',camera=11,visible_camera_clock_interval=['12:46:39','12:50:25'],same_load_identity_confirmed=False,numeric_weight_kg=None,
                placement_interval=['12:46:39','12:46:51'],departure_interval=['12:50:15','12:50:25'],
                observation='Covered gray settles on scale and later leaves. Entry-to-scale trajectory is hidden; same color/time is not a verified identity.',evidence=[ev('context',19,40),ev('scale',0,21)]),
            dict(stage='storage_placement',camera=15,visible_camera_clock_interval=['12:50:53','12:51:24'],same_load_identity_confirmed=False,
                storage_confirmed_interval=['12:51:21','12:51:24'],
                observation='Gray emerges from obscured staging, moves to row, is parked and forks withdrawn.51:19-21 sampled source boundary retained.50:25 platform-clear in11 to50:51 usable15 footage leaves an unverified route.',
                evidence=[ev('transfer',3,29),ev('storage',1,4)])],
        missing_stages=['calibrated_room15_entry_timestamp','verified_entry_to_scale_identity','verified_scale_to_storage_identity'],
        limitations=['Camera15 metadata jumps from source ending43:20 to source beginning47:24; no recorded45min counterpart found in archive inventory. Metadata does not establish continuous coverage.',
            'Covered appearance alone is not cheese evidence.','No numeric weight, full-cycle count or model-accuracy claim.'])
    negatives=[
        dict(shared,sequence_id='20261015_empty_gray_station_replacement_1245',review_status='accepted_negative_sequence',cycle_id=None,production_entry_count_target=0,
            camera=11,negative_class='empty_tank_internal_reposition',tracked_tank_count=1,direction='room11_waiting_area_to_station',
            visible_camera_clock_interval=['12:45:29','12:45:41'],evidence=[ev('boundary',15,27)],
            observation='Separate empty gray pushed from waiting area to station; open empty liner visible. Later filling46-48 excluded.',
            label_scope='Only the tracked empty local movement, not simultaneous loaded departure or later filling.'),
        dict(shared,sequence_id='20261015_empty_gray_return_1252',review_status='accepted_negative_sequence',cycle_id=None,production_entry_count_target=0,
            camera=11,negative_class='empty_crossing',tracked_tank_count=1,direction='room15_to_room11',
            visible_camera_clock_interval=['12:52:20','12:52:40'],crossing_time_uncertainty_seconds=5,evidence=[ev('scale',44,48)],
            observation='Door clear20, empty gray already emerging25, then moves to waiting position30-40. Empty forks withdrawn45. Do not infer exact threshold second or identity with previously stored gray.',
            label_scope='Tracked empty return only; third station tank continues receiving cheese independently.'),
    ]
    merge(OUT/'reviewed_sequence_labels.json',[partial]+negatives,'sequence_id')
    qp=OUT/'sequence_followup_queue.json';save(OUT/'review_history/followup_queue_before_20261031_31.json',read(qp))
    merge(qp,[dict(candidate_id='20261015_next_gray_filling_after1234',date='20261015',split='train',cycle_id=None,production_entry_count_target=None,
        status='resolved_as_partial_departure1245',reviewed_at=stamp,resolved_sequence_id=partial['sequence_id'],
        observation='Second station gray filling followed to45:28-42 departure.46:39-50:25 scale and50:53-51:24 storage observations retained without cross-gap full-cycle link.',
        next_action='Do not repeatedly sample a missing45min camera15 recording. Prioritise another paired training interval with coverage; retain this partial.',
        evidence=[oldfill,ev('boundary',14,28),ev('context',19,40),ev('scale',0,21),ev('transfer',3,29),ev('storage',1,4)]),
        dict(candidate_id='20261015_third_gray_filling_after1245',date='20261015',split='train',cycle_id=None,production_entry_count_target=None,
            status='needs_future_departure_context',reviewed_at=stamp,
            observation='Third gray placed empty45:41, visibly filled46-48 and throughout later11 sequence to52:55. Different empty gray returns52:25.',
            next_action='If revisiting15Oct inspect remaining same11 source after PTS260, first check matching15 coverage; do not merge with45min load.',
            evidence=[ev('boundary',27,34),ev('context',24,40),ev('scale',0,51)])],'candidate_id')
    registry=read(OUT/'object_review_decisions.json');save(OUT/'review_history/object_decisions_before_20261031_31.json',registry)
    decisions={r['id']:r for r in registry['reviews']}
    drafts={r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
    objnotes={'220':'Isolated covered gray moving away from station; complete body extent.',
        '221':'Covered gray on scale viewed through11 doorway; indicator/doorpost partly occlude left side.',
        '222':'Empty lined gray crossing back into11; rim and feet clear.',
        '223':'Gray transit body in15; declared crop cuts top and left, jack partly occludes lower-left side. Body only; no cover/load annotation.'}
    for ident,note in objnotes.items():
        assert ident not in decisions
        r=drafts[ident]
        decisions[ident]=dict(id=ident,image_sha256=r['sha256'],boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',load_state_reviewed=False,sequence_reviewed=False,
            instance_attributes=[dict(box_index=0,truncated=ident=='223',occluded=ident in ['221','223'],load_state='unknown_not_annotated')],
            evidence=[r['source_frame'],r['frames_manifest'],'outputs/tank_transfer_training_v1/detector_v1/sheets/'+('labels_27.jpg' if int(ident)<223 else 'labels_28.jpg')],note=note)
    registry['reviews']=list(decisions.values())
    r=drafts['224']
    registry.setdefault('excluded_roi_reviews',[]).append(dict(id='224',image_sha256=r['sha256'],reviewed_at=stamp,reviewer='assistant_visual_review',decision='exclude_whole_roi_not_an_empty_image',
        reason='Main empty gray identifiable, but cropped beige fragment behind worker has uncertain instance extent. Entire ROI excluded instead of omitting a tank fragment.',
        evidence=[r['image'],r['source_frame'],r['frames_manifest']]))
    registry.setdefault('corrections',[]).append('Batch31:220-223 independently overlay-reviewed; four train images/four boxes.223 top/left truncated.224 excluded due adjacent fragment; no zero-image target. Prior approvals retained.')
    save(OUT/'object_review_decisions.json',registry)
    inv=read(BASE/'archive_inventory.json');inspected={m['source']['member']:m['source_sha256'] for m in metas.values()}
    for r in inv['records']:
        if r['member'] in inspected:r.update(pixel_inspected=True,sha256=inspected[r['member']])
    assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test')
    save(BASE/'archive_inventory.json',inv)
    reviews=read(OUT/'screening_source_reviews.json');total=sum(r['sampled_frames_visually_reviewed'] for r in reviews);added=sum(len(m['samples']) for m in metas.values())
    state['last_completed'] += [
        f'Batch31 inspected {added} chronological sample presentations in seven15Oct windows; {total} total across {len({r["source_sha256"] for r in reviews})} sources and {len(reviews)} windows. Extractions finished,25/28Oct untouched.',
        'Second15Oct gray followed from prior filling to45:28-42 departure, crossing36-42. Scale46:39-50:25 and storage51:21-24 observed but not joined across unseen entry/staging. One partial added; full cycles remain5.',
        'Two scoped negatives added:45min empty station replacement and52min empty return. Totals72 negatives,29 partials. No duplicate count for later filling or empty forks.',
        'Four ROI images220-223/four boxes independently approved;224 excluded.225 candidates,169 approved images,228 boxes,56 exclusions,zero drafts. Training not released.',
    ]
    state['priority_next']=[
        'Batch31 complete. Five full cycles remain all13Oct. Prioritise paired routes on6/21Oct and validation; avoid accumulating easy negatives or resampling gaps on15Oct.',
        '15Oct second gray1245 partial:11 crossing45:36-42, later scale46:39-50:25, storage51:21-24. No inventoried15 recording covers45min entry. Existing partial is useful but must not become a full-cycle target through temporal proximity alone.',
        '15Oct third gray fills45:46-52:55, source Camera_11_DVR_20261015124838_20261015130210_11885480.mp4 continues after PTS260. Check paired15 metadata before choosing another window.',
    ]+[p for p in state['priority_next'] if p.startswith('Known gaps') or p.startswith('25/28') or p.startswith('Old21Oct') or p.startswith('6Oct17min') or p.startswith('8Oct11') or p.startswith('17Oct17min')]
    state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    state['scripts'] += [s for s in ['work/append_tank_roi_batch_20261031_31.py','work/record_tank_sequence_batch_20261031_31.py'] if s not in state['scripts']]
    save(OUT/'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_samples=added,total_presentations=total,additional_complete_cycles=0,additional_negative_sequences=2,additional_partial_sequences=1,training_started=False)))

if __name__=='__main__':main()
