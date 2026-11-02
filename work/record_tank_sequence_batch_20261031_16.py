"""Preserve the visually inspected 6 October 11:17-11:30 evidence.

Two fresh departures remain partial: direct room15 entries are not observed.
No missing link, clock offset, contents or new production count is invented.
"""
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read, save, merge, evidence

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'outputs/tank_transfer_training_v1'
OUT = BASE / 'dataset_v1'
RUN = 'sequence_review_20261031_16'


def main():
    state = read(OUT / 'continuation_state.json')
    if RUN in state.get('completed_curation_runs', []):
        print('Already recorded', RUN)
        return
    stamp = dt.datetime.now(dt.timezone.utc).isoformat()
    windows = {
        'origin_beige': ('beige_origin_1117_cam11', 40),
        'departure_beige': ('beige_departure_1120_cam11', 50),
        'origin_blue': ('origin_1123_cam11', 45),
        'people18': ('beige_entry_1118_cam15', 19),
        'people19': ('beige_scale_1119_cam15', 12),
        'scale21': ('beige_scale_1121_cam15', 15),
        'storage26': ('scale_context_1125_cam15', 39),
        'stack27': ('storage_context_1127_cam15', 28),
        'scale30': ('blue_entry_1129_cam15', 10),
    }
    paths = {k: OUT / 'sequence_review/20261006' / v[0] / 'frames.json' for k, v in windows.items()}
    metas = {k: read(p) for k, p in paths.items()}
    for k, m in metas.items():
        assert len(m['samples']) == windows[k][1]
        assert m['source']['date'] == '20261006' and m['source']['split'] == 'train'
        assert all((ROOT / s['image']).exists() for s in m['samples'])
    # Manually read visible clock pixels. These are not filename/PTS conversions.
    clocks = {
        'origin_beige': {0:'11:17:20',5:'11:17:40',11:'11:18:04',12:'11:18:08',14:'11:18:16',17:'11:18:28',23:'11:18:52',24:'11:18:56',25:'11:19:00',30:'11:19:20',36:'11:19:44',39:'11:19:56'},
        'departure_beige': {0:'11:20:00',5:'11:20:20',8:'11:20:32',9:'11:20:36',10:'11:20:40',11:'11:20:44',12:'11:20:48',13:'11:20:52',14:'11:20:56',15:'11:21:00',17:'11:21:08',28:'11:21:52',29:'11:21:56',30:'11:22:00',35:'11:22:20',37:'11:22:29',43:'11:22:53',45:'11:23:01',49:'11:23:16'},
        'origin_blue': {0:'11:23:20',5:'11:24:00',10:'11:24:40',15:'11:25:20',16:'11:25:28',17:'11:25:36',20:'11:26:00',27:'11:26:56',28:'11:27:04',30:'11:27:20',35:'11:28:00',39:'11:28:32',40:'11:28:40',41:'11:28:48',42:'11:28:56',43:'11:29:04',44:'11:29:12'},
        'people18': {0:'11:18:40',1:'11:18:44',2:'11:18:46',5:'11:18:52',8:'11:18:58',9:'11:19:00',12:'11:19:06',16:'11:19:14',18:'11:19:18'},
        'people19': {0:'11:19:29',1:'11:19:36',5:'11:19:44',8:'11:19:50',11:'11:19:56'},
        'scale21': {0:'11:21:41',1:'11:21:43',5:'11:21:47',10:'11:21:52',11:'11:21:53',12:'11:21:54',13:'11:21:55',14:'11:21:56'},
        'storage26': {0:'11:25:30',1:'11:25:35',5:'11:25:47',10:'11:26:02',13:'11:26:11',14:'11:26:14',15:'11:26:17',16:'11:26:20',18:'11:26:26',19:'11:26:29',20:'11:26:32',21:'11:26:35',22:'11:26:38',23:'11:26:41',24:'11:26:44',25:'11:26:47',28:'11:26:56',30:'11:27:02',38:'11:27:26'},
        'stack27': {0:'11:27:18',1:'11:27:35',5:'11:27:47',8:'11:27:56',10:'11:28:02',11:'11:28:05',12:'11:28:08',13:'11:28:11',16:'11:28:20',22:'11:28:38',24:'11:28:44',25:'11:28:48',27:'11:28:53'},
        'scale30': {0:'11:29:40',1:'11:30:01',2:'11:30:03',3:'11:30:05',4:'11:30:07',5:'11:30:09',6:'11:30:11',9:'11:30:17'},
    }
    notes = {
        'origin_beige': 'Fresh cheese placements into pale/beige tank at front filling station. White cheese and later cover distinguish it from the stationary scrap receptacle to the right. Unloaded manual jack returns from doorway18:08-16. People walk/talk near doorway18:28-19:44; no tank moves with these people. A blue-lined empty replacement waits locally left. No loaded departure in this window.',
        'departure_beige': 'Placements continue through20:32, cover is placed20:36, station tank pulled20:40 and crosses shared door20:48-52. Separate visibly empty blue-lined replacement moves into station20:48-21:00; subsequent filling starts around21:08. Through doorway, a beige tank is drawn onto scale21:56 and remains visible thereafter. Direct15 entry and intermediate staging not captured. This is a bounded middle section of a long11 source, not a source-start clock reset.',
        'origin_blue': 'Fresh blue-lined gray-body tank fills at front station23:20-28:32. Earlier beige tank on scale visible through doorway until25:20, pulled off25:28 and platform empty25:36. Manual jack returns27:04. Fresh station load pulled28:40-48, crosses threshold28:56 and is gone29:04. Another visibly empty blue-lined replacement moves into station28:56-29:12. Neither initial quantity nor fill completion volume is inferred.',
        'people18': 'Despite provisional window name, no tank entry occurs. Dark-clothed person walks from shared doorway into15 at18:46-52 and returns19:06-14. Existing inventory remains in view. This is a people-only tracked action, not a whole-room zero.',
        'people19': 'Initial19:29 image excluded for synchronization; first usable19:36. Two people near doorway; dark-clothed person enters15 while apron-clad person returns toward11. No tank travels with them, and no new tank is put on scale. Provisional filename is not an event label.',
        'scale21': 'First usable21:43 already shows beige tank staged left of shared doorway. Operator handles blue cover/liner, then pushes tank right onto scale21:53-56. Actual entry is not visible. Same beige appearance and scale appearance21:56 through camera11 are compatible, but do not prove identity across unobserved entry/staging gap.',
        'storage26': 'First usable25:35 after initial25:30. Three front blue containers are stationary initial inventory. Beige tank being handled is behind them in staging; do NOT label25:35-26:14 as scale dwell. Operator pulls beige left26:14-20, turns26:26-29, pushes into back row26:32-38, withdraws empty fork26:41-44. Beige stays in storage26:47 onward. Supplemental wider crops inspected because original doorway crop misses part of storage route. Unloaded manual jack returns toward doorway26:56-27:02. Earlier11 scale clearance25:28-36 is not a demonstrated same-load identity link to26:14 storage movement; no clock offset is fabricated.',
        'stack27': 'First usable27:35 after initial27:18. Powered jack travels unloaded27:35-47, then picks up already-present stacked tanks27:56-28:02, moves left28:05-08 and returns unloaded28:11-20. Upper beige tank is inverted and empty; upright lower gray contents remain unknown. This is internal reposition, not a fresh filling-station entry. Later28:38-44 jack carries a small blue bucket and must not be called unloaded. Stored beige in back row remains stationary. Manual operator appears near door28:48-53 with no incoming tank yet.',
        'scale30': 'Initial29:40 image is stale; first usable30:01 already has blue tank staged inside15 left of door. Operator draws it onto scale30:03-09; tank remains there through30:17. Direct threshold crossing and later storage absent. Candidate counterpart to11 fresh28:56-29:04 departure remains unlinked, not a completed transfer.',
    }
    reviews = []
    for k, m in metas.items():
        sheets = list(m['sheets'])
        if k == 'storage26':
            sheets += [str((paths[k].parent / f'storage_wide_{n}.jpg').relative_to(ROOT)) for n in (13,19,25)]
        reviews.append(dict(review_id='20261006/'+windows[k][0], reviewed_at=stamp,
            reviewer='assistant_visual_review', source_member=m['source']['member'],
            source_sha256=m['source_sha256'], date='20261006', camera=m['source']['camera'], split='train',
            frames_manifest=str(paths[k].relative_to(ROOT)), sampled_frames_visually_reviewed=len(m['samples']),
            reviewed_sheets=sheets, review_scope='Every chronological contact-sheet sample inspected, selected native images and separate ROI overlays inspected. Wider storage re-presentations are not extra sample counts. Not exhaustive native-frame viewing.',
            visible_clock_anchors=[dict(sample_index=i, source_pts_seconds=m['samples'][i]['source_pts_seconds'],
                relative_pts_seconds=m['samples'][i]['relative_pts_seconds'], visible_camera_clock=t,
                clock_read_uncertainty_seconds=1, image=m['samples'][i]['image'],
                usable_for_clock_alignment=(i != 0 or m['source']['camera'] == 11)) for i,t in clocks[k].items()],
            observation=notes[k], accepted_complete_cycle=False,
            clock_warning='Source-initial images excluded from cross-camera alignment. No exact offset inferred; middle-of-source11 samples are valid local chronology only.'))
    merge(OUT/'screening_source_reviews.json', reviews, 'review_id')
    def ev(k,a,b): return evidence(metas[k],a,b,paths[k])
    shared = dict(date='20261006', split='train', reviewer='assistant_visual_review', reviewed_at=stamp,
                  cycle_id=None, dataset_release_accepted=False)
    def neg(ident,camera,cls,times,proof,observation,scope,tanks):
        return dict(shared, sequence_id=ident, camera=camera, camera_track_id=ident,
            review_status='accepted_negative_sequence', production_entry_count_target=0,
            negative_class=cls, tracked_tank_count=tanks, visible_camera_clock_interval=times,
            clock_uncertainty_seconds=4, evidence=proof, observation=observation, label_scope=scope)
    labels = [
        neg('20261006_empty_blue_replacement_1120',11,'empty_tank_internal_reposition',['11:20:48','11:21:00'],[ev('origin_beige',0,39),ev('departure_beige',12,15)],'Visibly empty blue-lined waiting tank moves locally to filling station after beige load leaves.','Only this replacement before subsequent filling. Simultaneous loaded departure is a separate track.',1),
        neg('20261006_empty_blue_replacement_1129',11,'empty_tank_internal_reposition',['11:28:56','11:29:12'],[ev('origin_blue',39,44)],'A second visibly empty blue-lined replacement moves into station after fresh blue load leaves.','Only this replacement movement, not departing load or later production.',1),
        neg('20261006_empty_jack_after_storage_1126',15,'pallet_jack_without_tank',['11:26:41','11:27:02'],[ev('storage26',23,30)],'After beige tank is placed in back row, operator withdraws visibly empty manual jack and returns toward doorway.','Only empty fork withdrawal/return. Stored tank remains separate; its original production identity is unresolved.',0),
        neg('20261006_inverted_upper_internal_1128',15,'empty_tank_internal_reposition',['11:27:56','11:28:08'],[ev('stack27',8,12)],'Powered jack repositions an already-present stack; upper beige tank is visibly inverted.','ONLY inverted upper tank. Upright lower gray tank load is unknown, not zero-labelled. No door crossing in this movement.',1),
        neg('20261006_people_without_tank_1118',15,'people_without_tank',['11:18:46','11:19:56'],[ev('people18',2,5),ev('people18',12,16),ev('people19',1,11)],'People walk through shared doorway without transporting tanks during listed intervals.','One multi-segment people-only episode. Unobserved interval between source clips and other simultaneous room activity are not zero-labelled.',0),
    ]
    beige = dict(shared, sequence_id='20261006_fresh_beige_departure_partial_1120', camera=11,
        camera_track_id='cam11_beige_station_1117_1120', review_status='reviewed_partial_sequence',
        production_entry_count_target=None, observed_loaded_departure_count=1, entry15_camera_clock_interval=None,
        partial_reason='Fresh filling and loaded departure observed. Direct15 entry missing; later staging/scale and subsequent beige storage have unresolved identity across gaps. No complete-cycle target.',
        observation=notes['departure_beige'], evidence=[ev('origin_beige',0,39),ev('departure_beige',0,13)],
        stages=[dict(stage='filling_observed',visible_camera_clock_interval=['11:17:20','11:20:32'],clock_uncertainty_seconds=4,content_evidence='Visible cheese placements into station tank before cover. Initial contents and amount unknown.',evidence=[ev('origin_beige',0,39),ev('departure_beige',0,8)]),
                dict(stage='loaded_departure_11',visible_camera_clock_interval=['11:20:40','11:20:52'],doorway_crossing_camera11_interval=['11:20:48','11:20:52'],clock_uncertainty_seconds=4,evidence=[ev('departure_beige',10,13)])],
        unlinked_followup=dict(status='candidate_scale_and_storage_identity_gaps',production_entry_count_target=None,
            observation='Compatible beige tank already staged in15 at21:43, onto scale21:53-56.11 sees scale dwell then clearance25:28-36.15 shows beige in occluded staging25:35 onward and storage26:32-44 with empty fork withdrawal. Direct entry and intervening identity remain unconfirmed; no claim that front blue inventory is on scale and no fitted clock offset.',
            evidence=[ev('scale21',1,14),ev('departure_beige',28,49),ev('origin_blue',0,17),ev('storage26',1,30)],
            storage_placement_camera15_interval=['11:26:32','11:26:44'],storage_identity_to_fresh_origin='unresolved'),
        limitations=['Missing direct15 crossing prevents new-entry label.','White cover alone is not cheese evidence.','Storage action is visible, but same-load association needs a continuous bridge or independently validated identity.'])
    blue = dict(shared, sequence_id='20261006_fresh_blue_departure_partial_1129', camera=11,
        camera_track_id='cam11_blue_station_1121_1129', review_status='reviewed_partial_sequence',
        production_entry_count_target=None, observed_loaded_departure_count=1, entry15_camera_clock_interval=None,
        partial_reason='Fresh filling and door departure observed.15 resumes with tank already staged30:01; actual entry and later storage absent. No complete-cycle target.',
        observation=notes['origin_blue'], evidence=[ev('departure_beige',17,49),ev('origin_blue',0,43)],
        stages=[dict(stage='filling_observed',visible_camera_clock_interval=['11:21:08','11:28:32'],clock_uncertainty_seconds=8,content_evidence='Fresh cheese placements after empty replacement; reviewed source windows preserve chronological order. No quantity inferred.',evidence=[ev('departure_beige',17,49),ev('origin_blue',0,39)]),
                dict(stage='loaded_departure_11',visible_camera_clock_interval=['11:28:40','11:29:04'],doorway_crossing_camera11_interval=['11:28:56','11:29:04'],clock_uncertainty_seconds=8,evidence=[ev('origin_blue',40,43)])],
        unlinked_followup=dict(status='already_inside15_scale_candidate',production_entry_count_target=None,
            observation=notes['scale30'], evidence=[ev('stack27',25,27),ev('scale30',1,9)],
            scale_approach_camera15_interval=['11:30:03','11:30:09']),
        limitations=['No exact cross-camera offset or completed storage trajectory.','No tank quantity or kilograms inferred.'])
    labels += [beige,blue]
    merge(OUT/'reviewed_sequence_labels.json',labels,'sequence_id')
    merge(OUT/'sequence_followup_queue.json',[
        dict(candidate_id='20261006_beige_1120_entry_storage_gap',date='20261006',split='train',cycle_id=None,production_entry_count_target=None,status='partial_entry_and_storage_identity_gap',reviewed_at=stamp,reviewed_partial_sequence_id=beige['sequence_id'],observation=beige['partial_reason'],next_action='Seek15 direct20:48-21:43 entry/staging bridge, and25:20-35 scale-to-staging continuity if present. Reuse existing26min wider storage views; they prove placement only. Do not infer a clock offset from staged beige behind stationary foreground bins.',new_evidence=[ev('departure_beige',10,13),ev('scale21',1,14),ev('origin_blue',15,17),ev('storage26',13,30)]),
        dict(candidate_id='20261006_blue_1129_entry_storage_gap',date='20261006',split='train',cycle_id=None,production_entry_count_target=None,status='partial_entry_and_storage_missing',reviewed_at=stamp,reviewed_partial_sequence_id=blue['sequence_id'],observation=blue['partial_reason'],next_action='15 first usable30:01 is after actual crossing. Inspect metadata for a preceding bridge, then later113105-113136,113423-113444,113455-113514 for scale/storage; these files have not been visually reviewed in this batch. Do not treat stale29:40 frame as continuous crossing evidence.',new_evidence=[ev('origin_blue',40,43),ev('scale30',1,9)])
    ],'candidate_id')
    registry = read(OUT/'object_review_decisions.json')
    history = OUT/'review_history/object_decisions_before_20261031_16.json'
    if not history.exists(): save(history,registry)
    decisions={r['id']:r for r in registry['reviews']}
    draft={r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
    roi_notes={'140':'Beige-body blue-lined departing tank plus adjacent truncated background tank fragment at upper-left. Two generic instances; cover alone not load proof.',
        '141':'Departing tank at doorway, partial door/person occlusion. Generic detection only.',
        '142':'Loaded station tank in aisle plus distinct truncated upper-left background tank. Two generic instances.',
        '144':'Only visible truncated beige tank fragment in upper-right; top and right crop boundaries cut instance. Object presence only, no load or scale label.',
        '145':'Two separate stacked tanks: inverted upper beige, upright lower gray. Amodal extents overlap at stack boundary. Generic boxes only; lower contents unknown.'}
    for ident,note in roi_notes.items():
        assert ident not in decisions
        r=draft[ident]
        assert r['date']=='20261006' and r['split']=='train'
        sheet='15' if ident in ('140','141') else '16'
        decisions[ident]=dict(id=ident,image_sha256=r['sha256'],boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',load_state_reviewed=False,sequence_reviewed=False,instance_attributes=[dict(box_index=j,truncated=(b[0]==0 or b[1]==0 or b[2]==r['width'] or b[3]==r['height']),occluded=True,load_state='unknown_not_annotated') for j,b in enumerate(r['boxes_xyxy'])],evidence=[r['source_frame'],r['frames_manifest'],f'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_{sheet}.jpg'],note=note)
    registry['reviews']=list(decisions.values())
    exclusions={r['id']:r for r in registry.get('excluded_roi_reviews',[])}
    exclusions['143']=dict(id='143',image_sha256=draft['143']['sha256'],reviewed_at=stamp,reviewer='assistant_visual_review',decision='exclude_whole_roi_not_an_empty_image',reason='Door-occluded main tank and uncertain additional background fragment; no clean complete instance extents. Excluded crop is not an empty image.',evidence=[draft['143']['image'],draft['143']['source_frame'],draft['143']['frames_manifest']])
    registry['excluded_roi_reviews']=list(exclusions.values())
    registry.setdefault('corrections',[]).append('Batch16:140/141/142/144/145 approved after native context and separate labels15/16 overlay review,8 generic boxes.143 excluded. Prior reviewed decisions unchanged.')
    save(OUT/'object_review_decisions.json',registry)
    inventory=read(BASE/'archive_inventory.json')
    inspected={m['source']['member']:m['source_sha256'] for m in metas.values()}
    for r in inventory['records']:
        if r['member'] in inspected: r.update(pixel_inspected=True,sha256=inspected[r['member']])
    assert not any(r['pixel_inspected'] for r in inventory['records'] if r['split']=='test')
    save(BASE/'archive_inventory.json',inventory)
    allreviews=read(OUT/'screening_source_reviews.json')
    total=sum(r['sampled_frames_visually_reviewed'] for r in allreviews)
    nsource=len({r['source_member'] for r in allreviews})
    state['last_completed'] += [
        f'Batch16 inspected258 chronological samples in9 windows on6Oct; {total} total across{nsource} sources and{len(allreviews)} windows. Three wider storage-sheet presentations reuse existing samples, not additional frame counts. Extractions finished;25/28Oct untouched.',
        'Two fresh station departures20:48-52(beige) and28:56-29:04(blue) recorded as partials.15 first usable staging21:43/30:01 lacks direct entries. Beige storage26:32-44 visible but origin identity unresolved; no guessed full cycle or clock offset. Totals2 complete cycles,15 partials.',
        'Five track-scoped negatives added:two empty replacements, empty manual jack after storage, inverted upper tank internal reposition(lower contents unknown), and people-only doorway episode. Total37 negative sequences.',
        'Six native ROI candidates140-145 appended;five accepted with8 boxes,143 excluded. Totals146 candidates,99 approved images,151 accepted boxes,47 exclusions,zero unresolved object drafts. Dataset remains unreleased.'
    ]
    state['priority_next']=[
        'Batch16 all9 new6Oct windows recorded. Two newpartial departures1120/1129 need direct15 entry and same-load scale/storage continuity. Follow sequence_followup_queue; do not label provisional window names as actual entries.',
        'For6Oct beige, storage26:32-44 is visible but identity from25:28 scale clearance remains unverified. Stationary front blue bins are NOT proof of scale occupancy; no50-second offset has been established.',
        'For6Oct blue, later15 files113105-113136,113423-113444,113455-113514 are unreviewed potential scale/storage context. Need more defensible complete cycles across training days and true same-load/post-storage relocation negatives.',
    ]+[p for p in state['priority_next'] if p.startswith('Prioritize') or p.startswith('Known gaps') or p.startswith('25/28')]
    state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    for s in ['work/append_tank_roi_batch_20261031_16.py','work/record_tank_sequence_batch_20261031_16.py']:
        if s not in state['scripts']:state['scripts'].append(s)
    save(OUT/'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_temporal_samples=258,additional_partials=2,additional_negatives=5,additional_accepted_images=5,total_presentations=total,training_started=False)))


if __name__ == '__main__':
    main()
