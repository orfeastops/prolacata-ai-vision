"""Read-only evaluation aggregation plus review artifacts; no model changes."""
import json,collections,hashlib
from pathlib import Path
import cv2

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/facility_dataset/temporal_pipeline/unseen_test_20260926/object_trajectory_test_v1/opencv_run'

def save(name,data):
    (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

def video_check(path,expected):
    cap=cv2.VideoCapture(str(path));frames=0
    if not cap.isOpened():raise RuntimeError(f'Unreadable preview {path}')
    while True:
        ok,_=cap.read()
        if not ok:break
        frames+=1
    cap.release()
    if frames!=expected:raise RuntimeError(f'Preview length mismatch {path}: {frames}/{expected}')
    return dict(file=str(path),decoded_frames=frames,sha256=hashlib.sha256(path.read_bytes()).hexdigest())

def main():
    dev=json.loads((OUT/'october_development_report.json').read_text())
    test=json.loads((OUT/'september_full_video/frozen_prediction_report.json').read_text())
    frozen=json.loads((OUT/'frozen_config.json').read_text())
    source=ROOT/'work/evaluate_block_trajectories.py'
    runner=ROOT/'work/evaluate_block_trajectories_cv2.py'
    assert hashlib.sha256(source.read_bytes()).hexdigest()==frozen['counter_sha256']
    assert hashlib.sha256(runner.read_bytes()).hexdigest()==frozen['decoder_runner_sha256']
    events=json.loads((OUT/'september_full_video/events_with_manual_tanks.json').read_text())
    reasons=collections.Counter(reason for event in events for reason in event['reasons'])
    checks=[]
    for row in dev['segments']:
        folder=OUT/'october_development'/row['segment_id']
        report=json.loads((folder/'report.json').read_text())
        checks.append(video_check(folder/'trajectory_preview.webm',report['frames_processed']))
    checks.append(video_check(OUT/'september_full_video/trajectory_preview.webm',test['frames_processed']))
    # Extract the known four-block example without new inference or adjustments.
    cap=cv2.VideoCapture(str(OUT/'september_full_video/trajectory_preview.webm'))
    cap.set(cv2.CAP_PROP_POS_FRAMES,126*8)
    short=OUT/'four_block_trajectory_test.webm'
    writer=cv2.VideoWriter(str(short),cv2.VideoWriter_fourcc(*'VP80'),8,(640,420))
    assert writer.isOpened()
    for _ in range(12*8):
        ok,frame=cap.read();assert ok;writer.write(frame)
    writer.release();cap.release();checks.append(video_check(short,96))
    positives=[r for r in dev['segments'] if r['confirmed_deposits']>0]
    negatives=[r for r in dev['segments'] if r['confirmed_deposits']==0]
    event_tracks=[e for e in events if e['first_s']<=133.5 and e['last_s']>=130.0]
    summary=dict(status='evaluation_complete_failed_counting_readiness',
        development=dict(reviewed_segments=len(dev['segments']),positive_segments=len(positives),negative_segments=len(negatives),
            user_confirmed_blocks=dev['confirmed_deposits'],transfer_hypotheses=dev['hypotheses'],
            exact_positive_segments=sum(r['hypotheses']==r['confirmed_deposits'] for r in positives),
            negative_segments_with_false_hypotheses=sum(r['hypotheses']>0 for r in negatives),
            mean_absolute_hypothesis_count_difference=dev['mean_absolute_count_difference'],independent=False),
        september=test,unresolved_reason_counts=dict(reasons),
        known_four_block_example=dict(user_confirmed_blocks=4,approximate_review_interval_s=[130,133.5],
            overlapping_tracks=event_tracks,scope='Approximate timing diagnostic; not dense matched detection ground truth'),
        complete_block_count=None,production_ready=False,model_event_precision=None,model_event_recall=None,
        interpretation='Hypotheses are incomplete proxy outputs, not certified deposits. Unresolved tracks can split/merge and are not numbers of missed blocks.',
        next_method='Annotate and learn complete pickup/carry/release sequences with visible quantities on October sources; validate event counts on separate sources. Preserve September as excluded from fitting.')
    save('evaluation_summary.json',summary);save('video_verification.json',checks)
    a=test['hypotheses_by_manual_tank']['A'];b=test['hypotheses_by_manual_tank']['B'];u=test['unassigned']
    text=f'''ΑΠΟΤΕΛΕΣΜΑ ΔΟΚΙΜΗΣ ΚΑΤΑΜΕΤΡΗΣΗΣ — ΔΕΝ ΠΕΡΑΣΕ

Επεξεργάστηκε ολόκληρο το βίντεο της 26/9: {test['frames_processed']} δειγματοληπτημένα καρέ, {test['duration_processed_s']:.2f} δευτερόλεπτα, στα 8 καρέ/δευτερόλεπτο.
Δεν έγινε εκπαίδευση ή αλλαγή ορίων με δεδομένα της 26/9. Το βίντεο είχε ήδη εξεταστεί σε προηγούμενες δοκιμές, συνεπώς δεν αποτελεί πλέον εντελώς άγνωστο δείγμα.

ΠΡΟΤΑΣΕΙΣ ΤΟΥ ΔΟΚΙΜΑΣΤΙΚΟΥ ΜΕΤΡΗΤΗ
Δεξαμενή Α: {a['hypotheses']} προτάσεις, {a['unresolved_tracks']} άλυτες διαδρομές ανίχνευσης.
Δεξαμενή Β: {b['hypotheses']} προτάσεις, {b['unresolved_tracks']} άλυτες διαδρομές ανίχνευσης.
Εκτός των χειροκίνητων χρονικών ορίων: {u['hypotheses']} προτάσεις, {u['unresolved_tracks']} άλυτες διαδρομές.
Τα παραπάνω ΔΕΝ είναι πραγματικά σύνολα μπλοκ. Μία άλυτη διαδρομή μπορεί να αφορά τμήμα της κίνησης, επαναλαμβανόμενο εντοπισμό, λάθος εντοπισμό ή ομάδα τυριών.
Τα χρονικά όρια Α/Β είναι χειροκίνητα. Μετρώνται μόνο πιθανές προσθήκες κατά τη διάρκεια του βίντεο, όχι το προϋπάρχον περιεχόμενο της Α.

ΕΛΕΓΧΟΣ ΣΤΑ ΗΔΗ ΣΗΜΕΙΩΜΕΝΑ ΒΙΝΤΕΟ ΟΚΤΩΒΡΙΟΥ
12 αποσπάσματα: 7 με τοποθετήσεις, 5 χωρίς τοποθετήσεις.
Γνωστή ποσότητα από τις απαντήσεις σου: 53 μπλοκ.
Αυτόματες προτάσεις μεταφοράς: {dev['hypotheses']}.
Σωστός αριθμός στα αποσπάσματα με τοποθετήσεις: {summary['development']['exact_positive_segments']}/7.
Αποσπάσματα χωρίς τοποθετήσεις με ψευδή πρόταση: {summary['development']['negative_segments_with_false_hypotheses']}/5.
Πρόκειται για έλεγχο ανάπτυξης, με πηγές που εν μέρει χρησιμοποιήθηκαν στην εκπαίδευση, όχι για ανεξάρτητη αξιολόγηση.

ΣΥΜΠΕΡΑΣΜΑ
Η σημερινή σύνδεση εντοπισμού και παρακολούθησης δεν παρέχει αξιόπιστη καταμέτρηση. Οι βελτιώσεις στα κουτάκια δεν έχουν μετατραπεί σε σωστή μέτρηση τοποθετήσεων. Η εξαφάνιση ενός κουτιού μέσα στην περιοχή της δεξαμενής είναι επίσης ανεπαρκής από μόνη της ως απόδειξη τοποθέτησης.
Χρειάζεται αλλαγή του στόχου εποπτείας: πλήρεις διαδρομές παραλαβής–μεταφοράς–τοποθέτησης και πραγματικός αριθμός μπλοκ, με διατήρηση της συνέχειας μεταξύ καρέ. Οι αρχικές και τελικές φάσεις αυτών των διαδρομών δεν καλύπτονται επαρκώς από τις τωρινές ετικέτες μεταφερόμενου τυριού.
Η δοκιμή δεν τεκμηριώνει ποσοστό επιτυχίας ούτε επιτρέπει σύνδεση για αξιόπιστες αναφορές παραγωγής.
'''
    (OUT/'RESULTS_EL.txt').write_text(text,encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
