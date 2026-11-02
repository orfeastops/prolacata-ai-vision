"""Save native visual review of two empty returns and separate loaded tracks.

No model inference or training is performed here. Recording gaps remain gaps.
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
RUN='sequence_review_20261031_12'


def main():
    state=read(OUT/'continuation_state.json')
    if RUN in state.get('completed_curation_runs',[]):
        print('Already recorded:',RUN);return
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    windows={
        'gray':('relocation_1339_cam15',35),
        'empty':('relocation_1340_cam15',40),
        'entry':('relocation_1341_cam15',15),
        'origin':('origin_1339_cam11',70),
        'scale15':('relocation_1342_cam15',14),
        'pre35':('relocation_precontext_1335_cam15',16),
        'pre36':('relocation_precontext_1336_cam15',16),
        'scale11':('scale_departure_1343_cam11',45),
        'store_a':('storage_1347a_cam15',16),
        'store_b':('storage_1347b_cam15',22),
    }
    paths={k:OUT/'sequence_review/20261021'/v[0]/'frames.json' for k,v in windows.items()}
    metas={k:read(p) for k,p in paths.items()}
    for k,m in metas.items():
        assert len(m['samples'])==windows[k][1]
        assert m['source']['date']=='20261021' and m['source']['split']=='train'
        assert all((ROOT/s['image']).exists() for s in m['samples'])
    clocks={
        'gray':{0:'13:39:13',1:'13:39:33',7:'13:39:45',10:'13:39:51',11:'13:39:53',15:'13:40:01',16:'13:40:03',17:'13:40:05',34:'13:40:39'},
        'empty':{0:'13:40:37',1:'13:40:41',6:'13:40:46',10:'13:40:50',14:'13:40:54',18:'13:40:58',26:'13:41:06',36:'13:41:16',39:'13:41:19'},
        'entry':{0:'13:41:06',1:'13:41:21',3:'13:41:23',5:'13:41:25',7:'13:41:27',10:'13:41:30',14:'13:41:34'},
        'origin':{0:'13:38:55',1:'13:39:18',14:'13:39:57',15:'13:40:00',26:'13:40:33',29:'13:40:42',30:'13:40:45',33:'13:40:54',34:'13:40:57',36:'13:41:03',38:'13:41:09',39:'13:41:13',41:'13:41:19',42:'13:41:22',43:'13:41:25',44:'13:41:28',45:'13:41:30',48:'13:41:40',49:'13:41:43',50:'13:41:45',51:'13:41:48',54:'13:41:57',69:'13:42:42'},
        'scale15':{0:'13:41:46',1:'13:42:03',6:'13:42:08',11:'13:42:13',13:'13:42:15'},
        'pre35':{0:'13:35:08',1:'13:35:14',7:'13:35:20',15:'13:35:28'},
        'pre36':{0:'13:35:59',1:'13:36:07',9:'13:36:15',15:'13:36:21'},
        'scale11':{0:'13:42:45',1:'13:42:51',2:'13:42:57',3:'13:43:03',12:'13:43:57',13:'13:44:03',22:'13:44:57',23:'13:45:03',30:'13:45:45',31:'13:45:51',32:'13:45:57',33:'13:46:03',39:'13:46:39',41:'13:46:51',44:'13:47:09'},
        'store_a':{0:'13:46:50',1:'13:46:53',7:'13:46:59',8:'13:47:00',15:'13:47:07'},
        'store_b':{0:'13:46:58',1:'13:47:09',2:'13:47:10',3:'13:47:11',5:'13:47:13',19:'13:47:27',21:'13:47:29'},
    }
    notes={
        'gray':'First usable sample39:33 shows an already covered gray tank near doorway/row end. It is pulled to room centre35-45, turned47-51 and pushed into front storage row53-40:01. Empty fork is withdrawn40:03-05; gray stays parked through40:39. No fresh arrival is observed in this source. Earlier scale context does not prove identity across the36:21-to39:33 gap, so this is storage-only partial, NOT established already-stored relocation.',
        'empty':'Two different visibly empty beige tanks move from left room15 toward room11. First is carried on manual jack46-58; its bottom is clear47-52 and threshold crossing54-58. Second is hand-pushed41:06-19, reaches threshold16-19 and continues into11 in next source21-23. The gray stored at40:01 remains stationary. These are two physical tanks, two return trips and zero eligible production entries.',
        'entry':'Second empty beige return finishes at41:21-23. A different freshly filled beige tank appears at shared door25-27, crosses into15 approximately25-30, and is pulled to staging left of door30-34. Paired camera11 shows its departure from the active filling station. Exact clock offset is not asserted; visible camera clocks have bounded differences.',
        'origin':'First usable39:18: cheese already in beige station tank, with additional placements through40:33. Cover placed40:42-45. First empty beige return crosses40:54-57 and is put left in11. Apron operator returns with empty jack41:03-09, engages filled station tank13-19 and pulls it22-30 through doorway. Second empty beige return crosses19-22 and is put at filling station28-30; new filling starts around40-43. The loaded beige is visible through doorway turning toward scale40-45, settled48-57 and present through42:42. Distinct stationary scrap tank is separate. Initial contents and block counts unknown.',
        'scale15':'First usable42:03: operator handles white cover/fittings at scale03-13, behind fixed blue containers. Beige body is heavily occluded in15; ongoing platform occupancy is supported by paired11. No storage trajectory in this window.',
        'pre35':'First usable35:14: operator at scale handles cover/fittings and walks toward doorway. A gray body is heavily occluded behind fixed blue containers. Rows remain stationary. This does not establish that39-minute gray had already been stored or that it is the same scale load.',
        'pre36':'First usable36:07: operator returns from door to scale; occluded gray body remains at scale area. No arrival or storage observed. Last clock36:21, next reviewed39-minute source first usable39:33. Do not bridge that gap by gray color alone.',
        'scale11':'Bounded extraction starts at source-relative210 seconds, first sample is valid42:45 (not a source-start stale frame). Same beige is on scale through45:45. Jack engages45:51, load moves45:57, platform clear46:03. Beige edge remains visible in right room15 doorway area through at least46:39. Later room15 source resumes46:53 with a beige load already in centre. Scale-to-centre identity gap retained; do not turn compatible appearance into a complete-cycle target.',
        'store_a':'First usable46:53: covered beige load is already in centre. It turns53-59 and is pushed into front row gap47:00-07. Gray tank stored39-40min remains nearby. This supports storage placement, but preceding scale-to-centre path is not observed in15 and is not conclusively bridged by11.',
        'store_b':'Initial46:58 is stale; first usable47:09 follows previous source47:07 at same row position. Beige placement completed09-10, empty manual jack withdrawn11-13 and moved toward doorway14-27. Beige remains parked through29. This empty jack track is a negative, separate from all stored tanks and any other room activity.',
    }
    reviews=[]
    for k,m in metas.items():
        reviews.append(dict(review_id='20261021/'+windows[k][0],reviewed_at=stamp,reviewer='assistant_visual_review',
            source_member=m['source']['member'],source_sha256=m['source_sha256'],date='20261021',camera=m['source']['camera'],split='train',
            frames_manifest=str(paths[k].relative_to(ROOT)),sampled_frames_visually_reviewed=len(m['samples']),reviewed_sheets=m['sheets'],
            review_scope='Every chronological contact-sheet sample inspected. Selected native full frames and separate ROI overlays also reviewed; not exhaustive native-frame viewing.',
            visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],
                visible_camera_clock=t,clock_read_uncertainty_seconds=1,image=m['samples'][i]['image'],usable_for_clock_alignment=i!=0 or k=='scale11') for i,t in clocks[k].items()],
            observation=notes[k],accepted_complete_cycle=False,
            clock_warning='Source-start stale images excluded from alignment. Filenames and PTS are not camera synchronization. Explicit clock intervals and gaps retained.'))
    merge(OUT/'screening_source_reviews.json',reviews,'review_id')
    def ev(k,a,b):return evidence(metas[k],a,b,paths[k])
    shared=dict(date='20261021',split='train',reviewer='assistant_visual_review',reviewed_at=stamp,cycle_id=None,dataset_release_accepted=False)
    gray=dict(shared,sequence_id='20261021_gray_storage_only_partial_1339',camera=15,camera_track_id='cam15_gray_centre_to_row_1339',
        review_status='reviewed_partial_sequence',production_entry_count_target=None,
        partial_reason='Storage trajectory is visible, but initial filling, arrival and same-load scale correspondence are not established. A prior covered state does not prove prior storage.',
        observation=notes['gray'],visible_camera_clock_interval=['13:39:33','13:40:05'],
        evidence=[ev('gray',1,34),ev('pre35',1,15),ev('pre36',1,15)],
        stages=[dict(stage='storage_placement',visible_camera_clock_interval=['13:39:53','13:40:05'],clock_uncertainty_seconds=2,
            parked_and_jack_withdrawal_interval=['13:40:01','13:40:05'],content_evidence='Covered gray tank. Contents not visually established.',evidence=[ev('gray',11,34)])],
        limitations=['Do not assign already_stored_tank_relocation negative class: prior storage not evidenced.',
            '13:36:21-to13:39:33 source gap prevents linkage to earlier occluded gray scale load.',
            'No production entry target, starting inventory or weight inferred.'])
    beige=dict(shared,sequence_id='20261021_beige_entry_scale_partial_1341',camera=11,camera_track_id='cam11_beige_fill_1339_to_scale_1345',
        review_status='reviewed_partial_sequence',production_entry_count_target=None,
        observed_loaded_departure_count=1,observed_room15_entry_count=1,entry15_camera_clock_interval=['13:41:25','13:41:30'],
        partial_reason='Fresh filling, loaded departure, entry15 and scale occupancy/departure reviewed. Later beige storage is compatible but kept unlinked across the scale-to-centre trajectory gap.',
        observation=notes['origin'],evidence=[ev('origin',1,69),ev('entry',5,14),ev('scale15',1,13),ev('scale11',0,44)],
        stages=[
            dict(stage='filling_observed',visible_camera_clock_interval=['13:39:18','13:40:33'],clock_uncertainty_seconds=3,
                content_evidence='Fresh placements into beige station tank with cheese visible. Tank already partly filled at source start; no initial contents or block total inferred.',evidence=[ev('origin',1,26)]),
            dict(stage='loaded_departure_11',visible_camera_clock_interval=['13:41:22','13:41:30'],doorway_crossing_camera11_interval=['13:41:25','13:41:30'],clock_uncertainty_seconds=3,evidence=[ev('origin',41,45)]),
            dict(stage='entry_15',visible_camera_clock_interval=['13:41:25','13:41:30'],clock_uncertainty_seconds=3,
                correspondence_basis='One covered beige departure from filling station and corresponding apron operator/manual jack arrival in adjacent15 doorway; two visibly empty opposite-direction tanks are separately tracked.',
                clock_alignment='visually_corresponding_crossing_interval_only',camera_clock_offset_seconds=None,evidence=[ev('origin',42,45),ev('entry',5,14)]),
            dict(stage='scale_visit',visible_camera_clock_interval=['13:41:40','13:46:03'],scale_arrival_interval=['13:41:40','13:41:57'],
                scale_departure_interval=['13:45:45','13:46:03'],clock_uncertainty_seconds=6,
                observation='Occupied platform visible through11 door;15 view mostly occluded by blue containers. No numeric scale reading.',evidence=[ev('origin',48,69),ev('scale15',1,13),ev('scale11',0,33)]),
        ],
        unlinked_followup=dict(status='beige_storage_observed_same_load_identity_gap_retained',production_entry_count_target=None,
            visible_camera_clock_interval=['13:46:53','13:47:13'],parked_and_jack_withdrawal_interval=['13:47:09','13:47:13'],
            observation='Covered beige seen already in centre46:53, stored47:00-10, empty fork withdrawn11-13. Camera11 last partly visible beige staging edge around46:39 and camera15 resumes46:53; not a continuously verified same-load path.',
            source_join='Previous storage source ends47:07; next usable frame47:09 has same tank/row arrangement. Initial adjacent46:58 frame is stale.',
            evidence=[ev('store_a',1,15),ev('store_b',1,21)]),
        limitations=['No completed production-cycle target until scale-to-storage identity is resolved.',
            'Load appearance and timestamps alone do not bridge missing motion.',
            'Source-start stale images retained but not used for synchronization.',
            'Empty returns are two other physical tanks, not the loaded departure.'])
    empty=dict(shared,sequence_id='20261021_two_empty_beige_returns_1340',camera=15,camera_track_id='cam15_two_distinct_empty_beige_returns_1340_1341',
        review_status='accepted_negative_sequence',production_entry_count_target=0,negative_class='empty_crossing',tracked_tank_count=2,trip_count=2,direction='room15_to_room11',
        visible_camera_clock_interval=['13:40:46','13:41:23'],clock_uncertainty_seconds=3,
        trips=[dict(track_id='empty_beige_1_jack',camera15_crossing_interval=['13:40:54','13:40:58'],camera11_crossing_interval=['13:40:54','13:40:57'],
                evidence=[ev('empty',6,18),ev('origin',33,34)]),
            dict(track_id='empty_beige_2_hand_push',camera15_crossing_interval=['13:41:16','13:41:23'],camera11_crossing_interval=['13:41:19','13:41:22'],
                evidence=[ev('empty',26,39),ev('entry',1,3),ev('origin',41,45)])],
        evidence=[ev('empty',6,39),ev('entry',1,3),ev('origin',33,45)],observation=notes['empty'],
        label_scope='Only the two visible empty return trips before subsequent filling. Different freshly loaded beige exits11 during second replacement; not a whole-frame or whole-room zero.')
    jack=dict(shared,sequence_id='20261021_empty_jack_after_beige_storage_1347',camera=15,camera_track_id='cam15_empty_manual_jack_134711',
        review_status='accepted_negative_sequence',production_entry_count_target=0,negative_class='pallet_jack_without_tank',tracked_tank_count=0,
        visible_camera_clock_interval=['13:47:11','13:47:29'],clock_uncertainty_seconds=1,evidence=[ev('store_b',3,21)],
        observation='Manual jack is visibly pulled free after beige storage and moved toward doorway without a tank. The parked beige and adjacent gray remain stationary.',
        label_scope='Only empty jack movement; no zero label for unrelated room activity or inventory.')
    merge(OUT/'reviewed_sequence_labels.json',[gray,beige,empty,jack],'sequence_id')

    casepath=OUT/'sequence_review_case_20261021_390.json';case=read(casepath)
    hist=OUT/'review_history/case390_before_20261031_12.json'
    if not hist.exists():save(hist,dict(saved_at=stamp,record=copy.deepcopy(case)))
    case.update(status='native_review_complete_two_partial_tracks_and_two_empty_returns',reviewed_at=stamp,
        observation='Native context separates gray storage39-40min, two visibly empty beige returns40-41min and fresh filled beige departure/entry41min. Already-stored relocation is NOT established. Loaded beige scale-to-storage identity remains partial.',
        camera15_new_entry_time=None,camera15_new_entry_interval=['13:41:25','13:41:30'],
        scale_visit=['13:41:40','13:46:03'],storage_placement=None,
        reviewed_sequence_ids=[gray['sequence_id'],beige['sequence_id'],empty['sequence_id'],jack['sequence_id']],
        new_evidence=[str(p.relative_to(ROOT)) for p in paths.values()],prior_annotation=str(hist.relative_to(ROOT)))
    save(casepath,case)
    merge(OUT/'sequence_followup_queue.json',[
        dict(candidate_id='20261021_gray_pre_storage_origin_1339',date='20261021',split='train',cycle_id=None,production_entry_count_target=None,
            status='storage_only_partial_origin_gap_retained',reviewed_at=stamp,reviewed_partial_sequence_id=gray['sequence_id'],
            observation=gray['partial_reason'],next_action='Do not classify this as relocation of already stored load. Earlier reviewed15 ends36:21 and later resumes39:33; new source needed to prove origin.',new_evidence=[ev('gray',1,17)]),
        dict(candidate_id='20261021_beige_scale_storage_identity_1346',date='20261021',split='train',cycle_id=None,production_entry_count_target=None,
            status='partial_cycle_storage_candidate_identity_gap',reviewed_at=stamp,reviewed_partial_sequence_id=beige['sequence_id'],
            observation=beige['partial_reason'],next_action='Preserve partial; prioritize source diversity. Scale departure45:45-46:03, later staging edge through46:39, next usable15 already centre46:53. No guessed complete-cycle count.',new_evidence=[ev('scale11',30,41),ev('store_a',1,15),ev('store_b',1,5)])
    ],'candidate_id')

    registry=read(OUT/'object_review_decisions.json');decisions={r['id']:r for r in registry['reviews']}
    draft={r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
    roi_notes={'124':'One beige tank departing filling station, covered top; only object detection label, no load state inferred from cover.',
        '125':'One empty beige replacement at station, clipped at top/left of ROI and partly occluded by hands and conveyor. Visible bottom established in temporal context, but detection record has no load-state target.'}
    for ident,note in roi_notes.items():
        assert ident not in decisions;r=draft[ident]
        decisions[ident]=dict(id=ident,image_sha256=r['sha256'],boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',load_state_reviewed=False,sequence_reviewed=False,
            instance_attributes=[dict(box_index=j,truncated=(b[0]==0 or b[1]==0 or b[2]==r['width'] or b[3]==r['height']),occluded=ident=='125',load_state='unknown_not_annotated') for j,b in enumerate(r['boxes_xyxy'])],
            evidence=[r['source_frame'],r['frames_manifest'],'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_14.jpg'],note=note)
    registry['reviews']=list(decisions.values())
    registry.setdefault('corrections',[]).append('Batch12: native crops124/125 accepted after separate overlay review.123/126 excluded because overlapping liner and background-row extents were not certain; proposed boxes removed before release. Prior labels unchanged.')
    save(OUT/'object_review_decisions.json',registry)
    inventory=read(BASE/'archive_inventory.json');inspected={m['source']['member']:m['source_sha256'] for m in metas.values()}
    for r in inventory['records']:
        if r['member'] in inspected:r.update(pixel_inspected=True,sha256=inspected[r['member']])
    assert not any(r['pixel_inspected'] for r in inventory['records'] if r['split']=='test')
    save(BASE/'archive_inventory.json',inventory)
    total=sum(r['sampled_frames_visually_reviewed'] for r in read(OUT/'screening_source_reviews.json'))
    state['last_completed'] += [
        f'Batch12 inspected289 chronological sample presentations across10 windows on21Oct; {total} total. All extractions finished,25/28Oct untouched.',
        'Native case390 separates gray storage-only partial from fresh beige filling/entry13:41:25-30/scale partial. Later beige storage47min remains unlinked across trajectory gap. Earlier already-covered movement is not accepted as already-stored relocation. Complete cycles remain2; partials10.',
        'Added two negative episodes: two distinct empty beige return trips15-to11 and empty jack after beige storage.21 accepted negatives total, with track-specific scope.',
        'Four native ROI candidates123-126 appended;124/125 accepted with2 boxes,123/126 excluded after uncertain background boundaries in overlay review. Totals127 candidates,83 accepted images,132 accepted boxes,6 drafts,38 exclusions. No training release.'
    ]
    state['priority_next']=[
        'Batch12 all10 windows around21Oct13:35-47 fully inspected and recorded. Case390 native review complete; do not repeat. Storage identity gaps remain partial, not negative relocation or completed-cycle labels.',
        'Need diversity and17Oct validation sequences next. Prioritize metadata coverage before costly origin review.13Oct longer15 windows090821-091619 and102139-102912 not inspected; additional complete-cycle training days still needed.',
        'Known missing intervals:6Oct09:35:55-36:42;15Oct11:15:46-16:23;10Oct10:46:45-50 entry;21Oct0714/0731/0738 storage,0740 entry,13:36:21-39:33 gray origin,13:46:39-53 beige staging/storage identity. Do not repeat searches without new media.',
        'Need true same-load reentry and post-storage relocation examples. Covered gray tank at13:39 does not establish prior storage. Six old object drafts002/003/006/007/010/011 need full native context or justified exclusion.',
        '25/28Oct remain locked and unseen.17Oct is validation only. No training, uploads, original changes or GitHub publication. Update local review and source-backed quality checks.'
    ]
    state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    for name in ['work/append_tank_roi_batch_20261031_12.py','work/record_tank_sequence_batch_20261031_12.py']:
        if name not in state['scripts']:state['scripts'].append(name)
    save(OUT/'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_temporal_samples=289,additional_partial_sequences=2,additional_negative_sequences=2,additional_accepted_images=2,training_started=False)))


if __name__=='__main__':main()
