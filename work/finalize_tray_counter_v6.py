"""Publish local evidence for completed v6 development experiments."""
import json,hashlib,shutil,html
from pathlib import Path
from datetime import datetime,timezone
import cv2
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/facility_dataset/temporal_pipeline'
V6=BASE/'placement_counter_v6';SLOT=V6/'slot_probe';ASSOC=V6/'association_experiment'
OUT=BASE/'sequence_annotation_v4/tray_counter_v6_review'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,data):p.write_text(json.dumps(data,indent=2),encoding='utf-8')
def label(v):return {0:'EMPTY',1:'CHEESE',None:'UNCERTAIN'}[v]

def main():
    OUT.mkdir(exist_ok=True);(OUT/'patches').mkdir(exist_ok=True);(OUT/'frames').mkdir(exist_ok=True)
    association=load(ASSOC/'comparison.json');simple=load(SLOT/'results.json');deep=load(SLOT/'generic_encoder_probe/results.json')
    manifest=load(SLOT/'manifest.json');source={r['id']:r for r in manifest['rows']}
    first={r['id']:r for r in simple['rows']};rows=[]
    for r in deep['rows']:
        m=source[r['id']];relative=f"patches/{r['id']}.png"
        shutil.copyfile(m['patch'],OUT/relative)
        rows.append(dict(id=r['id'],frame_id=r['frame_id'],patch=relative,reference=r['reference_class'],
            simple=first[r['id']]['hard_prediction'],simple_qualified=first[r['id']]['predicted_class'],
            deep=r['hard_prediction'],deep_qualified=r['predicted_class'],deep_score=r['maximum_class_score'],
            source_pts_s=m['source_pts_s'],manual_bbox=m['bbox']))
    frame_groups={}
    for r in rows:frame_groups.setdefault(r['frame_id'],[]).append(r)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17)
    for fid,rs in frame_groups.items():
        im=Image.open(source[rs[0]['id']]['image']).convert('RGB');d=ImageDraw.Draw(im)
        for r in rs:
            color='orange' if r['reference'] is None else ('lime' if r['deep']==r['reference'] else 'red')
            d.rectangle(r['manual_bbox'],outline=color,width=2)
            d.text((r['manual_bbox'][0],r['manual_bbox'][1]),r['id'].rsplit('_',1)[1],fill=color,font=font)
        im.save(OUT/'frames'/f'{fid}.jpg',quality=95)
    errors=[r for r in rows if r['reference'] is None or r['deep']!=r['reference']]
    sheet=Image.new('RGB',(max(1,len(errors))*160,210),'#101824');draw=ImageDraw.Draw(sheet)
    for n,r in enumerate(errors):
        x=n*160;sheet.paste(Image.open(OUT/r['patch']).resize((120,140),Image.Resampling.NEAREST),(x+20,65))
        draw.text((x+3,3),r['id'],font=font,fill='white')
        draw.text((x+3,23),'Ref: '+label(r['reference']),font=font,fill='orange')
        draw.text((x+3,43),'Model: '+label(r['deep']),font=font,fill='white')
    sheet.save(OUT/'error_examples.jpg',quality=95)
    data=dict(created_utc=datetime.now(timezone.utc).isoformat(),association=association,
        slot_simple_metrics=simple['metrics'],slot_encoder_metrics=deep['metrics'],rows=rows,
        training_patches=96,training_frames=14,training_sources=1,development_sources=1,
        manual_localization=True,labels_author='assistant visual proposals',human_verified=False,
        automatic_tray_detector=False,automatic_release_detector=False,production_ready=False,
        september_used=False,new_github_publication=False)
    save(OUT/'results.json',data)
    a=association['metrics'];s=simple['metrics'];q=deep['metrics']
    table_rows=''.join(f"<tr><td>{html.escape(r['id'])}</td><td>{r['reference_count'] if r['reference_count'] is not None else 'Not exhaustive'}</td><td>{r['v5_candidate_additions']}</td><td>{r['v6_candidate_additions']}</td></tr>" for r in association['rows'])
    cards=[]
    for r in sorted(rows,key=lambda r:(r['reference'] is not None and r['reference']==r['deep'],r['id'])):
        status='obstructed' if r['reference'] is None else ('match' if r['reference']==r['deep'] else 'error')
        cards.append(f'''<article class="{status}" data-status="{status}"><strong>{r['id']}</strong>
        <a href="frames/{r['frame_id']}.jpg"><img src="{r['patch']}" alt="Original manually cropped tray position {r['id']}"></a>
        <p>Assistant label: <b>{label(r['reference'])}</b><br>Simple model: {label(r['simple'])}<br>YOLO features: <b>{label(r['deep'])}</b></p>
        <small>With abstention: {label(r['deep_qualified'])}<br>Uncalibrated score: {r['deep_score']:.3f}<br>Source time: {r['source_pts_s']:.3f}s</small></article>''')
    page=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Tray counter v6 — actual development results</title><style>
    body{{background:#0b1220;color:#e7edf5;font:16px/1.5 system-ui;margin:0 auto;padding:28px;max-width:1200px}}a{{color:#8bd3ff}}h1{{font-size:28px}}h2{{font-size:22px;margin-top:32px}}
    .notice{{padding:18px;background:#273248;border-left:4px solid #ffce68}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:15px}}article{{padding:15px;background:#152136;border-top:3px solid #56b988;border-radius:7px}}article.error,article.obstructed{{border-top-color:#ff946f}}article img{{display:block;width:144px;height:168px;margin:14px auto;image-rendering:auto}}article p{{margin-bottom:8px}}small{{color:#bccbdc}}table{{border-collapse:collapse;width:100%;margin:20px 0}}td,th{{border-bottom:1px solid #34435a;padding:9px;text-align:left}}button{{background:#234768;color:white;border:1px solid #689ac6;padding:9px 16px;cursor:pointer;margin:0 8px 15px 0}}.wide{{max-width:100%}}</style>
    <h1>Tray counter v6: completed experiments</h1>
    <p>29 October 2026 · October development footage only · <a href="../tray_inventory_review/review.html">20 original tray clips</a> · <a href="REPORT_EN.txt">Full English report</a></p>
    <div class="notice"><b>This is not a working production counter.</b> The tracking change did not improve counting. The appearance models were tested on manually selected and cropped tray positions. Labels are assistant proposals, and repeated patches are not independent events. No September footage or 126/154 totals were used.</div>
    <h2>1. Persistent tracking: no improvement</h2>
    <p>The same saved YOLO detections from {association['native_frames']:,} native frame instances were replayed. Geometry and model weights stayed fixed; association changed. There are 12 scored clips and one additional C02 clip without an exhaustive count.</p>
    <table><tr><th>Measure</th><th>Original v5</th><th>v6 experiment</th></tr>
    <tr><td>Candidate blocks / reference total</td><td>{a['v5']['candidate_sum']} / 53</td><td>{a['v6']['candidate_sum']} / 53</td></tr>
    <tr><td>Exact positive clips</td><td>0 / 7</td><td>0 / 7</td></tr><tr><td>Negative clips with false counts</td><td>0 / 5</td><td>0 / 5</td></tr>
    <tr><td>Mean absolute count error across 12 clips</td><td>{a['v5']['mean_absolute_count_error']:.2f}</td><td>{a['v6']['mean_absolute_count_error']:.2f}</td></tr></table>
    <p><b>Decision: do not replace v5 with this tracker.</b> Longer persistence can also join different transfers. Track disappearance remains an experimental release proxy.</p>
    <details><summary>All clip comparisons</summary><table><tr><th>Clip</th><th>Reference</th><th>v5</th><th>v6</th></tr>{table_rows}</table></details>
    <h2>2. Does a localized position contain cheese?</h2>
    <p>Both models learned from 96 clear crops in 14 frames of one 1 October source file. Evaluation used 48 clear crops and one obstructed challenge in eight frames of a different 21 October source file. Three obstructed training proposals were excluded. The YOLO backbone was frozen; only its small classification head was fitted.</p>
    <table><tr><th>Appearance result</th><th>HOG + colour</th><th>Generic YOLO features</th></tr>
    <tr><td>Matches to assistant labels, all clear slots</td><td>{s['hard_predictions_correct']} / 48</td><td>{q['hard_predictions_correct']} / 48</td></tr>
    <tr><td>Correct among predictions retained at fixed score threshold</td><td>{s['confident_correct']} / {s['confident_slots']}</td><td>{q['confident_correct']} / {q['confident_slots']}</td></tr>
    <tr><td>Abstentions on clear slots</td><td>{s['abstained_slots']} / 48</td><td>{q['abstained_slots']} / 48</td></tr>
    <tr><td>Obstructed challenge incorrectly given a definite state</td><td>1 / 1</td><td>1 / 1</td></tr></table>
    <p>The feature model still made three empty-to-cheese and three cheese-to-empty errors. Four incorrect predictions passed its fixed score threshold. Its score is not a calibrated probability. These figures are <b>not tank-counting accuracy</b>.</p>
    <h2>Actual patch predictions</h2><p>Click a patch to see its manually drawn location in the original frame. Green means agreement with the assistant label; orange marks disagreement or an obstructed challenge. Counts have not been inferred from these crops.</p>
    <button onclick="filter('all')">All 49</button><button onclick="filter('problem')">Errors and obstruction</button>
    <div class="grid">{''.join(cards)}</div>
    <h2>3. Inventory bookkeeping implemented, vision input still missing</h2>
    <p>A new gate checks that multiple loads share one observed tray-removal budget. Relocation on the same tray cannot add production, an empty tray does not imply release, and split releases cannot exceed the supported load. Fifteen software tests passed. These tests validate bookkeeping only.</p>
    <p><b>Remaining integration:</b> automatic tray/slot localization and identity, an explicit occlusion/stack state, and a separately supported tank release. The current appearance probe cannot fill those gaps, so it was not connected to a production total.</p>
    <script>function filter(mode){{document.querySelectorAll('article').forEach(e=>e.hidden=mode==='problem'&&e.dataset.status==='match');}}</script></html>'''
    (OUT/'review.html').write_text(page,encoding='utf-8')
    report=f'''TRAY COUNTER V6 — COMPLETED DEVELOPMENT EXPERIMENTS

Outcome
The association-only change did not improve counting and is not adopted. A real trained appearance classifier using frozen generic YOLO features agreed with 42/48 assistant clear-position labels, versus 39/48 for a simpler appearance baseline. This is an encouraging component result, not a functioning whole-tray or tank counter.

1. Association experiment
Same frozen v5 detector outputs, 3259 native frame instances from 13 October diagnostic clips. Twelve have exhaustive historical reference totals; C02 is not scored.
v5: 28 predicted candidate blocks vs 53 reference; exact positive clips 0/7; negative false-count clips 0/5; MAE 2.0833 over 12 clips.
v6: 24 predicted candidate blocks vs 53 reference; exact positive clips 0/7; negative false-count clips 0/5; MAE 2.4167 over 12 clips.
Positive-only MAE: v5 25/7 = 3.5714; v6 29/7 = 4.1429 blocks.
The v6 configuration was frozen before predictions; no parameter search followed the result. Decoder inputs exclude count references. The inventory gate was not used in this comparison, because no complete model-derived tray inventory or verified release input exists.

2. Appearance probe — actual fitted models
Training: 96 clear, manually localized 48x56 image crops (42 cheese, 54 empty), 14 frames, one 1 October source file. Three obstructed proposals are excluded from fitting.
Development test: 48 clear crops (19 cheese, 29 empty) plus one obstructed challenge, eight frames from one different 21 October source file. Patches share frames and trays; there are not 48 independent production events.
Labels and crop centers were authored and visually reviewed by the assistant. Five off-center evaluation proposals and one off-center training proposal were removed during annotation QA before fitting or predicting. No human verification is claimed.
HOG/colour + regularized logistic head: 39/48 hard-label agreement. 33/38 retained predictions agree, with 10 abstentions; five retained predictions are wrong.
Frozen generic YOLO26n multi-scale features + the same head training settings: 42/48 hard-label agreement. 37/41 retained predictions agree, with seven abstentions; four retained predictions are wrong.
YOLO-feature confusion matrix (rows truth empty/cheese, columns predicted empty/cheese): [[26,3],[3,16]].
Both models emit a definite state for the single obstructed challenge. Neither has demonstrated an adequate occlusion mechanism.
The score threshold 0.8 was fixed before fitting; scores are not calibrated probabilities. No full-tray quantity or tank additions were generated from the appearance probes. YOLO weights were frozen; the logistic head is the trained component. The simple probe was completed first and motivated the feature comparison; this is development model selection, not independent acceptance.
The first attempted OpenCV HOG/RTrees setup could not start because this installed cv2 build lacks HOGDescriptor and ml. No model or predictions were produced by that attempt. The completed baseline uses NumPy HOG and regularized logistic training without installing new packages.

3. Bookkeeping implemented
InventoryGate rejects mismatched or occluded snapshots, overlapping removal budgets, within-tray moves, release without positive destination evidence, repeated release IDs, and additions beyond the supported load quantity. Two simultaneous loads can share one source-removal budget, and split releases retain the remaining quantity. Fifteen software tests pass. Synthetic tests are not video accuracy measurements.

Required before integration
Automatic tray/position localization and stable identity remain unimplemented by the appearance probe. Stacks, clipped positions, gloves and occlusion must remain unknown rather than fabricated counts. A visually supported release signal remains required; disappearance alone is insufficient. Do not substitute the manually supplied crop centers or previous tray quantity proposals for model detections.

Data discipline
Both source files are October development material and have been visually inspected. No September file or 126/154 total entered training, reference scoring, threshold selection or prediction in this work. The prior September set is a known regression set, not pristine acceptance. Fresh full-tank footage remains necessary for later acceptance.
Original v5 artifacts and weights were preserved. New artifacts remain local; no GitHub publication or scheduled training was started.

Reproduction from project root
work/feta_env/Scripts/python.exe work/test_tray_counter_v6.py
work/feta_env/Scripts/python.exe work/evaluate_persistent_tracker_v6.py
work/feta_env/Scripts/python.exe work/prepare_slot_probe_v6.py
work/feta_env/Scripts/python.exe work/label_slot_probe_v6.py
work/feta_env/Scripts/python.exe work/train_slot_probe_v6.py
work/feta_env/Scripts/python.exe work/train_slot_encoder_probe_v6.py
work/feta_env/Scripts/python.exe work/finalize_tray_counter_v6.py
Frozen evaluators/trainers refuse to overwrite completed runs. Do not remove the guards to repeat selection against the same test.

Local review: http://127.0.0.1:8878/tray_counter_v6_review/review.html
'''
    (OUT/'REPORT_EN.txt').write_text(report,encoding='utf-8');(V6/'REPORT_EN.txt').write_text(report,encoding='utf-8')
    verification=dict(source_disjoint=not {r['source_sha256'] for r in manifest['rows'] if r['split']=='train'} &
        {r['source_sha256'] for r in manifest['rows'] if r['split']=='development_test'},
        patch_files_verified=sum(cv2.imread(str(OUT/r['patch'])) is not None for r in rows),
        expected_patch_files=len(rows),software_tests=15,
        model_files={str(p.relative_to(V6)):sha(p) for p in [SLOT/'slot_appearance_linear.npz',SLOT/'generic_encoder_probe/slot_encoder_head.npz']},
        existing_v5_inputs_unchanged=all(sha(BASE/'placement_counter_v5/object_expansion/predictions'/name)==digest
            for name,digest in load(ASSOC/'frozen_before_evaluation.json')['input_files_sha256'].items()),
        no_september_used=True,production_ready=False)
    assert verification['source_disjoint'] and verification['patch_files_verified']==49 and verification['existing_v5_inputs_unchanged']
    save(OUT/'verification.json',verification)
    print(json.dumps(verification,indent=2))

if __name__=='__main__':main()
