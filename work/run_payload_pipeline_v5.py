"""Wait for the one active training run, then evaluate and package exactly once."""
import json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/facility_dataset/temporal_pipeline/placement_counter_v5/object_expansion'
WEB=ROOT/'outputs/facility_dataset/temporal_pipeline/sequence_annotation_v4/object_model_review'
def save(name,obj):
    p=OUT/name;p.write_text(json.dumps(obj,indent=2),encoding='utf-8')
def run(script,log):
    with (OUT/log).open('w',encoding='utf-8') as stream:
        result=subprocess.run([sys.executable,str(ROOT/'work'/script)],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
    if result.returncode:raise RuntimeError(f'{script} exited {result.returncode}; see {log}')
def main():
    lock=OUT/'pipeline.lock'
    with lock.open('x',encoding='utf-8') as f:f.write(str(os.getpid()))
    save('pipeline_status.json',dict(stage='waiting_for_existing_training',pid=os.getpid()))
    try:
        while not (OUT/'training_complete.json').exists():
            if (OUT/'training_failure.json').exists():raise RuntimeError('Training failed; read training_failure.json and training.log')
            progress=OUT/'training_progress.json'
            if progress.exists():
                try:
                    text=progress.read_text();json.loads(text)
                    (WEB/'training_progress.json').write_text(text,encoding='utf-8')
                except (OSError,json.JSONDecodeError):pass
            time.sleep(10)
        for output,script,log,stage in [
            ('count_results.json','evaluate_payload_counter_v5.py','count_evaluation.log','counting_development_clips'),
            ('september_results.json','evaluate_september_payload_v5.py','september_evaluation.log','counting_september_native_video'),
            ('pipeline_complete.json','finalize_payload_v5.py','finalization.log','rendering_and_packaging')]:
            if (OUT/output).exists():continue
            save('pipeline_status.json',dict(stage=stage,pid=os.getpid()));run(script,log)
        save('pipeline_status.json',dict(stage='complete_pending_browser_verification_and_github_publication',pid=os.getpid()))
    except Exception as e:
        save('pipeline_failure.json',dict(error=str(e),at_unix=time.time()));raise
if __name__=='__main__':main()
