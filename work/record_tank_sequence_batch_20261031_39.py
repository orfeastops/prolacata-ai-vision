"""Record directly matched6Oct entry; keep absent downstream stages unresolved."""
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read, save, merge, evidence

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/tank_transfer_training_v1'
OUT=BASE/'dataset_v1'
RUN='sequence_review_20261031_39'

def main():
    state=read(OUT/'continuation_state.json')
    if RUN in state.get('completed_curation_runs',[]):
        print('Already recorded',RUN);return
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    windows={'departure':('morning_departure_0826_cam11',60),'entry':('morning_entry_0826_cam15',23)}
    paths={k:OUT/'sequence_review/20261006'/w/'frames.json' for k,(w,_) in windows.items()}
    metas={k:read(p) for k,p in paths.items()}
    for k,m in metas.items():
        assert m['source']['date']=='20261006' and m['source']['split']=='train'
        assert len(m['samples'])==windows[k][1]
    clocks={
        'departure':{0:'08:26:07',2:'08:26:09',9:'08:26:16',10:'08:26:17',11:'08:26:18',12:'08:26:19',
            13:'08:26:20',14:'08:26:21',15:'08:26:22',16:'08:26:23',17:'08:26:24',18:'08:26:25',
            19:'08:26:26',20:'08:26:27',21:'08:26:28',22:'08:26:29',23:'08:26:30',24:'08:26:31',
            25:'08:26:32',26:'08:26:33',27:'08:26:34',28:'08:26:35',29:'08:26:36',30:'08:26:37',
            31:'08:26:38',32:'08:26:39',33:'08:26:40',34:'08:26:41',35:'08:26:42',36:'08:26:43',
            37:'08:26:44',38:'08:26:45',45:'08:26:52',50:'08:26:57',53:'08:27:00',59:'08:27:06'},
        'entry':{0:'08:26:04',1:'08:26:14',2:'08:26:15',3:'08:26:16',4:'08:26:17',5:'08:26:18',
            6:'08:26:19',7:'08:26:20',8:'08:26:21',9:'08:26:22',10:'08:26:23',11:'08:26:24',
            12:'08:26:25',13:'08:26:26',14:'08:26:27',15:'08:26:28',16:'08:26:29',17:'08:26:30',
            18:'08:26:31',19:'08:26:32',20:'08:26:33',21:'08:26:34',22:'08:26:35'},
    }
    notes={
        'departure':'All60 chronological one-second samples/10 sheets inspected. Clock26:07-27:06. Station body already covered at07 after filling in previously reviewed broad window. Jack begins pulling around17-18, body clearstation19, crossesroom20-24, reachesdoor25, crosses26-30 and absent31. A different blue-lined empty replacement is taken from waitingrow26-30, pushed31-36 and stationary37-39. Cheese pickup40 and placement41 onward excluded from negative. Native26:22,25,34 inspected. Another person walks15-to11 at32-33 without cargo; retained as context, not another negative count. Fixed scrap tank remains distinct.',
        'entry':'All23 chronological samples/four sheets inspected. Initial26:04 then14-35. Door clear14-19, jack operator visible20-24. Same blue-lined body with white panels arrives26-30, turns/stages31-35 behind fixed foreground bins. Native26:27 and35 inspected. Matching is based on visible doorway traversal, distinctive cover/body and operator/jack direction in both views; not filenames alone. Foreground inventory occludes lower body. Other person crosses opposite direction32-33. No scale placement or storage completion in this window. No precise camera offset fitted.',
    }
    for k,m in metas.items():
        merge(OUT/'screening_source_reviews.json',[dict(
            review_id='20261006/'+windows[k][0],reviewed_at=stamp,reviewer='assistant_visual_review',
            date='20261006',camera=m['source']['camera'],split='train',source_member=m['source']['member'],
            source_sha256=m['source_sha256'],frames_manifest=str(paths[k].relative_to(ROOT)),
            sampled_frames_visually_reviewed=len(m['samples']),reviewed_sheets=m['sheets'],
            review_scope='All chronological sample sheets inspected; selected native images and three separate rendered object overlays reviewed. Not exhaustive native-frame viewing.',
            observation=notes[k],accepted_complete_cycle=False,
            clock_warning='Pixel clocks retained independently. Initial stale frame and PTS/filenames do not calibrate camera clocks.',
            visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],
                relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],visible_camera_clock=t,
                clock_read_uncertainty_seconds=1,image=m['samples'][i]['image'],usable_for_clock_alignment=False)
                for i,t in clocks[k].items()])],'review_id')

    # Reuse already-reviewed filling/scale observations without increasing screened-frame totals.
    paths['broad']=OUT/'sequence_review/20261006/morning_route_0811_cam11/frames.json'
    metas['broad']=read(paths['broad'])
    assert any(r['frames_manifest']==str(paths['broad'].relative_to(ROOT)) for r in read(OUT/'screening_source_reviews.json'))
    def ev(k,a,b):return evidence(metas[k],a,b,paths[k])
    save(OUT/'review_history/sequence_labels_before_20261031_39.json',read(OUT/'reviewed_sequence_labels.json'))
    shared=dict(date='20261006',split='train',reviewer='assistant_visual_review',reviewed_at=stamp,
        dataset_release_accepted=False,cycle_id=None,camera_clock_offset_seconds=None)
    partial=dict(shared,sequence_id='20261006_blue_station_departure0826_partial',
        review_status='reviewed_partial_sequence',production_entry_count_target=None,
        observed_loaded_entry_count=1,observed_entry_count_scope='One directly matched physical entry; full filling-to-storage cycle target remains unreleased.',
        camera_track_id={'11':'blue_station_load0826','15':'blue_arrival0826'},
        stages=[
            dict(stage='filling_observed',camera=11,visible_camera_clock_interval=['08:18:22','08:26:02'],
                initial_contents_unknown=False,initial_empty_evidence_sequence_id='20261006_empty_blue_station_replacement0817',
                observation='Previously reviewed distinct empty replacement stays at station and receives cheese. No block count inferred.',
                evidence=[ev('broad',20,43)]),
            dict(stage='loaded_departure_11',camera=11,visible_camera_clock_interval=['08:26:17','08:26:31'],
                observation='Same fresh-filled body covered with white panels, then pulled through doorway.',evidence=[ev('departure',10,24)]),
            dict(stage='entry_15',camera=15,visible_camera_clock_interval=['08:26:26','08:26:32'],
                room11_clock_interval=['08:26:25','08:26:31'],clock_uncertainty_seconds=1,
                identity_confirmed=True,correspondence_basis='Paired visible doorway passage of blue-lined body/white panels, same jack operator, outgoing direction in11 and incoming direction in15. Separate pixel-clock intervals retained.',
                evidence=[ev('departure',18,24),ev('entry',12,19)]),
            dict(stage='staging_observation',camera=15,visible_camera_clock_interval=['08:26:31','08:26:35'],
                same_load_identity_confirmed=True,observation='Arrival body turns behind fixed foreground bins; lower body occluded.',evidence=[ev('entry',18,22)])],
        reviewed_followup_observations=[
            dict(stage='scale_visit',camera=11,visible_camera_clock_interval=['08:27:42','08:30:42'],
                departure_interval=['08:30:42','08:31:22'],same_load_identity_confirmed=False,numeric_weight_kg=None,
                observation='Covered body seen on platform, moving31:02 and clear31:22.26:35-to27:40 room15 source gap leaves staging-to-scale route unverified.',
                evidence=[ev('broad',48,59)])],
        missing_stages=['verified_staging_to_scale_identity','verified_scale_to_storage_identity','confirmed_storage_completion'],
        limitations=['Room15 source after26:35 starts27:40 by filename; no visual inspection of its pixels yet and no staged-to-platform identity inferred.',
            'Camera11 platform departure at31:02 is followed by15 source metadata31:52. Missing trajectory cannot be repaired by a same-colored later tank.',
            'Partial record has one observed loaded entry, but no eligible complete-cycle target or production/day total.'])
    replacement=dict(shared,sequence_id='20261006_empty_blue_station_replacement0826',
        review_status='accepted_negative_sequence',production_entry_count_target=0,camera=11,
        negative_class='empty_tank_internal_reposition',tracked_tank_count=1,direction='room11_waiting_area_to_station',
        visible_camera_clock_interval=['08:26:26','08:26:39'],
        observation='Different empty blue-lined body moves from waiting row to station. Native26:34 shows empty bottom.',
        label_scope='Only empty replacement movement; excludes simultaneous filled doorway crossing, fixed scrap tank and cheese placement after26:40.',
        evidence=[ev('departure',19,32)])
    merge(OUT/'reviewed_sequence_labels.json',[partial,replacement],'sequence_id')
    qp=OUT/'sequence_followup_queue.json'
    save(OUT/'review_history/followup_queue_before_20261031_39.json',read(qp))
    merge(qp,[dict(candidate_id='20261006_blue_morning0826',date='20261006',split='train',reviewed_at=stamp,
        status='resolved_as_partial_downstream_route_missing',resolved_sequence_id=partial['sequence_id'],
        cycle_id=None,production_entry_count_target=None,observed_loaded_entry_count=1,
        observation='Fresh filling and11 departure matched to15 entry26:26-32; downstream staging/scale/storage chain not certified.',
        next_action='Do not repeat reviewed crossing. Known26:35-to27:40 staging gap and31:02-to31:52 storage gap remain; preserve partial unless new media bridges them.',
        evidence=[ev('departure',18,24),ev('entry',12,22),ev('broad',48,59)]),
        dict(candidate_id='20261006_replacement_after0826',date='20261006',split='train',reviewed_at=stamp,
            status='needs_future_departure_context',cycle_id=None,production_entry_count_target=None,
            observation='Distinct empty replacement at26:37-39 receives cheese from26:41 and remains filling through38:42 in already-reviewed broad window.',
            next_action='Check later paired coverage before extracting. No extra entry assigned to filling or initial stock.',
            evidence=[ev('departure',30,38),ev('broad',46,81)])],'candidate_id')

    registry=read(OUT/'object_review_decisions.json')
    save(OUT/'review_history/object_decisions_before_20261031_39.json',registry)
    decisions={r['id']:r for r in registry['reviews']}
    drafts={r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
    objnotes={
        '258':('Covered station departure in clear aisle; full body and feet.',False),
        '259':('Doorway tank, slight overlap by door hardware at right.',True),
        '260':('Different empty replacement with worker hands on back rim.',True),
    }
    for ident,(note,occluded) in objnotes.items():
        assert ident not in decisions
        r=drafts[ident];assert len(r['boxes_xyxy'])==1
        decisions[ident]=dict(id=ident,image_sha256=r['sha256'],
            boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',
            load_state_reviewed=False,sequence_reviewed=False,
            instance_attributes=[dict(box_index=0,truncated=False,occluded=occluded,load_state='unknown_not_annotated')],
            evidence=[r['source_frame'],r['frames_manifest'],'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_33.jpg'],
            note=note+' Native context and separate rendered overlay inspected. Object only; dataset release pending.')
    registry['reviews']=list(decisions.values())
    registry.setdefault('corrections',[]).append('Batch39: three6Oct ROI images/three boxes separately overlay-reviewed. Prior decisions preserved.')
    save(OUT/'object_review_decisions.json',registry)
    inv=read(BASE/'archive_inventory.json')
    inspected={m['source']['member']:m['source_sha256'] for m in metas.values()}
    for r in inv['records']:
        if r['member'] in inspected:r.update(pixel_inspected=True,sha256=inspected[r['member']])
    assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test')
    save(BASE/'archive_inventory.json',inv)
    reviews=read(OUT/'screening_source_reviews.json')
    total=sum(r['sampled_frames_visually_reviewed'] for r in reviews)
    added=sum(n for _,n in windows.values())
    state['last_completed'] += [
        f'Batch39 reviewed {added} new sample presentations in two6Oct windows; {total} total across {len({r["source_sha256"] for r in reviews})} sources and {len(reviews)} windows. Reused filling/scale context not counted twice. All extraction completed; test pixels untouched.',
        '6Oct08:26 fresh departure matched directly to15 entry26:26-32, with paired pixel-clock intervals retained. One observed entry, but downstream staging/scale/storage gaps keep sequence partial. Five full cycles unchanged;34 partials.',
        'One scoped negative added: distinct empty blue replacement26:26-39.83 negatives total. Initial storage and person-only crossing remain context, not extra production.',
        'Three ROI images/three boxes approved:261 candidates,203 approved,268 boxes,58 exclusions,zero drafts. Training remains unreleased.',
    ]
    state['priority_next']=[
        'Batch39 complete. Prioritise complete paired routes outside13Oct and17Oct validation.83 negatives already; avoid repeating known missing routes.',
        '6Oct08:26 partial now has directly matched15 entry26:26-32.26:35-to27:40 staging and31:02-to31:52 storage gaps remain. Do not repeat dense entry or infer a full cycle.',
        '6Oct replacement after08:26: empty at26:37-39, filling26:41-38:42. Later departure unreviewed. Check peer15 coverage before new extraction; broad0811-0839 already reviewed.',
    ]+[p for p in state['priority_next'] if not p.startswith('Batch38') and not p.startswith('6Oct08:26 candidate')]
    state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    state['scripts'] += [s for s in ['work/append_tank_roi_batch_20261031_39.py','work/record_tank_sequence_batch_20261031_39.py'] if s not in state['scripts']]
    save(OUT/'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_samples=added,total_presentations=total,
        additional_complete_cycles=0,additional_negative_sequences=1,additional_partial_sequences=1,training_started=False)))

if __name__=='__main__':main()
