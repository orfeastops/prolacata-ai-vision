from pathlib import Path
import json
from datetime import datetime,timezone
b=Path('outputs/tank_transfer_training_v1/dataset_v2/heldout_counting');r=b/'day28_runs'
now=datetime.now(timezone.utc).isoformat()
for i in range(11,17):
 d=r/f'clip_{i:03}';p=d/'review_queue.json';q=json.loads(p.read_text());samples=json.loads((d/'raw_review_10s/samples.json').read_text())
 q.update(review_status='sampled_zero_proposal_review_complete',confirmed_loaded_count=0,manual_observed_loaded_departures=0,reviewed_raw_samples=len(samples),sampling_s=10,manual_reference_exhaustive=False,reviewed_at=now,review_notes='Workers open and fit transparent plastic liners into empty bins. Bins repositioned within room; no outbound tank observed in sampled frames. White/translucent liners are not cheese evidence.',evidence=[str(s.relative_to(d)).replace('\\','/') for s in sorted((d/'raw_review_10s').glob('sheet*.jpg'))])
 p.write_text(json.dumps(q,indent=2),encoding='utf-8')
p=r/'manual_review_progress.json';q=json.loads(p.read_text());q.update(reviewed_clips=[f'clip_{i:03}' for i in range(17)],reviewed_raw_samples=192,updated_at=now,note='17 clips sampled visually: first 11 at 5s, clips11-16 at 10s. Clip007 person false positive reviewed at 1s. No loaded departure observed in these clips. Not exhaustive; boundary review and cross-file dedup remain pending.')
p.write_text(json.dumps(q,indent=2),encoding='utf-8')
observations={'reviewed_at':now,'status':'preliminary_clock_overlap_review_not_exact_frame_matching','aggregation_allowed':False,'pairs':[{'clips':[11,12],'observed_clocks':['clip011 sample21 07:07:39','clip012 sample0 07:07:36'],'observation':'Overlapping clock coverage, same bin-lining activity.'},{'clips':[12,13],'observed_clocks':['clip012 sample1 07:07:52','clip013 sample0 07:07:46'],'observation':'Overlapping clock coverage, same bin-lining activity.'},{'clips':[13,14],'observed_clocks':['clip013 sample1 07:08:14','clip014 sample0 07:08:11'],'observation':'Overlapping clock coverage, same bin-lining activity.'},{'clips':[15,16],'observed_clocks':['clip015 sample1 07:12:04','clip016 sample0 07:11:57'],'observation':'Overlapping clock coverage, same bin-lining activity.'}],'limitations':'Coarse samples establish clock overlap, not exact overlap boundaries or frame-level identity. Filename plus PTS is unreliable due to initial clock jumps. No count summed.'}
(r/'boundary_review_11_16.json').write_text(json.dumps(observations,indent=2),encoding='utf-8')
p=b/'review.html';h=p.read_text(encoding='utf-8');h=h.replace('137 δείγματα από τα πρώτα 11 αρχεία','192 δείγματα από τα πρώτα 17 αρχεία (ανά 5s στα πρώτα 11, ανά 10s στα επόμενα 6)')
h=h.replace('</section></html>','<p>Στα αρχεία 11–16 συνεχίζεται η τοποθέτηση πλαστικών επενδύσεων. Ελέγχθηκαν ενδεικτικά τα ρολόγια στα διαδοχικά αρχεία και καταγράφηκαν επικαλύψεις· η ακριβής αντιστοίχιση καρέ στα όρια εκκρεμεί. <a href="day28_runs/boundary_review_11_16.json">Παρατηρήσεις ορίων</a></p></section></html>')
p.write_text(h,encoding='utf-8');print('Saved 55 newly reviewed samples; cumulative 192 coarse + 33 dense, 17 clips. No aggregation.')
