import argparse,json,hashlib,time
from pathlib import Path
import av,cv2,numpy as np,torch
from ultralytics import YOLO

ap=argparse.ArgumentParser();ap.add_argument('--video',required=True);ap.add_argument('--out',required=True);ap.add_argument('--max-seconds',type=float,default=0);a=ap.parse_args()
b=Path('outputs/tank_transfer_training_v1/dataset_v2/heldout_counting');out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
torch.set_num_threads(4);cv2.setNumThreads(1)
config=dict(conf=.25,imgsz=640,min_iou=.1,max_gap_s=1.0,approach_bottom_y=.52,exit_bottom_y=.46,gate_x=[.49,.60],min_height=.07,count='outbound tank proposals, content unknown until reviewed',native_frames=True)
model=YOLO(str(b/'best.pt'));tracks={};history={};events=[];nextid=1;started=time.time();origin=None;lastsave=-10

def iou(x,y):
 lo=np.maximum(x[:2],y[:2]);hi=np.minimum(x[2:],y[2:]);inter=np.maximum(hi-lo,0).prod();return float(inter/((x[2:]-x[:2]).prod()+(y[2:]-y[:2]).prod()-inter+1e-9))
with av.open(a.video) as inp,(out/'detections.jsonl').open('w') as log:
 inp.streams.video[0].codec_context.thread_count=2
 for fi,f in enumerate(inp.decode(video=0)):
  if f.time is None:continue
  if origin is None:origin=float(f.time)
  t=float(f.time)-origin
  if a.max_seconds and t>a.max_seconds:break
  im=f.to_ndarray(format='bgr24');h,w=im.shape[:2]
  p=model.predict(im,imgsz=config['imgsz'],conf=config['conf'],verbose=False)[0]
  boxes=p.boxes.xyxy.cpu().numpy()/np.array([w,h,w,h]);scores=p.boxes.conf.tolist()
  ids=[i for i,tr in tracks.items() if t-tr['last']<=config['max_gap_s']]
  pairs={}
  if ids and len(boxes):
   candidates=sorted([(iou(tracks[i]['box'],x),j,i) for i in ids for j,x in enumerate(boxes)],reverse=True)
   used=set()
   for overlap,j,i in candidates:
    if overlap>=config['min_iou'] and j not in pairs and i not in used:pairs[j]=i;used.add(i)
  rows=[]
  for j,box in enumerate(boxes):
   ident=pairs.get(j)
   if ident is None:
    ident=nextid;nextid+=1;tracks[ident]={'first':t,'last':t,'box':box,'approach':False,'counted':False};history[ident]=[]
   tr=tracks[ident];tr.update(last=t,box=box);x=(box[0]+box[2])/2;y=box[3]
   if .44<x<.65 and y>config['approach_bottom_y']:tr['approach']=True
   if tr['approach'] and not tr['counted'] and config['gate_x'][0]<x<config['gate_x'][1] and y<config['exit_bottom_y'] and box[3]-box[1]>config['min_height']:
    tr['counted']=True;e={'id':len(events)+1,'track':ident,'pts_s':t,'frame':fi,'content':'unknown','status':'automatic_outbound_proposal'};events.append(e)
    cv2.imwrite(str(out/f'event_{e["id"]:03}.jpg'),p.plot())
   row={'track':ident,'box':box.tolist(),'confidence':scores[j]};rows.append(row)
   if not history[ident] or t-history[ident][-1]['t']>=.5:history[ident].append({'t':t,'box':box.tolist()})
  log.write(json.dumps({'frame':fi,'t':t,'detections':rows})+'\n')
  if t-lastsave>=10:
   lastsave=t;(out/'progress.json').write_text(json.dumps({'frame':fi,'seconds':t,'events':len(events),'elapsed':time.time()-started}))
(out/'result.json').write_text(json.dumps({'video':a.video,'model_sha256':hashlib.sha256((b/'best.pt').read_bytes()).hexdigest(),'config':config,'frames':fi+1,'duration_s':t,'events':events,'track_histories':history,'elapsed_s':time.time()-started},indent=2))
print(json.dumps({'events':events,'frames':fi+1,'elapsed_s':time.time()-started}))
