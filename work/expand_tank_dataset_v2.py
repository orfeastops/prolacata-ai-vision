"""Broad chronological screening pool. Extracted frames are NOT approved labels."""
import json,os,hashlib,io,zipfile,time,msvcrt,traceback
from pathlib import Path
import av
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1]; B=R/'outputs/tank_transfer_training_v1'; O=B/'dataset_v2'; O.mkdir(exist_ok=True)
def save(p,x):
 t=p.with_suffix('.tmp'); t.write_text(json.dumps(x,indent=2),encoding='utf8'); t.replace(p)
def main():
 lock=(O/'extraction.lock').open('a+b'); lock.seek(0); lock.write(b'0'); lock.flush(); lock.seek(0)
 try: msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
 except OSError: raise SystemExit('Extraction already running')
 inv=json.loads((B/'archive_inventory.json').read_text())
 rows=[r for r in inv['records'] if r['media_type']=='video' and r['date']!='20261028' and r['camera'] in [11,15]]
 # Round robin across days/cameras: first results cover all eligible groups.
 groups={}
 for r in sorted(rows,key=lambda r:r['member']): groups.setdefault((r['date'],r['camera']),[]).append(r)
 queue=[g[i] for i in range(max(map(len,groups.values()))) for g in groups.values() if i<len(g)]
 save(O/'source_queue.json',{'locked_test_days':['20261028'],'validation_days':['20261017'],'sources':queue,'note':'Original source split retained in inventory; v2 split assigned separately. Filename hours are not verified decoded coverage.'})
 started=time.time(); done=0; frames=0; errors=0
 for r in queue:
  ident=hashlib.sha256((r['archive']+'|'+r['member']).encode()).hexdigest()[:16]; d=O/'screening'/r['date']/str(r['camera'])/ident; d.mkdir(parents=True,exist_ok=True)
  if (d/'frames.json').exists():
   old=json.loads((d/'frames.json').read_text());done+=1;frames+=len(old['samples']);continue
  save(O/'progress.json',dict(status='extracting',pid=os.getpid(),completed_sources=done,total_sources=len(queue),candidate_frames=frames,errors=errors,current_source=r['member'],elapsed_seconds=time.time()-started))
  try:
   with zipfile.ZipFile(r['archive']) as z: raw=z.read(r['member'])
   samples=[]; first=None; tick=1.0
   with av.open(io.BytesIO(raw)) as c:
    s=c.streams.video[0]; s.codec_context.thread_count=2
    for f in c.decode(s):
     if f.time is None: continue
     if first is None: first=float(f.time)
     t=float(f.time)-first
     if t<tick: continue
     tick=t+30
     p=d/f'{len(samples):05d}.jpg'; im=f.to_image(); im.save(p,quality=93)
     samples.append(dict(image=str(p.relative_to(R)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),relative_pts=t,source_pts=float(f.time),review_status='unreviewed'))
   save(d/'frames.json',dict(source=r,source_sha256=hashlib.sha256(raw).hexdigest(),split='val' if r['date']=='20261017' else 'train',samples=samples,decoded_last_relative_pts=t if first is not None else None,labels_approved=False))
   if samples:
    chosen=samples[:12]; sheet=Image.new('RGB',(960,210*((len(chosen)+2)//3)),'#222'); draw=ImageDraw.Draw(sheet)
    for j,x in enumerate(chosen):
     im=Image.open(R/x['image']); im.thumbnail((320,180)); a=(j%3)*320;b=(j//3)*210;sheet.paste(im,(a,b+30));draw.text((a+3,b+3),f'{r["date"]} cam{r["camera"]} +{x["relative_pts"]:.1f}s',fill='white')
    sheet.save(d/'sheet.jpg')
   done+=1;frames+=len(samples)
  except Exception as e:
   errors+=1;save(d/'error.json',dict(error=str(e),traceback=traceback.format_exc()))
  html=f'<meta charset="utf-8"><h1>Dataset v2 — extraction progress</h1><p>{done}/{len(queue)} videos; {frames} unreviewed candidate frames; {errors} errors.</p><p>28 October held out. 17 October validation. Extracted does not mean visually reviewed or approved for training.</p>'
  (O/'review.html').write_text(html,encoding='utf8')
 save(O/'progress.json',dict(status='screening_extraction_finished_review_pending',completed_sources=done,total_sources=len(queue),candidate_frames=frames,errors=errors,elapsed_seconds=time.time()-started))
if __name__=='__main__':main()
