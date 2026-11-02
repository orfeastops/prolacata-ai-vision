"""Record further scale evidence, without converting recording gaps to cycles."""
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read, save, merge, evidence

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/tank_transfer_training_v1'
OUT=BASE/'dataset_v1'
RUN='sequence_review_20261031_11'


def main():
    state=read(OUT/'continuation_state.json')
    if RUN in state.get('completed_curation_runs',[]):
        print('Already recorded:',RUN);return
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    windows={
        'bridge':('scale_bridge_0733_cam15',18),
        'scale15':('scale_followup_0734_cam15',38),
        'followup15':('followup_0737_cam15',15),
        'scale11':('scale_followup_0735_cam11',84),
    }
    paths={k:OUT/'sequence_review/20261021'/v[0]/'frames.json' for k,v in windows.items()}
    metas={k:read(p) for k,p in paths.items()}
    for k,m in metas.items():
        assert len(m['samples'])==windows[k][1]
        assert m['source']['date']=='20261021' and m['source']['split']=='train'
        assert all((ROOT/s['image']).exists() for s in m['samples'])
    clocks={
        'bridge':{0:'07:33:22',1:'07:33:29',6:'07:33:34',8:'07:33:36',10:'07:33:38',12:'07:33:40',14:'07:33:42',17:'07:33:45'},
        'scale15':{0:'07:34:34',1:'07:34:39',5:'07:34:43',6:'07:34:44',11:'07:34:49',17:'07:34:55',
                   23:'07:35:01',26:'07:35:04',29:'07:35:07',30:'07:35:08',35:'07:35:13',37:'07:35:15'},
        'followup15':{0:'07:37:06',1:'07:37:09',5:'07:37:13',6:'07:37:14',7:'07:37:15',11:'07:37:19',14:'07:37:22'},
        'scale11':{0:'07:34:52',1:'07:35:09',2:'07:35:15',5:'07:35:33',11:'07:36:09',17:'07:36:45',
                   23:'07:37:21',29:'07:37:57',30:'07:38:03',31:'07:38:09',32:'07:38:15',33:'07:38:21',
                   43:'07:39:21',44:'07:39:27',45:'07:39:33',46:'07:39:39',47:'07:39:45',53:'07:40:21',
                   55:'07:40:33',56:'07:40:39',57:'07:40:45',58:'07:40:51',59:'07:40:57',60:'07:41:03',
                   61:'07:41:09',62:'07:41:15',65:'07:41:33',71:'07:42:09',77:'07:42:45',83:'07:43:21'},
    }
    notes={
        'bridge':'Initial33:22 is stale; first noninitial33:29 shows gray staged at doorway with manual jack. Operator pulls and turns this gray33:34-40, then pushes right toward scale33:42-45, where fixed blue containers occlude its body. Earlier reviewed camera15 entry source ends32:58 and resumes here at33:29:31 seconds of staging trajectory remain unsampled. Matching appearance/location is supportive, not proof of uninterrupted identity. No storage placement or new arrival occurs in this bounded movement.',
        'scale15':'Initial34:34 is stale, first noninitial34:39. Operator works at scale-side terminal through35:03, walks toward doorway04-09, then returns to terminal10-15. Moving gray is mostly hidden behind fixed blue containers; paired camera11 shows platform occupancy. Stationary beige/gray containers holding metal hoops remain at exactly the same foreground positions through35:15. Other room inventory remains separate. No storage movement observed.',
        'followup15':'Initial37:06 is stale, first noninitial37:09. Operator handles fittings around fixed blue containers09-13, then walks without a tank toward doorway14-19 and remains near it20-22. Gray scale body remains occluded from this view. No scale-to-storage trajectory here. Next available camera15 filename begins07:45:18; the camera11 scale departure around38:03-15 falls within the missing interval.',
        'scale11':'Initial34:52 is stale; first noninitial35:09. Gray is on scale through37:57, jack engages/moves at38:03-09, and platform is clear38:15. Tank moves right within15, not back into11; final storage is offscreen. Empty jack is next visible inside11 by39:33-39, but this does not identify storage location. Meanwhile a distinct beige station tank is filled through40:33, then pulled away40:39, reaches door40:45 and is out by40:51. It is seen in15 doorway/scale region41:03-09 and on platform by41:15 through43:21. A separate visibly empty beige replacement moves from local row to station40:45-57, followed by fresh filling from41:03 onward. No block totals or completed cycles inferred.'
    }
    reviews=[]
    for k,m in metas.items():
        reviews.append(dict(review_id='20261021/'+windows[k][0],reviewed_at=stamp,reviewer='assistant_visual_review',
            source_member=m['source']['member'],source_sha256=m['source_sha256'],date='20261021',camera=m['source']['camera'],split='train',
            frames_manifest=str(paths[k].relative_to(ROOT)),sampled_frames_visually_reviewed=len(m['samples']),reviewed_sheets=m['sheets'],
            review_scope='All chronological contact-sheet samples inspected. Selected native frames and separate object overlays also reviewed. Not exhaustive native-frame inspection.',
            visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],
                visible_camera_clock=t,clock_read_uncertainty_seconds=1,image=m['samples'][i]['image'],usable_for_clock_alignment=i!=0) for i,t in clocks[k].items()],
            observation=notes[k],accepted_complete_cycle=False,
            clock_warning='Stale initial images excluded from alignment. PTS and filename times are not verified cross-camera clocks; bounded visible-clock evidence only.'))
    merge(OUT/'screening_source_reviews.json',reviews,'review_id')
    def ev(k,a,b):return evidence(metas[k],a,b,paths[k])
    labels={r['sequence_id']:r for r in read(OUT/'reviewed_sequence_labels.json')}
    prior=labels['20261021_gray_filling_entry_partial_0732']
    history=OUT/'review_history/sequence_labels_before_20261031_11.json'
    if not history.exists():save(history,dict(saved_at=stamp,reason='Preserve earlier partial and pending scale observations before follow-up.',records=[copy.deepcopy(prior)]))
    prior.update(reviewed_at=stamp,
        partial_reason='Fresh filling, loaded departure and room15 entry remain confirmed. Later gray scale approach/dwell/departure are reviewed, but31 seconds of staging continuity and the scale-to-storage trajectory remain missing.',
        observation='One previously reviewed gray entry at07:32:45-50 remains partial. A gray staged at same location is then moved toward scale33:34-45, remains on platform through37:57 and leaves38:03-15. This additional evidence does not establish final storage or a completed cycle.')
    prior['evidence'] += [ev('bridge',1,17),ev('scale15',1,37),ev('followup15',1,14),ev('scale11',1,33)]
    prior['unlinked_followup']=dict(status='later_gray_scale_track_reviewed_staging_gap_retained',
        visible_camera_clock_interval=['07:33:29','07:38:15'],scale_approach_interval=['07:33:34','07:33:45'],
        scale_departure_interval=['07:37:57','07:38:15'],clock_uncertainty_seconds=6,
        observation='A gray staged at doorway33:29 is turned and pushed toward scale34-45, then platform occupancy is visible through camera11 until37:57. It leaves38:03-15. Same position/cover support correspondence with32:45-50 arrival, but the32:58-to33:29 gap is retained rather than asserted continuous. Storage after38:15 is outside available15 coverage.',
        evidence=[ev('bridge',1,17),ev('scale15',1,37),ev('followup15',1,14),ev('scale11',1,33)],production_entry_count_target=None)
    prior['storage_gap_search']=dict(status='available_export_gap_prevents_storage_label',last_camera15_clock='07:37:22',
        next_camera15_filename_start='20261021074518',next_source_pixels_reviewed=False,
        camera11_scale_departure_interval=['07:37:57','07:38:15'],
        evidence=[ev('followup15',14,14),ev('scale11',29,33)],
        next_action='Do not repeat this gap search without an additional source spanning38-minute scale departure/storage. Filename is coverage metadata only, not a clock anchor.')
    prior['limitations'].append('Later scale track is kept separately because staging has31-second unsampled interval; scale-to-storage lies in missing camera15 export interval37:22-to45:18(filename).')

    shared=dict(date='20261021',split='train',reviewer='assistant_visual_review',reviewed_at=stamp,cycle_id=None,dataset_release_accepted=False)
    beige=dict(shared,sequence_id='20261021_beige_filling_departure_scale_partial_0740',camera=11,
        camera_track_id='cam11_beige_station_0735_to_scale_0741',review_status='reviewed_partial_sequence',
        production_entry_count_target=None,observed_loaded_departure_count=1,observed_room15_entry_count=None,
        entry15_camera_clock_interval=None,
        partial_reason='Filled beige departure and subsequent scale occupancy visible through camera11 doorway. Camera15 entry and scale-to-storage coverage are missing/unreviewed, so no completed cycle.',
        observation='Beige station tank visibly receives cheese35:09-40:33, is pulled away40:39, reaches shared doorway40:45 and is out by40:51. Same beige trajectory is visible in15 through camera11, reaches platform41:03-15 and remains through43:21. The empty beige replacement at40:45-57 is a different physical tank.',
        evidence=[ev('scale11',1,62),ev('scale11',62,83)],
        stages=[
            dict(stage='filling_observed',visible_camera_clock_interval=['07:35:09','07:40:33'],clock_uncertainty_seconds=6,
                 content_evidence='Visible cheese blocks and placements in same beige station tank. Already partly filled at start; initial contents and block total unknown.',evidence=[ev('scale11',1,55)]),
            dict(stage='loaded_departure_11',visible_camera_clock_interval=['07:40:39','07:40:51'],
                 doorway_crossing_camera11_interval=['07:40:45','07:40:51'],clock_uncertainty_seconds=6,evidence=[ev('scale11',55,58)]),
            dict(stage='scale_visit',visible_camera_clock_interval=['07:41:03','07:43:21'],scale_arrival_interval=['07:41:03','07:41:15'],
                 clock_uncertainty_seconds=6,observation='Observed through camera11 doorway; last sample is ongoing occupancy, not a scale departure timestamp. No kilograms read.',evidence=[ev('scale11',60,83)])],
        limitations=['Camera15 event timestamp is absent, not derived from filenames or camera11 clock.','Storage and scale departure are not reviewed.','No complete production target or block total assigned.'])
    negative=dict(shared,sequence_id='20261021_empty_beige_replacement_074045',camera=11,
        camera_track_id='cam11_empty_beige_row_to_station_0740',review_status='accepted_negative_sequence',production_entry_count_target=0,
        negative_class='empty_tank_internal_reposition',tracked_tank_count=1,
        visible_camera_clock_interval=['07:40:45','07:40:57'],clock_uncertainty_seconds=6,evidence=[ev('scale11',57,59)],
        observation='Worker pushes one visibly empty beige tank from local row into filling position while a different filled beige exits. Exposed bottom is clearly visible40:51-57.',
        label_scope='Only empty internal replacement before fresh filling. Loaded departure, existing room stock and later filling are separate.')
    inventory_negative=dict(shared,sequence_id='20261021_stationary_hoop_container_inventory_0734',camera=15,
        camera_track_id='cam15_existing_beige_gray_hoop_pair_0734',review_status='accepted_negative_sequence',production_entry_count_target=0,
        negative_class='opening_inventory',tracked_tank_count=2,
        visible_camera_clock_interval=['07:34:39','07:35:15'],clock_uncertainty_seconds=1,evidence=[ev('scale15',1,37)],
        observation='Two adjacent foreground containers, beige in front and gray behind, hold metal hoops and are already present in first usable frame. Both remain stationary throughout this window; neither arrives from11.',
        label_scope='Only these two pre-existing foreground containers in this bounded source window. This is not whole-room zero, day-opening stock total, or a claim about contents of other tanks.')
    labels.update({r['sequence_id']:r for r in [beige,negative,inventory_negative]})
    save(OUT/'reviewed_sequence_labels.json',list(labels.values()))

    queue=read(OUT/'sequence_followup_queue.json')
    old=next(r for r in queue if r['candidate_id']=='20261021_gray_scale_storage_followup_0733')
    hp=OUT/'review_history/followup_before_20261031_11.json'
    if not hp.exists():save(hp,dict(saved_at=stamp,records=[copy.deepcopy(old)]))
    old.update(status='reviewed_partial_scale_trajectory_storage_missing',reviewed_at=stamp,
        observation=prior['partial_reason'],new_evidence=[ev('bridge',1,17),ev('scale11',29,33)],
        next_action='Preserve partial. Do not repeat37:22-to45:18 storage-gap search without new media. Shift curation to diverse sources and already-stored relocation negatives.')
    queue.append(dict(candidate_id='20261021_beige_scale_storage_0741',date='20261021',split='train',cycle_id=None,production_entry_count_target=None,
        status='partial_departure_scale_storage_unreviewed',reviewed_at=stamp,reviewed_partial_sequence_id=beige['sequence_id'],
        observation=beige['partial_reason'],new_evidence=[ev('scale11',55,83)],
        next_action='Keep partial; camera15 entry lies in known37:22-to45:18 coverage gap. Do not fabricate an entry timestamp. Seek more complete source intervals on other days first.'))
    save(OUT/'sequence_followup_queue.json',queue)

    registry=read(OUT/'object_review_decisions.json');decisions={r['id']:r for r in registry['reviews']}
    draft={r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
    notes_roi={
        '118':'Native gray tank during turn toward scale. Crop tightened before review to remove ambiguous neighboring equipment; body clipped at right/lower edge.',
        '119':'Beige station tank with cheese and worker/conveyor occlusion. Individual blocks are not annotated or counted.',
        '120':'Beige tank pulled from station, with white top and partly visible side behind operator. Cover alone not used as load classification.',
        '121':'Beige departing tank at doorway with top crop truncation and right doorway occlusion.',
        '122':'One empty beige internal replacement, plus separate stationary covered tank fragment at lower-left crop boundary.'}
    for ident,note in notes_roi.items():
        assert ident not in decisions
        r=draft[ident]
        decisions[ident]=dict(id=ident,image_sha256=r['sha256'],boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',load_state_reviewed=False,sequence_reviewed=False,
            instance_attributes=[dict(box_index=j,truncated=(b[0]==0 or b[1]==0 or b[2]==r['width'] or b[3]==r['height']),
                occluded=(ident in ['119','120','121']) or (ident=='122' and j==0),load_state='unknown_not_annotated') for j,b in enumerate(r['boxes_xyxy'])],
            evidence=[r['source_frame'],r['frames_manifest'],'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_'+('13' if ident in ['118','119'] else '14')+'.jpg'],note=note)
    registry['reviews']=list(decisions.values())
    registry.setdefault('corrections',[]).append('Batch11: five native ROIs118-122 with six boxes accepted after separate overlay review.118 was tightened before acceptance. Earlier accepted labels unchanged.')
    save(OUT/'object_review_decisions.json',registry)
    inventory=read(BASE/'archive_inventory.json');inspected={m['source']['member']:m['source_sha256'] for m in metas.values()}
    for r in inventory['records']:
        if r['member'] in inspected:r.update(pixel_inspected=True,sha256=inspected[r['member']])
    assert not any(r['pixel_inspected'] for r in inventory['records'] if r['split']=='test')
    save(BASE/'archive_inventory.json',inventory)
    total=sum(r['sampled_frames_visually_reviewed'] for r in read(OUT/'screening_source_reviews.json'))
    state['last_completed'] += [
        f'Batch11 reviewed155 additional sample presentations across4 new21Oct windows; {total} total. All extraction sessions finished;25/28Oct untouched.',
        '0732 gray partial refined with later staging-to-scale movement33:34-45, scale dwell and departure38:03-15.31-second staging gap and missing storage remain explicit. Prior label and queue versions saved in review_history.',
        'New beige fresh filling/departure40:39-51 and scale occupancy41:03-43:21 retained as partial. Two negatives added: empty beige internal replacement40:45-57 and existing stationary foreground container pair. Totals2 complete cycles,19 negatives,8 partials.',
        'Five native ROI images118-122 and6 boxes passed separate overlay review. Totals123 candidates,81 approved ROI images,130 boxes,6 drafts,36 exclusions. Training remains unreleased.'
    ]
    state['priority_next']=[
        'Batch11 complete:21Oct scale_bridge_0733_cam15,scale_followup_0734_cam15,followup_0737_cam15,scale_followup_0735_cam11.155 presentations inspected; do not repeat. No extraction active.',
        'Prioritize missing negative classes and source diversity: existing sequence_review_case_20261021_390.json points to native context with already-covered tank relocation and a separate filled departure. Review chronological source and identity before accepting; do not use old event counts as labels.',
        'For additional complete cycles,13Oct has longer15 source windows090821-091619 and102139-102912 not yet inspected. Need at least another training day too; metadata inventory shows other days mostly short15 clips, so check coverage before spending a full origin review on a storage gap.',
        'Known gaps must stay partial:6Oct entry09:35:55-36:42;15Oct scale-storage11:15:46-16:23;10Oct entry10:46:45-50;21Oct storage0714/0731/0738 and15 entry0740. Do not repeat these searches without new media.',
        'Need17Oct validation sequences and same-load reentry;25/28Oct remain locked. Six old object drafts002/003/006/007/010/011 still need full native context or justified exclusion. No training/uploads/original changes.'
    ]
    state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    for name in ['work/append_tank_roi_batch_20261031_11.py','work/record_tank_sequence_batch_20261031_11.py']:
        if name not in state['scripts']:state['scripts'].append(name)
    save(OUT/'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_temporal_samples=155,refined_partial_sequences=1,additional_partial_sequences=1,additional_negative_sequences=2,additional_accepted_images=5,training_started=False)))


if __name__=='__main__':main()
