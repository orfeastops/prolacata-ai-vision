"""Write English machine-readable continuity records from local evidence."""
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'work/project_handoff';OUT.mkdir(exist_ok=True)
T=ROOT/'outputs/facility_dataset/temporal_pipeline'

def save(name,value):(OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')

def main():
    transfer=json.loads((ROOT/'outputs/facility_dataset/transfer_status.json').read_text())
    remote=dict(snapshot_date='2026-10-27',status_basis='Previously recorded local observations; not a fresh remote-state audit',
        private_datasets=[transfer['dataset_url'],'https://www.kaggle.com/datasets/orfeastops/facility-camera11-unseen-test-september-26-2026'],
        runs=[dict(stage=stage,url=transfer[key],local_checkpoint_mirror_complete=False)
              for stage,key in [('GPU proposal preparation','run_url'),('Proposal export','export_run_url'),
                ('VideoMAE pretraining','video_pretraining_run_url'),('Reviewed action pilot','reviewed_action_pilot_url'),
                ('Pretrained action comparison','pretrained_action_comparison_url'),('September action-window inference','unseen_test_run_url')]],
        note='Numerical results and notebook sources are archived. Cloud-only checkpoint outputs require the corresponding Kaggle account/run; do not claim these are all mirrored to GitHub.')
    save('REMOTE_ARTIFACTS.json',remote)
    weights=[]
    for path in sorted((ROOT/'outputs').rglob('*.pt')):
        weights.append(dict(path=path.relative_to(ROOT).as_posix(),bytes=path.stat().st_size,
            sha256=hashlib.sha256(path.read_bytes()).hexdigest(),included_in_model_archives=True))
    save('MODEL_REGISTRY.json',dict(production_ready=False,locally_available_checkpoints=weights,
        important_versions=[
            dict(path='outputs/feta_training/hands_detector.pt',role='Historic hand/glove detector, not a cheese quantity counter'),
            dict(path='outputs/feta_training/yolo26n.pt',role='Generic pretrained image backbone used frozen in v3'),
            dict(path='outputs/facility_dataset/temporal_pipeline/placement_counter_v2/carried_cheese_uncertainty_v2/run/weights/last.pt',role='Single-block/unknown-quantity detector; complete reliable trajectories not established'),
            dict(path='outputs/facility_dataset/temporal_pipeline/placement_counter_v3/native_temporal_diagnostic/experimental_native_temporal_counter.pt',role='Failed all-source fitted count-rate baseline; not a held-out evaluation checkpoint'),
            dict(path='outputs/facility_dataset/temporal_pipeline/placement_counter_v3/native_temporal_diagnostic/fold_*.pt',role='Ten source-excluded heads used for reported development predictions')],
        required_v3_companions=['outputs/feta_training/yolo26n.pt','outputs/facility_dataset/temporal_pipeline/placement_counter_v3/native_temporal_diagnostic/fixed_projection.npy'],
        downloadable_base_model=dict(model_id='IDEA-Research/grounding-dino-tiny',local_path='work/models/grounding-dino-tiny/model.safetensors',mirrored_to_github=False,restore_script='work/download_grounding_dino.py'),
        cloud_only_checkpoint_locations='REMOTE_ARTIFACTS.json'))
    r=json.loads((T/'placement_counter_v3/native_temporal_diagnostic/results.json').read_text())
    clips=json.loads((T/'sequence_annotation_v4/manifest.json').read_text(encoding='utf-8'))
    save('CURRENT_STATE.json',dict(snapshot_date='2026-10-27',production_ready=False,live_cameras_connected=False,
        latest_completed_experiment='placement_counter_v3/native_temporal_diagnostic',
        latest_source_held_out_mae=r['source_held_out_mae'],latest_positive_exact=[1,7],latest_zero_false_positive=[2,5],
        next_task='Obtain expert quantities/timings for C01-C06, link them to object/group visual annotations, then evaluate a revised method by original source',
        annotation_batch=[dict(clip_id=c['clip_id'],date=c['date'],source_sha256=c['source_sha256'],expert_review_complete=False) for c in clips],
        no_active_training_job_started_for_v4=True,no_ground_truth_inferred_from_missing_review_entries=True,
        september_excluded_from_training=True,september_previously_inspected_for_error_analysis=True,
        october3_reserved_for_evaluation=True,automatic_tank_switching_complete=False,
        cross_camera_tank_association_complete=False,camera_wall_clock_verified=False,
        raw_camera_media_is_external_dependency=True))
    print('English model, cloud-artifact and continuation registries written')

if __name__=='__main__':main()
