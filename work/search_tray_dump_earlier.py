import json,cv2
from pathlib import Path
from PIL import Image,ImageDraw
out=Path('outputs/tray_dump_search_earlier');out.mkdir(exist_ok=True)
rs=json.loads(Path('outputs/camera_video_collection/inventory.json').read_text())['records']
sel=[r for r in rs if r['camera']==11 and ((r['date']=='20260926' and '141500'<=r['basename'][22:28]<'144000') or (r['date']=='20261001' and '134000'<=r['basename'][22:28]<'141000') or (r['date']=='20261021' and '140000'<=r['basename'][22:28]<'142500'))]
print('sources',len(sel),flush=True)
records=[];panels=[];sheet=0
for si,r in enumerate(sel):
 cap=cv2.VideoCapture(r['source']);tick=0
 while cap.grab():
  t=cap.get(cv2.CAP_PROP_POS_MSEC)/1000
  if t<tick:continue
  ok,im=cap.retrieve()
  if not ok:continue
  tick=t+8
  ident=len(records);p=out/f'f{ident:04}.jpg';cv2.imwrite(str(p),im)
  records.append(dict(id=ident,source=r['source'],name=r['basename'],t=t,image=str(p)))
  tile=Image.new('RGB',(480,292));tile.paste(Image.fromarray(cv2.cvtColor(im,cv2.COLOR_BGR2RGB)).resize((480,270)),(0,22));ImageDraw.Draw(tile).text((4,3),f'{ident} {r["date"]} {r["basename"][22:28]} +{t:.1f}s',fill='white');panels.append(tile)
  if len(panels)==20:
   canvas=Image.new('RGB',(1920,1460))
   for j,x in enumerate(panels):canvas.paste(x,((j%4)*480,(j//4)*292))
   canvas.save(out/f'sheet{sheet:02}.jpg');sheet+=1;panels=[]
 cap.release()
 print(si,r['basename'],len(records),flush=True)
if panels:
 canvas=Image.new('RGB',(1920,292*((len(panels)+3)//4)))
 for j,x in enumerate(panels):canvas.paste(x,((j%4)*480,(j//4)*292))
 canvas.save(out/f'sheet{sheet:02}.jpg')
(out/'frames.json').write_text(json.dumps(records,indent=2))
