"""Persist reviewed 15Oct sequences and native ROI overlays, without training."""
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read, save, merge, evidence

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'outputs/tank_transfer_training_v1'
OUT = BASE / 'dataset_v1'
RUN = 'sequence_review_20261031_18'


def main():
    state = read(OUT / 'continuation_state.json')
    if RUN in state.get('completed_curation_runs', []):
        print('Already recorded', RUN)
        return
    stamp = dt.datetime.now(dt.timezone.utc).isoformat()
    windows = {
        'early': ('early_route_0952_cam15', 28),
        'origin': ('origin_scan_0951_cam11', 75),
        'before': ('early_gap_end_0955_cam15', 12),
        'scale': ('early_scale_0958_cam15', 14),
        'store': ('early_storage_1001_cam15', 8),
        'after': ('early_storage_1002_cam15', 20),
    }
    paths = {k: OUT / 'sequence_review/20261015' / w / 'frames.json' for k, (w, n) in windows.items()}
    metas = {k: read(p) for k, p in paths.items()}
    for k, m in metas.items():
        assert len(m['samples']) == windows[k][1]
        assert m['source']['date'] == '20261015' and m['source']['split'] == 'train'
    # Manually read clock anchors. None are calculated by adding PTS to names.
    clocks = {
        'early': {0:'09:52:46',1:'09:52:57',3:'09:53:03',10:'09:53:24',11:'09:53:27',15:'09:53:39',16:'09:53:42',20:'09:53:54',21:'09:53:57',27:'09:54:15'},
        'origin': {0:'09:51:28',1:'09:51:39',2:'09:51:47',3:'09:51:55',4:'09:52:03',6:'09:52:19',7:'09:52:27',9:'09:52:43',19:'09:54:03',20:'09:54:11',21:'09:54:19',25:'09:54:51',26:'09:54:59',27:'09:55:07',28:'09:55:15',29:'09:55:23',35:'09:56:11',38:'09:56:35',39:'09:56:44',40:'09:56:52',41:'09:56:59',46:'09:57:40',47:'09:57:48',50:'09:58:12',53:'09:58:36',54:'09:58:44',55:'09:58:52',56:'09:59:00',57:'09:59:08',58:'09:59:16',59:'09:59:24',60:'09:59:32',61:'09:59:40',62:'09:59:48',63:'09:59:56',64:'10:00:04',65:'10:00:12',66:'10:00:20',67:'10:00:28',68:'10:00:36',69:'10:00:44',70:'10:00:52',71:'10:01:00',72:'10:01:08',73:'10:01:16',74:'10:01:24'},
        'before': {0:'09:55:56',1:'09:56:05',2:'09:56:07',3:'09:56:09',4:'09:56:11',5:'09:56:13',6:'09:56:15',7:'09:56:17',8:'09:56:18',9:'09:56:20',10:'09:56:23',11:'09:56:25'},
        'scale': {0:'09:58:09',1:'09:58:18',2:'09:58:20',3:'09:58:22',4:'09:58:24',5:'09:58:26',6:'09:58:28',7:'09:58:30',8:'09:58:32',9:'09:58:34',10:'09:58:36',11:'09:58:38',12:'09:58:40',13:'09:58:42'},
        'store': {0:'10:01:45',1:'10:02:06',2:'10:02:08',3:'10:02:10',4:'10:02:12',5:'10:02:14',6:'10:02:16',7:'10:02:18'},
        'after': {0:'10:02:10',1:'10:02:31',2:'10:02:33',3:'10:02:35',4:'10:02:37',5:'10:02:39',6:'10:02:41',7:'10:02:43',8:'10:02:45',9:'10:02:47',10:'10:02:49',11:'10:02:51',12:'10:02:53',13:'10:02:55',14:'10:02:57',15:'10:02:59',16:'10:03:01',17:'10:03:03',18:'10:03:05',19:'10:03:07'},
    }
    notes = {
        'early': 'No new tank entry in inspected samples. People-only movement52:57-53:03, powered truck carrying cartons53:24-27, then unloaded return53:39-42. Later small package movement53:54-57 is not labelled empty or a tank. Fixed blue bins and rear-row covered tanks are existing inventory. Correction to provisional commentary: a fixed blue item by the back wall is NOT a tank established to be dwelling on the scale; the scale platform remains clear.',
        'origin': 'Fresh cheese placement into beige station tank51:39-54:03; panel/cover added54:11-19. Separate visibly empty gray tank returns15-to11 around51:47-55, is put left and later replaces station tank54:59-55:15; fresh filling of gray replacement begins55:23 and continues through10:01:24. Beige station tank moved54:51-59 into room11 doorway staging, remains55:07-56:35, then crosses56:44-52 and is gone56:59. This staging is not a second entry. Through doorway, platform is clear through57:40; beige tank appears on platform57:48, settled58:12, dwell observed until10:01:08, moves off10:01:16 and platform clear10:01:24. No direct camera15 entry observed in available corresponding15 exports.',
        'before': 'Platform clear, fixed foreground bins unchanged. People walk through shared doorway56:09-18 without a tank. Last usable frame56:25 precedes the later56:44-52 loaded crossing in11. No entry bridge present in this file. Initial55:56 retained but not used for clock alignment.',
        'scale': 'Beige tank already on far-right scale from first usable58:18 through58:42. Operator handles the area, another walks left58:24-32; no new tank arrival within these samples. Initial58:09 is stale. The earlier11 departure is a candidate origin but direct15 entry is in the unrecorded interval, so no complete cycle accepted.',
        'store': 'Initial10:01:45 stale. First usable10:02:06 already shows beige tank off scale in aisle left of fixed blue bins. It is routed left toward rear storage group02:08-18. No fork release before final sample. This starts42 seconds after11 platform-clear sample10:01:24; same-load identity across the route gap is not established.',
        'after': 'Initial10:02:10 repeats older trajectory and is excluded for alignment. At first usable02:31, beige tank is parked at left end of rear group and unloaded jack is already withdrawn; tank stays through03:07. Prior usable02:18 to02:31 leaves13-second final-release gap. Empty jack travels toward right02:31-41, turns back left02:43-47. Different gray empty tank crosses15-to11 at02:37-43. Later beige empty tank heads to door02:55-03:01; a further empty gray tank approaches door02:53-03:07 but crossing completion is outside reviewed window. No new production increment assigned to any of these returns.',
    }
    for k, m in metas.items():
        review = dict(review_id='20261015/' + windows[k][0], reviewed_at=stamp,
            reviewer='assistant_visual_review', source_member=m['source']['member'],
            source_sha256=m['source_sha256'], date='20261015', camera=m['source']['camera'], split='train',
            frames_manifest=str(paths[k].relative_to(ROOT)), sampled_frames_visually_reviewed=len(m['samples']),
            reviewed_sheets=m['sheets'], observation=notes[k], accepted_complete_cycle=False,
            review_scope='Every chronological contact-sheet sample inspected; five selected full native images and five separate detection overlays inspected. Counts are sample presentations, not exhaustive native frames.',
            clock_warning='Stale initial images excluded from alignment; local camera-clock intervals retained, no scalar offset inferred.',
            visible_clock_anchors=[dict(sample_index=i, source_pts_seconds=m['samples'][i]['source_pts_seconds'],
                relative_pts_seconds=m['samples'][i]['relative_pts_seconds'], visible_camera_clock=t,
                clock_read_uncertainty_seconds=1, image=m['samples'][i]['image'], usable_for_clock_alignment=i!=0)
                for i,t in clocks[k].items()])
        merge(OUT / 'screening_source_reviews.json', [review], 'review_id')

    def ev(k,a,b): return evidence(metas[k],a,b,paths[k])
    shared = dict(date='20261015',split='train',reviewer='assistant_visual_review',reviewed_at=stamp,dataset_release_accepted=False)
    def neg(ident,cam,cls,times,proof,note,scope,tanks):
        return dict(shared, sequence_id=ident, camera=cam, camera_track_id=ident, cycle_id=None,
            review_status='accepted_negative_sequence',production_entry_count_target=0,negative_class=cls,
            tracked_tank_count=tanks,visible_camera_clock_interval=times,clock_uncertainty_seconds=8 if cam==11 else 2,
            evidence=proof,observation=note,label_scope=scope)
    additions = [
        neg('20261015_empty_gray_return_0951',11,'empty_crossing',['09:51:39','09:55:15'],
            [ev('origin',1,6),ev('origin',25,28)],
            'Empty gray tank returns15-to11 around51:47-55, parked locally, then same empty tank placed at filling station54:59-55:15.',
            'One physical empty return/replacement episode, not two production events. Fresh filling from55:23 belongs to a separate future load.',1),
        neg('20261015_empty_gray_return_1002',15,'empty_crossing',['10:02:35','10:02:43'],
            [ev('after',3,7)],'One visibly empty gray tank moved from left waiting group through door into11.',
            'Only this first gray return. Later beige/gray movements and stationary full inventory excluded from target scope.',1),
        neg('20261015_unloaded_jack_after_parking_1002',15,'pallet_jack_without_tank',['10:02:31','10:02:47'],
            [ev('after',1,9)],'Unloaded jack leaves rear storage group and then turns back toward empty-tank waiting group.',
            'Unloaded jack segment only, before later empty-tank pickup. The prior fork release and origin identity remain unresolved.',0),
    ]
    additions.append(dict(shared,sequence_id='20261015_fresh_beige_departure_partial_0956',review_status='reviewed_partial_sequence',
        cycle_id=None,camera_track_id={'11':'beige_fill_stage_exit_0951_0956','15':'candidate_beige_scale_storage_0958_1002'},
        production_entry_count_target=None,partial_reason='Fresh filling and loaded departure observed in11. Direct15 entry missing; later scale/storage identity unresolved across route and release gaps.',
        stages=[
            dict(stage='filling_observed',visible_camera_clock_interval=['09:51:39','09:54:03'],clock_uncertainty_seconds=8,
                content_evidence='Fresh cheese placements before covering54:11-19. Initial contents and count unknown.',evidence=[ev('origin',1,21)]),
            dict(stage='loaded_departure_11',visible_camera_clock_interval=['09:54:51','09:56:59'],
                station_clearance_interval=['09:54:51','09:54:59'],room11_staging_interval=['09:55:07','09:56:35'],
                doorway_crossing_camera11_interval=['09:56:35','09:56:59'],crossing_visible_samples=['09:56:44','09:56:52'],
                clock_uncertainty_seconds=8,evidence=[ev('origin',25,41)]),
        ],unlinked_followup=dict(status='entry_and_storage_identity_gaps',
            observation='Beige scale appearance through11 at57:48, settled58:12;15 dwell58:18-42.11 platform clears10:01:16-24.15 off-scale storage approach10:02:06-18; already parked by02:31. Origin identity retained as candidate, not accepted.',
            direct_entry15=None,scale_departure_camera11_interval=['10:01:08','10:01:24'],
            storage_approach_camera15_interval=['10:02:06','10:02:18'],parked_by_camera15='10:02:31',
            numeric_weight_kg=None,evidence=[ev('before',1,11),ev('origin',46,74),ev('scale',1,13),ev('store',1,7),ev('after',1,19)]),
        limitations=['No complete cycle or production total assigned.','No numeric clock offset inferred from filenames or PTS.','Station staging, scale movement and storage are not separate new entries.','Camera11 gray replacement begins fresh filling while beige load is staged; keep tank identities separate.']))
    merge(OUT / 'reviewed_sequence_labels.json', additions, 'sequence_id')
    merge(OUT / 'sequence_followup_queue.json', [dict(candidate_id='20261015_beige_0956_entry_storage_gap',
        date='20261015',split='train',cycle_id=None,production_entry_count_target=None,status='partial_entry_and_storage_identity_gap',
        reviewed_at=stamp,observation='15 usable ends09:56:25 then resumes09:58:18, skipping11 crossing56:44-52. Platform clear10:01:24 then15 aisle10:02:06;13-second final-release gap02:18-31.',
        next_action='Do not repeat these six source windows. New source evidence needed for direct15 entry and route/release continuity. Next gray station load is filling through10:01:24 and later section of11 long source remains unreviewed.',
        evidence=[ev('origin',25,74),ev('before',1,11),ev('scale',1,13),ev('store',1,7),ev('after',1,19)])], 'candidate_id')
    save(OUT / 'gap_search_20261031_18.json',dict(reviewed_at=stamp,day='20261015',split='train',
        findings=['15 source ending filename09:56:26 last sampled clock09:56:25; next first usable09:58:18.11 crossing sampled56:44-52 absent from reviewed15 media.',
                  '11 scale clear10:01:24; next15 first usable10:02:06.42-second route gap.',
                  '15 storage approach through10:02:18 then next first usable10:02:31 already parked.13-second fork-release gap.',
                  'Metadata-only search of old camera_video_collection inventory21Oct15 also shows07:10:49-11:29 then07:16:06-31; does not bridge07:14 storage. No old video pixels opened in this audit.'],
        action='Retain partial annotation; avoid repeated unchanged gap searches.'))
    registry = read(OUT / 'object_review_decisions.json')
    h = OUT / 'review_history/object_decisions_before_20261031_18.json'
    if not h.exists(): save(h,registry)
    decisions = {r['id']:r for r in registry['reviews']}
    draft = {r['id']:r for r in read(BASE / 'detector_v1/visual_annotation_draft.json')['records']}
    descriptions = {'152':'Covered beige tank staged in11 before actual exit; cover alone not a load label.',
        '153':'Empty gray return at11 doorway, fully identifiable tank body.',
        '154':'Empty gray replacement at station before filling; upper corner partly hidden by gloves.',
        '156':'Single empty beige tank in15; left/top crop truncation retained.',
        '157':'Single empty beige tank waiting beside11 wall.'}
    for ident,note in descriptions.items():
        assert ident not in decisions
        r=draft[ident]
        decisions[ident]=dict(id=ident,image_sha256=r['sha256'],
            boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',
            load_state_reviewed=False,sequence_reviewed=False,
            instance_attributes=[dict(box_index=0,truncated=ident=='156',occluded=ident in ('153','154','156'),load_state='unknown_not_annotated')],
            evidence=[r['source_frame'],r['frames_manifest'],'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_17.jpg'],note=note)
    registry['reviews']=list(decisions.values())
    r=draft['155']; registry.setdefault('excluded_roi_reviews',[]).append(dict(id='155',image_sha256=r['sha256'],reviewed_at=stamp,
        reviewer='assistant_visual_review',decision='exclude_whole_roi_not_an_empty_image',
        reason='Moving beige tank visible but overlapping background storage-row fragments have uncertain instance extent. Entire image excluded.',
        evidence=[r['image'],r['source_frame'],r['frames_manifest']]))
    registry.setdefault('corrections',[]).append('Batch18: five images152/153/154/156/157 passed separate overlay17 review;155 excluded for background fragments. All previous accepted decisions preserved.')
    save(OUT / 'object_review_decisions.json',registry)
    inv=read(BASE / 'archive_inventory.json'); inspected={m['source']['member']:m['source_sha256'] for m in metas.values()}
    for r in inv['records']:
        if r['member'] in inspected: r.update(pixel_inspected=True,sha256=inspected[r['member']])
    assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test')
    save(BASE / 'archive_inventory.json',inv)
    reviews=read(OUT/'screening_source_reviews.json'); total=sum(r['sampled_frames_visually_reviewed'] for r in reviews)
    state['last_completed'] += [
        f'Batch18 inspected157 chronological samples in6 new15Oct windows; {total} total across{len({r["source_sha256"] for r in reviews})} sources and{len(reviews)} windows. Extractions complete;25/28Oct remain unseen.',
        '15Oct beige fresh filling, room11 staging and loaded doorway crossing around09:56:44-52 recorded as partial. Direct15 entry,42-second scale-to-storage route and13-second final-release gaps retained. No extra entry from staging or storage.',
        'Three track-scoped negatives added:empty gray return/replacement09:51, separate empty gray return10:02 and unloaded jack10:02. Totals3 complete cycles,43 negatives,16 partials. Early blue wall item is fixed inventory, not a proven scale load.',
        'Six native ROI candidates152-157 added; five images/five boxes separately overlay-approved,155 excluded. Totals158 candidates,107 accepted images,160 boxes,51 exclusions,zero unresolved drafts. Training remains unreleased.'
    ]
    state['priority_next']=[
        'Batch18 all six15Oct0951-1003 windows recorded. Partial0956 has confirmed11 origin but direct15 entry and route/release gaps; see gap_search_20261031_18.json. Do not repeat these unchanged sources.',
        'Next15Oct gray load filling through10:01:24; remaining11 source095128-103726 beyond relativePTS600 is unreviewed.15 files100838-100911,100903-100932,100922-100948 may cover later activity; inspect chronological origin only if paired coverage is useful.',
        '3 complete cycles still all13Oct. Need full-cycle day diversity and true already-stored-load relocation/same-load reentry negatives, not additional easy people-only examples.',
        '13Oct subsequent091619-092224 and102139-102912 long15 windows remain unreviewed;11 source090303-092241 inspected only through09:15:04. Prioritize windows likely to preserve whole route.',
        'Old21Oct collection inventory does not bridge07:14 gap: same filename range ends07:11:29, resumes07:16:06. Metadata-only search recorded; do not repeat absent new sources.'
    ]+[p for p in state['priority_next'] if p.startswith('Known gaps') or p.startswith('25/28')]
    state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    state['scripts'] += [s for s in ['work/append_tank_roi_batch_20261031_18.py','work/record_tank_sequence_batch_20261031_18.py'] if s not in state['scripts']]
    save(OUT / 'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_samples=157,additional_partial_sequences=1,additional_negative_sequences=3,total_presentations=total,training_started=False)))


if __name__=='__main__': main()
