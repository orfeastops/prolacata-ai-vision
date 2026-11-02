"""Record validation-only17Oct evidence, retaining unobserved route segments."""
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read, save, merge, evidence

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/tank_transfer_training_v1'
OUT=BASE/'dataset_v1'
RUN='sequence_review_20261031_40'

def main():
    state=read(OUT/'continuation_state.json')
    if RUN in state.get('completed_curation_runs',[]):
        print('Already recorded',RUN);return
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    windows={'broad':('afternoon_1331_cam11',68),'storage':('afternoon_1331_cam15',22),
        'entry':('afternoon_1325_entry_cam15',32),'departure':('afternoon_1325_departure_cam11',45)}
    paths={k:OUT/'sequence_review/20261017'/w/'frames.json' for k,(w,_) in windows.items()}
    metas={k:read(p) for k,p in paths.items()}
    for k,m in metas.items():
        assert m['source']['date']=='20261017' and m['source']['split']=='validation'
        assert len(m['samples'])==windows[k][1]
    clocks={
        'broad':{0:'13:23:36',1:'13:23:51',2:'13:24:06',3:'13:24:21',4:'13:24:36',5:'13:24:51',6:'13:25:06',
            7:'13:25:21',8:'13:25:36',9:'13:25:51',10:'13:26:06',11:'13:26:21',12:'13:26:36',13:'13:26:51',
            14:'13:27:06',15:'13:27:21',16:'13:27:36',17:'13:27:51',18:'13:28:06',19:'13:28:21',20:'13:28:36',
            21:'13:28:51',22:'13:29:06',23:'13:29:21',24:'13:29:36',25:'13:29:51',26:'13:30:06',27:'13:30:21',
            28:'13:30:36',29:'13:30:51',30:'13:31:06',31:'13:31:21',32:'13:31:36',33:'13:31:51',34:'13:32:06',
            35:'13:32:21',36:'13:32:36',37:'13:32:51',38:'13:33:06',39:'13:33:21',40:'13:33:36',41:'13:33:51',
            42:'13:34:06',43:'13:34:21',44:'13:34:36',45:'13:34:51',46:'13:35:06',47:'13:35:21',48:'13:35:36',
            49:'13:35:52',50:'13:36:06',51:'13:36:21',52:'13:36:37',53:'13:36:52',54:'13:37:07',55:'13:37:22',
            56:'13:37:37',57:'13:37:52',58:'13:38:07',59:'13:38:22',60:'13:38:37',61:'13:38:52',62:'13:39:07',
            63:'13:39:22',64:'13:39:37',65:'13:39:52',66:'13:40:07',67:'13:40:22'},
        'storage':{0:'13:31:09',1:'13:31:29',2:'13:31:31',3:'13:31:33',4:'13:31:35',5:'13:31:37',6:'13:31:39',
            7:'13:31:41',8:'13:31:43',9:'13:31:45',10:'13:31:47',11:'13:31:49',12:'13:31:51',13:'13:31:53',
            14:'13:31:55',15:'13:31:57',16:'13:31:59',17:'13:32:01',18:'13:32:03',19:'13:32:05',20:'13:32:07',21:'13:32:09'},
        'entry':{0:'13:25:38',1:'13:25:40',6:'13:25:45',8:'13:25:47',12:'13:25:51',13:'13:25:52',14:'13:25:53',
            15:'13:25:54',16:'13:25:55',17:'13:25:56',18:'13:25:57',19:'13:25:58',20:'13:25:59',21:'13:26:00',
            22:'13:26:01',23:'13:26:02',24:'13:26:03',25:'13:26:04',26:'13:26:05',27:'13:26:06',28:'13:26:07',
            29:'13:26:08',30:'13:26:10',31:'13:26:11'},
        'departure':{0:'13:25:31',5:'13:25:36',8:'13:25:39',11:'13:25:42',12:'13:25:43',13:'13:25:44',14:'13:25:45',
            15:'13:25:46',16:'13:25:47',17:'13:25:48',18:'13:25:49',19:'13:25:50',20:'13:25:51',21:'13:25:52',
            22:'13:25:53',23:'13:25:54',24:'13:25:55',25:'13:25:56',26:'13:25:57',27:'13:25:58',28:'13:25:59',
            29:'13:26:00',35:'13:26:06',39:'13:26:10',40:'13:26:11',41:'13:26:12',42:'13:26:13',43:'13:26:14',44:'13:26:15'},
    }
    notes={
        'broad':'All68 chronological samples/12 sheets inspected.23:36-25:36 fresh cheese placed into beige tank from tray stacks, covered and removed near25:51. Different empty replacement is filled26:21-32:36; another beige empty body comes in32:51 and is parkedleft33:06, and previous loaded body departs33:36-51. Platform beige body at side26:21-51, moving27:06 and onscale27:21-30:36, clear30:51. A second scale body occupies35:06-38:07, is moving38:22, then covered body returns15-to11 at38:37 and is parkedleft39:07. At39:22 another visibly empty body enters; distinct station load is pulledtowarddoor39:52 and visible in15 at40:22. These later tracks are queued for dense identity/entry/reentry review, not new production labels. Native23:36 and38:37 inspected. Tray stacks and fixed scrap tank are separate objects.',
        'storage':'All22 samples/four original sheets inspected, plus two wider sheets of existing samples10-21 and selected native frames. Initial31:09 is isolated from next31:29 and is not clock alignment evidence. Covered beige body moves from near scale31:29 through aisle31:45; turns toward storage row31:47-53, remains parked55 onward. Empty forks withdrawn57-59; operator then approaches a different empty tank at left32:07-09. Wide sheets correct the original ROI clipping at left. This is confirmed storage of the tracked body, but its origin/scale-to-aisle trajectory is not linked across missing earlier media.',
        'entry':'All32 samples/six sheets inspected. Pixel clock initial25:38, next25:40, last26:11. Person alone crosses25:45-47. Beige fresh-loaded body appears at doorway25:52-56, turns/stages57-58 behind foreground bins, operatorhandleswhitepanel26:00-04. Different visibly empty beige tank is pushed fromleft towarddoor26:00-11. Its entry to11 occurs after this window and is not assigned an exact time. Native26:03 inspected to separate the empty body from loaded staged body and fixed bins. No whole-room zero label.',
        'departure':'All45 chronological samples/eight sheets inspected. Last cheese placements31-42; white sheet42-44, jack pulls45-46, turns47-48, movesbehindstack49-51. Partially occluded doorway52-57, clear58. Same fresh-loaded beige body corresponds to paired15 entry52-58. Native filling context from broad window confirms cheese rather than inferring from cover. Different body at right in15 visible26:13-15; no completed scale/storage association inferred from colour.',
    }
    for k,m in metas.items():
        extra=[]
        if k=='storage':extra=[str((paths[k].parent/f'wide_storage_{i}.jpg').relative_to(ROOT)) for i in (10,16)]
        merge(OUT/'screening_source_reviews.json',[dict(review_id='20261017/'+windows[k][0],reviewed_at=stamp,
            reviewer='assistant_visual_review',date='20261017',camera=m['source']['camera'],split='val',
            source_member=m['source']['member'],source_sha256=m['source_sha256'],frames_manifest=str(paths[k].relative_to(ROOT)),
            sampled_frames_visually_reviewed=len(m['samples']),reviewed_sheets=m['sheets'],supplemental_reviewed_sheets=extra,
            review_scope='Chronological sampled-image inspection, selected native frames, and separate object overlays. Validation annotation only; no training or rule tuning.',
            observation=notes[k],accepted_complete_cycle=False,
            clock_warning='Pixel clocks retained independently. Initial frame discontinuities, filenames and PTS do not establish synchronization.',
            visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],
                relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],visible_camera_clock=t,
                clock_read_uncertainty_seconds=1,image=m['samples'][i]['image'],usable_for_clock_alignment=False)
                for i,t in clocks[k].items()])],'review_id')
    def ev(k,a,b):return evidence(metas[k],a,b,paths[k])
    save(OUT/'review_history/sequence_labels_before_20261031_40.json',read(OUT/'reviewed_sequence_labels.json'))
    shared=dict(date='20261017',split='val',reviewer='assistant_visual_review',reviewed_at=stamp,
        dataset_release_accepted=False,cycle_id=None,camera_clock_offset_seconds=None)
    partial=dict(shared,sequence_id='20261017_beige_departure1325_partial',review_status='reviewed_partial_sequence',
        production_entry_count_target=None,observed_loaded_entry_count=1,
        observed_entry_count_scope='One matched entry; not an accepted filling-to-storage cycle or daily total.',
        camera_track_id={'11':'beige_fresh_fill1325','15':'beige_entry1325'},
        stages=[
            dict(stage='filling_observed',camera=11,visible_camera_clock_interval=['13:23:36','13:25:42'],
                initial_contents_unknown=True,observation='Cheese visibly placed from tray stacks; no block count inferred.',evidence=[ev('broad',0,8),ev('departure',0,11)]),
            dict(stage='loaded_departure_11',camera=11,visible_camera_clock_interval=['13:25:45','13:25:58'],
                observation='White sheet, jack pickup, move behind trays, doorway crossing and clear doorway.',evidence=[ev('departure',12,27)]),
            dict(stage='entry_15',camera=15,visible_camera_clock_interval=['13:25:52','13:25:58'],
                room11_clock_interval=['13:25:52','13:25:58'],clock_uncertainty_seconds=1,identity_confirmed=True,
                correspondence_basis='Same beige fresh-filled body, white sheet, jack/operator and simultaneous directed doorway passage in both views. No scalar offset fitted.',
                evidence=[ev('departure',21,27),ev('entry',12,19)]),
            dict(stage='staging_observation',camera=15,visible_camera_clock_interval=['13:25:58','13:26:11'],
                observation='Tracked loaded body remains behind foreground bins; operator moves white panel. Empty replacement is a separate body.',evidence=[ev('entry',19,31)])],
        reviewed_followup_observations=[
            dict(stage='scale_visit',camera=11,visible_camera_clock_interval=['13:27:21','13:30:36'],
                departure_interval=['13:30:36','13:30:51'],same_load_identity_confirmed=False,numeric_weight_kg=None,
                observation='Beige body staged right26:21-51, moves27:06 and on platform27:21.15 footage between26:11 and31:09 absent; staging route not densely certified.',evidence=[ev('broad',11,29)]),
            dict(stage='storage_placement',camera=15,visible_camera_clock_interval=['13:31:29','13:31:59'],
                parked_interval=['13:31:53','13:31:59'],empty_fork_withdrawal_interval=['13:31:57','13:31:59'],
                same_load_identity_confirmed=False,storage_of_this_local_track_confirmed=True,
                observation='A covered beige body follows visible aisle route into row and empty forks withdraw. Same body remains parked32:09. Missing scale-to-aisle route prevents linking to1325 arrival.',
                supplemental_evidence=[str((paths['storage'].parent/f'wide_storage_{i}.jpg').relative_to(ROOT)) for i in (10,16)],
                evidence=[ev('storage',1,21)])],
        missing_stages=['verified_staging_to_scale_identity','verified_scale_to_storage_identity'],
        limitations=['No complete-cycle count assigned. The storage track is not a new observed room entry.',
            'Platform clear30:51;15 isolated initial31:09 followed by31:29. This gap does not prove same-load identity.',
            '17Oct validation only. No model, prompt, sampling rule or threshold tuned from these labels.'])
    negative=dict(shared,sequence_id='20261017_empty_beige_internal1326',review_status='accepted_negative_sequence',
        production_entry_count_target=0,camera=15,negative_class='empty_tank_internal_reposition',tracked_tank_count=1,
        direction='room15_left_aisle_toward_door',visible_camera_clock_interval=['13:26:00','13:26:11'],
        observation='Different visibly empty body pushed toward door while newly arrived loaded tank remains staged.',
        label_scope='Only this empty internal movement; excludes simultaneous loaded arrival and fixed stock. No exact crossing time or fresh production inferred.',
        evidence=[ev('entry',21,31)])
    merge(OUT/'reviewed_sequence_labels.json',[partial,negative],'sequence_id')
    qp=OUT/'sequence_followup_queue.json'
    save(OUT/'review_history/followup_queue_before_20261031_40.json',read(qp))
    merge(qp,[dict(candidate_id='20261017_beige1325',date='20261017',split='val',reviewed_at=stamp,
        status='resolved_as_partial_route_gap',resolved_sequence_id=partial['sequence_id'],cycle_id=None,production_entry_count_target=None,
        observation='Fresh filling and matched entry52-58; scale and storage followup kept unlinked.',
        next_action='Do not repeat known absent26:11-to31:09 room15 route. Preserve storage/entry labels separately unless new media bridges them.',
        evidence=[ev('departure',21,27),ev('entry',12,31),ev('storage',1,21)]),
        dict(candidate_id='20261017_beige1333_return1338',date='20261017',split='val',reviewed_at=stamp,
            status='needs_dense_validation_route_and_return_review',cycle_id=None,production_entry_count_target=None,
            observation='Second fresh fill26:21-32:36 exits33:36-51; scale body35:06-38:07, covered return15-to11 at38:37, parkedleft39:07. Distinct station body exits near40:22.',
            next_action='Inspect dense33min departure/15 counterpart if present, and38min covered return. Keep distinct40min departure separate; do not count return/reposition as new production or infer identities from15sec sampling.',
            evidence=[ev('broad',11,67)])],'candidate_id')
    registry=read(OUT/'object_review_decisions.json')
    save(OUT/'review_history/object_decisions_before_20261031_40.json',registry)
    decisions={r['id']:r for r in registry['reviews']}
    drafts={r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
    for ident,note,occluded,truncated,sheet in [
        ('261','Filling tank, worker overlaps left rim.',True,False,33),
        ('262','Covered body returning to11; clear physical boundary.',False,False,34),
        ('263','Storage-aisle tank with worker occlusion and top crop truncation.',True,True,34)]:
        assert ident not in decisions
        r=drafts[ident];assert r['split']=='val' and len(r['boxes_xyxy'])==1
        decisions[ident]=dict(id=ident,image_sha256=r['sha256'],
            boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',
            load_state_reviewed=False,sequence_reviewed=False,
            instance_attributes=[dict(box_index=0,truncated=truncated,occluded=occluded,load_state='unknown_not_annotated')],
            evidence=[r['source_frame'],r['frames_manifest'],f'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_{sheet:02d}.jpg'],
            note=note+' Native context and separate rendered overlay inspected. Validation only; no training release.')
    registry['reviews']=list(decisions.values())
    registry.setdefault('corrections',[]).append('Batch40: three17Oct validation ROI images/three boxes separately reviewed; no prior decisions replaced.')
    save(OUT/'object_review_decisions.json',registry)
    inv=read(BASE/'archive_inventory.json');inspected={m['source']['member']:m['source_sha256'] for m in metas.values()}
    for r in inv['records']:
        if r['member'] in inspected:r.update(pixel_inspected=True,sha256=inspected[r['member']])
    assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test')
    save(BASE/'archive_inventory.json',inv)
    reviews=read(OUT/'screening_source_reviews.json');total=sum(r['sampled_frames_visually_reviewed'] for r in reviews)
    added=sum(n for _,n in windows.values())
    state['last_completed'] += [
        f'Batch40 reviewed {added} new validation17Oct sample presentations in four windows; {total} total across {len({r["source_sha256"] for r in reviews})} sources and {len(reviews)} windows. Two wide views reuse samples, not additional counts. Extractions complete; test pixels untouched.',
        '17Oct fresh beige departure matched to15 entry13:25:52-58. Scale and31min storage followups remain unlinked across route gaps. Five complete cycles unchanged;35 partials.',
        'One track-scoped empty internal movement added;84 negatives total. Later33min departure/38min covered return queued for dense review without new production labels.',
        'Three validation ROI images/three boxes approved:264 candidates,206 approved,271 boxes,58 exclusions,zero drafts. Dataset not released; no training.',
    ]
    state['priority_next']=[
        'Batch40 complete. Prioritise paired full routes outside13Oct and17Oct validation; avoid resampling known export gaps.',
        '17Oct33min beige departure and38min covered15-to11 return queued. Broad23:36-40:22 inspected; inspect dense boundaries and15 counterpart before identity/reentry labels. Distinct40min station departure stays separate.',
        '17Oct1325 partial has direct entry52-58 and independent31:29-59 confirmed storage. Staging-to-scale andscale-to-storage identity gaps remain; do not invent full cycle.',
    ]+[p for p in state['priority_next'] if not p.startswith('Batch39')]
    state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    state['scripts'] += ['work/append_tank_roi_batch_20261031_40.py','work/record_tank_sequence_batch_20261031_40.py']
    save(OUT/'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_samples=added,total_presentations=total,
        additional_complete_cycles=0,additional_negative_sequences=1,additional_partial_sequences=1,training_started=False)))

if __name__=='__main__':main()
