"""Render genuine model outputs and stage an English continuation package."""
import html,json,shutil,zipfile
from pathlib import Path
import cv2,numpy as np
from evaluate_payload_counter_v5 import ROOT,BASE,OUT,CONFIG
from train_transfer_events_v4 import save,load,digest
WEB=BASE/'sequence_annotation_v4/object_model_review'
EXPORT=ROOT/'github_export/payload_training_update_20261029'
SCRIPTS=['prepare_object_expansion_v5.py','object_labels_v5.py','build_object_dataset_v5.py',
    'train_payload_detector_v5.py','evaluate_payload_counter_v5.py','evaluate_september_payload_v5.py',
    'test_payload_counter_v5.py','finalize_payload_v5.py','run_payload_pipeline_v5.py',
    'verify_september_clock_v5.py','query_payload_counts_v5.py']
STYLE='body{font:16px/1.55 system-ui;background:#101822;color:#e9eef5;max-width:1100px;margin:auto;padding:28px}a{color:#83caff}video,img{width:100%;max-width:960px}section{margin:30px 0}.status{padding:18px;border-left:5px solid #d8ad62;background:#242632}table{width:100%;border-collapse:collapse}td,th{padding:9px;border-bottom:1px solid #45515d;text-align:left}summary{cursor:pointer}'
def pending():
    WEB.mkdir(parents=True,exist_ok=True)
    manifest=load(OUT/'dataset_manifest.json');save(WEB/'dataset_summary.json',{k:v for k,v in manifest.items() if k!='rows'})
    for p in (OUT/'box_review').glob('*.jpg'):shutil.copyfile(p,WEB/p.name)
    if (OUT/'training_progress.json').exists():shutil.copyfile(OUT/'training_progress.json',WEB/'training_progress.json')
    examples=''.join(f'<img loading="lazy" src="{p.name}" alt="Assistant training annotations">' for p in sorted(WEB.glob('boxes_*.jpg')))
    page=f'''<!doctype html><html lang="el"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>V5 — Εκπαίδευση ανιχνευτή τυριού</title><style>{STYLE}</style>
<h1>Νέα εκπαίδευση ανιχνευτή τυριού</h1><div class="status" id="progress">Η εκπαίδευση βρίσκεται σε εξέλιξη.</div>
<p>183 εικόνες εκπαίδευσης από 10 αρχεία: 89 με ορατό μεταφερόμενο τυρί και 94 αρνητικά παραδείγματα. Άλλες 53 εικόνες από 3 ξεχωριστά αρχεία χρησιμοποιούνται για έλεγχο. 12 εικόνες είναι ελεγμένα γειτονικά καρέ, όχι 12 ανεξάρτητες μεταφορές.</p>
<p>Εκπαιδεύεται ολόκληρος ο ανιχνευτής YOLO26n. Ακολουθούν δοκιμές στα 12 παλιά αποσπάσματα, στο C02 και στο βίντεο της 26/9. Κανένα από αυτά δεν συμμετέχει στην εκπαίδευση. Δεν υπάρχουν ακόμη νέα αποτελέσματα καταμέτρησης.</p>
<details><summary>Σημειώσεις εκπαίδευσης — δεν είναι προβλέψεις μοντέλου</summary><p>Τα παρακάτω κουτάκια σημειώθηκαν οπτικά από τον βοηθό. q = ποσότητα στο μεταφερόμενο φορτίο, q=0 = άγνωστη ποσότητα. Δεν αποτελούν ποσοστό επιτυχίας.</p>{examples}</details>
<script>async function refresh(){{try{{let r=await fetch('training_progress.json?'+Date.now());if(r.ok){{let p=await r.json();document.getElementById('progress').textContent=`Εκπαίδευση: ${{p.completed_epochs}} / ${{p.total_epochs}} κύκλοι · ${{Math.round(p.elapsed_s/60)}} λεπτά`;}}let done=await fetch('complete.json?'+Date.now());if(done.ok)location.reload();}}catch(e){{}}}}refresh();setInterval(refresh,15000);</script></html>'''
    (WEB/'review.html').write_text(page,encoding='utf-8')
