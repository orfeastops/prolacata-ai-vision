from pathlib import Path
from PIL import Image,ImageDraw
import cv2,numpy as np,json,sys
cv2.setNumThreads(1)
out=Path('outputs/tank_door_audit');date=sys.argv[1];dest=out/'proposals'/date;dest.mkdir(parents=True,exist_ok=True)
cached={}
if '--incremental' in sys.argv and (dest/'proposals.json').exists():
 for g in json.loads((dest/'proposals.json').read_text()):cached.setdefault(g['basename'],[]).append(g)
groups=[]
for p in sorted((out/date).glob('*/scan.json')):
 r=json.loads(p.read_text());picked=[];previous=None;previous_t=None
 if r['basename'] in cached:
  groups.extend(cached[r['basename']]);continue
 for f in r['candidates']:
  im=cv2.imread(str(out/f['image']));sm=cv2.resize(im,(640,360));hsv=cv2.cvtColor(sm[125:255,260:410],cv2.COLOR_BGR2HSV)
  b=int(np.count_nonzero(cv2.inRange(hsv,np.array([88,40,30]),np.array([135,255,255]))))
  gray=cv2.cvtColor(sm[120:245,280:410],cv2.COLOR_BGR2GRAY)
  motion=9999 if previous is None or f['t']-previous_t>5 else int(np.count_nonzero(cv2.absdiff(gray,previous)>25))
  previous=gray;previous_t=f['t']
  if b>=20 and motion>=180:picked.append(dict(**f,gate_blue=b,motion=motion))
 batches=[]
 for f in picked:
  if batches and f['t']-batches[-1][-1]['t']<=6:batches[-1].append(f)
  else:batches.append([f])
 for fs in batches:
  peak=max(fs,key=lambda f:f['gate_blue']*min(f['motion'],3000))
  groups.append(dict(source=r['source'],basename=r['basename'],start=fs[0]['t'],end=fs[-1]['t'],frames=fs,peak=peak))
groups.sort(key=lambda r:(r['basename'],r['start']))
for i,g in enumerate(groups):g['id']=f'{date}_{i:03}'
(dest/'proposals.json').write_text(json.dumps(groups,indent=2))
for batch in range(0,len(groups),12):
 sheet=Image.new('RGB',(1600,1080))
 for j,g in enumerate(groups[batch:batch+12]):
  im=Image.open(out/g['peak']['image']);w,h=im.size
  tile=Image.new('RGB',(400,360));tile.paste(im.crop((w*.37,h*.16,w*.71,h*.76)).resize((400,320)),(0,40))
  draw=ImageDraw.Draw(tile);draw.text((3,2),g['id']+' '+g['basename'][22:28],fill='white');draw.text((3,18),f"+{g['start']:.1f}..{g['end']:.1f} peak {g['peak']['t']:.1f}",fill='white')
  sheet.paste(tile,((j%4)*400,(j//4)*360))
 sheet.save(dest/f'sheet{batch//12:02}.jpg')
print(date,'sources',len(list((out/date).glob('*/scan.json'))),'groups',len(groups),'sheets',(len(groups)+11)//12)
