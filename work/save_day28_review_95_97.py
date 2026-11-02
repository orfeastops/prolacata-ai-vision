from pathlib import Path
import json,hashlib
from datetime import datetime,timezone
b=Path('outputs/tank_transfer_training_v1/dataset_v2/heldout_counting');r=b/'day28_runs';now=datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(p.read_text())
def save(p,q):p.write_text(json.dumps(q,indent=2))
for idx,n,clocks in [(95,3,'11:46:05-11:46:38'),(96,2,'11:46:39-11:46:52'),(97,3,'11:46:44-11:47:13')]:
 d=r/f'clip_{idx:03}'
 with (d/'source.mp4').open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
 assert sha==read(d/'source.json')['sha256']
 save(d/'source_hash_review.json',dict(checked_at=now,sha256=sha,matches_recorded=True,exact_duplicates_in_recorded_sources=[p.parent.name for p in r.glob('clip_*/source.json') if p.parent!=d and read(p).get('sha256')==sha]))
 q=read(d/'review_queue.json');assert not q['automatic_proposals'];q.update(review_status='sampled_visual_review_complete',reviewed_at=now,reviewed_raw_samples=n,reviewed_dense_samples=0,sampling_s=10,manual_reference_exhaustive=False,confirmed_loaded_count=0,manual_observed_loaded_departures=0,aggregation_allowed=False,evidence=['raw_review_10s/sheet_00.jpg'],review_notes=f'Cleaning near conveyor {clocks}; no sampled tank departure. Zero proposals checked; not exhaustive. Outside-room activity excluded.');save(d/'review_queue.json',q)
for folder,n,note in [('boundary_94_95',18,'095 first11:46:05 matches094PTS5.119 and18.159(stale tail).094 sampled tail11:46:18;095PTS2.04 clock11:46:20.'),('boundary_95_96',16,'096 first11:46:39 matches095PTS20.84 and23.84(stale tail).095 sampled tail11:46:40;096PTS2 clock11:46:44.'),('boundary_96_97',14,'097 first11:46:44 matches096PTS2.32 and11.36(stale tail).096 sampled tail11:46:52;097PTS2.04 clock11:46:55.')]:
 p=r/folder/'evidence.json';q=read(p);assert len(q['samples'])==n;q.update(visual_review_pending=False,reviewed_at=now,visually_reviewed_samples=n,review_notes=note+' Cleaning, no sampled departure. No constant offset or gap-free coverage asserted.',aggregation_allowed=False);save(p,q)
p=r/'manual_review_progress.json';q=read(p);assert q['reviewed_raw_samples'] in [1521,1529];q.update(reviewed_clips=[f'clip_{i:03}' for i in list(range(62))+list(range(63,98))],reviewed_raw_samples=1529,reviewed_boundary_samples=497,updated_at=now,note='97 clips sampled:000-061,063-097.095-097 cleaning, no sampled departures.22 block-loaded departures plus1 separate other-material departure. Daily total unset; remaining clips and boundary/gap reconciliation pending.');save(p,q)
p=b/'review.html';h=p.read_text(encoding='utf-8').replace('94 αποσπάσματα: 1521 αραιά δείγματα και 931 πυκνότερα δείγματα','97 αποσπάσματα: 1529 αραιά δείγματα και 931 πυκνότερα δείγματα');marker='<!-- review095097 -->'
if marker not in h:h=h.replace('<a href="day28_runs/manual_review_progress.json">',marker+'<p>Clips095–097:8 αραιά δείγματα καθαρισμού χωρίς παρατηρημένη έξοδο. Ελέγχθηκαν48 επιπλέον δείγματα ορίων με επαναλαμβανόμενα πρώτα καρέ. Συνολικά97 αποσπάσματα,1529 αραιά,931 πυκνά και497 δείγματα ορίων. Οι μετρήσεις παραμένουν αμετάβλητες· ημερήσιο άθροισμα εκκρεμεί.</p><a href="day28_runs/manual_review_progress.json">')
p.write_text(h,encoding='utf-8');print('Saved97 clips;1529 coarse;931 dense;497 boundary;counts unchanged.')
