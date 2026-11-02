from pathlib import Path
import json,hashlib
from datetime import datetime,timezone
b=Path('outputs/tank_transfer_training_v1/dataset_v2/heldout_counting');r=b/'day28_runs';now=datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(p.read_text())
def save(p,q):p.write_text(json.dumps(q,indent=2))
for i,n in [(74,3),(75,40)]:
 d=r/f'clip_{i:03}'
 with (d/'source.mp4').open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
 assert sha==read(d/'source.json')['sha256']
 save(d/'source_hash_review.json',dict(checked_at=now,sha256=sha,matches_recorded=True,exact_duplicates_in_recorded_sources=[p.parent.name for p in r.glob('clip_*/source.json') if p.parent!=d and read(p).get('sha256')==sha]))
 q=read(d/'review_queue.json');assert not q['automatic_proposals'];q.update(review_status='sampled_visual_review_complete',reviewed_at=now,reviewed_raw_samples=n,reviewed_dense_samples=0,sampling_s=10,manual_reference_exhaustive=False,confirmed_loaded_count=0,manual_observed_loaded_departures=0,aggregation_allowed=False,evidence=[f'raw_review_10s/sheet_{j:02}.jpg' for j in range((n+8)//9)],review_notes=('Foreground tank visibly empty; workers approach10:28:52-10:29:02, no departure seen.' if i==74 else 'Foreground tank initially empty, white blocks visibly placed from conveyor beginning around10:30:19-29 and accumulated through10:35:39. Tank remains foreground throughout sampled reference. No outbound departure observed. Appearance outside doorway around10:32:19 is not a room departure and is not counted. Continuity into076 must be reviewed before linking loading to departure.')+' Zero automatic proposals compared with sampled raw reference, not exhaustive.');save(d/'review_queue.json',q)
p=r/'manual_review_progress.json';q=read(p);assert q['reviewed_raw_samples'] in [1074,1117];q.update(reviewed_clips=[f'clip_{i:03}' for i in list(range(62))+list(range(63,76))],reviewed_raw_samples=1117,updated_at=now,note='75 clips sampled:000-061,063-075.062 excluded pre-reviewed fullclip.14 loaded departures;daily total unset;boundary/gap reconciliation incomplete.075 visible loading awaits link to076.');save(p,q)
p=b/'review.html';h=p.read_text(encoding='utf-8').replace('73 αποσπάσματα: 1074 αραιά δείγματα και 512 πυκνότερα δείγματα','75 αποσπάσματα: 1117 αραιά δείγματα και 512 πυκνότερα δείγματα');marker='<!-- review074_075 -->'
if marker not in h:h=h.replace('<a href="day28_runs/manual_review_progress.json">',marker+'<p>Στα clip074–075 ελέγχθηκαν43 επιπλέον αραιά δείγματα χωρίς νέα έξοδο. Στο075 τεκμηριώνεται τοποθέτηση λευκών τεμαχίων στην μπροστινή δεξαμενή περίπου10:30:19–10:35:39. Η δεξαμενή παραμένει στον χώρο στα δείγματα· η σύνδεση με επόμενη έξοδο εκκρεμεί. Δεν προστέθηκε φορτίο στον μετρητή. Ημερήσιο άθροισμα μη οριστικοποιημένο.</p><a href="day28_runs/manual_review_progress.json">')
p.write_text(h,encoding='utf-8');print('Saved75 clips;1117 coarse;512 dense;150 boundary;14 loaded;daily unset.')
