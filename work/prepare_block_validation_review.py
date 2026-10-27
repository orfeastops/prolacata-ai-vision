import json
from pathlib import Path
import cv2
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];B=R/'outputs/facility_dataset/temporal_pipeline'
O=B/'placement_counter_v2/individual_block_validation';O.mkdir(exist_ok=True)
reserved=json.loads((B/'placement_counter_v2/individual_block_review/validation_reservation.json').read_text())['sources']
a=json.loads((B/'sequence_annotation_v2/B023/annotation.json').read_text(encoding='utf-8-sig'))
reserved.append(dict(clip_id='B023',source_sha256=a['source_sha256']))
rows=[]
for src in reserved:
 clip=src['clip_id'];base=B/'sequence_annotation_v2'/clip
 a=json.loads((base/'annotation.json').read_text(encoding='utf-8-sig'));assert a['source_sha256']==src['source_sha256']
 times=[10,12,14,16,18,20,22,24,15,15.5,17,17.5] if clip=='B023' else [2,6,10,14]
 cap=cv2.VideoCapture(str(base/'hands.mp4'));sheet=Image.new('RGB',(1280,390*((len(times)+1)//2)),'white');d=ImageDraw.Draw(sheet)
 for i,t in enumerate(times):
  cap.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,im=cap.read();assert ok
  p=O/f'{clip}_{t:06.2f}.jpg';cv2.imwrite(str(p),im)
  x=i%2*640;y=i//2*390;sheet.paste(Image.open(p),(x,y+30));d.text((x+5,y+8),p.stem+' | RESERVED VALIDATION',fill='black')
  rows.append(dict(image_path=str(p),clip_id=clip,source_sha256=a['source_sha256'],time_s=t,source_encoded_time_s=a['source_encoded_start_s']+t,role='validation_only',training_eligible=False))
 cap.release();sheet.save(O/f'{clip}_sheet.jpg')
(O/'candidates.json').write_text(json.dumps(rows,indent=2))
