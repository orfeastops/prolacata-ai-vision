# Autonomous visual annotation update — 28 October 2026

The assistant completed the first visual annotation pass on C03-C06 without further narration from the owner. This update supersedes the previous handoff statement that these clips had no assistant annotations. The frozen October 27 release remains unchanged. No model weights or reported model accuracy changed.

Download `assistant-visual-annotation-update-20261028.zip` from this repository. Its SHA-256 is `cc2a4076863ef02aa516eca27c581d46db20bd77fb6035cbe9a407d12c8f49db`. After restoring the original research snapshot, extract this small update into the same workspace:

```powershell
python -m zipfile -e assistant-visual-annotation-update-20261028.zip .
```

The update contains four scripts and seven annotation/review metadata files, retaining their original paths. It contains no camera images or videos. Regenerate the private evidence from the original media using the commands below. Root `ASSISTANT_VISUAL_ANNOTATIONS_V4.json` duplicates the event annotation for direct browsing.

# Assistant visual annotation batch, 28 October 2026

The assistant inspected sequences from C03-C06 and authored **41 transfer sequences**, including transfers outside the original boundaries, and **24 negative intervals**. These are visual annotation proposals, not trained-model predictions and not human-verified ground truth. No new training run occurred.

| Clip | Proposed additions inside original clip | Qualification |
|---|---:|---|
| C03 | 10 plus unresolved | The white object carried from below the conveyor around 6.5-7.5 s is not identified confidently. Two further two-block transfers finish after the original end. |
| C04 | 18 | Includes a two-block carry that starts before the clip. A final two-block carry finishes after the end and is excluded. |
| C05 | 18 | Includes a right-side two-block carry that starts before the clip. A preceding left-side transfer finishes before time zero and is excluded. |
| C06 | 24 plus boundary uncertainty | A further two-block carry has an occluded release window crossing time zero. Attribution of those blocks to the original interval is unresolved. |

These values are proposed clip labels. They do not measure accuracy, full-tank contents, or daily production. Do not fill unresolved cases with zero or force a fixed tray total.

## Files

- `assistant_annotations.json`: event quantities, pickup/deposit intervals, source hashes, original source frame indices, evidence references, provenance, masks and seven sparse carried-block box annotations.
- `review.html`, `review_data.js`, `preview_data.js`: local review page with video, clickable events, evidence frames and unresolved-case filtering.
- `C03/annotated_review.webm` through `C06/annotated_review.webm`: complete cached native-frame contexts with assistant-authored temporal overlays. The displayed subtotal advances at the end of an annotated deposit interval; this is not an inferred exact release frame.
- `object_anchor_examples.jpg`: seven boxes drawn by the assistant on four selected frames. These are sparse evidence anchors, not a dense tracking result or a complete YOLO detection dataset.
- `C02_boundary_supplement.json`: the original expert's cut-off two-block carry completes after the original clip, at an assistant-estimated release interval of 31.4-32.1 seconds. The original human form export remains unchanged.
- `preview_manifest.json`: native frame counts and preview timing. All four videos were decoded after encoding: 571, 572, 572 and 572 frames respectively.

The complete context cache retains every original frame from about -2 to +36.2 seconds. Visual inspection used 0.5-second overview sheets, with 0.1-0.4-second detail sheets for selected movements and boundaries. Not every cached frame was inspected. Time labels refer to original presentation timestamps; the preview uses constant playback spacing. Camera wall-clock timing is not newly verified.

## Reproduce locally

From the original workspace, with the private source footage available:

```powershell
& work/feta_env/Scripts/python.exe work/build_autonomous_review_assets_v4.py
& work/feta_env/Scripts/python.exe work/export_assistant_visual_review_v4.py
& work/feta_env/Scripts/python.exe work/render_assistant_visual_review_v4.py
& work/feta_env/Scripts/python.exe work/serve_timed_review.py
```

Open `http://127.0.0.1:8878/assistant_visual_review/review.html`. If the existing server is already running, reuse it; do not start a second one. Scripts regenerate evidence media from the private originals, while the actual authored observations live in `work/assistant_visual_labels_v4.py`. Running the scripts does not redo visual reasoning or invoke a vision model.

## Training and evaluation boundary

All reviewed sources are October 1 or October 21 training candidates. September 26 and October 3 were untouched. Group entire source videos together when splitting later experiments. Assistant-generated labels must retain their provenance; do not report their agreement with another model as independent accuracy. Unresolved entries are masked from candidate training labels. Sparse boxes omit stationary cheese and must not be treated as fully annotated generic cheese-detector images.

The next implementation should use the visible carried block/group and its destination, with negative examples such as touching without pickup, empty-hand gestures, crumbs, separator sheets and adjustment of existing cheese. This annotation batch adds supervision; it does not repair the failed counters by itself. Verify source-level held-out count performance before processing a full day or connecting live cameras.
