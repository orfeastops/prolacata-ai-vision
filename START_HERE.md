# Continue from the current state

Snapshot date: **2026-10-27**, Europe/Athens.

## The user's operational objective

Camera 11 shows two workers taking whole feta blocks from conveyor trays and filling a tank. A separate stationary tank receives crumbs. Another worker removes a filled tank, brings it into camera 15 near the door, weighs it, then stores it in the aging room. Camera 15 contains both empty and full tanks. Full tanks often have a visible white top and are placed together, but appearance alone was previously misinterpreted and is not a verified inventory count.

The requested final report is the actual number of blocks added to each tank, tank transfer/weighing/storage times, daily tank totals, and eventually departures of aging-room pallets. The first tank in a test video may already contain cheese; count only additions visible during the test unless earlier continuous history is available. There is no required quota of 228 blocks. Employee-level productivity or identity is not part of the task.

## What is actually working and what is not

Data indexing, local review clips, user feedback storage, source-group evaluation and several bookkeeping/state unit tests exist. Neither high trimmed-action classification scores nor correct bookkeeping tests establish counting accuracy. The latest end-to-end count estimates still fail.

The latest completed experiment is `placement_counter_v3/native_temporal_diagnostic`. It trained and finished; it is not still running. Do not announce that it needs more training time. Its source-held-out results are poor and its `production_ready` flag is false.

The latest object detector under `placement_counter_v2/carried_cheese_uncertainty_v2` detects single-block or unknown-quantity regions. It does not supply reliable complete physical-object trajectories to the evidence-based counter. A strict trajectory trial accepted zero complete hypotheses, which means failure/abstention, not zero production.

## Immediate next task

Six new October clips, **C01–C06**, were prepared under:

`outputs/facility_dataset/temporal_pipeline/sequence_annotation_v4/`

They are about 30 seconds each, preserve every decoded original frame, and contain burned-in native clip-relative timestamps. C01 has ten reviewer-submitted entries preserved in EXPERT_FEEDBACK_C01.json: eight completed-transfer rows describe 18 blocks within the original clip. Extended context resolved the last left-side two-block carry: transfer starts at 28.20 seconds, reaches above the tank around 30.00, and releases one block at 30.74 and one at 33.30. Both releases occur after the original last frame at 29.96, so this carry adds zero blocks within the original clip and two in the extended context. The reviewer also describes three three-block carries and a valid drop from above without deep bending. Raw submissions and superseded timing are preserved separately. C02-C06 remain pending. The annotated 18 blocks are not an independently confirmed exhaustive C01 total. Do not pre-fill labels with model outputs or contact-sheet guesses.

1. Restore original media using `DATA_AND_REPRODUCIBILITY.md` if it is not already on the machine.
2. Regenerate the six clips if needed:

   ```powershell
   python work/prepare_timed_expert_batch_v4.py
   python work/build_timed_review_page_v4.py
   python work/serve_timed_review.py --port 8878
   ```

   Open `http://127.0.0.1:8878/review.html`. The range-capable server is necessary for reliable frame seeking in the browser. Plain `python -m http.server` did not provide usable video seeking in this environment.

3. Collect the user's quantities, lift times, release times, destination and per-clip totals. The browser can export JSON, or the user can answer in chat.
4. Preserve raw feedback and resolve ambiguity before creating training labels. Missing entries do not mean zero activity.
5. Link confirmed actions to visible object/group boxes or masks across pickup, carry and release frames. The user supplies domain truth; the assistant is responsible for preparing visual annotations rather than asking the user to draw every box.
6. Evaluate the revised method on excluded original sources. Keep every frame/overlapping interval from the same source in the same split. Do not repeatedly adjust a model against September 26.

This handoff does not prescribe another untested architecture as the solution. A revised approach must demonstrate correct block quantity and completed-release accounting, including one-, two- and three-block carries and gestures without cheese. The temporal count-rate diagnostic is a failed baseline to compare against, not the intended final production counter.

## Useful entry points

| File or directory | Purpose |
|---|---|
| `work/block_transfer_counter.py` | Counter that consumes verified physical-object evidence; does not generate that evidence from images |
| `work/evaluate_block_trajectories_cv2.py` | Frozen strict trajectory baseline using OpenCV decoding |
| `work/train_native_temporal_counter_v3.py` | Latest causal interval/count-rate diagnostic |
| `work/test_native_temporal_counter_v3.py` | Causality, elapsed-time integration, padding and unknown-quantity tests |
| `work/prepare_timed_expert_batch_v4.py` | New native-frame review clips |
| `work/build_timed_review_page_v4.py` | Review UI with frame stepping and timestamp capture |
| `work/serve_timed_review.py` | Loopback-only HTTP byte-range server |
| `outputs/facility_dataset/transfer_status.json` | Historical Kaggle runs and recorded observations |
| `outputs/facility_dataset/temporal_pipeline/sequence_annotation_v2/expert_feedback.json` | Authoritative stored user corrections |
| `MODEL_REGISTRY.json` | Important checkpoint paths and intended interpretation |

## Do not lose these constraints

- No fixed quantity per hand movement. Three-block carries were explicitly reported.
- Reaching/bending without lifting cheese must not count.
- Crumb disposal, salting, gesturing, separators and moving empty trays can resemble placement motion.
- A loaded hand may release blocks separately. Do not count pickup plus each release as extra blocks.
- A transfer cut off by a clip boundary is censored, not a complete negative.
- Nominal camera headers often say 30 fps while decoded native timestamps indicate about 15 fps. Preserve timestamps; do not reconstruct wall-clock time from frame number alone.
- The user is frustrated by repeated plans without execution. Show completed artifacts and measured failures, communicate progress, and do not substitute manually annotated illustrations for model predictions.
