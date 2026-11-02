"""Persist validation follow-up without inventing missing tank trajectories."""
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read, save, merge, evidence

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/tank_transfer_training_v1'
OUT=BASE/'dataset_v1'
RUN='sequence_review_20261031_29'

def main():
    state=read(OUT/'continuation_state.json')
    if RUN in state.get('completed_curation_runs',[]):
        print('Already recorded',RUN)
        return
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    windows={
        'staging':('beige_followup_1317_cam15',16),
        'scale15':('beige_followup_1318_cam15',8),
        'scale11':('beige_scale_followup_1317_cam11',51),
        'end15':('beige_scale_end_1322_cam15',13),
        'storage':('beige_storage_1323_cam15',19),
    }
    paths={k:OUT/'sequence_review/20261017'/w/'frames.json' for k,(w,n) in windows.items()}
    metas={k:read(p) for k,p in paths.items()}
    for k,m in metas.items():
        assert m['source']['date']=='20261017' and m['source']['split']=='validation'
        assert len(m['samples'])==windows[k][1]
    clocks={
        'staging':{0:'13:17:15',1:'13:17:21',2:'13:17:22',3:'13:17:23',4:'13:17:24',5:'13:17:25',6:'13:17:26',7:'13:17:27',8:'13:17:28',9:'13:17:29',10:'13:17:30',11:'13:17:31',12:'13:17:32',13:'13:17:33',14:'13:17:34',15:'13:17:35'},
        'scale15':{0:'13:18:46',1:'13:19:06',2:'13:19:08',3:'13:19:10',4:'13:19:12',5:'13:19:14',6:'13:19:16',7:'13:19:18'},
        'scale11':{0:'13:16:57',1:'13:17:05',2:'13:17:13',3:'13:17:21',4:'13:17:29',5:'13:17:37',6:'13:17:45',7:'13:17:53',8:'13:18:01',9:'13:18:09',10:'13:18:17',11:'13:18:25',12:'13:18:33',13:'13:18:41',14:'13:18:49',15:'13:18:57',16:'13:19:05',17:'13:19:13',18:'13:19:21',19:'13:19:29',20:'13:19:37',21:'13:19:45',22:'13:19:53',23:'13:20:01',24:'13:20:09',25:'13:20:17',26:'13:20:25',27:'13:20:33',28:'13:20:41',29:'13:20:49',30:'13:20:57',31:'13:21:05',32:'13:21:13',33:'13:21:20',34:'13:21:28',35:'13:21:36',36:'13:21:44',37:'13:21:52',38:'13:22:00',39:'13:22:08',40:'13:22:16',41:'13:22:24',42:'13:22:32',43:'13:22:40',44:'13:22:48',45:'13:22:56',46:'13:23:04',47:'13:23:12',48:'13:23:20',49:'13:23:28',50:'13:23:36'},
        'end15':{0:'13:21:53',1:'13:22:03',2:'13:22:05',3:'13:22:07',4:'13:22:09',5:'13:22:11',6:'13:22:13',7:'13:22:15',8:'13:22:17',9:'13:22:19',10:'13:22:21',11:'13:22:23',12:'13:22:25'},
        'storage':{0:'13:23:28',1:'13:23:34',2:'13:23:36',3:'13:23:38',4:'13:23:40',5:'13:23:42',6:'13:23:44',7:'13:23:46',8:'13:23:48',9:'13:23:50',10:'13:23:52',11:'13:23:54',12:'13:23:56',13:'13:23:58',14:'13:24:00',15:'13:24:02',16:'13:24:04',17:'13:24:06',18:'13:24:08'},
    }
    notes={
        'staging':'Initial17:15 precedes usable17:21. Operator handles a flat white board at rear doorway/staging area17:21-28, then bends beside the partly concealed staged load17:29-35. A separate empty foreground beige basket and fixed blue equipment stay in place. White tray stacks move through doorway independently. This begins after the17:01-05 room11 crossing, so no direct room15 entry clock or uninterrupted same-load identity is supplied. Native17:28 image inspected. A white board alone is not cheese evidence.',
        'scale15':'Initial18:46 precedes usable19:06. Operator works at partly hidden far-right scale area19:06-18 while another worker moves tall white tray stacks through doorway into11. Foreground empty beige waiting basket stays in place. No tank crossing in this sampled window.17:35-19:06 is an unobserved room15 interval, not evidence of uninterrupted staging-to-scale identity.',
        'scale11':'Loaded beige departure repeats prior17min context; different empty replacement in11 is subsequently filled from tray stacks. Platform visible through doorway is clear17:05-18:09. A beige body appears briefly at the side around18:17; platform still clear18:49 and covered beige is on scale18:57. Scale remains occupied in sampled views through22:24; clear22:32 onward. Native18:57 and22:24 frames confirm body and equipment rather than inferring from white colour alone. No numeric weight is readable. Tray stacks repeatedly brought15-to11 are not tanks. This follow-up does not bridge the concealed route from the earlier departing body into scale position.',
        'end15':'Initial21:53 precedes usable22:03. A worker crosses the aisle, collects a tall stack of white trays22:13-17 and pushes it through door22:19-25. Another operator remains near scale controls; scale load is mostly concealed at right. The tray-stack crossing is not a tank or fresh-production entry. Last reviewed sample22:25 precedes room11 scale clearance22:32; no storage route is shown here.',
        'storage':'Initial23:28 is early. Usable23:34 shows covered beige tank already in open aisle; operator pushes it to far-left end of rear row23:36-42. Native23:42/44/46/48 frames show destination outside the sheet crop: body remains parked and empty forks withdraw23:44-46. Forks are clear23:48; operator returns across aisle23:52-24:08. This proves a local storage placement, but previous15 samples end22:25 and next usable23:34 begins after the scale departure, so identity with the earlier scale load stays unlinked. It is not labelled as pre-existing-stock relocation or a second production entry.',
    }
    for k,m in metas.items():
        merge(OUT/'screening_source_reviews.json',[dict(
            review_id='20261017/'+windows[k][0],reviewed_at=stamp,reviewer='assistant_visual_review',
            date='20261017',camera=m['source']['camera'],split='val',source_member=m['source']['member'],
            source_sha256=m['source_sha256'],frames_manifest=str(paths[k].relative_to(ROOT)),
            sampled_frames_visually_reviewed=len(m['samples']),reviewed_sheets=m['sheets'],
            review_scope='All chronological sampled sheets inspected; selected native frames show scale and storage destination outside sheet crop. Not exhaustive native-frame viewing.',
            observation=notes[k],accepted_complete_cycle=False,
            clock_warning='Clock anchors read from pixels. Initial early frames, filename spans and PTS do not establish synchronization or fill trajectory gaps.',
            visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],
                relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],visible_camera_clock=t,
                clock_read_uncertainty_seconds=1,image=m['samples'][i]['image'],
                usable_for_clock_alignment=not(i==0 and k!='scale11')) for i,t in clocks[k].items()]
        )],'review_id')
    def ev(k,a,b):return evidence(metas[k],a,b,paths[k])
    labels=read(OUT/'reviewed_sequence_labels.json')
    save(OUT/'review_history/sequence_labels_before_20261031_29.json',labels)
    ident='20261017_beige_filling_aisle_departure_partial_1317'
    partial=copy.deepcopy(next(r for r in labels if r['sequence_id']==ident))
    partial.update(reviewed_at=stamp,camera_clock_offset_seconds=None,
        cross_camera_identity='Later staged, scale and storage observations remain explicitly unlinked across missing/occluded trajectories.',
        missing_stages=['verified_entry_15_clock_and_identity','linked_scale_visit','linked_storage_placement'])
    partial['reviewed_followup_observations']=[
        dict(stage='staging_candidate',camera=15,visible_camera_clock_interval=['13:17:21','13:17:35'],
            same_load_identity_confirmed=False,
            observation='Rear staged body already present at first usable frame; operator places white panel. Earlier direct entry missing.',evidence=[ev('staging',1,15)]),
        dict(stage='scale_visit',camera=11,visible_camera_clock_interval=['13:18:49','13:22:32'],
            placement_interval=['13:18:49','13:18:57'],occupied_sample_interval=['13:18:57','13:22:24'],
            departure_interval=['13:22:24','13:22:32'],numeric_weight_kg=None,same_load_identity_confirmed=False,
            observation='Covered beige scale body through doorway. Interval is from camera11, not calibrated camera15 time. Route from17min departure is concealed/unrecorded in15.',
            evidence=[ev('scale11',14,42),ev('scale15',1,7),ev('end15',1,12)]),
        dict(stage='storage_placement',camera=15,visible_camera_clock_interval=['13:23:34','13:23:48'],
            storage_confirmed_interval=['13:23:44','13:23:48'],same_load_identity_confirmed=False,
            observation='Covered beige parked at far-left rear row; empty forks withdrawn44-46 and fully clear48. Missing route after scale, so not a linked full cycle.',
            evidence=[ev('storage',1,8)]),
    ]
    partial['limitations'] += [
        'Later room15 staging, scale and storage evidence is retained without promoting the sequence to a complete cycle.',
        'Room15 usable samples end13:22:25 and next start13:23:34. Initial23:28 frame is retained but cannot establish continuous identity.',
        'Covered beige appearance alone cannot link tanks across missing routes; no production total is assigned.',
    ]
    merge(OUT/'reviewed_sequence_labels.json',[partial],'sequence_id')
    qp=OUT/'sequence_followup_queue.json'
    save(OUT/'review_history/followup_queue_before_20261031_29.json',read(qp))
    merge(qp,[dict(candidate_id='20261017_beige1317_followup',date='20261017',split='val',cycle_id=None,
        production_entry_count_target=None,status='resolved_to_reviewed_partial_with_unlinked_followups',reviewed_at=stamp,
        resolved_sequence_id=ident,
        observation='Reviewed17min staging,19-22min scale,23min storage. Direct15 entry and staging/scale/storage routes remain missing. No full-cycle label.',
        next_action='Do not re-extract these reviewed windows to fill absent trajectories. Need additional source coverage to link this load. Keep17Oct validation only.',
        evidence=[ev('staging',1,15),ev('scale11',14,42),ev('storage',1,8)])],'candidate_id')
    save(OUT/'gap_search_20261031_29.json',dict(reviewed_at=stamp,date='20261017',split='val',
        known_intervals=[
            dict(camera=15,last_reviewed_clock='13:17:35',next_usable_clock='13:19:06',issue='Unobserved staging-to-scale route; intervening initial frame18:46 not used for continuous identity.'),
            dict(camera=15,last_reviewed_clock='13:22:25',next_usable_clock='13:23:34',issue='Scale-to-storage route missing; source initial23:28 already in transit.'),
        ],
        scale_clearance_camera11_interval=['13:22:24','13:22:32'],
        storage_release_camera15_interval=['13:23:44','13:23:48'],
        camera_clock_offset_seconds=None,full_cycle_confirmed=False,
        conclusion='Refined partial only. Local storage is observed; source link to prior scale body is unknown. Do not turn gap into negative or new production target.'))

    registry=read(OUT/'object_review_decisions.json')
    save(OUT/'review_history/object_decisions_before_20261031_29.json',registry)
    decisions={r['id']:r for r in registry['reviews']}
    drafts={r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
    obj_notes={
        '211':'Beige scale body seen through door; doorpost and adjacent equipment partially occlude edges. No mass or load class exported.',
        '212':'Separate beige tank receiving cheese in open11 aisle, partly occluded by two workers. Not the beige load already on scale.',
        '213':'Covered beige storage-transit body crop with top clipped. Pallet jack below/right is not a second tank.',
        '214':'Distinct visibly empty foreground waiting basket in15; native/crop bottom clips body. It is pre-existing inventory, not a new entry.',
    }
    for ident,note in obj_notes.items():
        assert ident not in decisions
        r=drafts[ident]
        decisions[ident]=dict(id=ident,image_sha256=r['sha256'],
            boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',
            load_state_reviewed=False,sequence_reviewed=False,
            instance_attributes=[dict(box_index=0,truncated=ident in ['213','214'],occluded=ident in ['211','212'],load_state='unknown_not_annotated')],
            evidence=[r['source_frame'],r['frames_manifest'],'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_26.jpg'],note=note)
    registry['reviews']=list(decisions.values())
    registry.setdefault('corrections',[]).append('Batch29:211-214 independently overlay-reviewed, all validation only. Prior approvals preserved. Four images/four tank boxes; no load attribute training export.')
    save(OUT/'object_review_decisions.json',registry)
    inv=read(BASE/'archive_inventory.json')
    inspected={m['source']['member']:m['source_sha256'] for m in metas.values()}
    for r in inv['records']:
        if r['member'] in inspected:r.update(pixel_inspected=True,sha256=inspected[r['member']])
    assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test')
    save(BASE/'archive_inventory.json',inv)
    reviews=read(OUT/'screening_source_reviews.json')
    total=sum(r['sampled_frames_visually_reviewed'] for r in reviews)
    state['last_completed'] += [
        f'Batch29 reviewed107 chronological presentations in5 validation windows; {total} total across{len({r["source_sha256"] for r in reviews})} sources and{len(reviews)} windows. Extractions finished;25/28Oct untouched.',
        '17Oct beige17min partial refined with later scale placement18:49-57, departure22:24-32 and local storage release23:44-48. Identity across concealed/missing entry/staging/storage route remains unlinked. Totals unchanged:5 complete,68 negatives,27 partials.',
        'Four validation ROI images211-214 and four boxes passed separate overlay review.215 candidates,160 accepted images,219 boxes,55 exclusions,zero drafts. No training release.',
    ]
    state['priority_next']=[
        'Batch29 complete.5 full cycles are still all13Oct. Prioritise diverse training-day full routes and a complete validation example; do not pad easy negatives.',
        '17Oct17min beige follow-up is resolved to a partial: scale18:57-22:24 and storage23:44-48 observed, but15 entry/staging and22:25-23:34 route gaps remain. Do not repeat these windows without new source coverage.',
        'For a different training period, metadata-only15Oct camera15 adjacent sources123922-124025_12005694,124016-124054_12006487,124053-124142_12007276 form a filename-overlap search cluster. Find paired11 filling/departure and surrounding15 scale context before accepting a cycle. Filename overlap is not proven continuity.',
        'Metadata audit found10Oct1020-1025 long15 cluster, but its102149-102519_11336402 and paired11 source102209-102546_11298457 were already inspected in empty-return review. Read prior notes before reusing; longest filename span alone is not a production candidate.',
    ]+[p for p in state['priority_next'] if p.startswith('Known gaps') or p.startswith('25/28') or p.startswith('Old21Oct') or p.startswith('6Oct17min') or p.startswith('8Oct11')]
    state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    state['scripts'] += [s for s in ['work/append_tank_roi_batch_20261031_29.py','work/record_tank_sequence_batch_20261031_29.py'] if s not in state['scripts']]
    save(OUT/'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_samples=107,total_presentations=total,additional_complete_cycles=0,additional_negative_sequences=0,additional_partial_sequences=0,training_started=False)))

if __name__=='__main__':main()
