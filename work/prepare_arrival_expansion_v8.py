"""Source-separated, unapproved annotation candidates. No training is launched."""
import os
os.environ['YOLO_AUTOINSTALL']='false'
os.environ['YOLO_OFFLINE']='true'
import re,json,hashlib,datetime
from pathlib import Path
import cv2,torch
from PIL import Image,ImageDraw,ImageFont
from ultralytics import YOLO
from arrival_counter_v7 import deduplicate_positions

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/facility_dataset/temporal_pipeline/arrival_counter_v8/native_candidates'
ROI=[980,910,1250,1080]
def save(p,x):p.write_text(json.dumps(x,indent=2),encoding='utf-8')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    if (OUT/'candidates.json').exists():raise RuntimeError('Candidates already prepared')
    files=[]
    for p in sorted((ROOT/'work/facility_media').glob('*Camera_11*.mp4')):
        m=re.search(r'DVR_(\d{14})_(\d{14})',p.name)
        if not m:continue
        a,b=[datetime.datetime.strptime(s,'%Y%m%d%H%M%S') for s in m.groups()]
        files.append(dict(path=p,start=a,end=b,seconds=(b-a).total_seconds()))
    test=[f for f in files if f['start'].strftime('%Y%m%d')=='20261003']
    # Entire day is quarantined, including overlapping exports and companion photos.
    save(OUT/'split_policy.json',dict(held_out_date='2026-10-03',
        holdout_videos=[str(f['path']) for f in test],
        holdout_excluded_from_extraction=True,holdout_excluded_from_training_and_tuning=True,
        historical_exposure='Not claimed never seen in the whole project; held out from this arrival-model experiment.',
        september_excluded=True,roi_full_frame=ROI,
        draft_labels_not_training_labels=True))
    selected=[]
    excluded={'3b97807568b8bda5','083b968351ac628f'}
    for date in ['20261001','20261021']:
        pool=sorted([f for f in files if f['start'].strftime('%Y%m%d')==date and f['seconds']>=180
            and f['start'].hour>=6 and f['path'].name.split('_')[0] not in excluded],key=lambda f:f['start'])
        chosen=[]
        for f in pool:
            if all(abs((f['start']-g['start']).total_seconds())>=1800 and (f['end']<=g['start'] or f['start']>=g['end']) for g in chosen):chosen.append(f)
        # Distribute across the available workday; final selected source is validation.
        indices=sorted(set(round(i*(len(chosen)-1)/6) for i in range(min(7,len(chosen)))))
        for j,i in enumerate(indices):selected.append(dict(**chosen[i],split='val' if j==len(indices)-1 else 'train',date=date))
    for d in ['images','overlays','sheets']:(OUT/d).mkdir(exist_ok=True)
    records=[];sources=[]
    cv2.setNumThreads(2);torch.set_num_threads(4)
    weights=ROOT/'outputs/facility_dataset/temporal_pipeline/arrival_counter_v7/detector_run/weights/last.pt'
    model=YOLO(str(weights))
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17)
    for sidx,f in enumerate(selected):
        cap=cv2.VideoCapture(str(f['path']));assert cap.isOpened()
        fps=cap.get(cv2.CAP_PROP_FPS);frames=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));source_sha=sha(f['path'])
        sources.append(dict(id=f'S{sidx:02d}',path=str(f['path']),sha256=source_sha,date=f['date'],split=f['split'],frames=frames,fps=fps))
        images=[];batch=[]
        next_index=0
        for j,fraction in enumerate([.08,.20,.32,.44,.56,.68,.80,.92]):
            target=int((frames-1)*fraction)
            # DVR HEVC seeks can return damaged reference-frame images. Decode
            # every prior frame sequentially, converting only selected frames.
            ok=True
            while next_index<=target:
                ok=cap.grab()
                if not ok:break
                next_index+=1
            if ok:ok,im=cap.retrieve()
            if not ok:continue
            idx=int(cap.get(cv2.CAP_PROP_POS_FRAMES))-1;t=cap.get(cv2.CAP_PROP_POS_MSEC)/1000
            ident=f'S{sidx:02d}_{j:02d}';crop=im[ROI[1]:ROI[3],ROI[0]:ROI[2]].copy()
            assert crop.shape[:2]==(170,270)
            cv2.imwrite(str(OUT/'images'/f'{ident}.png'),crop)
            if j==0:cv2.imwrite(str(OUT/'images'/f'S{sidx:02d}_context.jpg'),im)
            batch.append(dict(id=ident,source_id=f'S{sidx:02d}',source_sha256=source_sha,date=f['date'],split=f['split'],
                frame_index=idx,pts_s=t,image=str(OUT/'images'/f'{ident}.png'),review_status='pending',approved=False,
                sequential_decode=True,decoded_prior_frames=next_index))
            images.append(crop)
        cap.release()
        preds=model.predict(images,imgsz=384,conf=.25,iou=.4,device='cpu',verbose=False)
        for r,im,pred in zip(batch,images,preds):
            detections=[dict(bbox=[float(v) for v in b],class_id=int(c),confidence=float(s)) for b,c,s in zip(pred.boxes.xyxy.tolist(),pred.boxes.cls.tolist(),pred.boxes.conf.tolist())]
            positions=deduplicate_positions([d for d in detections if d['class_id']!=2])
            r['draft_labels']=positions+[d for d in detections if d['class_id']==2]
            r['draft_cheese_count']=sum(d['class_id']==0 for d in positions)
            r['label_origin']='v7 model proposal; not ground truth'
            panel=Image.new('RGB',(540,382),'#101824');panel.paste(Image.fromarray(cv2.cvtColor(im,cv2.COLOR_BGR2RGB)).resize((540,340)),(0,42))
            d=ImageDraw.Draw(panel);d.text((5,4),f"{r['id']} {r['date']} {r['split']} t={r['pts_s']:.2f} C={r['draft_cheese_count']}",font=font,fill='white')
            for k,o in enumerate(r['draft_labels']):
                b=o['bbox'];color=['lime','cyan','yellow','orange'][o['class_id']]
                b=[b[0]*2,b[1]*2+42,b[2]*2,b[3]*2+42];d.rectangle(b,outline=color,width=2)
                if o['class_id']!=2:d.text((b[0]+2,b[1]+2),f"{k}:{['C','E','T','U'][o['class_id']]}",font=font,fill=color,stroke_width=1,stroke_fill='black')
            panel.save(OUT/'overlays'/f"{r['id']}.jpg",quality=96);records.append(r)
        print(f"Extracted {f['date']} {sidx+1}/{len(selected)}",flush=True)
    save(OUT/'sources.json',sources);save(OUT/'candidates.json',records)
    for i in range(0,len(records),6):
        part=records[i:i+6];sheet=Image.new('RGB',(1080,382*((len(part)+1)//2)),'#101824')
        for j,r in enumerate(part):sheet.paste(Image.open(OUT/'overlays'/f"{r['id']}.jpg"),((j%2)*540,(j//2)*382))
        sheet.save(OUT/'sheets'/f'review_{i//6:02d}.jpg',quality=96)
    save(OUT/'preparation_complete.json',dict(candidate_images=len(records),source_videos=len(sources),
        dates=sorted(set(r['date'] for r in records)),teacher_sha256=sha(weights),training_started=False,
        labels_approved=0,holdout_date_extracted=False))
    print('Candidates:',len(records),'Sources:',len(sources))
if __name__=='__main__':main()
