"""Render selected original test frames for visual inspection only."""
import argparse,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/facility_dataset/temporal_pipeline/unseen_test_20260926/assistant_count_audit_20261029'
def main():
    p=argparse.ArgumentParser();p.add_argument('start',type=float);p.add_argument('end',type=float)
    p.add_argument('--step',type=float,default=.5);p.add_argument('--columns',type=int,default=3)
    p.add_argument('--width',type=int,default=640)
    a=p.parse_args();index=json.loads((OUT/'evidence_index.json').read_text())
    rows=[r for r in index['rows'] if a.start<=r['target_s']<a.end]
    rows=rows[::max(1,round(a.step/.25))]
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20);tile_h=round(a.width*360/640)+26
    for page in range((len(rows)+11)//12):
        selected=rows[page*12:(page+1)*12]
        sheet=Image.new('RGB',(a.columns*a.width,((len(selected)+a.columns-1)//a.columns)*tile_h),'#17202a')
        draw=ImageDraw.Draw(sheet)
        for j,r in enumerate(selected):
            x,y=j%a.columns*a.width,j//a.columns*tile_h
            sheet.paste(Image.open(OUT/r['image']).resize((a.width,tile_h-26)),(x,y+26))
            draw.text((x+4,y+2),f"{r['time_s']:.3f}s | native {r['native_frame']}",fill='white',font=font)
        name=f'detail_{a.start:g}_{a.end:g}_{a.step:g}_{page}.jpg';sheet.save(OUT/name,quality=96)
        print(str(OUT/name))
if __name__=='__main__':main()
