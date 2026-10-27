"""Can the detector learn eight reviewed images? Not an independent accuracy test."""
import os,json,time,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1]
B=R/'outputs/facility_dataset/temporal_pipeline/placement_counter_v2'
O=B/'individual_block_learning_diagnostic'
os.environ.update(YOLO_CONFIG_DIR=str(R/'outputs/feta_training/runtime_config'),YOLO_AUTOINSTALL='false',MPLBACKEND='Agg',MPLCONFIGDIR=str(R/'outputs/feta_training/matplotlib_config'))
def save(name,data):
 (O/name).write_text(json.dumps(data,indent=2),encoding='utf-8')
def main():
 import torch
 from ultralytics import YOLO
 from ultralytics.models.yolo.detect import DetectionTrainer
 torch.set_num_threads(4)
 O.mkdir(parents=True,exist_ok=True)
 if (O/'summary.json').exists(): raise RuntimeError('Diagnostic already complete')
 names={'B022_019.50','B020_014.00','B021_010.50','N01_02_006.00','N21_03_004.00','N01_05_001.00','N21_02_001.00','N01_02_010.00'}
 rows=[a for a in json.loads((B/'individual_block_review/annotations.json').read_text()) if Path(a['image_path']).stem in names]
 assert len(rows)==8 and all(a['detector_export_eligible'] for a in rows)
 for row in rows:
  p=Path(row['image_path']);dest=O/'dataset/images'/p.name;label=O/'dataset/labels'/(p.stem+'.txt')
  dest.parent.mkdir(parents=True,exist_ok=True);label.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
  lines=[]
  for a in row['individual_blocks']:
   x1,y1,x2,y2=a['bbox_xyxy'];lines.append(f'0 {(x1+x2)/1280} {(y1+y2)/720} {(x2-x1)/640} {(y2-y1)/360}')
  label.write_text('\n'.join(lines))
 save('manifest.json',dict(purpose='Training fit diagnostic ONLY, deliberately evaluated on training images; no generalization estimate',frames=rows,september26_used=False,reserved_validation_used=False))
 yaml=O/'dataset.yaml';yaml.write_text(f'path: {(O/"dataset").as_posix()}\ntrain: images\nval: images\nnames:\n  0: carried_feta_block\n')
 config=dict(epochs=60,imgsz=640,batch=4,nbs=4,warmup_epochs=0,lr0=.003,lrf=.1,freeze=11,optimizer='AdamW',device='cpu',workers=0,patience=0,seed=43,deterministic=True,mosaic=0,mixup=0,fliplr=0,flipud=0,degrees=0,translate=0,scale=0,hsv_h=0,hsv_s=0,hsv_v=0,plots=False,val=False)
 save('config.json',config)
 class CountedTrainer(DetectionTrainer):
  updates=0
  def optimizer_step(self):
   super().optimizer_step();self.updates+=1
 start=time.time()
 model=YOLO(str(R/'outputs/feta_training/yolo26n.pt'))
 def progress(t): save('progress.json',dict(status='training',epoch=t.epoch+1,epochs=60,optimizer_updates=t.updates,elapsed_seconds=round(time.time()-start)))
 model.add_callback('on_fit_epoch_end',progress)
 model.train(trainer=CountedTrainer,data=str(yaml),project=str(O),name='run',exist_ok=True,**config)
 detector=YOLO(str(O/'run/weights/last.pt'));results=[]
 for row in rows:
  p=detector.predict(row['image_path'],conf=.25,imgsz=640,device='cpu',verbose=False)[0]
  boxes=p.boxes.xyxy.tolist();gt=[b['bbox_xyxy'] for b in row['individual_blocks']];matched=set()
  for box in boxes:
   scores=[]
   for i,b in enumerate(gt):
    if i in matched: continue
    inter=max(0,min(box[2],b[2])-max(box[0],b[0]))*max(0,min(box[3],b[3])-max(box[1],b[1]))
    union=(box[2]-box[0])*(box[3]-box[1])+(b[2]-b[0])*(b[3]-b[1])-inter
    if union and inter/union>=.5:scores.append((inter/union,i))
   if scores:matched.add(max(scores)[1])
  results.append(dict(image=Path(row['image_path']).name,targets=len(gt),predictions=len(boxes),matched=len(matched),false_positives=len(boxes)-len(matched),misses=len(gt)-len(matched)))
  dest=O/'previews'/Path(row['image_path']).name;dest.parent.mkdir(exist_ok=True);p.save(filename=str(dest))
 save('summary.json',dict(status='complete',purpose='TRAINING FIT ONLY',evaluation_on_training_images=True,production_ready=False,independent_accuracy_available=False,results=results,optimizer_updates=model.trainer.updates,elapsed_seconds=round(time.time()-start)))
 save('progress.json',dict(status='complete',optimizer_updates=model.trainer.updates))
 print(json.dumps(results))
if __name__=='__main__':main()
