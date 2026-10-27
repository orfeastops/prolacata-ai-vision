"""Present actual excluded-source predictions, preserving the frozen experiment."""
import json
import math
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/facility_dataset/temporal_pipeline/placement_counter_v3'
OUT=BASE/'native_temporal_diagnostic'


def font(size):
    return ImageFont.truetype('C:/Windows/Fonts/arial.ttf',size)


def main():
    result=json.loads((OUT/'results.json').read_text(encoding='utf-8'))
    rows=json.loads((BASE/'interval_supervision.json').read_text(encoding='utf-8'))['segments']
    pred={p['segment_id']:p for p in result['predictions']}
    # Fixed examples cover split releases, three-block pickup and empty-tray motion.
    selected=['N21_05_11_25','N01_05_0_20','N01_04_0_8']
    videos=[]
    cv2.setNumThreads(2)
    for sid in selected:
        row=next(r for r in rows if r['segment_id']==sid)
        p=pred[sid]
        with np.load(BASE/'native_frames'/(sid+'.npz')) as native:
            frames=native['frames']
        with np.load(OUT/(sid+'_held_out.npz')) as output:
            times=output['native_relative_times']
            cumulative=output['increments'].sum(axis=1).cumsum()
        assert len(frames)==len(times)==len(cumulative)
        assert math.isclose(float(cumulative[-1]),p['expected_count'],rel_tol=1e-5)
        target=OUT/(sid+'_held_out_review.webm')
        # Preview has constant playback spacing. Inference used original VFR PTS.
        preview_fps=len(frames)/row['duration_s']
        writer=cv2.VideoWriter(str(target),cv2.VideoWriter_fourcc(*'VP80'),preview_fps,(1000,540))
        if not writer.isOpened():
            raise RuntimeError('VP8 preview writer unavailable')
        max_count=max(2,math.ceil(max(p['expected_count'],p['confirmed_count'])))
        for i,frame in enumerate(frames):
            canvas=Image.new('RGB',(1000,540),(17,24,39));d=ImageDraw.Draw(canvas)
            d.text((18,12),'ΠΡΟΒΛΕΨΗ ΜΟΝΤΕΛΟΥ — ΣΕ ΑΡΧΙΚΟ ΒΙΝΤΕΟ ΕΚΤΟΣ ΕΚΠΑΙΔΕΥΣΗΣ',font=font(21),fill='white')
            d.text((18,46),sid+'  |  χρόνος '+f'{times[i]:.2f}s',font=font(18),fill='#b6c3d1')
            canvas.paste(Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)),(18,87))
            d.text((685,91),'Εκτίμηση μέχρι τώρα',font=font(19),fill='#fbbf24')
            d.text((685,121),f'{cumulative[i]:.2f}',font=font(42),fill='#fbbf24')
            d.text((685,190),'Τελική εκτίμηση: '+f'{p["expected_count"]:.2f}',font=font(21),fill='white')
            d.text((685,227),'Δική σου μέτρηση: '+str(p['confirmed_count']),font=font(21),fill='#7dd3fc')
            d.text((685,265),'Απόκλιση: '+f'{p["absolute_error"]:.2f}',font=font(21),fill='white')
            x0,y0,x1,y1=700,430,970,325
            d.line((x0,y1,x0,y0,x1,y0),fill='#718096',width=1)
            pts=[(x0+(x1-x0)*float(times[k])/row['duration_s'],
                  y0-(y0-y1)*float(cumulative[k])/max_count) for k in range(i+1)]
            if len(pts)>1:d.line(pts,fill='#fbbf24',width=2)
            d.text((700,439),'Αθροιστική εκτίμηση μοντέλου',font=font(15),fill='#fbbf24')
            d.text((18,465),'Ανάλυση όλων των αρχικών καρέ. Η προεπισκόπηση τα προβάλλει με σταθερό ρυθμό.',font=font(17),fill='#b6c3d1')
            d.text((18,493),'Πειραματική εκτίμηση πλήθους· δεν αποτελεί επιβεβαιωμένη καταμέτρηση παραγωγής.',font=font(18),fill='#fca5a5')
            writer.write(cv2.cvtColor(np.asarray(canvas),cv2.COLOR_RGB2BGR))
        writer.release()
        cap=cv2.VideoCapture(str(target));decoded=0;ok,first=cap.read()
        if not ok:raise RuntimeError('Preview does not decode')
        Image.fromarray(cv2.cvtColor(first,cv2.COLOR_BGR2RGB)).save(OUT/(sid+'_preview.png'))
        decoded=1
        while cap.read()[0]:decoded+=1
        cap.release()
        assert decoded==len(frames),(sid,decoded,len(frames))
        videos.append(dict(segment_id=sid,path=str(target),decoded_frames=decoded,
            original_inference_frames=len(frames),playback_fps=preview_fps,
            no_images_deliberately_skipped_or_duplicated=True,
            preview_constant_spacing=True,inference_original_variable_timestamps=True))
    text=[
        'Πειραματικός χρονικός μετρητής — αρχικά καρέ',
        '',
        f'Εκπαιδεύτηκε και ελέγχθηκε σε {result["segments"]} σημειωμένα αποσπάσματα από {result["source_files"]} αρχικά αρχεία.',
        f'Χρησιμοποιήθηκαν {result["native_frames"]} καρέ χωρίς αραίωση, από 1/10 και 21/10. Δεν χρησιμοποιήθηκε η 26/9.',
        'Κάθε πρόβλεψη ελέγχου προέρχεται από εκπαίδευση που εξαιρούσε ολόκληρο το αντίστοιχο αρχικό αρχείο.',
        f'Μέσο απόλυτο σφάλμα: {result["source_held_out_mae"]:.2f} μπλοκ ανά απόσπασμα.',
        f'Ακριβές στρογγυλοποιημένο σύνολο: {result["source_held_out_rounded_exact"]}/{result["segments"]}.',
        f'Στα θετικά: {result["positive_clips_rounded_exact"]}/{result["positive_clips"]}. Ψευδές θετικό σε μηδενικά: {result["negative_clips_false_positive"]}/{result["negative_clips"]}.',
        '',
        'Απόσπασμα | δική σου μέτρηση | εκτίμηση μοντέλου | απόλυτο σφάλμα',
    ]
    for row in rows:
        p=pred[row['segment_id']]
        text.append(f'{p["segment_id"]} | {p["confirmed_count"]} | {p["expected_count"]:.2f} | {p["absolute_error"]:.2f}')
    text += ['',
        'Δεν είναι ποσοστό επιτυχίας ανίχνευσης μπλοκ. Οι δεκαδικές τιμές είναι εκτιμήσεις πλήθους.',
        'Τα χρονικά διαστήματα επισημάνθηκαν από τον βοηθό. Τα συνολικά πλήθη προέρχονται από τις επιβεβαιώσεις σου.',
        'Πρόκειται για έλεγχο ανάπτυξης σε λίγα ήδη εξετασμένα παραδείγματα, όχι νέο τυφλό τεστ.',
        'Η εκπαίδευση και η αρχιτεκτονική άλλαξαν μαζί με τα fps· δεν αποδίδουμε διαφορά μόνο στα fps.',
        'Δεν έχει ολοκληρωθεί αυτόματη αλλαγή δεξαμενής, αντιστοίχιση καμερών ή έλεγχος ζωντανής παραγωγής.',
        'Δεν δηλώνεται έτοιμο για σύνδεση στην παραγωγή.']
    (OUT/'RESULTS_EL.txt').write_text('\n'.join(text),encoding='utf-8')
    (OUT/'preview_verification.json').write_text(json.dumps(videos,indent=2),encoding='utf-8')
    print(json.dumps(dict(videos=len(videos),report=str(OUT/'RESULTS_EL.txt')),ensure_ascii=False))


if __name__=='__main__':main()
