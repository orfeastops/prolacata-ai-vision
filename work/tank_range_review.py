import sys, json
from pathlib import Path
from PIL import Image,ImageDraw
root=Path('outputs/tank_door_audit');date=sys.argv[1];idx=int(sys.argv[2]);lo=float(sys.argv[3]);hi=float(sys.argv[4])
g=json.loads((root/'proposals'/date/'proposals.json').read_text())[idx]
r=json.loads((root/Path(g['peak']['image']).parent/'scan.json').read_text())
fs=[f for f in r['candidates'] if lo<=f['t']<=hi]
choose=[fs[round(i*(len(fs)-1)/15)] for i in range(16)]
sheet=Image.new('RGB',(1920,1600))
for j,f in enumerate(choose):
 im=Image.open(root/f['image']);w,h=im.size;tile=Image.new('RGB',(480,400))
 tile.paste(im.crop((0,15,310,50)).resize((480,54)),(0,22))
 tile.paste(im.crop((w*.37,h*.16,w*.71,h*.76)).resize((480,324)),(0,76))
 ImageDraw.Draw(tile).text((3,3),f"{g['id']} +{f['t']:.2f}s",fill='white');sheet.paste(tile,((j%4)*480,(j//4)*400))
dest=root/'event_review'/date/f'{idx:03}_range_{lo:.0f}_{hi:.0f}.jpg';sheet.save(dest);print(dest)
