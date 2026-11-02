import json,cv2
from pathlib import Path
from PIL import Image,ImageDraw
rs=json.loads(Path('outputs/camera_video_collection/inventory.json').read_text())['records'];r=next(x for x in rs if x['basename']=='Camera_11_DVR_20261021141803_20261021142941_2899458.mp4')
out=Path('outputs/tray_dump_detail_oct21');out.mkdir(exist_ok=True);cap=cv2.VideoCapture(r['source']);panels=[];tick=560.;j=0
while cap.grab():
 t=cap.get(cv2.CAP_PROP_POS_MSEC)/1000
 if t>625:break
 if t<tick:continue
 ok,im=cap.retrieve()
 if not ok:continue
 tick=t+1
 h,w=im.shape[:2];im=im[int(h*.57):h,int(w*.38):int(w*.84)]
 cv2.imwrite(str(out/f'{t:.2f}.jpg'),im)
 tile=Image.new('RGB',(450,360));tile.paste(Image.fromarray(cv2.cvtColor(im,cv2.COLOR_BGR2RGB)).resize((450,338)),(0,22));ImageDraw.Draw(tile).text((4,3),f'{r["basename"]} +{t:.2f}',fill='white');panels.append(tile)
 if len(panels)==12:
  sheet=Image.new('RGB',(1800,1080))
  for k,x in enumerate(panels):sheet.paste(x,((k%4)*450,(k//4)*360))
  sheet.save(out/f'sheet{j}.jpg');panels=[];j+=1
if panels:
 sheet=Image.new('RGB',(1800,1080))
 for k,x in enumerate(panels):sheet.paste(x,((k%4)*450,(k//4)*360))
 sheet.save(out/f'sheet{j}.jpg')
print(r['source'])

