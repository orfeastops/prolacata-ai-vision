from pathlib import Path
import av,sys,json
from PIL import Image,ImageDraw
b=Path('outputs/tank_transfer_training_v1/dataset_v2/heldout_counting');freeze=json.loads((b/'frozen_test_protocol.json').read_text());out=b/'test28_review';out.mkdir(exist_ok=True)
samples=[];origin=None;next_t=0;tiles=[]
with av.open(str(b/'test28_camera11_094400.mp4')) as c:
 c.streams.video[0].codec_context.thread_count=2
 for f in c.decode(video=0):
  if f.time is None:continue
  if origin is None:origin=float(f.time)
  t=float(f.time)-origin
  if t>180:break
  if t+1e-6<next_t:continue
  next_t+=2;im=f.to_image();name=f'raw_{len(samples):03}.jpg';im.save(out/name,quality=90)
  # Fixed camera11 doorway/approach view based on validation geometry, not detections.
  tile=Image.new('RGB',(480,300));tile.paste(im.crop((700,120,1280,880)).resize((480,270)),(0,30));ImageDraw.Draw(tile).text((5,5),f'{len(samples):03} PTS {t:.2f}s',fill='white');tiles.append(tile);samples.append({'file':name,'pts_s':t})
for start in range(0,len(tiles),12):
 sh=Image.new('RGB',(1920,900))
 for j,im in enumerate(tiles[start:start+12]):sh.paste(im,((j%4)*480,(j//4)*300))
 sh.save(out/f'sheet_{start//12:02}.jpg',quality=92)
(out/'samples.json').write_text(json.dumps(samples,indent=2));print(len(samples),'independent raw samples')
