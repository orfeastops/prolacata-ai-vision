"""Evaluate frozen counts against disclosed user totals; no inference or training."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/facility_dataset/temporal_pipeline/unseen_test_20260926/assistant_count_audit_20261029'
MODEL = ROOT / 'outputs/facility_dataset/temporal_pipeline/placement_counter_v5/object_expansion/september_results.json'


def read_frozen(path):
    data = path.read_bytes()
    return json.loads(data), hashlib.sha256(data).hexdigest()


def main():
    reference, reference_hash = read_frozen(OUT / 'user_reference_counts.json')
    visual, visual_hash = read_frozen(OUT / 'visual_count_ledger.json')
    model, model_hash = read_frozen(MODEL)
    if len({reference['source_sha256'], visual['source_sha256'], model['source_sha256']}) != 1:
        raise ValueError('Source hashes do not match; comparison refused.')
    truth = reference['reference_additions_by_tank']
    frozen = {'model_v5': model['predicted_additions_by_tank'],
              'assistant_visual_review': visual['visual_estimate_by_tank']}
    methods = {}
    for name, counts in frozen.items():
        rows = {tank: {
            'user_reference_count': truth[tank], 'frozen_count': counts[tank],
            'signed_error': counts[tank] - truth[tank],
            'absolute_error': abs(counts[tank] - truth[tank]),
            'relative_count_error_percent': 100 * (counts[tank] - truth[tank]) / truth[tank],
        } for tank in ('A', 'B')}
        methods[name] = dict(by_tank=rows, reference_total=sum(truth.values()),
            predicted_total=sum(counts.values()), net_count_error=sum(counts.values()) - sum(truth.values()),
            mean_absolute_count_error=sum(r['absolute_error'] for r in rows.values()) / len(rows),
            exact_tank_counts=sum(r['absolute_error'] == 0 for r in rows.values()), tank_count=2)
    report = dict(status='evaluated_against_user_supplied_totals', source_sha256=reference['source_sha256'],
        reference_file_sha256=reference_hash, frozen_visual_ledger_sha256=visual_hash,
        frozen_model_results_sha256=model_hash, checkpoint_sha256=model['checkpoint_sha256'],
        methods=methods, event_level_accuracy=None, event_precision=None, event_recall=None,
        use_for_training=False, use_for_threshold_tuning=False,
        observations=[
            'The user supplied total additions A=126 and B=154 after both predictions were recorded.',
            'Original model predictions 58/82 and assistant predictions 125/152 remain unchanged.',
            'The original assistant A ambiguity (124-125) means an error of -2 or -1 against 126.',
            'These are aggregate count errors. Misses and false positives may cancel; totals alone cannot establish event precision or recall.',
            'The location of the assistant discrepancies is unresolved. Earlier exclusions around 230-241s and 583-585s are interpretations, not verified event labels.',
            'Do not automatically add one event to A or two to B to match the reference totals.',
            'No model run, weight update, threshold adjustment, or test-to-training transfer occurred.',
            'This video was already inspected in diagnostic work and is not a pristine future acceptance test.'
        ])
    (OUT / 'user_reference_comparison.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    summary = '''USER-REFERENCE COMPARISON — SEPTEMBER 26 TEST

Tank | User reference | Frozen model | Model error | Frozen visual review | Visual error
A    | 126            | 58           | -68         | 125                  | -1
B    | 154            | 82           | -72         | 152                  | -2
Total| 280            | 140          | -140        | 277                  | -3

The model total is 50% below the user reference total. This is an aggregate
count error, not a statement that event detection accuracy is 50%.
Model mean absolute count error: 70 blocks per tank in this two-tank test.
Neither tank count is exact. This version fails this count comparison.

The assistant's first-tank estimate included one ambiguous piece (124-125),
so its A shortfall is 1-2. Its B shortfall is 2. These original estimates
are preserved. The user's totals do not identify the exact mistaken events.

Reference provenance: user-supplied manual totals, not independently verified
event labels. All quantities are additions within this video only.
No training or threshold tuning used these totals. No predictions were changed.
'''
    (OUT / 'USER_REFERENCE_COMPARISON.txt').write_text(summary, encoding='utf-8')
    page = OUT / 'review.html'
    html = page.read_text(encoding='utf-8')
    marker = '<!-- USER_REFERENCE_COMPARISON_START -->'
    end_marker = '<!-- USER_REFERENCE_COMPARISON_END -->'
    if marker in html:
        start = html.index(marker)
        end = html.index(end_marker, start) + len(end_marker)
        html = html[:start] + html[end:]
    banner = marker + '''<section style="margin:20px 0;padding:20px;background:#e8eef7;border:2px solid #314e78">
<h2>User reference now available</h2>
<p>The user reports <strong>A: 126; B: 154</strong>. Original predictions remain unchanged.</p>
<table><thead><tr><th>Tank</th><th>User reference</th><th>Frozen model</th><th>Model difference</th><th>Original visual estimate</th><th>Visual difference</th></tr></thead>
<tbody><tr><td>A</td><td>126</td><td>58</td><td>−68</td><td>125 (124–125 ambiguity)</td><td>−1 (or −2)</td></tr>
<tr><td>B</td><td>154</td><td>82</td><td>−72</td><td>152</td><td>−2</td></tr></tbody></table>
<p>The model counted 140 against the reference of 280: a 50% net shortfall.
This is a count discrepancy, not event detection accuracy. Neither tank count is exact.</p>
<p>The discrepancies in the visual ledger have not been localized. The earlier exclusions remain reviewer interpretations; no event was added merely to fit the new totals.</p>
<p><a href="USER_REFERENCE_COMPARISON.txt">Comparison report</a> · <a href="user_reference_comparison.json">Comparison data</a> · <a href="user_reference_counts.json">Reference provenance</a></p>
</section>''' + end_marker
    html = html.replace('</h1>', '</h1>' + banner, 1)
    html = html.replace('Visual estimate, pending reference counts.', 'Original visual estimate, recorded before user totals were disclosed.')
    html = html.replace("Compare with the user's withheld A/B totals before treating any count as reference truth.",
                        'The user-reference comparison above supersedes the earlier pending-reference status. The ledger below remains the original visual estimate.')
    page.write_text(html, encoding='utf-8')
    # Verify preservation of the two prediction artifacts and the source identity.
    if read_frozen(OUT / 'visual_count_ledger.json')[1] != visual_hash or read_frozen(MODEL)[1] != model_hash:
        raise RuntimeError('A frozen prediction artifact changed during comparison.')
    print(json.dumps(methods, indent=2))


if __name__ == '__main__':
    main()
