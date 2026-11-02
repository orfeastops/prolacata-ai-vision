import datetime as dt
from pathlib import Path
from record_tank_boundary_review_20261031 import read,save,merge,evidence
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'outputs/tank_transfer_training_v1';OUT=BASE/'dataset_v1';RUN='sequence_review_20261031_63'
def main():
 state=read(OUT/'continuation_state.json')
 if RUN in state.get('completed_curation_runs',[]):return
 stamp=dt.datetime.now(dt.timezone.utc).isoformat();evs=[];sources={}
 windows=[('seventh_scale1333_cam15',['13:33:09','13:33:31','13:33:34','13:33:37','13:33:40'],'Beige at wall scale initially; scale empty in later samples. Route obscured by stationary staging bins. Departure bounded33:09-31; initial clock jump prevents continuous tracking.'),('seventh_storage1334_cam15',['13:33:53','13:34:12','13:34:16','13:34:20','13:34:24','13:34:28','13:34:32','13:34:36','13:34:40','13:34:44','13:34:48','13:34:52','13:34:56'],'Covered beige moves from staging12-32, parked alongside separate existing beige by36. Jack withdraws36-40; bare forks travel away40-48, toward doorway52-56. New parked tank remains through56. Initial53-to12 clock jump retained; no direct link to earlier scale tank across obscured route.')]
 for w,clocks,obs in windows:
  p=OUT/'sequence_review/20261015'/w/'frames.json';m=read(p);assert len(m['samples'])==len(clocks);sources[m['source']['member']]=m['source_sha256'];evs.append(evidence(m,0,len(clocks)-1,p))
  merge(OUT/'screening_source_reviews.json',[dict(review_id='20261015/'+w,date='20261015',split='train',camera=15,reviewer='assistant_visual_review',reviewed_at=stamp,source_member=m['source']['member'],source_sha256=m['source_sha256'],frames_manifest=str(p.relative_to(ROOT)),sampled_frames_visually_reviewed=len(clocks),reviewed_sheets=m['sheets'],accepted_complete_cycle=False,review_scope='All extracted chronological sample tiles inspected; no exhaustive native-frame claim.',observation=obs,visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=m['samples'][i]['source_pts_seconds'],relative_pts_seconds=m['samples'][i]['relative_pts_seconds'],visible_camera_clock=t,clock_read_uncertainty_seconds=1,image=m['samples'][i]['image'],usable_for_clock_alignment=False) for i,t in enumerate(clocks)])],'review_id')
 labels=read(OUT/'reviewed_sequence_labels.json');save(OUT/'review_history/sequence_labels_before_20261031_63.json',labels)
 row=next(r for r in labels if r['sequence_id']=='20261015_seventh_beige_departure1328_partial');row['reviewed_at']=stamp
 follow=row['unlinked_followup'];follow.setdefault('room15_scale_evidence',[]).append(evs[0]);follow['room15_local_storage_evidence']=[evs[1]]
 follow['observation']+=' Batch63: scale occupied33:09, empty31-40. Covered beige local route34:12-32, parked36-56 with jack withdrawal36-40. Scale-to-staging identity unresolved through occlusion/coverage gap; missing room15 incoming crossing28:18-24 persists. No complete-cycle promotion based on beige appearance or timestamps.'
 labels.append(dict(sequence_id='20261015_empty_jack_after_storage1334',date='20261015',split='train',reviewer='assistant_visual_review',reviewed_at=stamp,review_status='accepted_negative_sequence',cycle_id=None,production_entry_count_target=0,dataset_release_accepted=False,camera=15,negative_class='pallet_jack_without_tank',tracked_tank_count=0,visible_camera_clock_interval=['13:34:40','13:34:48'],observation='Bare jack withdraws and travels away while newly parked beige remains alongside separate stored beige.',label_scope='Unloaded jack only; no whole-room negative or new production entry.',evidence=[evidence(m,8,10,p)]))
 save(OUT/'reviewed_sequence_labels.json',labels)
 inv=read(BASE/'archive_inventory.json')
 for r in inv['records']:
  if r['member'] in sources:r.update(pixel_inspected=True,sha256=sources[r['member']])
 assert not any(r['pixel_inspected'] for r in inv['records'] if r['split']=='test');save(BASE/'archive_inventory.json',inv)
 state['last_completed'].append('Batch63:18 camera15 samples across two sources reviewed. Local covered-beige storage34:36-56 and empty-jack negative40-48 documented. Scale departure33:09-31 bounded, identity through staging unresolved; seventh origin remains partial.')
 state['priority_next']=['Batch63 seventh_scale1333_cam15 and seventh_storage1334_cam15 fully reviewed; do not repeat. Local storage confirmed but room15 entry and scale-to-staging identity missing.','Continue object ROI annotation from reviewed15Oct windows using native context and separate overlays; batch62 added2 approved ROIs. Expand complete-cycle coverage only where both cameras have continuous evidence.']+[x for x in state['priority_next'] if x.startswith('Known gaps') or x.startswith('25/28')]
 state.update(updated_at=stamp,active_extraction_processes=[],dataset_ready=False);state.setdefault('completed_curation_runs',[]).append(RUN);state['scripts'].append('work/record_tank_sequence_batch_20261031_63.py');save(OUT/'continuation_state.json',state)
 print('Recorded18 temporal samples and1 negative; retained partial cycle')
if __name__=='__main__':main()
