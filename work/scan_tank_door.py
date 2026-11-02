import av,cv2,numpy as np,json,time,re,concurrent.futures,datetime
from pathlib import Path
ROOT=Path.cwd(); OUT=ROOT/'outputs/tank_door_audit';OUT.mkdir(exist_ok=True)
rs=json.loads((ROOT/'outputs/camera_video_collection/inventory.json').read_text())['records']
rs=sorted([r for r in rs if r['camera']==11],key=lambda r:(r['date'],r['basename']))
def scan(r):
 ident=r['sha256'][:16]; folder=OUT/r['date']/ident;folder.mkdir(parents=True,exist_ok=True)
 marker=folder/'scan.json'
 if marker.exists():return json.loads(marker.read_text())
 c=av.open(r['source']);s=c.streams.video[0];s.thread_type='AUTO';s.codec_context.thread_count=2
 base=None;tick=0.;frames=[];n=0
 for f in c.decode(s):
  n+=1
  if f.time is None:continue
  if base is None:base=float(f.time)
  t=float(f.time)-base
  if t<tick:continue
  tick=t+2
  im=f.to_ndarray(format='bgr24'); small=cv2.resize(im,(640,360))
  # Candidate gate only: color never supplies a final tank count.
  roi=small[65:240,260:440];hsv=cv2.cvtColor(roi,cv2.COLOR_BGR2HSV)
  blue=cv2.inRange(hsv,np.array([88,35,30]),np.array([135,255,255]))
  blue_count=int(np.count_nonzero(blue))
  if blue_count>=25:
   name=f'{t:08.2f}.jpg';cv2.imwrite(str(folder/name),cv2.resize(im,(960,540)),[cv2.IMWRITE_JPEG_QUALITY,86])
   frames.append(dict(t=round(t,3),blue=blue_count,image=str((folder/name).relative_to(OUT))))
 c.close()
 result=dict(source=r['source'],basename=r['basename'],date=r['date'],sha256=r['sha256'],native_frames=n,last_pts=t,candidates=frames)
 marker.write_text(json.dumps(result));return result
if __name__=='__main__':
 start=time.time();done=[];errors=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  jobs={pool.submit(scan,r):r for r in rs}
  for fut in concurrent.futures.as_completed(jobs):
   try:done.append(fut.result())
   except Exception as e:errors.append(dict(source=jobs[fut]['basename'],error=str(e)))
   p=dict(completed=len(done),total=len(rs),errors=errors,candidate_frames=sum(len(d['candidates']) for d in done),elapsed=round(time.time()-start))
   (OUT/'progress.json').write_text(json.dumps(p))
   if len(done)%25==0:print(json.dumps(p),flush=True)
 (OUT/'scan_complete.json').write_text(json.dumps(dict(sources=done,errors=errors)))
 print('DONE',len(done),'errors',len(errors),flush=True)
