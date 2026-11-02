from pathlib import Path
import json
from datetime import datetime, timezone

b = Path('outputs/tank_transfer_training_v1/dataset_v2/heldout_counting')
r = b / 'day28_runs'
now = datetime.now(timezone.utc).isoformat()
notes = {
    44: 'White blocks placed into foreground tank; tank remains in room. No loaded departure observed in sampled frames.',
    45: 'Foreground loaded tank remains stationary; workers handle or cover top. No departure observed in sampled frames.',
    46: 'Covered foreground tank remains stationary; workers waiting. No departure observed in sampled frames.',
    47: 'Covered foreground tank remains stationary; workers waiting. No departure observed in sampled frames.',
}
for i, count in [(44,15),(45,5),(46,3),(47,3)]:
    d = r / f'clip_{i:03}'
    p = d / 'review_queue.json'
    q = json.loads(p.read_text())
    q.update(review_status='sampled_visual_review_complete', confirmed_loaded_count=0,
             manual_observed_loaded_departures=0, reviewed_raw_samples=count,
             sampling_s=10, manual_reference_exhaustive=False, reviewed_at=now,
             review_notes=notes[i], aggregation_ready=False,
             evidence=[str(s.relative_to(d)).replace('\\','/') for s in sorted((d/'raw_review_10s').glob('sheet*.jpg'))])
    p.write_text(json.dumps(q,indent=2),encoding='utf-8')
p = r / 'manual_review_progress.json'
q = json.loads(p.read_text())
q.update(reviewed_clips=[f'clip_{i:03}' for i in range(48)], reviewed_raw_samples=386,
         updated_at=now, aggregation_ready=False,
         note='48 clips sampled. One loaded departure confirmed clip043 clock08:04:02; one person false positive clip007. Clips044-047 show filling/covered stationary tank, no further observed departure. No daily aggregation; exact boundary checks pending.')
p.write_text(json.dumps(q,indent=2),encoding='utf-8')
p=b/'review.html'
h=p.read_text(encoding='utf-8').replace('Ελέγχθηκαν 44 αποσπάσματα: 360 αραιά δείγματα','Ελέγχθηκαν 48 αποσπάσματα: 386 αραιά δείγματα')
h=h.replace('Δεν εκτιμήθηκαν βάρος ή ποσοστό πληρότητας.</p>', 'Δεν εκτιμήθηκαν βάρος ή ποσοστό πληρότητας. Στα clip044–047 εξετάστηκαν άλλα 26 δείγματα: γέμισμα και αναμονή της επόμενης δεξαμενής, χωρίς νέα παρατηρημένη έξοδο.</p>')
h=h.replace('Hashes πρώτων 29 πηγών</a>', 'Hashes πρώτων 29 πηγών</a> · <a href="day28_runs/source_hash_audit_029_047.json">Hashes πηγών 029–047 (χωρίς ακριβή διπλότυπα στις πρώτες 48)</a>')
p.write_text(h,encoding='utf-8')
print('Saved 48 reviewed clips, 386 coarse samples, 54 dense samples; daily count unset.')
