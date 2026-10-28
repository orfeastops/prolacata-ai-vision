# Experiment history and decisions

This is a reconstruction from saved scripts, reports and user corrections. Historical measurements retain their original scope. It is not a claim that all steps produced a deployable model.

## 1. Source consolidation and the physical process

The user provided camera exports, ZIP archives, stills and videos across several dates. The October temporal index contains **1,069 distinct video sources** with **22.117 hours of encoded playback**, covering camera 11 on October 1/3/21 and camera 15 on October 1/3/5/21/22. This indexed subset does not prove that every full day or all ten days mentioned by the user are present. DVR filename intervals sometimes differ from encoded playback duration.

Camera 11 filling, the stationary crumb tank, camera 15 weighing/storage, and the October 22 forklift/pallet-departure scenario were identified by the user. Early visual interpretation incorrectly treated empty camera 15 tanks as full/stored product. The corrected process is recorded in the annotations and must govern future labels.

Main files: `work/unify_facility_data.py`, `work/build_temporal_source_index.py`, `outputs/facility_dataset/media_manifest*.json`, `temporal_pipeline/temporal_media_index.json`.

## 2. Hand/glove detectors and proposal generation

Initial YOLO hand/glove models and Grounding DINO proposals located candidate regions. Proposal quality was inconsistent; bounding boxes were never sufficient proof of whole-block quantity. The user corrected several hand and action interpretations, including the importance of visible loss of raised cheese from trays.

A private Kaggle GPU preparation run produced 3,460 proposal files. The saved transfer report records CRC-verified local retrieval. These are machine proposals and must not be promoted to expert ground truth automatically.

Main files: `build_glove_dataset.py`, `build_hands_v2.py`, `audit_gpu_proposals.py`, `outputs/feta_training/`, `outputs/facility_dataset/annotation_audit/`.

## 3. Temporal pretraining and trimmed action classification

The recorded VideoMAE pretraining run started from random initialization and completed 10 epochs / 13,930 optimizer steps over 1,032 videos and 1,013 photos, with October 3 excluded. The historical Kaggle output was recorded as 1.13 GB. The full remote checkpoint is not present among the local `.pt` files in this snapshot; its notebook/output location is preserved in `REMOTE_ARTIFACTS.json`.

A 76-example supervised action pilot achieved about 0.430 validation macro-F1 and 0.444 test macro-F1. A later frozen `facebook/vjepa2-vitl-fpc16-256-ssv2` comparison classified 18 pretrimmed test clips correctly (macro-F1 1.0). That small test had five whole-block-transfer clips, one separator clip and twelve other/idle clips, based on assistant-reviewed action labels.

**These scores were action-category scores, not the accuracy of block quantities, release events, tanks or continuous live video.**

Main files: `facility_video_pretraining.py`, `train_supervised_facility_actions.py`, `compare_pretrained_facility_actions.py`, `temporal_pipeline/supervised_actions/`.

## 4. September 26 action-window test

The user supplied a separate September 26 export with 154 videos and 154 photos. The action-window test processed all 154 videos and classified 12,748 overlapping windows with zero failed video sources. It did not estimate quantities. Neighboring windows can describe the same movement and must never be summed as events or multiplied by two.

The saved result explicitly has `accuracy: null`, `quantity_prediction: false`, and `tank_counts: null`. Training and threshold tuning were disabled for this test.

Main file: `temporal_pipeline/unseen_test_20260926/test_results.json`.

## 5. Two-tank hand-motion counter: rejected by user

The approximately 13-minute test clip `Camera_11_DVR_20260926142542_20260926143911_94077690.mp4` begins with a partly filled tank, which is removed before filling continues in another tank. Early hand-motion counting produced A=25 and B=34 (59 total), with substantial uncertainty. The user reported both misses and false positives; these totals are not accepted production quantities.

The user identified a concrete failure: both workers pick up two blocks each around 130.62 s and place the four blocks around 132.35–132.39 s. The earlier model failed to account for this correctly. Tank time boundaries were manually marked, not discovered automatically.

The user's true full A/B totals have not been stored as disclosed ground truth in this handoff. Do not invent them or treat old model totals as truth. September footage has now been inspected for diagnosis, so it is no longer a pristine blind acceptance set even though it remains excluded from training.

Main files: `facility_placement_counter.py`, `finalize_two_tank_test.py`, `unseen_test_20260926/two_tank_counter_v1/`.

## 6. Expert corrections and object-oriented attempts

The user reviewed positive and negative October clips and corrected: empty gestures, salting, crumbs, empty-tray handling, simultaneous carries, separate releases, seven-block trays, and occasional three-block pickups. A tray often contains ten blocks, but it is not a guaranteed quantity. A tank often contains 228, but that is not a target or inference rule.

