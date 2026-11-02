"""Read visible DVR clock evidence only; does not train or alter predictions."""
import json
from pathlib import Path
import cv2
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/facility_dataset/temporal_pipeline'
OUT=BASE/'placement_counter_v5/object_expansion/clock_review'
source=Path(json.loads((BASE/'unseen_test_20260926/two_tank_counter_v1/report.json').read_text())['source'])
def main():
    cv2.setNumThreads(1);OUT.mkdir(parents=True,exist_ok=True)
    targets=[0.,1.,248.,249.,250.,251.,252.,253.];rows=[];tiles=[];k=0;i=0;first=None
    cap=cv2.VideoCapture(str(source));assert cap.isOpened()
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17)
    while k<len(targets):
        ok,frame=cap.read()
        if not ok:break
        pts=cap.get(cv2.CAP_PROP_POS_MSEC)/1000
        if first is None:first=pts
        t=pts-first
        if t>=targets[k]:
            path=OUT/f'clock_{k:02d}.png';cv2.imwrite(str(path),frame[20:110,20:570])
            tile=Image.new('RGB',(550,122),'#101822');tile.paste(Image.open(path),(0,32))
            ImageDraw.Draw(tile).text((5,5),f'Native frame {i} | video {t:.3f}s | PTS {pts:.3f}s',font=font,fill='white')
            tiles.append(tile);rows.append(dict(frame=i,video_seconds=t,original_pts_s=pts,image=str(path)));k+=1
        i+=1
    cap.release();assert len(rows)==len(targets)
    sheet=Image.new('RGB',(550,len(tiles)*122),'#101822')
    for n,tile in enumerate(tiles):sheet.paste(tile,(0,n*122))
    sheet.save(OUT/'clock_evidence.png')
    (OUT/'clock_frames.json').write_text(json.dumps(dict(source=str(source),first_pts=first,rows=rows,wall_clock_not_yet_transcribed=True),indent=2),encoding='utf-8')
    print('Clock evidence extracted, no inference or training performed',flush=True)
if __name__=='__main__':main()
