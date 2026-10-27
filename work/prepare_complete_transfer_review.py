"""Extract original frames for temporal supervision; never infer labels here."""
import argparse,json,hashlib
from pathlib import Path
import cv2
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/facility_dataset/temporal_pipeline'
OUT=BASE/'placement_counter_v3/complete_transfer_review'

def main():
    p=argparse.ArgumentParser();p.add_argument('segment');p.add_argument('--step',type=float,default=.5);p.add_argument('--start',type=float,default=0);p.add_argument('--end',type=float);a=p.parse_args()
    rows=json.loads((BASE/'sequence_annotation_v2/count_checkpoint_v2/segments.json').read_text())
    row=next(r for r in rows if r['segment_id']==a.segment)
    assert row['date'] in ['2026-10-01','2026-10-21']
    source=Path(row['media_path']);suffix=f'_range_{a.start:g}_{a.end:g}' if a.end is not None else ''
    dest=OUT/(a.segment+suffix);dest.mkdir(parents=True,exist_ok=True)
    cap=cv2.VideoCapture(str(source));fps=cap.get(cv2.CAP_PROP_FPS);count=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    indices=list(range(round(a.start*fps),min(count,round(a.end*fps)+1) if a.end is not None else count,max(1,round(fps*a.step))));frames=[]
    for n in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES,n);ok,frame=cap.read();assert ok
        path=dest/f'frame_{n:04d}.jpg';cv2.imwrite(str(path),frame)
        frames.append(dict(frame_index=n,time_s=n/fps,image_path=str(path)))
    cap.release()
    for page,start in enumerate(range(0,len(frames),6),1):
        sheet=Image.new('RGB',(1280,3*390),(245,245,245));draw=ImageDraw.Draw(sheet)
        for j,r in enumerate(frames[start:start+6]):
            x=(j%2)*640;y=(j//2)*390
            sheet.paste(Image.open(r['image_path']),(x,y+30))
            draw.text((x+8,y+7),f'{a.segment} | t={r["time_s"]:.3f}s | frame={r["frame_index"]}',fill='black')
        sheet.save(dest/f'sequence_{page:02d}.jpg')
    manifest=dict(segment=row,review_media_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),fps=fps,
        frame_count=count,sampled_frames=frames,labels_generated=False,september_used=False)
    (dest/'review_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(dict(segment=a.segment,frames=len(frames),sheets=(len(frames)+5)//6,directory=str(dest))))

if __name__=='__main__':main()
