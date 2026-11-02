"""Independent chronological image selection for rechecking the tank count."""
import datetime as dt
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw

root=Path('outputs/tank_door_audit')
date,start,end,stride,name=sys.argv[1:6]
stride=float(stride)
lo=dt.datetime.strptime(date+start,'%Y%m%d%H:%M:%S')
hi=dt.datetime.strptime(date+end,'%Y%m%d%H:%M:%S')
rows=[]
for p in (root/date).glob('*/scan.json'):
    r=json.loads(p.read_text())
    origin=dt.datetime.strptime(r['basename'][14:28],'%Y%m%d%H%M%S')
    last=None
    for f in r['candidates']:
        stamp=origin+dt.timedelta(seconds=f['t'])
        if lo<=stamp<=hi and (last is None or (stamp-last).total_seconds()>=stride):
            rows.append(dict(**f,source=r['source'],basename=r['basename'],approximate_clock=str(stamp.time())))
            last=stamp
rows.sort(key=lambda f:(f['approximate_clock'],f['basename']))
dest=root/'recheck_20261030'/name
dest.mkdir(parents=True,exist_ok=True)
(dest/'frames.json').write_text(json.dumps(rows,indent=2))
for batch in range(0,len(rows),12):
    sheet=Image.new('RGB',(1920,1400))
    for j,f in enumerate(rows[batch:batch+12]):
        im=Image.open(root/f['image'])
        tile=Image.new('RGB',(640,350))
        tile.paste(im.resize((640,320)),(0,30))
        ImageDraw.Draw(tile).text((4,4),f"#{batch+j} approx {f['approximate_clock']} PTS {f['t']:.1f}",fill='white')
        sheet.paste(tile,((j%3)*640,(j//3)*350))
    sheet.save(dest/f'sheet{batch//12:02}.jpg')
print(name,len(rows),'frames',(len(rows)+11)//12,'sheets')
