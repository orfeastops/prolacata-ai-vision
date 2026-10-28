# Prolacata AI Vision

## Latest model experiment: 28 October 2026

Read [EVENT_TRAINING_RESULT_20261028.md](EVENT_TRAINING_RESULT_20261028.md) before the annotation-only update below. A real training run now used C01 and assistant C03-C06 (50 release entries, 25 negative intervals). C02 and all ten sources of the historical benchmark remained excluded. The source-check count MAE was 5.083, with 2/7 positive clips exact and false counts in 1/5 negative clips. The research screen failed. No live camera connection occurred. The checkpoint, scripts and frozen predictions are preserved in `event-training-update-20261028.zip`.

Research workspace for counting feta blocks added to production tanks in camera 11, associating completed tank transfers with weighing/storage in camera 15, and eventually reporting pallet departures from the aging room.

**Status: experimental, not ready for production or live-camera counting.** The repository preserves the work and its failures so another session can continue without mistaking a successful training job for a successful counter.

Start with **[START_HERE.md](START_HERE.md)**, then **[EXPERIMENT_HISTORY.md](EXPERIMENT_HISTORY.md)** and **[DATA_AND_REPRODUCIBILITY.md](DATA_AND_REPRODUCIBILITY.md)**. The next annotation task is described in **[ANNOTATION_PROTOCOL.md](ANNOTATION_PROTOCOL.md)**.

## What is preserved

- `work/`: preparation, labeling, training, evaluation and review scripts.
- `snapshot-data.zip`: recorded annotations, source indexes, notebook sources, configurations, numerical reports, and auxiliary work metadata, retaining their original directory layout.
- `snapshot-models-*.zip`: locally available experiment checkpoints and the fixed feature projection.
- `snapshot_manifest.json`: archive and member SHA-256 checksums.
- `restore_snapshot.py`: verifies and restores the packaged files into the checkout.
- English handoff documentation and model/cloud-artifact registries.

Historic annotation text and user statements are retained in their original language where necessary for provenance. New handoff documentation is in English. Original Greek review interfaces remain available for the reviewer.

Camera videos, employee images, large image caches and Python environments are not embedded in these Git archives. The original media was uploaded to the user's **private Kaggle datasets**, and local source hashes/paths are preserved. This is a project/checkpoint handoff, **not a self-contained backup of all camera footage**. The restoration guide identifies those dependencies explicitly.

## Restore

Clone this repository or download its source ZIP. The seven `snapshot-*.zip` archives are separate assets on the **[research release](https://github.com/orfeastops/prolacata-ai-vision/releases/tag/v0.0.0-research-20261027)**. Run `python download_snapshot.py` to retrieve them automatically and verify every SHA-256 checksum. Alternatively, download all seven archives manually into the checkout root. A Git clone alone does not include those checkpoint/data archives.

From the repository root:

```powershell
python download_snapshot.py
python restore_snapshot.py --verify-only
python restore_snapshot.py
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-core.txt
.\.venv\Scripts\python.exe work/test_block_transfer_counter.py
.\.venv\Scripts\python.exe work/test_native_temporal_counter_v3.py
```

The dependency file records the core versions used locally. `runtime_versions.json` includes additional package versions. Some historical scripts require FFmpeg, optional ML libraries, Kaggle GPU resources, or adjustment of original import paths; copying this snapshot does not establish that every historical script runs without setup on another machine.

## Previous diagnostic: 27 October 2026

The native-frame temporal diagnostic used 12 reviewed clips from 10 original October files, containing 53 expert-confirmed additions. Each validation prediction excluded its entire original source file from training. These are reused development clips, not a fresh independent acceptance test.

| Measure | Result |
|---|---:|
| Frame instances, with no temporal thinning | 2,687 |
| Distinct source frames, accounting for overlapping clips | 2,643 |
| Approximate measured source rate | 15 fps, variable timestamps |
| Source-held-out mean absolute error | 2.364 blocks per clip |
| Positive clips with correct rounded total | 1 / 7 |
| Zero-count clips with a false positive rounded total | 2 / 5 |
| Training clips fitted to the correct rounded total | 12 / 12 |

The training/evaluation gap demonstrates overfitting. The model is a causal count-rate experiment using frozen generic YOLO image features; its decimal outputs are expected counts. It is not verified tracking of individual blocks from pickup to release. Changing the architecture and supervision alongside the frame rate means the result is not an isolated 8-versus-15-fps experiment.

Full report after restoration:
`outputs/facility_dataset/temporal_pipeline/placement_counter_v3/native_temporal_diagnostic/results.json`.

## Essential counting rules

- Count actual whole blocks released into the filling tank, once each.
- Do not assume two blocks per gesture, ten per tray, or 228 per tank.
- Gloves, hand motion, bending, crumbs and tray handling are insufficient evidence by themselves.
- Unknown quantities and occluded/cut-off actions remain unknown rather than becoming zeros.
- Left/right positions distinguish simultaneous actions; personal employee identification is unnecessary.
- September 26 is excluded from training. It has already been inspected for errors, so it is no longer a pristine blind acceptance set.
- October 3 is reserved for evaluation; the new annotation batch uses October 1 and October 21.

Automatic tank changes, camera 11/15 association, verified wall-clock times and end-to-end continuous live acceptance testing remain unfinished.

Third-party packages and pretrained weights retain their upstream terms. No new license for the overall project is assigned by this snapshot.
