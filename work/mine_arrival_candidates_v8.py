"""Mine full-looking tray candidates for visual annotation, never test data."""
import os
os.environ['YOLO_AUTOINSTALL']='false';os.environ['YOLO_OFFLINE']='true'
import json
from pathlib import Path
import cv2,torch
from PIL import Image,ImageDraw,ImageFont
from ultralytics import YOLO
from prepare_arrival_expansion_v8 import ROOT,OUT,ROI,save
from arrival_counter_v7 import deduplicate_positions

DEST=OUT.parent/'arrival_candidates'
def main():
    DEST.mkdir(exist_ok=True)
    if (DEST/'candidates.json').exists():raise RuntimeError('Mining already complete')
    for d in ['images','overlays','sheets']:(DEST/d).mkdir(exist_ok=True)
    sources=json.loads((OUT/'sources.json').read_text())
    approved_sources=['S00','S01','S04','S08','S10','S11']
    selected=[s for s in sources if s['id'] in approved_sources]
    save(DEST/'selection_policy.json',dict(sources=approved_sources,window_s=[0,180],
        candidate_interval_s=1,selection='up to six highest-confidence 9/10-cheese proposals per source, >=10s apart',
        label_status='unapproved model proposals',heldout_date='2026-10-03',
        validation_sources=['S02','S06','S09','S13'],not_counting_evaluation=True))
    cv2.setNumThreads(2);torch.set_num_threads(4)
    model=YOLO(str(ROOT/'outputs/facility_dataset/temporal_pipeline/arrival_counter_v7/detector_run/weights/last.pt'))
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17);records=[]
    for source in selected:
        assert source['date'] in ['20261001','20261021']
        cap=cv2.VideoCapture(source['path']);index=-1;tick=0.;batch=[];proposals=[]
        def flush():
            if not batch:return
            preds=model.predict([x[2] for x in batch],imgsz=384,conf=.25,iou=.4,device='cpu',verbose=False)
            for (idx,t,im),pred in zip(batch,preds):
                ds=[dict(bbox=[float(v) for v in b],class_id=int(c),confidence=float(s)) for b,c,s in zip(pred.boxes.xyxy.tolist(),pred.boxes.cls.tolist(),pred.boxes.conf.tolist())]
                pos=deduplicate_positions([d for d in ds if d['class_id']!=2]);cheese=[d for d in pos if d['class_id']==0]
                trays=[d for d in ds if d['class_id']==2]
                if len(cheese) not in [9,10] or len(pos)!=10 or not trays or any(d['class_id']==3 for d in pos):continue
                proposals.append(dict(frame_index=idx,pts_s=t,im=im,draft_labels=pos+trays,
                    draft_cheese_count=len(cheese),score=sum(d['confidence'] for d in pos)/len(pos)))
            batch.clear()
        while cap.grab():
            index+=1;t=cap.get(cv2.CAP_PROP_POS_MSEC)/1000
            if t>180:break
            if t+1e-6<tick:continue
            ok,im=cap.retrieve()
            if not ok:continue
            batch.append((index,t,im[ROI[1]:ROI[3],ROI[0]:ROI[2]].copy()));tick=t+1.
            if len(batch)==16:flush()
        flush();cap.release();chosen=[]
        for p in sorted(proposals,key=lambda x:-x['score']):
            if all(abs(p['pts_s']-q['pts_s'])>=10 for q in chosen):chosen.append(p)
            if len(chosen)==6:break
        for j,p in enumerate(sorted(chosen,key=lambda x:x['pts_s'])):
            ident=f"{source['id']}_M{j:02d}";im=p.pop('im');p.pop('score')
            path=DEST/'images'/f'{ident}.png';cv2.imwrite(str(path),im)
            r=dict(**p,id=ident,source_id=source['id'],source_sha256=source['sha256'],date=source['date'],split='train',
                image=str(path),review_status='pending',approved=False,sequential_decode=True,
                label_origin='v7 proposal mined for full-tray diversity; requires visual review')
            records.append(r)
            panel=Image.new('RGB',(540,382),'#101824');panel.paste(Image.fromarray(cv2.cvtColor(im,cv2.COLOR_BGR2RGB)).resize((540,340)),(0,42));d=ImageDraw.Draw(panel)
            d.text((5,4),f"{ident} {r['date']} t={r['pts_s']:.2f} C={r['draft_cheese_count']}",font=font,fill='white')
            for k,o in enumerate(r['draft_labels']):
                b=o['bbox'];b=[b[0]*2,b[1]*2+42,b[2]*2,b[3]*2+42];color=['lime','cyan','yellow','orange'][o['class_id']]
                d.rectangle(b,outline=color,width=2)
                if o['class_id']!=2:d.text((b[0]+2,b[1]+2),f"{k}:{['C','E','T','U'][o['class_id']]}",font=font,fill=color,stroke_width=1,stroke_fill='black')
            panel.save(DEST/'overlays'/f'{ident}.jpg',quality=96)
        print(source['id'],len(proposals),'proposals;',len(chosen),'retained',flush=True)
        save(DEST/'progress.json',dict(sources_finished=selected.index(source)+1,sources_total=len(selected),candidate_images=len(records)))
    save(DEST/'candidates.json',records)
    for i in range(0,len(records),4):
        group=records[i:i+4];sheet=Image.new('RGB',(1080,764),'#101824')
        for j,r in enumerate(group):sheet.paste(Image.open(DEST/'overlays'/f"{r['id']}.jpg"),((j%2)*540,(j//2)*382))
        sheet.save(DEST/'sheets'/f'review_{i//4:02d}.jpg',quality=96)
    print('Done',len(records),flush=True)
if __name__=='__main__':main()
