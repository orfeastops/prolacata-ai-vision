"""Persist reviewed scale continuity, storage ambiguity and negative motions.

No training, inferred cross-camera identity, or held-out pixels. Re-running is
idempotent once the continuation record is saved. Previous sequence versions
are preserved before refinement.
"""
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read, save, merge, evidence

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'outputs/tank_transfer_training_v1'
OUT = BASE/'dataset_v1'
RUN = 'sequence_review_20261031_04'


def main():
    state = read(OUT/'continuation_state.json')
    if RUN in state.get('completed_curation_runs',[]):
        print('Already recorded:',RUN)
        return
    stamp = dt.datetime.now(dt.timezone.utc).isoformat()
    windows = {
        'scale11':('20261015','scale_continuity_cam11_review',69),
        'storage':('20261015','storage_settle_1116_review',26),
        'blue36':('20261006','blue_arrival_followup_0936',8),
        'blue37':('20261006','blue_scale_followup_0937',8),
        'blue38':('20261006','blue_scale_followup_0938',21),
        'blue39':('20261006','blue_scale_followup_0939',13),
        'door6':('20261006','blue_departure_door_detail',51),
    }
    paths = {k:OUT/'sequence_review'/d/n/'frames.json' for k,(d,n,_) in windows.items()}
    metas = {k:read(p) for k,p in paths.items()}
    for k,m in metas.items():
        assert len(m['samples'])==windows[k][2]
        assert m['source']['date']==windows[k][0] and m['source']['split']=='train'
        assert all((ROOT/s['image']).exists() for s in m['samples'])
    # Manually read clock anchors from the contact sheets/native pixels.
    clocks = {
        'scale11':{0:'11:13:37',2:'11:13:43',5:'11:13:52',8:'11:14:01',12:'11:14:13',15:'11:14:22',24:'11:14:49',30:'11:15:07',33:'11:15:16',39:'11:15:34',40:'11:15:37',41:'11:15:40',42:'11:15:43',43:'11:15:46',44:'11:15:49',48:'11:16:01',55:'11:16:22',56:'11:16:25',61:'11:16:40',63:'11:16:46',68:'11:17:01'},
        'storage':{0:'11:16:37',1:'11:16:48',2:'11:16:50',3:'11:16:52',4:'11:16:54',5:'11:16:56',6:'11:16:58',7:'11:17:00',8:'11:17:02',9:'11:17:04',10:'11:17:06',11:'11:17:08',12:'11:17:10',13:'11:17:12',14:'11:17:14',15:'11:17:16',16:'11:17:18',17:'11:17:20',18:'11:17:22',19:'11:17:24',20:'11:17:26',21:'11:17:28',22:'11:17:30',23:'11:17:32',24:'11:17:34',25:'11:17:36'},
        'blue36':{0:'09:36:42',1:'09:37:00',2:'09:37:02',3:'09:37:05',4:'09:37:07',5:'09:37:08',6:'09:37:10',7:'09:37:12'},
        'blue37':{0:'09:37:24',1:'09:37:32',2:'09:37:34',3:'09:37:36',4:'09:37:38',5:'09:37:40',6:'09:37:42',7:'09:37:44'},
        'blue38':{0:'09:37:56',1:'09:38:04',2:'09:38:06',3:'09:38:08',4:'09:38:10',5:'09:38:12',6:'09:38:14',7:'09:38:16',8:'09:38:18',9:'09:38:20',10:'09:38:22',11:'09:38:24',12:'09:38:26',13:'09:38:28',14:'09:38:30',15:'09:38:32',16:'09:38:34',17:'09:38:36',18:'09:38:38',19:'09:38:40',20:'09:38:42'},
        'blue39':{0:'09:38:27',1:'09:38:48',2:'09:38:50',3:'09:38:52',4:'09:38:54',5:'09:38:56',6:'09:38:58',7:'09:39:00',8:'09:39:02',9:'09:39:04',10:'09:39:06',11:'09:39:09',12:'09:39:10'},
        'door6':{0:'09:35:45',4:'09:35:53',5:'09:35:55',6:'09:35:57',7:'09:35:59',8:'09:36:01',9:'09:36:03',10:'09:36:05',11:'09:36:07',12:'09:36:09',13:'09:36:11',14:'09:36:13',18:'09:36:21',24:'09:36:33',29:'09:36:43',36:'09:36:57',40:'09:37:05',42:'09:37:09',43:'09:37:11',44:'09:37:13',45:'09:37:15',46:'09:37:17',47:'09:37:19',48:'09:37:21',49:'09:37:23',50:'09:37:25'},
    }
    notes = {
        'scale11':'Camera11 sees the same beige tank stationary on the room15 scale through the doorway,11:13:37-11:15:40. Operators handle fittings/hose; these are not entries. Manual jack engages at11:15:34-40, tank rolls off11:15:43-46 and scale is empty by11:15:49, remaining empty through11:17:01. This extends the earlier matched scale stage. The tank leaves the narrow doorway view before the next room15 source begins11:16:23; roughly37 seconds of its trajectory remain unobserved. Color alone cannot connect the later storage maneuver.',
        'storage':'First frame reads11:16:37, then jumps to11:16:48. It overlaps the earlier11:16:23-45 storage-row maneuver. Beige tank is parked at the front edge of the rear stored row; operator lowers and withdraws the manual jack11:16:54-58, leaving the beige tank stationary through11:17:36. This confirms storage placement of that later track, but not its identity with the11:15:43 scale departure across the gap. Empty jack moves away11:16:58-11:17:06. Operator next engages a different visibly empty gray tank on the left and moves it across room15 at11:17:16-36 toward the door. A doorway crossing is not yet visible. Existing row tanks and foreground inverted containers are separate stock.',
        'blue36':'A covered blue tank is already in room15 near the doorway and fixed blue bins at first visible09:36:42; next sample jumps to09:37:00. Operator maneuvers it toward the scale09:37:10-12. This window does not show its entry from room11. Shared blue color is insufficient to match the09:36:05-11 loaded departure. Fixed blue tanks and stored covered stock are separate instances.',
        'blue37':'Covered blue tank remains on the scale at right. First frame09:37:24, next09:37:32, then through09:37:44. People handle the scale-side area. No tank arrival, scale departure or storage placement is established here; do not infer kilograms.',
        'blue38':'Covered blue tank stays at the scale throughout the sampled interval. First frame09:37:56 then09:38:04. Forklift carries a separate stack of gray containers through the doorway09:38:04-12, toward left/lower room, and later returns without that stack09:38:30-42. Their contents are not verified and this movement is not a newly filled tank cycle label. Scale-side operator handles fittings around09:38:32-42.',
        'blue39':'First frame reads09:38:27 then jumps to09:38:48; do not align from filename09:38:28. Blue tank stays at scale through09:39:10. Empty forklift travels toward and through doorway back to room11 around09:38:54-09:39:02; this is not a manual pallet jack and is not included under the pallet_jack_without_tank class. Operator handles wall/hose near scale09:39:04-10. No tank storage is shown.',
        'door6':'Empty forklift passes room15-to11 at09:35:53-57. A different loaded blue tank with the white boards/top just applied at the filling station is pulled toward the door09:35:59-09:36:03, crosses09:36:05-09 and disappears behind the wall by09:36:11-13. Doorway remains clear of tanks until09:37:09. A blue/gray tank with blue fittings on top appears moving toward the scale09:37:11-21. The intervening staging and application of fittings are outside this narrow view, so this later tank is only a candidate match. Forks are withdrawn by09:37:23-25. No extra new-entry count is assigned to scale placement.',
    }
    reviews=[]
    for k,m in metas.items():
        day,name,_=windows[k]
        reviews.append(dict(review_id=day+'/'+name,reviewed_at=stamp,reviewer='assistant_visual_review',
            source_member=m['source']['member'],source_sha256=m['source_sha256'],date=day,camera=m['source']['camera'],split='train',
            frames_manifest=str(paths[k].relative_to(ROOT)),sampled_frames_visually_reviewed=len(m['samples']),reviewed_sheets=m['sheets'],
            review_scope='All chronological contact-sheet samples visually reviewed, with native frame inspection where needed; not exhaustive native-frame review.',
            visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],
                visible_camera_clock=t,clock_read_uncertainty_seconds=1,image=m['samples'][i]['image'],usable_for_clock_alignment=not(i==0 and k not in ['scale11','door6'])) for i,t in clocks[k].items()],
            observation=notes[k],accepted_complete_cycle=False,
            clock_warning='Manually read pixels only. Initial source frames can be stale; filename and PTS are not synchronization proof.'))
    merge(OUT/'screening_source_reviews.json',reviews,'review_id')

    def ev(k,a,b):
        return evidence(metas[k],a,b,paths[k])

    seqpath=OUT/'reviewed_sequence_labels.json'
    labels={r['sequence_id']:r for r in read(seqpath)}
    p15=labels['20261015_beige_filling_entry_scale_partial_1110']
    p6=labels['20261006_blue_filling_departure_partial_0936']
    history=OUT/'review_history'
    history.mkdir(exist_ok=True)
    hp=history/'sequence_labels_before_20261031_04.json'
    if not hp.exists():
        save(hp,dict(saved_at=stamp,reason='Preserve previous partial-stage evidence before refinement.',records=[copy.deepcopy(p15),copy.deepcopy(p6)]))
    p15.update(reviewed_at=stamp,
        partial_reason='Scale departure and later storage placement are individually visible, but about37 seconds of the trajectory between11:15:46 and11:16:23 remain unobserved. Same-load identity is not established across this gap.',
        observation='Previously linked filling, one entry into room15 and scale occupancy are preserved. Camera11 now confirms the scale departure11:15:43-46. A later beige track is visibly parked and its jack withdrawn11:16:54-58, but that storage is kept unlinked because its origin cannot yet be confirmed.')
    p15['evidence'].append(ev('scale11',0,44))
    sc=next(s for s in p15['stages'] if s['stage']=='scale_visit')
    sc.update(visible_camera_clock_interval=['11:11:42','11:15:46'],scale_departure_clock_interval=['11:15:40','11:15:49'],
        observation='Scale occupancy through11:15:40 and departure11:15:43-46 are visible in camera11 doorway context; empty by11:15:49. Actual weight is not read.',
        source_join_review=dict(earlier_room15_last_clock='11:13:43',camera11_first_clock='11:13:37',
            identity_evidence='Overlapping scale occupancy, same beige body and fittings, same location and continued handling.',
            limitation='Sampled visual continuity and per-camera clock intervals; no scalar clock offset certified.'))
    sc['evidence'].append(ev('scale11',0,44))
    follow=p15['unlinked_followup']
    follow.update(status='storage_placement_confirmed_for_later_track_origin_identity_unresolved',
        visible_camera_clock_interval=['11:16:23','11:17:36'],parked_and_jack_withdrawal_interval=['11:16:54','11:16:58'],
        observation='Later beige maneuver is followed to parked storage and jack withdrawal. Initial11:16:37 frame in this source overlaps11:16:37 in the earlier storage source. Beige remains parked through11:17:36. It is NOT yet linked to the earlier scale departure across the unobserved trajectory; no production cycle target is assigned.')
    follow['evidence'].append(ev('storage',0,25))
    p15['limitations'].append('Later storage stage is visually confirmed, but a complete cycle still requires origin identity; do not bridge the37-second interval by beige color alone.')

    p6.update(reviewed_at=stamp,
        partial_reason='Loaded room11 departure is clear; room15 first shows a candidate blue tank after the crossing. Its entry and staging continuity are not visible, and final storage is not reviewed.',
        next_review='Search room15 sources spanning09:36:05-11 before trying to link the scale tank. Inspect09:39-09:43 follow-ups for scale departure/storage only after identity review. Do not match blue color or derive entry clock from filename.')
    p6['evidence'].append(ev('door6',5,14))
    dep=next(s for s in p6['stages'] if s['stage']=='loaded_departure_11')
    dep.update(visible_camera_clock_interval=['09:35:55','09:36:13'],doorway_crossing_camera11_interval=['09:36:05','09:36:11'],clock_uncertainty_seconds=2,
        observation='Tank reaches doorway09:36:03, crosses09:36:05-09, disappears behind wall by09:36:11-13. This is the same tank from the reviewed camera11 filling sequence. Room15 event clock remains unverified.')
    dep['evidence'].append(ev('door6',5,14))
    p6['unlinked_followup']=dict(status='candidate_scale_track_unresolved_origin_identity',visible_camera_clock_interval=['09:36:42','09:39:10'],
        evidence=[ev('blue36',0,7),ev('blue37',0,7),ev('blue38',0,20),ev('blue39',0,12),ev('door6',43,50)],
        observation='Room15 shows an already-present covered blue tank, then movement to scale09:37:10-12 and continued scale occupancy through09:39:10. Camera11 sees a blue/gray tank with blue fittings on the scale09:37:11-25. The change from white top at departure to fittings and the staging route are not visible; origin match remains a candidate, not an accepted cycle.')
    p6['limitations']=[x for x in p6['limitations'] if not x.startswith('8-second')]
    p6['limitations'].append('Departure was refined with2-second samples. Later scale evidence still has source gaps and no certified clock offset or same-load identity.')

    common=dict(date='20261015',split='train',reviewer='assistant_visual_review',reviewed_at=stamp,
                review_status='accepted_negative_sequence',cycle_id=None,production_entry_count_target=0,dataset_release_accepted=False)
    jack=dict(common,sequence_id='20261015_empty_jack_after_storage_111658',negative_class='pallet_jack_without_tank',
        camera_track_id='cam15_empty_jack_after_beige_parking_111658',camera=15,
        visible_camera_clock_interval=['11:16:58','11:17:06'],clock_uncertainty_seconds=2,evidence=[ev('storage',4,10)],
        observation='Operator withdraws jack from the now-stationary beige tank and moves it across room15 with visible empty forks. No tank accompanies this jack segment.',
        label_scope='Only the empty-jack movement11:16:58-11:17:06. Earlier storage of the beige tank and later pickup of a gray tank are separate actions; this is not a whole-frame zero label.')
    empty=dict(common,sequence_id='20261015_gray_empty_internal_move_111716',negative_class='empty_tank_internal_reposition',
        camera_track_id='cam15_gray_empty_leftrow_to_door_111716',camera=15,tracked_object_count=1,
        visible_camera_clock_interval=['11:17:16','11:17:36'],clock_uncertainty_seconds=2,evidence=[ev('storage',11,25)],
        observation='A visibly empty gray tank with liner is picked from the existing left-side row and moved across room15 toward the shared doorway. Its bottom/interior and separate body are visible. This is an existing empty tank, not a fresh filled arrival from room11. Door crossing is not visible before the clip ends.',
        label_scope='Only the tracked empty gray internal movement. Do not label an unseen later crossing or any simultaneous stored load as negative.')
    labels.update({s['sequence_id']:s for s in [jack,empty]})
    save(seqpath,list(labels.values()))

    registry=read(OUT/'object_review_decisions.json')
    decisions={r['id']:r for r in registry['reviews']}
    draft=read(BASE/'detector_v1/visual_annotation_draft.json')['records']
    for r in draft:
        if r['id'] not in ['083','084','085','086','087']:
            continue
        attrs=[dict(box_index=j,truncated=(b[0]==0 or b[1]==0 or b[2]==r['width'] or b[3]==r['height']),
                    occluded=r['id'] in ['085','086','087'],load_state='unknown_not_annotated') for j,b in enumerate(r['boxes_xyxy'])]
        decisions[r['id']]=dict(id=r['id'],image_sha256=r['sha256'],
            boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',
            load_state_reviewed=False,sequence_reviewed=False,instance_attributes=attrs,
            evidence=[r['source_frame'],r['frames_manifest'],str((BASE/'detector_v1/sheets'/('labels_09.jpg' if r['id']=='087' else 'labels_08.jpg')).relative_to(ROOT))],
            note='Native chronology and cropped image inspected, then separate rendered overlay reviewed. Object-only labels; temporal load identity and production target are recorded separately.')
    registry['reviews']=list(decisions.values())
    registry.setdefault('corrections',[]).append('Batch04 adds five source-backed ROI images and five separately reviewed tank boxes, including a visibly empty gray tank in room15. No earlier decision overwritten.')
    save(OUT/'object_review_decisions.json',registry)
    inventory=read(BASE/'archive_inventory.json')
    inspected={m['source']['member']:m['source_sha256'] for m in metas.values()}
    for r in inventory['records']:
        if r['member'] in inspected:
            r['pixel_inspected']=True
            r['sha256']=inspected[r['member']]
    assert not any(r['pixel_inspected'] for r in inventory['records'] if r['split']=='test')
    save(BASE/'archive_inventory.json',inventory)
    state['last_completed'] += [
        'Batch04 reviewed196 additional chronological sample presentations across seven source windows;840 presentations total. All source windows extracted and inspected, with clock anchors and hashes preserved.',
        '15Oct scale departure refined to11:15:43-46 via camera11. Later beige storage confirmed with jack withdrawal11:16:54-58, but same-load identity across37-second trajectory gap remains unresolved. Partial stays partial.',
        '6Oct loaded blue room11 crossing refined to09:36:05-11. Room15 candidate scale tank reviewed through09:39:10, kept unlinked because initial entry and staging are not visible.',
        'Added two track-scoped negatives: empty manual jack after storage, and one visibly empty gray internal movement in room15. Totals:1 complete cycle,5 negatives,3 partials.',
        'Five ROI images083-087 appended and separately overlay-reviewed. Totals88 candidates,47 accepted ROI images,73 boxes. Prior sequence versions retained in review_history. Training remains unreleased.'
    ]
    state['priority_next']=[
        'Batch04 is complete; do not repeat its seven windows. Source reviews now record840 sample presentations. All extraction sessions completed.',
        '15Oct gap remaining: beige tank leaves room15 scale in camera11 view11:15:43-46, next room15 view11:16:23. Storage/jack withdrawal11:16:54-58 is confirmed for later track but origin match unresolved. Preserve partial if no additional view bridges the trajectory.',
        '6Oct room11 loaded blue crossing09:36:05-11 is clear. Room15 candidate first clock09:36:42 (next09:37:00), scale occupancy09:37:12-09:39:10. Search earlier room15 exports for actual entry/staging; inspect09:39-09:43 only for scale/storage after identity check. Do not infer from blue color.',
        '15Oct empty gray movement11:17:16-36 is accepted only as internal reposition. Next camera11 source20261015111646_20261015112403_11866435 may cover its later return, but do not create a second negative for the same physical movement without linking/deduplication.',
        'Continue unresolved camera15 ROI002/003/006/007/010/011/066/067 with native context;060-062/069/072-074 pending. Earlier exclusions and reviews remain valid.',
        'Expand other training days and same-load reentry/already-stored relocation examples.17Oct validation still lacks reviewed complete cycles;25/28 pixels remain locked. Coverage is below release requirements. No training or uploads.'
    ]
    state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    state['scripts'] += ['work/append_tank_roi_batch_20261031_04.py','work/record_tank_sequence_batch_20261031_04.py']
    save(OUT/'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_temporal_samples=196,additional_negative_sequences=2,additional_approved_images=5,training_started=False)))


if __name__=='__main__':
    main()
