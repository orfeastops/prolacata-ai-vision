"""Record inspected validation return sequences without inventing origin identity."""
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read, save, merge, evidence

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/tank_transfer_training_v1'
OUT=BASE/'dataset_v1'
RUN='sequence_review_20261031_41'

def main():
    state=read(OUT/'continuation_state.json')
    if RUN in state.get('completed_curation_runs',[]):
        print('Already recorded',RUN);return
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    windows={'dense':('afternoon_return1338_cam11',112),
             'empty':('afternoon_return1338_cam15',16),
             'scale':('afternoon_scale1335_cam15',8)}
    paths={k:OUT/'sequence_review/20261017'/w/'frames.json' for k,(w,_) in windows.items()}
    metas={k:read(p) for k,p in paths.items()}
    for k,m in metas.items():
        assert len(m['samples'])==windows[k][1]
        assert m['source']['date']=='20261017' and m['source']['split']=='validation'
    clocks={
        'dense':{0:'13:32:56',1:'13:33:00',2:'13:33:04',5:'13:33:16',6:'13:33:20',8:'13:33:28',
            9:'13:33:32',10:'13:33:36',11:'13:33:40',12:'13:33:44',15:'13:33:56',18:'13:34:08',
            29:'13:34:52',30:'13:34:56',31:'13:35:00',32:'13:35:04',33:'13:35:08',34:'13:35:12',
            37:'13:35:24',44:'13:35:52',47:'13:36:04',59:'13:36:52',60:'13:36:56',71:'13:37:40',
            75:'13:37:56',77:'13:38:04',78:'13:38:08',79:'13:38:12',80:'13:38:16',81:'13:38:20',
            82:'13:38:24',83:'13:38:28',84:'13:38:32',85:'13:38:36',86:'13:38:40',87:'13:38:44',
            90:'13:38:56',91:'13:39:00',92:'13:39:04',93:'13:39:08',94:'13:39:12',95:'13:39:16',
            96:'13:39:20',97:'13:39:24',98:'13:39:28',101:'13:39:40',102:'13:39:44',
            103:'13:39:48',104:'13:39:52',105:'13:39:56',106:'13:40:00',107:'13:40:04',
            108:'13:40:08',109:'13:40:12',110:'13:40:16',111:'13:40:20'},
        'empty':{0:'13:38:38',1:'13:38:52',2:'13:38:54',3:'13:38:56',4:'13:38:58',5:'13:39:00',
            6:'13:39:02',7:'13:39:04',8:'13:39:06',9:'13:39:08',10:'13:39:10',11:'13:39:12',
            12:'13:39:14',13:'13:39:16',14:'13:39:18',15:'13:39:20'},
        'scale':{0:'13:35:32',1:'13:35:53',2:'13:35:55',3:'13:35:57',4:'13:35:59',5:'13:36:01',
            6:'13:36:03',7:'13:36:05'},
    }
    notes={
        'dense':'All112 samples/19 sheets inspected. Fresh filling continues32:56-33:04; white sheet16-20. Jack departs33:36, body crosses40 and clears44. Separate empty replacement moves20-40 and is filled44 onward. Covered body first approaches scale35:00, adjusted04-20, dwells24-38:08, moves12-24 and platform clear28. Body reappears at doorway32 and is fully in11 at36; pushedleft40-44, repositioned38:56-39:08 and parkedleft. Scale-to-return trajectory has a brief out-of-view turn; same origin as33min fresh departure is NOT certified. Distinct empty beige body enters39:20-24, staysnear door then is pushedleft39:52-40:08. New station load filled33:44-37:56, covered38:04; taken39:48-40:04. Returned covered body remains parkedleft. Native0,10,37,97 inspected. No complete cycles inferred.',
        'empty':'All16 samples/three sheets inspected. Isolated initial38:38, next38:52. People traverse aisle52-56. Different empty beige body movesfromleft39:08-16, reaches door18-20; matches visible emptybody in11 at39:20-24. Native39:14 inspected. Earlier covered return38:32-36 has already happened; this is a distinct empty track. Foreground bins and stored tanks remain fixed.',
        'scale':'All8 samples/two sheets inspected. Initial35:32 then35:53,55,57,59,36:01,03,05. Operator movesnear scale console behind fixed bins. Platform load strongly occluded; this does not repair missing33min arrival or prove its identity. No weight read. No numeric clock offset derived from initial-frame discontinuity.',
    }
    for k,m in metas.items():
        merge(OUT/'screening_source_reviews.json',[dict(review_id='20261017/'+windows[k][0],reviewed_at=stamp,
            reviewer='assistant_visual_review',date='20261017',camera=m['source']['camera'],split='val',
            source_member=m['source']['member'],source_sha256=m['source_sha256'],frames_manifest=str(paths[k].relative_to(ROOT)),
            sampled_frames_visually_reviewed=len(m['samples']),reviewed_sheets=m['sheets'],
            review_scope='Every sampled presentation visually inspected in order; selected native frames and separate object overlays. Validation annotation only.',
            observation=notes[k],accepted_complete_cycle=False,
            clock_warning='Pixel clocks independently read. Filenames and PTS do not establish synchronization; initial jumps retained.',
            visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],
                relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],visible_camera_clock=t,
                clock_read_uncertainty_seconds=1,image=m['samples'][i]['image'],usable_for_clock_alignment=False)
                for i,t in clocks[k].items()])],'review_id')
    # Previously reviewed broad filling context is reused, not counted again.
    paths['broad']=OUT/'sequence_review/20261017/afternoon_1331_cam11/frames.json'
    metas['broad']=read(paths['broad'])
    def ev(k,a,b):return evidence(metas[k],a,b,paths[k])
    save(OUT/'review_history/sequence_labels_before_20261031_41.json',read(OUT/'reviewed_sequence_labels.json'))
    shared=dict(date='20261017',split='val',reviewer='assistant_visual_review',reviewed_at=stamp,
        dataset_release_accepted=False,cycle_id=None,camera_clock_offset_seconds=None)
    p1=dict(shared,sequence_id='20261017_beige_departure1333_partial',review_status='reviewed_partial_sequence',
        production_entry_count_target=None,camera_track_id={'11':'fresh_beige1333'},
        stages=[
            dict(stage='filling_observed',camera=11,visible_camera_clock_interval=['13:26:21','13:33:04'],
                initial_contents_unknown=True,observation='Fresh tray cheese placements; initial replacement moment outside this bounded filling certification.',
                evidence=[ev('broad',11,36),ev('dense',0,2)]),
            dict(stage='loaded_departure_11',camera=11,visible_camera_clock_interval=['13:33:36','13:33:44'],
                observation='Sheet placed16-20; jack moves loaded body36, doorway40, clear44.',evidence=[ev('dense',5,12)])],
        reviewed_followup_observations=[
            dict(stage='scale_visit',camera=11,visible_camera_clock_interval=['13:35:00','13:38:24'],
                stationary_interval=['13:35:24','13:38:08'],departure_interval=['13:38:12','13:38:28'],
                same_load_identity_confirmed=False,numeric_weight_kg=None,
                observation='Independent covered beige body at platform; direct33min room15 entry and staging unavailable.',
                evidence=[ev('dense',30,83),ev('scale',0,7)]),
            dict(stage='return_to_room11',camera=11,visible_camera_clock_interval=['13:38:32','13:38:36'],
                local_reposition_interval=['13:38:40','13:39:08'],direction='15_to_11',production_entry_increment=0,
                same_load_identity_confirmed=False,load_state='covered_unknown',
                observation='Covered body enters and parksleft. It resembles the just-departed platform body but turn leaves view at38:28; origin1333 is unverified. Cover does not establish contents. No new production entry in this reverse direction.',
                evidence=[ev('dense',81,95)])],
        missing_stages=['verified_entry_15','verified_origin_to_scale_identity','storage_placement'],
        limitations=['Partial fresh departure and explicitly unlinked later scale/return context. No full-cycle target.',
            'Room15 source coverage missing33:00-35:32 and36:06-38:38. Do not infer a fresh fill from the returning cover.'])
    p2=dict(shared,sequence_id='20261017_beige_departure1340_partial',review_status='reviewed_partial_sequence',
        production_entry_count_target=None,camera_track_id={'11':'fresh_beige1340'},
        stages=[
            dict(stage='filling_observed',camera=11,visible_camera_clock_interval=['13:33:44','13:37:56'],
                initially_empty_observed=True,observation='Empty replacement becomes filling tank; white tray blocks visibly added. No block-count label.',
                evidence=[ev('dense',6,12),ev('dense',12,75)]),
            dict(stage='loaded_departure_11',camera=11,visible_camera_clock_interval=['13:39:48','13:40:04'],
                doorway_interval=['13:40:00','13:40:04'],observation='This newly filled station body passes through door. Prior covered return remains parkedleft throughout, so these are distinct physical tracks.',
                evidence=[ev('dense',103,111)])],
        missing_stages=['verified_entry_15','scale_visit','storage_placement'],
        limitations=['Visible11 departure alone is not a completed storage cycle. Further15 follow-up not yet reviewed.'])
    n1=dict(shared,sequence_id='20261017_empty_beige_replacement1333',review_status='accepted_negative_sequence',
        production_entry_count_target=0,camera=11,negative_class='empty_tank_internal_reposition',tracked_tank_count=1,
        visible_camera_clock_interval=['13:33:20','13:33:40'],direction='room11_left_to_filling_station',
        observation='Visibly empty beige replacement pushed into station while different fresh-loaded body departs.',
        label_scope='Only this empty reposition, before filling begins. Not whole-scene zero.',evidence=[ev('dense',6,11)])
    n2=dict(shared,sequence_id='20261017_empty_beige_return1339',review_status='accepted_negative_sequence',
        production_entry_count_target=0,cameras=[15,11],negative_class='empty_crossing',tracked_tank_count=1,
        direction='15_to_11',visible_camera_clock_interval=['13:39:08','13:39:24'],
        camera15_door_interval=['13:39:18','13:39:20'],camera11_door_interval=['13:39:20','13:39:24'],
        clock_uncertainty_seconds=2,
        observation='Empty beige body pushed to doorway in15, matching body enters11 and movesleft after wait. Bottom visible. Distinct from covered38min return and station load.',
        correspondence_basis='Same empty beige body/operator and directed doorway passage visible in both cameras; uncertainty intervals retained, no scalar clock calibration.',
        label_scope='Only one empty return trip, not two counts for two views, and not a zero for concurrent fresh filling/departure.',
        evidence=[ev('empty',9,15),ev('dense',95,108)])
    merge(OUT/'reviewed_sequence_labels.json',[p1,p2,n1,n2],'sequence_id')
    qp=OUT/'sequence_followup_queue.json'
    save(OUT/'review_history/followup_queue_before_20261031_41.json',read(qp))
    merge(qp,[dict(candidate_id='20261017_beige1333_return1338',date='20261017',split='val',reviewed_at=stamp,
        status='resolved_as_partial_with_separate_return_context',resolved_sequence_id=p1['sequence_id'],cycle_id=None,
        production_entry_count_target=None,observation='Fresh departure33:36-44; later scale and coveredreturn32-36 retained as unlinked origin context. Separate emptyreturn39:18-24 certified.',
        next_action='Do not resample missing15 coverage33:00-35:32 or36:06-38:38. No completed cycle or same-load reentry claim without origin evidence.',
        evidence=[ev('dense',9,12),ev('dense',78,97),ev('empty',9,15)]),
        dict(candidate_id='20261017_beige1340',date='20261017',split='val',reviewed_at=stamp,
            status='needs_validation_followup_coverage_check',resolved_sequence_id=p2['sequence_id'],cycle_id=None,
            production_entry_count_target=None,observation='Fresh filled station body exits40:00-04; previous covered return remainsleft.',
            next_action='Check15 metadata around40min before extracting. Next11 source134102-134920 remains unreviewed. Preserve direct-entry gap if15 first usable follows40:04.',
            evidence=[ev('dense',103,111)])],'candidate_id')
    registry=read(OUT/'object_review_decisions.json')
    save(OUT/'review_history/object_decisions_before_20261031_41.json',registry)
    decisions={r['id']:r for r in registry['reviews']}
    drafts={r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
    for ident,note in [('264','Empty return body overlapped by worker at left.'),('265','Independent scale body, partly occluded by doorway and foreground item.')]:
        assert ident not in decisions
        r=drafts[ident];assert r['split']=='val' and len(r['boxes_xyxy'])==1
        decisions[ident]=dict(id=ident,image_sha256=r['sha256'],
            boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',
            load_state_reviewed=False,sequence_reviewed=False,
            instance_attributes=[dict(box_index=0,truncated=False,occluded=True,load_state='unknown_not_annotated')],
            evidence=[r['source_frame'],r['frames_manifest'],'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_34.jpg'],
            note=note+' Native context and separate rendered overlay inspected. Validation only.')
    registry['reviews']=list(decisions.values())
    registry.setdefault('corrections',[]).append('Batch41: two validation ROI boxes separately reviewed; earlier decisions preserved.')
    save(OUT/'object_review_decisions.json',registry)
    inv=read(BASE/'archive_inventory.json');inspected={m['source']['member']:m['source_sha256'] for m in metas.values()}
    for r in inv['records']:
        if r['member'] in inspected:r.update(pixel_inspected=True,sha256=inspected[r['member']])
    assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test')
    save(BASE/'archive_inventory.json',inv)
    reviews=read(OUT/'screening_source_reviews.json');total=sum(r['sampled_frames_visually_reviewed'] for r in reviews)
    state['last_completed'] += [
        f'Batch41 reviewed136 further validation sample presentations in3 windows;{total} total across{len({r["source_sha256"] for r in reviews})} sources/{len(reviews)} windows. Extractions complete;25/28Oct unseen.',
        '17Oct33min fresh departure and distinct40min fresh departure recorded as partials. Later35min scale/38min covered return retain unverified origin.5 complete cycles unchanged;37 partials.',
        'Two scoped negatives:33min empty replacement and one39min empty return matched across both cameras.86 negative sequences total. Covered return is not falsely called empty or new production.',
        'Two validation ROI images/boxes accepted:266 candidates,208 approved ROI images,273 boxes,58 exclusions,zero drafts. Dataset not released; no training or tuning.',
    ]
    state['priority_next']=[
        'Batch41 complete. Prioritise remaining training-day6/15Oct full-route candidates;17Oct annotations stay validation only.',
        '17Oct33min departure remainspartial;35min scale and38min covered return unlinked to origin. Empty39min return matched. Do not repeat dense32:56-40:20 or known15 gaps.',
        '17Oct40min fresh departure partial has dense filling33:44-37:56 and exit40:00-04. Next11 source134102-134920 uninspected; inspect15 coverage before new extraction. Returned covered load remainsparkedleft.',
    ]+[p for p in state['priority_next'] if not p.startswith('Batch40') and not p.startswith('17Oct33min')]
    state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    state['scripts'] += ['work/append_tank_roi_batch_20261031_41.py','work/record_tank_sequence_batch_20261031_41.py']
    save(OUT/'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_samples=136,total_presentations=total,
        additional_complete_cycles=0,additional_negative_sequences=2,additional_partial_sequences=2,training_started=False)))

if __name__=='__main__':main()
