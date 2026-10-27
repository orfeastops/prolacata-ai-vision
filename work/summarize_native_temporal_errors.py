"""Describe the frozen result without modifying training or test thresholds."""
import hashlib,json,math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/facility_dataset/temporal_pipeline'
OUT=BASE/'placement_counter_v3/native_temporal_diagnostic'
r=json.loads((OUT/'results.json').read_text(encoding='utf-8'))
fit=r['training_fit']
fit_mae=sum(abs(p['expected_count']-p['reference_count']) for p in fit)/len(fit)
fit_exact=sum(math.floor(p['expected_count']+.5)==p['reference_count'] for p in fit)
criteria=json.loads((OUT/'evaluation_gate.json').read_text())['conditions']
passes=(r['positive_clips_rounded_exact']==r['positive_clips'] and
    r['negative_clips_false_positive']==0 and
    r['source_held_out_mae']<=criteria['source_held_out_mae_at_most'])
old=json.loads((BASE/'placement_counter_v2/segment_count_probe/results.json').read_text())
assert {p['segment_id']:p['confirmed_count'] for p in r['predictions']}=={
    p['segment_id']:p['confirmed_count'] for p in old['predictions']}
analysis=dict(
    frozen_results_sha256=hashlib.sha256((OUT/'results.json').read_bytes()).hexdigest(),
    training_fit_mae=fit_mae,training_fit_rounded_exact=fit_exact,training_clips=len(fit),
    held_out_development_mae=r['source_held_out_mae'],
    held_out_development_rounded_exact=r['source_held_out_rounded_exact'],
    passes_minimum_development_screen=passes,
    interpretation='Large training-versus-source-held-out gap is evidence of overfitting; reliable counting has not been established.',
    prior_linear_count_probe_mae=old['leave_source_out_mean_absolute_error'],
    comparison_warning='Same small reused development clips; architecture, supervision and fps all changed. This is not an isolated fps experiment or independent validation.',
    label_coverage=json.loads((BASE/'placement_counter_v3/interval_label_coverage.json').read_text()),
    september_full_video_rerun_started=False,
    production_ready=False,
    next_evidence_needed='Generalization of whole-block quantities and empty/crumb gestures across original sources; correct training-set totals alone do not suffice.')
(OUT/'error_analysis.json').write_text(json.dumps(analysis,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:analysis[k] for k in ('training_fit_mae','training_fit_rounded_exact',
    'held_out_development_mae','held_out_development_rounded_exact','passes_minimum_development_screen')},indent=2))
