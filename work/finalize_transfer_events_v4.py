"""Render frozen predictions and preserve the research result, without retraining."""
from pathlib import Path
import hashlib
import html
import json
import zipfile
import cv2
import numpy as np
from train_transfer_events_v4 import ROOT,BASE,OUT,REVIEW,load,save,digest

WEB=BASE/'sequence_annotation_v4/event_model_review'
EXPORT=ROOT/'github_export/event_training_update_20261028'

def preview(row,prediction):
    path=WEB/(row['id']+'.webm')
    t=np.asarray(row['timestamps'])
    if 'native_npz' in row:
        with np.load(row['native_npz']) as f:frames=f['frames'].copy()
    else:frames=[cv2.imread(p) for p in row['image_files']]
    fps=(len(t)-1)/(t[-1]-t[0])
    writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'VP80'),fps,(960,650))
    assert writer.isOpened()
    for ts,frame in zip(t,frames):
        canvas=np.full((650,960,3),(24,18,15),np.uint8)
        canvas[0:540]=cv2.resize(frame,(960,540))
        # Only events already emitted by the decoder are shown. Timestamp attribution
        # and delayed emission are separate fields; neither is human release truth.
        accepted=[e for e in prediction['accepted_events'] if e['emitted_at_s']<=ts and 0<=e['time_s']<=row['original_end_s']]
        uncertain=[e for e in prediction['unresolved_events'] if e['emitted_at_s']<=ts]
        count=sum(e['predicted_quantity'] for e in accepted)
        recent=[e for e in accepted if ts-e['emitted_at_s']<1.]
        cv2.putText(canvas,f"{row['id']} | source-relative clip time {ts:.2f}s | MODEL OUTPUT",(14,567),cv2.FONT_HERSHEY_SIMPLEX,.65,(235,235,235),1,cv2.LINE_AA)
        cv2.putText(canvas,f'Accepted additions: {count}    Unresolved episodes: {len(uncertain)}',(14,599),cv2.FONT_HERSHEY_SIMPLEX,.7,(80,220,255),2,cv2.LINE_AA)
        note='Experimental prediction; no verified object boxes or tank total.'
        if recent:note=' | '.join(f"{e['side']} +{e['predicted_quantity']} at {e['time_s']:.2f}s" for e in recent)
        cv2.putText(canvas,note,(14,630),cv2.FONT_HERSHEY_SIMPLEX,.55,(200,200,200),1,cv2.LINE_AA)
        writer.write(canvas)
    writer.release()
    cap=cv2.VideoCapture(str(path));n=0
    while True:
        ok,_=cap.read()
        if not ok:break
        n+=1
    cap.release();assert n==len(t),(row['id'],n,len(t))
    return dict(id=row['id'],frames=n,path=str(path),playback='native frames at average spacing; true original PTS burned in')

def main():
    cv2.setNumThreads(2);WEB.mkdir(parents=True,exist_ok=True);EXPORT.mkdir(parents=True,exist_ok=True)
    result=load(OUT/'results.json');rows=load(OUT/'dataset.json')['rows'];metrics=result['metrics']
    preds=result['predictions'];c02=next(p for p in preds if p['id']=='C02')
    historical=[p for p in preds if p['role']=='historical_source_check']
    pos=[p for p in historical if p['reference_complete_clip_count']>0]
    neg=[p for p in historical if p['reference_complete_clip_count']==0]
    selected=['C02',max(pos,key=lambda p:p['absolute_count_error'])['id'],max(neg,key=lambda p:p['accepted_additions_in_original_clip'])['id']]
    videos=[]
    for ident in selected:
        videos.append(preview(next(r for r in rows if r['id']==ident),next(p for p in preds if p['id']==ident)))
    trs=''.join(f"<tr><td>{html.escape(p['id'])}</td><td>{p['reference_complete_clip_count']}</td><td>{p['accepted_additions_in_original_clip']}</td><td>{p['absolute_count_error']}</td><td>{len(p['unresolved_events'])}</td></tr>" for p in historical)
    sections=''.join(f'<section><h2>{html.escape(v["id"])}</h2><video controls preload="metadata" src="{v["id"]}.webm"></video></section>' for v in videos)
    entries=''.join(f"<tr><td>{e['side']}</td><td>{e['time_s']:.2f}</td><td>{e['emitted_at_s']:.2f}</td><td>{e['predicted_quantity']}</td><td>{', '.join(e['reasons']) or 'accepted'}</td></tr>" for e in sorted(c02['accepted_events']+c02['unresolved_events'],key=lambda e:e['time_s']))
    page=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>V4 event and quantity model — actual held-out results</title>
