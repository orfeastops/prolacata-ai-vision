"""Extract original frames and timed evidence sheets for assistant visual annotation.

All native frames are retained as inspection JPEGs; overview sampling does not
change model inputs. No detections or quantities are inferred by this script.
"""
import argparse
import hashlib
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'outputs/facility_dataset/temporal_pipeline/sequence_annotation_v4'
OUT = SOURCE / 'assistant_visual_review'
FONT = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 20)

def sheet(clip, times, frames, targets, name):
    dest = OUT / clip / 'sheets'; dest.mkdir(parents=True, exist_ok=True)
    indices = [int(np.argmin(abs(np.asarray(times)-t))) for t in targets]
    canvas = Image.new('RGB', (1280, ((len(indices)+1)//2)*392), '#111827')
    draw = ImageDraw.Draw(canvas)
    for n, i in enumerate(indices):
        x, y = (n % 2)*640, (n//2)*392
        draw.text((x+8,y+5), f'{clip}  t={times[i]:.3f}s  frame={i}', font=FONT, fill='white')
        canvas.paste(Image.open(frames[i]), (x,y+32))
    canvas.save(dest / (name+'.jpg'), quality=96)
    return dict(file=(dest/(name+'.jpg')).relative_to(ROOT).as_posix(), frame_indices=indices)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--clips',nargs='+',default=['C03','C04','C05','C06','C02','C01'])
    parser.add_argument('--detail',nargs=3,type=float,metavar=('START','END','STEP'))
    args=parser.parse_args();cv2.setNumThreads(2)
    candidates=json.loads((SOURCE/'candidate_sources.json').read_text(encoding='utf-8'))
    for clip in args.clips:
        dest=OUT/clip;dest.mkdir(parents=True,exist_ok=True)
        meta_path=dest/'frames.json'
        if not meta_path.exists():
            ref=json.loads((SOURCE/clip/'annotation.json').read_text(encoding='utf-8'))
            source=next(s for s in candidates if s['sha256']==ref['source_sha256'])
            path=Path(source['local_path'])
            with path.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==ref['source_sha256']
            start=ref['original_first_pts_s'];lo=max(0,start-2);hi=start+36.2
            cap=cv2.VideoCapture(str(path));assert cap.isOpened();i=0;times=[];indices=[];files=[]
            while True:
                ok,frame=cap.read()
                if not ok:break
                pts=cap.get(cv2.CAP_PROP_POS_MSEC)/1000
                if pts>hi:break
                if pts>=lo:
                    fn=dest/f'frame_{len(files):04d}.jpg'
                    assert cv2.imwrite(str(fn),frame[720:1080,800:1440],[cv2.IMWRITE_JPEG_QUALITY,97])
                    times.append(round(pts-start,6));indices.append(i);files.append(fn.name)
                i+=1
            cap.release()
            assert len(times)>500 and np.all(np.diff(indices)==1) and np.all(np.diff(times)>0)
            meta=dict(clip_id=clip,source_sha256=ref['source_sha256'],source_file=str(path),
                original_first_clip_pts_s=start,relative_times_s=times,source_frame_indices=indices,
                files=files,roi_xyxy=[800,720,1440,1080],coordinate_system='native 640x360 ROI',
                all_native_frames_in_context_retained=True,quantity_labels_generated=False)
            meta_path.write_text(json.dumps(meta,indent=2),encoding='utf-8')
        meta=json.loads(meta_path.read_text(encoding='utf-8'));times=meta['relative_times_s'];files=[dest/f for f in meta['files']]
        if args.detail:
            a,b,step=args.detail;targets=np.arange(a,b+step/4,step)
            for offset in range(0,len(targets),10):
                selected=targets[offset:offset+10]
                sheet(clip,times,files,selected,f'detail_{selected[0]:05.2f}_{selected[-1]:05.2f}')
        else:
            pages=[sheet(clip,times,files,np.arange(s,s+5,.5),f'overview_{s:02d}_{s+5:02d}') for s in range(0,30,5)]
            (dest/'overview_pages.json').write_text(json.dumps(pages,indent=2),encoding='utf-8')
        print(f'{clip}: {len(times)} native context frames and evidence sheets ready',flush=True)

if __name__=='__main__':main()
