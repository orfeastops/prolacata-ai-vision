from pathlib import Path
import av,json
from PIL import Image,ImageDraw
b=Path('outputs/tank_transfer_training_v1/dataset_v2/heldout_counting');out=b/'fullclip_dense_review';out.mkdir(exist_ok=True)
with av.open(str(b/'test28_camera11_094400.mp4')) as c:
 s=c.streams.video[0];s.codec_context.thread_count=2
 origin=next(f for f in c.decode(video=0) if f.time is not None).time
 for name,start,end in [('departure2',620,656),('departure3',1050,1090)]:
  c.seek(int((origin+max(0,start-45))/s.time_base),stream=s,backward=True);tiles=[];rows=[];target=start
  for f in c.decode(video=0):
   if f.time is None:continue
   t=float(f.time-origin)
   if t>end:break
   if t<target:continue
   target=t+1.999;im=f.to_image();file=f'{name}_{len(rows):03}.jpg';im.save(out/file,quality=92)
   tile=Image.new('RGB',(640,390));tile.paste(im.resize((640,360)),(0,30));ImageDraw.Draw(tile).text((5,5),f'{name} PTS {t:.3f}',fill='white');tiles.append(tile);rows.append({'file':file,'pts_s':t})
  for i in range(0,len(tiles),9):
   sheet=Image.new('RGB',(1920,1170))
   for j,tile in enumerate(tiles[i:i+9]):sheet.paste(tile,((j%3)*640,(j//3)*390))
   sheet.save(out/f'{name}_sheet_{i//9}.jpg',quality=91)
  (out/f'{name}_samples.json').write_text(json.dumps(rows,indent=2))
  print(name,len(rows),flush=True)
