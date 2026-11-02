import json,sys
from pathlib import Path
from PIL import Image,ImageDraw
root=Path('outputs/tank_door_audit');date=sys.argv[1];ids=[int(x) for x in sys.argv[2].split(',')]
gs=json.loads((root/'proposals'/date/'proposals.json').read_text());out=root/'event_review'/date;out.mkdir(parents=True,exist_ok=True)
for idx in ids:
 g=gs[idx];p=root/Path(g['peak']['image']).parent/'scan.json';r=json.loads(p.read_text())
 lo=max(0,g['start']-8);hi=g['end']+12;fs=[f for f in r['candidates'] if lo<=f['t']<=hi]
 if '--peak' in sys.argv:
  lo=max(0,g['peak']['t']-12);hi=g['peak']['t']+20;fs=[f for f in r['candidates'] if lo<=f['t']<=hi]
 if not fs:continue
 choose=[fs[round(i*(len(fs)-1)/7)] for i in range(8)]
 sheet=Image.new('RGB',(1920,800))
 for j,f in enumerate(choose):
  im=Image.open(root/f['image']);w,h=im.size;tile=Image.new('RGB',(480,400))
  tile.paste(im.crop((0,15,310,50)).resize((480,54)),(0,22))
  tile.paste(im.crop((w*.37,h*.16,w*.71,h*.76)).resize((480,324)),(0,76))
  ImageDraw.Draw(tile).text((3,3),f"{g['id']} +{f['t']:.2f}s",fill='white');sheet.paste(tile,((j%4)*480,(j//4)*400))
 sheet.save(out/(f'{idx:03}_peak.jpg' if '--peak' in sys.argv else f'{idx:03}.jpg'))
print('rendered',date,ids)
