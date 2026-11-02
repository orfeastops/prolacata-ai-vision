"""Extract unannotated evidence for a human/assistant visual count, never training."""
import json
from pathlib import Path
import cv2
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'outputs/facility_dataset/temporal_pipeline'
OUT = BASE / 'unseen_test_20260926/assistant_count_audit_20261029'
SOURCE = ROOT / 'work/unseen_test_20260926/media/794fc5b166d6b60e8e0352ec4a46a0aa0089028ebef3c25994668d5be5a0435e_Camera_11_DVR_20260926142542_20260926143911_94077690.mp4'

def main():
    sources = list((ROOT / 'work/unseen_test_20260926/media').glob('*Camera_11_DVR_20260926142542_20260926143911_94077690.mp4'))
    assert len(sources) == 1, sources
    source = sources[0]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'frames').mkdir(exist_ok=True)
    (OUT / 'sheets').mkdir(exist_ok=True)
    cap = cv2.VideoCapture(str(source)); assert cap.isOpened()
    cv2.setNumThreads(2)
    rows, overviews = [], []
    target, next_overview, frame_id, first = 0., 0., 0, None
    while True:
        ok, frame = cap.read()
        if not ok: break
        pts = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
        if first is None: first = pts
        t = pts - first
        if t + 1e-8 >= target:
            name = f'{len(rows):05d}.jpg'
            assert cv2.imwrite(str(OUT / 'frames' / name), frame[720:1080,800:1440], [cv2.IMWRITE_JPEG_QUALITY,94])
            rows.append(dict(i=len(rows),native_frame=frame_id,time_s=t,target_s=target,image='frames/'+name))
            target += .25
        if t + 1e-8 >= next_overview:
            small = cv2.resize(frame, (640,360))
            overviews.append((t, Image.fromarray(cv2.cvtColor(small,cv2.COLOR_BGR2RGB))))
            next_overview += 20
        frame_id += 1
    cap.release()
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
    for page in range((len(rows[::4]) + 15)//16):
        subset = rows[::4][page*16:(page+1)*16]
        sheet = Image.new('RGB',(1920,4*296),'#17202a'); draw = ImageDraw.Draw(sheet)
        for j,r in enumerate(subset):
            x,y=(j%4)*480,(j//4)*296
            sheet.paste(Image.open(OUT/r['image']).resize((480,270)),(x,y+26))
            draw.text((x+5,y+2),f"{r['time_s']:.2f}s | frame {r['native_frame']}",font=font,fill='white')
        sheet.save(OUT/'sheets'/f'page_{page:02d}.jpg',quality=95)
    for page in range((len(overviews)+11)//12):
        sheet=Image.new('RGB',(1920,4*386),'#17202a');draw=ImageDraw.Draw(sheet)
        for j,(t,img) in enumerate(overviews[page*12:(page+1)*12]):
            x,y=(j%3)*640,(j//3)*386
            sheet.paste(img,(x,y+26));draw.text((x+5,y+2),f'{t:.2f}s',font=font,fill='white')
        sheet.save(OUT/f'overview_{page:02d}.jpg',quality=94)
    (OUT/'evidence_index.json').write_text(json.dumps(dict(source=str(source),native_frames=frame_id,
        duration_s=rows[-1]['time_s'],sampling_seconds=.25,roi=[800,720,1440,1080],rows=rows,
        purpose='Visual test audit only. Not training labels. Predictions not used to select evidence.',
        reviewer_aware_of_model_totals=True,user_totals_received=False),indent=2),encoding='utf-8')
    print(json.dumps(dict(frames_extracted=len(rows),native_frames=frame_id,pages=(len(rows[::4])+15)//16,output=str(OUT))),flush=True)

if __name__=='__main__':main()
