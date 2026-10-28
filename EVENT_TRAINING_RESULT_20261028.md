# V4 event and quantity experiment — 28 October 2026

Training completed. Research progression screen **failed**. Production readiness remains false.

## Result

- Complete-clip October development benchmark: 5.083 blocks mean absolute error, 2/7 positive clips exactly counted, false accepted additions in 1/5 negative clips.
- C02 (entire original source excluded): 16 accepted additions within the original clip. The user's listed entries describe 7 completed transfers / 14 blocks, not an independently confirmed exhaustive clip total. Matched 4/7 listed transfers; 4 matched quantities. Unmatched predictions require visual review, not automatic false-positive labels.
- All 6118 frame instances were retained; no 8-fps sampling.
- Unresolved episodes are recorded separately; abstention is not verified zero production.

| Clip | Expert complete count | Model accepted additions | Unresolved episodes |
|---|---:|---:|---:|
| B007_11_18 | 2 | 12 | 1 |
| N21_04_3_11 | 10 | 10 | 2 |
| N21_04_11_19.9375 | 0 | 0 | 0 |
| N21_05_0_14 | 0 | 22 | 0 |
| N21_05_11_25 | 7 | 6 | 0 |
| N01_05_0_20 | 10 | 27 | 1 |
| N21_03_0_20 | 4 | 8 | 2 |
| N21_02_0_20 | 10 | 17 | 0 |
| N01_02_0_20 | 10 | 10 | 1 |
| N01_03_0_19.9375 | 0 | 0 | 2 |
| N01_01_0_19.9375 | 0 | 0 | 2 |
| N01_04_0_8 | 0 | 0 | 3 |

## Frozen recipe and limitations

The new head predicts carrying probability, deposit probability and quantities one/two/three. It uses spatial features from the existing generic frozen YOLO26n encoder, backward feature differences, native timestamp differences and causal temporal convolutions. This is a learned event/quantity diagnostic, not verified individual cheese detection or object tracking. Seven sparse annotation boxes were not treated as a complete object dataset.

Training: C01 and assistant C03-C06; five distinct October 1/21 sources, 50 release entries (including the two separately timed releases from C01's final carry), 25 explicit negative intervals. Expert observations have weight 1; assistant proposals have weight 0.5. Unknown gaps and two unresolved assistant cases are masked. Release intervals supervise one positive peak rather than repeating the group count at every frame. No whole-clip total loss is used.

Quantity supervision is imbalanced: five one-block releases, 42 two-block releases and three three-block releases. All three-block training examples come from C01. A classifier always saying two would match 84% of these training quantities while failing the actual task; that is a label-distribution baseline, not measured model accuracy. Quantity scores are uncalibrated softmax outputs.

C02 and all ten original sources of the 12 historical benchmark segments are wholly excluded from training, normalization and optimizer updates. Model checkpoint, script, configuration and dataset hashes were saved before inference. Thresholds and epochs were fixed before results, with no subsequent tuning. The historical benchmark has been inspected before and is not pristine acceptance data. Its short clips have cold-start/cutoff limitations; C02 includes native context before and after the original boundary.

No September 26 or October 3 frames were used. The failed screen does not justify another full September run or live deployment. No tank boundaries, cross-camera associations or verified daily production totals were added.

## Reproduce and inspect

```powershell
& work/feta_env/Scripts/python.exe work/test_transfer_events_v4.py
& work/feta_env/Scripts/python.exe work/train_transfer_events_v4.py
& work/feta_env/Scripts/python.exe work/finalize_transfer_events_v4.py
```

The trainer refuses to overwrite an existing completed experiment. Restore its saved artifacts to inspect rather than rerun it. The local review is `http://127.0.0.1:8878/event_model_review/review.html`, served by the existing loopback-only review server. Private media and feature caches remain local; published results and checkpoint do not include camera frames or video. Extract `event-training-update-20261028.zip` at the project root to restore the relative paths.

Seven bookkeeping/causality/file-lock tests passed. Three preview videos were fully decoded after encoding. These checks validate implementation and files, not visual model correctness. A feature-extraction attempt stopped on a transient Windows file-replacement lock; atomic JSON writes now retry, and the preserved feature caches were reused without changing model settings.

Checkpoint SHA-256: `a50aa3e44cab4f22d7c9852c6cfc6f412d1838ab5eba4d91d0a52d348cbc38b8`.
