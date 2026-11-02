"""Read-only diagnosis of saved v5 outputs. No decoder execution or tuning."""
import json
import hashlib
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'outputs/facility_dataset/temporal_pipeline'
V5 = BASE / 'placement_counter_v5/object_expansion'
OUT = BASE / 'unseen_test_20260926/assistant_count_audit_20261029'


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    paths = [V5 / name for name in ('september_results.json', 'count_results.json',
                                   'dataset_manifest.json', 'training_complete.json')]
    original_hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    september, development, manifest, training = [load(p) for p in paths]
    stats = {}
    for split in ('train', 'val'):
        rows = [r for r in manifest['rows'] if r['split'] == split]
        stats[split] = dict(frames=len(rows), positive_frames=sum(bool(r['labels']) for r in rows),
            payload_annotations_by_quantity=dict(Counter(str(label[1]) for r in rows for label in r['labels'])))
    rejected = september['unresolved_tracks']
    result = dict(
        status='diagnosis_only_no_training_or_parameter_changes',
        original_artifact_sha256=original_hashes,
        source_sha256=september['source_sha256'],
        training_stats=stats,
        training_epochs=training['epochs'],
        september=dict(accepted_tracks=len(september['accepted_events']), unresolved_tracks=len(rejected),
            rejection_reason_counts=dict(Counter(reason for e in rejected for reason in e['reasons'])),
            reason_counts_overlap=True,
            accepted_quantity_histogram=dict(Counter(str(e['predicted_quantity']) for e in september['accepted_events'])),
            native_frames=september['frames_processed'],
            maximum_gap_s=development['config']['maximum_gap_s']),
        development_metrics=development['metrics'],
        example_130_to_133s=[e for e in rejected if 130 <= e['first_seen_s'] < 133],
        interpretation=[
            'At approximately 130.76-131.28s both image sides have tracks classified as carrying two blocks. Those tracks end before the user-described placement around 132.35s and are rejected.',
            'This demonstrates detections followed by lost or incomplete trajectories. It does not prove that every detection was correct or assign all net error to the tracker.',
            'The custom counter closes tracks after 0.4s without matched detections, uses greedy centroid association, fixed source/destination geometry, and disappearance as a release proxy.',
            '102 rejected tracks are not 102 missed placements: tracks can be fragments, duplicates, negatives, or genuine missed transfers.',
            'Training payload annotations are strongly imbalanced: six quantity-one, ninety quantity-two, four quantity-three, one unknown. These are boxes, not unique transfers.',
            'All seventy accepted September tracks voted for two blocks. Quantity-one and quantity-three performance is unproven.',
            'The source-disjoint development clips also undercount (28 versus 53 blocks), with zero exact positive clips out of seven. The weakness is not isolated to the September video.',
            'All native decoded frames were processed in the test. Increasing a supposed 8-fps sample rate is not the current fix.'
        ],
        next_experiments_in_order=[
            'Use October development sequences to compare persistent object trackers against the current greedy association. Keep detector weights fixed first to isolate tracking effects. Tune only on development data.',
            'Represent pickup, carrying/temporary occlusion, tank entry, release, crumb destination, and return as temporal state. Count a verified transfer once; preserve uncertainty when release is not visible. Disappearance alone is insufficient.',
            'Review and expand diverse training sequences covering pickup, motion blur, partial occlusion, approach/release, 1/2/3 blocks, split releases, and negative movements. Do not replace unique transfers with many nearly identical neighboring frames.',
            'Use the assistant to draft sequence annotations from other days, retain provenance and uncertainty, and request user review only for unresolved examples. Do not treat assistant labels as verified truth.',
            'Evaluate count error per complete tank, false positives on negative movements, missed transfers and duplicate counts where event labels exist. Select checkpoints and settings on development/validation only.',
            'Keep September 26 as a known regression comparison with user totals 126/154; no training or threshold tuning on it. Reserve fresh complete tanks from other days for a new acceptance evaluation.'
        ],
        implementation_status='No model, tracker configuration, annotations, or training process changed by this diagnostic.',
        official_tracking_reference='https://docs.ultralytics.com/modes/track/')
    (OUT / 'v5_failure_diagnosis.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    lines = ['V5 COUNTING FAILURE DIAGNOSIS', '', 'Verified observations:']
    lines.extend('- ' + item for item in result['interpretation'])
    lines += ['', 'Next experiments (development data only):']
    lines.extend(f'{i}. {item}' for i, item in enumerate(result['next_experiments_in_order'], 1))
    lines += ['', result['implementation_status'], '',
              'Official tracker capabilities: ' + result['official_tracking_reference'],
              'No promise of zero error or a particular accuracy follows from this diagnosis.']
    (OUT / 'V5_FAILURE_DIAGNOSIS.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    for path, digest in original_hashes.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest:
            raise RuntimeError(f'Original artifact changed: {path}')
    print(json.dumps(dict(training_stats=stats, september=result['september'], development_metrics=result['development_metrics']), indent=2))


if __name__ == '__main__':
    main()
