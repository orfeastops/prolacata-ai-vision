import os,json,time,shutil,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];B=R/'outputs/facility_dataset/temporal_pipeline/placement_counter_v2';O=B/'individual_blocks_expanded_v1'
os.environ.update(YOLO_CONFIG_DIR=str(R/'outputs/feta_training/runtime_config'),YOLO_AUTOINSTALL='false',MPLBACKEND='Agg',MPLCONFIGDIR=str(R/'outputs/feta_training/matplotlib_config'))
def save(name,obj):(O/name).write_text(json.dumps(obj,indent=2),encoding='utf-8')
def main():
 import torch
 from ultralytics import YOLO
 from ultralytics.models.yolo.detect import DetectionTrainer
 torch.set_num_threads(4);O.mkdir(exist_ok=True)
 if (O/'summary.json').exists():raise RuntimeError('Completed run exists')
 rows=[r for r in json.loads((B/'individual_block_review/annotations.json').read_text()) if r['detector_export_eligible']]
 rows+=json.loads((B/'block_orientation_expansion/annotations.json').read_text())
 for r in json.loads((B/'object_review/reviewed_hard_negatives.json').read_text()):
  assert r['image_review_complete'];r.update(individual_blocks=[],detector_export_eligible=True);rows.append(r)
 held={r['source_sha256'] for r in json.loads((B/'individual_block_validation/frozen_labels.json').read_text())['frames']}
 assert not held & {r['source_sha256'] for r in rows}
 assert len({Path(r['image_path']).name for r in rows})==len(rows)
 for r in rows:
  p=Path(r['image_path']);dest=O/'dataset/images'/p.name;label=O/'dataset/labels'/(p.stem+'.txt')
  dest.parent.mkdir(parents=True,exist_ok=True);label.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
  lines=[]
  for b in r['individual_blocks']:
   x1,y1,x2,y2=b['bbox_xyxy'];assert 0<=x1<x2<=640 and 0<=y1<y2<=360
   lines.append(f'0 {(x1+x2)/1280} {(y1+y2)/720} {(x2-x1)/640} {(y2-y1)/360}')
  label.write_text('\n'.join(lines))
 checkpoint=B/'individual_block_learning_diagnostic/run/weights/last.pt'
 save('manifest.json',dict(frames=rows,training_images=len(rows),positive_frames=sum(bool(r['individual_blocks']) for r in rows),boxes=sum(len(r['individual_blocks']) for r in rows),source_count=len({r['source_sha256'] for r in rows}),initial_checkpoint=str(checkpoint),initial_checkpoint_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest(),held_out_sources=list(held),september26_used=False))
 yaml=O/'dataset.yaml';yaml.write_text(f'path: {(O/"dataset").as_posix()}\ntrain: images\nval: images\nnames:\n  0: carried_feta_block\n')
 config=dict(epochs=25,imgsz=640,batch=4,nbs=4,warmup_epochs=0,lr0=.0007,lrf=.1,freeze=11,optimizer='AdamW',device='cpu',workers=0,patience=0,seed=43,deterministic=True,mosaic=0,mixup=0,fliplr=0,flipud=0,degrees=3,translate=.04,scale=.1,hsv_h=0,hsv_s=.1,hsv_v=.1,plots=False,val=False)
 save('config.json',dict(**config,checkpoint_policy='fixed last epoch; no selection on development validation',built_in_val_scope='training fit only; separate held-out check after training'))
 class Trainer(DetectionTrainer):
  updates=0
  def optimizer_step(self):super().optimizer_step();self.updates+=1
 model=YOLO(str(checkpoint));start=time.time()
 def progress(t):save('progress.json',dict(status='training',epoch=t.epoch+1,epochs=25,updates=t.updates,elapsed_seconds=round(time.time()-start)))
 model.add_callback('on_fit_epoch_end',progress)
 model.train(trainer=Trainer,data=str(yaml),project=str(O),name='run',exist_ok=True,**config)
 from evaluate_block_diagnostic_holdout import evaluate
 evaluate('individual_blocks_expanded_v1',O/'development_check')
 report=json.loads((O/'development_check/evaluation.json').read_text())
 save('summary.json',dict(status='complete',training_images=len(rows),updates=model.trainer.updates,elapsed_seconds=round(time.time()-start),development_results=report['results'],production_ready=False,video_counting_available=False,limitation='Reused tiny development check, not a fresh independent accuracy estimate'))
 save('progress.json',dict(status='complete',updates=model.trainer.updates))
if __name__=='__main__':main()
