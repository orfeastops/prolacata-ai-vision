"""Publish the completed, frozen v7 run locally; never retrain or rescore it."""
import html
import json
import shutil
from pathlib import Path

import cv2
import numpy as np

from build_arrival_detector_v7 import ROOT, OUT, AUDIT, save, digest

REVIEW = ROOT / 'outputs/facility_dataset/temporal_pipeline/sequence_annotation_v4/arrival_counter_v7_review'


def read(name):
    return json.loads((OUT / name).read_text(encoding='utf-8'))


def fmt(value):
    return '\u2014' if value is None else str(value)


def main():
    complete = read('inference_complete.json')
    assert digest(OUT / 'predictions_frozen.json') == complete['prediction_sha256']
    result = read('count_results.json')
    training = read('training_complete.json')
    frozen = read('predictions_frozen.json')
    proposals = [r for r in frozen['records'] if r['status'] == 'automatic_arrival_proposal']
    proposal_frames = {r['frame_index']: r for r in proposals}
    REVIEW.mkdir(parents=True, exist_ok=True)
    (REVIEW / 'automatic').mkdir(exist_ok=True)
    video = Path(complete['preview'])
    cap = cv2.VideoCapture(str(video))
    assert cap.isOpened(), video
    n = 0
    dimensions = set()
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if n in proposal_frames:
            cv2.imwrite(str(REVIEW / 'automatic' / f"tray_{proposal_frames[n]['tray_id']:03d}.jpg"), frame)
        n += 1
        dimensions.add((frame.shape[1], frame.shape[0]))
    cap.release()
    assert n == complete['native_frames'], (n, complete['native_frames'])
    assert dimensions == {(640, 416)}, dimensions
    verification = dict(decoded_frames=n, expected_frames=complete['native_frames'],
                        dimensions=[640, 416], all_frames_decoded=True,
                        constant_preview_fps=15, source_pts_burned_in=True,
                        preview_sha256=digest(video))
    save(OUT / 'preview_verification.json', verification)
    REVIEW.mkdir(parents=True, exist_ok=True)
    (REVIEW / 'snapshots').mkdir(exist_ok=True)
    shutil.copy2(video, REVIEW / video.name)
    for row in result['snapshot_rows']:
        shutil.copy2(row['image'], REVIEW / 'snapshots' / (row['id'] + '.jpg'))
    for name in ['count_results.json', 'predictions_frozen.json', 'training_complete.json',
                 'counter_frozen_before_inference.json', 'preview_verification.json']:
        shutil.copy2(OUT / name, REVIEW / name)

    # Human-readable frozen output. None is missing, never zero.
    am = result['automatic_metrics']
    sm = result['snapshot_metrics']
    lines = [
        'ARRIVING TRAY COUNTER V7 - FROZEN DEVELOPMENT EXPERIMENT',
        '',
        'Task: count visible individual cheese blocks on an arriving tray.',
        'This is an object detector trained from generic YOLO weights, with an experimental tray episode decoder.',
        f"Training: {training['training_images']} images from one October 1 video; {training['epochs']} fixed epochs.",
        f"Validation: {training['validation_images']} images from October 21. Final checkpoint was last.pt, fixed before counting.",
        'Labels are assistant-authored approximate boxes, visually reviewed, not independently expert-verified.',
        'October 21 did not enter optimizer training, but was used for image validation and inspected in prior development.',
        'September 26 and its reference counts were not used in this experiment.',
        '',
        f"Every native October 21 frame processed: {complete['native_frames']}.",
        f"Selected arrival snapshots: {sm['exact']}/{sm['arrivals']} exactly equal the reviewed initial count.",
        f"Snapshot MAE: {sm['mean_absolute_error_on_returned_counts']} blocks over {sm['model_returned_count']} returned counts.",
        f"Automatically associated arrival counts: {am['exact']}/{am['reviewed_arrivals']} exact; {am['no_matched_automatic_count']} have no matched count.",
        f"Automatic proposals over the full video: {am['automatic_records_in_full_video']}; unmatched: {am['unmatched_records_in_full_video']}.",
        'Automatic matching uses a predeclared +/-3 second window around reviewed snapshots, not manually verified event identity.',
        'Unmatched full-video proposals are not all proven false positives: the reviewed arrival schedule covers only part of the source.',
        '',
        'Tray | Reference initial count | Snapshot visible count | Automatically associated count',
    ]
    auto = {r['id']: r for r in result['automatic_rows']}
    for r in result['snapshot_rows']:
        lines.append(f"{r['id']} | {fmt(r['reference_count'])} | {fmt(r['predicted_visible_cheese'])} | {fmt(auto[r['id']]['automatic_count'])}")
    lines.extend([
        '',
        'References: previous assistant visual audit; the seven-block T17 case was user-confirmed. T15 stacking quantity is unknown and excluded.',
        'Ten is tray capacity, not an assumed cheese count. Empty tray positions are separate from cheese.',
        'Selected snapshot counts are not proof of automatic arrival recognition or the original tray load when occluded.',
        'All nine scored arrivals contain either 7 or 10 blocks. Counts 1-6, 8, 9 and empty arrivals remain unvalidated on a separate source.',
        'The decoder requires ten detected positions, so missing or occluded positions can prevent a count. This is a limitation of v7.',
        'Overlapping trays, stacking, early removals, cropped positions and repeated detections remain failure risks.',
        'This is not a production-ready system or an independent acceptance test. Image mAP is not counting accuracy.',
        'No detector threshold, count rule, checkpoint or label was changed after these predictions.',
    ])
    report = '\n'.join(lines) + '\n'
    (OUT / 'RESULTS_EN.txt').write_text(report, encoding='utf-8')
    (REVIEW / 'RESULTS_EN.txt').write_text(report, encoding='utf-8')

    table_rows = []
    cards = []
    tiles = []
    for r in result['snapshot_rows']:
        ident = r['id']
        a = auto[ident]
        label = 'Unscored: stacking' if r['reference_count'] is None else ('Exact snapshot' if r['exact_snapshot'] else 'Snapshot mismatch')
        css = 'neutral' if r['reference_count'] is None else ('good' if r['exact_snapshot'] else 'bad')
        table_rows.append(f"<tr><td><a href='#{ident}'>{ident}</a></td><td>{r['time_s']:.3f}s</td><td>{fmt(r['reference_count'])}</td><td class='{css}'>{fmt(r['predicted_visible_cheese'])}</td><td>{fmt(a['automatic_count'])}</td></tr>")
        cards.append(f"""<article id='{ident}'><h2>{ident} <span class='{css}'>{label}</span></h2>
        <a href='snapshots/{ident}.jpg'><img loading='lazy' src='snapshots/{ident}.jpg' alt='{ident}: actual model detections at {r['time_s']:.3f} seconds'></a>
        <p>Reviewed arrival load: <b>{fmt(r['reference_count'])}</b> &middot; model-visible blocks: <b>{fmt(r['predicted_visible_cheese'])}</b> &middot; empty positions: {r['observed_empty']} &middot; obscured: {fmt(r['observed_unknown'])}</p>
        <p>Positions detected: {r['observed_positions']}/10. Associated automatic count: <b>{fmt(a['automatic_count'])}</b> at {fmt(a['automatic_time_s'])}s. Snapshot time was selected manually; it is not input to the model.</p>
        <button onclick='seek({max(0, r['time_s']-2)})'>Play this arrival</button></article>""")
        if a['matched_tray_id'] is not None:
            cards[-1] = cards[-1].replace('</article>', f"<details><summary>Actual frame where automatic count {a['automatic_count']} was recorded ({a['automatic_time_s']:.3f}s)</summary><img loading='lazy' src='automatic/tray_{a['matched_tray_id']:03d}.jpg' alt='Model frame for automatic arrival {a['matched_tray_id']}'></details></article>")
        im = cv2.imread(r['image'])
        tile = np.zeros((448, 640, 3), np.uint8)
        tile[:416] = im
        cv2.putText(tile, f"{ident} reference={fmt(r['reference_count'])} visible={fmt(r['predicted_visible_cheese'])} auto={fmt(a['automatic_count'])}", (8,440), cv2.FONT_HERSHEY_SIMPLEX,.5,(255,255,255),1)
        tiles.append(tile)
    sheet = np.vstack([np.hstack(tiles[i:i+2]) for i in range(0,len(tiles),2)])
    cv2.imwrite(str(OUT / 'snapshot_contact_sheet.jpg'), sheet)
    proposal_tiles = []
    proposal_cards = []
    matched_ids = {r['matched_tray_id']:r['id'] for r in result['automatic_rows'] if r['matched_tray_id'] is not None}
    for r in proposals:
        image_name = f"tray_{r['tray_id']:03d}.jpg"
        tag = matched_ids.get(r['tray_id'], 'Not associated with a scored arrival')
        proposal_cards.append(f"<article><h2>Track {r['tray_id']} · count {r['count']}</h2><p>{html.escape(tag)} · source {r['count_source_time_s']:.3f}s</p><img loading='lazy' src='automatic/{image_name}' alt='Automatic proposal track {r['tray_id']}'><button onclick='seek({max(0,r['frame_index']/15-2)})'>Play proposal</button></article>")
        tile = np.zeros((448,640,3),np.uint8)
        tile[:416] = cv2.imread(str(REVIEW/'automatic'/image_name))
        cv2.putText(tile,f"Track {r['tray_id']} count={r['count']} {matched_ids.get(r['tray_id'],'UNMATCHED')}",(8,440),cv2.FONT_HERSHEY_SIMPLEX,.5,(255,255,255),1)
        proposal_tiles.append(tile)
    if len(proposal_tiles)%2:
        proposal_tiles.append(np.zeros_like(proposal_tiles[0]))
    if proposal_tiles:
        cv2.imwrite(str(OUT/'automatic_contact_sheet.jpg'),np.vstack([np.hstack(proposal_tiles[i:i+2]) for i in range(0,len(proposal_tiles),2)]))
    p = f"""<!doctype html><html lang='en'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
    <title>V7 · Cheese on arriving trays</title><style>
    body{{margin:0;background:#111827;color:#e5e7eb;font:16px/1.5 system-ui,sans-serif}}main{{max-width:1250px;margin:auto;padding:28px}}
    h1{{font-size:32px;line-height:1.15}}h2{{font-size:20px}}a{{color:#93c5fd}}.banner,article{{background:#1e293b;padding:20px;border-radius:12px;margin:18px 0}}.banner{{border-left:4px solid #fbbf24}}
    .metrics{{display:flex;gap:18px;flex-wrap:wrap}}.metric{{background:#1e293b;padding:18px;border-radius:10px;flex:1;min-width:190px}}.metric strong{{font-size:32px;display:block}}
    .good{{color:#86efac}}.bad{{color:#fda4af}}.neutral{{color:#fcd34d}}h2 span{{font-size:14px;margin-left:12px}}
    table{{width:100%;border-collapse:collapse}}td,th{{text-align:left;padding:10px;border-bottom:1px solid #475569}}.scroll{{overflow:auto}}
    .cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:20px}}article{{margin:0}}img,video{{width:100%;height:auto;border-radius:7px}}video{{max-height:650px;background:black}}button{{background:#2563eb;color:white;border:0;border-radius:5px;padding:10px;cursor:pointer}}details{{margin-top:24px}}pre{{white-space:pre-wrap;font:14px/1.6 ui-monospace,monospace}}
    @media(max-width:500px){{main{{padding:14px}}.cards{{grid-template-columns:1fr}}}}
    </style><main><p>FACILITY VISION / DEVELOPMENT EXPERIMENT / V7</p><h1>Count cheese on each arriving tray</h1>
    <p>Green C = cheese, cyan E = empty position, orange ? = obscured position, yellow = tray. Every box below is a saved model prediction.</p>
    <div class='banner'><b>Experimental. The snapshot and automatic arrival results are different checks.</b><br>12 training images from October 1; 2 image-validation frames from October 21. Counting test: all {complete['native_frames']:,} native frames of October 21. These are known development scenes, not an independent acceptance test. References include assistant visual annotations.</div>
    <div class='metrics'><div class='metric'>Exact selected snapshots<strong>{sm['exact']} / {sm['arrivals']}</strong>MAE {sm['mean_absolute_error_on_returned_counts']:.2f} blocks across {sm['model_returned_count']} counts</div>
    <div class='metric'>Exact associated automatic arrivals<strong>{am['exact']} / {am['reviewed_arrivals']}</strong>{am['no_matched_automatic_count']} arrivals without a matched count</div>
    <div class='metric'>Video frames verified<strong>{n:,}</strong>All native frames processed; no 4/8 fps inference sampling</div></div>
    <p>No cheese total is forced to 10. Unseen/obscured positions can leave the automatic count unresolved. T15 stacking is unscored. This test does not validate all quantities from 1 to 10.</p>
    <div class='scroll'><table><thead><tr><th>Arrival</th><th>Source time</th><th>Reviewed load</th><th>Visible model count</th><th>Associated automatic count</th></tr></thead><tbody>{''.join(table_rows)}</tbody></table></div>
    <h2>Continuous model output</h2><video id='preview' controls preload='metadata' src='{video.name}'></video>
    <p>Preview retains all source frames at constant 15 fps; the source timestamp in the image is authoritative. {am['automatic_records_in_full_video']} automatic proposals in the full video. The reviewed arrival list covers only part of this video; unmatched proposals are not automatically false positives.</p>
    <div class='cards'>{''.join(cards)}</div><h2>Every automatic proposal, including unmatched ones</h2><p>These are raw experimental outputs. Counting a known arrival correctly does not establish that tray identities or the total number of arrivals are correct.</p><div class='cards'>{''.join(proposal_cards)}</div><details><summary>Method, provenance and limitations</summary><pre>{html.escape(report)}</pre></details>
    <p><a href='count_results.json'>Count results JSON</a> · <a href='predictions_frozen.json'>Frozen predictions</a> · <a href='RESULTS_EN.txt'>English report</a> · <a href='preview_verification.json'>Video verification</a></p>
    <script>function seek(sourceSeconds){{const v=document.getElementById('preview'); v.currentTime=sourceSeconds;v.scrollIntoView({{behavior:'smooth',block:'center'}});v.play();}}</script></main></html>"""
    # Seek buttons use frame index / preview FPS, not the source PTS approximation.
    for r in result['snapshot_rows']:
        p = p.replace(f"seek({max(0, r['time_s']-2)})", f"seek({max(0, r['frame_index']/15-2)})")
    (REVIEW / 'review.html').write_text(p, encoding='utf-8')
    save(OUT / 'review_complete.json', dict(review_path=str(REVIEW/'review.html'),
        url='http://127.0.0.1:8878/arrival_counter_v7_review/review.html',
        frozen_prediction_sha256=digest(OUT/'predictions_frozen.json'),
        complete_native_preview_verified=True,production_ready=False))
    print(json.dumps(dict(snapshot_metrics=sm,automatic_metrics=am,review=str(REVIEW/'review.html')),indent=2))


if __name__ == '__main__':
    main()
