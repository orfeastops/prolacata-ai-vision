# Continue this project with Claude

## Latest model experiment: 28 October 2026

Read [EVENT_TRAINING_RESULT_20261028.md](EVENT_TRAINING_RESULT_20261028.md) before the annotation-only update below. A real training run now used C01 and assistant C03-C06 (50 release entries, 25 negative intervals). C02 and all ten sources of the historical benchmark remained excluded. The source-check count MAE was 5.083, with 2/7 positive clips exact and false counts in 1/5 negative clips. The research screen failed. No live camera connection occurred. The checkpoint, scripts and frozen predictions are preserved in `event-training-update-20261028.zip`.

The owner requested this GitHub handoff specifically to continue with Claude. Preserve the current work, inspect the actual camera footage yourself, and prioritize measurable progress over repeated planning or asking the owner to label every movement.

## Update: 28 October 2026

Read [ASSISTANT_VISUAL_REVIEW_20261028.md](ASSISTANT_VISUAL_REVIEW_20261028.md) and [ASSISTANT_VISUAL_ANNOTATIONS_V4.json](ASSISTANT_VISUAL_ANNOTATIONS_V4.json) before continuing. The assistant has now visually annotated C03-C06: 41 transfer sequences including context, 24 negative intervals, two unresolved cases, and seven sparse carried-block boxes. The small update ZIP preserves the scripts, labels and review page; private evidence media can be regenerated. These are assistant-authored proposals, not new model results or human ground truth. C02 boundary context was also inspected without modifying the human form export.

## Prompt to start the next session

> Continue the feta production vision project in this repository. First read CLAUDE_HANDOFF.md, START_HERE.md, CURRENT_STATE.json, EXPERIMENT_HISTORY.md, ANNOTATION_PROTOCOL.md and DATA_AND_REPRODUCIBILITY.md. Inspect the existing code, checkpoints and numerical failures before selecting a method. The goal is actual whole-block additions per tank and timestamps, followed by tank movement from camera 11 to camera 15. Do not assume fixed quantities per gesture, tray or tank. Extract sequential source frames and short contextual videos yourself, inspect visible cheese during pickup/carry/release, and create draft object/group and temporal labels. Use the saved expert C01/C02 labels as anchors. Ask me only about genuinely unresolved visual/domain ambiguity; do not make me narrate every frame. Distinguish your draft annotations from human-confirmed ground truth and from model predictions. Keep complete source videos grouped in evaluation splits; keep September 26 out of training and October 3 reserved. Demonstrate count accuracy on excluded sources before another full-day run or live deployment. Do not present hand-motion boxes, model-training completion, or fitted training counts as validated production counting. Continue from the preserved artifacts rather than starting over.

## Bring the artifacts into the new environment

1. Clone `https://github.com/orfeastops/prolacata-ai-vision.git` or extract the GitHub source ZIP.
2. Run `python download_snapshot.py`, then `python restore_snapshot.py --verify-only` and `python restore_snapshot.py`.
3. Read the private Kaggle dataset links in DATA_AND_REPRODUCIBILITY.md. Access requires the owner's Kaggle account; raw camera footage is not published on GitHub. If Claude has access to the same Windows machine, use the existing local files instead of downloading them again.
4. Original workspace: `C:/Users/evant/Documents/Codex/2026-10-22/c-users-evant-desktop`. The existing Python environment is `work/feta_env/Scripts/python.exe`. October originals are in `work/facility_media/`; September originals are in `work/unseen_test_20260926/media/`.
5. The review UI runs locally at `http://127.0.0.1:8878/review.html`. For another computer, regenerate the clips from their source hashes and run `work/serve_timed_review.py`. The localhost link does not work remotely by itself.

## Latest feedback, received during publication

The **root** `CURRENT_STATE.json`, `EXPERT_FEEDBACK_C01.json`, `EXPERT_FEEDBACK_C02.json` and `REVIEW_FORM_EXPORT_C02_20261027.json` are the current handoff records. The C02 response arrived after the seven large artifact archives were frozen. C02 is therefore supplied as these additional Git-tracked files, not inside `snapshot-data.zip`. Older copies under restored `work/project_handoff/` are historical and must not overwrite the root records. Do not rerun one-off handoff or feedback generators blindly.

- C01: ten form entries. Eight completed transfers describe 18 blocks within the original clip. The final left-side two-block carry starts at 28.20 seconds and releases at 30.74 and 33.30, both after the original 29.96-second boundary. Three carries explicitly contain three blocks each. A valid drop can occur from above without deep bending. No separately confirmed exhaustive clip total was supplied.
- C02: fourteen form entries. Seven completed positive transfers describe 14 blocks. Six entries describe no-new-block adjustment, tray movement or crumb disposal. A final two-block carry is cut off before its release is visible.
- One C02 entry contains raw quantity `18` while its action and note explicitly describe rearranging cheese already inside the tank. Preserve this inconsistency and inspect the source; do not treat `18` as either a newly deposited quantity or an independently confirmed clip total. The semantic increment for rearrangement is zero, but that conflicting entry is not automatically training-eligible.
- C03–C06 have assistant visual proposals in the October 28 update, with two unresolved cases. They still have no returned expert form labels. Preserve the distinction between assistant proposals and expert-confirmed truth; do not infer zero activity from a missing form row.

## What the next method must improve

The previous v3 count-rate diagnostic fit all 12 training clip totals but only 1 of 7 held-out positive totals exactly after rounding. Its held-out MAE was 2.364 blocks per clip, with false positive totals in 2 of 5 zero-count clips. It used generic frozen YOLO features and a temporal count-rate head, not dependable tracking of individual cheese blocks. The preceding strict object-trajectory approach accepted no complete transfers. Both are failed counting baselines, preserved for diagnosis.

Visible blue gloves and white cheese can guide candidate regions; contact, bending or a hand entering a tank alone is not enough. Follow the actual cheese or a carried group from source tray to destination, preserve group quantity, and account for separate releases without double counting. Some gestures adjust existing cheese or discard crumbs. The footage can support richer visual annotation; assistant-generated labels still need source-level validation rather than being declared correct because another model agrees.

No live cameras are connected. Automatic tank switching, camera 11/15 association, verified camera wall-clock reporting, and production acceptance remain unfinished. The October 28 event model trained on C01; C02 remained source-held-out.
