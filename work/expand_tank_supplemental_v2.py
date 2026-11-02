"""Screen byte-distinct supplemental sources using the shared extraction OS lock."""
import json,hashlib,os,time,msvcrt,traceback
from pathlib import Path
import av
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1]
B=R/'outputs/tank_transfer_training_v1/dataset_v2'
def save(p,x):
 t=p.with_suffix('.tmp');t.write_text(json.dumps(x,indent=2),encoding='utf8');t.replace(p)
def main():
 lock=(B/'extraction.lock').open('a+b');lock.seek(0)
 try:msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
 except OSError:raise SystemExit('Another extraction owns the shared OS lock')
 assert json.loads((B/'progress.json').read_text(encoding='utf8'))['status']=='screening_extraction_finished_review_pending'
 rows=json.loads((B/'supplemental_extraction_queue.json').read_text(encoding='utf8'))['sources']
 done=frames=errors=0;started=time.time()
 for r in rows:
  assert r['date']!='20261028'
  d=B/'supplemental_screening'/r['date']/str(r['camera'])/r['sha256'][:16];d.mkdir(parents=True,exist_ok=True)
  if (d/'frames.json').exists():
   done+=1;frames+=len(json.loads((d/'frames.json').read_text(encoding='utf8'))['samples']);continue
  save(B/'supplemental_progress.json',dict(status='extracting',pid=os.getpid(),completed_sources=done,total_sources=len(rows),candidate_frames=frames,errors=errors,current_source=r['available_path']))
  try:
   p=Path(r['available_path']);assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']
   samples=[];first=None;tick=1.;last=None
   with av.open(str(p)) as c:
    s=c.streams.video[0];s.codec_context.thread_count=2
    for f in c.decode(s):
     if f.time is None:continue
     if first is None:first=float(f.time)
     t=float(f.time)-first;last=t
     if t<tick:continue
     tick=t+30.;out=d/f'{len(samples):05d}.jpg';f.to_image().save(out,quality=93)
     samples.append(dict(image=str(out.relative_to(R)),sha256=hashlib.sha256(out.read_bytes()).hexdigest(),relative_pts=t,source_pts=float(f.time),review_status='unreviewed'))
   save(d/'frames.json',dict(source=r,source_sha256=r['sha256'],split='val' if r['date']=='20261017' else 'train',samples=samples,decoded_last_relative_pts=last,labels_approved=False))
   if samples:
    chosen=samples[:12];im=Image.new('RGB',(960,210*((len(chosen)+2)//3)),'#222');dr=ImageDraw.Draw(im)
    for j,x in enumerate(chosen):
     tile=Image.open(R/x['image']);tile.thumbnail((320,180));u=j%3*320;v=j//3*210;im.paste(tile,(u,v+30));dr.text((u+2,v+2),f'{r["date"]} cam{r["camera"]} +{x["relative_pts"]:.1f}s',fill='white')
    im.save(d/'sheet.jpg')
   done+=1;frames+=len(samples)
  except Exception as e:
   errors+=1;save(d/'error.json',dict(error=str(e),traceback=traceback.format_exc()))
 save(B/'supplemental_progress.json',dict(status='screening_extraction_finished_review_pending',completed_sources=done,total_sources=len(rows),candidate_frames=frames,errors=errors,elapsed_seconds=time.time()-started))
if __name__=='__main__':main()
