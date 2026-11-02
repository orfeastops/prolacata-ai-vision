import datetime as dt
import hashlib,json
from pathlib import Path
from record_tank_boundary_review_20261031 import read,save,merge,evidence
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/tank_transfer_training_v1'
OUT=BASE/'dataset_v1'
RUN='sequence_review_20261031_47'
def main():
    state=read(OUT/'continuation_state.json')
    if RUN in state.get('completed_curation_runs',[]):return
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    windows={'broad':('third_gray_after1252_cam11',38),'dense':('third_departure1253_dense_cam11',20),'entrysearch':('third_entry1253_cam15',14)}
    paths={k:OUT/'sequence_review/20261015'/w/'frames.json' for k,(w,n) in windows.items()}
    metas={k:read(p) for k,p in paths.items()}
    clocks={'broad':{0:'12:53:00',2:'12:53:30',3:'12:53:45',4:'12:54:00',5:'12:54:15',7:'12:54:45',27:'12:59:45',30:'13:00:30',37:'13:02:15'},'dense':{0:'12:53:25',4:'12:53:33',5:'12:53:35',7:'12:53:39',9:'12:53:43',10:'12:53:45',12:'12:53:49',13:'12:53:51',15:'12:53:55',19:'12:54:03'},'entrysearch':{0:'12:53:26',5:'12:53:31',13:'12:53:39'}}
    notes={'broad':'All38 samples/seven sheets inspected. Station load has cheese53:00-30, covered departure by45. Distinct empty replacement at station54:00; fresh filling54:15 through13:02:15. Through door platform empty53:00-54:30, gray body54:45, people occlusion55:00-59:30, gray visible59:45-13:00:15, empty00:30 onward. Scale observation remains unlinked: arrival identity unavailable. Actual final clock exceeds filename end.', 'dense':'All20 samples/four sheets inspected; native39 and51 viewed. Cheese visible25-31, cover33, loaded departure35-49; threshold43-49. Separate empty replacement moves47-55 and remains visibly empty through54:03. Do not merge simultaneous tracks.', 'entrysearch':'All14 samples/three sheets inspected. Actual clocks53:26-39. People at door, no tank entry in this interval. Clip ends before camera11 departure threshold43-49; independent clocks and unknown offset. This is unsuccessful search context, not a whole-clip negative or a positive entry despite window name.'}
    for k,m in metas.items():
        w,n=windows[k];assert len(m['samples'])==n and m['source']['split']=='train' and m['source']['date']=='20261015'
        merge(OUT/'screening_source_reviews.json',[dict(review_id='20261015/'+w,reviewed_at=stamp,reviewer='assistant_visual_review',date='20261015',camera=m['source']['camera'],split='train',source_member=m['source']['member'],source_sha256=m['source_sha256'],frames_manifest=str(paths[k].relative_to(ROOT)),sampled_frames_visually_reviewed=n,reviewed_sheets=m['sheets'],observation=notes[k],accepted_complete_cycle=False,review_scope='All chronological sample presentations inspected; not exhaustive native-frame inspection.',visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],visible_camera_clock=t,clock_read_uncertainty_seconds=1,image=m['samples'][i]['image'],usable_for_clock_alignment=False) for i,t in clocks[k].items()])],'review_id')
    paths['fill']=OUT/'sequence_review/20261015/second_gray_scale_after1248_cam11/frames.json';metas['fill']=read(paths['fill'])
    def ev(k,a,b):return evidence(metas[k],a,b,paths[k])
    shared=dict(date='20261015',split='train',reviewer='assistant_visual_review',reviewed_at=stamp,dataset_release_accepted=False,camera_clock_offset_seconds=None,cycle_id=None)
    partial=dict(shared,sequence_id='20261015_third_gray_departure1253_partial',review_status='reviewed_partial_sequence',production_entry_count_target=None,partial_reason='Room15 incoming crossing and final storage identity not established. Available inspected entry-search source ends53:39.',observation='Fresh filling in11 followed by covered departure53:35-49. Later scale occupancy seen through door is unlinked; no production entry target.',evidence=[ev('fill',0,51),ev('broad',0,3),ev('dense',0,12),ev('entrysearch',0,13)],stages=[dict(stage='filling_observed',camera=11,evidence=[ev('fill',0,51),ev('broad',0,2)]),dict(stage='loaded_departure_11',camera=11,visible_camera_clock_interval=['12:53:35','12:53:49'],doorway_crossing_camera11_interval=['12:53:43','12:53:49'],evidence=[ev('dense',5,12)])],unlinked_followup=dict(observation='Through-door gray scale occupancy54:45-13:00:15; unknown identity across unseen entry.',evidence=[ev('broad',7,29)]))
    negative=dict(shared,sequence_id='20261015_empty_replacement1253',review_status='accepted_negative_sequence',production_entry_count_target=0,camera=11,negative_class='empty_tank_internal_reposition',tracked_tank_count=1,visible_camera_clock_interval=['12:53:47','12:54:03'],observation='Separate visibly empty lined gray tank moved from left waiting position into filling station. Stops before fresh filling.',label_scope='Replacement track only; excludes departing filled load and adjacent scrap tank.',evidence=[ev('dense',11,19)])
    save(OUT/'review_history/sequence_labels_before_20261031_47.json',read(OUT/'reviewed_sequence_labels.json'))
    merge(OUT/'reviewed_sequence_labels.json',[partial,negative],'sequence_id')
    qp=OUT/'sequence_followup_queue.json';queue=read(qp);save(OUT/'review_history/followup_queue_before_20261031_47.json',queue)
    for row in queue:
        if row.get('candidate_id')=='20261015_third_gray_filling_after1245':
            row.update(status='reviewed_partial_pending_entry_and_storage',resolved_sequence_id=partial['sequence_id'],cycle_id=None,reviewed_at=stamp,next_action='Do not repeat53:26-39 source15. Check alternate coverage of53:43-49; next known filename starts57:13, actual pixels not yet inspected here.')
    save(qp,queue)
    registry=read(OUT/'object_review_decisions.json');save(OUT/'review_history/object_decisions_before_20261031_47.json',registry)
    drafts={r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
    for ident,note in {'284':'Covered outgoing gray body.','285':'Empty replacement body; hands partly occlude rim.'}.items():
        assert not any(r['id']==ident for r in registry['reviews']);r=drafts[ident]
        registry['reviews'].append(dict(id=ident,image_sha256=r['sha256'],
          boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
          reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',load_state_reviewed=False,sequence_reviewed=False,
          instance_attributes=[dict(box_index=0,truncated=False,occluded=ident=='285',load_state='unknown_not_annotated')],
          evidence=[r['source_frame'],r['frames_manifest'],'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_37.jpg'],
          note=note+' Native context, crop and independent rendered overlay inspected.'))
    save(OUT/'object_review_decisions.json',registry)

    inv=read(BASE/'archive_inventory.json');inspected={m['source']['member']:m['source_sha256'] for m in metas.values()}
    for r in inv['records']:
        if r['member'] in inspected:r.update(pixel_inspected=True,sha256=inspected[r['member']])
    assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test')
    save(BASE/'archive_inventory.json',inv)
    state['last_completed']+=['Batch47:72 new sample presentations in three15Oct windows reviewed. Fresh third-gray departure1253 retained partial, missing verified15 entry/storage. One empty replacement negative added. Two native ROI images284-285 with two boxes independently overlay-reviewed. No test pixels or training.']
    state['priority_next']=['Batch47 saved: do not repeat third_gray_after1252_cam11,third_departure1253_dense_cam11,third_entry1253_cam15. Entry search ends53:39 before11 threshold53:43-49. Inspect alternate15 coverage or retain gap. Next source15 filename57:13 is not yet pixel-reviewed here.','15Oct next fresh station fill54:15-13:02:15 available in broad window. Seek paired later sources for day diversity; seven complete cycles still all13Oct.']+[p for p in state['priority_next'] if p.startswith('Known gaps') or p.startswith('25/28')]
    state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    state['scripts']+=['work/append_tank_roi_batch_20261031_47.py','work/record_tank_sequence_batch_20261031_47.py']
    save(OUT/'continuation_state.json',state)
    print('Recorded batch47:72 samples,2 images,1 negative,1 partial;0 new complete cycles')
if __name__=='__main__':main()