def preview(row):
    result=load(OUT/'predictions'/f"{row['id']}.json");path=WEB/f"{row['id']}.webm"
    if 'native_npz' in row:
        with np.load(row['native_npz']) as z:frames=z['frames'].copy()
    else:frames=[cv2.imread(p) for p in row['image_files']]
    times=np.asarray(row['timestamps']);fps=(len(times)-1)/(times[-1]-times[0])
    writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'VP80'),fps,(640,438));assert writer.isOpened()
    for frame,output in zip(frames,result['frame_outputs']):
        t=output['time_s'];canvas=np.full((438,640,3),(24,18,15),np.uint8);canvas[:360]=frame
        for d in output['detections']:
            x1,y1,x2,y2=map(int,d['bbox']);color=(60,220,100) if d['quantity'] else (40,150,250)
            cv2.rectangle(canvas,(x1,y1),(x2,y2),color,1)
            cv2.putText(canvas,f"#{d['track_id']} q={d['quantity'] or '?'}",(x1,max(12,y1-3)),cv2.FONT_HERSHEY_SIMPLEX,.4,color,1,cv2.LINE_AA)
        ev=[e for e in result['accepted_events'] if e['emitted_at_s']<=t and 0<=e['time_s']<=row['original_end_s']]
        value=sum(e['predicted_quantity'] for e in ev)
        cv2.putText(canvas,f"{row['id']} | {t:.2f}s | MODEL additions: {value}",(8,384),cv2.FONT_HERSHEY_SIMPLEX,.50,(235,235,235),1,cv2.LINE_AA)
        cv2.putText(canvas,'Experimental group tracks; release and quantity may be wrong',(8,409),cv2.FONT_HERSHEY_SIMPLEX,.42,(80,180,255),1,cv2.LINE_AA)
        cv2.putText(canvas,'Counts exclude visible context outside the original clip',(8,430),cv2.FONT_HERSHEY_SIMPLEX,.40,(200,200,200),1,cv2.LINE_AA)
        writer.write(canvas)
    writer.release();cap=cv2.VideoCapture(str(path));n=0
    while True:
        ok,_=cap.read()
        if not ok:break
        n+=1
    cap.release();assert n==len(frames)
    return dict(id=row['id'],path=str(path),verified_native_frames=n)
