from pathlib import Path
from PIL import Image, ImageDraw
import sys, json
root=Path('outputs/tank_door_audit')
date=sys.argv[1]
for p in (root/'camera15_matches'/date).glob('*.json'):
    fs=json.loads(p.read_text())
    if not fs:continue
    for b in range(0,len(fs),8):
        sheet=Image.new('RGB',(1920,700))
        for j,f in enumerate(fs[b:b+8]):
            im=Image.open(root/'camera15'/f['image'])
            tile=Image.new('RGB',(480,350))
            ImageDraw.Draw(tile).text((3,1),p.stem+' '+str(b+j)+' +'+str(f['t']),fill='white')
            tile.paste(im.crop((0,15,310,50)).resize((480,48)),(0,20))
            tile.paste(im.crop((580,0,870,180)).resize((480,282)),(0,68))
            sheet.paste(tile,((j%4)*480,(j//4)*350))
        sheet.save(p.parent/f'{p.stem}_detail{b//8:02}.jpg')
print('done')
