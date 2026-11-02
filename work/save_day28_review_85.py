from pathlib import Path
import json,hashlib
from datetime import datetime,timezone
b=Path('outputs/tank_transfer_training_v1/dataset_v2/heldout_counting');r=b/'day28_runs';d=r/'clip_085';now=datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(p.read_text())
def save(p,q):p.write_text(json.dumps(q,indent=2))
with (d/'source.mp4').open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
assert sha==read(d/'source.json')['sha256']
save(d/'source_hash_review.json',dict(checked_at=now,sha256=sha,matches_recorded=True,exact_duplicates_in_recorded_sources=[p.parent.name for p in r.glob('clip_*/source.json') if p.parent!=d and read(p).get('sha256')==sha]))
q=read(d/'review_queue.json');assert not q['automatic_proposals'];q.update(review_status='sampled_visual_review_complete',reviewed_at=now,reviewed_raw_samples=7,reviewed_dense_samples=0,sampling_s=10,manual_reference_exhaustive=False,confirmed_loaded_count=0,manual_observed_loaded_departures=0,aggregation_allowed=False,evidence=['raw_review_10s/sheet_00.jpg'],review_notes='Foreground tank stationary with visible white blocks and handling11:06:15-11:07:20. No room departure in sampled reference; zero proposals checked, not exhaustive. Outside-room activity not counted. Link to next departure awaits086 review.');save(d/'review_queue.json',q)
p=r/'boundary_84_85/evidence.json';q=read(p);q.update(visual_review_pending=False,reviewed_at=now,visually_reviewed_samples=11,review_notes='First085 clock11:06:15 exactly matches084PTS429.576. Sampled084 tail11:06:19;085PTS2 clock11:06:22. Foreground tank with white blocks stays stationary; no boundary departure. Outside-room tank movement not counted. No constant offset or gap-free coverage asserted.',aggregation_allowed=False);save(p,q)
p=r/'manual_review_progress.json';q=read(p);assert q['reviewed_raw_samples'] in [1301,1308];q.update(reviewed_clips=[f'clip_{i:03}' for i in list(range(62))+list(range(63,86))],reviewed_raw_samples=1308,reviewed_boundary_samples=302,updated_at=now,note='85 clips sampled:000-061,063-085.062 excluded pre-reviewed fullclip.18 loaded departures;daily total unset;boundary/gap reconciliation incomplete.085 sampled stationary loading,086 departure review pending.');save(p,q)
p=b/'review.html';h=p.read_text(encoding='utf-8').replace('84 αποσπάσματα: 1301 αραιά δείγματα και 693 πυκνότερα δείγματα','85 αποσπάσματα: 1308 αραιά δείγματα και 693 πυκνότερα δείγματα');marker='<!-- review085 -->'
if marker not in h:h=h.replace('<a href="day28_runs/manual_review_progress.json">',marker+'<p>Clip085:7 επιπλέον αραιά δείγματα δείχνουν γέμισμα χωρίς παρατηρημένη έξοδο. Ελέγχθηκαν11 δείγματα ορίου084–085 (302 συνολικά), με ακριβή αντιστοίχιση πρώτου καρέ. Παραμένουν18 επιβεβαιωμένες φορτωμένες έξοδοι στην πρόσθετη ουρά, χωρίς τελικό ημερήσιο άθροισμα.</p><a href="day28_runs/manual_review_progress.json">')
p.write_text(h,encoding='utf-8');print('Saved85 clips;1308 coarse;693 dense;302 boundary;18 loaded;daily unset.')
