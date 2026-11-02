import json,cv2,numpy as np
from pathlib import Path
from PIL import Image,ImageDraw
root=Path('outputs/facility_dataset');out=Path('outputs/tank_door_audit/existing');out.mkdir(parents=True,exist_ok=True)
rs=json.loads((root/'frame_manifest.json').read_text());rows=[]
for r in rs:
 if r['camera']!=11:continue
 p=root/r['image'];im=cv2.imread(str(p))
 if im is None:continue
 small=cv2.resize(im,(640,360));hsv=cv2.cvtColor(small[65:240,260:440],cv2.COLOR_BGR2HSV)
 count=int(np.count_nonzero(cv2.inRange(hsv,np.array([88,35,30]),np.array([135,255,255]))))
 if count<25:continue
 rows.append(dict(**r,blue=count))
rows.sort(key=lambda r:(r['date'],r['source_basename'],r['relative_pts_seconds'] or 0))
(out/'frames.json').write_text(json.dumps(rows))
for batch in range(0,len(rows),24):
 sheet=Image.new('RGB',(1600,1080))
 for j,r in enumerate(rows[batch:batch+24]):
  im=Image.open(root/r['image']);w,h=im.size
  crop=im.crop((int(w*.38),int(h*.14),int(w*.71),int(h*.73))).resize((400,245))
  tile=Image.new('RGB',(400,270));tile.paste(crop,(0,25));draw=ImageDraw.Draw(tile)
  draw.text((3,2),f"#{batch+j} {r['source_basename'][14:28]} +{r['relative_pts_seconds']} b={r['blue']}",fill='white')
  sheet.paste(tile,((j%4)*400,(j//4)*180))
 # Taller 4x6 layout preserves all panels.
 sheet=Image.new('RGB',(1600,1620))
 for j,r in enumerate(rows[batch:batch+24]):
  im=Image.open(root/r['image']);w,h=im.size;tile=Image.new('RGB',(400,270))
  tile.paste(im.crop((int(w*.38),int(h*.14),int(w*.71),int(h*.73))).resize((400,245)),(0,25))
  ImageDraw.Draw(tile).text((3,2),f"#{batch+j} {r['source_basename'][14:28]} +{r['relative_pts_seconds']} b={r['blue']}",fill='white')
  sheet.paste(tile,((j%4)*400,(j//4)*270))
 sheet.save(out/f'sheet{batch//24:02}.jpg')
print('frames',len(rows),'sheets',(len(rows)+23)//24)
