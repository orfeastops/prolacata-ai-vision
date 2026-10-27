"""Propose hand-centred crops from October only; labels require visual review."""
import os,json,pathlib,collections
os.environ['YOLO_AUTOINSTALL']='false'
os.environ['YOLO_CONFIG_DIR']='outputs/feta_training/runtime_config'
import cv2,torch
from ultralytics import YOLO
from PIL import Image,ImageDraw
torch.set_num_threads(4)
ROOT=pathlib.Path('outputs/facility_dataset/temporal_pipeline')
OUT=ROOT/'placement_counter_v1'; OUT.mkdir(exist_ok=True)
(OUT/'carry_crops').mkdir(exist_ok=True)
model=YOLO('outputs/feta_training/hands_detector.pt')
samples={}
for p in sorted((ROOT/'review_batch_01').glob('B*/reviewed_events.json')):
    r=json.loads(p.read_text()); cid=r['source']['clip_id']
    for e in r.get('events',[]):
        if e.get('quantity')!=2 or 'pickup_window_s' not in e:continue
        a=e['pickup_window_s'][1]; b=e['release_window_s'][0]
        if b<a:continue
        t=(a+b)/2; idx=min(64,max(1,round((t-.125)*4)+1))
        samples[cid,idx]='transfer context; individual hand state UNLABELLED'
for e in json.loads((ROOT/'supervised_actions/examples.json').read_text()):
    if e['label']=='whole_block_transfer':continue
    t=sum(e['clip_interval_s'])/2; idx=min(64,max(1,round((t-.125)*4)+1))
    samples.setdefault((e['clip_id'],idx),'non-transfer context; individual hand state UNLABELLED')
rows=[]
for (cid,idx),hint in sorted(samples.items()):
    p=ROOT/'review_batch_01'/cid/'dense_review'/f'd_{idx:03d}.jpg'
    if not p.exists():continue
    frame=cv2.imread(str(p)); h,w=frame.shape[:2]
    if (w,h)!=(640,360):raise ValueError((p,w,h))
    result=model.predict(frame,conf=.25,imgsz=640,verbose=False,device='cpu')[0]
    for box in result.boxes:
        xy=box.xyxy[0].tolist(); cx=(xy[0]+xy[2])/2;cy=(xy[1]+xy[3])/2
        # Large enough to see the hand and nearby carried object.
        x=max(0,min(w-112,int(cx-56)));y=max(0,min(h-112,int(cy-56)))
        crop=frame[y:y+112,x:x+112]
        rid=f'H{len(rows):03d}'; dest=OUT/'carry_crops'/f'{rid}.jpg';cv2.imwrite(str(dest),crop)
        rows.append(dict(id=rid,clip_id=cid,frame_index=idx,time_s=.125+(idx-1)/4,
                         box=xy,roi=[x,y,x+112,y+112],image=str(dest),context=hint,label=None))
(OUT/'carry_review_candidates.json').write_text(json.dumps(rows,indent=2))
for page in range((len(rows)+39)//40):
    sheet=Image.new('RGB',(1000,8*160),'white');d=ImageDraw.Draw(sheet)
    for j,r in enumerate(rows[page*40:(page+1)*40]):
        x=(j%5)*200;y=(j//5)*160
        im=Image.open(r['image']).resize((134,134));sheet.paste(im,(x,y+24))
        # Centre dot points at the tracked hand, not an object truth label.
        rx,ry,_,_=r['roi'];b=r['box'];cx=((b[0]+b[2])/2-rx)*134/112;cy=((b[1]+b[3])/2-ry)*134/112
        d.rectangle((x+cx-2,y+24+cy-2,x+cx+2,y+24+cy+2),outline='red')
        d.text((x+2,y+2),f"{r['id']} {r['clip_id']} {r['time_s']:.2f}",fill='black')
    sheet.save(OUT/f'carry_review_{page+1}.jpg')
print(json.dumps({'hand_crops':len(rows),'pages':(len(rows)+39)//40}))
