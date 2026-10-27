"""Show extra context for the user's final two-block C01 annotation."""
import json
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/facility_dataset/temporal_pipeline/sequence_annotation_v4'

def main():
    row=json.loads((OUT/'C01/annotation.json').read_text(encoding='utf-8'))
    src=next(r for r in json.loads((OUT/'candidate_sources.json').read_text()) if r['sha256']==row['source_sha256'])
    origin=row['original_first_pts_s'];start=origin+26;stop=origin+36
    cap=cv2.VideoCapture(src['local_path']);frames=[];times=[];indices=[];idx=0
    while True:
        ok,f=cap.read()
        if not ok:raise RuntimeError('Source ended before boundary context')
        t=cap.get(cv2.CAP_PROP_POS_MSEC)/1000
        if t>=stop:break
        if t>=start:frames.append(f[720:1080,800:1440].copy());times.append(t-origin);indices.append(idx)
        idx+=1
    cap.release();assert np.all(np.diff(indices)==1)
    fps=(len(frames)-1)/(times[-1]-times[0]);end=row['native_relative_timestamps_s'][-1]
    target=OUT/'C01/boundary_context.webm'
    writer=cv2.VideoWriter(str(target),cv2.VideoWriter_fourcc(*'VP80'),fps,(1280,800));assert writer.isOpened()
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',23)
    for t,f in zip(times,frames):
        canvas=Image.new('RGB',(1280,800),(17,24,39));d=ImageDraw.Draw(canvas)
        d.text((20,10),f'C01 CONTEXT | Original C01 time: {t:.2f} s | Original last frame: {end:.2f} s',font=font,fill='white')
        d.text((20,43),'AFTER the original clip boundary' if t>end else 'INSIDE the original clip boundary',font=font,fill='#fca5a5' if t>end else '#7dd3fc')
        canvas.paste(Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB)).resize((1280,720)),(0,80))
        writer.write(cv2.cvtColor(np.asarray(canvas),cv2.COLOR_RGB2BGR))
    writer.release();cap=cv2.VideoCapture(str(target));n=0
    while cap.read()[0]:n+=1
    cap.release();assert n==len(frames)
    (OUT/'C01/boundary_context.json').write_text(json.dumps(dict(source_sha256=src['sha256'],
        original_C01_relative_interval=[times[0],times[-1]],native_frames=n,original_clip_last_time=end,
        purpose='Resolve final two-block release at original clip end; no additional quantities assumed',
        labels_remain_pending=True),indent=2),encoding='utf-8')
    print(json.dumps(dict(path=str(target),native_frames=n,first_time=times[0],last_time=times[-1])))

if __name__=='__main__':main()