def complete():
    cv2.setNumThreads(2);WEB.mkdir(parents=True,exist_ok=True);EXPORT.mkdir(parents=True,exist_ok=True)
    training=load(OUT/'training_complete.json');manifest=load(OUT/'dataset_manifest.json')
    result=load(OUT/'count_results.json');sept=load(OUT/'september_results.json');m=result['metrics']
    rows=[r for r in load(BASE/'placement_counter_v4/event_quantity_diagnostic/dataset.json')['rows'] if r['role']!='train']
    videos=[preview(r) for r in rows]
    save(OUT/'preview_verification.json',dict(videos=videos,september_verified_frames=sept['preview_verified_frames']))
    benchmark=[p for p in result['predictions'] if p['reference_count'] is not None]
    table=''.join(f"<tr><td>{p['id']}</td><td>{p['reference_count']}</td><td>{p['accepted_additions']}</td><td>{len(p['unresolved_tracks'])}</td></tr>" for p in benchmark)
    c02=next(p for p in result['predictions'] if p['id']=='C02')
    blocks=sept['predicted_additions_by_tank'];passed=m['positive_exact']>=6 and m['negative_false_counts']==0 and m['mean_absolute_count_error']<=1
    save(WEB/'results.json',dict(training=training,development=result,september=sept))
    sections=''.join(f'<details><summary>{v["id"]} — πραγματικές προβλέψεις</summary><video controls preload="metadata" src="{v["id"]}.webm"></video></details>' for v in videos)
    page=f'''<!doctype html><html lang="el"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>V5 — Αποτελέσματα ανιχνευτή και καταμέτρησης</title><style>{STYLE}</style>
<h1>Αποτελέσματα νέας εκπαίδευσης και καταμέτρησης</h1>
<div class="status">Η εκπαίδευση ολοκληρώθηκε: {training['epochs']} κύκλοι, {training['optimizer_updates']} ενημερώσεις βαρών. Δεν έχει εγκριθεί σύνδεση στις κάμερες.</div>
<p>Εκπαίδευση σε 183 εικόνες από 10 αρχεία, με 94 αρνητικά παραδείγματα. Έλεγχος εικόνων σε 53 εικόνες άλλων 3 αρχείων. Εκπαιδεύτηκε ολόκληρος ο ανιχνευτής και η τελική έκδοση δοκιμάστηκε χωρίς αλλαγή ορίων.</p>
<h2>12 αποσπάσματα με γνωστή μέτρηση</h2><p>Ακριβής μέτρηση στα {m['positive_exact']}/{m['positive_clips']} θετικά αποσπάσματα. Λανθασμένη προσθήκη στα {m['negative_false_counts']}/{m['negative_clips']} αρνητικά. Μέσο απόλυτο σφάλμα: {m['mean_absolute_count_error']:.2f} μπλοκ. Πρόκειται για γνωστό έλεγχο ανάπτυξης από πηγές εκτός εκπαίδευσης, όχι τελικό ποσοστό αξιοπιστίας.</p>
<table><thead><tr><th>Απόσπασμα</th><th>Δική σου μέτρηση</th><th>Πρόβλεψη</th><th>Αβέβαιες διαδρομές</th></tr></thead><tbody>{table}</tbody></table>
<h2>Βίντεο 26/9 — δύο δεξαμενές</h2><p>Πειραματικές προσθήκες: Α = {blocks['A']}, Β = {blocks['B']}. Αβέβαιες διαδρομές: {len(sept['unresolved_tracks'])}. Επεξεργάστηκε {sept['frames_processed']} φυσικά καρέ. Οι αριθμοί αφορούν μόνο προσθήκες μέσα στο βίντεο, όχι τα αρχικά περιεχόμενα.</p>
<p>Τα χρονικά όρια Α/Β παραμένουν χειροκίνητα. Το βίντεο δεν χρησιμοποιήθηκε για εκπαίδευση ή αλλαγή ορίων, αλλά έχει επιθεωρηθεί σε παλιότερες δοκιμές. Δεν έχουμε τεκμηριωμένο ποσοστό επιτυχίας ούτε επιβεβαιωμένο σύνολο δεξαμενής.</p>
<video controls preload="metadata" src="september_two_tanks_v5.webm"></video>
<p>Τα πράσινα κουτάκια είναι πλέον έξοδος του εκπαιδευμένου ανιχνευτή. q = εκτιμώμενα μπλοκ στο ίδιο φορτίο, # = διαδρομή φορτίου. Η καταμέτρηση χρησιμοποιεί κίνηση προς τη δεξαμενή και εξαφάνιση του φορτίου ως πειραματική ένδειξη απόθεσης. Μπορεί να χάσει ή να διπλομετρήσει μεταφορές.</p>
<h2>C02 και υπόλοιπα αποσπάσματα</h2><p>C02: {c02['accepted_additions']} προβλεπόμενες προσθήκες. Οι σημειωμένες εγγραφές περιγράφουν 14 μπλοκ σε 7 μεταφορές, αλλά δεν έχει επιβεβαιωθεί ανεξάρτητο πλήρες σύνολο για όλο το C02.</p>{sections}<p><a href="results.json">Αναλυτικά παγιωμένα αποτελέσματα</a></p></html>'''
    (WEB/'review.html').write_text(page,encoding='utf-8');save(WEB/'complete.json',dict(complete=True))
    table_md='\n'.join(f"| {p['id']} | {p['reference_count']} | {p['accepted_additions']} | {len(p['unresolved_tracks'])} |" for p in benchmark)
    doc=f'''# V5 carried-payload detector and counter — 29 October 2026

The actual detector was fine-tuned for {training['epochs']} epochs, with {training['optimizer_updates']} optimizer updates. Production readiness remains **false**.

## Data and training

The assistant visually screened 276 anchors from 13 distinct October 1/21 source videos, corrected enlarged box overlays and retained 224 anchors. Twelve adjacent native frames passed a strict template check AND visual review. These are not twelve independent transfer events. Training has 183 images (89 positive, 94 negative) from ten source files; source-held-out image validation has 53 images (8 positive, 45 negative) from D03, D07 and D08. Unknown/unreviewed frames were excluded, never automatically labelled as background.

One box encloses a carried load, potentially containing one, two or three blocks. It is not necessarily an individual-block bounding box. Quantity zero in the annotation file means **unknown**, not zero cheese. Quantities are highly imbalanced, with few singles/triples. The boxes are assistant-generated approximations, and only some quantities (notably C01) are expert-confirmed. Assistant-label agreement is not independent production accuracy.

Training starts from generic YOLO26n, updates the complete detector (freeze=0), and uses the fixed last epoch for counting evaluation. The old v4 frozen-feature temporal classifier is not used in the v5 decoder. C02, all historical count-check sources, September 26 and October 3 remain outside optimizer updates. Source hashes and interval overlap checks are preserved.

## Actual count results

Known 12-clip development benchmark: MAE **{m['mean_absolute_count_error']:.3f} blocks**; **{m['positive_exact']}/{m['positive_clips']}** positive clips exactly counted; false accepted additions in **{m['negative_false_counts']}/{m['negative_clips']}** negative clips. These clips have been inspected in earlier work and are not pristine acceptance data. The progression screen {'passed' if passed else 'failed'}; neither outcome authorizes production use.

| Clip | Expert complete count | Model additions | Unresolved tracks |
|---|---:|---:|---:|
{table_md}

C02: {c02['accepted_additions']} additions within the original boundary; seven expert-listed transfers describe fourteen blocks, not an independently exhaustive total. The original complete source was excluded from detector training.

September 26 full two-tank video: **A +{blocks['A']}, B +{blocks['B']}**, {len(sept['unresolved_tracks'])} unresolved tracks, {sept['frames_processed']} native frames across {sept['duration_processed_s']:.2f} seconds. Initial contents are unknown; these are experimental additions only. Preserved manual tank intervals A=[0,289), B=[305,726); tank recognition is not automatic. The user's independent totals have not been disclosed. September was never trained or used for threshold tuning in this run; previous visual diagnostics mean it is not pristine.

## Decoder and limitations

Native-frame detections are associated with short velocity-based one-to-one tracks. A track is a candidate deposit only after observed movement from the pickup corridor into a fixed tank polygon and disappearance for 0.4 seconds. Quantity is a weighted vote of detector classes. Stationary detections, movement toward scraps, unknown quantity and clip-cutoff tracks are not silently counted. **Disappearance is not physical proof of release**. Occlusion, group separation, fragmentation and partial clip boundaries can still cause omissions or duplicates. There are no worker identities, fixed tray totals, fixed tank capacities or live-camera connections.

The seven automated tests verify bookkeeping and geometry invariants, not vision accuracy. All rendered preview frames are decoded again for integrity. Full-frame review videos and camera images stay local; the GitHub package contains code, label/provenance manifests, trained weights, predictions and logs.

## Continue from here

Unpack `payload-training-update-20261029.zip` into the original workspace. Read `dataset_manifest.json`, `counter_frozen_before_test.json`, `count_results.json`, `september_results.json` and the training/config/log files. Use the local review at http://127.0.0.1:8878/object_model_review/review.html. The source files remain under `work/facility_media` and `work/unseen_test_20260926/media`; SHA-256 links identify them. Do not train on the September results, tune thresholds to the hidden tank totals, or report image mAP as block-counting accuracy.

Checkpoint SHA-256: `{training['checkpoint_sha256']}`.
'''
    (EXPORT/'PAYLOAD_TRAINING_RESULT_20261029.md').write_text(doc,encoding='utf-8')
    save(EXPORT/'PAYLOAD_TRAINING_RESULT_20261029.json',dict(training=training,counts=manifest['counts'],development_metrics=m,september=dict(predicted_additions_by_tank=blocks,frames=sept['frames_processed'],unresolved_tracks=len(sept['unresolved_tracks'])),production_ready=False))
    state=load(ROOT/'work/project_handoff/CURRENT_STATE.json')
    state.update(latest_completed_experiment='placement_counter_v5/object_expansion',latest_training_update='2026-10-29',
        production_ready=False,live_cameras_connected=False,v5_training_status='complete',
        latest_source_held_out_mae=m['mean_absolute_count_error'],latest_positive_exact=[m['positive_exact'],m['positive_clips']],
        latest_zero_false_positive=[m['negative_false_counts'],m['negative_clips']],
        next_task='Read PAYLOAD_TRAINING_RESULT_20261029.md, inspect actual detections and tracks, and compare frozen September A/B additions with user totals only after presenting the predictions. Do not tune on test data.',
        v5=dict(checkpoint_sha256=training['checkpoint_sha256'],counts=manifest['counts'],metrics=m,september_additions=blocks,release_detector_is_disappearance_proxy=True))
    save(EXPORT/'CURRENT_STATE.json',state)
    insert=f"## Latest detector experiment: 29 October 2026\n\nRead [PAYLOAD_TRAINING_RESULT_20261029.md](PAYLOAD_TRAINING_RESULT_20261029.md). The complete detector was fine-tuned on 183 images from ten sources, with separate 53-image source validation. Known count-check MAE {m['mean_absolute_count_error']:.3f}, positive exact {m['positive_exact']}/{m['positive_clips']}, false counts in {m['negative_false_counts']}/{m['negative_clips']} negative clips. September experimental additions A +{blocks['A']}, B +{blocks['B']}; manual boundaries and no confirmed user totals. No live deployment. Code, weights, annotations and predictions are in `payload-training-update-20261029.zip`.\n\n"
    for name in ['CLAUDE_HANDOFF.md','README.md','EXPERIMENT_HISTORY.md']:
        src=ROOT/'work/project_handoff'/name
        if not src.exists():src=ROOT/'github_export/prolacata-ai-vision'/name
        original=src.read_text(encoding='utf-8')
        first,rest=original.split('\n',1)
        (EXPORT/name).write_text(first+'\n\n'+insert+rest.lstrip('\n'),encoding='utf-8')
    archive=EXPORT/'payload-training-update-20261029.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for name in SCRIPTS:z.write(ROOT/'work'/name,arcname='work/'+name)
        # Shared utility import is needed by the new scripts.
        z.write(ROOT/'work/train_transfer_events_v4.py',arcname='work/train_transfer_events_v4.py')
        for p in OUT.rglob('*'):
            if not p.is_file() or p.suffix.lower() not in {'.json','.txt','.yaml','.csv','.log','.pt'}:continue
            if 'native' in p.relative_to(OUT).parts or 'attempt_01_callback_error' in p.relative_to(OUT).parts:continue
            if p.suffix=='.pt' and p.name!='last.pt':continue
            z.write(p,arcname=p.relative_to(ROOT).as_posix())
        for p in (OUT/'attempt_01_callback_error').glob('*.json'):z.write(p,arcname=p.relative_to(ROOT).as_posix())
    save(EXPORT/'publication_manifest.json',dict(published=False,files=[dict(name=p.name,bytes=p.stat().st_size,sha256=digest(p)) for p in EXPORT.iterdir() if p.is_file() and p.name!='publication_manifest.json']))
    save(OUT/'pipeline_complete.json',dict(complete=True,published=False,review_url='http://127.0.0.1:8878/object_model_review/review.html',export=str(EXPORT),metrics=m,september_additions=blocks))
if __name__=='__main__':
    import sys
    pending() if '--pending' in sys.argv else complete()
