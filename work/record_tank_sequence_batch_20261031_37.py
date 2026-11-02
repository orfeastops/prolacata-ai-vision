"""Record inspected6Oct morning evidence, preserving unobserved cross-camera gaps."""
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read, save, merge, evidence

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/tank_transfer_training_v1'
OUT=BASE/'dataset_v1'
RUN='sequence_review_20261031_37'

def main():
    state=read(OUT/'continuation_state.json')
    if RUN in state.get('completed_curation_runs',[]):
        print('Already recorded',RUN);return
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    windows={
        'broad':('morning_route_0750_cam11',49),
        'after':('morning_route_0802_cam11',33),
        'door15':('morning_entry_0803_cam15',24),
        'departure':('morning_departure_0801_cam11',46),
        'before15':('morning_preentry_0801_cam15',12),
        'scale':('morning_scale_0805_cam11',39),
    }
    paths={k:OUT/'sequence_review/20261006'/w/'frames.json' for k,(w,_) in windows.items()}
    metas={k:read(p) for k,p in paths.items()}
    for k,m in metas.items():
        assert m['source']['date']=='20261006' and m['source']['split']=='train'
        assert len(m['samples'])==windows[k][1]
    # Selected manually read pixel clocks; PTS and filename time are not clock evidence.
    clocks={
        'broad':{0:'07:50:11',1:'07:50:41',4:'07:51:26',20:'07:55:26',38:'07:59:56',
            39:'08:00:11',40:'08:00:27',41:'08:00:41',42:'08:00:56',43:'08:01:11',
            44:'08:01:27',45:'08:01:41',46:'08:01:56',47:'08:02:11',48:'08:02:26'},
        'after':{0:'08:02:16',1:'08:02:35',2:'08:02:40',3:'08:02:45',7:'08:03:05',
            8:'08:03:10',9:'08:03:15',13:'08:03:35',24:'08:04:30',32:'08:05:10'},
        'door15':{0:'08:02:52',1:'08:03:03',2:'08:03:04',3:'08:03:05',4:'08:03:06',
            5:'08:03:07',6:'08:03:08',7:'08:03:09',8:'08:03:10',9:'08:03:11',10:'08:03:12',
            11:'08:03:13',12:'08:03:14',13:'08:03:15',14:'08:03:16',23:'08:03:25'},
        'departure':{0:'08:01:21',3:'08:01:24',5:'08:01:26',8:'08:01:29',9:'08:01:30',
            12:'08:01:33',18:'08:01:39',20:'08:01:41',23:'08:01:44',24:'08:01:45',
            26:'08:01:47',27:'08:01:48',28:'08:01:49',29:'08:01:50',30:'08:01:51',
            31:'08:01:52',32:'08:01:53',33:'08:01:54',35:'08:01:56',38:'08:01:59',
            40:'08:02:01',43:'08:02:04',45:'08:02:06'},
        'before15':{0:'08:01:15',1:'08:01:30',2:'08:01:31',3:'08:01:32',4:'08:01:33',
            5:'08:01:34',6:'08:01:35',7:'08:01:36',8:'08:01:37',9:'08:01:38',
            10:'08:01:39',11:'08:01:40'},
        'scale':{0:'08:05:14',1:'08:05:24',2:'08:05:34',3:'08:05:44',4:'08:05:54',
            5:'08:06:04',6:'08:06:14',15:'08:07:44',16:'08:07:54',17:'08:08:04',
            18:'08:08:15',19:'08:08:25',20:'08:08:35',21:'08:08:45',22:'08:08:55',
            23:'08:09:05',24:'08:09:15',25:'08:09:25',26:'08:09:35',27:'08:09:45',
            28:'08:09:55',29:'08:10:05',30:'08:10:15',31:'08:10:25',32:'08:10:35',
            33:'08:10:45',34:'08:10:55',35:'08:11:05',36:'08:11:15',37:'08:11:25',38:'08:11:35'},
    }
    notes={
        'broad':'All49 chronological samples inspected. Blue-lined station body contains cheese and receives further additions through08:01:27. Initial contents unknown. Third operator prepares manual jack51:26, then waits. White panels laid near01:27; filled body moves away01:41 and is gone01:56. Distinct empty replacement arrives01:56 and is at station02:11. Fixed scrap tank on right remains distinct. Dense doorway/replacement follow-up inspected separately. No link to earlier07:45 load or numerical camera offset inferred.',
        'after':'All33 chronological samples inspected. Initial08:02:16 then02:35. Replacement station tank receives cheese. A light beige/gray body with blue material at top is visible beyond the door from02:45 near/on platform and remains to05:10. Yellow powered pallet truck exits11 toward15 near03:05 without tank cargo. Door/scale body is not assigned to prior blue departure: entry/staging route missing, physical appearance and covering differ. Same-color or time-near observations are insufficient.',
        'door15':'All24 chronological samples inspected. Initial02:52 then03:03. Unloaded yellow powered pallet truck emerges from11, turns left03:03-08 and moves left out of the crop by03:12. No tank on its forks. Operator remains near hidden doorway/staging area. Native03:15 inspected: fixed empty foreground bins obscure the scale, covered tanks already in rows remain separate, and beige blue-lined wall tank is distinct. Fresh blue load entry01:47-52 is not sampled. Window name is a candidate label, not proof of an entry.',
        'departure':'All46 one-second samples inspected, displayed01:21-02:06. Cheese visible21-26, white panels positioned24-32. Unloaded yellow powered truck enters11 at29-33 and moves left. Fresh station tank pulled39, clear station41, turns42-45, reaches door47, crosses48-51 and is absent52. Separate empty blue tank selected from waiting row48, moved54-59 and at station02:01-04. Native01:41,47,56 inspected. Later cheese additions excluded from replacement negative. Fixed scrap tank is not the production load.',
        'before15':'All12 chronological samples inspected. Initial01:15 then01:30. Unloaded yellow truck leaves15 into11 at30-32, clear33. This precedes filled departure from11 at47-52. Source ends01:40, next15 initial02:52 then usable03:03; the loaded entry is in missing room15 coverage. Existing tanks are not labeled new production. No whole-room zero label.',
        'scale':'All39 chronological samples inspected. Light beige/gray blue-topped tank on platform beyond door05:14-54, moves off06:04, clear06:14. Native05:54 and06:04 checked. Identity relative to blue fresh departure remains unverified. Unloaded manual jack returns07:44. Replacement station body keeps receiving cheese through11:35, sometimes with white sheets/layers. Many stationary empty tanks at left and scrap tank right remain distinct. Room15 next metadata starts07:11, so it does not bridge06:04 platform departure. No storage completion or measured weight inferred.',
    }
    for k,m in metas.items():
        merge(OUT/'screening_source_reviews.json',[dict(
            review_id='20261006/'+windows[k][0],reviewed_at=stamp,reviewer='assistant_visual_review',
            date='20261006',camera=m['source']['camera'],split='train',
            source_member=m['source']['member'],source_sha256=m['source_sha256'],frames_manifest=str(paths[k].relative_to(ROOT)),
            sampled_frames_visually_reviewed=len(m['samples']),reviewed_sheets=m['sheets'],
            review_scope='All chronological sample sheets inspected; selected native images and four separate rendered object overlays reviewed. Not exhaustive native-frame viewing.',
            observation=notes[k],accepted_complete_cycle=False,
            clock_warning='Selected pixel clocks only. Stale initial frames and filename/PTS are not synchronization evidence.',
            visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],
                relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],visible_camera_clock=t,
                clock_read_uncertainty_seconds=1,image=m['samples'][i]['image'],usable_for_clock_alignment=False)
                for i,t in clocks[k].items()])],'review_id')

    def ev(k,a,b):return evidence(metas[k],a,b,paths[k])
    save(OUT/'review_history/sequence_labels_before_20261031_37.json',read(OUT/'reviewed_sequence_labels.json'))
    shared=dict(date='20261006',split='train',reviewer='assistant_visual_review',reviewed_at=stamp,
        dataset_release_accepted=False,cycle_id=None,camera_clock_offset_seconds=None)
    partial=dict(shared,sequence_id='20261006_blue_station_departure0801_partial',
        review_status='reviewed_partial_sequence',production_entry_count_target=None,
        camera_track_id={'11':'blue_station_load0801','15':None},
        stages=[
            dict(stage='filling_observed',camera=11,visible_camera_clock_interval=['07:50:41','08:01:26'],
                initial_contents_unknown=True,evidence=[ev('broad',1,44),ev('departure',0,5)]),
            dict(stage='loaded_departure_11',camera=11,visible_camera_clock_interval=['08:01:39','08:01:52'],
                observation='Fresh filled station body covered with white panels, then physically exits room11.',evidence=[ev('departure',18,31)]),
            dict(stage='entry_15',camera=11,visible_camera_clock_interval=['08:01:47','08:01:52'],
                room15_clock_interval=None,clock_basis='Physical passage observed from11 only; no calibrated room15 timestamp.',
                evidence=[ev('departure',26,31)])],
        reviewed_followup_observations=[
            dict(stage='staging_observation',camera=15,visible_camera_clock_interval=['08:02:52','08:03:25'],
                same_load_identity_confirmed=False,observation='Worker and partly hidden tank activity beyond fixed foreground tanks. Entry missing; no physical identity link.',
                evidence=[ev('door15',0,23)]),
            dict(stage='scale_visit',camera=11,visible_camera_clock_interval=['08:02:45','08:05:54'],
                departure_interval=['08:05:54','08:06:14'],same_load_identity_confirmed=False,numeric_weight_kg=None,
                observation='Light beige/gray blue-topped body visible on platform; moves06:04, clear06:14. This observation is explicitly unlinked to fresh blue departure.',
                evidence=[ev('after',3,32),ev('scale',0,6)])],
        missing_stages=['calibrated_room15_entry_timestamp','verified_entry_to_scale_identity','verified_scale_to_storage_identity','confirmed_storage_completion'],
        limitations=['Room15 ends08:01:40 and resumes initial08:02:52/usable08:03:03; entry from11 at01:47-52 not captured.',
            'Room15 ends08:03:25, next source metadata begins08:07:11, missing platform departure06:04. No later parked same-color body can close that identity gap.',
            'Observed scale body differs in visible body color/covering from fresh blue departure; neither equivalence nor a second production entry is inferred.'])
    replacement=dict(shared,sequence_id='20261006_empty_blue_station_replacement0801',
        review_status='accepted_negative_sequence',production_entry_count_target=0,camera=11,
        negative_class='empty_tank_internal_reposition',tracked_tank_count=1,direction='room11_waiting_area_to_station',
        visible_camera_clock_interval=['08:01:48','08:02:04'],
        observation='Different empty blue-lined body selected from waiting row, pushed to filling station. Empty bottom visible at01:56.',
        label_scope='Only this bounded empty movement, excluding fresh full departure, scrap tank and subsequent filling.',evidence=[ev('departure',27,43)])
    truck=dict(shared,sequence_id='20261006_unloaded_yellow_truck0803',
        review_status='accepted_negative_sequence',production_entry_count_target=0,
        negative_class='pallet_jack_without_tank',tracked_vehicle_count=1,tracked_tank_count=0,direction='room11_to_room15',
        camera_clock_intervals={'11':['08:03:00','08:03:10'],'15':['08:03:03','08:03:12']},
        observation='Yellow powered pallet truck crosses from11 to15 without tank cargo and turns left. Both camera views reviewed.',
        label_scope='Only unloaded vehicle passage. Earlier opposite crossing at01:30 is screening context, not a second counted negative; no whole-room absence label.',
        correspondence_basis='Vehicle shape, operator, travel direction and adjacent doorway movement; separate clock intervals retained, no scalar offset.',
        evidence=[ev('after',6,8),ev('door15',1,10)])
    merge(OUT/'reviewed_sequence_labels.json',[partial,replacement,truck],'sequence_id')
    qp=OUT/'sequence_followup_queue.json'
    save(OUT/'review_history/followup_queue_before_20261031_37.json',read(qp))
    merge(qp,[dict(candidate_id='20261006_blue_morning0801',date='20261006',split='train',reviewed_at=stamp,
        status='resolved_as_partial_missing_route',resolved_sequence_id=partial['sequence_id'],cycle_id=None,production_entry_count_target=None,
        observation='Fresh filling and11 doorway crossing01:47-52 verified. Subsequent light-body scale visit unlinked; storage not captured.',
        next_action='Do not resample missing01:40-02:52 entry or03:25-07:11 scale-to-storage route without new media.',
        evidence=[ev('departure',26,31),ev('before15',11,11),ev('door15',0,23),ev('scale',4,6)]),
        dict(candidate_id='20261006_replacement_after0801',date='20261006',split='train',reviewed_at=stamp,
            status='needs_future_departure_context',cycle_id=None,production_entry_count_target=None,
            observation='Distinct replacement at02:01, receiving cheese by02:35 and still at station through11:35.',
            next_action='Check paired15 coverage before pursuing next11 source081123-083900. Avoid assuming filename envelopes are continuous.',
            evidence=[ev('after',1,32),ev('scale',0,38)])],'candidate_id')

    registry=read(OUT/'object_review_decisions.json')
    save(OUT/'review_history/object_decisions_before_20261031_37.json',registry)
    decisions={r['id']:r for r in registry['reviews']}
    drafts={r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
    objnotes={
        '250':'Fresh station body being pulled away, partly occluded by worker/conveyor. Cover alone is not a load attribute.',
        '251':'Doorway tank including body and feet, partially overlapped by doorway hardware.',
        '252':'Distinct empty replacement body, hand overlap at back rim. Object box only.',
        '253':'Independent platform body behind doorframe. Left/top partly occluded; no same-load or contents assertion.',
    }
    for ident,note in objnotes.items():
        assert ident not in decisions
        r=drafts[ident];assert len(r['boxes_xyxy'])==1
        decisions[ident]=dict(id=ident,image_sha256=r['sha256'],
            boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',
            load_state_reviewed=False,sequence_reviewed=False,
            instance_attributes=[dict(box_index=0,truncated=False,occluded=True,load_state='unknown_not_annotated')],
            evidence=[r['source_frame'],r['frames_manifest'],'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_32.jpg'],
            note=note+' Native context and separate rendered overlay inspected. Dataset release pending.')
    registry['reviews']=list(decisions.values())
    registry.setdefault('corrections',[]).append('Batch37: four6Oct ROI images/four boxes separately overlay-reviewed. All previous approvals preserved; no inferred load labels.')
    save(OUT/'object_review_decisions.json',registry)
    inv=read(BASE/'archive_inventory.json')
    inspected={m['source']['member']:m['source_sha256'] for m in metas.values()}
    for r in inv['records']:
        if r['member'] in inspected:r.update(pixel_inspected=True,sha256=inspected[r['member']])
    assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test')
    save(BASE/'archive_inventory.json',inv)
    reviews=read(OUT/'screening_source_reviews.json')
    total=sum(r['sampled_frames_visually_reviewed'] for r in reviews)
    added=sum(len(m['samples']) for m in metas.values())
    state['last_completed'] += [
        f'Batch37 reviewed {added} sample presentations in six6Oct windows; {total} total across {len({r["source_sha256"] for r in reviews})} sources and {len(reviews)} windows. All six extractions completed; test pixels untouched.',
        '6Oct fresh blue station departure08:01:47-52 preserved as partial.15 entry missing; light-body scale observation02:45-05:54/off06:04/clear06:14 remains explicitly unlinked. Five complete cycles unchanged;32 partials.',
        'Two scoped negatives added: empty blue station replacement01:48-02:04 and unloaded yellow truck03:03-12.81 negatives total, no whole-room zero labels.',
        'Four ROI images/four boxes approved:254 candidates,196 approved,261 boxes,58 exclusions,zero drafts. Dataset not released and training not started.',
    ]
    state['priority_next']=[
        'Batch37 complete. Prioritise available complete paired routes on training days other than13Oct and17Oct validation.81 negatives already; do not repeat known gaps.',
        '6Oct08:01 partial retained:11 exit01:47-52,15 ends01:40 then02:52/03:03. Light-body scale seen02:45-05:54/off06:04/clear06:14 unlinked.15 next07:11 leaves route missing; do not resample absent media.',
        '6Oct thirdblue replacement after08:01 atstation02:01, fills02:35-11:35; next11 source081123-083900. Check15 peer coverage first.',
    ]+[p for p in state['priority_next'] if not p.startswith('Batch36') and 'next11 source075011-080216 remains uninspected' not in p]
    state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    state['scripts'] += [s for s in ['work/append_tank_roi_batch_20261031_37.py','work/record_tank_sequence_batch_20261031_37.py'] if s not in state['scripts']]
    save(OUT/'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_samples=added,total_presentations=total,
        additional_complete_cycles=0,additional_negative_sequences=2,additional_partial_sequences=1,training_started=False)))

if __name__=='__main__':main()
