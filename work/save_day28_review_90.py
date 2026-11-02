from pathlib import Path
import json,hashlib
from datetime import datetime,timezone
b=Path('outputs/tank_transfer_training_v1/dataset_v2/heldout_counting');r=b/'day28_runs';d=r/'clip_090';now=datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(p.read_text())
def save(p,q):p.write_text(json.dumps(q,indent=2))
with (d/'source.mp4').open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
assert sha==read(d/'source.json')['sha256']
save(d/'source_hash_review.json',dict(checked_at=now,sha256=sha,matches_recorded=True,exact_duplicates_in_recorded_sources=[p.parent.name for p in r.glob('clip_*/source.json') if p.parent!=d and read(p).get('sha256')==sha]))
q=read(d/'review_queue.json');assert not q['automatic_proposals'];q.update(review_status='sampled_visual_review_complete',reviewed_at=now,reviewed_raw_samples=8,reviewed_dense_samples=0,sampling_s=10,manual_reference_exhaustive=False,confirmed_loaded_count=0,manual_observed_loaded_departures=0,aggregation_allowed=False,evidence=['raw_review_10s/sheet_00.jpg'],review_notes='Cleaning/handling near conveyor11:38:46-11:40:07. Tanks stationary, no room departure in sampled reference. Zero proposals checked; not exhaustive. Outside-room activity excluded.');save(d/'review_queue.json',q)
p=r/'boundary_89_90/evidence.json';q=read(p);q.update(visual_review_pending=False,reviewed_at=now,visually_reviewed_samples=18,review_notes='No exact decoded first-frame match in previous tail. Sampled089 tail11:38:44;090first11:38:46,PTS2 clock11:38:59. Tanks stationary, no sampled boundary departure. Unobserved intervals retained; no constant offset or gap-free coverage asserted.',aggregation_allowed=False);save(p,q)
p=r/'manual_review_progress.json';q=read(p);assert q['reviewed_raw_samples'] in [1497,1505];q.update(reviewed_clips=[f'clip_{i:03}' for i in list(range(62))+list(range(63,91))],reviewed_raw_samples=1505,reviewed_boundary_samples=391,updated_at=now,note='90 clips sampled:000-061,063-090.090 zero proposals and no sampled exit.22 loaded departures;daily total unset;remaining clips and boundary/gap reconciliation pending. All160 automatic passes complete.');save(p,q)
p=b/'review.html';h=p.read_text(encoding='utf-8').replace('89 αποσπάσματα: 1497 αραιά δείγματα και 908 πυκνότερα δείγματα','90 αποσπάσματα: 1505 αραιά δείγματα και 908 πυκνότερα δείγματα');marker='<!-- review090 -->'
if marker not in h:h=h.replace('<a href="day28_runs/manual_review_progress.json">',marker+'<p>Clip090:8 αραιά δείγματα καθαρισμού/χειρισμών χωρίς παρατηρημένη έξοδο· ελέγχθηκαν οι μηδενικές προτάσεις.18 επιπλέον δείγματα ορίου089–090, χωρίς ακριβές ταίριασμα πρώτου καρέ. Συνολικά90 αποσπάσματα,1505 αραιά,908 πυκνά και391 δείγματα ορίων. Παραμένουν22 επιβεβαιωμένες φορτωμένες έξοδοι στην πρόσθετη ουρά, χωρίς ημερήσιο άθροισμα.</p><a href="day28_runs/manual_review_progress.json">')
p.write_text(h,encoding='utf-8');print('Saved90;1505 coarse;908 dense;391 boundary;22 loaded.')
