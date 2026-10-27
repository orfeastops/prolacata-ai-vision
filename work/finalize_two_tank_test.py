"""Assemble frozen model predictions with explicitly MANUAL tank-presence intervals.
Never uses the user's hidden counts, never trains or changes any inference rules.
Exit 2 means inference/video encoding has not finished.
"""
import json,pathlib,hashlib,subprocess,sys
import cv2,numpy as np
ROOT=pathlib.Path(__file__).resolve().parents[1]
D=ROOT/'outputs/facility_dataset/temporal_pipeline/unseen_test_20260926/two_tank_counter_v1'
F=ROOT/'outputs/facility_dataset/temporal_pipeline/placement_counter_v1/frozen_blind_run'
PHASES=[dict(tank_id='A',start_s=0,end_s=289,initial_contents='already partly filled; count additions only'),
        dict(tank_id='B',start_s=305,end_s=726,initial_contents='count additions only')]

def assign(event):
    contact=event['tank_contact_s']
    if contact is None:return None
    for phase in PHASES:
        if phase['start_s']<=contact<=event['end_s']<=phase['end_s']:return phase['tank_id']
    return None

def main():
    if not (D/'report.json').exists():print('WAITING: inference report not ready');return 2
    report=json.loads((D/'report.json').read_text())
    cap=cv2.VideoCapture(str(D/'counter_preview.mp4'))
    if not cap.isOpened() or int(cap.get(cv2.CAP_PROP_FRAME_COUNT))!=report['frames']:
        cap.release();print('WAITING: preview not fully encoded');return 2
    cap.set(cv2.CAP_PROP_POS_FRAMES,report['frames']-1);valid,_=cap.read();cap.release()
    if not valid:print('WAITING: final frame unavailable');return 2
    events=json.loads((D/'events.json').read_text())
    for e in events:e['tank_id']=assign(e);e['tank_assignment_basis']='assistant manual scene review; not model prediction'
    counts={k:sum(e['predicted_quantity'] or 0 for e in events if e['tank_id']==k) for k in ['A','B']}
    excluded=[e for e in events if e['predicted_quantity'] is not None and e['tank_id'] is None]
    summary=dict(status='completed_experimental_not_validated',source_sha256=report['source_sha256'],
        frames_processed=report['frames'],duration_processed_s=report['duration_processed_s'],
        predicted_additions_by_tank=counts,unassigned_predicted_deposits=len(excluded),
        unresolved_episodes=report['unresolved_episodes'],
        manual_tank_intervals=PHASES,tank_boundary_precision='approximately 2 seconds; transition intervals left unassigned',
        manual_tank_review_evidence=['change_timeline.jpg','departure_timeline.jpg'],
        model_accuracy=None,user_counts_received=False,training_on_test=False,threshold_tuning_on_test=False,
        exact_tank_totals=None,production_ready=False,
        development_check='On October B019: 10 annotated blocks, 2 model deposit predictions; counting validation failed. This is a diagnostic baseline.',
        model_limitations=['Weak hand/object appearance classifier; stationary cheese near an empty hand can be mistaken for a carried block.',
         'Hand detection misses and track fragmentation cause lost or potentially duplicated events.',
         'Only a one-block-per-hand visual class was trained; no reliable crumbs or hidden multiple-block classification.',
         'Tank intervals are manually supplied, not automatically detected; no live camera integration.'],
        frozen_files={p.name:hashlib.file_digest(p.open('rb'),'sha256').hexdigest() for p in F.iterdir() if p.is_file()})
    (D/'per_tank_events.json').write_text(json.dumps(events,indent=2))
    # This report is the immutable blind prediction, created before user truth.
    (D/'blind_prediction_report.json').write_text(json.dumps(summary,indent=2))
    ff=ROOT/'work/video_decoder/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
    cap=cv2.VideoCapture(str(D/'counter_preview.mp4'));fps=report['configuration']['fps']
    target=D/'two_tanks_preview.mp4'
    encoder=subprocess.Popen([str(ff),'-loglevel','error','-y','-f','rawvideo','-pix_fmt','bgr24','-s','640x460','-r',str(fps),'-i','pipe:0','-an','-c:v','libx264','-preset','veryfast','-crf','23','-pix_fmt','yuv420p',str(target)],stdin=subprocess.PIPE)
    i=0
    try:
        while True:
            ok,frame=cap.read()
            if not ok:break
            t=i/fps;canvas=np.zeros((460,640,3),np.uint8);canvas[:400]=frame
            current={k:sum(e['predicted_quantity'] or 0 for e in events if e['tank_id']==k and e['end_s']<=t) for k in ['A','B']}
            cv2.putText(canvas,f"Tank A additions: {current['A']} | Tank B additions: {current['B']}",(8,423),0,.62,(255,255,255),1)
            cv2.putText(canvas,'EXPERIMENTAL - manual tank split - counts NOT validated',(8,448),0,.44,(0,190,255),1)
            encoder.stdin.write(canvas.tobytes());i+=1
    finally:cap.release();encoder.stdin.close();code=encoder.wait()
    if code or i!=report['frames']:raise RuntimeError('Incomplete comparison preview')
    text=(f"Πειραματική πρόβλεψη προσθηκών: δεξαμενή Α {counts['A']}, δεξαμενή Β {counts['B']}.\n"
          f"Αβέβαιες ακολουθίες: {report['unresolved_episodes']}. Προβλέψεις χωρίς ασφαλή αντιστοίχιση δεξαμενής: {len(excluded)}.\n"
          "Οι αριθμοί ΔΕΝ είναι επιβεβαιωμένη παραγωγή. Η παλιά δοκιμή με 10 σημειωμένα μπλοκ έδωσε μόνο 2 προβλέψεις.\n"
          "Τα χρονικά όρια των δεξαμενών σημειώθηκαν χειροκίνητα. Δεν χρησιμοποιήθηκαν οι κρυφές μετρήσεις του χρήστη.\n"
          "Δεν έγινε εκπαίδευση ή ρύθμιση στα δεδομένα της 26/9.\n")
    (D/'RESULTS_EL.txt').write_text(text,encoding='utf-8')
    (D/'comparison_complete.json').write_text(json.dumps(dict(completed=True,frames=i,preview=str(target),report=str(D/'blind_prediction_report.json')),indent=2))
    print(json.dumps(summary,indent=2));return 0

if __name__=='__main__':sys.exit(main())
