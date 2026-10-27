# Data, artifacts and reproducibility

## Restore the local project snapshot

The complete project/checkpoint bundle is distributed as the release asset `prolacata-research-snapshot-2026-10-27.zip`. Extract it first. Source code and handoff documents are also browsable in Git, but `snapshot-data.zip` and the six model archives are release assets inside that bundle. A plain Git clone requires these additional archives before restoration.

Run `python restore_snapshot.py --verify-only`, then `python restore_snapshot.py` from the repository root. Every archive and extracted member is checked against `snapshot_manifest.json`. Extraction is constrained to the checkout. Existing files with different bytes are protected unless `--overwrite` is explicitly supplied.

The GitHub archives contain text records, configurations, notebooks, code and locally available experiment weights. Paths retain the original `work/` and `outputs/` structure. The old absolute workspace prefix is replaced with `.` in copied text. Relative paths should be resolved from the repository root. Some original raw-import paths outside the workspace still need remapping on another computer.

Historical report/checkpoint hashes describe their original inputs. Sanitized text copies can differ from those old hashes. `snapshot_manifest.json` provides checksums for the exported copies; do not overwrite historical provenance to disguise this distinction.

## Original media

The camera media is separately stored in the user's private Kaggle datasets:

- [October camera 11/15 data](https://www.kaggle.com/datasets/orfeastops/facility-production-camera-11-and-15-october-2026)
- [September 26 test data](https://www.kaggle.com/datasets/orfeastops/facility-camera11-unseen-test-september-26-2026)

These links identify existing recorded destinations; this handoff did not change their permissions or revalidate every remote object. Access requires the user's Kaggle account. Original local imports also came from `cameradata`, WeTransfer folders and the separate `camera11 test.zip` supplied by the user.

After downloading/extracting the private datasets, use the source indexes to locate files by SHA-256 and filename. The main working layout expects October originals under `work/facility_media/` and September originals under `work/unseen_test_20260926/media/`. The media index contains the exact hash-prefixed names and expected relative paths. Images, native pixel caches and preview videos can be regenerated from those sources.

Important indexes after restoration:

- `outputs/facility_dataset/media_manifest.json`
- `outputs/facility_dataset/media_manifest_portable.json`
- `outputs/facility_dataset/temporal_pipeline/temporal_media_index.json`
- `outputs/facility_dataset/temporal_pipeline/unseen_test_20260926/media_manifest.json`
- `outputs/facility_dataset/temporal_pipeline/unseen_test_20260926/video_index.json`
- `outputs/facility_dataset/temporal_pipeline/sequence_annotation_v4/candidate_sources.json`

Raw camera footage and images are not published in the public GitHub repository. This is an explicit external-data dependency, not a claim that the GitHub checkout alone contains all video pixels.

## Cloud-only outputs and downloadable base models

`REMOTE_ARTIFACTS.json` records the Kaggle notebook runs and output locations. Some cloud artifacts, including the full VideoMAE pretraining output and the pretrained action-classification head, were not present among the locally available checkpoint files. They must be retrieved through the corresponding Kaggle run if needed. The saved numerical observations and notebook sources are included locally.

The downloaded Grounding DINO base model is approximately 657 MiB and is not a project-trained checkpoint. Its source is `IDEA-Research/grounding-dino-tiny`; `work/download_grounding_dino.py` retrieves the official files. Its local model/configuration inventory is preserved. Other upstream bases retain their upstream licenses and download sources.

## Rebuild the latest native-frame experiment inputs

Once original media paths are available:

```powershell
python work/cache_native_transfer_frames.py
python work/audit_native_transfer_alignment.py
```

Existing labels and completed result files should be preserved. Several builders deliberately refuse to overwrite frozen results. Do not delete those guards to rerun a supposedly blind experiment. A changed method should get a new experiment directory and explicit provenance.

The final temporal checkpoint depends on both the saved generic YOLO base and `fixed_projection.npy`, with the training-source normalization stored in the checkpoint. Restoring the head alone is insufficient. Source-held-out predictions require their corresponding `fold_*.pt` checkpoints rather than the final all-source model.

## Decoding and time

Sequential OpenCV decoding from the original camera file is the established fallback. The old `work/video_decoder/.../ffmpeg*.exe` became inaccessible in the original environment; do not assume that binary exists in a fresh checkout. Install/configure a legitimate FFmpeg runtime separately if a historical script needs it.

Preserve actual frame timestamps. The encoded timeline, filename start/end times, and camera's burned-in wall clock have not been proven equivalent. Preview videos use constant playback spacing but display original variable timestamps. Exact production wall-clock reporting remains a separate validation task.

## Review UI

```powershell
python work/prepare_timed_expert_batch_v4.py
python work/build_timed_review_page_v4.py
python work/serve_timed_review.py --port 8878
```

The helper binds only to `127.0.0.1` and supports HTTP byte ranges for video seeking. Open `http://127.0.0.1:8878/review.html`. Review entries are stored in that browser's local storage until exported. Browser local storage is not part of this repository: use the JSON export or preserve the user's chat feedback explicitly.
