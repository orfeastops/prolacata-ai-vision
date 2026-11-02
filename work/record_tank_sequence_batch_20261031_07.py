"""Record10Oct visual empty-return review and separately reviewed ROI boxes.

No inference, training, original modification or test-day inspection occurs.
Clock values below were read from pixels, not generated from filename/PTS.
"""
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read,save,merge,evidence

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/tank_transfer_training_v1'
OUT=BASE/'dataset_v1'
RUN='sequence_review_20261031_07'

def main():
    state=read(OUT/'continuation_state.json')
    if RUN in state.get('completed_curation_runs',[]):
        print('Already recorded:',RUN);return
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    windows={'return15':('screening_1021_cam15',51),'return11':('screening_1022_cam11',55),
             'later15':('candidate_1050_cam15',14)}
    paths={k:OUT/'sequence_review/20261010'/name/'frames.json' for k,(name,_) in windows.items()}
    metas={k:read(p) for k,p in paths.items()}
    for k,m in metas.items():
        assert len(m['samples'])==windows[k][1]
        assert m['source']['date']=='20261010' and m['source']['split']=='train'
        assert all((ROOT/s['image']).is_file() for s in m['samples'])
    clocks={
        'return15':{0:'10:21:48',1:'10:22:02',6:'10:22:22',7:'10:22:27',8:'10:22:30',9:'10:22:34',10:'10:22:38',13:'10:22:50',14:'10:22:55',17:'10:23:06',18:'10:23:10',20:'10:23:18',21:'10:23:22',25:'10:23:38',27:'10:23:46',28:'10:23:50',30:'10:23:58',34:'10:24:14',35:'10:24:18',37:'10:24:26',38:'10:24:30',42:'10:24:46',43:'10:24:50',47:'10:25:06',48:'10:25:10',49:'10:25:14',50:'10:25:19'},
        'return11':{0:'10:22:08',1:'10:22:23',3:'10:22:31',4:'10:22:35',5:'10:22:39',8:'10:22:51',9:'10:22:55',11:'10:23:03',12:'10:23:07',14:'10:23:15',15:'10:23:19',16:'10:23:23',18:'10:23:31',22:'10:23:47',23:'10:23:51',26:'10:24:03',29:'10:24:15',30:'10:24:19',32:'10:24:27',36:'10:24:43',38:'10:24:51',39:'10:24:55',41:'10:25:03',42:'10:25:07',43:'10:25:11',44:'10:25:15',46:'10:25:23',49:'10:25:35',50:'10:25:39',51:'10:25:43',54:'10:25:55'},
        'later15':{0:'10:50:37',1:'10:50:54',2:'10:50:57',3:'10:51:00',4:'10:51:03',5:'10:51:06',6:'10:51:09',7:'10:51:12',8:'10:51:15',9:'10:51:18',10:'10:51:21',11:'10:51:24',12:'10:51:27',13:'10:51:30'}
    }
    notes={
        'return15':'Bulk return of visibly empty tanks from the left room15 row through the shared doorway toward room11. Seven successive trips carry2,2,2,1,2,2,2 tanks. Gray and beige bodies are kept separate even when touching. Empty interiors/liners visible; corresponding room11 views show arrival and placement along the left row. Filled/covered storage rows and fixed blue containers remain background context, not new production. First stale image10:21:48 then10:22:02; timestamps read from pixels, not filename duration. No fresh loaded11-to15 cycle assigned.',
        'return11':'Confirms seven return trips from15 into11, with13 visibly empty gray/beige tanks sorted into the existing left row by10:25:55. The initially present row is not part of that return count. Several trips push two tanks together; the last pair waits near the door before each is moved to the row. A gray tank already holding cheese stays at the filling station and a separate crumb tank stays on the right. Those stationary contents are not evidence of a newly completed fill or entry. Source begins with stale10:22:08 then10:22:23. No scalar clock alignment inferred.',
        'later15':'Covered tanks are already parked at start; their appearance here does not establish arrival or contents. Clearly empty yellow powered pallet-jack forks visible10:51:00 and again10:51:09-18, then jack turns toward doorway without a tank. Brief off-screen interval10:51:03-06 is retained. Operator handles a manual jack beside the doorway; partly visible tank/cover context behind fixed blue bins remains unresolved. No newly loaded entry, scale completion or storage event assigned in this window.'
    }
    reviews=[]
    for k,m in metas.items():
        reviews.append(dict(review_id='20261010/'+windows[k][0],reviewed_at=stamp,reviewer='assistant_visual_review',
            source_member=m['source']['member'],source_sha256=m['source_sha256'],date='20261010',camera=m['source']['camera'],split='train',
            frames_manifest=str(paths[k].relative_to(ROOT)),sampled_frames_visually_reviewed=len(m['samples']),reviewed_sheets=m['sheets'],
            review_scope='All chronological contact-sheet samples visually inspected. Native source context checked for selected object ROIs. Not exhaustive native-frame viewing.',
            visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],
                relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],visible_camera_clock=t,clock_read_uncertainty_seconds=1,
                image=m['samples'][i]['image'],usable_for_clock_alignment=i!=0) for i,t in clocks[k].items()],
            observation=notes[k],accepted_complete_cycle=False,
            clock_warning='Initial stale frames retained and not used for clock alignment. Camera clock intervals and original PTS both retained; no filename-derived or scalar inter-camera synchronization.'))
    merge(OUT/'screening_source_reviews.json',reviews,'review_id')
    def ev(k,a,b):return evidence(metas[k],a,b,paths[k])
    # Seven successive physical return trips form one reviewed negative episode,
    # not seven independent training sequences. Door times are bounded samples.
    trip_specs=[
        (2,['gray','gray'],[6,9],[3,8],['10:22:30','10:22:34'],['10:22:31','10:22:35']),
        (2,['gray','beige'],[7,14],[8,14],['10:22:50','10:22:55'],['10:22:55','10:23:03']),
        (2,['beige','beige'],[17,21],[14,18],['10:23:18','10:23:22'],['10:23:19','10:23:23']),
        (1,['beige'],[25,28],[21,26],['10:23:46','10:23:50'],['10:23:47','10:23:51']),
        (2,['beige','beige'],[30,35],[28,32],['10:24:14','10:24:18'],['10:24:15','10:24:19']),
        (2,['beige','gray'],[36,43],[35,44],['10:24:38','10:24:50'],['10:24:43','10:24:51']),
        (2,['beige','gray'],[47,50],[44,54],['10:25:14','10:25:19'],['10:25:15','10:25:23']),
    ]
    trips=[]
    for i,(count,colors,a,b,t15,t11) in enumerate(trip_specs,1):
        trips.append(dict(trip_id=f'empty_return_10Oct_{i:02d}',tracked_tank_count=count,visible_tank_colors=colors,
            direction='15_to_11',production_entry_count_target=0,camera15_door_interval=t15,camera11_door_interval=t11,
            evidence=[ev('return15',*a),ev('return11',*b)],
            temporal_precision='Sample-bounded crossing interval; partial doorway occlusion and up-to4-second sample spacing. No exact simultaneous camera-clock calibration.'))
    common=dict(date='20261010',split='train',reviewer='assistant_visual_review',reviewed_at=stamp,
        review_status='accepted_negative_sequence',cycle_id=None,production_entry_count_target=0,dataset_release_accepted=False)
    returns=dict(common,sequence_id='20261010_bulk_empty_returns_1022',camera=[11,15],
        camera_track_id={'15':'bulk_empty_tanks_to_door_1022','11':'same_return_trips_sorted_left_row_1022'},
        negative_class='empty_crossing',tracked_tank_count=13,tracked_object_count=13,physical_return_trip_count=7,
        visible_camera_clock_interval=['10:22:22','10:25:55'],clock_uncertainty_seconds=4,
        evidence=[ev('return15',1,50),ev('return11',1,54)],return_trips=trips,
        observation='Seven successive15-to11 empty-return trips:2+2+2+1+2+2+2=13 tanks. Corresponding doorway views and subsequent empty-row placement establish return direction. Final pair waits inside11 before both move to the row. One accepted negative episode, zero new production entries.',
        label_scope='Only the thirteen empty-return tracks. Do not apply a whole-frame zero/empty label to the stationary cheese-filled tank, crumb tank or existing stored tanks.',
        content_evidence='Open interiors and exposed empty bottoms/liners are visible on both sides. Minor liner/refuse does not constitute a new cheese load.',
        cross_camera_identity='Visual correspondence from direction, ordered trip composition, adjacent-door appearance and uninterrupted room11 placement; not color alone.',
        camera_clock_offset_seconds=None,
        limitations=['Chronological sampled-image visual annotation, not model output or independently certified ground truth.',
            'Exact threshold timestamps are unresolved; intervals and source discontinuities retained.',
            'The thirteen tanks are an episode inventory, not thirteen independent complete-cycle labels. No cheese production inferred.'])
    jack=dict(common,sequence_id='20261010_empty_powered_jack_105109',camera=15,
        camera_track_id='cam15_empty_powered_jack_105109',negative_class='pallet_jack_without_tank',tracked_tank_count=0,
        visible_camera_clock_interval=['10:51:09','10:51:30'],clock_uncertainty_seconds=3,evidence=[ev('later15',6,13)],
        observation='Yellow powered jack moves into aisle, turns with visibly empty forks and returns toward doorway. No tank carried during this observed track.',
        label_scope='This observed empty-jack track only. Other stored tanks and the partly occluded door-side activity are not negative production labels.',
        earlier_context='An empty jack is also visible10:51:00 then exits the left edge10:51:03-06. This unobserved interval is not labeled as a continuous identity track or a separate negative episode.')
    merge(OUT/'reviewed_sequence_labels.json',[returns,jack],'sequence_id')
    follow=dict(candidate_id='20261010_door_scale_context_1051',date='20261010',split='train',
        status='requires_origin_and_door_review',reviewed_at=stamp,production_entry_count_target=None,cycle_id=None,
        evidence=[ev('later15',0,13)],
        observation='Manual-jack handling and partly obscured tank/cover beside shared door. Existing white-top storage tanks are not new arrivals. Origin, entry and any scale-to-storage trajectory remain unverified; no cycle label assigned.',
        next_source_camera11='10.10/Camera_11_DVR_DVR_20261030170903/Camera_11_DVR_20261010103818_20261010111042_11305426.mp4',
        next_source_camera15='10.10/Camera_15_DVR_DVR_20261030170903/Camera_15_DVR_20261010105138_20261010105201_11345644.mp4')
    merge(OUT/'sequence_followup_queue.json',[follow],'candidate_id')
    registry=read(OUT/'object_review_decisions.json'); decisions={r['id']:r for r in registry['reviews']}
    drafts={r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
    notes_roi={
        '094':'Two separate empty gray bodies returning together. Front one occludes lower rear body; all visible instances labeled.',
        '095':'Beige and gray empty return bodies at door, plus two distinct left-border stationary tank fragments. Doorpost occlusion retained.',
        '096':'Two adjacent empty beige bodies from room15 return. Crop truncates both upper rims; source context checked to distinguish two tanks. No joined-pair box.',
        '097':'Stationary gray tank contains cheese blocks. Lower body is cropped and conveyor occludes its front. No new filling or transfer event inferred from this image.',
        '098':'Separate stationary crumb tank. Conveyor occludes lower right. Not a fresh whole-cheese production load.',
        '099':'Three fixed blue containers and a small top-left gray background tank fragment. Metal fittings, jugs and white covers are not additional tanks.'}
    occluded={'094':[0],'095':[1,2,3],'096':[], '097':[0],'098':[0],'099':[2,3]}
    for ident,note in notes_roi.items():
        assert ident not in decisions
        r=drafts[ident]; overlay=BASE/'detector_v1/sheets'/('labels_11.jpg' if ident=='099' else 'labels_10.jpg')
        decisions[ident]=dict(id=ident,image_sha256=r['sha256'],boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',load_state_reviewed=False,sequence_reviewed=False,
            instance_attributes=[dict(box_index=j,truncated=(b[0]==0 or b[1]==0 or b[2]==r['width'] or b[3]==r['height']),
                occluded=j in occluded[ident],load_state='unknown_not_annotated') for j,b in enumerate(r['boxes_xyxy'])],
            evidence=[r['source_frame'],r['frames_manifest'],str(overlay.relative_to(ROOT))],note=note)
    registry['reviews']=list(decisions.values());registry.setdefault('corrections',[]).append('Batch07 adds094-099, six native10Oct ROIs with14 boxes after separate overlay review. Existing annotations unchanged. Load attributes remain unreleased.')
    save(OUT/'object_review_decisions.json',registry)
    inventory=read(BASE/'archive_inventory.json');inspected={m['source']['member']:m['source_sha256'] for m in metas.values()}
    for r in inventory['records']:
        if r['member'] in inspected:r.update(pixel_inspected=True,sha256=inspected[r['member']])
    assert not any(r['pixel_inspected'] for r in inventory['records'] if r['split']=='test')
    save(BASE/'archive_inventory.json',inventory)
    total=sum(r['sampled_frames_visually_reviewed'] for r in read(OUT/'screening_source_reviews.json'))
    state['last_completed'] += [
        f'Batch07 reviewed120 chronological samples in3 new10Oct source windows; {total} sample presentations total. Extractions completed; no test pixels inspected.',
        'Paired10Oct cameras confirm one bulk empty-return episode:7 trips,13 physical tanks, direction15-to11, zero production entries. Consecutive trips and initial inventory remain distinct; no whole-frame negative applied.',
        'One additional empty powered-jack track accepted as negative. Totals2 complete cycles,11 negative episodes,3 partials.10Oct door/scale candidate queued without inventing origin or entry.',
        'Six native10Oct ROIs094-099 and14 boxes passed separate overlay review. Totals100 candidates,61 accepted images,105 accepted boxes;6 drafts and33 excluded. No training export released.'
    ]
    state['priority_next']=[
        'Batch07 completed10Oct screening_1021_cam15, screening_1022_cam11 and candidate_1050_cam15. Do not repeat these120 samples. No extraction is active.',
        'Resolve queued10Oct door/scale context around10:51 with camera11 long source10:38:18-11:10:42 and adjacent camera15 exports. Inspect actual clocks and fresh filling before accepting a new cycle. Sparse export gaps may require retaining a partial.',
        'Need complete cycles across additional training days and17Oct validation, and already-stored relocation/same-load-reentry negatives.25/28Oct stay locked without pixels.',
        '6Oct entry09:35:55-09:36:42 and15Oct scale-to-storage11:15:46-11:16:23 gaps remain unresolved. Do not repeat failed searches; preserve existing partials.',
        'Six object drafts002/003/006/007/010/011 remain. Expand representative views with native context and separate overlays. No training, uploads or original changes.'
    ]
    state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    for name in ['work/append_tank_roi_batch_20261031_07.py','work/record_tank_sequence_batch_20261031_07.py']:
        if name not in state['scripts']:state['scripts'].append(name)
    save(OUT/'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_temporal_samples=120,additional_negatives=2,additional_accepted_images=6,additional_boxes=14,training_started=False)))

if __name__=='__main__':main()
