"""Fixed small source-held-out check; never adjusts model or threshold."""
import os,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];B=R/'outputs/facility_dataset/temporal_pipeline/placement_counter_v2';O=B/'individual_block_validation'
os.environ.update(YOLO_CONFIG_DIR=str(R/'outputs/feta_training/runtime_config'),YOLO_AUTOINSTALL='false',MPLCONFIGDIR=str(R/'outputs/feta_training/matplotlib_config'))
def prepare():
 rows=json.loads((O/'candidates.json').read_text());selected=[]
 for r in rows:
  stem=Path(r['image_path']).stem
  if r['clip_id'] in {'N01_06','N21_06'} or stem in {'B023_010.00','B023_012.00'}:boxes=[]
  elif stem=='B023_015.50':boxes=[[246,157,301,190],[332,174,378,221]]
  else:continue
  r.update(boxes=boxes,reviewer='assistant visual inspection before model predictions',expert_frame_verified=False)
  selected.append(r)
 (O/'frozen_labels.json').write_text(json.dumps(dict(confidence=.25,iou=.5,selection='Clear visually labelled frames; other samples excluded as ambiguous before inference',frames=selected),indent=2))
def evaluate(run_name='individual_block_learning_diagnostic', output=None):
 import torch
 from ultralytics import YOLO
 torch.set_num_threads(4)
 frozen=json.loads((O/'frozen_labels.json').read_text());rows=frozen['frames']
 training=json.loads((B/run_name/'manifest.json').read_text())['frames']
 assert not {r['source_sha256'] for r in rows}&{r['source_sha256'] for r in training}
 model=YOLO(str(B/run_name/'run/weights/last.pt'));out=[]
 destination=Path(output) if output else O
 destination.mkdir(parents=True,exist_ok=True)
 for r in rows:
  p=model.predict(r['image_path'],conf=frozen['confidence'],device='cpu',imgsz=640,verbose=False)[0]
  boxes=p.boxes.xyxy.tolist();matched=set()
  for box in boxes:
   candidates=[]
   for i,gt in enumerate(r['boxes']):
    if i in matched:continue
    inter=max(0,min(box[2],gt[2])-max(box[0],gt[0]))*max(0,min(box[3],gt[3])-max(box[1],gt[1]))
    union=(box[2]-box[0])*(box[3]-box[1])+(gt[2]-gt[0])*(gt[3]-gt[1])-inter
    if union and inter/union>=frozen['iou']:candidates.append((inter/union,i))
   if candidates:matched.add(max(candidates)[1])
  out.append(dict(image=Path(r['image_path']).name,targets=len(r['boxes']),predictions=len(boxes),matched=len(matched),false_positives=len(boxes)-len(matched),misses=len(r['boxes'])-len(matched)))
  dest=destination/'predictions'/Path(r['image_path']).name;dest.parent.mkdir(exist_ok=True);p.save(filename=str(dest))
 report=dict(results=out,source_overlap_with_training=False,production_ready=False,scope='Tiny diagnostic on 3 different original sources: only 1 positive frame and 10 negative frames. Not video counting accuracy. No threshold tuning.',block_deposits_measured=False)
 report['checkpoint_run']=run_name
 report['reused_development_check']=run_name!='individual_block_learning_diagnostic'
 (destination/'evaluation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
if __name__=='__main__':
 import sys
 if '--prepare' in sys.argv:prepare()
 else:evaluate()
