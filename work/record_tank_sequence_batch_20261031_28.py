"""Record inspected preparation examples and a separate validation departure."""
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read, save, merge, evidence

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'outputs/tank_transfer_training_v1'
OUT = BASE / 'dataset_v1'
RUN = 'sequence_review_20261031_28'


def main():
    state = read(OUT / 'continuation_state.json')
    if RUN in state.get('completed_curation_runs', []):
        print('Already recorded', RUN)
        return
    stamp = dt.datetime.now(dt.timezone.utc).isoformat()
    windows = {
        'setup11': ('20261008', 'early_pair_context_0518_cam11', 22),
        'liners11': ('20261008', 'early_production_screen_0545_cam11', 38),
        'setup15': ('20261008', 'early_pair_screen_0517_cam15', 31),
        'val15': ('20261017', 'midday_1314_cam15', 23),
        'val11': ('20261017', 'midday_1310_cam11', 45),
        'scale15': ('20261017', 'midday_scale_departure_1313_cam15', 11),
        'detail11': ('20261017', 'midday_tank_unloading_1316_cam11', 33),
    }
    paths = {k: OUT / 'sequence_review' / d / w / 'frames.json' for k, (d, w, n) in windows.items()}
    metas = {k: read(p) for k, p in paths.items()}
    for k, m in metas.items():
        day, window, n = windows[k]
        assert m['source']['date'] == day and len(m['samples']) == n
        assert m['source']['split'] == ('validation' if day == '20261017' else 'train')
    clocks = {
        'setup11': {0:'05:18:39',1:'05:18:46',4:'05:19:01',10:'05:19:31',16:'05:20:01',19:'05:20:16',20:'05:20:21',21:'05:20:26'},
        'liners11': {0:'05:45:16',1:'05:45:38',3:'05:45:54',4:'05:46:02',6:'05:46:18',7:'05:46:26',8:'05:46:34',9:'05:46:42',10:'05:46:50',12:'05:47:06',20:'05:48:10',25:'05:48:50',30:'05:49:30',34:'05:50:02',37:'05:50:26'},
        'setup15': {0:'05:17:36',1:'05:17:45',3:'05:17:55',6:'05:18:10',7:'05:18:15',10:'05:18:30',14:'05:18:50',16:'05:19:00',20:'05:19:20',24:'05:19:40',28:'05:20:00',30:'05:20:10'},
        'val15': {0:'13:14:16',1:'13:14:32',3:'13:14:36',6:'13:14:42',7:'13:14:44',12:'13:14:54',13:'13:14:56',14:'13:14:58',15:'13:15:00',16:'13:15:02',17:'13:15:04',18:'13:15:06',19:'13:15:08',20:'13:15:10',21:'13:15:12',22:'13:15:14'},
        'val11': {0:'13:10:16',1:'13:10:26',2:'13:10:36',6:'13:11:16',7:'13:11:27',12:'13:12:17',14:'13:12:37',16:'13:12:57',17:'13:13:07',18:'13:13:17',24:'13:14:17',28:'13:14:57',29:'13:15:07',30:'13:15:17',31:'13:15:27',32:'13:15:37',33:'13:15:47',34:'13:15:57',35:'13:16:07',36:'13:16:17',38:'13:16:37',39:'13:16:47',40:'13:16:57',41:'13:17:07',44:'13:17:37'},
        'scale15': {0:'13:13:00',1:'13:13:04',2:'13:13:06',4:'13:13:10',6:'13:13:14',8:'13:13:18',10:'13:13:22'},
        'detail11': {0:'13:15:37',1:'13:15:41',2:'13:15:44',3:'13:15:49',4:'13:15:52',5:'13:15:56',6:'13:16:01',7:'13:16:04',8:'13:16:09',9:'13:16:12',10:'13:16:17',11:'13:16:21',12:'13:16:25',13:'13:16:29',14:'13:16:33',15:'13:16:37',16:'13:16:41',17:'13:16:45',18:'13:16:49',19:'13:16:53',20:'13:16:57',21:'13:17:01',22:'13:17:05',23:'13:17:09',24:'13:17:13',28:'13:17:29',29:'13:17:33',30:'13:17:37',32:'13:17:45'},
    }
    notes = {
        'setup11': 'Preproduction preparation. Worker unfolds blue plastic liners among empty gray tanks; two foreground receptacles initially have visibly open perforated bottoms. No cheese trays on conveyor and no fresh tank departure. Worker heads through doorway with loose plastic at20:21. Loose plastic is not a cheese load or tank. Source initial18:39 precedes first usable18:46.',
        'liners11': 'Still preparation despite the search name early_production_screen. Foreground empty tank receives blue liner45:54-46:18; right receptacle receives liner46:26-42 and slight local repositioning. Workers then line waiting tanks through50:26. No cheese filling or productive doorway crossing observed. These are the same preparation episode and not38 distinct negative events.',
        'setup15': 'Existing gray and beige baskets and parked empty manual jack. Worker carries and unfolds white plastic beside left waiting tank18:10-20:10. Existing basket bodies stay in the room; no tank arrival through the doorway in reviewed samples. White plastic handling must not be confused with loaded cheese. Scope is the visible preparation activity and existing inventory, not a claim about unseen time intervals.',
        'val15': 'Early initial14:16 frame shows a covered gray body at left edge; first usable14:32 already has it outside the crop. No storage trajectory accepted from this initial image. Operator crosses aisle with visibly empty forks14:36-42. A separate visibly empty beige basket enters open aisle from left14:54-58, turns15:00-04, then crosses15-to11 at15:06-12. Concurrent stack of white trays is moved by another worker and is not a tank. Full native14:58 confirms the empty beige body and separate stationary inventory.',
        'val11': 'Beige station tank visibly receives cheese10:16 onward, with tray handling and liner/sheet placement between layers. Different covered gray body is already on scale at the beginning and leaves scale view13:07-17; its fresh origin is outside this window. An empty beige replacement arrives from15 around15min and is parked at left. Station tank is moved to open aisle15:47-57, receives further cheese from the separate tray stack, and exits near17min. Another empty beige basket at left is moved internally17:33-37. Do not treat stacks of trays or scrap tank as production tanks.',
        'scale15': 'Operator works at largely hidden right scale area13:04-12; by13:14-22 he brings the manual jack toward the door staging area, with load body mostly concealed by fixed equipment/tray stacks. This does not establish a complete scale-to-storage route or same-load identity with the later14:16 initial gray image. No numerical weight or fresh origin is visible.',
        'detail11': 'Four-second samples correct the preliminary unloading hypothesis: the beige production tank is pulled from station15:49-56, then is filled further from white trays beside it16:04-49. Empty trays are carried back toward conveyor; the separate stack height decreases while the same tank remains loaded. A white sheet is placed over the top16:53-57, then the tank approaches door17:01 and is gone behind the door by17:05; following tray stack partly occludes crossing. Later17:29-45 empty basket is the distinct left-side replacement seen throughout. The directory name reflects search intent, not an unloading label. No block-count target and no new counting rule is derived from validation.',
    }
    for k, m in metas.items():
        day, window, n = windows[k]
        split = 'val' if day == '20261017' else 'train'
        merge(OUT/'screening_source_reviews.json', [dict(
            review_id=day+'/'+window, reviewed_at=stamp, reviewer='assistant_visual_review',
            date=day, camera=m['source']['camera'], split=split, source_member=m['source']['member'],
            source_sha256=m['source_sha256'], frames_manifest=str(paths[k].relative_to(ROOT)),
            sampled_frames_visually_reviewed=n, reviewed_sheets=m['sheets'],
            review_scope='All chronological sampled sheets visually inspected; selected native full frames and separate ROI overlays. Not exhaustive native-frame inspection.',
            observation=notes[k], accepted_complete_cycle=False,
            clock_warning='Camera clocks read from pixels. PTS and filename spans do not establish synchronization or fill missing video.',
            visible_clock_anchors=[dict(sample_index=i, source_pts_seconds=m['samples'][i]['source_pts_seconds'],
                relative_pts_seconds=m['samples'][i]['relative_pts_seconds'], visible_camera_clock=t,
                clock_read_uncertainty_seconds=1, image=m['samples'][i]['image'],
                usable_for_clock_alignment=not(i==0 and k not in ['val11','detail11'])) for i,t in clocks[k].items()]
        )], 'review_id')

    def ev(k,a,b): return evidence(metas[k],a,b,paths[k])
    common = dict(reviewer='assistant_visual_review', reviewed_at=stamp, dataset_release_accepted=False, cycle_id=None)
    labels = [
        dict(common, sequence_id='20261008_room11_liner_preparation', date='20261008', split='train',
            review_status='accepted_negative_sequence', production_entry_count_target=0, camera=11,
            negative_class='opening_inventory', visible_camera_clock_intervals=[['05:18:46','05:20:26'],['05:45:38','05:50:26']],
            observation='Empty waiting/station tanks are lined before production. No productive transfer in these two observed windows.',
            label_scope='Only visible preparation activity. Gap20:26-45:38 is unobserved and not zero-labelled. Counted as one episode, not each basket or image.',
            evidence=[ev('setup11',1,21), ev('liners11',1,37)]),
        dict(common, sequence_id='20261008_room15_liner_preparation', date='20261008', split='train',
            review_status='accepted_negative_sequence', production_entry_count_target=0, camera=15,
            negative_class='opening_inventory', visible_camera_clock_interval=['05:17:45','05:20:10'],
            observation='Stationary waiting inventory while worker handles loose white plastic; no new tank entry.',
            label_scope='Visible stationary inventory and plastic handling; not unseen room activity.', evidence=[ev('setup15',1,30)]),
        dict(common, sequence_id='20261017_empty_beige_return_1315', date='20261017', split='val',
            review_status='accepted_negative_sequence', production_entry_count_target=0, camera=15,
            negative_class='empty_crossing', direction='15_to_11', tracked_tank_count=1,
            visible_camera_clock_interval=['13:14:54','13:15:12'], doorway_interval=['13:15:06','13:15:12'],
            observation='One visibly empty beige basket is taken from room15 through the doorway into11. Simultaneous tray stack is excluded.',
            label_scope='Only the empty returning basket; different loaded tank still filling in11 is separate.', evidence=[ev('val15',12,21)]),
        dict(common, sequence_id='20261017_beige_filling_aisle_departure_partial_1317', date='20261017', split='val',
            review_status='reviewed_partial_sequence', production_entry_count_target=None,
            camera_track_id={'11':'beige_station_then_aisle_then_door1317'}, camera_clock_offset_seconds=None,
            stages=[dict(stage='filling_observed', camera=11,
                visible_camera_clock_interval=['13:10:16','13:16:49'],
                content_evidence='Cheese is placed into the station tank; after moving into aisle, further tray-to-tank filling is visible. Initial contents unknown.',
                evidence=[ev('val11',0,33),ev('detail11',3,18)]),
                dict(stage='loaded_departure_11', camera=11, visible_camera_clock_interval=['13:16:57','13:17:05'],
                    doorway_interval=['13:17:01','13:17:05'], clock_uncertainty_seconds=4,
                    observation='Same beige body with white top approaches door and leaves11; tray stack partly occludes last crossing. Exact camera15 entry clock unreviewed.',
                    evidence=[ev('detail11',18,22)])],
            missing_stages=['verified_entry_15_clock_and_identity','scale_visit','storage_placement'],
            limitations=['Validation annotation only, not training or rule tuning.',
                'Filling continues after tank is moved from its usual station.',
                'A later separate empty basket must not be mistaken for the departing load.']),
    ]
    save(OUT/'review_history/sequence_labels_before_20261031_28.json',read(OUT/'reviewed_sequence_labels.json'))
    merge(OUT/'reviewed_sequence_labels.json',labels,'sequence_id')
    qp=OUT/'sequence_followup_queue.json'
    save(OUT/'review_history/followup_queue_before_20261031_28.json',read(qp))
    merge(qp,[dict(candidate_id='20261017_beige1317_followup',date='20261017',split='val',cycle_id=None,
        production_entry_count_target=None,status='needs_entry_scale_storage_review',reviewed_at=stamp,
        resolved_sequence_id=labels[-1]['sequence_id'],
        observation='Visible loaded beige exit11 at17:01-05; later15 context not yet inspected. Preserve validation-only status.',
        next_action='Inspect17Oct15 source131715-131735_12231087 and adjacent131846-131919_12231846, then131910-131941_12232559. Paired11 long source is13130823-134022_12239199. Do not infer from filename overlap.',
        evidence=[ev('detail11',18,22)]),
        dict(candidate_id='20261017_older_gray_scale1313_storage_unlinked',date='20261017',split='val',cycle_id=None,
            production_entry_count_target=None,status='unresolved_origin_and_storage_gap',reviewed_at=stamp,
            observation='Older gray already on scale10:16-12:57; gone13:17.13:14:16 initial15 image shows covered gray at left, but no observed route or origin. Not a complete cycle and not accepted as relocation.',
            next_action='If revisiting, source131409-131429_12229338 can refine local storage only. Origin needs earlier camera11; no gap bridging by initial stale frame.',
            evidence=[ev('val11',0,18),ev('scale15',0,10),ev('val15',0,3)])], 'candidate_id')

    inventory=read(BASE/'archive_inventory.json')
    limits=[]
    for day in ['20261008','20261017','20261023']:
        for camera in [11,15]:
            rows=[r for r in inventory['records'] if r['date']==day and r['camera']==camera and r['media_type']=='video']
            limits.append(dict(date=day,camera=camera,video_files=len(rows),first_filename_start=min(r['filename_start'] for r in rows),last_filename_end=max(r['filename_end'] for r in rows)))
    save(OUT/'coverage_search_20261031_28.json',dict(reviewed_at=stamp,metadata_only=True,
        source='archive_inventory.json',limits=limits,
        limitations='Filename envelope only; neither continuous coverage nor verified video-clock duration.',
        conclusion='8Oct11 ends05:56:22; later07:37/11:41 camera15 suggestions lack a camera11 counterpart in this archive.23Oct11 ends06:19:12. Use other training days for full cycles;17Oct remains validation.'))
    seen={m['source']['member']:m['source_sha256'] for m in metas.values()}
    for r in inventory['records']:
        if r['member'] in seen:r.update(pixel_inspected=True,sha256=seen[r['member']])
    assert not any(r['pixel_inspected'] for r in inventory['records'] if r['split']=='test')
    save(BASE/'archive_inventory.json',inventory)

    registry=read(OUT/'object_review_decisions.json')
    save(OUT/'review_history/object_decisions_before_20261031_28.json',registry)
    decisions={r['id']:r for r in registry['reviews']}
    drafts={r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
    obj_notes={
        '206':'8Oct empty fixed receptacle before lining; conveyor obscures lower right.',
        '207':'8Oct same receptacle after blue liner fitting; conveyor occlusion remains. Both images belong to train.',
        '208':'17Oct empty returning beige body-only crop; upper rim clipped and worker obscures right. Validation only.',
        '209':'17Oct loaded departing beige body; lower edge clipped and following worker/trays obscure front. Validation only.',
        '210':'17Oct separate empty beige waiting basket; small front-left occlusion from fixed instrument. Validation only.',
    }
    for ident,note in obj_notes.items():
        assert ident not in decisions
        r=drafts[ident]
        decisions[ident]=dict(id=ident,image_sha256=r['sha256'],
            boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',
            load_state_reviewed=False,sequence_reviewed=False,
            instance_attributes=[dict(box_index=0,truncated=ident in ['208','209'],occluded=True,load_state='unknown_not_annotated')],
            evidence=[r['source_frame'],r['frames_manifest'],'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_25.jpg'],note=note)
    registry['reviews']=list(decisions.values())
    registry.setdefault('corrections',[]).append('Batch28:206-210 independently overlay-reviewed. Two training images from8Oct, three validation images from17Oct. No load class exported; prior boxes unchanged.')
    save(OUT/'object_review_decisions.json',registry)
    reviews=read(OUT/'screening_source_reviews.json')
    total=sum(r['sampled_frames_visually_reviewed'] for r in reviews)
    state['last_completed'] += [
        f'Batch28 reviewed203 chronological presentations in7 windows on8/17Oct; {total} total across{len({r["source_sha256"] for r in reviews})} sources and{len(reviews)} windows. No active extraction;25/28Oct untouched.',
        '8Oct two preparation negatives added. Archive metadata shows11 ends05:56:22, so later15 candidate windows cannot produce paired cycles from this archive.23Oct11 ends06:19:12. Filename envelopes are not continuous coverage.',
        '17Oct validation: one empty beige15-to11 return added, and one fresh beige filling/aisle-filling/departure partial. Dense review corrected preliminary unloading hypothesis; this is further filling outside station. No model rules tuned.5 full cycles,68 negatives,27 partials.',
        'Five native ROI images206-210 approved after separate overlays.211 candidates,156 accepted images,215 boxes,55 exclusions,zero drafts. No training release.'
    ]
    state['priority_next']=[
        'Batch28 complete. Full cycles remain5 on13Oct only. Prioritise diverse training-day complete routes and complete validation examples; do not pad with more easy negatives.',
        '17Oct validation beige17min partial has fresh filling and loaded exit17:01-05. Next inspect15 source131715-131735_12231087 and adjacent131846-131919_12231846,131910-131941_12232559. Continue long11 source13130823-134022_12239199 for scale corroboration. Keep validation-only; no tuning.',
        '8Oct11 archive stops05:56:22,23Oct11 stops06:19:12.8Oct sampled windows show preparation. Drop earlier07:37/11:41 paired-cycle suggestion unless new media supplied. Inventory envelope is metadata, not proof of continuous coverage.',
        '17Oct1316 window named midday_tank_unloading actually shows further filling from tray stack, followed by loaded departure. Never convert its search name or initial hypothesis into an unloading label. Separate empty replacement stays in11.',
    ]+[p for p in state['priority_next'] if p.startswith('Known gaps') or p.startswith('25/28') or p.startswith('Old21Oct') or p.startswith('6Oct17min')]
    state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    state['scripts'] += [s for s in ['work/append_tank_roi_batch_20261031_28.py','work/record_tank_sequence_batch_20261031_28.py'] if s not in state['scripts']]
    save(OUT/'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_samples=203,total_presentations=total,training_started=False)))


if __name__=='__main__':main()
