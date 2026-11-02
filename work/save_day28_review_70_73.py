from pathlib import Path
import json,hashlib
from datetime import datetime,timezone
b=Path('outputs/tank_transfer_training_v1/dataset_v2/heldout_counting');r=b/'day28_runs';now=datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(p.read_text())
def save(p,q):p.write_text(json.dumps(q,indent=2))
for i,n in [(70,6),(71,4),(72,9),(73,3)]:
 d=r/f'clip_{i:03}'
 with (d/'source.mp4').open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
 assert sha==read(d/'source.json')['sha256']
 save(d/'source_hash_review.json',dict(checked_at=now,sha256=sha,matches_recorded=True,exact_duplicates_in_recorded_sources=[p.parent.name for p in r.glob('clip_*/source.json') if p.parent!=d and read(p).get('sha256')==sha]))
 q=read(d/'review_queue.json');assert not q['automatic_proposals'];q.update(review_status='sampled_visual_review_complete',reviewed_at=now,reviewed_raw_samples=n,reviewed_dense_samples=0,sampling_s=10,manual_reference_exhaustive=False,confirmed_loaded_count=0,manual_observed_loaded_departures=0,aggregation_allowed=False,evidence=['raw_review_10s/sheet_00.jpg'],review_notes=('Empty tank repositioned from left stack to foreground at10:22:55-10:23:05; no room departure observed.' if i==70 else 'Foreground and left-stack tanks remain stationary in samples; people move through doorway, no tank departure observed.')+' Zero proposals compared to sampled raw reference; not exhaustive.');save(d/'review_queue.json',q)
p=r/'boundary_72_73/evidence.json';q=read(p);q.update(visual_review_pending=False,reviewed_at=now,visually_reviewed_samples=17,review_notes='Sampled072 tail clock10:26:15-31;073 first10:26:56 thenPTS2 clock10:27:02. No exact decoded first-frame match in searched072 tail. Stationary tanks and people near doorway; no departure in boundary samples. Visible clock gap retained; no continuity or exact gap duration asserted.',aggregation_allowed=False);save(p,q)
p=r/'manual_review_progress.json';q=read(p);assert q['reviewed_raw_samples'] in [1052,1074];q.update(reviewed_clips=[f'clip_{i:03}' for i in list(range(62))+list(range(63,74))],reviewed_raw_samples=1074,reviewed_dense_samples=512,reviewed_boundary_samples=150,observed_loaded_departures=14,updated_at=now,note='73 clips sampled:000-061,063-073.062 excluded pre-reviewed fullclip.14 loaded departures;daily total unset;boundary/gap reconciliation incomplete.');save(p,q)
p=b/'review.html';h=p.read_text(encoding='utf-8').replace('69 αποσπάσματα: 1052 αραιά δείγματα και 512 πυκνότερα δείγματα','73 αποσπάσματα: 1074 αραιά δείγματα και 512 πυκνότερα δείγματα');marker='<!-- review070_073 -->'
if marker not in h:h=h.replace('<a href="day28_runs/manual_review_progress.json">',marker+'<p>Στα clip070–073 εξετάστηκαν22 επιπλέον αραιά δείγματα χωρίς νέα έξοδο. Στο070 μία ορατά κενή δεξαμενή μετακινείται από την αριστερή στοίβα μπροστά. Στο όριο072–073 εξετάστηκαν17 δείγματα: παραμένει κενό μεταξύ ορατών ωρών10:26:31 και10:26:56. Συνολικά150 δείγματα ορίων, χωρίς οριστικοποιημένο ημερήσιο άθροισμα. Η επισκόπηση παραμένει δειγματοληπτική.</p><a href="day28_runs/manual_review_progress.json">')
p.write_text(h,encoding='utf-8');print('Saved73 clips;1074 coarse;512 dense;150 boundary;14 loaded;daily unset.')