<style>body{{font:16px/1.55 system-ui;background:#101822;color:#e9eef5;max-width:1120px;margin:auto;padding:28px}}h1{{font-size:30px}}a{{color:#82c9ff}}.status{{padding:20px;background:#302126;border-left:5px solid #ed9b50}}table{{width:100%;border-collapse:collapse;margin:24px 0}}th,td{{border-bottom:1px solid #3b4653;padding:9px;text-align:left}}video{{width:100%;max-width:960px}}section{{margin-top:36px}}code{{color:#aed3ed}}</style>
<h1>V4 event and quantity model</h1><p>28 October 2026 · Frozen predictions · Five October training sources</p>
<div class="status"><strong>Research screen: {'PASSED' if metrics['screen_passed'] else 'FAILED'}. Not approved for live counting.</strong><br>
Historical source check: mean absolute error {metrics['mean_absolute_count_error']:.2f} blocks; {metrics['positive_exact']}/{metrics['positive_clips']} positive clips exact; {metrics['negative_false_counts']}/{metrics['negative_clips']} empty/negative clips received false counts.</div>
<p>The model received images and previous frames, without annotation event windows at inference. Training used 50 release entries and 25 explicit negative intervals. Assistant proposals were weighted below expert labels. Unlabelled time was masked.</p>
<p><strong>C02 was excluded from training:</strong> the model accepted {c02['accepted_additions_in_original_clip']} block additions within the original clip. The expert listed 7 completed transfers describing 14 blocks; no exhaustive independent clip total was confirmed. {c02['expert_event_check']['matched_events']}/7 listed transfers matched a prediction within the declared timing tolerance, and {c02['expert_event_check']['matched_correct_quantity']} of those had the listed quantity. This is not a full-clip accuracy percentage.</p>
<p>Unresolved episodes are displayed separately. An accepted count of zero is not evidence of zero production. The historical benchmark has been inspected in earlier experiments and is a development check. September 26 and October 3 were not used.</p>
<h2>Complete-clip count benchmark</h2><table><thead><tr><th>Clip</th><th>Expert count</th><th>Model accepted</th><th>Absolute error</th><th>Unresolved</th></tr></thead><tbody>{trs}</tbody></table>
{sections}<h2>C02 model event log</h2><table><thead><tr><th>Image side</th><th>Attributed time</th><th>Emission time</th><th>Proposed quantity</th><th>Status</th></tr></thead><tbody>{entries}</tbody></table>
<p><a href="../assistant_visual_review/review.html">Assistant annotation page</a> · <a href="results.json">Full frozen results</a></p></html>'''
    (WEB/'review.html').write_text(page,encoding='utf-8');save(WEB/'results.json',result)
    save(OUT/'preview_verification.json',dict(videos=videos,all_decoded=True))
    table='\n'.join(f"| {p['id']} | {p['reference_complete_clip_count']} | {p['accepted_additions_in_original_clip']} | {len(p['unresolved_events'])} |" for p in historical)
    text=f'''# V4 event and quantity experiment — 28 October 2026

Training completed. Research progression screen **{'passed' if metrics['screen_passed'] else 'failed'}**. Production readiness remains false.

## Result

- Complete-clip October development benchmark: {metrics['mean_absolute_count_error']:.3f} blocks mean absolute error, {metrics['positive_exact']}/{metrics['positive_clips']} positive clips exactly counted, false accepted additions in {metrics['negative_false_counts']}/{metrics['negative_clips']} negative clips.
- C02 (entire original source excluded): {c02['accepted_additions_in_original_clip']} accepted additions within the original clip. The user's listed entries describe 7 completed transfers / 14 blocks, not an independently confirmed exhaustive clip total. Matched {c02['expert_event_check']['matched_events']}/7 listed transfers; {c02['expert_event_check']['matched_correct_quantity']} matched quantities. Unmatched predictions require visual review, not automatic false-positive labels.
- All {result['native_frame_instances']} frame instances were retained; no 8-fps sampling.
- Unresolved episodes are recorded separately; abstention is not verified zero production.

| Clip | Expert complete count | Model accepted additions | Unresolved episodes |
|---|---:|---:|---:|
{table}

## Frozen recipe and limitations

The new head predicts carrying probability, deposit probability and quantities one/two/three. It uses spatial features from the existing generic frozen YOLO26n encoder, backward feature differences, native timestamp differences and causal temporal convolutions. This is a learned event/quantity diagnostic, not verified individual cheese detection or object tracking. Seven sparse annotation boxes were not treated as a complete object dataset.

Training: C01 and assistant C03-C06; five distinct October 1/21 sources, 50 release entries (including the two separately timed releases from C01's final carry), 25 explicit negative intervals. Expert observations have weight 1; assistant proposals have weight 0.5. Unknown gaps and two unresolved assistant cases are masked. Release intervals supervise one positive peak rather than repeating the group count at every frame. No whole-clip total loss is used.

Quantity supervision is imbalanced: five one-block releases, 42 two-block releases and three three-block releases. All three-block training examples come from C01. A classifier always saying two would match 84% of these training quantities while failing the actual task; that is a label-distribution baseline, not measured model accuracy. Quantity scores are uncalibrated softmax outputs.

C02 and all ten original sources of the 12 historical benchmark segments are wholly excluded from training, normalization and optimizer updates. Model checkpoint, script, configuration and dataset hashes were saved before inference. Thresholds and epochs were fixed before results, with no subsequent tuning. The historical benchmark has been inspected before and is not pristine acceptance data. Its short clips have cold-start/cutoff limitations; C02 includes native context before and after the original boundary.

No September 26 or October 3 frames were used. {'The screen passed, but further independent acceptance work remains.' if metrics['screen_passed'] else 'The failed screen does not justify another full September run or live deployment.'} No tank boundaries, cross-camera associations or verified daily production totals were added.

## Reproduce and inspect

```powershell
& work/feta_env/Scripts/python.exe work/test_transfer_events_v4.py
& work/feta_env/Scripts/python.exe work/train_transfer_events_v4.py
& work/feta_env/Scripts/python.exe work/finalize_transfer_events_v4.py
```

The trainer refuses to overwrite an existing completed experiment. Restore its saved artifacts to inspect rather than rerun it. The local review is `http://127.0.0.1:8878/event_model_review/review.html`, served by the existing loopback-only review server. Private media and feature caches remain local; published results and checkpoint do not include camera frames or video. Extract `event-training-update-20261028.zip` at the project root to restore the relative paths.

Seven bookkeeping/causality/file-lock tests passed. Three preview videos were fully decoded after encoding. These checks validate implementation and files, not visual model correctness. A feature-extraction attempt stopped on a transient Windows file-replacement lock; atomic JSON writes now retry, and the preserved feature caches were reused without changing model settings.

Checkpoint SHA-256: `{result['checkpoint_sha256']}`.
'''
    (OUT/'RESULTS_EN.md').write_text(text,encoding='utf-8')
    (EXPORT/'EVENT_TRAINING_RESULT_20261028.md').write_text(text,encoding='utf-8')
    files=[ROOT/'work/train_transfer_events_v4.py',ROOT/'work/test_transfer_events_v4.py',ROOT/'work/finalize_transfer_events_v4.py',ROOT/'work/prepare_event_training_handoff_v4.py',ROOT/'work/audit_transfer_sources_v4.py']
    files.extend(OUT/name for name in ['config.json','dataset.json','results.json','frozen_before_evaluation.json','event_quantity_v4.pt','run.log','RESULTS_EN.md','preview_verification.json'])
    files.extend(OUT.glob('*_predictions.npz'))
    files.extend(OUT.glob('attempt_*.log'))
    files.append(OUT/'source_audit.json')
    files.append(OUT/'supervision_balance.json')
    archive=EXPORT/'event-training-update-20261028.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in files:z.write(p,p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None
    save(EXPORT/'EVENT_TRAINING_RESULT_20261028.json',result)
    save(EXPORT/'package_manifest.json',dict(archive=archive.name,bytes=archive.stat().st_size,sha256=digest(archive),
        members=len(files),camera_media_included=False,published=False))
    print(json.dumps(dict(metrics=metrics,previews=videos,archive_bytes=archive.stat().st_size)),flush=True)

if __name__=='__main__':main()
