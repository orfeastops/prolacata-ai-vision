from pathlib import Path
import json,hashlib
from datetime import datetime,timezone
b=Path('outputs/tank_transfer_training_v1/dataset_v2/heldout_counting');r=b/'day28_runs';now=datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(p.read_text())
def save(p,q):p.write_text(json.dumps(q,indent=2))
for idx,n,clocks in [(92,4,'11:44:43-11:45:19'),(93,5,'11:45:15-11:46:00'),(94,2,'11:45:45-11:46:10')]:
 d=r/f'clip_{idx:03}'
 with (d/'source.mp4').open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
 assert sha==read(d/'source.json')['sha256']
 save(d/'source_hash_review.json',dict(checked_at=now,sha256=sha,matches_recorded=True,exact_duplicates_in_recorded_sources=[p.parent.name for p in r.glob('clip_*/source.json') if p.parent!=d and read(p).get('sha256')==sha]))
 q=read(d/'review_queue.json');assert not q['automatic_proposals'];q.update(review_status='sampled_visual_review_complete',reviewed_at=now,reviewed_raw_samples=n,reviewed_dense_samples=0,sampling_s=10,manual_reference_exhaustive=False,confirmed_loaded_count=0,manual_observed_loaded_departures=0,aggregation_allowed=False,evidence=['raw_review_10s/sheet_00.jpg'],review_notes=f'Cleaning/handling near conveyor {clocks}. Tanks in room stationary, no sampled room departure. Zero proposals checked; not exhaustive. Outside-room activity excluded.');save(d/'review_queue.json',q)
for folder,n,note in [('boundary_91_92',18,'No exact first-frame match.091 tail11:43:40,092 first11:44:43 andPTS2 clock11:44:51. Recording gap retained.091 departure already classified separately, not counted again.'),('boundary_92_93',11,'093first11:45:15 exactly matches092PTS26.092tail11:45:19,093PTS2 clock11:45:22. Cleaning, no sampled departure.'),('boundary_93_94',16,'094first11:45:45 exactly matches093PTS25 and40(stale tail). Sampled093tail11:45:59;094PTS1.999 clock11:46:02. Cleaning, no sampled departure.')]:
 p=r/folder/'evidence.json';q=read(p);q.update(visual_review_pending=False,reviewed_at=now,visually_reviewed_samples=n,review_notes=note+' No constant offset or gap-free coverage asserted.',aggregation_allowed=False);save(p,q)
p=r/'manual_review_progress.json';q=read(p);assert q['reviewed_raw_samples'] in [1510,1521];q.update(reviewed_clips=[f'clip_{i:03}' for i in list(range(62))+list(range(63,95))],reviewed_raw_samples=1521,reviewed_boundary_samples=449,updated_at=now,note='94 clips sampled:000-061,063-094.092-094 cleaning, no sampled departures.22 block-loaded departures plus1 separate other-material departure. Daily total unset;remaining clips and boundary/gap reconciliation pending.');save(p,q)
p=b/'review.html';h=p.read_text(encoding='utf-8').replace('91 αποσπάσματα: 1510 αραιά δείγματα και 931 πυκνότερα δείγματα','94 αποσπάσματα: 1521 αραιά δείγματα και 931 πυκνότερα δείγματα');marker='<!-- review092094 -->'
if marker not in h:h=h.replace('<a href="day28_runs/manual_review_progress.json">',marker+'<p>Clips092–094:11 αραιά δείγματα καθαρισμού χωρίς παρατηρημένη έξοδο. Ελέγχθηκαν45 επιπλέον δείγματα ορίων, με κενό091–092 και επαναλαμβανόμενα πρώτα καρέ092–093 και093–094. Συνολικά94 αποσπάσματα,1521 αραιά,931 πυκνά και449 δείγματα ορίων. Παραμένουν22 φορτωμένες έξοδοι και μία χωριστή έξοδος άλλου ορατού υλικού, χωρίς ημερήσιο άθροισμα.</p><a href="day28_runs/manual_review_progress.json">')
p.write_text(h,encoding='utf-8');print('Saved94 clips;1521 coarse;931 dense;449 boundary;counts unchanged.')
