"""Score frozen Qwen outputs locally. Correct counts never go to Kaggle."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'outputs/facility_dataset/temporal_pipeline/pretrained_video_count_v1'
V5_PATH = BASE.parent / 'placement_counter_v5/object_expansion/count_results.json'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('predictions', type=Path)
    parser.add_argument('--output-dir', type=Path, default=BASE)
    parser.add_argument('--variant', default='v1 all native frames')
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    refs = json.loads((BASE / 'local_reference_counts_DO_NOT_UPLOAD.json').read_text())
    raw = args.predictions.read_bytes()
    predictions = json.loads(raw)
    by_id = {p['id']: p for p in predictions}
    assert len(by_id) == len(predictions), 'Duplicate clip IDs'
    assert set(by_id) <= {r['id'] for r in refs}, 'Unknown clip IDs'
    old_predictions = {p['id']: p for p in json.loads(V5_PATH.read_text())['predictions']}
    rows = []
    for ref in refs:
        old = old_predictions[ref['original_segment_id']]
        assert old['source_sha256'] == ref['source_sha256']
        assert old['reference_count'] == ref['reference_count']
        pred = by_id.get(ref['id'])
        if pred:
            assert pred['source_sha256'] == ref['source_sha256'], 'Source mismatch'
        parsed = pred is not None and pred['status'] == 'parsed'
        count = pred['predicted_additions'] if parsed else None
        if parsed:
            assert type(count) is int and count >= 0
            assert count == sum(e['quantity'] for e in pred['answer']['events'])
        rows.append(dict(id=ref['id'], segment=ref['original_segment_id'],
            reference=ref['reference_count'], v5=old['accepted_additions'], qwen=count,
            qwen_status=pred['status'] if pred else 'missing',
            error=None if count is None else count-ref['reference_count'],
            uncertain_events=pred.get('uncertain_event_count') if pred else None))
    valid = [r for r in rows if r['qwen'] is not None]
    positive = [r for r in rows if r['reference'] > 0]
    negative = [r for r in rows if r['reference'] == 0]
    report = dict(variant=args.variant, predictions_sha256=hashlib.sha256(raw).hexdigest(),
        benchmark='Historical October development clips, not a pristine acceptance set',
        clips_expected=len(rows), clips_parsed=len(valid),
        missing_or_invalid=len(rows)-len(valid),
        positive_exact=sum(r['error']==0 for r in positive), positive_total=len(positive),
        negative_false_counts=sum(r['qwen'] is not None and r['qwen']>0 for r in negative),
        negative_parsed=sum(r['qwen'] is not None for r in negative), negative_total=len(negative),
        mean_absolute_count_error_parsed=sum(abs(r['error']) for r in valid)/len(valid) if valid else None,
        full_benchmark_mae=sum(abs(r['error']) for r in valid)/len(rows) if len(valid)==len(rows) else None,
        reference_additions=sum(r['reference'] for r in rows),
        predicted_additions_parsed=sum(r['qwen'] for r in valid),
        v5_mean_absolute_count_error=sum(abs(r['v5']-r['reference']) for r in rows)/len(rows),
        v5_positive_exact=sum(r['v5']==r['reference'] for r in positive),
        v5_negative_false_counts=sum(r['v5']>0 for r in negative),
        event_precision_recall_available=False, production_ready=False, rows=rows)
    (args.output_dir/'local_comparison.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    lines = ['Qwen3-VL October counting experiment: '+args.variant,
        f"Parsed {len(valid)}/{len(rows)} clips; invalid/missing: {len(rows)-len(valid)}.",
        f"Positive exact totals: {report['positive_exact']}/{len(positive)}.",
        f"Negative clips with false counts: {report['negative_false_counts']}/{len(negative)}; parsed negatives: {report['negative_parsed']}.",
        f"Mean absolute count error on parsed clips: {report['mean_absolute_count_error_parsed']}.",
        'ID | Reference | Previous v5 | Qwen | Qwen error | Status']
    lines += [f"{r['id']} | {r['reference']} | {r['v5']} | {r['qwen']} | {r['error']} | {r['qwen_status']}" for r in rows]
    lines += ['', 'Clip totals cannot establish event precision/recall: missed and false events may cancel.',
        'This is a historically reviewed development benchmark. No September footage or reference counts were supplied to Qwen.',
        'No training or count targets were supplied. Consult each variant protocol for development revisions.']
    (args.output_dir/'COMPARISON.txt').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2))


if __name__ == '__main__':
    main()
