"""Record source-backed6Oct partial routes and empty replacements; no training."""
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read,save,merge,evidence

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/tank_transfer_training_v1'
OUT=BASE/'dataset_v1'
RUN='sequence_review_20261031_42'

def main():
    state=read(OUT/'continuation_state.json')
    if RUN in state.get('completed_curation_runs',[]):
        print('Already recorded',RUN);return
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    windows={
        'join':('20261006','morning_join0839_cam11',25),
        'broad':('20261006','morning_after0839_cam11',75),
        'dep1':('20261006','morning_departure0841_cam11',30),
        'dep2':('20261006','morning_departure0853_cam11',35),
        'side':('20261015','scale_after1032_cam15',11),
    }
    paths={k:OUT/'sequence_review'/day/w/'frames.json' for k,(day,w,n) in windows.items()}
    metas={k:read(p) for k,p in paths.items()}
    for k,m in metas.items():
        assert len(m['samples'])==windows[k][2]
        assert m['source']['date']==windows[k][0] and m['source']['split']=='train'
    clocks={
        'join':{0:'08:39:00',1:'08:39:02',2:'08:39:04',3:'08:39:07',4:'08:39:09',
            5:'08:39:10',8:'08:39:16',11:'08:39:22',14:'08:39:28',17:'08:39:35',
            20:'08:39:41',23:'08:39:47',24:'08:39:49'},
        'broad':{0:'08:39:44',1:'08:40:17',2:'08:40:37',3:'08:40:57',4:'08:41:17',
            5:'08:41:37',6:'08:41:57',7:'08:42:17',8:'08:42:37',16:'08:45:17',
            17:'08:45:37',18:'08:45:57',23:'08:47:38',24:'08:47:57',27:'08:48:58',
            30:'08:49:58',40:'08:53:18',41:'08:53:38',42:'08:53:58',43:'08:54:18',
            45:'08:54:58',47:'08:55:38',48:'08:55:58',49:'08:56:18',50:'08:56:38',
            51:'08:56:58',52:'08:57:18',53:'08:57:38',54:'08:57:58',55:'08:58:18',
            56:'08:58:38',57:'08:58:58',58:'08:59:18',59:'08:59:38',60:'08:59:58',
            61:'09:00:18',62:'09:00:38',63:'09:00:58',64:'09:01:18',65:'09:01:38',
            66:'09:01:58',67:'09:02:18',68:'09:02:38',69:'09:02:58',70:'09:03:18',
            71:'09:03:38',72:'09:03:58',73:'09:04:18',74:'09:04:38'},
        'dep1':{0:'08:40:39',1:'08:40:41',2:'08:40:43',3:'08:40:45',4:'08:40:47',
            5:'08:40:49',6:'08:40:51',7:'08:40:53',8:'08:40:55',9:'08:40:57',10:'08:40:59',
            11:'08:41:01',12:'08:41:03',13:'08:41:05',14:'08:41:07',15:'08:41:09',
            16:'08:41:11',17:'08:41:13',18:'08:41:15',19:'08:41:17',20:'08:41:19',
            21:'08:41:21',22:'08:41:23',23:'08:41:25',24:'08:41:27',25:'08:41:29',
            26:'08:41:31',27:'08:41:33',28:'08:41:35',29:'08:41:37'},
        'dep2':{0:'08:53:08',1:'08:53:10',2:'08:53:12',3:'08:53:14',4:'08:53:16',5:'08:53:18',
            6:'08:53:20',7:'08:53:22',8:'08:53:24',9:'08:53:26',10:'08:53:28',11:'08:53:30',
            12:'08:53:32',13:'08:53:34',14:'08:53:36',15:'08:53:38',16:'08:53:40',17:'08:53:42',
            18:'08:53:44',19:'08:53:46',20:'08:53:48',21:'08:53:50',22:'08:53:52',23:'08:53:54',
            24:'08:53:56',25:'08:53:58',26:'08:54:00',27:'08:54:02',28:'08:54:04',29:'08:54:06',
            30:'08:54:08',31:'08:54:10',32:'08:54:12',33:'08:54:14',34:'08:54:16'},
        'side':{0:'10:32:00',1:'10:32:15',2:'10:32:17',3:'10:32:19',4:'10:32:21',5:'10:32:23',
            6:'10:32:25',7:'10:32:27',8:'10:32:29',9:'10:32:31',10:'10:32:33'},
    }
    notes={
        'join':'All25 samples/five sheets inspected. Pixel clock39:00-49, despite filename ending39:44. Previously filled blue-lined station tank waits while workers handle top/trays. Jack operator waits behind. Separate scrap container and waiting empty tanks remain distinct. No outgoing crossing in this short join.',
        'broad':'All75 samples/13 sheets inspected, not every native frame. Initial39:44 then40:17. Loaded station tank leaves40:57 and is gone41:17; dense review refines this. Replacement fills41min-53min, then leaves53:38 and is gone53:58. A covered platform body appears42:17, dwells through45:17, moves45:37 and is clear45:57; origin not linked. Another covered body is at scale54:58-57:38, moves57:58 and platform clears58:18; also unlinked to station origin. Empty jack returns47:38 then empty forks parked47:57; retained as context only. Third fresh beige station body fills54min-09:03:38, is gone03:58; empty replacement visible04:18-38. Third departure requires dense boundary review. No new complete cycle, storage identity or scale weight claimed.',
        'dep1':'All30 samples/five sheets inspected. Neat cheese layer39-43 then white cover45-51. Jack pulls53-55, acrossroom57-59, body crosses doorway41:01-05 and absent07. Different empty blue-lined gray body moves from waiting row41:05-15; remains empty17-21, first placements visible23 onward. Native40:59 and41:11 inspected, plus separate ROI overlays. Concurrent scrap tank is not replacement.',
        'dep2':'All35 samples/six sheets inspected. Fresh block placements53:08-22; white cover24-34. Jack starts moving36-38, crossesroom40-44, doorway46-50, gone52. Different visibly empty beige body taken from waiting row40-54; first cheese visible58. Native53:48 inspected. Prior station load and empty replacement have separate tracks. No room15 arrival or complete storage cycle inferred.',
        'side':'All11 samples/two sheets and native32:19 inspected. Initial32:00 then32:15-33. One person walks from doorway leftwards15-21 without a tank; second person follows29-33. Existing foreground and stored tanks remain fixed. Covered platform body behind fixed blue bins stays heavily occluded; no link to fresh29min departure established. Prior inspected source ended32:07, next useful image32:15: retain eight-second join gap.',
    }
    for k,m in metas.items():
        day,window,n=windows[k]
        merge(OUT/'screening_source_reviews.json',[dict(review_id=day+'/'+window,reviewed_at=stamp,
            reviewer='assistant_visual_review',date=day,camera=m['source']['camera'],split='train',
            source_member=m['source']['member'],source_sha256=m['source_sha256'],frames_manifest=str(paths[k].relative_to(ROOT)),
            sampled_frames_visually_reviewed=n,reviewed_sheets=m['sheets'],
            review_scope='All chronological sample presentations visually inspected; selected native context and separate object overlays. Not exhaustive native-frame inspection.',
            observation=notes[k],accepted_complete_cycle=False,
            clock_warning='Clock anchors read from pixels, never inferred from filename or PTS. Initial jumps preserved; no exact cross-camera offset asserted.',
            visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],
                relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],visible_camera_clock=t,
                clock_read_uncertainty_seconds=1,image=m['samples'][i]['image'],usable_for_clock_alignment=False)
                for i,t in clocks[k].items()])],'review_id')
    # Reuse previously inspected filling evidence without double-counting review totals.
    for k,w in [('oldbroad','morning_route_0811_cam11'),('olddep','morning_departure_0826_cam11')]:
        paths[k]=OUT/'sequence_review/20261006'/w/'frames.json';metas[k]=read(paths[k])
        assert any(r['frames_manifest']==str(paths[k].relative_to(ROOT)) for r in read(OUT/'screening_source_reviews.json'))
    def ev(k,a,b):return evidence(metas[k],a,b,paths[k])
    save(OUT/'review_history/sequence_labels_before_20261031_42.json',read(OUT/'reviewed_sequence_labels.json'))
    shared=dict(date='20261006',split='train',reviewer='assistant_visual_review',reviewed_at=stamp,
        dataset_release_accepted=False,cycle_id=None,camera_clock_offset_seconds=None)
    p1=dict(shared,sequence_id='20261006_blue_departure0841_partial',review_status='reviewed_partial_sequence',
        production_entry_count_target=None,camera_track_id={'11':'fresh_blue0841'},
        stages=[
            dict(stage='filling_observed',camera=11,visible_camera_clock_interval=['08:26:41','08:38:42'],
                initially_empty_observed=True,initial_empty_evidence_sequence_id='20261006_empty_blue_station_replacement0826',
                observation='Previously reviewed replacement receives cheese; same body remains at station through39min join and40min cover.',
                evidence=[ev('olddep',30,59),ev('oldbroad',46,81),ev('join',0,24),ev('dep1',0,6)]),
            dict(stage='loaded_departure_11',camera=11,visible_camera_clock_interval=['08:40:53','08:41:07'],
                doorway_interval=['08:41:01','08:41:07'],observation='Fresh filled blue-lined gray body is covered, pulled across room and through doorway.',
                evidence=[ev('dep1',3,14)])],
        reviewed_followup_observations=[dict(stage='scale_visit',camera=11,visible_camera_clock_interval=['08:42:17','08:45:37'],
            departure_interval=['08:45:17','08:45:57'],same_load_identity_confirmed=False,numeric_weight_kg=None,
            observation='Independent covered platform body, not certified as this fresh departure. No room15 entry trajectory.',evidence=[ev('broad',7,18)])],
        missing_stages=['verified_entry_15','verified_origin_to_scale_identity','storage_placement'],
        limitations=['Available room15 file metadata ends08:36:10 then resumes08:47:09. Filenames are coverage clues, not clock calibration. Direct41min entry cannot be supplied from these sources.',
            'Partial fresh filling/departure only; no production-cycle count target.'])
    p2=dict(shared,sequence_id='20261006_blue_departure0853_partial',review_status='reviewed_partial_sequence',
        production_entry_count_target=None,camera_track_id={'11':'fresh_blue0853'},
        stages=[
            dict(stage='filling_observed',camera=11,visible_camera_clock_interval=['08:41:23','08:53:22'],
                initially_empty_observed=True,initial_empty_evidence_sequence_id='20261006_empty_blue_replacement0841',
                observation='Distinct empty replacement gets block placements; no block count target.',
                evidence=[ev('dep1',15,29),ev('broad',6,40),ev('dep2',0,7)]),
            dict(stage='loaded_departure_11',camera=11,visible_camera_clock_interval=['08:53:36','08:53:52'],
                doorway_interval=['08:53:46','08:53:52'],observation='Same newly filled gray body receives cover and leaves. Empty beige replacement is separate.',
                evidence=[ev('dep2',8,22)])],
        reviewed_followup_observations=[dict(stage='scale_visit',camera=11,visible_camera_clock_interval=['08:54:58','08:57:58'],
            departure_interval=['08:57:38','08:58:18'],same_load_identity_confirmed=False,numeric_weight_kg=None,
            observation='Independent later covered body dwells on platform. Arrival/staging link to53min station origin not reviewed or assumed.',
            evidence=[ev('broad',45,55)])],
        missing_stages=['verified_entry_15','verified_origin_to_scale_identity','storage_placement'],
        limitations=['Room15 metadata ends08:47:29 then resumes08:55:39, leaving53min direct entry unavailable. Later55/59min sources may add unlinked follow-up only unless trajectory evidence establishes identity.',
            'Sampling is chronological visual curation, not a validated counting model.'])
    negatives=[]
    for ident,color,k,a,b,times in [
        ('20261006_empty_blue_replacement0841','blue-lined gray','dep1',13,20,['08:41:05','08:41:19']),
        ('20261006_empty_beige_replacement0853','blue-lined beige','dep2',16,23,['08:53:40','08:53:54'])]:
        negatives.append(dict(shared,sequence_id=ident,review_status='accepted_negative_sequence',camera=11,
            production_entry_count_target=0,negative_class='empty_tank_internal_reposition',tracked_tank_count=1,
            direction='room11_waiting_area_to_filling_station',visible_camera_clock_interval=times,
            observation='Visibly empty '+color+' replacement pushed from waiting row to station; bottom visible.',
            label_scope='Only the empty replacement movement before filling begins. Concurrent filled departure and scrap container excluded.',
            evidence=[ev(k,a,b)]))
    negatives.append(dict(shared,sequence_id='20261015_person_without_tank1032',date='20261015',
        review_status='accepted_negative_sequence',camera=15,production_entry_count_target=0,
        negative_class='people_without_tank',tracked_people_count=1,visible_camera_clock_interval=['10:32:15','10:32:21'],
        observation='One person walks away from doorway towards left aisle without a tank or jack.',
        label_scope='Only this pedestrian trajectory. Not a room-wide absence label; stored tanks and platform body exist.',
        evidence=[ev('side',1,4)]))
    merge(OUT/'reviewed_sequence_labels.json',[p1,p2,*negatives],'sequence_id')
    qp=OUT/'sequence_followup_queue.json'
    save(OUT/'review_history/followup_queue_before_20261031_42.json',read(qp))
    merge(qp,[
        dict(candidate_id='20261006_replacement_after0826',date='20261006',split='train',reviewed_at=stamp,
            status='resolved_as_partial_departure0841',resolved_sequence_id=p1['sequence_id'],cycle_id=None,
            production_entry_count_target=None,observation='26min replacement stays at station through39min join, then exits41:01-07.',
            next_action='Do not repeat known15 coverage gap36:10-47:09 or infer origin from covered scale body.',evidence=[ev('join',0,24),ev('dep1',0,14)]),
        dict(candidate_id='20261006_blue0853_route_gap',date='20261006',split='train',reviewed_at=stamp,
            status='resolved_as_partial_entry_gap',resolved_sequence_id=p2['sequence_id'],cycle_id=None,production_entry_count_target=None,
            observation='Fresh53min loaded departure46-52; later platform body54:58-58:18 unlinked.',
            next_action='Direct53min entry absent from current15 coverage.55:39/59:39 and09:00 clips uninspected; do not infer continuity across missing interval.',
            evidence=[ev('dep2',18,22),ev('broad',45,55)]),
        dict(candidate_id='20261006_beige0903',date='20261006',split='train',reviewed_at=stamp,
            status='needs_dense_departure_and_peer_coverage_review',cycle_id=None,production_entry_count_target=None,
            observation='Beige replacement empty53:54, receives cheese53:58 onward through09:03:38. Station vacated03:58, new empty replacement04:18-38. Broad sampling does not certify exact doorway crossing.',
            next_action='Inspect bounded11 PTS1400-1465 and15 sources090331-090353/090342-090412 plus adjacent coverage. Check existing extraction first. Do not add a complete-cycle target from broad disappearances.',
            evidence=[ev('dep2',23,34),ev('broad',43,74)])], 'candidate_id')
    registry=read(OUT/'object_review_decisions.json')
    save(OUT/'review_history/object_decisions_before_20261031_42.json',registry)
    decisions={r['id']:r for r in registry['reviews']}
    drafts={r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
    for ident,occluded,sheet,note in [
        ('266',False,'34','Covered outgoing body; fresh origin established only in separate sequence label.'),
        ('267',True,'34','Empty gray replacement, foreground table partly overlaps lower-left body.'),
        ('268',True,'35','Empty beige replacement, hands slightly overlap back rim.')]:
        assert ident not in decisions
        r=drafts[ident];assert r['split']=='train' and len(r['boxes_xyxy'])==1
        decisions[ident]=dict(id=ident,image_sha256=r['sha256'],
            boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',
            load_state_reviewed=False,sequence_reviewed=False,
            instance_attributes=[dict(box_index=0,truncated=False,occluded=occluded,load_state='unknown_not_annotated')],
            evidence=[r['source_frame'],r['frames_manifest'],f'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_{sheet}.jpg'],
            note=note+' Native context, candidate crop and separate rendered overlay inspected. ROI detection only.')
    registry['reviews']=list(decisions.values())
    registry.setdefault('corrections',[]).append('Batch42: three training ROI boxes separately reviewed; previous decisions preserved.')
    save(OUT/'object_review_decisions.json',registry)
    inv=read(BASE/'archive_inventory.json');inspected={m['source']['member']:m['source_sha256'] for m in metas.values()}
    for r in inv['records']:
        if r['member'] in inspected:r.update(pixel_inspected=True,sha256=inspected[r['member']])
    assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test')
    save(BASE/'archive_inventory.json',inv)
    reviews=read(OUT/'screening_source_reviews.json');total=sum(r['sampled_frames_visually_reviewed'] for r in reviews)
    state['last_completed'] += [
        f'Batch42 inspected176 further training sample presentations in5 windows on6/15Oct;{total} total across{len({r["source_sha256"] for r in reviews})} sources/{len(reviews)} windows. Extractions completed;25/28Oct unseen.',
        '6Oct fresh41min and53min loaded departures recorded as partials with independently bounded door crossings. Later scale observations unlinked across15 coverage gaps. Complete cycles5 unchanged;partials39.',
        'Two empty replacement movements and one15Oct pedestrian-only trajectory accepted as scoped negatives.89 negatives total. Third6Oct09:03 departure queued for dense/paired review.',
        'Three native ROI images/boxes accepted after separate overlays:269 candidates,211 approved images,276 boxes,58 excluded,zero drafts. No training or dataset release.',
    ]
    state['priority_next']=[
        'Batch42 complete. Prioritise6Oct09:03 candidate: fresh beige filling53:58-09:03:38, broad departure before03:58. Inspect11 PTS1400-1465 in083944-090435 and15 paired090331-090353/090342-090412; check extraction status first.',
        '6Oct41min and53min departures are partials. Direct15 coverage gaps36:10-47:09 and47:29-55:39 prevent matching entry. Do not re-extract these known gaps or infer origin from platform cover.',
        '15Oct additional10:32 window reviewed; platform body remains unlinked to29min origin and eight-second32:07-15 join gap remains. Pedestrian15-21 is a scoped negative.',
    ]+[p for p in state['priority_next'] if not p.startswith('Batch41') and not p.startswith('6Oct replacement after08:26')]
    state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    state['scripts'] += ['work/append_tank_roi_batch_20261031_42.py','work/record_tank_sequence_batch_20261031_42.py']
    save(OUT/'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_samples=176,total_presentations=total,
        additional_complete_cycles=0,additional_negative_sequences=3,additional_partial_sequences=2,training_started=False)))

if __name__=='__main__':main()
