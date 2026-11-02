from pathlib import Path
import json,hashlib
from datetime import datetime,timezone
b=Path('outputs/tank_transfer_training_v1/dataset_v2/heldout_counting');r=b/'day28_runs';now=datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(p.read_text())
def save(p,q):p.write_text(json.dumps(q,indent=2))
for idx,count,clock in [(82,8,'10:56:17-10:57:31'),(83,9,'10:57:27-10:58:56')]:
 d=r/f'clip_{idx:03}'
 with (d/'source.mp4').open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
 assert sha==read(d/'source.json')['sha256']
 save(d/'source_hash_review.json',dict(checked_at=now,sha256=sha,matches_recorded=True,exact_duplicates_in_recorded_sources=[p.parent.name for p in r.glob('clip_*/source.json') if p.parent!=d and read(p).get('sha256')==sha]))
 q=read(d/'review_queue.json');assert not q['automatic_proposals'];q.update(review_status='sampled_visual_review_complete',reviewed_at=now,reviewed_raw_samples=count,reviewed_dense_samples=0,sampling_s=10,manual_reference_exhaustive=False,confirmed_loaded_count=0,manual_observed_loaded_departures=0,aggregation_allowed=False,evidence=['raw_review_10s/sheet_00.jpg'],review_notes=f'Foreground tank stationary with visible white blocks and handling {clock}. No room departure in sampled reference; zero proposals checked, not exhaustive. Outside-room activity not counted.');save(d/'review_queue.json',q)
for folder,count,note in [('boundary_81_82',18,'No exact first-frame match in searched tail. Sampled081 tail10:56:15;082 first10:56:17 thenPTS2 clock10:56:23. Stationary foreground tank with white blocks on both sides; no sampled boundary departure. Unobserved intervals retained.'),('boundary_82_83',13,'First083 clock10:57:27 exactly matches082PTS66. Sampled082 tail10:57:35;083PTS2 clock10:57:38. Foreground tank stationary with white blocks. No boundary departure. No constant offset or gap-free coverage asserted.')]:
 p=r/folder/'evidence.json';q=read(p);q.update(visual_review_pending=False,reviewed_at=now,visually_reviewed_samples=count,review_notes=note,aggregation_allowed=False);save(p,q)
p=r/'manual_review_progress.json';q=read(p);assert q['reviewed_raw_samples'] in [1240,1257];q.update(reviewed_clips=[f'clip_{i:03}' for i in list(range(62))+list(range(63,84))],reviewed_raw_samples=1257,reviewed_boundary_samples=274,updated_at=now,note='83 clips sampled:000-061,063-083.062 excluded pre-reviewed fullclip.17 loaded departures;daily total unset;boundary/gap reconciliation incomplete.082-083 sampled stationary loading and zero proposals.');save(p,q)
p=b/'review.html';h=p.read_text(encoding='utf-8').replace('81 αποσπάσματα: 1240 αραιά δείγματα και 645 πυκνότερα δείγματα','83 αποσπάσματα: 1257 αραιά δείγματα και 645 πυκνότερα δείγματα');marker='<!-- review082083 -->'
if marker not in h:h=h.replace('<a href="day28_runs/manual_review_progress.json">',marker+'<p>Clip082–083:17 επιπλέον αραιά δείγματα δείχνουν γέμισμα χωρίς παρατηρημένη έξοδο. Ελέγχθηκαν31 δείγματα ορίων081–082–083 (274 συνολικά). Ακριβής αντιστοίχιση πρώτου καρέ βρέθηκε στο082–083, όχι στο081–082. Διατηρούνται τα μη παρατηρημένα διαστήματα. Παραμένουν17 επιβεβαιωμένες φορτωμένες έξοδοι στην πρόσθετη ουρά· δεν υπάρχει τελικό ημερήσιο άθροισμα.</p><a href="day28_runs/manual_review_progress.json">')
p.write_text(h,encoding='utf-8');print('Saved83 clips;1257 coarse;645 dense;274 boundary;17 loaded;daily unset.')
