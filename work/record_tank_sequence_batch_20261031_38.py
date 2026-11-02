"""Record six visually reviewed6Oct windows; do not bridge absent entry/storage footage."""
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read, save, merge, evidence

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/tank_transfer_training_v1'
OUT=BASE/'dataset_v1'
RUN='sequence_review_20261031_38'

def main():
    state=read(OUT/'continuation_state.json')
    if RUN in state.get('completed_curation_runs',[]):
        print('Already recorded',RUN);return
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    windows={
        'broad':('morning_route_0811_cam11',82),
        'before13':('morning_route_0813_cam15',8),
        'before15':('morning_route_0815_cam15',12),
        'entry15':('morning_entry_0817_cam15',21),
        'storage':('morning_storage_0822_cam15',16),
        'departure':('morning_departure_0817_cam11',56),
    }
    paths={k:OUT/'sequence_review/20261006'/w/'frames.json' for k,(w,_) in windows.items()}
    metas={k:read(p) for k,p in paths.items()}
    for k,m in metas.items():
        assert m['source']['date']=='20261006' and m['source']['split']=='train'
        assert len(m['samples'])==windows[k][1]
    # Pixel clock anchors read on chronological contact sheets. These are not a fitted camera offset.
    clocks={
        'broad':{0:'08:11:23',1:'08:12:01',5:'08:13:21',10:'08:15:01',15:'08:16:41',
            16:'08:17:01',17:'08:17:21',18:'08:17:42',19:'08:18:01',20:'08:18:22',21:'08:18:42',
            22:'08:19:02',23:'08:19:22',27:'08:20:42',29:'08:21:22',30:'08:21:42',31:'08:22:02',
            43:'08:26:02',44:'08:26:22',45:'08:26:42',46:'08:27:02',48:'08:27:42',
            57:'08:30:42',58:'08:31:02',59:'08:31:22',70:'08:35:03',74:'08:36:23',81:'08:38:42'},
        'before13':{0:'08:13:43',1:'08:13:51',2:'08:13:53',3:'08:13:55',4:'08:13:57',5:'08:13:59',6:'08:14:01',7:'08:14:03'},
        'before15':{0:'08:15:14',1:'08:15:25',2:'08:15:27',3:'08:15:28',4:'08:15:30',5:'08:15:32',
            6:'08:15:35',7:'08:15:37',8:'08:15:39',9:'08:15:41',10:'08:15:42',11:'08:15:44'},
        'entry15':{0:'08:17:38',1:'08:17:42',2:'08:17:43',3:'08:17:44',4:'08:17:45',5:'08:17:46',
            6:'08:17:47',7:'08:17:48',8:'08:17:49',9:'08:17:50',10:'08:17:51',11:'08:17:52',
            12:'08:17:53',13:'08:17:54',14:'08:17:55',15:'08:17:56',16:'08:17:57',17:'08:17:58',
            18:'08:17:59',19:'08:18:00',20:'08:18:01'},
        'storage':{0:'08:22:29',1:'08:22:37',2:'08:22:38',3:'08:22:39',4:'08:22:40',5:'08:22:41',
            6:'08:22:42',7:'08:22:43',8:'08:22:44',9:'08:22:45',10:'08:22:46',11:'08:22:47',
            12:'08:22:48',13:'08:22:49',14:'08:22:50',15:'08:22:51'},
        'departure':{0:'08:17:01',6:'08:17:07',7:'08:17:08',8:'08:17:09',9:'08:17:10',11:'08:17:12',
            12:'08:17:13',15:'08:17:16',16:'08:17:17',17:'08:17:18',18:'08:17:19',19:'08:17:20',
            20:'08:17:21',21:'08:17:22',24:'08:17:25',29:'08:17:30',30:'08:17:31',31:'08:17:32',
            32:'08:17:33',33:'08:17:34',34:'08:17:35',35:'08:17:36',36:'08:17:37',37:'08:17:38',
            38:'08:17:39',39:'08:17:40',40:'08:17:41',41:'08:17:42',42:'08:17:43',43:'08:17:44',
            44:'08:17:45',45:'08:17:46',46:'08:17:47',47:'08:17:48',48:'08:17:49',49:'08:17:50',
            50:'08:17:51',51:'08:17:52',52:'08:17:53',53:'08:17:54',54:'08:17:55',55:'08:17:56'},
    }
    notes={
        'broad':'All82 chronological samples/14 sheets inspected. Initial clock11:23 then12:01. First blue-lined station body receives cheese through17:01, leaves by17:21; dense follow-up resolves departure. Distinct empty replacement moves17:42, atstation18:01, cheese additions18:22 onward. Covered gray body on platform beyond door18:42-21:22, moving21:42, clear22:02: explicitly unlinked to fresh17min departure because room15 entry/staging coverage absent. Second station body departs26:22, gone26:42, another replacement atstation26:42 and fills27:02-38:42. Separate platform visit27:42-30:42, moving31:02, clear31:22. Second transfer queued for denser inspection, not accepted as a cycle. Fixed scrap tank right and waiting empty row left remain separate. No full-day total or scalar camera offset inferred.',
        'before13':'All8 chronological samples/two sheets inspected. Initial13:43 then13:51-14:03. People move near wall/door without visible tank movement in sampled area. Covered storage rows and empty foreground bins are initial inventory. Screening context only, not whole-room absence or new negative count.',
        'before15':'All12 chronological samples/two sheets inspected. Initial15:14 then15:25-44. Worker comes from doorway without tank and joins another beside stored rows. No loaded entry is visible in this window; no whole-room zero label or new negative count.',
        'entry15':'All21 chronological samples/four sheets inspected. Initial17:38 then17:42-18:01. Worker handles hose and partly hidden staging/tank activity behind fixed foreground bins. The actual17:17-22 doorway crossing seen by11 is already over before this source. No direct15 entry timestamp, physical identity or full cycle established. Window name is a candidate label only.',
        'storage':'All16 chronological samples/three sheets inspected. Initial22:29 then22:37-51. Gray blue-covered body emerges37-40, turns41-43 and is pushed toward back-wall storage44-51. Native22:40 and22:46 inspected. Final fork withdrawal/parking completion is not captured. Camera11 platform departure21:42-to15initial22:29 leaves a trajectory gap; origin and identity remain explicitly unlinked. Cover does not prove cheese.',
        'departure':'All56 one-second samples/10 sheets inspected, clock17:01-56. Cheese visible during final station handling01-07; white panels positioned08-09. Fresh body starts being pulled10, clear station12, turns towarddoor13-16, reaches threshold17, crosses18-21 and absent22. Different empty blue-lined body selected from waiting row31-38, moved39-46, atstation47-49. Empty bottom directly visible43. Later cheese pickup54-56 excluded from negative. Native17:13,17 and43 inspected. Fixed scrap tank remains distinct.',
    }
    for k,m in metas.items():
        merge(OUT/'screening_source_reviews.json',[dict(
            review_id='20261006/'+windows[k][0],reviewed_at=stamp,reviewer='assistant_visual_review',
            date='20261006',camera=m['source']['camera'],split='train',source_member=m['source']['member'],
            source_sha256=m['source_sha256'],frames_manifest=str(paths[k].relative_to(ROOT)),
            sampled_frames_visually_reviewed=len(m['samples']),reviewed_sheets=m['sheets'],
            review_scope='All chronological sample sheets inspected; selected native images and four separate rendered object overlays reviewed. Not exhaustive native-frame viewing.',
            observation=notes[k],accepted_complete_cycle=False,
            clock_warning='Selected pixel clocks only. Initial stale frames and filename/PTS are not synchronization evidence.',
            visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],
                relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],visible_camera_clock=t,
                clock_read_uncertainty_seconds=1,image=m['samples'][i]['image'],usable_for_clock_alignment=False)
                for i,t in clocks[k].items()])],'review_id')

    def ev(k,a,b):return evidence(metas[k],a,b,paths[k])
    save(OUT/'review_history/sequence_labels_before_20261031_38.json',read(OUT/'reviewed_sequence_labels.json'))
    shared=dict(date='20261006',split='train',reviewer='assistant_visual_review',reviewed_at=stamp,
        dataset_release_accepted=False,cycle_id=None,camera_clock_offset_seconds=None)
    partial=dict(shared,sequence_id='20261006_blue_station_departure0817_partial',
        review_status='reviewed_partial_sequence',production_entry_count_target=None,
        camera_track_id={'11':'blue_station_load0817','15':None},
        stages=[
            dict(stage='filling_observed',camera=11,visible_camera_clock_interval=['08:12:01','08:17:07'],
                initial_contents_unknown=True,evidence=[ev('broad',1,16),ev('departure',0,6)]),
            dict(stage='loaded_departure_11',camera=11,visible_camera_clock_interval=['08:17:10','08:17:22'],
                observation='Fresh station body contains visible cheese before white panels are placed; physically exits11.',evidence=[ev('departure',9,21)]),
            dict(stage='entry_15',camera=11,visible_camera_clock_interval=['08:17:17','08:17:22'],
                room15_clock_interval=None,clock_basis='Physical passage seen from11 only; no calibrated room15 timestamp.',
                evidence=[ev('departure',16,21)])],
        reviewed_followup_observations=[
            dict(stage='staging_observation',camera=15,visible_camera_clock_interval=['08:17:38','08:18:01'],
                same_load_identity_confirmed=False,observation='Partly hidden staging activity; fresh doorway crossing already missed.',evidence=[ev('entry15',0,20)]),
            dict(stage='scale_visit',camera=11,visible_camera_clock_interval=['08:18:42','08:21:22'],
                departure_interval=['08:21:22','08:22:02'],same_load_identity_confirmed=False,numeric_weight_kg=None,
                observation='Covered gray body on platform; moving21:42 and clear22:02. Unlinked to prior fresh departure.',evidence=[ev('broad',21,31)]),
            dict(stage='storage_approach',camera=15,visible_camera_clock_interval=['08:22:37','08:22:51'],
                same_load_identity_confirmed=False,storage_completion_confirmed=False,
                observation='Gray covered body moves toward back storage; final release not observed. Identity across missing route unresolved.',evidence=[ev('storage',0,15)])],
        missing_stages=['calibrated_room15_entry_timestamp','verified_entry_to_scale_identity','verified_scale_to_storage_identity','confirmed_storage_completion'],
        limitations=['Room15 peer begins initial08:17:38/usable08:17:42, after17:17-22 crossing from11. Earlier15 source metadata ends16:25; absent entry footage cannot be reconstructed from clocks.',
            'Scale movement visible21:42, then15 first image22:29/usable22:37; missing physical trajectory prevents identity linkage.',
            'Storage source ends22:51 with operator still handling the load; no final fork withdrawal or settled position confirmed.',
            'Earlier08:01 replacement context is not certified as same body across unreviewed file join11:35-to12:01. No zero starting contents assumed.'])
    replacement=dict(shared,sequence_id='20261006_empty_blue_station_replacement0817',
        review_status='accepted_negative_sequence',production_entry_count_target=0,camera=11,
        negative_class='empty_tank_internal_reposition',tracked_tank_count=1,direction='room11_waiting_area_to_station',
        visible_camera_clock_interval=['08:17:31','08:17:49'],
        observation='Different empty blue-lined body selected from waiting row and pushed to filling station; empty bottom visible at17:43.',
        label_scope='Only bounded empty replacement movement. Excludes outgoing loaded tank, fixed scrap tank and subsequent cheese additions.',
        evidence=[ev('departure',30,48)])
    merge(OUT/'reviewed_sequence_labels.json',[partial,replacement],'sequence_id')
    qp=OUT/'sequence_followup_queue.json'
    save(OUT/'review_history/followup_queue_before_20261031_38.json',read(qp))
    merge(qp,[dict(candidate_id='20261006_blue_morning0817',date='20261006',split='train',reviewed_at=stamp,
        status='resolved_as_partial_missing_route',resolved_sequence_id=partial['sequence_id'],cycle_id=None,production_entry_count_target=None,
        observation='Fresh filling and11 doorway crossing17:17-22 verified. Later15 staging, scale and storage approach unlinked; completion not captured.',
        next_action='Do not repeat absent entry or21:42-to22:29 scale/storage route without new media.',
        evidence=[ev('departure',16,21),ev('entry15',0,20),ev('broad',29,31),ev('storage',0,15)]),
        dict(candidate_id='20261006_replacement_after0801',date='20261006',split='train',reviewed_at=stamp,
            status='later_departure_reviewed_prior_join_uncertified',cycle_id=None,production_entry_count_target=None,
            related_partial_sequence_id=partial['sequence_id'],
            observation='Previous02:01 replacement fills through11:35. Later12:01-17:07 station fill and17:17-22 exit now reviewed separately. Cross-file identity has not been certified.',
            next_action='No need to repeat0811-0839 broad screen. If linkage matters, inspect native11:35-to12:01 join; it cannot fix missing15 entry/storage route.',
            evidence=[ev('broad',1,16),ev('departure',16,21)]),
        dict(candidate_id='20261006_blue_morning0826',date='20261006',split='train',reviewed_at=stamp,
            status='needs_dense_departure_and_peer_review',cycle_id=None,production_entry_count_target=None,
            observation='Distinct second station load departs26:22, gone26:42; replacement present26:42 and fills27:02 onward. Platform visit27:42-30:42, off31:02/clear31:22 not yet linked.',
            next_action='Potential15 entry source082604-082635_10679970, later082740-082823/082825-082908/082945-083000.15 next083152 leaves31:02-to31:52 storage route gap. Review bounded entry without promising full cycle; do not resample already inspected broad11.',
            evidence=[ev('broad',20,46),ev('broad',48,59)])],'candidate_id')

    registry=read(OUT/'object_review_decisions.json')
    save(OUT/'review_history/object_decisions_before_20261031_38.json',registry)
    decisions={r['id']:r for r in registry['reviews']}
    drafts={r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
    objnotes={
        '254':('Fresh station body in clear room aisle; white panels do not alone prove contents.',False,'32'),
        '255':('Doorway tank with feet, minor doorway hardware overlap.',True,'32'),
        '256':('Distinct empty replacement; hands overlap back rim. Object box only.',True,'33'),
        '257':('Independent platform body partly hidden by doorframe. No same-load or contents assertion.',True,'33'),
    }
    for ident,(note,occluded,sheet) in objnotes.items():
        assert ident not in decisions
        r=drafts[ident];assert len(r['boxes_xyxy'])==1
        decisions[ident]=dict(id=ident,image_sha256=r['sha256'],
            boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
            reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',
            load_state_reviewed=False,sequence_reviewed=False,
            instance_attributes=[dict(box_index=0,truncated=False,occluded=occluded,load_state='unknown_not_annotated')],
            evidence=[r['source_frame'],r['frames_manifest'],f'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_{sheet}.jpg'],
            note=note+' Native context and separate rendered overlay inspected. Dataset release pending.')
    registry['reviews']=list(decisions.values())
    registry.setdefault('corrections',[]).append('Batch38: four6Oct ROI images/four boxes separately overlay-reviewed. Existing approvals preserved; no inferred load labels.')
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
        f'Batch38 reviewed {added} sample presentations in six6Oct windows; {total} total across {len({r["source_sha256"] for r in reviews})} sources and {len(reviews)} windows. All extractions completed; test pixels untouched.',
        '6Oct fresh blue station exit08:17:17-22 retained as partial.15 staging starts17:38/42;18:42-21:22 scale visit and22:37-51 storage approach remain unlinked across gaps. Final storage release unobserved. Five full cycles unchanged;33 partials.',
        'One scoped negative added: empty blue replacement17:31-49.82 negatives total. Second departure26:22 screened and queued without cycle count.',
        'Four ROI images/four boxes approved:258 candidates,200 approved,265 boxes,58 exclusions,zero drafts. Training remains unreleased.',
    ]
    state['priority_next']=[
        'Batch38 complete. Prioritise available complete paired routes on days other than13Oct, plus17Oct validation.82 negatives already; do not repeat known missing media.',
        '6Oct08:17 partial:11 entry17:17-22,15 starts17:38/42. Scale18:42-21:22/off21:42/clear22:02;15 storage approach22:37-51 unlinked and release missing. Do not resample these windows without new media.',
        '6Oct08:26 candidate already broadly screened in11: departure26:22/gone26:42.15 source082604-082635 may show entry; later082740-082823/082825-082908/082945-083000. Platformoff31:02 then15 starts31:52: storage gap known. Dense entry review only if useful; no complete-cycle assumption.',
    ]+[p for p in state['priority_next'] if not p.startswith('Batch37') and 'next11 source081123-083900' not in p]
    state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    state['scripts'] += [s for s in ['work/append_tank_roi_batch_20261031_38.py','work/record_tank_sequence_batch_20261031_38.py'] if s not in state['scripts']]
    save(OUT/'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,additional_samples=added,total_presentations=total,
        additional_complete_cycles=0,additional_negative_sequences=1,additional_partial_sequences=1,training_started=False)))

if __name__=='__main__':main()
