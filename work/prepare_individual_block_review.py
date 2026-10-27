import json
from pathlib import Path
import cv2
from PIL import Image, ImageDraw
R=Path(__file__).resolve().parents[1]
S=R/'outputs/facility_dataset/temporal_pipeline/sequence_annotation_v2'
O=R/'outputs/facility_dataset/temporal_pipeline/placement_counter_v2/individual_block_review'
O.mkdir(parents=True,exist_ok=True)
selection={'B020':[10,10.5,13,13.5,14,14.5,15,15.5], 'B022':[19,19.5,20,20.5,21,21.5,22,22.5], 'N21_05':[14.25,14.5,14.75,15,17,17.5,18,18.5],
 'B004':[18,18.5,19,19.5,20,20.5,21,21.5], 'B021':[8,8.5,9,9.5,10,10.5,11,11.5], 'N21_02':[1,2,4,5,6,7,8,9],
 'N01_02':[0.5,2,4,6,8,10,12,14], 'N01_05':[1,3,5,7,9,11,13,15], 'N21_03':[1,2,3,4,5,7,9,11]}
rows=[]
for clip,times in selection.items():
 a=json.loads((S/clip/'annotation.json').read_text(encoding='utf-8-sig'))
 assert a['date'] in {'2026-10-01','2026-10-21'}
 assert a['source_sha256'] not in {'409e37f528e4e47f9b1defd9400998248845c0e2ee8b8b2f2a273c107666de87','ed7258bc653a6cfb777332c03d93178ebf5a86ae0cfebb3ffe5b6087ae24cf0f'}, 'Reserved source cannot enter training review'
 cap=cv2.VideoCapture(str(S/clip/'hands.mp4'))
 sheet=Image.new('RGB',(1280,1560),'white');d=ImageDraw.Draw(sheet)
 for i,t in enumerate(times):
  cap.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,frame=cap.read();assert ok
  assert frame.shape[:2]==(360,640)
  p=O/f'{clip}_{t:06.2f}.jpg';cv2.imwrite(str(p),frame)
  x=i%2*640;y=i//2*390;sheet.paste(Image.open(p),(x,y+30));d.text((x+5,y+8),p.stem,fill='black')
  rows.append(dict(image_path=str(p),clip_id=clip,time_s=t,source_sha256=a['source_sha256'],source_encoded_time_s=a['source_encoded_start_s']+t,date=a['date']))
 cap.release();sheet.save(O/f'{clip}_sheet.jpg')
(O/'candidates.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print(f'Prepared {len(rows)} frames, no automatic labels')
