import json
from pathlib import Path
import cv2
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];B=R/'outputs/facility_dataset/temporal_pipeline';O=B/'placement_counter_v2/block_orientation_expansion';O.mkdir(exist_ok=True)
selection={'N01_02':[5,5.25,5.5,5.75,6.25,6.5], 'B022':[19.25,19.75,20.25,20.75,21.25,21.5], 'B020':[13.75,14.25,14.75], 'N21_03':[1.5,1.75,2.25,2.5]}
rows=[]
held={r['source_sha256'] for r in json.loads((B/'placement_counter_v2/individual_block_validation/frozen_labels.json').read_text())['frames']}
for clip,times in selection.items():
 s=B/'sequence_annotation_v2'/clip;a=json.loads((s/'annotation.json').read_text(encoding='utf-8-sig'));assert a['source_sha256'] not in held
 assert a['date'] in {'2026-10-01','2026-10-21'}
 cap=cv2.VideoCapture(str(s/'hands.mp4'));sheet=Image.new('RGB',(1280,390*((len(times)+1)//2)),'white');d=ImageDraw.Draw(sheet)
 for i,t in enumerate(times):
  cap.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,im=cap.read();assert ok
  p=O/f'{clip}_{t:06.2f}.jpg';cv2.imwrite(str(p),im)
  x=i%2*640;y=i//2*390;sheet.paste(Image.open(p),(x,y+30));d.text((x+5,y+8),p.stem,fill='black')
  rows.append(dict(image_path=str(p),clip_id=clip,source_sha256=a['source_sha256'],time_s=t,date=a['date']))
 cap.release();sheet.save(O/f'{clip}_sheet.jpg')
(O/'candidates.json').write_text(json.dumps(rows,indent=2))
