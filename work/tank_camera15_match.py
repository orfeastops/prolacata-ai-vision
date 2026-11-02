"""Create visual cross-camera evidence, never infer a match from time alone."""
import json, sys, datetime
from pathlib import Path
from PIL import Image, ImageDraw

root = Path('outputs/tank_door_audit')
date, clock, name = sys.argv[1:4]
target = datetime.datetime.strptime(date + clock, '%Y%m%d%H:%M:%S')
rows = []
for p in (root/'camera15'/date).glob('*/scan.json'):
    r = json.loads(p.read_text())
    start = datetime.datetime.strptime(r['basename'][14:28], '%Y%m%d%H%M%S')
    for f in r['frames']:
        stamp = start + datetime.timedelta(seconds=f['t'])
        delta = (stamp-target).total_seconds()
        if -24 <= delta <= 100:
            rows.append(dict(**f, basename=r['basename'], approximate_clock=str(stamp.time()), delta=delta))
rows.sort(key=lambda f: (f['approximate_clock'], f['basename']))
dest = root/'camera15_matches'/date
dest.mkdir(parents=True, exist_ok=True)
(dest/f'{name}.json').write_text(json.dumps(rows, indent=2))
for batch in range(0,len(rows),12):
    sheet = Image.new('RGB',(1920,1200))
    for j,f in enumerate(rows[batch:batch+12]):
        im=Image.open(root/'camera15'/f['image'])
        tile=Image.new('RGB',(640,300))
        tile.paste(im.resize((640,270)),(0,30))
        ImageDraw.Draw(tile).text((4,4),f"{name} frame {batch+j}: approximate {f['approximate_clock']} PTS {f['t']:.1f}",fill='white')
        sheet.paste(tile,((j%3)*640,(j//3)*300))
    sheet.save(dest/f'{name}_{batch//12:02}.jpg')
print(name,'frames',len(rows),'sheets',(len(rows)+11)//12)
