"""Record inspected 21Oct evidence, retaining the missing storage stage."""
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read, save, merge, evidence

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/tank_transfer_training_v1'
OUT=BASE/'dataset_v1'
RUN='sequence_review_20261031_09'

def main():
    state=read(OUT/'continuation_state.json')
    if RUN in state.get('completed_curation_runs',[]):
        print('Already recorded:',RUN); return
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    windows={
        'origin':('gray_origin_0705_cam11',69),
        'entry':('entry_0709_cam15',22),
        'scale':('scale_followup_0710_cam11',90),
        'room15':('scale_storage_0710_cam15',17),
        'return':('scale_exit_0716_cam15',15),
        'door':('departure_boundary_0709_cam11',16),
    }
    paths={k:OUT/'sequence_review/20261021'/n/'frames.json' for k,(n,_) in windows.items()}
    metas={k:read(p) for k,p in paths.items()}
    for k,m in metas.items():
        assert len(m['samples'])==windows[k][1]
        assert m['source']['date']=='20261021' and m['source']['split']=='train'
        assert all((ROOT/s['image']).is_file() for s in m['samples'])
    # These are visual clock readings, not filename/PTS clock conversions.
    clocks={
        'origin':{0:'07:05:54',1:'07:06:13',2:'07:06:17',3:'07:06:21',6:'07:06:33',12:'07:06:57',18:'07:07:22',24:'07:07:46',28:'07:08:02',32:'07:08:18',36:'07:08:34',38:'07:08:42',39:'07:08:46',40:'07:08:50',41:'07:08:54',42:'07:08:58',43:'07:09:02',44:'07:09:06',45:'07:09:10',48:'07:09:22',49:'07:09:26',54:'07:09:46',60:'07:10:10',66:'07:10:34',68:'07:10:42'},
        'entry':{0:'07:08:39',1:'07:08:59',2:'07:09:00',3:'07:09:01',4:'07:09:02',5:'07:09:03',6:'07:09:04',7:'07:09:05',8:'07:09:06',9:'07:09:07',10:'07:09:08',11:'07:09:09',12:'07:09:10',16:'07:09:14',18:'07:09:16',21:'07:09:19'},
        'scale':{0:'07:10:34',1:'07:10:48',6:'07:11:08',12:'07:11:32',18:'07:11:56',24:'07:12:20',30:'07:12:44',36:'07:13:08',42:'07:13:32',48:'07:13:56',54:'07:14:20',56:'07:14:28',57:'07:14:32',58:'07:14:36',59:'07:14:40',60:'07:14:44',61:'07:14:48',66:'07:15:08',72:'07:15:32',78:'07:15:56',84:'07:16:20',86:'07:16:28',87:'07:16:32',88:'07:16:36',89:'07:16:40'},
        'room15':{0:'07:10:49',1:'07:10:59',2:'07:11:01',6:'07:11:09',12:'07:11:21',16:'07:11:29'},
        'return':{0:'07:16:05',1:'07:16:18',2:'07:16:19',5:'07:16:22',8:'07:16:25',9:'07:16:26',10:'07:16:27',11:'07:16:28',12:'07:16:29',13:'07:16:30',14:'07:16:31'},
        'door':{0:'07:08:59',1:'07:09:00',2:'07:09:01',3:'07:09:02',4:'07:09:03',5:'07:09:04',6:'07:09:05',7:'07:09:06',8:'07:09:07',9:'07:09:08',10:'07:09:09',11:'07:09:10',12:'07:09:11',13:'07:09:12',14:'07:09:13',15:'07:09:14'},
    }
    notes={
        'origin':'Workers visibly place cheese in gray station tank07:06:13-08:42. They cover it07:08:46-50; the manual jack pulls that tank from the station07:08:54-09:02 and through the shared door07:09:04-09. A different visibly empty gray tank moves from the local row to the station07:08:54-09:06; next filling begins by09:10. Through doorway, the departed tank moves onto scale07:09:22-26 and remains through07:10:42. Initial07:05:54 frame is stale relative to next07:06:13; actual inspected tail extends beyond filename end. Neither start contents nor block total inferred.',
        'entry':'Gray tank with flat white covers follows the operator/manual jack through shared door07:09:05-09, partly hidden by operator and fixed blue bins. It then turns in staging area07:09:10-19. Ordered trajectory, geometry, covers and jack movement correspond to camera11; color alone is not the identity basis. Initial07:08:39 frame is stale; first noninitial07:08:59. One observed room15 entry, but storage remains unobserved.',
        'scale':'Same scale-side gray tank remains visible through camera11 doorway07:10:48-14:36; jack engages around14:28, tank moves right14:40-44, and platform is empty14:48. No loaded return into11 seen. Its storage destination is outside camera11 view. Empty manual jack returns15-to11 at16:28-40. Initial07:10:34 frame is stale; previous source last inspected10:42 and next noninitial10:48 retain a six-second join uncertainty, not asserted exhaustive continuity.',
        'room15':'Room15 operators handle items near the scale/doorway07:10:59-11:29; the gray scale load is mostly occluded behind fixed blue containers. Paired camera11 retains platform evidence. No storage placement or additional production tank inferred here. Fixed blue containers, metal-hoop holding tanks and empty inventory row remain separate existing objects. Initial07:10:49 frame is stale.',
        'return':'After initial stale07:16:05, operator approaches from left with visibly empty manual pallet jack07:16:18-25, turns toward doorway16:26-29 and passes into11 by16:30-31. Corresponding camera11 shows empty forks16:28 and operator16:32-40. No tank is being carried. This empty-jack return does not establish where the earlier gray tank was stored.',
        'door':'One-second camera11 samples refine loaded gray crossing: approaches07:09:02-03, reaches threshold09:04, body crosses09:05-08 and clears11 by09:09. No tank in opening09:10-14. Empty replacement is a separate foreground track. Retain bounded camera-clock event intervals; no exact scalar synchronization estimated.',
    }
    reviews=[]
    for k,m in metas.items():
        reviews.append(dict(review_id='20261021/'+windows[k][0],reviewed_at=stamp,reviewer='assistant_visual_review',
            source_member=m['source']['member'],source_sha256=m['source_sha256'],date='20261021',camera=m['source']['camera'],split='train',
            frames_manifest=str(paths[k].relative_to(ROOT)),sampled_frames_visually_reviewed=len(m['samples']),reviewed_sheets=m['sheets'],
            review_scope='Every chronological contact-sheet sample inspected; selected native full-frame context and separate object overlays inspected. Not exhaustive native-frame viewing.',
            visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],
                relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],visible_camera_clock=t,clock_read_uncertainty_seconds=1,
                image=m['samples'][i]['image'],usable_for_clock_alignment=not(k!='door' and i==0)) for i,t in clocks[k].items()],
            observation=notes[k],accepted_complete_cycle=False,
            clock_warning='Initial stale frames retained but excluded from alignment; PTS and observed clocks remain distinct. No exact scalar camera offset asserted.'))
    merge(OUT/'screening_source_reviews.json',reviews,'review_id')
    def ev(k,a,b):return evidence(metas[k],a,b,paths[k])
    shared=dict(date='20261021',split='train',reviewer='assistant_visual_review',reviewed_at=stamp,cycle_id=None,dataset_release_accepted=False)
    partial=dict(shared,sequence_id='20261021_gray_filling_entry_scale_partial_0709',camera='11+15',
        camera_track_id='cam11_gray_station_0708_to_cam15_scale_0709',review_status='reviewed_partial_sequence',
        production_entry_count_target=None,observed_loaded_departure_count=1,observed_room15_entry_count=1,
        partial_reason='Fresh filling, loaded departure, corresponding room15 entry and scale visit are visible. Room15 exports miss scale departure-to-storage interval; completed cycle cannot be certified.',
        observation=notes['origin']+' '+notes['entry'],
        evidence=[ev('origin',1,68),ev('door',0,15),ev('entry',1,21),ev('scale',1,61),ev('room15',1,16)],
        cross_camera_identity='Reviewed event correspondence from shared doorway trajectory, tank/cover geometry and manual-jack movement. No color-only match or exact scalar clock offset.',
        entry15_camera_clock_interval=['07:09:05','07:09:09'],clock_uncertainty_seconds=1,
        stages=[
            dict(stage='filling_observed',visible_camera_clock_interval=['07:06:13','07:08:42'],clock_uncertainty_seconds=4,
                 content_evidence='Cheese blocks and placements visible in same gray station tank before covers are placed.',evidence=[ev('origin',1,38)]),
            dict(stage='loaded_departure_11',visible_camera_clock_interval=['07:08:54','07:09:09'],
                 doorway_crossing_camera11_interval=['07:09:04','07:09:09'],clock_uncertainty_seconds=1,evidence=[ev('origin',41,44),ev('door',5,10)]),
            dict(stage='entry_15',visible_camera_clock_interval=['07:09:05','07:09:09'],clock_uncertainty_seconds=1,
                 observation='Partial doorway occlusion; one corresponding incoming gray tank, followed into staging.',evidence=[ev('entry',7,21),ev('door',6,10)]),
            dict(stage='scale_visit',visible_camera_clock_interval=['07:09:22','07:14:48'],
                 scale_arrival_interval=['07:09:22','07:09:26'],scale_departure_interval=['07:14:36','07:14:48'],
                 clock_uncertainty_seconds=4,evidence=[ev('origin',48,68),ev('scale',1,61),ev('room15',1,16)],
                 observation='Platform occupancy and later movement observed mainly through camera11 doorway. No weight value inferred. Six-second adjacent-source join uncertainty retained.')],
        storage_gap_search=dict(status='available_export_gap_prevents_storage_label',
            last_camera15_clock='07:11:29',next_camera15_initial_stale_clock='07:16:05',next_camera15_noninitial_clock='07:16:18',
            evidence=[ev('room15',16,16),ev('return',0,14),ev('scale',58,61)],
            metadata_search_locations=['C:/Users/evant/Desktop/Facility_Camera_Videos/2026-10-21','work/facility_media','C:/Users/evant/Desktop/camera.zip'],
            observation='Older desktop and extracted-media copies have the same preceding071049-071129 and following071606-071631 filename intervals; no source bridging the0714 scale departure was found. No extra pixels from those duplicate exports inspected.',
            next_action='Do not repeat same gap search. Need additional source covering scale departure through parking, or retain partial. Empty-jack return is not proof of storage identity.'),
        limitations=['Station tank already contains cheese at first inspected frame; no initial-empty or cheese-block-total assertion.',
            'Storage stage absent, so no complete-cycle production target or cycle ID assigned.',
            'Clock intervals are visually read; sampled chronology is not exhaustive frame inspection or independently certified ground truth.',
            'The folder names scale_storage and scale_exit are extraction intentions, not accepted action labels.'])
    negatives=[
        dict(shared,sequence_id='20261021_empty_gray_replacement_070854',camera=11,
             camera_track_id='cam11_empty_gray_row_to_station_070854',review_status='accepted_negative_sequence',production_entry_count_target=0,
             negative_class='empty_tank_internal_reposition',tracked_tank_count=1,visible_camera_clock_interval=['07:08:54','07:09:06'],clock_uncertainty_seconds=4,
             evidence=[ev('origin',41,44)],observation='One visibly empty gray replacement is pushed from local tank row to the filling station while a DIFFERENT covered loaded gray leaves.',
             content_evidence='Exposed gray interior and bottom visible before first placements by07:09:10.',
             label_scope='Zero applies only to the internal empty replacement movement before filling. Simultaneous loaded departure and subsequent filling are separate.'),
        dict(shared,sequence_id='20261021_empty_manual_jack_return_071618',camera='15+11',
             camera_track_id='cam15_empty_manual_jack_to_cam11_0716',review_status='accepted_negative_sequence',production_entry_count_target=0,
             negative_class='pallet_jack_without_tank',tracked_tank_count=0,visible_camera_clock_interval=['07:16:18','07:16:40'],clock_uncertainty_seconds=4,
             evidence=[ev('return',1,14),ev('scale',86,89)],observation=notes['return'],
             label_scope='Only the visibly empty manual jack crossing; existing room15 tanks and simultaneous room11 filling are not whole-frame negatives.')]
    merge(OUT/'reviewed_sequence_labels.json',[partial]+negatives,'sequence_id')
    followup=dict(candidate_id='20261021_gray_storage_gap_0714',date='20261021',split='train',cycle_id=None,production_entry_count_target=None,
        status='reviewed_partial_storage_missing_from_available_exports',reviewed_at=stamp,reviewed_partial_sequence_id=partial['sequence_id'],
        observation=partial['partial_reason'],new_evidence=[ev('scale',58,61),ev('room15',16,16),ev('return',0,14)],
        next_action='Do not repeat0711-0716 storage-gap search. Continue another well-covered paired interval/day; preserve this partial.')
    merge(OUT/'sequence_followup_queue.json',[followup],'candidate_id')
    registry=read(OUT/'object_review_decisions.json')
    decisions={r['id']:r for r in registry['reviews']}
    drafts={r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
    roi_notes={
        '106':'Cheese-filled gray station tank; operator/conveyor occlusion and lower crop truncation. Native context and independent overlay inspected.',
        '107':'Covered departing gray in aisle. Left crop clips body edge; nearby empty replacement remains outside crop. Cover alone is not a load attribute.',
        '108':'Empty gray replacement being positioned at station; exposed interior, worker occlusion. Top crop truncation retained; later filling not included in negative episode.',
        '109':'Covered gray at shared threshold, partly hidden by doorpost; left/lower crop truncation retained.',
        '111':'Arriving covered gray and separate crop-edge stationary blue bin. Both boxes kept; background bin is not an additional arriving load.'}
    for ident,note in roi_notes.items():
        assert ident not in decisions
        r=drafts[ident]
        decisions[ident]=dict(id=ident,image_sha256=r['sha256'],boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',load_state_reviewed=False,sequence_reviewed=False,
            instance_attributes=[dict(box_index=j,truncated=(b[0]==0 or b[1]==0 or b[2]==r['width'] or b[3]==r['height']),
                occluded=(ident in ['106','108','109'] or (ident=='111' and j==0)),load_state='unknown_not_annotated') for j,b in enumerate(r['boxes_xyxy'])],
            evidence=[r['source_frame'],r['frames_manifest'],'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_12.jpg'],note=note)
    registry['reviews']=list(decisions.values())
    r=drafts['110']
    registry.setdefault('excluded_roi_reviews',[]).append(dict(id='110',image_sha256=r['sha256'],reviewer='assistant_visual_review',reviewed_at=stamp,
        reason='Doorway/worker occlusion and neighboring background body boundaries not sufficiently clear for clean object supervision.',
        evidence=[r['source_frame'],r['frames_manifest'],'outputs/tank_transfer_training_v1/detector_v1/sheets/candidate_batch09.jpg']))
    registry.setdefault('corrections',[]).append('Batch09 adds106-111: five ROI images and six boxes pass separate overlay review;110 excluded for uncertain occluded boundaries. Prior annotations preserved.')
    save(OUT/'object_review_decisions.json',registry)
    inventory=read(BASE/'archive_inventory.json')
    inspected={m['source']['member']:m['source_sha256'] for m in metas.values()}
    for r in inventory['records']:
        if r['member'] in inspected:r.update(pixel_inspected=True,sha256=inspected[r['member']])
    assert not any(r['pixel_inspected'] for r in inventory['records'] if r['split']=='test')
    save(BASE/'archive_inventory.json',inventory)
    total=sum(r['sampled_frames_visually_reviewed'] for r in read(OUT/'screening_source_reviews.json'))
    state['last_completed'] += [
        f'Batch09 inspected229 chronological sample presentations across6 windows on21Oct; {total} total. All extraction finished;25/28Oct untouched.',
        '21Oct gray fresh filling, departure, room15 entry07:09:05-09 and scale visit recorded as PARTIAL. Scale departure07:14:36-48 falls in missing room15 interval07:11:29-16:18; no storage label or complete-cycle target invented.',
        'Added two track-scoped negatives: empty gray replacement07:08:54-09:06 and empty manual jack return07:16:18-40. Totals2 complete cycles,14 negative episodes,5 partials.',
        'Six native ROI candidates106-111 appended; five images/six boxes approved after independent overlays,110 excluded. Totals112 candidates,71 approved ROI images,116 boxes,6 drafts,35 exclusions. Training remains unreleased.'
    ]
    state['priority_next']=[
        'Batch09 completed21Oct gray_origin_0705_cam11,entry_0709_cam15,scale_followup_0710_cam11,scale_storage_0710_cam15,scale_exit_0716_cam15,departure_boundary_0709_cam11.229 presentations inspected; do not repeat. No extraction active.',
        'Before extracting another21/23Oct cycle, inspect filename interval coverage in camera15 for expected entry AND scale-to-storage. This is only scheduling metadata; use actual pixels/clocks for labels. Need diverse complete cycles and17Oct validation;25/28Oct remain locked.',
        'Do not repeat unresolved gaps:6Oct entry09:35:55-36:42;15Oct scale-to-storage11:15:46-16:23;10Oct entry10:46:45-50;21Oct storage after scale departure07:14:36-48 (camera15 missing11:29-16:18). Keep partials.',
        'Need already-stored relocation and same-load-reentry negatives; avoid inflating counts with duplicate tracks or correlated frames.',
        'Six drafts002/003/006/007/010/011 remain. Expand native context before accepting.17Oct validation must retain split; no training/uploads/original changes.'
    ]
    state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    for name in ['work/append_tank_roi_batch_20261031_09.py','work/record_tank_sequence_batch_20261031_09.py']:
        if name not in state['scripts']:state['scripts'].append(name)
    save(OUT/'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_temporal_samples=229,additional_partial_sequences=1,additional_negative_sequences=2,additional_accepted_images=5,training_started=False)))

if __name__=='__main__':main()
