"""Record the visually reviewed 17Oct validation material, without training.

Native chronology, missing entry frames and unlinked storage are explicit.
All labels remain unreleased; no held-out test pixels have been inspected.
"""
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read, save, merge, evidence

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/tank_transfer_training_v1'
OUT=BASE/'dataset_v1'
RUN='sequence_review_20261031_13'


def main():
    state=read(OUT/'continuation_state.json')
    if RUN in state.get('completed_curation_runs',[]):
        print('Already recorded:',RUN);return
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    windows={
        'setup':('early_inventory_0505_cam15',71),
        'origin':('origin_1038_cam11',35),
        'older_storage':('entry_context_1041_cam15',21),
        'join':('departure_1040_cam11',28),
        'departure':('departure_1041_cam11',50),
        'staging':('scale_context_1042_cam15',15),
    }
    paths={k:OUT/'sequence_review/20261017'/v[0]/'frames.json' for k,v in windows.items()}
    metas={k:read(p) for k,p in paths.items()}
    for k,m in metas.items():
        assert len(m['samples'])==windows[k][1]
        assert m['source']['date']=='20261017' and m['source']['split']=='validation'
        assert all((ROOT/s['image']).exists() for s in m['samples'])
    # Anchors read from the rendered camera overlays, not calculated from PTS.
    clocks={
        'setup':{0:'05:05:04',1:'05:05:22',2:'05:05:28',3:'05:05:34',5:'05:05:46',7:'05:05:58',9:'05:06:10',12:'05:06:28',14:'05:06:40',18:'05:07:04',28:'05:08:04',38:'05:09:04',48:'05:10:04',50:'05:10:16',58:'05:11:04',60:'05:11:16',61:'05:11:22',68:'05:12:04',70:'05:12:16'},
        'origin':{0:'10:38:56',1:'10:39:11',10:'10:39:38',17:'10:39:59',18:'10:40:02',24:'10:40:20',29:'10:40:35',30:'10:40:38',33:'10:40:47',34:'10:40:50'},
        'older_storage':{0:'10:41:24',1:'10:41:33',2:'10:41:35',3:'10:41:35',7:'10:41:39',8:'10:41:40',9:'10:41:42',11:'10:41:44',13:'10:41:46',15:'10:41:47',16:'10:41:49',18:'10:41:50',19:'10:41:52',20:'10:41:52'},
        'join':{0:'10:40:50',1:'10:40:54',3:'10:40:58',4:'10:41:00',13:'10:41:18',23:'10:41:38',27:'10:41:46'},
        'departure':{0:'10:41:55',1:'10:41:58',2:'10:42:01',6:'10:42:13',9:'10:42:22',12:'10:42:31',18:'10:42:49',19:'10:42:52',20:'10:42:55',21:'10:42:58',22:'10:43:01',23:'10:43:04',24:'10:43:07',25:'10:43:10',29:'10:43:22',39:'10:43:52',49:'10:44:22'},
        'staging':{0:'10:42:59',1:'10:43:17',2:'10:43:18',5:'10:43:21',9:'10:43:25',14:'10:43:30'},
    }
    notes={
        'setup':'Three operators upright and arrange many visibly empty gray and beige tanks from stacks already inside room15 into rows at the left/back. Gray examples05:05:28-46,05:05:58-06:10 and06:28-40; other movements overlap. Beige05:10:16 has a clearly empty perforated bottom. These are internal empty-tank setup moves, not new filled entries. The already-present blue-lined tank remains near the back until an operator removes its bag around05:11:16-22 and moves the underlying tank. No exact unique tank total assigned; no cheese inferred from a liner. First source-start image05:05:04 is stale; usable sequence starts05:05:22.',
        'origin':'First usable10:39:11: a covered high-sided gray tank is already on the room15 scale, visible through room11 door. Operator handles fittings until40:35 and engages jack40:38-47; load begins moving40:50. A DIFFERENT low-profile gray tank with visible cheese is being filled at the room11 station throughout39:11-40:50; the stationary beige scrap receptacle is separate. Starting cheese quantity unknown. Do not link the later41-minute storage scene to the tank still being filled in11.',
        'older_storage':'Despite the extraction name entry_context, first usable41:33 shows a covered high-sided gray tank already near doorway staging. It moves into room centre35-42, turns44-46 and is pushed toward a storage-row position47-52. Worker/jack still engaged at source end; no completed jack withdrawal observed. Prior scale departure40:50-54 and this41:33 staging are separated by a gap. Similar gray color does not establish identity or prior storage. Repeated camera-clock seconds retained literally.',
        'join':'Same low-profile cheese tank continues at filling station through41:46; no loaded station departure. The earlier high-sided gray has cleared the scale by40:54, leaving platform empty. First image40:50 aligns with the previous source end but is not used as an independent synchronization anchor. This joins current station context, not the older storage track.',
        'departure':'Low-profile gray remains at station, with further cheese placements42:13-49. Operator returns from15 with empty manual jack42:22-31, engages filled tank31-49 and pulls it toward shared door52-58. It reaches threshold43:01 and is absent from11 by43:04. Separate empty gray replacement moves from local left row42:58-43:07; its empty lined bottom is visible and filling resumes around43:10. Scale platform beyond door remains empty through44:22. The preceding source ends41:46 and this begins41:55;9-second gap is retained. No newly completed production cycle or numeric block count assigned.',
        'staging':'Despite extraction name scale_context, first usable43:17 shows a low-profile gray tank already staged left of room15 door; operator handles white boards/cover/fittings through43:30. Actual entry threshold moment is missing: source initial42:59 is stale and11 departure is43:01-04. No scale visit in this window, consistent with empty platform in paired11 through44:22. An older high-sided covered gray is parked in a left front row, distinct from the low-profile staged tank. Do not infer entry clock or scale/storage completion from filenames.',
    }
    reviews=[]
    for k,m in metas.items():
        reviews.append(dict(review_id='20261017/'+windows[k][0],reviewed_at=stamp,reviewer='assistant_visual_review',
            source_member=m['source']['member'],source_sha256=m['source_sha256'],date='20261017',camera=m['source']['camera'],split='val',
            frames_manifest=str(paths[k].relative_to(ROOT)),sampled_frames_visually_reviewed=len(m['samples']),reviewed_sheets=m['sheets'],
            review_scope='Every chronological contact-sheet sample inspected. Four selected native full frames and separate ROI overlays also reviewed. Not exhaustive native-frame viewing. Validation annotation only; no model or threshold tuning.',
            visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],
                visible_camera_clock=t,clock_read_uncertainty_seconds=1,image=m['samples'][i]['image'],usable_for_clock_alignment=i!=0) for i,t in clocks[k].items()],
            observation=notes[k],accepted_complete_cycle=False,
            clock_warning='Source-start images excluded from synchronization. Filename intervals and decoder PTS do not establish cross-camera alignment.'))
    merge(OUT/'screening_source_reviews.json',reviews,'review_id')
    def ev(k,a,b):return evidence(metas[k],a,b,paths[k])
    shared=dict(date='20261017',split='val',reviewer='assistant_visual_review',reviewed_at=stamp,cycle_id=None,dataset_release_accepted=False)
    setup=dict(shared,sequence_id='20261017_empty_tank_setup_0505',camera=15,camera_track_id='cam15_empty_tank_setup_episode_0505',
        review_status='accepted_negative_sequence',production_entry_count_target=0,negative_class='empty_tank_internal_reposition',tracked_tank_count=None,
        visible_camera_clock_interval=['05:05:22','05:12:16'],clock_uncertainty_seconds=6,evidence=[ev('setup',1,70)],
        observation=notes['setup'],label_scope='One episode of observed empty internal setup movements, not a unique-tank inventory count or zero label for all room activity. Already-present lined tank has no inferred cheese content.')
    jack=dict(shared,sequence_id='20261017_empty_jack_return_1042',camera=11,camera_track_id='cam11_empty_manual_jack_return_104222',
        review_status='accepted_negative_sequence',production_entry_count_target=0,negative_class='pallet_jack_without_tank',tracked_tank_count=0,
        visible_camera_clock_interval=['10:42:22','10:42:31'],clock_uncertainty_seconds=3,evidence=[ev('departure',9,12)],
        observation='Operator enters room11 from15 with an unloaded manual jack before engaging the station tank.',
        label_scope='Only the unloaded return segment; subsequent filled-tank pickup is a different action and not a negative.')
    empty=dict(shared,sequence_id='20261017_empty_gray_replacement_1043',camera=11,camera_track_id='cam11_empty_gray_replacement_104258',
        review_status='accepted_negative_sequence',production_entry_count_target=0,negative_class='empty_tank_internal_reposition',tracked_tank_count=1,
        visible_camera_clock_interval=['10:42:58','10:43:07'],clock_uncertainty_seconds=3,evidence=[ev('departure',21,24)],
        observation='One visibly empty gray lined tank is moved from the local left row to the filling station. Empty bottom visible43:04-07. Filling begins later.',
        label_scope='Only this empty replacement before filling. Different loaded tank departs simultaneously; not a whole-frame zero.')
    fresh=dict(shared,sequence_id='20261017_fresh_gray_departure_partial_1043',camera=11,camera_track_id='cam11_fresh_low_gray_1039_1043',
        review_status='reviewed_partial_sequence',production_entry_count_target=None,observed_loaded_departure_count=1,
        entry15_camera_clock_interval=None,arrival15_observed_by='10:43:17',
        partial_reason='Filling and loaded departure observed. A compatible low gray load appears staged in15 after an entry-recording gap. Exact threshold moment, scale visit and storage are not established; no complete-cycle target.',
        observation=notes['departure'],evidence=[ev('origin',1,34),ev('join',1,27),ev('departure',1,49)],
        stages=[
            dict(stage='filling_observed',visible_camera_clock_interval=['10:39:11','10:42:49'],clock_uncertainty_seconds=3,
                content_evidence='Cheese placements into the station tank seen across adjacent reviewed11 windows; initial contents unknown.9-second source gap41:46-55 retained.',
                evidence=[ev('origin',1,34),ev('join',1,27),ev('departure',1,18)]),
            dict(stage='loaded_departure_11',visible_camera_clock_interval=['10:42:52','10:43:04'],doorway_crossing_camera11_interval=['10:42:58','10:43:04'],
                clock_uncertainty_seconds=3,evidence=[ev('departure',19,23)]),
        ],
        unlinked_followup=dict(status='compatible_low_gray_staged_in15_entry_not_sampled',production_entry_count_target=None,
            visible_camera_clock_interval=['10:43:17','10:43:30'],arrival_observed_by='10:43:17',entry15_camera_clock_interval=None,
            observation=notes['staging'],correspondence='Compatible appearance/location after11 departure; no continuous door crossing available. Same-load identity remains provisional.',
            evidence=[ev('staging',1,14)]),
        limitations=['No invented entry timestamp, camera offset, complete production count or starting cheese quantity.',
            'The older covered high-sided gray at scale/storage is a different observation from the fresh low-profile station load.',
            'Validation labels only. No training, model selection or threshold adjustment performed.'])
    older=dict(shared,sequence_id='20261017_older_gray_scale_partial_1040',camera=11,camera_track_id='cam11_existing_gray_scale_1039',
        review_status='reviewed_partial_sequence',production_entry_count_target=None,
        partial_reason='Covered gray already on scale when source starts. Fresh filling and arrival not observed. Later storage approach is separated by a source gap and kept unlinked.',
        observation=notes['origin'],evidence=[ev('origin',1,34),ev('join',0,1)],
        stages=[dict(stage='scale_visit',visible_camera_clock_interval=['10:39:11','10:40:54'],scale_departure_interval=['10:40:47','10:40:54'],
            clock_uncertainty_seconds=4,content_evidence='Covered gray; contents unknown. No numeric scale reading.',evidence=[ev('origin',1,34),ev('join',0,1)])],
        unlinked_followup=dict(status='gray_storage_approach_origin_and_gap_unresolved',production_entry_count_target=None,
            visible_camera_clock_interval=['10:41:33','10:41:52'],observation=notes['older_storage'],evidence=[ev('older_storage',1,20)]),
        limitations=['Do not classify as already-stored relocation: prior storage is not established.',
            'Do not match this older tank to fresh station filling in11.',
            'Storage approach alone is not proof of completed storage; operator and fork remain engaged at source end.'])
    merge(OUT/'reviewed_sequence_labels.json',[setup,jack,empty,fresh,older],'sequence_id')
    merge(OUT/'sequence_followup_queue.json',[
        dict(candidate_id='20261017_low_gray_scale_storage_after1043',date='20261017',split='val',cycle_id=None,production_entry_count_target=None,
            status='validation_partial_missing_entry_scale_storage',reviewed_at=stamp,reviewed_partial_sequence_id=fresh['sequence_id'],
            observation=fresh['partial_reason'],next_action='If pursuing followup, inspect native11 sources104422-104531,104509-104613,104602-104931 and104937-105427 before connecting15 source104925-104952.15 gap43:30-49:25 remains. Do not infer entry from stale42:59 frame.',new_evidence=[ev('departure',19,49),ev('staging',1,14)]),
        dict(candidate_id='20261017_older_gray_storage_origin_1041',date='20261017',split='val',cycle_id=None,production_entry_count_target=None,
            status='validation_scale_and_storage_unlinked',reviewed_at=stamp,reviewed_partial_sequence_id=older['sequence_id'],
            observation=older['partial_reason'],next_action='Retain partial unless new media bridges40:50/54-to41:33 and establishes origin. Do not turn into negative prior-stock relocation.',new_evidence=[ev('origin',29,34),ev('older_storage',1,20)])
    ],'candidate_id')

    registry=read(OUT/'object_review_decisions.json');decisions={r['id']:r for r in registry['reviews']}
    draft={r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
    notes_roi={
        '127':'Empty beige moving internally in15; operator occludes right side. Validation object box only.',
        '128':'Covered gray leaving station; full tank body visible. Cover alone supplies no load-state target. Validation only.',
        '129':'Empty replacement at station; hands/body and conveyor occlude front. Cropped at right/bottom. Validation only.',
        '130':'Separate stationary beige scrap receptacle; worker/conveyor occlude lower outline. Generic tank detection only; no production-entry label from this image. Validation only.',
    }
    for ident,note in notes_roi.items():
        assert ident not in decisions;r=draft[ident];assert r['split']=='val' and r['date']=='20261017'
        sheet='14' if ident=='127' else '15'
        decisions[ident]=dict(id=ident,image_sha256=r['sha256'],boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',load_state_reviewed=False,sequence_reviewed=False,
            instance_attributes=[dict(box_index=j,truncated=(b[0]==0 or b[1]==0 or b[2]==r['width'] or b[3]==r['height']),occluded=ident!='128',load_state='unknown_not_annotated') for j,b in enumerate(r['boxes_xyxy'])],
            evidence=[r['source_frame'],r['frames_manifest'],f'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_{sheet}.jpg'],note=note)
    registry['reviews']=list(decisions.values())
    registry.setdefault('corrections',[]).append('Batch13: four17Oct validation-only native ROIs127-130 accepted with4 object boxes after separate overlay review. No prior boxes changed; no load attributes guessed.')
    save(OUT/'object_review_decisions.json',registry)

    # Repair the summary overwritten by the old builder, using the durable
    # batch12 temporal labels as evidence. The builder now preserves this file.
    casepath=OUT/'sequence_review_case_20261021_390.json';case=read(casepath)
    ids=['20261021_gray_storage_only_partial_1339','20261021_beige_entry_scale_partial_1341','20261021_two_empty_beige_returns_1340','20261021_empty_jack_after_beige_storage_1347']
    labels={r['sequence_id']:r for r in read(OUT/'reviewed_sequence_labels.json')}
    assert all(i in labels for i in ids)
    history=OUT/'review_history/case390_builder_overwrite_before_20261031_13.json'
    if not history.exists():save(history,dict(saved_at=stamp,record=copy.deepcopy(case)))
    beige=labels[ids[1]]
    case.update(status='native_review_complete_two_partial_tracks_and_two_empty_returns',reviewed_at=beige['reviewed_at'],
        observation='Native context separates gray storage39-40min, two visibly empty beige returns40-41min and fresh filled beige departure/entry41min. Already-stored relocation is NOT established. Loaded beige scale-to-storage identity remains partial.',
        camera15_new_entry_time=None,camera15_new_entry_interval=beige['entry15_camera_clock_interval'],scale_visit=['13:41:40','13:46:03'],storage_placement=None,
        reviewed_sequence_ids=ids,prior_annotation='outputs/tank_transfer_training_v1/dataset_v1/review_history/case390_before_20261031_12.json',
        restored_from='outputs/tank_transfer_training_v1/dataset_v1/reviewed_sequence_labels.json',restoration_at=stamp,
        restoration_reason='Prevented generic workspace builder from overwriting reviewed case. Original checked temporal labels preserved unchanged.')
    save(casepath,case)
    inventory=read(BASE/'archive_inventory.json');inspected={m['source']['member']:m['source_sha256'] for m in metas.values()}
    for r in inventory['records']:
        if r['member'] in inspected:r.update(pixel_inspected=True,sha256=inspected[r['member']])
    assert not any(r['pixel_inspected'] for r in inventory['records'] if r['split']=='test')
    save(BASE/'archive_inventory.json',inventory)
    total=sum(r['sampled_frames_visually_reviewed'] for r in read(OUT/'screening_source_reviews.json'))
    state['last_completed'] += [
        f'Batch13 reviewed220 chronological validation sample presentations in6 windows on17Oct; {total} total across68 source videos and86 windows. Test25/28Oct untouched. All extractions completed.',
        '17Oct validation:3 negative episodes(empty internal setup, empty jack return, empty gray replacement) and2 partial tracks(fresh low-gray departure; older high-gray scale/unlinked storage). No guessed43-minute entry clock or complete cycle. Totals2 complete,24 negative,12 partial;3 negatives and2 partials are validation only.',
        'Four native17Oct validation ROIs127-130 and4 boxes passed separate overlay review. Totals131 candidates,87 accepted images,136 boxes,6 old drafts,38 exclusions. No training release.',
        'Workspace builder now preserves reviewed case390. Restored batch12 case summary from preserved temporal labels; overwritten generic summary archived. Integrity verifier now checks temporal label/source date and partition consistency, including validation-only17Oct.'
    ]
    state['priority_next']=[
        'Batch13 all6 windows on17Oct05:05-12 and10:39-44 reviewed and recorded. Do not repeat. Validation low-gray partial lacks actual15 entry43:01-04 and subsequent scale/storage; current15 ends43:30, next available filename49:25.11 later windows may supply scale evidence but not missing15 identity.',
        'Need additional complete-cycle TRAINING days and true post-storage relocation/same-load reentry negatives.13Oct long15 windows090821-091619 and102139-102912 remain uninspected, but currently both accepted complete cycles already from13Oct. Prioritize continuous camera coverage on other training days before more origin review.',
        'Known gaps unchanged:6Oct09:35:55-36:42;15Oct11:15:46-16:23;10Oct10:46:45-50 entry;21Oct0714/0731/0738 storage,0740 entry,13:36:21-39:33 gray origin,13:46:39-53 beige staging/storage identity.17Oct older gray40:50/54-41:33 also unlinked. Do not repeat gap searches without new media.',
        'Six old object drafts002/003/006/007/010/011 still need full native context or justified exclusion. Image/sequence coverage remains below protocol; no release based on integrity checks alone.',
        '25/28Oct remain locked and unseen.17Oct validation only; do not use its annotations for training or rule tuning. No training, uploads, original changes or GitHub publication. Update local review and source-backed quality checks.'
    ]
    state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    for name in ['work/append_tank_roi_batch_20261031_13.py','work/record_tank_sequence_batch_20261031_13.py']:
        if name not in state['scripts']:state['scripts'].append(name)
    save(OUT/'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_temporal_samples=220,additional_validation_partials=2,additional_validation_negatives=3,additional_validation_images=4,training_started=False)))


if __name__=='__main__':main()
