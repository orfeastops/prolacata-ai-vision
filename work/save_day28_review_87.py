from pathlib import Path
import json,hashlib
from datetime import datetime,timezone
b=Path('outputs/tank_transfer_training_v1/dataset_v2/heldout_counting');r=b/'day28_runs';d=r/'clip_087';now=datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(p.read_text())
def save(p,q):p.write_text(json.dumps(q,indent=2))
with (d/'source.mp4').open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
assert sha==read(d/'source.json')['sha256']
save(d/'source_hash_review.json',dict(checked_at=now,sha256=sha,matches_recorded=True,exact_duplicates_in_recorded_sources=[p.parent.name for p in r.glob('clip_*/source.json') if p.parent!=d and read(p).get('sha256')==sha]))
q=read(d/'review_queue.json');assert not q['automatic_proposals'];q.update(review_status='sampled_visual_review_complete',reviewed_at=now,reviewed_raw_samples=14,reviewed_dense_samples=0,sampling_s=10,manual_reference_exhaustive=False,confirmed_loaded_count=0,manual_observed_loaded_departures=0,aggregation_allowed=False,evidence=['raw_review_10s/sheet_00.jpg','raw_review_10s/sheet_01.jpg'],review_notes='Foreground tank stationary with visible white blocks and handling11:10:17-11:12:44. First frame repeats previous footage. No room departure in sampled reference; zero proposals checked, not exhaustive. Outside-room activity not counted.');save(d/'review_queue.json',q)
p=r/'boundary_86_87/evidence.json';q=read(p);q.update(visual_review_pending=False,reviewed_at=now,visually_reviewed_samples=17,review_notes='First087 clock11:10:17 exactly matches086PTS167.604. Sampled086 tail11:10:33;087PTS2 clock11:10:36. Foreground tank with white blocks stays stationary; no boundary departure. No constant offset or gap-free coverage asserted.',aggregation_allowed=False);save(p,q)
p=r/'manual_review_progress.json';q=read(p);assert q['reviewed_raw_samples'] in [1327,1341];q.update(reviewed_clips=[f'clip_{i:03}' for i in list(range(62))+list(range(63,88))],reviewed_raw_samples=1341,reviewed_boundary_samples=337,updated_at=now,note='87 clips sampled:000-061,063-087.062 excluded pre-reviewed fullclip.19 loaded departures;daily total unset;boundary/gap reconciliation incomplete.087 sampled stationary loading and zero proposals.');save(p,q)
p=b/'review.html';h=p.read_text(encoding='utf-8').replace('86 αποσπάσματα: 1327 αραιά δείγματα και 758 πυκνότερα δείγματα','87 αποσπάσματα: 1341 αραιά δείγματα και 758 πυκνότερα δείγματα');marker='<!-- review087 -->'
if marker not in h:h=h.replace('<a href="day28_runs/manual_review_progress.json">',marker+'<p>Clip087:14 επιπλέον αραιά δείγματα δείχνουν γέμισμα χωρίς παρατηρημένη έξοδο. Ελέγχθηκαν17 δείγματα ορίου086–087 (337 συνολικά), με ακριβή αντιστοίχιση πρώτου καρέ. Παραμένουν19 επιβεβαιωμένες φορτωμένες έξοδοι στην πρόσθετη ουρά, χωρίς τελικό ημερήσιο άθροισμα.</p><a href="day28_runs/manual_review_progress.json">')
p.write_text(h,encoding='utf-8');print('Saved87 clips;1341 coarse;758 dense;337 boundary;19 loaded;daily unset.')
