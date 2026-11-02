"""Persist batch23 visual observations; uncertain trajectory joins stay partial."""
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read, save, merge, evidence

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'outputs/tank_transfer_training_v1'
OUT = BASE/'dataset_v1'
RUN = 'sequence_review_20261031_23'


def main():
    state = read(OUT/'continuation_state.json')
    if RUN in state.get('completed_curation_runs', []):
        print('Already recorded', RUN)
        return
    stamp = dt.datetime.now(dt.timezone.utc).isoformat()
    windows = {
        'graypark': ('gray_park_1036_cam15',23),
        'grayafter': ('gray_release_1036_cam15',14),
        'entry': ('beige_entry_1037_cam15',18),
        'stage': ('beige_scale_1038_cam15',8),
        'scale1': ('beige_scale_1039_cam15',12),
        'scale2': ('beige_scale_1040_cam15',14),
        'context': ('beige_scale_context_1037_cam11',50),
        'scale3': ('beige_scale_end_1042_cam15',17),
        'route': ('beige_route_1043_cam15',19),
        'park': ('beige_storage_1044_cam15',19),
        'end11': ('beige_scale_end_1041_cam11',41),
    }
    paths={k:OUT/'sequence_review/20261015'/w/'frames.json' for k,(w,n) in windows.items()}
    metas={k:read(p) for k,p in paths.items()}
    for k,m in metas.items():
        assert m['source']['date']=='20261015' and m['source']['split']=='train'
        assert len(m['samples'])==windows[k][1]
    # Selected clock anchors were read from rendered image clocks.
    clocks={
        'graypark':{0:'10:36:23',1:'10:36:30',9:'10:36:38',17:'10:36:46',22:'10:36:51'},
        'grayafter':{0:'10:36:35',1:'10:36:52',13:'10:37:04'},
        'entry':{0:'10:37:15',1:'10:37:19',5:'10:37:23',6:'10:37:24',9:'10:37:27',10:'10:37:28',11:'10:37:29',12:'10:37:30',13:'10:37:31',15:'10:37:33',16:'10:37:34',17:'10:37:35'},
        'stage':{0:'10:38:05',1:'10:38:15',2:'10:38:17',3:'10:38:19',4:'10:38:21',5:'10:38:23',6:'10:38:25',7:'10:38:27'},
        'scale1':{0:'10:39:39',1:'10:39:45',8:'10:39:59',9:'10:40:01',11:'10:40:05'},
        'scale2':{0:'10:40:09',1:'10:40:13',4:'10:40:19',6:'10:40:23',13:'10:40:37'},
        'context':{0:'10:37:26',1:'10:37:31',2:'10:37:36',3:'10:37:41',11:'10:38:21',12:'10:38:26',13:'10:38:31',14:'10:38:36',49:'10:41:31'},
        'scale3':{0:'10:41:58',1:'10:42:13',2:'10:42:15',3:'10:42:17',7:'10:42:25',9:'10:42:29',14:'10:42:39',15:'10:42:41',16:'10:42:43'},
        'route':{0:'10:43:38',1:'10:43:45',4:'10:43:48',5:'10:43:49',6:'10:43:50',8:'10:43:52',9:'10:43:53',15:'10:43:59',16:'10:44:00',18:'10:44:02'},
        'park':{0:'10:43:49',1:'10:44:09',2:'10:44:10',3:'10:44:13',4:'10:44:14',5:'10:44:17',6:'10:44:18',7:'10:44:20',8:'10:44:23',9:'10:44:24',10:'10:44:26',11:'10:44:29',12:'10:44:30',13:'10:44:32',14:'10:44:35',15:'10:44:36',16:'10:44:38',17:'10:44:41',18:'10:44:42'},
        'end11':{0:'10:41:34',1:'10:41:53',2:'10:41:59',3:'10:42:05',4:'10:42:11',5:'10:42:17',6:'10:42:23',7:'10:42:29',8:'10:42:35',9:'10:42:41',10:'10:42:47',11:'10:42:53',12:'10:42:59',13:'10:43:05',14:'10:43:11',15:'10:43:17',16:'10:43:23',17:'10:43:29',18:'10:43:35',19:'10:43:41',20:'10:43:47',21:'10:43:53',22:'10:43:59',23:'10:44:05',24:'10:44:11',25:'10:44:17',26:'10:44:23',27:'10:44:29',28:'10:44:35',29:'10:44:41',30:'10:44:47',31:'10:44:53',32:'10:44:59',33:'10:45:05',34:'10:45:11',35:'10:45:17',36:'10:45:23',37:'10:45:29',38:'10:45:35',39:'10:45:41',40:'10:45:47'},
    }
    notes={
        'graypark':'Initial36:23 early image. Gray already parked at front of rear storage row first usable36:30, stays through36:51. Prior route35:50 to36:30 leaves40-second sampled gap; parking/jack release not shown. People walk left to doorway36:38-46; no tank moves.',
        'grayafter':'Initial36:35 early image. People near doorway36:52-37:04, stored gray unchanged. One-second usable join from prior36:51, which does not bridge preceding40-second route-to-park gap. Directory name release is a search label, not an observed release event.',
        'entry':'Initial37:15 snapshot already has operator inside15 with jack, beige largely behind fixed blue bins. First usable series37:19-23 beige in staging, direct entry not seen. Separate visibly empty gray taken from waiting row37:24-28, approachesdoor29-30, crosses31-33, gone34-35. No new production entry assigned to empty return.',
        'stage':'Initial38:05 early image. Beige in doorway staging38:15-27, operator attends top/jack and people pass. Not yet a clear platform view. Next15 first usable39:45 already on platform leaves78 seconds; camera11 sampled context shows approach38:26-36.',
        'scale1':'Initial39:39 early image. Beige already on far-right platform39:45-40:05. Operator and visitors talk; people move, tank stays. No entry event.',
        'scale2':'Initial40:09 early image. Beige stationary on platform40:13-37. Visitor removes white apron/garment40:19-23 and walks left; not a tank event. Eight-second15 source join40:05-13.',
        'context':'Camera11 first37:26 already shows beige in15 staging. Empty gray crosses into11 at sampled37:31 and reaches station37:36, begins fresh cheese filling37:41, continues to41:31. Beige staging through38:21, moves38:26-31, settled platform38:36 through41:31. Fixed scrap receptacle separate. Do not derive a scalar clock offset from this coarse counterpart.',
        'scale3':'Initial41:58 early image. Beige still on far-right platform42:13-43. Top handled13-15; visitors leave17-29. Operator kneels near jack in left staging25-39 then stands41-43. No tank platform departure in this15 source; camera11 observes subsequent movement47-59.',
        'route':'Initial43:38 early image. Beige already off scale in left staging first usable43:45. Pulled45-48, turned49-52, moves toward left end of rear row53-44:02. Final parking/fork release not shown. Camera11 platformclear42:59 to first usable15route43:45 leaves46seconds, although11 retains beige edge in staging through43:35.',
        'park':'Initial43:49 early image. Beige already parked at left end of rear row44:09, operator withdrawing jack09-10, unloaded forks clear13. Last route44:02 to first parked09 leaves7-second final-placement gap. Beige remains stationary. A different visibly empty gray is selected from waiting row44:18-23, pulled24-32, crossesdoor35-38, out41-42. Negative is that gray only.',
        'end11':'Initial41:34 early image then41:53. Beige still scale through42:41, engaged/moving42:47, shifted to staging42:53, platform clear42:59. Staging beige edge remains through43:35, absent43:41. Gray at11 station receives cheese throughout to45:29. Separate empty gray from15 alreadyinside11 at44:41, parkedleft44:47; unloaded jack goes toward fillingstation44:53. Fresh gray receives cover45:35, pulled45:41, approachesdoor45:47; crossing not yet shown. Separate empty waiting gray pushed toward station at45:47. No new count assigned.',
    }
    for k,m in metas.items():
        merge(OUT/'screening_source_reviews.json',[dict(review_id='20261015/'+windows[k][0],reviewed_at=stamp,reviewer='assistant_visual_review',date='20261015',camera=m['source']['camera'],split='train',source_member=m['source']['member'],source_sha256=m['source_sha256'],frames_manifest=str(paths[k].relative_to(ROOT)),sampled_frames_visually_reviewed=len(m['samples']),reviewed_sheets=m['sheets'],review_scope='All chronological sheet samples inspected; selected native frames and separate object overlays also reviewed. Not exhaustive native-frame viewing.',observation=notes[k],accepted_complete_cycle=False,clock_warning='Initial early/stale frames excluded from alignment. PTS and filename are not camera synchronization.',visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],visible_camera_clock=t,clock_read_uncertainty_seconds=1,image=m['samples'][i]['image'],usable_for_clock_alignment=not(i==0 and k!='context')) for i,t in clocks[k].items()])],'review_id')
    def ev(k,a,b): return evidence(metas[k],a,b,paths[k])
    originpath=OUT/'sequence_review/20261015/next_origin_1021_cam11/frames.json'
    origin=read(originpath)
    labels=read(OUT/'reviewed_sequence_labels.json')
    hist=OUT/'review_history/sequence_labels_before_20261031_23.json'
    if not hist.exists(): save(hist,labels)
    gray=copy.deepcopy(next(r for r in labels if r['sequence_id']=='20261015_fresh_gray_departure_partial_1029'))
    gray.update(reviewed_at=stamp)
    gray['unlinked_followup'].update(first_usable_already_parked_camera15='10:36:30',route_to_already_parked_gap_seconds=40,storage_placement_observed=False,observation='Gray already parked at36:30; prior route ends35:50, leaving40 seconds without parking/release.97-second arrival gap remains. No complete cycle accepted.')
    gray['unlinked_followup']['evidence'] += [ev('graypark',1,22),ev('grayafter',1,13)]
    gray.setdefault('revision_notes',[]).append('Batch23: later parked gray view reviewed; route-to-park40-second gap explicit. Prior record archived.')
    shared=dict(date='20261015',split='train',reviewer='assistant_visual_review',reviewed_at=stamp,dataset_release_accepted=False)
    beige=dict(shared,sequence_id='20261015_fresh_beige_departure_partial_1037',review_status='reviewed_partial_sequence',cycle_id=None,production_entry_count_target=None,camera_track_id={'11':'fresh_beige_station_1029_1037','15':'unlinked_beige_staging_scale_storage_1037_1044'},cross_camera_identity='unresolved_direct_entry_and_storage_route',camera_clock_offset_seconds=None,
        stages=[dict(stage='filling_observed',camera=11,visible_camera_clock_interval=['10:29:31','10:36:51'],clock_uncertainty_seconds=10,content_evidence='Replacement beige receives cheese at filling station; fixed scrap tank separate.',evidence=[evidence(origin,48,92,originpath)]),dict(stage='loaded_departure_11',camera=11,visible_camera_clock_interval=['10:37:11','10:37:21'],clock_uncertainty_seconds=10,observation='Covered37:01, pulled37:11, gone37:21; exact threshold intersection not sampled.',evidence=[evidence(origin,93,95,originpath)])],
        missing_stages=['linked_entry_15','linked_scale_visit','linked_storage_placement'],
        unlinked_followup=dict(first_usable_beige_staging_camera15='10:37:19',direct_entry_observed=False,scale_approach_camera11_interval=['10:38:26','10:38:36'],scale_camera11_interval=['10:38:36','10:42:41'],platform_departure_camera11_interval=['10:42:47','10:42:59'],same_camera11_staging_edge_visible_through='10:43:35',later_beige_route_camera15_interval=['10:43:45','10:44:02'],platform_clear_to_first_route_sample_seconds=46,first_usable_already_parked_camera15='10:44:09',route_to_already_parked_gap_seconds=7,unloaded_fork_withdrawal_camera15_interval=['10:44:09','10:44:13'],numeric_weight_kg=None,evidence=[ev('entry',0,5),ev('stage',1,7),ev('context',0,49),ev('scale1',1,11),ev('scale2',1,13),ev('scale3',1,16),ev('end11',1,19),ev('route',1,18),ev('park',1,5)],observation='Staging-to-scale followed in sampled11 context; later15 route/park observations retained without claiming fresh origin linkage across obscured arrival and missing route intervals.'),
        limitations=['No exact entry clock, production count or complete-cycle target.','White cover alone is not cheese evidence.','Clocks remain separately observed, no scalar offset inferred.','Sampled views are not continuous native-frame tracking.'])
    neg1=dict(shared,sequence_id='20261015_empty_gray_return_1037',review_status='accepted_negative_sequence',cycle_id=None,production_entry_count_target=0,camera=15,camera_track_id='empty_gray_return_103724',negative_class='empty_crossing',tracked_tank_count=1,direction='15_to_11',visible_camera_clock_interval=['10:37:24','10:37:35'],clock_uncertainty_seconds=1,evidence=[ev('entry',6,17),ev('context',1,2)],observation='Visibly empty gray from waiting row passes15 doorway31-33,gone34-35.11 has empty gray replacement sampled31-36. Independent clock readings retained, not a calibrated offset.',label_scope='Only tracked empty return, not simultaneous beige staging/scale or subsequent gray filling.')
    neg2=dict(shared,sequence_id='20261015_empty_gray_return_1044',review_status='accepted_negative_sequence',cycle_id=None,production_entry_count_target=0,camera=15,camera_track_id='empty_gray_return_104418',negative_class='empty_crossing',tracked_tank_count=1,direction='15_to_11',visible_camera_clock_interval=['10:44:18','10:44:42'],clock_uncertainty_seconds=2,evidence=[ev('park',6,18),ev('end11',29,30)],observation='Different empty gray selected from waiting row18-23,pulled24-32,door35-38,gone41-42.11 shows empty gray already inside41 and parkedleft47. Not a second production entry.',label_scope='Only this empty return. Existing stored beige and filling gray are separate.')
    merge(OUT/'reviewed_sequence_labels.json',[gray,beige,neg1,neg2],'sequence_id')
    qpath=OUT/'sequence_followup_queue.json'
    queue=read(qpath)
    hist=OUT/'review_history/followup_queue_before_20261031_23.json'
    if not hist.exists(): save(hist,queue)
    changes=[]
    for old in queue:
        if old['candidate_id']=='20261015_next_beige_departure_1037':
            r=copy.deepcopy(old)
            r.update(reviewed_at=stamp,status='resolved_to_reviewed_partial',resolved_sequence_id=beige['sequence_id'],observation='Fresh beige37min departure and later staging/scale/route/storage reviewed. Direct15 entry not shown;46-second platform-clear-to-route and7-second final parking gaps retained.',next_action='Retain partial; no repeated unchanged windows without new coverage.')
            r['evidence'] += [ev('context',0,14),ev('route',1,18),ev('park',1,5)]
            changes.append(r)
        elif old['candidate_id']=='20261015_next_gray_after1020':
            r=copy.deepcopy(old)
            r.update(reviewed_at=stamp,next_action='Later gray already parked36:30 reviewed;40-second route-to-park gap and97-second arrival gap unresolved. Do not repeat unchanged sources.')
            r['evidence'] += [ev('graypark',1,22),ev('grayafter',1,13)]
            changes.append(r)
    changes.append(dict(candidate_id='20261015_next_gray_departure_1045',date='20261015',split='train',cycle_id=None,production_entry_count_target=None,status='partial_followup_pending',reviewed_at=stamp,observation='Gray replacement receives cheese37:41-45:29, covered45:35,pulled45:41,near door45:47. Exact crossing/15 counterpart not yet reviewed.',next_action='Continue11 same source104134-111111 after PTS240; inspect15 sources around1045-1053. Avoid re-extracting completed first240-second window.',evidence=[ev('context',3,49),ev('end11',1,40)]))
    merge(qpath,changes,'candidate_id')
    save(OUT/'gap_search_20261031_23.json',dict(reviewed_at=stamp,day='20261015',findings=['Gray29min partial:97-second arrival gap, later40-second route-to-first-parked gap.','Beige37min partial:direct entry not observed;46-second platform-clear to first15 route, with staging edge in11 until43:35;7-second final route/park join.','Two empty gray returns excluded from production counting.','Freshgray45min departure queued; no crossing/count invented.'],action='Retain partials; stage evidence is not an accepted full cycle.'))
    registry=read(OUT/'object_review_decisions.json')
    hist=OUT/'review_history/object_decisions_before_20261031_23.json'
    if not hist.exists(): save(hist,registry)
    decisions={r['id']:r for r in registry['reviews']}
    drafts={r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
    desc={'182':'Two distinct gray tanks: empty local replacement and covered departure. Both bodies separately boxed; worker slightly occludes empty rim.','183':'One visibly empty beige waiting tank, isolated body; load attribute not exported.','185':'Single moving gray return body; top truncated to exclude background stored row.','186':'Fixed beige scrap receptacle, partly occluded lower/right by conveyor; body class only.'}
    for ident,note in desc.items():
        assert ident not in decisions
        r=drafts[ident]
        decisions[ident]=dict(id=ident,image_sha256=r['sha256'],boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',load_state_reviewed=False,sequence_reviewed=False,instance_attributes=[dict(box_index=i,truncated=ident=='185',occluded=(ident=='186' or ident=='182' and i==0),load_state='unknown_not_annotated') for i in range(len(r['boxes_xyxy']))],evidence=[r['source_frame'],r['frames_manifest'],'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_21.jpg'],note=note)
    registry['reviews']=list(decisions.values())
    registry.setdefault('corrections',[]).append('Batch23:182/183/185/186 approved after separate overlay review;4ROIs/5boxes.184 excluded due blurred/truncated boundary. Earlier decisions unchanged.')
    save(OUT/'object_review_decisions.json',registry)
    inv=read(BASE/'archive_inventory.json')
    inspected={m['source']['member']:m['source_sha256'] for m in metas.values()}
    for r in inv['records']:
        if r['member'] in inspected: r.update(pixel_inspected=True,sha256=inspected[r['member']])
    assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test')
    save(BASE/'archive_inventory.json',inv)
    reviews=read(OUT/'screening_source_reviews.json')
    added=sum(len(m['samples']) for m in metas.values())
    total=sum(r['sampled_frames_visually_reviewed'] for r in reviews)
    state['last_completed'] += [
        f'Batch23 inspected {added} chronological presentations in11 windows on15Oct; {total} total across {len({r["source_sha256"] for r in reviews})} sources and {len(reviews)} windows. Extractions complete;25/28Oct untouched.',
        'Gray29min partial extended with later already parked view36:30;40-second route gap retained. Beige37min fresh departure added as partial, direct15 entry missing,46-second platform-clear-to-route and7-second final parking gaps. Totals5 complete,21 partials.',
        'Two distinct empty gray15-to11 return episodes37min/44min added as negatives. Total56 negatives. Next fresh gray45min departure queued separately.',
        'Five native ROI candidates182-186 added:four approved with5boxes,184 excluded for blurred boundary. Totals187 candidates,132 approved images,188boxes,55exclusions,zero drafts. Dataset unreleased.'
    ]
    state['priority_next']=[
        'Batch23 complete.5 complete cycles all13Oct. Need day-diverse full cycles and genuine same-load reentry/post-storage relocation negatives; do not mistake more partials/easy negatives for dataset readiness.',
        'Next15Oct freshgray45min:11 source104134-111111 afterPTS240,15 sources around1045-1053. Entry/storage may have export gaps; inspect before accepting cycle. All earlier37min andgray36min windows complete.',
        '13Oct next distinctload:11 sources093135-093311/093311-094655 and15 after093339 could support fullcycle, but prioritize day diversity.',
        '13Oct102139-102912 long15 source unreviewed;11 gap10:00:12-25:11 may miss origin.'
    ]+[p for p in state['priority_next'] if p.startswith('Known gaps') or p.startswith('25/28') or p.startswith('Old21Oct')]
    state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    state['scripts'] += [s for s in ['work/append_tank_roi_batch_20261031_23.py','work/record_tank_sequence_batch_20261031_23.py'] if s not in state['scripts']]
    save(OUT/'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_samples=added,total_presentations=total,additional_complete_cycles=0,additional_partial_sequences=1,additional_negative_sequences=2,training_started=False)))


if __name__=='__main__':main()
