import pathlib,json,os,time
os.environ['HF_HUB_OFFLINE']='1'
os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
os.environ['TOKENIZERS_PARALLELISM']='false'
import torch
from PIL import Image,ImageDraw
from transformers import AutoProcessor,AutoModelForZeroShotObjectDetection
torch.set_num_threads(4)
ROOT=pathlib.Path('outputs/facility_dataset');OUT=ROOT/'model_comparison';OUT.mkdir(exist_ok=True)
processor=AutoProcessor.from_pretrained('work/models/grounding-dino-tiny',local_files_only=True)
model=AutoModelForZeroShotObjectDetection.from_pretrained('work/models/grounding-dino-tiny',local_files_only=True).eval()
records=json.loads(pathlib.Path('outputs/feta_training/manual_annotations_v2.json').read_text())
validation=[r for r in records if r['split']=='val']

def iou(a,b):
 inter=max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
 union=(a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-inter
 return inter/union if union else 0

def detect(image,prompt):
 inputs=processor(images=image,text=prompt,return_tensors='pt')
 with torch.inference_mode():outputs=model(**inputs)
 r=processor.post_process_grounded_object_detection(outputs,inputs.input_ids,threshold=.05,text_threshold=.15,target_sizes=[image.size[::-1]])[0]
 labels=r.get('text_labels',r.get('labels',[]))
 return [dict(box=[float(x) for x in b],confidence=float(s),label=str(label)) for b,s,label in zip(r['boxes'],r['scores'],labels)]

results=[];stats={str(t):dict(tp=0,fp=0,fn=0) for t in (.1,.2,.3,.4)};started=time.time()
for index,r in enumerate(validation):
 image=Image.open(pathlib.Path('outputs/feta_training/dataset_v2/images/val')/r['image']).convert('RGB')
 predictions=detect(image,'a blue gloved hand.')
 # Grounding DINO emits overlapping text-query proposals; use explicit NMS.
 kept=[]
 for pred in sorted(predictions,key=lambda p:-p['confidence']):
  if all(iou(pred['box'],p['box'])<.5 for p in kept):kept.append(pred)
 for t in (.1,.2,.3,.4):
  available=set(range(len(r['boxes_xyxy'])));tp=fp=0
  for p in [p for p in kept if p['confidence']>=t]:
   if available:
    match=max(available,key=lambda i:iou(p['box'],r['boxes_xyxy'][i]))
    if iou(p['box'],r['boxes_xyxy'][match])>=.5:tp+=1;available.remove(match);continue
   fp+=1
  s=stats[str(t)];s['tp']+=tp;s['fp']+=fp;s['fn']+=len(available)
 draw=ImageDraw.Draw(image)
 for b in r['boxes_xyxy']:draw.rectangle(b,outline='yellow',width=1)
 for p in kept:
  if p['confidence']>=.2:
   b=p['box'];draw.rectangle(b,outline='#00ff99',width=2);draw.text((b[0],max(0,b[1]-12)),f"{p['confidence']:.2f}",fill='#00ff99',stroke_width=1,stroke_fill='black')
 image.save(OUT/('grounding_'+r['image']))
 results.append(dict(image=r['image'],predictions=kept,ground_truth=r['boxes_xyxy']))
 (OUT/'grounding_hand_predictions.json').write_text(json.dumps(results,indent=2))
 print('DINO VALIDATION',index+1,'/',len(validation),'elapsed',round(time.time()-started),flush=True)

for s in stats.values():
 s['precision']=s['tp']/(s['tp']+s['fp']) if s['tp']+s['fp'] else 0
 s['recall']=s['tp']/(s['tp']+s['fn']) if s['tp']+s['fn'] else 0
old=json.loads(pathlib.Path('outputs/feta_training/model_report.json').read_text())
report=dict(task='gloved_hand detection on 12 previously used validation images, 19 assistant-annotated boxes',
 grounding_dino=dict(model='IDEA-Research/grounding-dino-tiny',training_on_facility=False,prompt='a blue gloved hand.',nms_iou=.5,threshold_metrics=stats,elapsed_seconds=round(time.time()-started)),
 yolo_existing=old['fixed_threshold_validation_at_iou_0_5'],
 caveats=['This is an initial pipeline comparison, not a determination of the best model family.',
          'Grounding DINO uses a pretrained zero-shot model; YOLO used 52 facility hand labels.',
          'Image resizing, NMS and confidence scales differ. No independent test set.',
          'No block-counting or transfer accuracy has been evaluated.'])
(OUT/'grounding_vs_initial_yolo.json').write_text(json.dumps(report,indent=2))

# Inspect the alternative on blocks, bins and handling equipment as annotation proposals.
all_media=json.loads((ROOT/'media_manifest.json').read_text())
selected=[]
for camera,date in ((11,'2026-10-01'),(11,'2026-10-21'),(15,'2026-10-01'),(15,'2026-10-21'),(15,'2026-10-22')):
 group=sorted([r for r in all_media if r['camera']==camera and r['date']==date and r['extension']=='.jpg'],key=lambda r:r['filename_start'])
 if group:selected.append(group[len(group)//2])
object_results=[]
for r in selected:
 image=Image.open(r['local_path']).convert('RGB')
 if r['camera']==11:image=image.crop((800,720,1440,1080))
 prompt='a gloved hand. a white cheese block. a plastic storage bin. a pallet truck. a forklift.'
 predictions=detect(image,prompt)
 object_results.append(dict(source_sha256=r['sha256'],source=r['basename'],camera=r['camera'],date=r['date'],prompt=prompt,predictions=predictions,labels_status='unverified_model_proposals'))
 d=ImageDraw.Draw(image)
 for p in predictions:
  if p['confidence']>=.25:
   b=p['box'];d.rectangle(b,outline='#ff3333',width=2);d.text((b[0],max(0,b[1]-12)),p['label']+f" {p['confidence']:.2f}",fill='red',stroke_width=1,stroke_fill='white')
 image.save(OUT/f'objects_camera{r["camera"]}_{r["date"]}.jpg')
 print('OBJECT PROPOSALS',r['camera'],r['date'],flush=True)
(OUT/'object_proposals.json').write_text(json.dumps(object_results,indent=2))
print(json.dumps(report,indent=2),flush=True)
