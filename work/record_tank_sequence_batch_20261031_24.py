"""Batch24: reviewed15Oct departure, unlinked storage and empty return."""
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read, save, merge, evidence

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/tank_transfer_training_v1'
OUT=BASE/'dataset_v1'
RUN='sequence_review_20261031_24'


def main():
    state=read(OUT/'continuation_state.json')
    if RUN in state.get('completed_curation_runs',[]):
        print('Already recorded',RUN)
        return
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    windows={'origin':('gray_departure_1045_cam11',66),'scale1':('gray_scale_1047a_cam15',15),'scale2':('gray_scale_1047b_cam15',11),'stage':('gray_route_1052_cam15',26),'storage':('gray_storage_1053_cam15',30)}
    paths={k:OUT/'sequence_review/20261015'/w/'frames.json' for k,(w,n) in windows.items()}
    metas={k:read(p) for k,p in paths.items()}
    for k,m in metas.items():
        assert m['source']['date']=='20261015' and m['source']['split']=='train'
        assert len(m['samples'])==windows[k][1]
    clocks={
        'origin':{0:'10:45:49',1:'10:45:57',2:'10:46:05',3:'10:46:13',6:'10:46:37',7:'10:46:45',8:'10:46:53',9:'10:47:01',12:'10:47:25',16:'10:47:57',17:'10:48:05',24:'10:49:01',32:'10:50:05',36:'10:50:37',38:'10:50:53',39:'10:51:01',40:'10:51:09',41:'10:51:17',42:'10:51:25',43:'10:51:33',44:'10:51:41',45:'10:51:49',46:'10:51:57',47:'10:52:05',48:'10:52:13',49:'10:52:21',50:'10:52:29',51:'10:52:37',52:'10:52:45',53:'10:52:53',54:'10:53:01',55:'10:53:09',56:'10:53:17',57:'10:53:25',58:'10:53:33',59:'10:53:41',60:'10:53:49',61:'10:53:57',62:'10:54:05',63:'10:54:13',64:'10:54:21',65:'10:54:29'},
        'scale1':{0:'10:46:54',1:'10:47:03',2:'10:47:05',5:'10:47:11',8:'10:47:17',12:'10:47:25',14:'10:47:29'},
        'scale2':{0:'10:47:27',1:'10:47:31',2:'10:47:33',5:'10:47:39',8:'10:47:45',10:'10:47:49'},
        'stage':{0:'10:52:13',1:'10:52:23',6:'10:52:28',10:'10:52:32',12:'10:52:34',15:'10:52:37',20:'10:52:42',25:'10:52:47'},
        'storage':{0:'10:53:09',1:'10:53:21',2:'10:53:23',3:'10:53:25',4:'10:53:27',5:'10:53:29',6:'10:53:31',7:'10:53:33',8:'10:53:35',9:'10:53:37',10:'10:53:39',11:'10:53:41',12:'10:53:43',13:'10:53:45',14:'10:53:47',15:'10:53:49',16:'10:53:51',17:'10:53:53',18:'10:53:55',19:'10:53:57',20:'10:53:59',21:'10:54:01',22:'10:54:03',23:'10:54:05',24:'10:54:07',25:'10:54:09',26:'10:54:11',27:'10:54:13',28:'10:54:15',29:'10:54:17'},
    }
    notes={
        'origin':'Covered gray near room11 door45:49, gone45:57. Empty gray local replacement reaches station45:57; visible cheese placement46:05 through53:09. Later layers/cover53:57-54:05; no next loaded departure by54:29. Earlier gray appears at platform through doorway46:53, settled47:01, remains through51:17, platform clear51:25. Narrow gray edge persists in right staging; identity uncertain. Empty gray from15 already in11 at54:13, parked left54:21, unloaded jack approaches filled station54:29. Fixed scrap tank is separate.',
        'scale1':'Initial46:54 early image excluded from alignment. Gray already on far-right platform at first usable47:03, stays through47:29. Operator attends the tank; people walk past. Earlier camera15 last usable44:42 to47:03 is141 seconds and includes room11 departure45:49-57. Direct room15 entry is missing.',
        'scale2':'Initial47:27 overlaps prior source. Gray stationary on platform47:31-49; two-second usable join47:29-31. People cross doorway, no new tank entry. Camera11 sampling retains later platform occupancy.',
        'stage':'Initial52:13 early image. Operator handles jack behind fixed blue bins52:23-47; person walks from doorway to left28-35. No unoccluded gray route shown. Directory name route is a search label only. Gray platform already cleared in camera11 at51:25; do not infer stored identity from operator alone.',
        'storage':'Initial53:09 early image. Covered gray already emerging beside rear row/door at first usable53:21, pulled23-25, turned27-29, pushed left31-37, settled39; fork withdrawal41-45 leaves gray parked. Missing34 seconds from previous usable camera15 sample52:47 to53:21. Neither already-stored relocation nor fresh origin linkage is proven. A different visibly empty gray is selected from left waiting row49-51, pulled53-55, turns/stops57-54:05, approaches door07, crosses09-17 (still partly visible). Camera11 has empty gray inside at54:13; keep clocks separate, do not infer exact offset.',
    }
    for k,m in metas.items():
        merge(OUT/'screening_source_reviews.json',[dict(review_id='20261015/'+windows[k][0],reviewed_at=stamp,reviewer='assistant_visual_review',date='20261015',camera=m['source']['camera'],split='train',source_member=m['source']['member'],source_sha256=m['source_sha256'],frames_manifest=str(paths[k].relative_to(ROOT)),sampled_frames_visually_reviewed=len(m['samples']),reviewed_sheets=m['sheets'],review_scope='All chronological sampled sheets inspected, selected native frames and separate object overlays reviewed. Not exhaustive native-frame tracking.',observation=notes[k],accepted_complete_cycle=False,clock_warning='Initial early frames excluded from alignment; PTS/filename are not clock offsets.',visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],visible_camera_clock=t,clock_read_uncertainty_seconds=1,image=m['samples'][i]['image'],usable_for_clock_alignment=not(i==0 and k!='origin')) for i,t in clocks[k].items()])],'review_id')
    def ev(k,a,b): return evidence(metas[k],a,b,paths[k])
    priorpath=OUT/'sequence_review/20261015/beige_scale_end_1041_cam11/frames.json'
    prior=read(priorpath)
    fillpath=OUT/'sequence_review/20261015/beige_scale_context_1037_cam11/frames.json'
    fill=read(fillpath)
    labels=read(OUT/'reviewed_sequence_labels.json')
    hist=OUT/'review_history/sequence_labels_before_20261031_24.json'
    if not hist.exists(): save(hist,labels)
    shared=dict(date='20261015',split='train',reviewer='assistant_visual_review',reviewed_at=stamp,dataset_release_accepted=False)
    gray=dict(shared,sequence_id='20261015_fresh_gray_departure_partial_1045',review_status='reviewed_partial_sequence',cycle_id=None,production_entry_count_target=None,camera_track_id={'11':'fresh_gray_fill_1037_departure1045','15':'unlinked_gray_scale_storage_1047_1053'},cross_camera_identity='unresolved_entry_gap_and_staging_route',camera_clock_offset_seconds=None,
        stages=[dict(stage='filling_observed',camera=11,visible_camera_clock_interval=['10:37:41','10:45:29'],clock_uncertainty_seconds=6,content_evidence='Visibly empty gray replacement receives cheese at station; fixed scrap receptacle separate.',evidence=[evidence(fill,3,49,fillpath),evidence(prior,1,37,priorpath)]),dict(stage='loaded_departure_11',camera=11,visible_camera_clock_interval=['10:45:41','10:45:57'],doorway_approach_observed_at='10:45:49',clock_uncertainty_seconds=8,observation='Covered45:35, pulled41, near door47-49, gone57. Exact threshold frame not sampled.',evidence=[evidence(prior,38,40,priorpath),ev('origin',0,1)])],missing_stages=['linked_entry_15','linked_scale_visit','linked_storage_placement'],
        unlinked_followup=dict(last_usable_camera15_before_entry_gap='10:44:42',first_usable_gray_on_platform_camera15='10:47:03',sampled_entry_gap_seconds=141,scale_camera11_interval=['10:47:01','10:51:17'],platform_clear_camera11='10:51:25',first_usable_gray_storage_route_camera15='10:53:21',platform_clear_to_first_route_sample_seconds=116,last_usable_camera15_staging_context='10:52:47',camera15_staging_to_first_route_gap_seconds=34,storage_placement_camera15_interval=['10:53:31','10:53:45'],unloaded_fork_withdrawal_camera15_interval=['10:53:41','10:53:45'],storage_observed_but_origin_unlinked=True,numeric_weight_kg=None,evidence=[ev('origin',8,65),ev('scale1',1,14),ev('scale2',1,10),ev('stage',1,25),ev('storage',1,13)],observation='Gray platform and later storage confirmed separately. Initial15 entry missing; staging route has34-second sample gap. No full cycle or new production entry target inferred.'),limitations=['White cover is not cheese proof.','No calibrated clock offset or exact entry assigned.','Storage visit alone does not resolve fresh origin or already-stored relocation.'])
    empty=dict(shared,sequence_id='20261015_empty_gray_return_1054',review_status='accepted_negative_sequence',cycle_id=None,production_entry_count_target=0,camera=15,camera_track_id='empty_gray_waiting_return_105349',negative_class='empty_crossing',tracked_tank_count=1,direction='15_to_11',visible_camera_clock_interval=['10:53:49','10:54:17'],clock_uncertainty_seconds=2,evidence=[ev('storage',15,29),ev('origin',63,65)],observation='Separate visibly empty gray taken from waiting row49-51, through aisle53-54:07, door09-17. Still partly visible in15 at17;11 empty tank already inside at13. Camera clocks not calibrated; keep separate observations.',label_scope='Only the empty return, excluding previous gray storage and next fresh gray filling.')
    # Extend an existing return through its local station replacement; do not
    # count the same physical empty tank as a second negative episode.
    prior_empty=copy.deepcopy(next(r for r in labels if r['sequence_id']=='20261015_empty_gray_return_1044'))
    prior_empty['reviewed_at']=stamp
    prior_empty['evidence'] += [ev('origin',0,2)]
    prior_empty.setdefault('followup_observations',[]).append(dict(camera=11,visible_camera_clock_interval=['10:45:49','10:46:05'],observation='Empty waiting gray moved locally into filling position45:49-57; new cheese placement46:05. This extends the previous return episode; no second negative count.'))
    merge(OUT/'reviewed_sequence_labels.json',[gray,empty,prior_empty],'sequence_id')
    queuepath=OUT/'sequence_followup_queue.json';queue=read(queuepath)
    hist=OUT/'review_history/followup_queue_before_20261031_24.json'
    if not hist.exists(): save(hist,queue)
    changes=[]
    for old in queue:
        if old['candidate_id']=='20261015_next_gray_departure_1045':
            r=copy.deepcopy(old)
            r.update(reviewed_at=stamp,status='resolved_to_reviewed_partial',resolved_sequence_id=gray['sequence_id'],observation='Loaded45min room11 departure confirmed. Room15 entry lies in141-second gap; later gray storage53min has unresolved origin/staging link.',next_action='Keep partial; no repeated gap search without new coverage.')
            r['evidence'] += [ev('origin',0,1),ev('scale1',1,14),ev('storage',1,13)]
            changes.append(r)
    changes.append(dict(candidate_id='20261015_next_gray_filling_1054',date='20261015',split='train',cycle_id=None,production_entry_count_target=None,status='partial_followup_pending',reviewed_at=stamp,observation='Separate gray replacement starts receiving cheese46:05; layers complete by53:49, covered53:57-54:05; operator approaches with jack54:29. No departure yet inspected.',next_action='Continue11 same104134-111111 source after PTS762 and15 after105418 only if needed; prioritise other training days for full-cycle diversity.',evidence=[ev('origin',1,65)]))
    merge(queuepath,changes,'candidate_id')
    save(OUT/'gap_search_20261031_24.json',dict(reviewed_at=stamp,day='20261015',findings=['Room15 entry141-second sample gap44:42-47:03 includes45min room11 departure.','Camera11 gray platform clear51:25;15 first usable gray storage route53:21,116 seconds apart; intermediate15 staging52:23-47 only shows operator behind bins.','Storage53:31-45 confirmed locally but fresh origin unlinked.','No already-stored relocation label inferred from covered tank emerging beside stored row.'],action='Keep partials; no invented linkage or clock offset.'))
    registry=read(OUT/'object_review_decisions.json')
    hist=OUT/'review_history/object_decisions_before_20261031_24.json'
    if not hist.exists(): save(hist,registry)
    decisions={r['id']:r for r in registry['reviews']}
    drafts={r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
    for ident,note in {'187':'Isolated covered gray departure near11 door.','188':'Empty gray local replacement; worker occlusion at upper rim and lower left.','189':'Top-truncated gray storage transit body; operator partly occludes right edge.','190':'Top-truncated empty gray return body; crop excludes background row.'}.items():
        assert ident not in decisions
        r=drafts[ident]
        decisions[ident]=dict(id=ident,image_sha256=r['sha256'],boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',load_state_reviewed=False,sequence_reviewed=False,instance_attributes=[dict(box_index=0,truncated=ident in ['189','190'],occluded=ident in ['188','189'],load_state='unknown_not_annotated')],evidence=[r['source_frame'],r['frames_manifest'],'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_22.jpg'],note=note)
    registry['reviews']=list(decisions.values())
    registry.setdefault('corrections',[]).append('Batch24:187-190 separately overlay reviewed; four ROIs/four boxes. Earlier decisions unchanged.')
    save(OUT/'object_review_decisions.json',registry)
    inv=read(BASE/'archive_inventory.json');inspected={m['source']['member']:m['source_sha256'] for m in metas.values()}
    for r in inv['records']:
        if r['member'] in inspected:r.update(pixel_inspected=True,sha256=inspected[r['member']])
    assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test')
    save(BASE/'archive_inventory.json',inv)
    reviews=read(OUT/'screening_source_reviews.json');total=sum(r['sampled_frames_visually_reviewed'] for r in reviews);added=sum(len(m['samples']) for m in metas.values())
    state['last_completed'] += [
        f'Batch24 inspected {added} chronological presentations in5 windows on15Oct; {total} total across {len({r["source_sha256"] for r in reviews})} sources and {len(reviews)} windows. Extractions complete;25/28Oct untouched.',
        'Fresh gray45min departure added as partial:141-second15 entry gap; later53min storage confirmed but origin unlinked. Existing44min empty return extended through local replacement without duplicate negative. Totals5 complete,22 partials.',
        'One empty gray15-to11 return54min added as negative. Total57 negatives. Next gray fresh filling54min queued without count.',
        'Four native ROI images187-190/four boxes approved after separate overlays. Totals191 candidates,136 approved images,192 boxes,55 exclusions,zero drafts. Dataset unreleased.'
    ]
    state['priority_next']=[
        'Batch24 complete.5 complete cycles all13Oct. Prioritise other training days and true post-storage relocation/same-load reentry; avoid accumulating only15Oct partials/easy negatives.',
        'Metadata-only scan found unreviewed6Oct15 sources101303-101436_10737864 and095611-095737_10731057 (93/86-second filename spans). Inspect adjacent11/15 context for a day-diverse cycle; filename spans do not prove continuous coverage.',
        '15Oct next gray filling54min queued:11 same104134-111111 after PTS762;15 after105418. All45min entry/scale/storage windows complete;141-second entry gap not bridged.',
        '13Oct next distinct load:11 sources093135-093311/093311-094655 and15 after093339 could support full cycle.13Oct102139-102912 long15 source unreviewed;11 origin may be missing.'
    ]+[p for p in state['priority_next'] if p.startswith('Known gaps') or p.startswith('25/28') or p.startswith('Old21Oct')]
    state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    state['scripts'] += [s for s in ['work/append_tank_roi_batch_20261031_24.py','work/record_tank_sequence_batch_20261031_24.py'] if s not in state['scripts']]
    save(OUT/'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_samples=added,total_presentations=total,additional_complete_cycles=0,additional_partial_sequences=1,additional_negative_sequences=1,training_started=False)))


if __name__=='__main__':main()
