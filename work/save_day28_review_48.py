from pathlib import Path
import json, hashlib
from datetime import datetime, timezone
b=Path('outputs/tank_transfer_training_v1/dataset_v2/heldout_counting'); r=b/'day28_runs'; d=r/'clip_048'
now=datetime.now(timezone.utc).isoformat()
p=d/'review_queue.json'; q=json.loads(p.read_text())
dense=json.loads((d/'raw_review_2s_230_290/samples.json').read_text())
q.update(review_status='sampled_visual_review_complete',confirmed_loaded_count=1,manual_observed_loaded_departures=1,reviewed_raw_samples=50,sampling_s=10,reviewed_dense_samples=len(dense),dense_sampling_s=2,manual_reference_exhaustive=False,reviewed_at=now,aggregation_allowed=False)
q['evidence']=[f'raw_review_10s/sheet_{i:02}.jpg' for i in range(6)]
q['event_reviews']=[dict(id=1,track=120,pts_s=270.399,visible_clock='08:15:00',decision='visually_confirmed_loaded_departure',content_basis='Visible white blocks placed in foreground tank before covering, followed by sampled pickup and transport to doorway.',fullness_fraction=None,weight_kg=None,overlay_reviewed=True,evidence=['event_001.jpg']+[str(s.relative_to(d)).replace('\\','/') for s in sorted((d/'raw_review_2s_230_290').glob('sheet*.jpg'))])]
q['review_notes']='One loaded departure observed. Replacement empty tank brought forward and subsequently filled. Later tank visible outside door is not counted as another departure from this room. Boundary reconciliation pending.'
p.write_text(json.dumps(q,indent=2),encoding='utf-8')
p=r/'manual_review_progress.json'; q=json.loads(p.read_text());q.update(reviewed_clips=[f'clip_{i:03}' for i in range(49)],reviewed_raw_samples=436,reviewed_dense_samples=54+len(dense),observed_loaded_departures=2,updated_at=now,note='49 clips sampled. Loaded departures confirmed clip043 08:04:02 and clip048 08:15:00. Person false positive clip007. No daily aggregation; exact boundaries pending.');p.write_text(json.dumps(q,indent=2),encoding='utf-8')
actual=hashlib.sha256((d/'source.mp4').read_bytes()).hexdigest(); expected=json.loads((d/'source.json').read_text())['sha256']
(d/'source_hash_review.json').write_text(json.dumps(dict(sha256=actual,matches_recorded=actual==expected,reviewed_at=now),indent=2))
p=b/'review.html';h=p.read_text(encoding='utf-8');h=h.replace('Ελέγχθηκαν 48 αποσπάσματα: 386 αραιά δείγματα και 54 πυκνότερα δείγματα',f'Ελέγχθηκαν 49 αποσπάσματα: 436 αραιά δείγματα και {54+len(dense)} πυκνότερα δείγματα')
h=h.replace('Μία φορτωμένη έξοδος επιβεβαιώθηκε στο clip043, ώρα εικόνας 08:04:02.','Δύο φορτωμένες έξοδοι επιβεβαιώθηκαν στην πρόσθετη ουρά: clip043 στις 08:04:02 και clip048 στις 08:15:00 (ώρα εικόνας).')
h=h.replace('<a href="day28_runs/manual_review_progress.json">','<p>Στο clip048 ελέγχθηκαν το γέμισμα με λευκά τεμάχια, η κάλυψη και η μεταφορά προς την πόρτα, με πυκνότερη δειγματοληψία ανά 2s και έλεγχο overlay.</p><img src="day28_runs/clip_048/raw_review_2s_230_290/sheet_01.jpg"><img src="day28_runs/clip_048/event_001.jpg"><a href="day28_runs/clip_048/review_queue.json">Τεκμηρίωση 08:15</a> · <a href="day28_runs/manual_review_progress.json">')
p.write_text(h,encoding='utf-8');print('Saved clip048 review; dense samples',len(dense),'hash match',actual==expected)
