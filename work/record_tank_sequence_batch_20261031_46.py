"""Persist reviewed 13Oct 09:45 production route, preserving earlier reviews."""
import datetime as dt
import hashlib
import json
from pathlib import Path
from record_tank_boundary_review_20261031 import read, save, merge, evidence

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/tank_transfer_training_v1'
OUT=BASE/'dataset_v1'
RUN='sequence_review_20261031_46'

def main():
    state=read(OUT/'continuation_state.json')
    if RUN in state.get('completed_curation_runs',[]):
        print('Already recorded');return
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    windows={'dep':('departure0944_cam11',31),'entry':('entry0944_cam15',25),
      'approach':('approach0946_cam15',10),'scale':('scale0946_cam15',19),
      'off':('scale0948_cam15',15),'route':('route0949_cam15',37),
      'dense':('entry0945_dense_cam15',14),'park':('parking0950_dense_cam15',19),
      'after':('release0951_dense_cam15',17)}
    paths={k:OUT/'sequence_review/20261013'/w/'frames.json' for k,(w,n) in windows.items()}
    metas={k:read(p) for k,p in paths.items()}
    clocks={
      'dep':{0:'09:44:44',7:'09:44:51',11:'09:44:55',12:'09:44:56',16:'09:45:00',17:'09:45:01',20:'09:45:04',24:'09:45:08',26:'09:45:10',30:'09:45:14'},
      'entry':{0:'09:44:20',1:'09:44:26',9:'09:44:58',10:'09:45:02',11:'09:45:06',12:'09:45:10',23:'09:45:54',24:'09:45:58'},
      'approach':{0:'09:45:47',1:'09:46:09',2:'09:46:12',3:'09:46:15',9:'09:46:33'},
      'scale':{0:'09:46:32',1:'09:46:53',7:'09:47:23',9:'09:47:33',18:'09:48:18'},
      'off':{0:'09:48:14',1:'09:48:23',6:'09:48:49',9:'09:49:04',12:'09:49:19',13:'09:49:24',14:'09:49:29'},
      'route':{0:'09:49:23',1:'09:49:38',5:'09:49:58',7:'09:50:08',8:'09:50:13',9:'09:50:18',10:'09:50:23',12:'09:50:33',19:'09:51:08',20:'09:51:13',28:'09:51:53',30:'09:52:03',36:'09:52:33'},
      'dense':{0:'09:44:57',3:'09:45:00',4:'09:45:01',5:'09:45:02',6:'09:45:03',7:'09:45:04',8:'09:45:05',9:'09:45:06',13:'09:45:10'},
      'park':{0:'09:50:23',5:'09:50:28',8:'09:50:31',9:'09:50:32',10:'09:50:33',11:'09:50:34',18:'09:50:41'},
      'after':{0:'09:50:58',5:'09:51:03',10:'09:51:08',11:'09:51:09',12:'09:51:10',16:'09:51:14'}}
    notes={
      'dep':'All31 samples/six sheets viewed. Cheese visible44:44-46, covered47-49, moves51-58, threshold45:00-04. Native44:55 and45:04 inspected. Distinct empty replacement moves44:56 to station45:05, still empty08, cheese lift09/placement10. Right-edge sliver of departing load remains visible through door04; threshold interval is approximate, not an exact instant.',
      'entry':'All25 samples/five sheets viewed. Initial44:20 then26; one covered gray load crosses45:02-06, staged10-54. Operator handles top, then engages jack58. Yellow powered jack and stacked small metal containers are unrelated tracks. Lower incoming body partly hidden by fixed bins.',
      'approach':'All10 samples/two sheets viewed. Initial45:47 stale; next46:09 shows same covered gray body moving right from staging,12 approaches platform,15 settled through33.11-second sampled join from prior45:58 retained; same operator, liner and route, no competing tank.',
      'scale':'All19 samples/four sheets viewed. Initial46:32 stale relative to prior33. First noninitial53 leaves20-second stationary-platform join. Same gray body on platform throughout to48:18, operator attends47:23-33. No numeric weight or verified measurement. Packaging activity is separate.',
      'off':'All15 samples/three sheets viewed. Initial48:14 stale, first23 follows preceding18 by5 seconds. Same covered body remains on scale; operator prepares handling49:19-24, moving left by29. Metal-container stacks and people in foreground are unrelated.',
      'route':'All37 samples/seven sheets viewed, native50:13 inspected. Initial49:23 stale; next38 shows tank at door-side staging, nine-second sampled join from prior29 retained. Same operator handles jack and load in staging through50:03, emerges08-13, rotates left18, pushed into rear row23-31. Tank remains as bare forks pull out32-34; dense window confirms. Empty jack stays near parked tank while operator talks, then moves away51:08-14 and returns toward door51:53-52:03. Tank stays parked through52:33. Small metal-container pallets are not tanks.',
      'dense':'All14 samples/three sheets viewed. Operator approaches44:57-59, gray covered body at threshold45:00-03, turns left04-06 and stages07-10. Same outgoing11 load, operator, loose liner and white cover, no second eligible crossing. Independent clocks retained.',
      'park':'All19 samples/four sheets viewed. Covered gray load pushed into rear-row position50:23-31. Operator draws jack backward32-34, unloaded forks visible and tank stationary. Final placement interval31-34. Nearby person partly occludes jack, so no subsecond release claim.',
      'after':'All17 samples/three sheets viewed. Window name is only an extraction label: actual fork withdrawal occurred earlier50:32-34. From50:58 tank already parked and forks already empty. Operator talks, draws empty jack away51:08-14; no new production entry.'}
    for k,m in metas.items():
        w,n=windows[k];assert len(m['samples'])==n
        assert m['source']['split']=='train' and m['source']['date']=='20261013'
        merge(OUT/'screening_source_reviews.json',[dict(review_id='20261013/'+w,reviewed_at=stamp,
          reviewer='assistant_visual_review',date='20261013',camera=m['source']['camera'],split='train',
          source_member=m['source']['member'],source_sha256=m['source_sha256'],frames_manifest=str(paths[k].relative_to(ROOT)),
          sampled_frames_visually_reviewed=n,reviewed_sheets=m['sheets'],observation=notes[k],accepted_complete_cycle=False,
          review_scope='All chronological sample presentations inspected; not exhaustive native-frame inspection.',
          visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],
            relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],visible_camera_clock=t,
            clock_read_uncertainty_seconds=1,image=m['samples'][i]['image'],usable_for_clock_alignment=False) for i,t in clocks[k].items()])],'review_id')
    # Existing reviewed filling evidence is reused without inflating sample count.
    for k,w in [('fill','next_route0933_cam11'),('origin','departure0935_cam11')]:
        paths[k]=OUT/'sequence_review/20261013'/w/'frames.json';metas[k]=read(paths[k])
    def ev(k,a,b):return evidence(metas[k],a,b,paths[k])
    shared=dict(date='20261013',split='train',reviewer='assistant_visual_review',reviewed_at=stamp,
        dataset_release_accepted=False,camera_clock_offset_seconds=None)
    cycle=dict(shared,sequence_id='20261013_gray_cycle0945',cycle_id='20261013_gray_cycle0945',
        camera_track_id={'11':'gray_station_departure0944','15':'gray_entry0945_storage0950'},
        review_status='accepted_complete_cycle',production_entry_count_target=1,entry_camera=15,
        entry_clock_interval=['09:45:00','09:45:06'],clock_alignment_status='visual_correspondence_with_interval_uncertainty_retained',
        counting_rule='One fresh filling-to-storage load. Staging, parking and empty jack return do not add entries.',
        stages=[
          dict(stage='filling_observed',camera=11,visible_camera_clock_interval=['09:36:01','09:44:46'],
            content_evidence='Previously reviewed empty replacement at36:00 receives fresh cheese01-02, fills through44:44; visible cheese before cover44:47.',
            evidence=[ev('origin',21,40),ev('fill',18,68),ev('dep',0,2)]),
          dict(stage='loaded_departure_11',camera=11,visible_camera_clock_interval=['09:44:47','09:45:04'],
            doorway_crossing_camera11_interval=['09:45:00','09:45:04'],clock_uncertainty_seconds=1,
            observation='Fresh load covered then pulled from filling station through shared door; distinct empty replacement tracked separately.',evidence=[ev('dep',3,20)]),
          dict(stage='entry_15',camera=15,visible_camera_clock_interval=['09:45:00','09:45:06'],clock_uncertainty_seconds=1,
            observation='Corresponding covered gray load with same operator and liner enters once and turns into staging. Stationary bins partly occlude base. Clocks independent.',
            evidence=[ev('dep',15,20),ev('dense',2,13),ev('entry',10,24)]),
          dict(stage='scale_visit',camera=15,visible_camera_clock_interval=['09:46:09','09:49:29'],
            scale_approach_interval=['09:46:09','09:46:15'],scale_departure_clock_interval=['09:49:19','09:49:29'],
            numeric_weight_kg=None,measurement_success_verified=False,
            observation='Same load moves from staging right onto platform, dwells, then pulled left.11-second staging/approach and20-second stationary scale source joins retained, not continuous native coverage.',
            evidence=[ev('entry',23,24),ev('approach',1,9),ev('scale',1,18),ev('off',1,14)]),
          dict(stage='storage_placement',camera=15,visible_camera_clock_interval=['09:49:29','09:52:33'],
            parking_approach_interval=['09:50:08','09:50:31'],unloaded_fork_withdrawal_interval=['09:50:31','09:50:34'],clock_uncertainty_seconds=3,
            observation='Same covered tank returns to staging then crosses aisle into rear-row slot; unloaded forks withdraw, tank stays while operator talks and takes bare jack away. Nine-second source join49:29-38 retained.',
            evidence=[ev('off',13,14),ev('route',1,36),ev('park',0,18),ev('after',0,16)])],
        limitations=['Sampled visual trajectory review; no measured kilograms or exact cross-camera offset.',
          'Initial stale frames excluded from chronology; sampled source joins11/20/5/9 seconds explicitly retained.',
          'Identity uses observed origin, operator, cover/liner and trajectory rather than color or matching timestamps alone.'])
    negatives=[dict(shared,sequence_id='20261013_empty_gray_replacement0945',cycle_id=None,review_status='accepted_negative_sequence',
       camera=11,negative_class='empty_tank_internal_reposition',production_entry_count_target=0,tracked_tank_count=1,
       visible_camera_clock_interval=['09:44:56','09:45:08'],observation='Distinct empty waiting tank moved into filling station; visible empty interior. Stop before first cheese placement.',
       label_scope='Replacement track only, not simultaneous departing production load.',evidence=[ev('dep',12,24)]),
       dict(shared,sequence_id='20261013_unloaded_jack_after_storage0950',cycle_id=None,review_status='accepted_negative_sequence',
       camera=15,negative_class='pallet_jack_without_tank',production_entry_count_target=0,tracked_tank_count=0,
       visible_camera_clock_interval=['09:50:34','09:52:03'],observation='Bare jack after storage; pauses during conversation then returns toward door. Stored tank remains fixed.',
       label_scope='Only unloaded manual jack, not whole room.',evidence=[ev('park',11,18),ev('after',0,16),ev('route',13,30)])]
    save(OUT/'review_history/sequence_labels_before_20261031_46.json',read(OUT/'reviewed_sequence_labels.json'))
    merge(OUT/'reviewed_sequence_labels.json',[cycle,*negatives],'sequence_id')
    qp=OUT/'sequence_followup_queue.json';save(OUT/'review_history/followup_queue_before_20261031_46.json',read(qp))
    merge(qp,[dict(candidate_id='20261013_next_station_load_after0936',date='20261013',split='train',cycle_id=None,
      production_entry_count_target=None,status='resolved_in_reviewed_complete_cycle',resolved_sequence_id=cycle['sequence_id'],reviewed_at=stamp,
      observation='Entry45:00-06, scale, rear-row storage50:31-34 reviewed.',next_action='Resolved; do not count queue entry separately.',evidence=[ev('dense',3,9),ev('park',8,11)])],'candidate_id')
    registry=read(OUT/'object_review_decisions.json');save(OUT/'review_history/object_decisions_before_20261031_46.json',registry)
    drafts={r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
    for ident,note in {'281':'Covered outgoing gray body.','282':'Empty replacement; right-edge truncation and hand occlusion.','283':'Separate static blue aisle tank; no production entry implied.'}.items():
        assert not any(r['id']==ident for r in registry['reviews']);r=drafts[ident]
        registry['reviews'].append(dict(id=ident,image_sha256=r['sha256'],
          boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),
          reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',load_state_reviewed=False,sequence_reviewed=False,
          instance_attributes=[dict(box_index=0,truncated=ident=='282',occluded=ident=='282',load_state='unknown_not_annotated')],
          evidence=[r['source_frame'],r['frames_manifest'],'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_37.jpg'],
          note=note+' Native context, crop and independent rendered overlay inspected.'))
    save(OUT/'object_review_decisions.json',registry)
    inv=read(BASE/'archive_inventory.json');inspected={m['source']['member']:m['source_sha256'] for m in metas.values()}
    for r in inv['records']:
        if r['member'] in inspected:r.update(pixel_inspected=True,sha256=inspected[r['member']])
    assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test')
    save(BASE/'archive_inventory.json',inv)
    added=sum(n for w,n in windows.values())
    state['last_completed'] += [f'Batch46: {added} new temporal presentations in nine windows on13Oct reviewed and recorded. Existing filling evidence reused without double-counting.',
      'Seventh complete cycle: entry15 09:45:00-06, scale visit, rear-row storage/fork withdrawal50:31-34. Explicit source joins retained.',
      'Two scoped negatives added. Three native ROI images/three boxes separately overlay reviewed. Dataset remains unreleased; no training or test pixels.']
    state['priority_next']=['Batch46 route resolved; do not repeat nine windows. Three new images281-283 approved.',
       'Prioritise complete cycles on another paired training day; all seven complete cycles remain13Oct.15Oct source11 12:48:38-13:02:10 reviewed only through relative255.519; check counterpart coverage before extraction.',
       '13Oct next station load begins45:10; subsequent11 source09:46:55-54:05 and15 sourcesafter09:52 remain available, but day diversity has higher priority.']+[p for p in state['priority_next'] if p.startswith('Known gaps') or p.startswith('25/28')]
    state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False)
    state.setdefault('completed_curation_runs',[]).append(RUN)
    state['scripts']+=['work/append_tank_roi_batch_20261031_46.py','work/record_tank_sequence_batch_20261031_46.py']
    save(OUT/'continuation_state.json',state)
    print(json.dumps(dict(recorded=RUN,new_temporal_presentations=added,new_cycles=1,new_negatives=2,new_images=3)))

if __name__=='__main__':main()
