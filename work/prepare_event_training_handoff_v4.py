"""Stage English continuation records for a completed, frozen v4 experiment."""
from pathlib import Path
import json
from train_transfer_events_v4 import ROOT,OUT,load,save,digest

def main():
    export=ROOT/'github_export/event_training_update_20261028'
    result=load(OUT/'results.json');m=result['metrics']
    handoff=ROOT/'work/project_handoff'
    state=load(handoff/'CURRENT_STATE.json')
    state.update(latest_completed_experiment='placement_counter_v4/event_quantity_diagnostic',
        latest_training_update='2026-10-28',production_ready=False,live_cameras_connected=False,
        no_active_training_job_started_for_v4=False,v4_training_status='complete',
        historical_v3_metrics=dict(source_held_out_mae=2.364043176174164,positive_exact=[1,7],zero_false_positive=[2,5]),
        latest_source_held_out_mae=m['mean_absolute_count_error'],
        latest_positive_exact=[m['positive_exact'],m['positive_clips']],
        latest_zero_false_positive=[m['negative_false_counts'],m['negative_clips']],
        metric_comparability='Different training sources, supervision, head and discrete decoding; not a controlled architecture-only or fps comparison.',
        v4_event_quantity_experiment=dict(metrics=m,train_clips=['C01','C03','C04','C05','C06'],
            excluded_new_source='C02',training_release_entries=50,training_negative_intervals=25,
            checkpoint_sha256=result['checkpoint_sha256'],result_file='EVENT_TRAINING_RESULT_20261028.json',
            trained_object_detector=False,trained_temporal_event_quantity_heads=True),
        next_task='Read EVENT_TRAINING_RESULT_20261028.md and inspect the frozen model outputs. Improve carried-object evidence and representation using development sources; preserve C02 and historical source-check provenance. Do not tune on September 26 or October 3, report training fit as production accuracy, or reconnect cameras.')
    save(export/'CURRENT_STATE.json',state)
    marker='## Latest model experiment: 28 October 2026\n'
    insert=f'''{marker}
Read [EVENT_TRAINING_RESULT_20261028.md](EVENT_TRAINING_RESULT_20261028.md) before the annotation-only update below. A real training run now used C01 and assistant C03-C06 (50 release entries, 25 negative intervals). C02 and all ten sources of the historical benchmark remained excluded. The source-check count MAE was {m['mean_absolute_count_error']:.3f}, with {m['positive_exact']}/{m['positive_clips']} positive clips exact and false counts in {m['negative_false_counts']}/{m['negative_clips']} negative clips. The research screen {'passed' if m['screen_passed'] else 'failed'}. No live camera connection occurred. The checkpoint, scripts and frozen predictions are preserved in `event-training-update-20261028.zip`.

'''
    text=(handoff/'CLAUDE_HANDOFF.md').read_text(encoding='utf-8')
    assert marker not in text, 'Update already staged; inspect instead of duplicating'
    first,rest=text.split('\n',1)
    text=first+'\n\n'+insert+rest.lstrip('\n')
    text=text.replace('No new training was started on C01 or C02.','The October 28 event model trained on C01; C02 remained source-held-out.')
    text=text.replace('The latest count-rate diagnostic fit all 12 training clip totals','The previous v3 count-rate diagnostic fit all 12 training clip totals')
    (export/'CLAUDE_HANDOFF.md').write_text(text,encoding='utf-8')
    for name in ('README.md','EXPERIMENT_HISTORY.md'):
        source=handoff/name
        if not source.exists():source=ROOT/'github_export/prolacata-ai-vision'/name
        original=source.read_text(encoding='utf-8')
        if name=='README.md':
            first,rest=original.split('\n',1)
            updated=first+'\n\n'+insert+rest.lstrip('\n')
            updated=updated.replace('## Latest completed diagnostic: 27 October 2026','## Previous diagnostic: 27 October 2026')
        else:updated=original+'\n\n'+insert
        (export/name).write_text(updated,encoding='utf-8')
    payloads=[p for p in export.iterdir() if p.is_file() and p.name!='package_manifest.json']
    save(export/'publication_manifest.json',dict(published=False,files=[dict(name=p.name,bytes=p.stat().st_size,sha256=digest(p)) for p in payloads]))
    print(json.dumps([p.name for p in payloads]))

if __name__=='__main__':main()
