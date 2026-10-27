import os,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];B=R/'outputs/facility_dataset/temporal_pipeline/placement_counter_v2';O=B/'carried_cheese_uncertainty_v2'
os.environ.update(YOLO_CONFIG_DIR=str(R/'outputs/feta_training/runtime_config'),YOLO_AUTOINSTALL='false')
def prepare():
 rows=json.loads((B/'individual_block_validation/frozen_labels.json').read_text())['frames']
 for r in rows:r['objects']=[dict(class_id=0,bbox_xyxy=b) for b in r['boxes']]
 candidates=json.loads((B/'individual_block_validation/candidates.json').read_text())
 extra={'B023_014.00':[[162,230,224,285]],'B023_017.00':[[157,173,221,231]]}
 for r in candidates:
  key=Path(r['image_path']).stem
  if key in extra:
   r['objects']=[dict(class_id=1,bbox_xyxy=b) for b in extra[key]];rows.append(r)
 manifest=json.loads((O/'manifest.json').read_text())
 assert not {r['source_sha256'] for r in rows}&{r['source_sha256'] for r in manifest['frames']}
 (O/'frozen_development_labels.json').write_text(json.dumps(dict(frames=rows,confidence=.25,iou=.5,labels_by='assistant before evaluating new checkpoint',is_fresh_independent_test=False,quantity_ground_truth_provided=False),indent=2))
def evaluate():
 import torch
 from ultralytics import YOLO
 torch.set_num_threads(4)
 data=json.loads((O/'frozen_development_labels.json').read_text());all_results={}
 for run in ['individual_blocks_expanded_v1','carried_cheese_uncertainty_v2']:
  model=YOLO(str(B/run/'run/weights/last.pt'));results=[]
  for row in data['frames']:
   p=model.predict(row['image_path'],conf=data['confidence'],imgsz=640,device='cpu',verbose=False)[0]
   boxes=p.boxes.xyxy.tolist();classes=[int(x) for x in p.boxes.cls.tolist()];matched=set();correct=0;matches=[]
   for k,box in enumerate(boxes):
    candidates=[]
    for i,obj in enumerate(row['objects']):
     if i in matched:continue
     gt=obj['bbox_xyxy'];inter=max(0,min(box[2],gt[2])-max(box[0],gt[0]))*max(0,min(box[3],gt[3])-max(box[1],gt[1]))
     union=(box[2]-box[0])*(box[3]-box[1])+(gt[2]-gt[0])*(gt[3]-gt[1])-inter
     if union and inter/union>=data['iou']:candidates.append((inter/union,i))
    if candidates:
     _,i=max(candidates);matched.add(i);ok=classes[k]==row['objects'][i]['class_id'];correct+=ok
     matches.append(dict(target_index=i,predicted_class=classes[k],expected_class=row['objects'][i]['class_id'],class_correct=ok))
   results.append(dict(image=Path(row['image_path']).name,targets=len(row['objects']),detections=len(boxes),localized_regions=len(matched),correct_class=correct,false_regions=len(boxes)-len(matched),missed_regions=len(row['objects'])-len(matched),matches=matches,boxes=boxes,classes=classes,confidences=p.boxes.conf.tolist()))
   dest=O/'development_predictions'/run/Path(row['image_path']).name;dest.parent.mkdir(parents=True,exist_ok=True);p.save(filename=str(dest))
  all_results[run]=results
 report=dict(models=all_results,scope='Reused development footage; 13 frames, 4 target regions, 10 negative frames. Region localization and class checks only, not counts.',production_ready=False,block_deposits_measured=False)
 (O/'evaluation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
if __name__=='__main__':
 import sys
 prepare() if '--prepare' in sys.argv else evaluate()
