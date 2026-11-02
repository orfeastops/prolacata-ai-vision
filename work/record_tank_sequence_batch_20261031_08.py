"""Persist visually inspected 10Oct evidence; no training or test-day access."""
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read, save, merge, evidence

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/tank_transfer_training_v1'
OUT=BASE/'dataset_v1'
RUN='sequence_review_20261031_08'

def main():
    state=read(OUT/'continuation_state.json')
    if RUN in state.get('completed_curation_runs',[]):
        print('Already recorded:',RUN); return
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    windows={
        'origin':('earlier_filling_departure_1042_cam11',83),
        'scale':('origin_scale_1047_cam11',78),
        'door':('departure_boundary_1046_cam11',20),
        'aisle':('after_105138_cam15',8),
        'store':('after_105152_cam15',9),
        'later':('after_105329_cam15',11),
        'gap':('entry_gap_search_104409_cam15',6),
    }
    paths={k:OUT/'sequence_review/20261010'/n/'frames.json' for k,(n,_) in windows.items()}
    metas={k:read(p) for k,p in paths.items()}
    for k,m in metas.items():
        assert len(m['samples'])==windows[k][1]
        assert m['source']['date']=='20261010' and m['source']['split']=='train'
        assert all((ROOT/s['image']).is_file() for s in m['samples'])
    # Explicit clock anchors read from the inspected images, not calculated from PTS.
    clocks={
        'origin':{0:'10:41:49',18:'10:43:01',20:'10:43:09',21:'10:43:13',22:'10:43:17',23:'10:43:21',45:'10:44:49',46:'10:44:53',47:'10:44:57',48:'10:45:01',54:'10:45:25',70:'10:46:29',71:'10:46:33',72:'10:46:37',73:'10:46:41',74:'10:46:45',75:'10:46:49',76:'10:46:53',77:'10:46:57',82:'10:47:17'},
        'scale':{0:'10:47:19',6:'10:47:43',7:'10:47:47',8:'10:47:51',10:'10:47:59',12:'10:48:07',18:'10:48:31',24:'10:48:55',30:'10:49:19',39:'10:49:55',41:'10:50:03',49:'10:50:35',54:'10:50:55',55:'10:50:59',56:'10:51:03',57:'10:51:07',58:'10:51:11',72:'10:52:07',73:'10:52:11',77:'10:52:27'},
        'door':{0:'10:46:33',1:'10:46:34',2:'10:46:35',3:'10:46:36',4:'10:46:37',5:'10:46:38',6:'10:46:39',7:'10:46:40',8:'10:46:41',9:'10:46:42',10:'10:46:43',11:'10:46:44',12:'10:46:45',13:'10:46:46',14:'10:46:47',15:'10:46:48',16:'10:46:49',17:'10:46:50',18:'10:46:51',19:'10:46:52'},
        'aisle':{0:'10:51:37',1:'10:51:48',2:'10:51:50',3:'10:51:52',4:'10:51:54',5:'10:51:56',6:'10:51:59',7:'10:52:00'},
        'store':{0:'10:51:52',1:'10:52:04',2:'10:52:06',3:'10:52:08',4:'10:52:10',5:'10:52:12',6:'10:52:14',7:'10:52:16',8:'10:52:18'},
        'later':{0:'10:53:29',1:'10:53:36',2:'10:53:37',3:'10:53:40',4:'10:53:41',5:'10:53:43',6:'10:53:46',7:'10:53:47',8:'10:53:49',9:'10:53:52',10:'10:53:53'},
        'gap':{0:'10:44:09',1:'10:44:31',2:'10:44:34',3:'10:44:37',4:'10:44:40',5:'10:44:43'},
    }
    notes={
        'origin':'Workers visibly fill the gray station tank with cheese through10:46:29, then cover it. Manual jack arrives without a tank10:44:49-53 and engages the station load. Loaded gray departs10:46:36-50. A distinct empty gray replacement is pushed from the left row to the station10:46:41-53, then filling of that next tank starts. A previous gray load already on the scale at10:41:49 leaves it10:43:13-21; that earlier load is not the new departure and has no reviewed origin here.',
        'scale':'A covered gray tank comes onto the room15 scale, visible through the camera11 doorway at10:47:47-51; it dwells there until10:51:03, is pulled right10:51:07 and the platform is empty10:51:11. A trajectory gap from the10:46:45-50 room11 exit to this scale appearance prevents an accepted same-load match. Workers in11 fill a DIFFERENT next tank throughout this window. Empty yellow powered jack enters11 at10:52:07 and parks at left by10:52:11; do not duplicate the existing negative jack episode.',
        'door':'Dense one-second samples show loaded gray departing the station10:46:36, reaching the shared doorway10:46:45, crossing10:46:46-49 and clear of room11 by10:46:50. Distinct empty gray replacement moves from left row to workstation10:46:41-52. The room11 crossing interval is not an observed room15 clock timestamp.',
        'aisle':'After initial stale10:51:37, noninitial samples begin10:51:48. Covered gray emerges from behind fixed blue containers into the aisle10:51:48-54 and pauses10:51:56-52:00 with manual jack. Neither its original room15 entry nor the entire route from the scale is visible. An empty yellow powered jack moves separately. No production entry assigned.',
        'store':'Initial stale10:51:52 is followed by10:52:04. Gray with white cover/fittings moves from open aisle toward the front-right storage row10:52:06-14; manual jack is withdrawn10:52:16-18 while tank remains parked. This is a storage observation with unverified production origin, not an accepted full cycle. Source gap10:52:00-04 retained.',
        'later':'Covered gray remains parked in the row through10:53:53. A yellow powered jack appears carrying a small blue object/bag; it is not annotated as empty or as a cheese-tank entry. Initial stale10:53:29 and jump to10:53:36 retained. No new tank entry label.',
        'gap':'The last preceding room15 export shows earlier covered-load aisle context at initial10:44:09 and then empty jack handling10:44:31-43. It ends10:44:43 and cannot bridge the new room11 loaded crossing10:46:45-50. Available adjacent room15 exports jump to initial10:50:37/noninitial10:50:54. Do not repeat this unsuccessful entry-gap search or infer the new load from the earlier gray.',
    }
    reviews=[]
    for k,m in metas.items():
        reviews.append(dict(review_id='20261010/'+windows[k][0],reviewed_at=stamp,reviewer='assistant_visual_review',
            source_member=m['source']['member'],source_sha256=m['source_sha256'],date='20261010',camera=m['source']['camera'],split='train',
            frames_manifest=str(paths[k].relative_to(ROOT)),sampled_frames_visually_reviewed=len(m['samples']),reviewed_sheets=m['sheets'],
            review_scope='All chronological contact-sheet samples visually inspected, with native context for selected object ROIs. Not exhaustive native-frame viewing.',
            visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],
                relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],visible_camera_clock=t,clock_read_uncertainty_seconds=1,
                image=m['samples'][i]['image'],usable_for_clock_alignment=not(k in ['aisle','store','later','gap'] and i==0)) for i,t in clocks[k].items()],
            observation=notes[k],accepted_complete_cycle=False,
            clock_warning='Initial stale frames are not alignment anchors. Retain original PTS and observed clock intervals separately; no scalar camera synchronization asserted.'))
    merge(OUT/'screening_source_reviews.json',reviews,'review_id')
    def ev(k,a,b):return evidence(metas[k],a,b,paths[k])
    shared=dict(date='20261010',split='train',reviewer='assistant_visual_review',reviewed_at=stamp,cycle_id=None,dataset_release_accepted=False)
    partial=dict(shared,sequence_id='20261010_gray_filling_departure_partial_1046',camera=11,
        camera_track_id='cam11_gray_cheese_station_departure_1046',review_status='reviewed_partial_sequence',
        production_entry_count_target=None,observed_loaded_departure_count=1,
        partial_reason='Fresh filling and loaded room11 departure observed. Room15 entry is absent from available exports; later scale and storage gray tracks are not assigned the same production identity.',
        observation=notes['origin'],evidence=[ev('origin',0,82),ev('door',0,19)],
        stages=[dict(stage='filling_observed',visible_camera_clock_interval=['10:41:49','10:46:29'],clock_uncertainty_seconds=4,
            content_evidence='Visible cheese blocks and placement into the same gray station tank before covering.',evidence=[ev('origin',0,70)]),
            dict(stage='loaded_departure_11',visible_camera_clock_interval=['10:46:36','10:46:50'],clock_uncertainty_seconds=1,
                doorway_crossing_camera11_interval=['10:46:45','10:46:50'],evidence=[ev('door',3,17)],
                observation='Same station tank pulled into doorway; no camera15 event time inferred.')],
        unlinked_followup=dict(status='scale_and_storage_candidates_not_joined_to_production_origin',
            observation='Later gray on scale10:47:47-51:11 and room15 storage movement10:51:48-52:18 are reviewed as unlinked evidence. Missing entry and an obscured scale-to-aisle route prevent a complete production cycle.',
            evidence=[ev('scale',7,58),ev('aisle',1,7),ev('store',1,8),ev('later',1,10)],
            scale_observation=dict(visible_camera_clock_interval=['10:47:47','10:51:11'],evidence=[ev('scale',7,58)],
                observation=notes['scale']),
            storage_observation=dict(visible_camera_clock_interval=['10:51:48','10:52:18'],storage_confirmation_interval=['10:52:16','10:52:18'],
                evidence=[ev('aisle',1,7),ev('store',1,8),ev('later',1,10)],observation=notes['store']),
            limitations=['Approximately57-second unobserved route after loaded room11 exit before candidate reaches scale.',
                'Scale departure10:51:07-11 and room15 emergence10:51:48 have an obscured/gapped route; same-load identity not certified.',
                'White cover/fittings alone do not establish cheese contents. Adjacent storage-source gap10:52:00-04 retained.']),
        entry_gap_search=dict(status='available_adjacent_exports_reviewed_gap_unresolved',evidence=[ev('gap',0,5)],
            preceding_last_visible_clock='10:44:43',next_source_initial_clock='10:50:37',next_source_first_noninitial_clock='10:50:54',
            next_source_evidence_manifest='outputs/tank_transfer_training_v1/dataset_v1/sequence_review/20261010/candidate_1050_cam15/frames.json',
            observation=notes['gap']),
        next_review='Do not repeat this entry-gap search. Preserve partial; expand better-covered paired days21/23Oct and17Oct validation.',
        limitations=['Chronological visual curation, not a model prediction or independently certified ground truth.',
            'No complete-cycle or room15-entry count target. Empty replacement and the earlier already-on-scale load remain distinct.'])
    negative=dict(shared,sequence_id='20261010_empty_gray_replacement_104641',camera=11,
        camera_track_id='cam11_empty_gray_left_row_to_station_104641',review_status='accepted_negative_sequence',
        production_entry_count_target=0,negative_class='empty_tank_internal_reposition',tracked_tank_count=1,
        visible_camera_clock_interval=['10:46:41','10:46:53'],clock_uncertainty_seconds=1,
        evidence=[ev('door',8,19),ev('origin',73,76)],
        observation='One visibly empty gray tank leaves left inventory row and is pushed to filling station while a different loaded gray leaves through the shared door.',
        content_evidence='Open gray interior and exposed bottom visible throughout the replacement movement, before later filling.',
        label_scope='Only this empty internal replacement track has zero production-entry target. Do not apply zero to the simultaneous loaded departure or the later filling of this replacement.')
    merge(OUT/'reviewed_sequence_labels.json',[partial,negative],'sequence_id')
    followups=read(OUT/'sequence_followup_queue.json')
    f=next(x for x in followups if x['candidate_id']=='20261010_door_scale_context_1051')
    previous=copy.deepcopy(f); previous.pop('review_history',None)
    f.setdefault('review_history',[]).append(previous)
    f.update(status='reviewed_partial_origin_with_unresolved_entry_and_followup_identity',reviewed_at=stamp,
        reviewed_partial_sequence_id=partial['sequence_id'],observation=partial['partial_reason'],
        new_evidence=[ev('origin',0,82),ev('door',0,19),ev('scale',7,58),ev('aisle',1,7),ev('store',1,8),ev('gap',0,5)],
        next_action='No repeat extraction. Preserve partial because camera15 entry is missing; move to better-covered21/23Oct or validation17Oct.')
    save(OUT/'sequence_followup_queue.json',followups)
    registry=read(OUT/'object_review_decisions.json')
    decisions={r['id']:r for r in registry['reviews']}
    drafts={r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
    roi_notes={
        '100':'Cheese-filled gray station tank. Worker and conveyor occlude body; lower crop boundary retained. Object-only acceptance.',
        '101':'Covered gray departure tank in central aisle. Native full-frame context distinguishes it from the left empty row. Left crop truncation retained.',
        '102':'Covered gray tank at shared doorway. Right rim partially occluded by door structure. Object acceptance does not establish room15 entry timestamp.',
        '103':'Separate later scale-view gray body, partly hidden by doorway and operator. Production identity remains unlinked.',
        '105':'Empty gray replacement at station before subsequent filling. Worker/conveyor occlusion and lower crop truncation retained.'}
    for ident,note in roi_notes.items():
        assert ident not in decisions
        r=drafts[ident]
        decisions[ident]=dict(id=ident,image_sha256=r['sha256'],boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',load_state_reviewed=False,sequence_reviewed=False,
            instance_attributes=[dict(box_index=j,truncated=(b[0]==0 or b[1]==0 or b[2]==r['width'] or b[3]==r['height']),
                occluded=ident in ['100','102','103','105'],load_state='unknown_not_annotated') for j,b in enumerate(r['boxes_xyxy'])],
            evidence=[r['source_frame'],r['frames_manifest'],str((BASE/'detector_v1/sheets/labels_11.jpg').relative_to(ROOT))],note=note)
    registry['reviews']=list(decisions.values())
    r=drafts['104']
    registry.setdefault('excluded_roi_reviews',[]).append(dict(id='104',image_sha256=r['sha256'],reviewer='assistant_visual_review',reviewed_at=stamp,
        reason='Foreground gray body clear but overlapping crop-edge background body extents uncertain after native/overlay review. Whole ROI excluded rather than guessing clean labels.',
        evidence=[r['source_frame'],r['frames_manifest'],'outputs/tank_transfer_training_v1/detector_v1/sheets/candidate104_detail.png']))
    registry.setdefault('corrections',[]).append('Batch08 adds100-105; five ROI images/five boxes accepted after separate overlays,104 excluded for uncertain background boundaries. Prior accepted annotations unchanged.')
    save(OUT/'object_review_decisions.json',registry)
    inventory=read(BASE/'archive_inventory.json')
    inspected={m['source']['member']:m['source_sha256'] for m in metas.values()}
    for r in inventory['records']:
        if r['member'] in inspected:r.update(pixel_inspected=True,sha256=inspected[r['member']])
    assert not any(r['pixel_inspected'] for r in inventory['records'] if r['split']=='test')
    save(BASE/'archive_inventory.json',inventory)
    total=sum(r['sampled_frames_visually_reviewed'] for r in read(OUT/'screening_source_reviews.json'))
    state['last_completed'] += [
        f'Batch08 reviewed215 chronological samples in7 windows on10Oct; {total} total presentations. All extractions finished, no test pixels inspected.',
        '10Oct fresh gray filling and loaded departure10:46:45-50 added as partial. Available room15 exports end10:44:43 then resume10:50:37(initial stale)/10:50:54. Later scale and storage gray observations remain unlinked; no invented entry or complete cycle.',
        'One empty gray internal replacement movement added as track-scoped negative. Totals2 complete cycles,12 negative episodes,4 partials. Simultaneous loaded departure is separate.',
        'Six native ROI candidates100-105 added; five accepted with5 boxes,104 excluded after overlay review. Totals106 candidates,66 accepted images,110 accepted boxes,6 drafts,34 exclusions. Training remains unreleased.'
    ]
    state['priority_next']=[
        'Batch08 completed10Oct earlier_filling_departure_1042_cam11,origin_scale_1047_cam11,departure_boundary_1046_cam11,after_105138_cam15,after_105152_cam15,after_105329_cam15,entry_gap_search_104409_cam15. Do not repeat these215 samples. No extraction active.',
        'Move to better-covered paired21Oct or23Oct sources for distinct complete training cycles;17Oct remains validation. Need fresh origin, actual entry, scale and storage.25/28Oct stay locked without pixels.',
        'Need diverse complete cycles across training days and17Oct validation, plus already-stored relocation and same-load-reentry negatives. Avoid inflating counts with correlated frames or repeated tracks.',
        'Do not repeat failed gaps:6Oct entry09:35:55-09:36:42;15Oct scale-to-storage11:15:46-11:16:23;10Oct room15 missing entry10:46:45-50 and obscured later scale/storage connection. Keep partials.',
        'Six object drafts002/003/006/007/010/011 remain. Expand clear native context and separate overlay review. No training, uploads or original changes.'
    ]
    state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    for name in ['work/append_tank_roi_batch_20261031_08.py','work/record_tank_sequence_batch_20261031_08.py']:
        if name not in state['scripts']:state['scripts'].append(name)
    save(OUT/'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_temporal_samples=215,additional_partial_sequences=1,additional_negative_sequences=1,additional_accepted_images=5,training_started=False)))

if __name__=='__main__':main()
