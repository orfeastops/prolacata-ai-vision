from pathlib import Path
import json, hashlib
from datetime import datetime, timezone
b=Path('outputs/tank_transfer_training_v1/dataset_v2/heldout_counting');r=b/'day28_runs'
now=datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(p.read_text())
def save(p,q):p.write_text(json.dumps(q,indent=2))
for i,n in [(66,6),(67,4),(68,3),(69,4)]:
 d=r/f'clip_{i:03}'
 with (d/'source.mp4').open('rb') as f: sha=hashlib.file_digest(f,'sha256').hexdigest()
 assert sha==read(d/'source.json')['sha256']
 save(d/'source_hash_review.json',dict(checked_at=now,sha256=sha,matches_recorded=True,exact_duplicates_in_recorded_sources=[p.parent.name for p in r.glob('clip_*/source.json') if p.parent!=d and read(p).get('sha256')==sha]))
 q=read(d/'review_queue.json');q.update(review_status='sampled_visual_review_complete',reviewed_at=now,reviewed_raw_samples=n,reviewed_dense_samples=0,sampling_s=10,manual_reference_exhaustive=False,confirmed_loaded_count=0,manual_observed_loaded_departures=0,aggregation_allowed=False,evidence=['raw_review_10s/sheet_00.jpg'],review_notes='Zero automatic proposals reviewed against raw sampled reference. Inbound/repositioned visibly empty tanks toward left stack; no new outbound departure observed. Sparse sampling is not an exhaustive negative reference.'+(' First frame repeats prior clip065 departure at10:18:07; already counted in065, not a new event. Boundary reviewed separately.' if i==66 else ''));save(d/'review_queue.json',q)
p=r/'boundary_65_66/evidence.json';q=read(p);q.update(visual_review_pending=False,reviewed_at=now,visually_reviewed_samples=13,review_notes='First066 clock10:18:07 exactly matches065PTS46.12 and repeats already counted065 departure. Sampled065 tail to10:18:15,066PTS2.04 clock10:18:18. Covered tank outside doorway then empty tanks enter at10:18:30. No additional outbound event in boundary samples. No constant clock offset or gap-free coverage asserted.',aggregation_allowed=False);save(p,q)
p=r/'manual_review_progress.json';q=read(p);assert q['reviewed_raw_samples'] in [1035,1052];q.update(reviewed_clips=[f'clip_{i:03}' for i in list(range(62))+list(range(63,70))],reviewed_raw_samples=1052,reviewed_dense_samples=512,reviewed_boundary_samples=133,observed_loaded_departures=14,updated_at=now,note='69 clips sampled:000-061,063-069.062 excluded pre-reviewed fullclip.14 loaded departures;daily total unset;boundary/gap reconciliation incomplete.');save(p,q)
p=b/'review.html';h=p.read_text(encoding='utf-8').replace('65 αποσπάσματα: 1035 αραιά δείγματα και 512 πυκνότερα δείγματα','69 αποσπάσματα: 1052 αραιά δείγματα και 512 πυκνότερα δείγματα')
marker='<!-- review066_069 -->'
if marker not in h:h=h.replace('<a href="day28_runs/manual_review_progress.json">',marker+'<p>Ελέγχθηκαν 17 επιπλέον αραιά δείγματα στα clip066–069 με μηδενικές προτάσεις: είσοδοι/μετακινήσεις ορατά κενών δεξαμενών, χωρίς νέα έξοδο στα δείγματα. Τα 13 δείγματα ορίου065–066 δείχνουν επανάληψη της ήδη καταμετρημένης εξόδου του065, χωρίς διπλή προσθήκη. Συνολικά133 δείγματα ορίων. Οι14 επιβεβαιωμένες φορτωμένες έξοδοι στην πρόσθετη ουρά παραμένουν μη οριστικοποιημένο ημερήσιο άθροισμα. Η επισκόπηση είναι δειγματοληπτική.</p><a href="day28_runs/manual_review_progress.json">')
p.write_text(h,encoding='utf-8')
print('Saved69 reviewed clips;1052 coarse;512 dense;133 boundary;14 loaded;daily unset.')
