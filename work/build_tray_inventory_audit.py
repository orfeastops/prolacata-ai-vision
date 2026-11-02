"""Build October-only visual feasibility evidence, without generating labels.

Sequential decoding preserves original timestamps. Quarter-second images are
inspection aids only; this is neither training nor sampled model inference.
"""
import json, hashlib, time
from pathlib import Path
import cv2
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/facility_dataset/temporal_pipeline'
OUT=BASE/'sequence_annotation_v4/tray_inventory_review'
SOURCES={'O01':'3b97807568b8bda51f60f7924b2fd667f0e698b6d649b4c88a2717ac8f5241ec',
         'O21':'083b968351ac628ff86fcf35ffa5537e14d5c0e53a02c431c3c6f0388dbf4b39'}
FONT=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19)

def make_sheet(sid, rows, name):
    dest=OUT/sid/'sheets';dest.mkdir(exist_ok=True)
    im=Image.new('RGB',(1280,392*((len(rows)+1)//2)), '#101824');d=ImageDraw.Draw(im)
    for n,r in enumerate(rows):
        x=n%2*640;y=n//2*392
        d.text((x+8,y+5),f'{sid} source t={r["pts_s"]:.3f}s / frame {r["source_frame_index"]}',font=FONT,fill='white')
        im.paste(Image.open(OUT/sid/r['image']),(x,y+32))
    im.save(dest/(name+'.jpg'),quality=94)

def main():
    cv2.setNumThreads(2);OUT.mkdir(parents=True,exist_ok=True)
    media={r['sha256']:r for r in json.loads((BASE/'temporal_media_index.json').read_text())}
    reports=[]
    for sid,digest in SOURCES.items():
        dest=OUT/sid;dest.mkdir(exist_ok=True)
        meta=dest/'frames.json'
        if meta.exists():reports.append(json.loads(meta.read_text()));continue
        src=media[digest];assert src['date'].startswith('2026-10-')
        path=Path(src['local_path'])
        with path.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest
        cap=cv2.VideoCapture(str(path));assert cap.isOpened()
        frames=[];all_pts=[];i=0;next_tick=0.;started=time.time()
        while True:
            ok,im=cap.read()
            if not ok:break
            t=cap.get(cv2.CAP_PROP_POS_MSEC)/1000
            if all_pts:assert t>all_pts[-1], 'Non-increasing source timestamps'
            all_pts.append(t)
            if t+1e-6>=next_tick:
                fn=f'f_{i:05d}.jpg'
                assert cv2.imwrite(str(dest/fn),im[720:1080,800:1440],[cv2.IMWRITE_JPEG_QUALITY,97])
                frames.append(dict(pts_s=round(t,6),source_frame_index=i,image=fn))
                next_tick+=.25
            i+=1
            if i%1500==0:print(sid,i,round(t,2),round(time.time()-started,1),flush=True)
        cap.release()
        report=dict(source_id=sid,source_sha256=digest,source_file=str(path),date=src['date'],
            roi_xyxy=[800,720,1440,1080],native_frames_decoded=i,all_native_pts_s=all_pts,
            inspection_frames=frames,inspection_policy='first original frame at or after each 0.25 s tick; no interpolation',
            labels_generated=False,model_inference=False,clock_time_verified=False,
            split='October development feasibility only; not independent evaluation')
        meta.write_text(json.dumps(report,indent=2),encoding='utf-8')
        overview=[min(frames,key=lambda r:abs(r['pts_s']-t)) for t in range(0,int(all_pts[-1])+1,2)]
        for n in range(0,len(overview),12):make_sheet(sid,overview[n:n+12],f'overview_{n//12:02d}')
        reports.append(report)
        print('DONE',sid,i,len(frames),flush=True)
    (OUT/'source_manifest.json').write_text(json.dumps([{k:v for k,v in r.items() if k not in ('all_native_pts_s','inspection_frames')} for r in reports],indent=2),encoding='utf-8')

if __name__=='__main__':main()
