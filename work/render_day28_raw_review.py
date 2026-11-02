from pathlib import Path
import json,av,argparse
from PIL import Image,ImageDraw
p=argparse.ArgumentParser();p.add_argument('--indices',nargs='+',type=int,required=True);p.add_argument('--step',type=float,default=5);p.add_argument('--start',type=float,default=0);p.add_argument('--end',type=float,default=None);a=p.parse_args()
b=Path('outputs/tank_transfer_training_v1/dataset_v2/heldout_counting/day28_runs')
for idx in a.indices:
 d=b/f'clip_{idx:03}';folder='raw_review' if a.step==5 else f'raw_review_{a.step:g}s';folder+=f'_{a.start:g}_{a.end:g}' if a.end is not None else '';o=d/folder;o.mkdir(exist_ok=True);tiles=[];rows=[];origin=None;target=a.start
 with av.open(str(d/'source.mp4')) as c:
  c.streams.video[0].codec_context.thread_count=1
  for f in c.decode(video=0):
   if f.time is None:continue
   if origin is None:origin=float(f.time)
   t=float(f.time)-origin
   if a.end is not None and t>a.end:break
   if t<target:continue
   target=t+a.step-.001;im=f.to_image();name=f'raw_{len(rows):03}.jpg';im.save(o/name,quality=88);rows.append({'file':name,'pts_s':t})
   tile=Image.new('RGB',(640,390));tile.paste(im.resize((640,360)),(0,30));ImageDraw.Draw(tile).text((5,5),f'clip{idx:03} PTS{t:.3f}',fill='white');tiles.append(tile)
 for start in range(0,len(tiles),9):
  sh=Image.new('RGB',(1920,1170))
  for j,tile in enumerate(tiles[start:start+9]):sh.paste(tile,((j%3)*640,(j//3)*390))
  sh.save(o/f'sheet_{start//9:02}.jpg',quality=89)
 (o/'samples.json').write_text(json.dumps(rows,indent=2));print(idx,len(rows),flush=True)
