"""Persist source-backed 6/15 October reviews, with incomplete paths isolated."""
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read, save, merge, evidence

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'outputs/tank_transfer_training_v1'
OUT = BASE / 'dataset_v1'
RUN = 'sequence_review_20261031_03'


def main():
    state = read(OUT / 'continuation_state.json')
    if RUN in state.get('completed_curation_runs', []):
        print('Already recorded:', RUN)
        return
    stamp = dt.datetime.now(dt.timezone.utc).isoformat()
    windows = {
        'arrival': ('20261015', 'before_scale_1110_review', 23),
        'scale': ('20261015', 'before_scale_1111_review', 15),
        'origin': ('20261015', 'filling_departure_1110_review', 76),
        'empty': ('20261015', 'empty_return_1111_review', 23),
        'blue': ('20261006', 'filling_screen_0933_review', 46),
        'later': ('20261015', 'after_scale_gap_1116_review', 8),
    }
    paths = {k: OUT / 'sequence_review' / day / name / 'frames.json' for k,(day,name,_) in windows.items()}
    metas = {k: read(p) for k,p in paths.items()}
    for k,m in metas.items():
        assert len(m['samples']) == windows[k][2]
        assert m['source']['date'] == windows[k][0] and m['source']['split'] == 'train'
        assert all((ROOT/s['image']).exists() for s in m['samples'])
    # Explicit anchors read from the displayed image pixels. No filename+PTS conversion.
    clocks = {
        'arrival': {0:'11:10:21',1:'11:10:36',6:'11:10:46',7:'11:10:48',8:'11:10:50',9:'11:10:52',10:'11:10:54',11:'11:10:56',12:'11:10:58',15:'11:11:04',17:'11:11:08',22:'11:11:18'},
        'scale': {0:'11:11:20',1:'11:11:28',6:'11:11:38',8:'11:11:42',10:'11:11:46',11:'11:11:48',12:'11:11:50',13:'11:11:52',14:'11:11:54'},
        'origin': {0:'11:08:48',6:'11:09:00',7:'11:09:02',8:'11:09:04',12:'11:09:12',18:'11:09:24',24:'11:09:36',30:'11:09:48',36:'11:10:00',42:'11:10:12',48:'11:10:24',52:'11:10:32',53:'11:10:34',54:'11:10:36',59:'11:10:46',60:'11:10:48',61:'11:10:50',62:'11:10:52',63:'11:10:54',64:'11:10:56',65:'11:10:58',75:'11:11:18'},
        'empty': {0:'11:11:21',1:'11:11:39',3:'11:11:43',5:'11:11:47',6:'11:11:49',7:'11:11:51',8:'11:11:53',9:'11:11:55',10:'11:11:57',13:'11:12:03',14:'11:12:05',18:'11:12:13',22:'11:12:21'},
        'blue': {0:'09:33:52',1:'09:34:03',8:'09:34:59',9:'09:35:07',14:'09:35:47',15:'09:35:55',16:'09:36:03',17:'09:36:11',18:'09:36:19',19:'09:36:27',24:'09:37:07',25:'09:37:15',30:'09:37:55',31:'09:38:03',38:'09:38:59',42:'09:39:31',45:'09:39:55'},
        'later': {0:'11:16:23',1:'11:16:33',2:'11:16:35',3:'11:16:37',4:'11:16:39',5:'11:16:41',6:'11:16:43',7:'11:16:45'},
    }
    notes = {
        'arrival': 'Scale starts empty. Operator and manual jack approach from room11; beige white-topped tank passes the shared doorway and is partly hidden by the fixed blue bins at11:10:52-58, then waits near the door. Two different empty gray tanks arrive side by side from the left at11:11:04-08, moving toward room11. Do not merge them with the beige load.',
        'scale': 'Beige white-topped tank is moved right onto the scale during11:11:42-48 and stays there through11:11:54. Two empty gray tanks pass toward room11 around11:11:48-54; their visible empty interiors and subsequent camera11 separation establish two physical tanks, one paired return movement. No kilograms are read.',
        'origin': 'Workers repeatedly place cheese blocks into a beige tank at the filling station,11:08:48-11:10:32. White cover is applied by11:10:34-36. Same tank is pulled away11:10:46-48, crosses the doorway11:10:52-56 and is gone by11:10:58. Fixed scrap tank remains at the conveyor. An unloaded manual jack enters11:09:02-04; people also cross without a tank. Those movements are not production entries.',
        'empty': 'Two distinct gray tanks with empty interiors return from room15 through the door at11:11:49-53. One is moved to the filling station by11:12:03 and cheese placements begin by11:12:05-13. The other moves left. The beige tank already on the scale remains visible through the doorway; it is a separate track. The first frame reads11:11:21, then the next sampled frame jumps to11:11:39.',
        'blue': 'Blue tank at the filling station visibly contains cheese blocks and receives placements. It is covered by09:35:55, leaves the station, reaches the doorway09:36:03 and has left room11 by09:36:11. A separate empty blue replacement tank moves to the station09:36:11-19 and is subsequently filled. Forklift-only movement and forklift-carried stacks of gray containers occur separately; their load contents and cross-camera identity are not asserted. No room15 entry or storage is verified by this window.',
        'later': 'A covered beige tank is maneuvered in front of the rear storage row at11:16:33-45. At the final sample it is being placed along the front edge; final jack withdrawal is not yet visible. Scale departure and identity continuity from the11:13:43 scale observation are missing from the inspected windows. This later maneuver is not accepted as either a new production entry or a confirmed same-load storage/relocation event. First frame reads11:16:23, next sampled frame11:16:33.',
    }
    reviews = []
    for k,m in metas.items():
        day,name,_ = windows[k]
        reviews.append(dict(review_id=day+'/'+name, reviewed_at=stamp,
            reviewer='assistant_visual_review', source_member=m['source']['member'],
            source_sha256=m['source_sha256'], date=day, camera=m['source']['camera'], split='train',
            frames_manifest=str(paths[k].relative_to(ROOT)), sampled_frames_visually_reviewed=len(m['samples']),
            reviewed_sheets=m['sheets'],
            review_scope='All chronological contact-sheet samples viewed; this is sampled visual review, not exhaustive native-frame review.',
            visible_clock_anchors=[dict(sample_index=i, source_pts_seconds=m['samples'][i]['source_pts_seconds'],
                relative_pts_seconds=m['samples'][i]['relative_pts_seconds'], visible_camera_clock=t,
                clock_read_uncertainty_seconds=1, image=m['samples'][i]['image'],
                usable_for_clock_alignment=not(i==0 and k!='origin')) for i,t in clocks[k].items()],
            observation=notes[k], accepted_complete_cycle=False,
            clock_warning='Keep per-camera intervals; initial export frames may be stale. PTS and filenames are not clock calibration.'))
    merge(OUT/'screening_source_reviews.json',reviews,'review_id')

    def ev(k,a,b):
        return evidence(metas[k],a,b,paths[k])

    dwellp = OUT/'sequence_review/20261015/frames.json'
    dwellm = read(dwellp)
    dwell = evidence(dwellm,1,22,dwellp)
    partial15 = dict(sequence_id='20261015_beige_filling_entry_scale_partial_1110',date='20261015',split='train',
        reviewer='assistant_visual_review',reviewed_at=stamp,review_status='reviewed_partial_sequence',
        cycle_id=None,candidate_load_id='20261015_beige_1110_pending_storage',
        camera_track_id={'11':'beige_from_filling_111046','15':'beige_door_to_scale_111052'},
        production_entry_count_target=None,observed_loaded_entry_count=1,dataset_release_accepted=False,
        entry_camera=15,entry_clock_interval=['11:10:52','11:10:58'],camera_clock_offset_seconds=None,
        cross_camera_identity='visually_corresponding_departure_arrival_and_scale_path_with_door_occlusion',
        partial_reason='Scale-to-storage continuity and final parked/jack-withdrawn stage are unverified. Do not promote this to a complete cycle.',
        observation='Cheese filling, covered beige departure, one corresponding arrival in room15 and scale visit are source-backed. A later beige storage-row maneuver is only a candidate continuation because the scale departure is missing.',
        evidence=[ev('origin',0,65),ev('arrival',9,22),ev('scale',1,14),dwell],
        stages=[
            dict(stage='filling_observed',visible_camera_clock_interval=['11:08:48','11:10:32'],clock_uncertainty_seconds=2,evidence=[ev('origin',0,52)],content_evidence='Individual cheese blocks and repeated placement into the same beige tank are visible; initial contents and total quantity unknown.'),
            dict(stage='loaded_departure_11',visible_camera_clock_interval=['11:10:46','11:10:58'],doorway_crossing_camera11_interval=['11:10:52','11:10:56'],clock_uncertainty_seconds=2,evidence=[ev('origin',59,65)]),
            dict(stage='entry_15',visible_camera_clock_interval=['11:10:52','11:10:58'],clock_uncertainty_seconds=3,timestamp_precision='interval_only',evidence=[ev('arrival',9,12),ev('origin',62,65)],correspondence_basis='Shared doorway, beige body and white top, same operator and jack, compatible trajectory and neighboring visible clock intervals. Numeric clock offset remains uncertified.'),
            dict(stage='scale_visit',visible_camera_clock_interval=['11:11:42','11:13:43'],clock_uncertainty_seconds=2,evidence=[ev('scale',8,14),dwell,ev('empty',3,10)],observation='Occupancy and handling on scale are visible; weight and a continuous recording across export joins are not established.'),
        ],
        unlinked_followup=dict(status='candidate_only_unresolved_identity_and_recording_gap',visible_camera_clock_interval=['11:16:23','11:16:45'],evidence=[ev('later',0,7)],observation=notes['later']),
        limitations=['Existing stock and the two empty returns are separate tracks.',
            'The incoming gray empty replacement is a later filling cycle, not a second count for the beige load.',
            'A filename gap between room15 exports is a search clue, not proof of missing real-world action; inspect overlapping sources before declaring irrecoverable loss.',
            'No kg, starting fill quantity, exact synchronized timestamp or completed storage cycle is inferred.'])
    negative = dict(sequence_id='20261015_two_empty_gray_return_1111',date='20261015',split='train',
        reviewer='assistant_visual_review',reviewed_at=stamp,review_status='accepted_negative_sequence',
        negative_class='empty_crossing',cycle_id=None,production_entry_count_target=0,dataset_release_accepted=False,
        tracked_object_count=2,camera_track_ids=['gray_empty_return_A_1111','gray_empty_return_B_1111'],
        direction='room15_to_room11',camera_clock_offset_seconds=None,
        visible_camera_clock_intervals={'15':['11:11:48','11:11:54'],'11':['11:11:47','11:11:55']},
        evidence=[ev('arrival',15,22),ev('scale',10,14),ev('empty',5,13)],
        observation='Two gray tanks with visible empty interiors move side by side from room15 into room11 and are then separated. One reaches the filling station; the other moves left. This is one reviewed paired return sequence containing two physical tanks, zero new loaded room15 entries.',
        label_scope='Only the two empty gray return tracks. The beige tank on the room15 scale and subsequent cheese placement into one replacement tank are separate activities, not room-wide negative labels.')
    partial6 = dict(sequence_id='20261006_blue_filling_departure_partial_0936',date='20261006',split='train',
        reviewer='assistant_visual_review',reviewed_at=stamp,review_status='reviewed_partial_sequence',
        cycle_id=None,camera_track_id='cam11_blue_cheese_departure_093603',production_entry_count_target=None,dataset_release_accepted=False,
        observed_loaded_departure_count=1,partial_reason='Room15 entry, scale and storage for this load have not been matched. Do not assign an entry time from the camera11 source filename.',
        observation=notes['blue'],evidence=[ev('blue',0,19)],
        stages=[
            dict(stage='filling_observed',visible_camera_clock_interval=['09:33:52','09:35:47'],clock_uncertainty_seconds=8,evidence=[ev('blue',0,14)],content_evidence='Blue tank with visible cheese blocks and placements; excludes the later empty blue replacement.'),
            dict(stage='loaded_departure_11',visible_camera_clock_interval=['09:35:55','09:36:11'],clock_uncertainty_seconds=8,evidence=[ev('blue',15,17)],observation='Covered blue tank moves from filling station to door; tank is at doorway in09:36:03 sample and absent by09:36:11. Dense review still needed for exact crossing bounds.'),
        ],
        next_review='Inspect room15 sources ending09:35:55 and starting09:36:43,09:37:24,09:37:56 plus any overlapping export. Do not match on blue color alone.',
        limitations=['8-second screening cadence only bounds the movement; it is not exact crossing timing.','Forklift stacks of other containers remain unknown load/identity, not assumed empty.','New empty blue replacement and its later filling are separate from this departure.'])
    merge(OUT/'reviewed_sequence_labels.json',[partial15,negative,partial6],'sequence_id')

    # Separate ROI overlay review: preserve all older image decisions and hashes.
    registry = read(OUT/'object_review_decisions.json')
    decisions = {r['id']:r for r in registry['reviews']}
    draft = read(BASE/'detector_v1/visual_annotation_draft.json')['records']
    for r in draft:
        if r['id'] not in ['075','076','077','078','080','081']:
            continue
        assert r['id'] not in decisions
        attrs=[]
        for j,b in enumerate(r['boxes_xyxy']):
            attrs.append(dict(box_index=j,truncated=(b[0]==0 or b[1]==0 or b[2]==r['width'] or b[3]==r['height']),
                occluded=(r['id'] in ['077','078','080','081']),load_state='unknown_not_annotated'))
        decisions[r['id']]=dict(id=r['id'],image_sha256=r['sha256'],
            boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',
            load_state_reviewed=False,sequence_reviewed=False,instance_attributes=attrs,
            evidence=[r['source_frame'],r['frames_manifest'],str((BASE/'detector_v1/sheets'/('labels_07.jpg' if int(r['id'])<80 else 'labels_08.jpg')).relative_to(ROOT))],
            note='Native source chronology, ROI crop and rendered overlay separately inspected. Includes the beige scale tank visible through the doorway in080/081. Object boxes alone do not label a new production entry.')
    registry['reviews']=list(decisions.values())
    registry.setdefault('corrections',[]).append('Batch03: eight new source-backed camera11 crops; six approved with ten boxes.079/082 excluded as whole images because occluded instance boundaries are uncertain. Two empty return tanks are separate physical tracks.')
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
        'Batch03 reviewed191 additional sample presentations in six source windows on6/15Oct, totaling644 presentations across12 source videos and17 windows. No test pixels inspected.',
        '15Oct beige filling, departure, room15 entry11:10:52-58 and scale dwell are linked as a PARTIAL cycle. Later beige storage-row movement11:16:23-45 is unlinked pending gap/identity review; not accepted as a complete cycle.',
        '15Oct two visibly empty gray tanks return together from15 to11: one accepted negative sequence, two physical tank tracks, zero production entries. Total accepted negative sequences3.',
        '6Oct blue cheese-tank filling and loaded departure around09:36 retained as partial; room15 counterpart not inferred. Total reviewed partial sequences3.',
        'Eight new ROI images appended075-082 without resetting existing candidates. Six passed separate overlay review; two uncertain frames excluded. Total83 candidates,42 approved ROI images,68 accepted boxes. Training remains unreleased.'
    ]
    state['priority_next']=[
        'Do not repeat completed batch03 windows. Read source reviews and sequence labels:1 complete13Oct cycle,3 negatives,3 partials.191 new samples and six approved ROI images are durable.',
        'Resolve15Oct scale-to-storage continuity: initial15 source ends visibly11:13:43; next inspected source begins11:16:23 then jumps to11:16:33. Inspect overlapping camera11 source20261015111121_20261015111703_11865461 at laterPTS and camera15 files around11:13-11:17. Check final jack withdrawal in20261015111637_20261015111737_11952771. Do not match the beige tank solely by color.',
        '6Oct loaded blue departure: visually reviewed09:35:55-09:36:11 in cam11 source20261006093352_20261006095629_10668503. Inspect room15 exports ending09:35:55 and starting09:36:43/09:37:24/09:37:56 and overlaps; keep partial if entry or identity cannot be established.',
        'Continue unresolved camera15 ROI cases002/003/006/007/010/011 and066/067 with native context;060-062/069/072-074 pending.079/082 deliberately excluded for heavy occlusion.',
        'Expand other training dates and negative classes same-load reentry and already-stored relocation.17Oct validation lacks reviewed complete cycles.25/28 stay locked/unopened.',
        'Coverage is far below release targets. Continue dataset curation only; no training, source edits, uploads or publishing.'
    ]
    state['updated_at']=stamp
    state['active_extraction_processes']=[]
    state['dataset_ready']=False
    state.setdefault('completed_curation_runs',[]).append(RUN)
    state['scripts']+=['work/append_tank_roi_batch_20261031_03.py','work/record_tank_sequence_batch_20261031_03.py']
    save(OUT/'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_temporal_samples=191,additional_approved_images=6,training_started=False)))


if __name__=='__main__':
    main()
