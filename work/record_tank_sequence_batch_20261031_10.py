"""Persist inspected later21Oct trajectories; incomplete storage stays partial."""
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read, save, merge, evidence

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/tank_transfer_training_v1'
OUT=BASE/'dataset_v1'
RUN='sequence_review_20261031_10'


def main():
    state=read(OUT/'continuation_state.json')
    if RUN in state.get('completed_curation_runs',[]):
        print('Already recorded:',RUN); return
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    windows={
        'origin':('origin_scale_0721_cam11',100),
        'entry':('entry_scale_0725_cam15',23),
        'staging':('storage_0730_cam15',17),
        'scale':('scale_departure_0730_cam15',21),
        'second':('second_entry_0732_cam15',23),
        'door':('departure_boundary_0725_cam11',18),
    }
    paths={k:OUT/'sequence_review/20261021'/v[0]/'frames.json' for k,v in windows.items()}
    metas={k:read(p) for k,p in paths.items()}
    for k,m in metas.items():
        assert len(m['samples'])==windows[k][1]
        assert m['source']['date']=='20261021' and m['source']['split']=='train'
        assert all((ROOT/s['image']).exists() for s in m['samples'])
    # Manually read visible camera clocks from the inspected image sequence.
    clocks={
        'origin':{0:'07:21:33',1:'07:21:52',4:'07:22:16',5:'07:22:24',15:'07:23:44',17:'07:24:00',
                  18:'07:24:08',22:'07:24:40',23:'07:24:48',25:'07:25:04',26:'07:25:12',27:'07:25:20',
                  28:'07:25:28',30:'07:25:44',31:'07:25:52',32:'07:26:00',60:'07:29:44',65:'07:30:24',
                  66:'07:30:32',78:'07:32:08',79:'07:32:16',80:'07:32:24',81:'07:32:32',82:'07:32:40',
                  83:'07:32:48',84:'07:32:56',85:'07:33:04',90:'07:33:44',91:'07:33:52',99:'07:34:56'},
        'entry':{0:'07:25:09',1:'07:25:17',2:'07:25:18',7:'07:25:23',12:'07:25:28',22:'07:25:38'},
        'staging':{0:'07:30:25',1:'07:30:41',5:'07:30:45',9:'07:30:49',10:'07:30:50',16:'07:30:56'},
        'scale':{0:'07:30:16',1:'07:30:20',8:'07:30:27',15:'07:30:34',16:'07:30:35',19:'07:30:38',20:'07:30:39'},
        'second':{0:'07:32:24',1:'07:32:37',4:'07:32:40',5:'07:32:41',8:'07:32:44',9:'07:32:45',
                  14:'07:32:50',15:'07:32:51',16:'07:32:52',17:'07:32:53',18:'07:32:54',22:'07:32:58'},
        'door':{0:'07:25:02',6:'07:25:08',9:'07:25:11',10:'07:25:12',11:'07:25:13',14:'07:25:16',15:'07:25:17',17:'07:25:19'},
    }
    notes={
        'origin':'Three distinct gray loads must not be conflated. One gray is ALREADY on the scale at first frame and leaves07:22:16-24; its filling origin was not reviewed. A different station gray is visibly filled07:21:52-24:40, covered24:48, pulled away25:04, crosses the door25:12-17 and is on the scale by25:28. A separate visibly empty gray replacement moves from local row to station25:12-28, then is filled from around25:52/26:00 until32:16. The first new gray clears the scale30:24-32; camera15 shows staging, not storage. Empty jack returns32:08-16. The second station gray is covered32:24, leaves32:32-40, crosses32:48 and is out by32:56. A distinct visibly empty beige replacement moves from local row to station32:48-56; later filling is separate. A gray is subsequently placed on the scale33:44-52 and remains through34:56; keep this scale follow-up pending camera15 trajectory confirmation. Initial07:21:33 is stale; next sample reads21:52.',
        'entry':'First noninitial07:25:17 already shows the incoming gray partly hidden behind fixed blue containers. It turns17-23 and moves right onto scale23-28, remaining through38. The source initial25:09 frame is stale and is not an exact preceding crossing anchor. Camera11 supplies the departure25:12-17; exact camera15 threshold crossing is unsampled here. Stationary containers and room11 background stock are separate instances, not additional arrivals.',
        'staging':'Despite the extraction folder name storage, no storage placement occurs in these inspected samples. Initial30:25 is stale, first noninitial30:41. Gray tank and upright jack remain staged behind fixed blue containers near the doorway through30:56. Operator walks into aisle41-45 without jack, turns back46-49, and returns50-56. The missing interval before later empty-jack return32:08 prevents storage identity/placement certification.',
        'scale':'Initial30:16 is stale, first noninitial30:20. Operator pulls gray with white top fittings from scale through occlusion behind fixed blue container toward door/aisle30:27-34. It remains staged35-39, jack upright; operator steps away without jack38-39. Camera11 platform is occupied30:24 and empty32. No storage placement visible. Last inspected39 joins next source first noninitial41 with two seconds unobserved, not assumed exhaustive continuity.',
        'second':'Initial32:24 is stale, first noninitial32:37. Door clear37-40; operator and gray appear41-44. One gray crosses shared doorway45-50 and is clearly inside15 aisle51-53, then turns into staging54-58 with manual jack. Filling/departure counterpart in camera11 is distinct from previous25-minute load. Scale visit and storage remain pending later trajectory review; no new production label for stationary room inventory.',
        'door':'Dense one-second camera11 samples: loaded covered gray approaches25:08-11, reaches threshold25:12, crosses13-16 and clears room11 by17. No invented scalar synchronization. Camera15 first noninitial17 already contains the arriving tank behind fixed blue bins; this window does not supply exact camera15 boundary timing.',
    }
    reviews=[]
    for k,m in metas.items():
        reviews.append(dict(review_id='20261021/'+windows[k][0],reviewed_at=stamp,reviewer='assistant_visual_review',
            source_member=m['source']['member'],source_sha256=m['source_sha256'],date='20261021',camera=m['source']['camera'],split='train',
            frames_manifest=str(paths[k].relative_to(ROOT)),sampled_frames_visually_reviewed=len(m['samples']),reviewed_sheets=m['sheets'],
            review_scope='All chronological contact-sheet samples visually inspected; selected native full frames and separate object overlays inspected. Not exhaustive native-frame viewing.',
            visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],
                visible_camera_clock=t,clock_read_uncertainty_seconds=1,image=m['samples'][i]['image'],
                usable_for_clock_alignment=not(k!='door' and i==0)) for i,t in clocks[k].items()],
            observation=notes[k],accepted_complete_cycle=False,
            clock_warning='Source initial stale frames excluded from alignment. Camera clocks, relative PTS and absolute source PTS are separate. No exact scalar offset asserted.'))
    merge(OUT/'screening_source_reviews.json',reviews,'review_id')
    def ev(k,a,b): return evidence(metas[k],a,b,paths[k])
    shared=dict(date='20261021',split='train',reviewer='assistant_visual_review',reviewed_at=stamp,cycle_id=None,dataset_release_accepted=False)
    partial1=dict(shared,sequence_id='20261021_gray_filling_arrival_scale_partial_0725',camera='11+15',
        camera_track_id='cam11_gray_station_0724_to_cam15_scale_0725',review_status='reviewed_partial_sequence',
        production_entry_count_target=None,observed_loaded_departure_count=1,observed_room15_arrival_count=1,
        observed_room15_entry_count=None,entry15_camera_clock_interval=None,room15_arrival_observed_by='07:25:17',
        partial_reason='Fresh filling, departure, matching room15 arrival and scale trajectory visible. Exact camera15 crossing is unsampled and final storage missing.',
        observation=notes['entry']+' '+notes['scale']+' '+notes['staging'],
        evidence=[ev('origin',1,28),ev('door',0,17),ev('entry',1,22),ev('origin',28,66),ev('scale',1,20),ev('staging',1,16)],
        cross_camera_identity='Ordered shared-door trajectory, body/cover geometry and jack movement support corresponding arrival; not a color-only match or precise clock calibration.',
        stages=[
            dict(stage='filling_observed',visible_camera_clock_interval=['07:21:52','07:24:40'],clock_uncertainty_seconds=8,
                 content_evidence='Cheese blocks and placements visible at station before covering; existing initial contents unknown.',evidence=[ev('origin',1,23)]),
            dict(stage='loaded_departure_11',visible_camera_clock_interval=['07:25:04','07:25:17'],
                 doorway_crossing_camera11_interval=['07:25:12','07:25:17'],clock_uncertainty_seconds=1,evidence=[ev('origin',25,27),ev('door',10,15)]),
            dict(stage='entry_15',observability='arrival_visible_crossing_not_sampled',visible_camera_clock_interval=None,
                 arrival_observed_by='07:25:17',clock_uncertainty_seconds=1,evidence=[ev('entry',1,7)],
                 observation='Arrival inside15 is visible; do not report a fabricated exact threshold timestamp from a stale initial frame.'),
            dict(stage='scale_visit',visible_camera_clock_interval=['07:25:23','07:30:34'],
                 scale_arrival_interval=['07:25:23','07:25:28'],scale_departure_interval=['07:30:24','07:30:34'],clock_uncertainty_seconds=8,
                 evidence=[ev('entry',7,22),ev('origin',28,66),ev('scale',1,20)],observation='Scale occupancy and later movement corroborated by both views; no kilograms inferred.')],
        storage_gap_search=dict(status='available_export_gap_prevents_storage_label',last_camera15_clock='07:30:56',
            next_camera15_initial_stale_clock='07:32:24',next_camera15_noninitial_clock='07:32:37',
            empty_jack_return_camera11_interval=['07:32:08','07:32:16'],evidence=[ev('staging',1,16),ev('second',0,1),ev('origin',78,79)],
            observation='Gray remains staged at30:56; empty jack is back in11 by32:08-16. No export bridges the intervening load trajectory. Later static tank or empty jack does not prove storage location/identity.',
            next_action='Keep partial; do not repeat the same available-source gap search.'),
        limitations=['No initial-empty or cheese-block-total assertion.','No storage completion or numeric production target assigned.','Folder names are extraction intentions, not action labels.'])
    partial2=dict(shared,sequence_id='20261021_gray_filling_entry_partial_0732',camera='11+15',
        camera_track_id='cam11_gray_station_0726_to_cam15_entry_0732',review_status='reviewed_partial_sequence',
        production_entry_count_target=None,observed_loaded_departure_count=1,observed_room15_entry_count=1,
        entry15_camera_clock_interval=['07:32:45','07:32:50'],clock_uncertainty_seconds=1,
        partial_reason='Fresh filling, loaded departure and corresponding room15 entry reviewed. Later scale and storage trajectory review remains pending.',
        observation=notes['second'],evidence=[ev('origin',27,84),ev('second',1,22)],
        cross_camera_identity='Distinct replacement-to-fill-to-departure track and corresponding doorway trajectory; color alone not used for identity.',
        stages=[
            dict(stage='filling_observed',visible_camera_clock_interval=['07:26:00','07:32:16'],clock_uncertainty_seconds=8,
                 content_evidence='Gray replacement initially shows empty interior at25:20-28; later cheese placements visible. Filling start is bounded, not a block count.',evidence=[ev('origin',27,32),ev('origin',32,79)]),
            dict(stage='loaded_departure_11',visible_camera_clock_interval=['07:32:32','07:32:56'],
                 doorway_crossing_camera11_interval=['07:32:40','07:32:56'],clock_uncertainty_seconds=8,evidence=[ev('origin',80,84)]),
            dict(stage='entry_15',visible_camera_clock_interval=['07:32:45','07:32:50'],clock_uncertainty_seconds=1,
                 observation='Tank partially occluded by operator/fixed containers at threshold, then visible inside aisle51-53 and staging54-58.',evidence=[ev('second',5,22)])],
        unlinked_followup=dict(observation='Camera11 shows gray being placed onto scale07:33:44-52 and remaining through34:56. Review next camera15 windows before attaching this as confirmed same-load scale trajectory or storage.',
             evidence=[ev('origin',90,99)],production_entry_count_target=None),
        limitations=['Sampled chronology; exact scalar camera offset not asserted.','No complete cycle or storage placement label yet.'])
    negatives=[
        dict(shared,sequence_id='20261021_empty_gray_replacement_072512',camera=11,camera_track_id='cam11_empty_gray_row_to_station_0725',
             review_status='accepted_negative_sequence',production_entry_count_target=0,negative_class='empty_tank_internal_reposition',tracked_tank_count=1,
             visible_camera_clock_interval=['07:25:12','07:25:28'],clock_uncertainty_seconds=8,evidence=[ev('origin',26,28)],
             observation='One visibly empty gray replacement moves from local row to filling station while a different loaded gray leaves.',
             content_evidence='Exposed lined bottom visible at25:20-28 before subsequent cheese placements.',
             label_scope='Zero only for the empty internal replacement before filling; loaded departure and later filling are separate.'),
        dict(shared,sequence_id='20261021_empty_beige_replacement_073248',camera=11,camera_track_id='cam11_empty_beige_row_to_station_0732',
             review_status='accepted_negative_sequence',production_entry_count_target=0,negative_class='empty_tank_internal_reposition',tracked_tank_count=1,
             visible_camera_clock_interval=['07:32:48','07:32:56'],clock_uncertainty_seconds=8,evidence=[ev('origin',83,84)],
             observation='One visibly empty beige replacement moves from row into station while another gray load exits.',
             content_evidence='Open lined beige interior/bottom visible at32:56 before later filling.',
             label_scope='Only the empty replacement track; no whole-frame negative and no claim that later filling is negative.'),
        dict(shared,sequence_id='20261021_empty_manual_jack_return_073208',camera=11,camera_track_id='cam11_empty_jack_return_0732',
             review_status='accepted_negative_sequence',production_entry_count_target=0,negative_class='pallet_jack_without_tank',tracked_tank_count=0,
             visible_camera_clock_interval=['07:32:08','07:32:16'],clock_uncertainty_seconds=8,evidence=[ev('origin',78,79)],
             observation='Operator returns through shared doorway with empty manual jack, then engages next station load. No tank carried during the return.',
             label_scope='Empty-jack movement only, not simultaneous station filling or evidence of prior tank storage.')]
    merge(OUT/'reviewed_sequence_labels.json',[partial1,partial2]+negatives,'sequence_id')
    merge(OUT/'sequence_followup_queue.json',[
        dict(candidate_id='20261021_gray_storage_gap_0731',date='20261021',split='train',cycle_id=None,production_entry_count_target=None,
             status='reviewed_partial_storage_missing_from_available_exports',reviewed_at=stamp,reviewed_partial_sequence_id=partial1['sequence_id'],
             observation=partial1['partial_reason'],new_evidence=[ev('staging',16,16),ev('origin',78,79)],
             next_action='Do not repeat30:56-to32:08 storage-gap search without additional source.'),
        dict(candidate_id='20261021_gray_scale_storage_followup_0733',date='20261021',split='train',cycle_id=None,production_entry_count_target=None,
             status='pending_scale_storage_trajectory_review',reviewed_at=stamp,reviewed_partial_sequence_id=partial2['sequence_id'],
             observation=partial2['partial_reason'],new_evidence=[ev('second',15,22),ev('origin',90,99)],
             next_action='Review21Oct camera15 files073322-073346,073434-073516,073706-073722 plus camera11 next073452-074314. First verify source coverage through scale-to-storage; preserve partial if gaps remain.')],'candidate_id')

    registry=read(OUT/'object_review_decisions.json'); decisions={r['id']:r for r in registry['reviews']}
    drafts={r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
    roi_notes={
        '112':'Filled station gray with visible cheese; person/conveyor occlusion and crop-bottom truncation. Separate stationary gray fragment at upper right retained.',
        '113':'Covered departing gray, partly occluded by operator; crop-right truncation. Cover alone is not a cheese attribute.',
        '114':'Empty gray station replacement with exposed bottom; person and conveyor occlusion, right/lower crop truncation.',
        '115':'Empty beige station replacement with exposed bottom; worker/conveyor occlusion. Crop tightened before acceptance to avoid ambiguous border fragment; top/right/bottom truncation retained.',
        '117':'Separate stationary beige and gray metal-hoop containers plus blue tank at crop edge. All are existing room inventory, not new production arrivals.'}
    for ident,note in roi_notes.items():
        assert ident not in decisions
        r=drafts[ident]
        decisions[ident]=dict(id=ident,image_sha256=r['sha256'],boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',load_state_reviewed=False,sequence_reviewed=False,
            instance_attributes=[dict(box_index=j,truncated=(b[0]==0 or b[1]==0 or b[2]==r['width'] or b[3]==r['height']),
                occluded=(ident in ['112','113','114','115'] and j==0) or (ident=='117' and j>0),load_state='unknown_not_annotated') for j,b in enumerate(r['boxes_xyxy'])],
            evidence=[r['source_frame'],r['frames_manifest'],'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_'+('12' if ident=='112' else '13')+'.jpg'],note=note)
    registry['reviews']=list(decisions.values())
    r=drafts['116']
    registry.setdefault('excluded_roi_reviews',[]).append(dict(id='116',image_sha256=r['sha256'],reviewer='assistant_visual_review',reviewed_at=stamp,
        reason='Overlapping tank/cart boundaries behind fixed blue container remain ambiguous. Excluded after native context and attempted overlay review; no guessed object box accepted.',
        evidence=[r['source_frame'],r['frames_manifest'],'outputs/tank_transfer_training_v1/detector_v1/sheets/candidate_batch10.jpg']))
    registry.setdefault('corrections',[]).append('Batch10:112-117 appended; five ROIs/eight boxes accepted after separate overlays,116 excluded.115 tightened before acceptance; prior accepted annotations unchanged.')
    save(OUT/'object_review_decisions.json',registry)
    inventory=read(BASE/'archive_inventory.json'); inspected={m['source']['member']:m['source_sha256'] for m in metas.values()}
    for r in inventory['records']:
        if r['member'] in inspected:r.update(pixel_inspected=True,sha256=inspected[r['member']])
    assert not any(r['pixel_inspected'] for r in inventory['records'] if r['split']=='test')
    save(BASE/'archive_inventory.json',inventory)
    total=sum(r['sampled_frames_visually_reviewed'] for r in read(OUT/'screening_source_reviews.json'))
    state['last_completed'] += [
        f'Batch10 inspected202 chronological sample presentations across6 later21Oct windows; {total} total. All extraction finished;25/28Oct untouched.',
        'Two21Oct gray tracks added as partials:25-minute fresh fill/departure/arrival/scale lacks exact15 entry crossing and storage;32-minute fresh fill/departure/entry45-50 awaits subsequent scale/storage review. Complete cycles remain2.',
        'Added two empty internal replacements(gray25:12-28, beige32:48-56) and one empty-jack return32:08-16 as track-scoped negatives. Totals17 negatives and7 partials.',
        'Six native ROI candidates112-117 appended; five images/eight boxes approved after separate overlays,116 excluded. Totals118 candidates,76 approved ROI images,124 boxes,6 drafts,36 exclusions. Training remains unreleased.'
    ]
    state['priority_next']=[
        'Batch10 completed origin_scale_0721_cam11,entry_scale_0725_cam15,storage_0730_cam15,scale_departure_0730_cam15,second_entry_0732_cam15,departure_boundary_0725_cam11.202 samples inspected; do not repeat. No extraction active.',
        'Next queued21Oct gray0732 entry: review15 files073322-073346,073434-073516,073706-073722 and11 next073452-074314 for scale/storage. Check coverage first; file names/PTS are not synchronization.',
        'Do not repeat unresolved gaps:6Oct entry09:35:55-36:42;15Oct scale-storage11:15:46-16:23;10Oct entry10:46:45-50;21Oct0714 storage and0731 storage30:56-to32:08. Keep partials.',
        'Need complete cycles on additional training days,17Oct validation, already-stored relocation and same-load-reentry negatives.25/28Oct remain locked.',
        'Six drafts002/003/006/007/010/011 remain. Expand native context and resolve tank/cart/occluded background boundaries before accepting. Preserve all prior decisions; no training/uploads/original changes.'
    ]
    state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    for name in ['work/append_tank_roi_batch_20261031_10.py','work/record_tank_sequence_batch_20261031_10.py']:
        if name not in state['scripts']:state['scripts'].append(name)
    save(OUT/'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_temporal_samples=202,additional_partial_sequences=2,additional_negative_sequences=3,additional_accepted_images=5,training_started=False)))


if __name__=='__main__':main()