The small individual-block detector series expanded from 8 annotated frames to 43 and then 52 frames. The uncertainty variant has classes for a single block and an unknown-quantity cheese group. It cannot establish how many blocks are in an occluded group or provide complete object identities automatically.

A weak clip-count model with frozen generic features and a linear count-density head was tested on 12 source-grouped clips. Mean absolute error was about 2.89 blocks per clip; it failed, including predicting cheese in empty-tray footage.

Main directories: `sequence_annotation_v2/`, `placement_counter_v2/individual_block_learning_diagnostic/`, `individual_blocks_expanded_v1/`, `carried_cheese_uncertainty_v2/`, `segment_count_probe/`.

## 7. Strict trajectory counter: zero accepted hypotheses

The frozen detector/tracker was evaluated on all 12 October development clips and on the full September test video. The full test sampled 6,418 frames at 8 fps over 802.25 seconds. It accepted zero complete transfer hypotheses and left 363 unresolved tracks. October development contained 53 confirmed blocks and also yielded zero accepted hypotheses.

This was a pipeline failure/abstention. It did **not** mean that no blocks were placed. Frequent problems included missing pickup or tank paths, ambiguous association and unknown group quantity. No training or threshold adjustment was performed on September.

The FFmpeg helper became inaccessible locally. Sequential OpenCV decoding and VP8 WebM writing were used instead. Original HEVC seeks produced reference-frame warnings, so subsequent original-source extraction decoded sequentially from frame zero.

Main directory: `unseen_test_20260926/object_trajectory_test_v1/opencv_run/`.

## 8. Native-frame causal temporal diagnostic: completed, failed

The user challenged the 8-fps sampling choice. It had been a speed compromise without a validated accuracy tradeoff. The next diagnostic preserved all original frames and native timestamps.

Twelve previously reviewed October clips contain 53 blocks in total. Assistant-reviewed release intervals were added without inventing per-frame quantity allocations or physical object IDs. The interval labels contain twenty two-block releases, five one-block releases, one known three-block release, and two quantity-unknown releases whose combined left-side count is five.

The native cache has 2,687 clip-frame instances / 2,643 distinct original frames. Frame indexes are contiguous inside each interval; image-anchor timing alignment passed. Measured rates are approximately 14.86–15.03 fps despite nominal 30-fps metadata.

The model uses frozen generic YOLO spatial features, fixed random projection, backward temporal differences and a causal convolutional count-rate head. Ten leave-one-original-source-out fits were run with fixed settings, plus a final all-source fit. It used no September 26 or October 3 data.

Results: MAE **2.364**, correct rounded positive totals **1/7**, false positives on zero-count clips **2/5**. Training MAE was **0.052**, with **12/12** correct rounded training totals. The discrepancy is evidence of overfitting. A ten-block source-held-out clip was estimated at **1.41**; a seven-block clip was estimated at **6.56**. Neither example by itself is an accuracy guarantee.

All six causality/bookkeeping tests passed. Those tests concern code behavior, not counting performance. The minimum development screen failed, so another full September rerun was not launched.

## 9. Current step: timestamped expert batch C01–C06

Six new, not previously reviewed original October source files were selected across the workday. Each review clip is about 30 seconds, uses every native frame and displays original clip-relative timestamps. A browser review form supports 0.25×/0.5× playback, frame stepping, lift/release buttons, notes and JSON export. Quantities and complete-event coverage remain pending user confirmation.

The next work is richer object/transfer supervision and source-held-out validation, not another claim of successful live counting. English handoff documentation and available local artifacts are being published to the user's GitHub repository to preserve this state.


## 10. First v4 expert response

The user completed the C01 form with ten entries. Three left-side transfers contain three blocks each. Another valid right-side transfer drops two blocks from above without deep bending. One blank quantity field was explicitly resolved as two from the reviewer note, and one no-new-block adjustment was retained as a zero increment. Eight completed rows describe 18 blocks within the original clip. A final two-block row initially appeared unresolved at its boundary. After reviewing an extended native-frame context clip, the user confirmed transfer start at 28.20, arrival above the tank around 30.00, and individual releases at 30.74 and 33.30 seconds. Both releases are after the original 29.96-second last frame. Preserve the carry across clip boundaries and do not count those two early. No new model training has started from these labels. See EXPERT_FEEDBACK_C01.json, the preserved original form export, and C01_boundary_chat_confirmation_20261027.json.


## Latest model experiment: 28 October 2026

Read [EVENT_TRAINING_RESULT_20261028.md](EVENT_TRAINING_RESULT_20261028.md) before the annotation-only update below. A real training run now used C01 and assistant C03-C06 (50 release entries, 25 negative intervals). C02 and all ten sources of the historical benchmark remained excluded. The source-check count MAE was 5.083, with 2/7 positive clips exact and false counts in 1/5 negative clips. The research screen failed. No live camera connection occurred. The checkpoint, scripts and frozen predictions are preserved in `event-training-update-20261028.zip`.

