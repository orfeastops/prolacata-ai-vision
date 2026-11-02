"""Targeted sequential temporal review; shares the screening OS lock."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,zipfile,io,time,os,msvcrt
import av
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];B=R/'outputs/tank_transfer_training_v1/dataset_v2'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def save(p,d):
 t=p.with_suffix('.tmp');t.write_text(json.dumps(d,indent=2),encoding='utf8');t.replace(p)
lock=(B/'extraction.lock').open('a+b');lock.seek(0)
try:msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
except OSError:raise SystemExit('Shared extraction lock held; do not start another process')
for p in ['progress.json','supplemental_progress.json']:assert read(B/p)['status']=='screening_extraction_finished_review_pending'
f=read(B/'next_dense_followup.json');assert f['date']!='20261028'
assert 0 <= f['start_relative_pts'] < f['end_relative_pts'] and f['end_relative_pts']-f['start_relative_pts'] <= 180, 'Target must be a bounded window up to180 seconds; split longer footage into review windows'
m=read(B/f['manifest']);assert m['source']['date']==f['date'];assert m['split']==('val' if f['date']=='20261017' else 'train')
o=B/'dense_review'/f"{f['date']}_cam{f['camera']}_{f['source_id']}_door"
if (o/'frames.json').exists():raise SystemExit('Target extraction already complete; reuse manifest')
assert not o.exists(),'Partial target already exists; inspect progress before retry'
o.mkdir();state=dict(status='reading_source',pid=os.getpid(),output=str(o.relative_to(B)),source_id=f['source_id'],errors=[],started_at=datetime.now(timezone.utc).isoformat())
save(B/'targeted_dense_progress.json',state)
try:
 with zipfile.ZipFile(m['source']['archive']) as z:data=z.read(m['source']['member'])
 assert hashlib.sha256(data).hexdigest()==m['source_sha256']
 samples=[];origin=None;tick=f['start_relative_pts'];last=None;last_save=time.monotonic();jumps=[]
 with av.open(io.BytesIO(data)) as c:
  stream=c.streams.video[0];stream.codec_context.thread_count=2
  for fr in c.decode(stream):
   if fr.time is None:continue
   t=float(fr.time)
   if origin is None:origin=t
   rel=t-origin
   if last is not None and rel-last>1:jumps.append(dict(before=last,after=rel))
   last=rel
   if time.monotonic()-last_save>2:
    state.update(status='sequential_decoding',decoded_relative_pts=rel,candidate_samples=len(samples));save(B/'targeted_dense_progress.json',state);last_save=time.monotonic()
   if rel>f['end_relative_pts']:break
   if rel+1e-6<tick:continue
   p=o/f'{len(samples):05d}.jpg';fr.to_image().save(p,quality=93)
   samples.append(dict(image=str(p.relative_to(R)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),relative_pts=rel,source_pts=t,review_status='unreviewed'));tick=rel+2
 save(o/'frames.json',dict(source=m['source'],source_sha256=m['source_sha256'],split=m['split'],requested_start_relative_pts=f['start_relative_pts'],requested_end_relative_pts=f['end_relative_pts'],sampling='Sequential decoding from source start; samples at least2 actual PTS seconds apart. No clock synchronization inferred.',decoded_through_relative_pts=last,pts_jumps_over_one_second=jumps,samples=samples,labels_approved=False))
 for start in range(0,len(samples),16):
  out=Image.new('RGB',(1600,1000),'#222');d=ImageDraw.Draw(out)
  for j,s in enumerate(samples[start:start+16]):
   im=Image.open(R/s['image']);im.thumbnail((400,225));x=j%4*400;y=j//4*250;out.paste(im,(x,y));d.text((x+3,y+227),f'{start+j} PTS+{s["relative_pts"]:.1f}',fill='white')
  out.save(o/f'sheet_{start}.jpg')
 state.update(status='extraction_finished_visual_review_pending',candidate_samples=len(samples),decoded_relative_pts=last,completed_at=datetime.now(timezone.utc).isoformat());save(B/'targeted_dense_progress.json',state);print(json.dumps(state))
except Exception as e:
 state.update(status='error',errors=[str(e)]);save(B/'targeted_dense_progress.json',state);raise
finally:lock.close()
