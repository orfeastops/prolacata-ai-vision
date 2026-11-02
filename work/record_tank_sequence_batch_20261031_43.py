"""Record the reviewed6Oct09:03 partial transfer and track-scoped negatives."""
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read,save,merge,evidence

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/tank_transfer_training_v1'
OUT=BASE/'dataset_v1'
RUN='sequence_review_20261031_43'

def main():
    state=read(OUT/'continuation_state.json')
    if RUN in state.get('completed_curation_runs',[]):
        print('Already recorded',RUN);return
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    windows={
        'dep':('morning_departure0903_cam11',33),
        'a':('morning_entry0903a_cam15',18),
        'b':('morning_entry0903b_cam15',20),
        'scale':('morning_scale0906_cam15',8),
        'store':('morning_storage0909_cam15',8),
        'after':('morning_after_storage0910_cam15',7),
    }
    paths={k:OUT/'sequence_review/20261006'/w/'frames.json' for k,(w,n) in windows.items()}
    metas={k:read(p) for k,p in paths.items()}
    for k,m in metas.items():
        assert len(m['samples'])==windows[k][1]
        assert m['source']['date']=='20261006' and m['source']['split']=='train'
    # Every value below was read from sampled image pixels, not PTS or filenames.
    clocks={
        'dep':['09:03:18','09:03:20','09:03:22','09:03:24','09:03:26','09:03:28',
            '09:03:30','09:03:32','09:03:34','09:03:36','09:03:38','09:03:40',
            '09:03:42','09:03:44','09:03:46','09:03:48','09:03:50','09:03:52',
            '09:03:54','09:03:56','09:03:58','09:04:00','09:04:02','09:04:04',
            '09:04:06','09:04:08','09:04:10','09:04:12','09:04:14','09:04:16',
            '09:04:18','09:04:20','09:04:22'],
        'a':['09:03:31','09:03:37','09:03:38','09:03:39','09:03:40','09:03:41',
            '09:03:42','09:03:43','09:03:44','09:03:45','09:03:46','09:03:47',
            '09:03:48','09:03:49','09:03:50','09:03:51','09:03:52','09:03:53'],
        'b':['09:03:42','09:03:54','09:03:55','09:03:56','09:03:57','09:03:58',
            '09:03:59','09:04:00','09:04:01','09:04:02','09:04:03','09:04:04',
            '09:04:05','09:04:06','09:04:07','09:04:08','09:04:09','09:04:10',
            '09:04:11','09:04:12'],
        'scale':['09:05:57','09:06:11','09:06:14','09:06:15','09:06:17','09:06:19','09:06:22','09:06:24'],
        'store':['09:09:17','09:09:33','09:09:35','09:09:37','09:09:39','09:09:41','09:09:43','09:09:45'],
        'after':['09:09:57','09:10:08','09:10:10','09:10:12','09:10:14','09:10:16','09:10:18'],
    }
    notes={
        'dep':'All33 chronological samples/six sheets inspected. Fresh station load receives blocks through03:34, covered36-42; jack starts44, body moves46-50, approachesdoor52, crosses54-56 and gone58. Separate visibly empty gray replacement moves from waiting row03:54-04:10, remains empty through18, first new blocks20-22. Native03:50 and04:04 plus candidate crops and separate overlays inspected. Waiting and scrap tanks stay distinct. No count of cheese blocks inferred.',
        'a':'All18 samples/three sheets inspected. Initial03:31 followed by03:37: retain jump. Person without tank walks from doorway37-44, then handles small items by existing stored body45-53. Jack operator approachesdoor46-48; light body with blue liner and white top approaches49-50, crosses51-53 partly behind operator and fixed bins. Native03:51 inspected. Match to11 departure based on specific covered body/operator/door direction, not equality of clocks. No numeric clock offset asserted.',
        'b':'All20 samples/four sheets inspected. Initial03:42 followed by03:54; old initial image excluded from alignment. Prior source final53 and next useful54 permit one-second sampled join. Incoming light body continues54-57 then stages behind fixed bins through04:12. Native03:58 inspected. Blue body seen through doorway04:02-04 is not a verified additional entry: camera11 shows an internal empty replacement. No second production label. Route to scale after04:12 is not visible.',
        'scale':'All8 samples/two sheets inspected. Initial05:57 then06:11, with irregular pixel-clock increments preserved. Beige covered body already at right platform, stationary through24 while operator moves near console and bins. No observed arrival from03min staging, no numeric weight and no same-load identity across missing trajectory.',
        'store':'All8 samples/two sheets plus native09:37/39 inspected. Initial09:17 then09:33. Beige covered body moves left through39, then back towards rear row41-45. Origin and earlier scale identity unresolved. No final jack release in this clip. ROI271 excluded entirely: target near right crop boundary and small ambiguous background tank fragments would otherwise be omitted.',
        'after':'All7 samples/two sheets inspected. Initial09:57 already shows parked rear-row beige body; next useful10:08 has withdrawn empty manual jack. Empty jack rolls towards doorway10-18. Prior source ends09:45, leaving12 seconds before initial57 plus11 seconds to next useful10:08. Do not assign a precise release time or merge storage movement identity across these gaps. Only empty-jack trajectory is accepted negative.',
    }
    for k,m in metas.items():
        w,n=windows[k];assert len(clocks[k])==n
        merge(OUT/'screening_source_reviews.json',[dict(review_id='20261006/'+w,reviewed_at=stamp,
            reviewer='assistant_visual_review',date='20261006',camera=m['source']['camera'],split='train',
            source_member=m['source']['member'],source_sha256=m['source_sha256'],frames_manifest=str(paths[k].relative_to(ROOT)),
            sampled_frames_visually_reviewed=n,reviewed_sheets=m['sheets'],
            review_scope='All chronological sample presentations visually inspected; selected native contexts and separate object overlays. Not exhaustive native-frame review.',
            observation=notes[k],accepted_complete_cycle=False,
            clock_warning='Pixel-read camera times only; initial jumps and independent camera intervals retained. No exact synchronization inferred.',
            visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],
                relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],visible_camera_clock=t,
                clock_read_uncertainty_seconds=1,image=m['samples'][i]['image'],usable_for_clock_alignment=False)
                for i,t in enumerate(clocks[k])])],'review_id')
    # Reuse prior visual evidence without adding it to newly inspected totals.
    for k,w in [('fill','morning_after0839_cam11'),('empty','morning_departure0853_cam11'),('later11','morning_route_0904_cam11')]:
        paths[k]=OUT/'sequence_review/20261006'/w/'frames.json';metas[k]=read(paths[k])
        assert any(r['frames_manifest']==str(paths[k].relative_to(ROOT)) for r in read(OUT/'screening_source_reviews.json'))
    def ev(k,a,b):return evidence(metas[k],a,b,paths[k])
    labels=read(OUT/'reviewed_sequence_labels.json')
    save(OUT/'review_history/sequence_labels_before_20261031_43.json',labels)
    shared=dict(date='20261006',split='train',reviewer='assistant_visual_review',reviewed_at=stamp,
        dataset_release_accepted=False,cycle_id=None,camera_clock_offset_seconds=None)
    partial=dict(shared,sequence_id='20261006_beige_departure0903_partial',review_status='reviewed_partial_sequence',
        production_entry_count_target=None,camera_track_id={'11':'fresh_light_body0903','15':'incoming_light_body0903'},
        stages=[
            dict(stage='filling_observed',camera=11,visible_camera_clock_interval=['08:53:58','09:03:34'],
                initially_empty_observed=True,initial_empty_evidence_sequence_id='20261006_empty_beige_replacement0853',
                observation='Previously inspected empty light/beige body receives fresh cheese at station; same body covered before departure. Blue liner changes apparent body color; color is not an identity key.',
                evidence=[ev('empty',23,34),ev('fill',43,71),ev('dep',0,12)]),
            dict(stage='loaded_departure_11',camera=11,visible_camera_clock_interval=['09:03:44','09:03:58'],
                doorway_interval=['09:03:52','09:03:58'],
                observation='Covered freshly filled body leaves station, traverses room and doorway. Separate empty replacement remains within11.',
                evidence=[ev('dep',13,20)]),
            dict(stage='entry_15',camera=15,visible_camera_clock_interval=['09:03:51','09:03:56'],
                room11_clock_interval=['09:03:52','09:03:58'],same_load_identity_confirmed=True,
                observation='Specific covered light body with operator/jack enters behind fixed bins and stages by doorway. Camera clock intervals retained independently; body-centre crossing occluded.',
                evidence=[ev('a',13,17),ev('b',1,19),ev('dep',16,20)])],
        reviewed_followup_observations=[
            dict(stage='scale_visit',camera=15,visible_camera_clock_interval=['09:05:57','09:06:24'],
                same_load_identity_confirmed=False,numeric_weight_kg=None,
                observation='Independent covered beige body already on platform after missing staging-to-scale trajectory.',
                evidence=[ev('scale',0,7)]),
            dict(stage='scale_visit',camera=11,visible_camera_clock_interval=['09:05:27','09:08:42'],
                departure_interval=['09:08:42','09:08:58'],same_load_identity_confirmed=False,numeric_weight_kg=None,
                observation='Prior broad samples show platform occupancy then clear. Not linked to03min entry merely by appearance.',
                evidence=[ev('later11',2,16)]),
            dict(stage='storage_approach',camera=15,visible_camera_clock_interval=['09:09:33','09:09:45'],
                same_load_identity_confirmed=False,
                observation='Beige covered body rolls left and turns towards rear row. Later parked body09:57 and empty jack10:08 are separated by gaps; no certified storage completion for this origin.',
                evidence=[ev('store',1,7),ev('after',0,6)])],
        missing_stages=['verified_origin_to_scale_identity','verified_scale_to_storage_identity','storage_placement'],
        limitations=['Direct entry reviewed, but no complete production-cycle target because staging-to-scale and scale-to-storage trajectory are missing.',
            'Room15 staging ends09:04:12; next source initial05:57 then06:11. Storage source initial09:17 then09:33; previous11 platform clear08:58. These are real reviewed gaps, not inferred clock synchronization.',
            'One-second sampled join between15 entry files53-54 is retained. Exact event time and numeric weight not invented.'])
    negatives=[
        dict(shared,sequence_id='20261006_empty_gray_replacement0903',review_status='accepted_negative_sequence',camera=11,
            production_entry_count_target=0,negative_class='empty_tank_internal_reposition',tracked_tank_count=1,
            direction='room11_waiting_area_to_filling_station',visible_camera_clock_interval=['09:03:54','09:04:18'],
            observation='Visibly empty blue-lined gray tank moves from waiting row to filling station; bottom visible. First new cheese appears04:20, outside negative interval.',
            label_scope='Only empty replacement before filling. Concurrent covered outgoing load and stationary scrap tank excluded.',evidence=[ev('dep',18,30)]),
        dict(shared,sequence_id='20261006_person_without_tank0903',review_status='accepted_negative_sequence',camera=15,
            production_entry_count_target=0,negative_class='people_without_tank',tracked_people_count=1,
            visible_camera_clock_interval=['09:03:37','09:03:44'],
            observation='One person walks from doorway into aisle without a tank or jack.',
            label_scope='Only this pedestrian, not whole-room absence. Incoming production tank later in same source remains separate.',evidence=[ev('a',1,8)]),
        dict(shared,sequence_id='20261006_empty_manual_jack0910',review_status='accepted_negative_sequence',camera=15,
            production_entry_count_target=0,negative_class='pallet_jack_without_tank',
            visible_camera_clock_interval=['09:10:08','09:10:18'],
            observation='Manual jack is already empty and withdrawn, then rolls towards doorway. Its prior load identity is not inferred.',
            label_scope='Only unloaded manual jack trajectory, not parked tanks or all room movement.',evidence=[ev('after',1,6)])]
    merge(OUT/'reviewed_sequence_labels.json',[partial,*negatives],'sequence_id')
    qp=OUT/'sequence_followup_queue.json'
    save(OUT/'review_history/followup_queue_before_20261031_43.json',read(qp))
    merge(qp,[dict(candidate_id='20261006_beige0903',date='20261006',split='train',reviewed_at=stamp,
        status='resolved_as_partial_missing_scale_storage_identity',resolved_sequence_id=partial['sequence_id'],
        cycle_id=None,production_entry_count_target=None,
        observation='Fresh filling and matched15 doorway entry03:51-56 reviewed. Later scale and storage movements remain unlinked across recording gaps.',
        next_action='Do not repeat these six reviewed windows or invent full cycle. Known15 route gap04:12-05:57/06:11; scale-to-storage identity and final parking gaps remain. Revisit only with additional source coverage.',
        evidence=[ev('dep',13,20),ev('a',13,17),ev('b',1,19),ev('scale',0,7),ev('store',0,7),ev('after',0,6)])],'candidate_id')
    registry=read(OUT/'object_review_decisions.json')
    save(OUT/'review_history/object_decisions_before_20261031_43.json',registry)
    decisions={r['id']:r for r in registry['reviews']}
    drafts={r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
    for ident,occluded,note in [('269',False,'Covered outgoing body, load context kept in separate temporal label.'),
            ('270',True,'Empty internal replacement, hands and foreground table partly occlude body.')]:
        assert ident not in decisions
        r=drafts[ident];assert r['split']=='train' and len(r['boxes_xyxy'])==1
        decisions[ident]=dict(id=ident,image_sha256=r['sha256'],
            boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',
            load_state_reviewed=False,sequence_reviewed=False,
            instance_attributes=[dict(box_index=0,truncated=False,occluded=occluded,load_state='unknown_not_annotated')],
            evidence=[r['source_frame'],r['frames_manifest'],'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_35.jpg'],
            note=note+' Native context, candidate crop and independent rendered overlay inspected. ROI detection only.')
    assert drafts['271']['annotation_status']=='excluded_uncertain_instance_boundaries'
    registry['reviews']=list(decisions.values())
    registry.setdefault('corrections',[]).append('Batch43:269/270 accepted after separate overlay review.271 wholly excluded: uncertain small background tank fragments and tight target boundary. Previous decisions preserved.')
    save(OUT/'object_review_decisions.json',registry)
    inv=read(BASE/'archive_inventory.json');inspected={m['source']['member']:m['source_sha256'] for m in metas.values()}
    for r in inv['records']:
        if r['member'] in inspected:r.update(pixel_inspected=True,sha256=inspected[r['member']])
    assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test')
    save(BASE/'archive_inventory.json',inv)
    reviews=read(OUT/'screening_source_reviews.json');total=sum(r['sampled_frames_visually_reviewed'] for r in reviews)
    state['last_completed'] += [
        f'Batch43 inspected94 further training sample presentations in6 windows on6Oct;{total} total across{len({r["source_sha256"] for r in reviews})} sources/{len(reviews)} windows. Extractions completed;25/28Oct unseen.',
        '6Oct fresh09:03 departure directly matched to15 entry03:51-56 with independent camera intervals. Later scale/storage identity unverified across gaps; partials40, complete cycles5 unchanged.',
        'Three scoped negatives added: empty gray internal replacement, pedestrian, empty manual jack return.92 negatives total. No second entry inferred from body visible through doorway during replacement.',
        'Three native ROI candidates appended; two accepted after separate overlays, one excluded for uncertain edge/background.272 candidates,213 approved images,278 boxes,59 excluded,zero drafts. Training remains unreleased.',
    ]
    state['priority_next']=[
        'Batch43 complete.6Oct09:03 fresh departure is partial with directly matched15 entry03:51-56. Do not repeat reviewed09:03/06/09/10 sources: staging-to-scale and storage identity gaps remain.',
        'Prioritise next6Oct station load after09:15: fresh filling16:12-23:42 previously reviewed; next11 source092349-092437,15 next092828-092845. Inspect metadata coverage before extraction; avoid known gaps and no full-cycle inference from appearances.',
        'New03min replacement evidence shows empty gray body04:10-18, first cheese20-22. Prior09:15 partial starts04:46. Keep earlier precursor as context until short source join visually verified; do not silently overwrite old initial-contents uncertainty.',
    ]+[p for p in state['priority_next'] if not p.startswith('Batch42') and not p.startswith('6Oct secondblue after09:15:')]
    state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    state['scripts'] += ['work/append_tank_roi_batch_20261031_43.py','work/record_tank_sequence_batch_20261031_43.py']
    save(OUT/'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_samples=94,total_presentations=total,
        additional_complete_cycles=0,additional_negative_sequences=3,additional_partial_sequences=1,training_started=False)))

if __name__=='__main__':main()
