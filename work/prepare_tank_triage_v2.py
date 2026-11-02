"""Prepare native-source contact sheets; no triage/label approval is implied."""
import json,argparse
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];B=R/'outputs/tank_transfer_training_v1/dataset_v2'
p=argparse.ArgumentParser();p.add_argument('--day',required=True);p.add_argument('--camera',required=True,type=int);p.add_argument('--batch',required=True,type=int);p.add_argument('--cap',type=int,default=64);a=p.parse_args()
assert a.day!='20261028','Protected test day; do not inspect'
assert not (B/f'visual_triage_batch{a.batch:03d}.json').exists(),'Batch already reviewed; use new batch number'
seen=set()
for path in [B/'initial_visual_triage.json',*B.glob('visual_triage_batch*.json')]:
 d=json.loads(path.read_text(encoding='utf8'))
 for row in (d if isinstance(d,list) else d.get('observations',[d])):
  if not row.get('dense_manifest'):
   seen.update((row.get('source_id'),i) for i in row.get('sample_indices',[]))
choices=[]
for folder in ['screening','supplemental_screening']:
 for path in (B/folder/a.day/str(a.camera)).glob('*/frames.json'):
  m=json.loads(path.read_text(encoding='utf8'));assert m['source']['date']==a.day
  new=[(i,s) for i,s in enumerate(m['samples']) if (path.parent.name,i) not in seen]
  if new:choices.append((path,new))
choices.sort(key=lambda x:(-len(x[1]),str(x[0])))
rows=[]
for path,new in choices:
 for i,s in new:
  rows.append([str(path.relative_to(R)),i,s])
  if len(rows)>=a.cap:break
 if len(rows)>=a.cap:break
(R/f'work/tank_review_{a.batch:03d}.json').write_text(json.dumps(rows),encoding='utf8')
for start in range(0,len(rows),16):
 out=Image.new('RGB',(1600,1000),'#222');dr=ImageDraw.Draw(out)
 for j,(path,i,s) in enumerate(rows[start:start+16]):
  im=Image.open(R/s['image']);im.thumbnail((400,225));x=j%4*400;y=j//4*250;out.paste(im,(x,y));dr.text((x+3,y+227),f'{start+j} s{i} {Path(path).parent.name[:8]}',fill='white')
 out.save(B/f'triage_{a.batch:03d}_{start}.jpg')
print(json.dumps({'rows':len(rows),'batch':a.batch,'unreviewed_sources':len(choices)}))
