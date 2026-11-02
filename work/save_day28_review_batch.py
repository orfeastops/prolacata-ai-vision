from pathlib import Path
import json,re
from datetime import datetime,timezone
b=Path('outputs/tank_transfer_training_v1/dataset_v2/heldout_counting')
r=b/'day28_runs'
now=datetime.now(timezone.utc).isoformat()
notes={5:'Workers place plastic liners in stationary empty bins. No loaded departure observed.',6:'Workers prepare empty bins with plastic liners; liners are not evidence of cheese. No loaded departure observed.',7:'Person walks towards and through doorway; stationary lined bins. Automatic event 1 labels person as tank. Reviewed overlay and all 33 one-second samples; no tank accompanies the person.',8:'People enter and walk through room; lined bins stationary. No loaded departure observed.',9:'Person crosses room towards rear work area; lined bins stationary. No loaded departure observed.',10:'Person crosses room towards foreground; lined bins stationary. No loaded departure observed.'}
for i,n in notes.items():
 d=r/f'clip_{i:03}'
 q=json.loads((d/'review_queue.json').read_text())
 q.update(review_status='sampled_visual_review_complete',confirmed_loaded_count=0,manual_observed_loaded_departures=0,reviewed_raw_samples=len(json.loads((d/'raw_review/samples.json').read_text())),sampling_s=5,manual_reference_exhaustive=False,review_notes=n,reviewed_at=now)
 q['evidence']=[str(p.relative_to(d)).replace('\\','/') for p in sorted((d/'raw_review').glob('sheet_*.jpg'))]
 if i==7:
  q['reviewed_dense_samples']=33
  q['dense_sampling_s']=1
  q['rejected_false_positive_count']=1
  q['event_reviews']=[dict(id=1,track=23,pts_s=19.6,visible_clock='06:58:10',decision='rejected_false_positive_person',confirmed_loaded_departure=False,reason=n,evidence=['event_001.jpg']+[str(p.relative_to(d)).replace('\\','/') for p in sorted((d/'raw_review_1s').glob('sheet_*.jpg'))])]
 (d/'review_queue.json').write_text(json.dumps(q,indent=2),encoding='utf-8')
p=json.loads((r/'manual_review_progress.json').read_text())
p.update(reviewed_clips=[f'clip_{i:03}' for i in range(11)],reviewed_raw_samples=137,reviewed_dense_samples=33,dense_samples_may_overlap_raw=True,observed_loaded_departures=0,rejected_false_positive_count=1,updated_at=now,note='11 clips sampled visually. Clip007 automatic event rejected: person, not tank; overlay and 33 dense samples reviewed. Negative checks are not exhaustive; boundaries and overlaps remain unresolved.',daily_count=None)
(r/'manual_review_progress.json').write_text(json.dumps(p,indent=2),encoding='utf-8')
h=(b/'review.html').read_text(encoding='utf-8')
s='''<section id="day-progress"><h2>Επέκταση στην ημέρα</h2><p>Ελέγχθηκαν οπτικά 137 δείγματα από τα πρώτα 11 αρχεία, και 33 πυκνότερα δείγματα ανά 1s στο clip007 (με επικάλυψη δειγμάτων). Παρατηρήθηκαν προετοιμασία χώρου, πλαστικές επενδύσεις και άδειες δεξαμενές, χωρίς παρατηρημένη φορτωμένη έξοδο σε αυτά τα αρχεία.</p><p>Μία αυτόματη πρόταση στο clip007, PTS19.6s / ρολόι06:58:10, απορρίφθηκε μετά από έλεγχο πρωτότυπης ακολουθίας και overlay: πρόκειται για άνθρωπο που το μοντέλο χαρακτήρισε δεξαμενή. Το αυτόματο αποτέλεσμα διατηρείται αυτούσιο και η απόρριψη καταγράφεται χωριστά. Δεν άλλαξαν μοντέλο ή thresholds.</p><img src="day28_runs/clip_007/event_001.jpg"><p>Οι αρνητικοί έλεγχοι είναι δειγματοληπτικοί. Όρια αρχείων, επικαλύψεις και κενά παραμένουν προς έλεγχο. Η σειριακή επεξεργασία συνεχίζεται· δεν υπάρχει ημερήσιο σύνολο.</p><a href="day28_runs/manual_review_progress.json">Πρόοδος χειροκίνητου ελέγχου</a> · <a href="day28_runs/clip_007/review_queue.json">Τεκμηρίωση απόρριψης</a></section>'''
h=re.sub(r'<section id="day-progress">.*?</section>',s,h,flags=re.S)
(b/'review.html').write_text(h,encoding='utf-8')
print('Saved 6 clip reviews; cumulative 11 clips, 137 coarse and 33 dense samples; 1 rejected person proposal.')
