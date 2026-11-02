from pathlib import Path
import av,json,hashlib
from PIL import Image,ImageDraw
b=Path('outputs/tank_transfer_training_v1/dataset_v2/heldout_counting/day28_runs');o=b/'boundary_88_89';o.mkdir(exist_ok=True)
tiles=[];rows=[];firsthash=None;matches=[]
for idx in [89,88]:
 with av.open(str(b/f'clip_{idx:03}'/'source.mp4')) as c:
  s=c.streams.video[0];s.codec_context.thread_count=1
  origin=float(s.start_time*s.time_base) if s.start_time is not None else 0
  duration=float(s.duration*s.time_base)
  if idx==88:c.seek(int((origin+max(0,duration-25))/float(s.time_base)),stream=s)
  target=0 if idx==89 else duration-20
  for f in c.decode(video=0):
   if f.time is None:continue
   t=float(f.time)-origin
   if idx==89 and t>15:break
   digest=hashlib.sha256(f.to_ndarray(format='rgb24').tobytes()).hexdigest()
   if idx==89 and firsthash is None:firsthash=digest
   if idx==88 and digest==firsthash:matches.append(t)
   if t<target:continue
   target=t+1.99;im=f.to_image();name=f'clip{idx}_{len(rows):03}.jpg';im.save(o/name,quality=90)
   tile=Image.new('RGB',(640,390));tile.paste(im.resize((640,360)),(0,30));ImageDraw.Draw(tile).text((5,5),f'clip{idx} PTS {t:.3f}',fill='white');tiles.append(tile);rows.append(dict(clip=idx,pts_s=t,file=name))
for start in range(0,len(tiles),9):
 sh=Image.new('RGB',(1920,1170))
 for j,t in enumerate(tiles[start:start+9]):sh.paste(t,((j%3)*640,(j//3)*390))
 sh.save(o/f'sheet_{start//9:02}.jpg')
(o/'evidence.json').write_text(json.dumps(dict(samples=rows,exact_decoded_first_frame89_matches_in88=matches,visual_review_pending=True),indent=2));print(len(rows),matches)












