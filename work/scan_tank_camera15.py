import av,cv2,json,time
from pathlib import Path
root=Path.cwd();out=root/'outputs/tank_door_audit/camera15';out.mkdir(exist_ok=True)
rs=json.loads((root/'outputs/camera_video_collection/inventory.json').read_text())['records'];rs=sorted([r for r in rs if r['camera']==15 and r['date'] in ('20261001','20261003','20261021')],key=lambda r:(r['date'],r['basename']))
start=time.time();errors=[]
for i,r in enumerate(rs):
 folder=out/r['date']/r['sha256'][:16];folder.mkdir(parents=True,exist_ok=True);marker=folder/'scan.json'
 if marker.exists():continue
 try:
  c=av.open(r['source']);s=c.streams.video[0];s.thread_type='AUTO';s.codec_context.thread_count=2;tick=0;base=None;fs=[]
  for f in c.decode(s):
   if f.time is None:continue
   if base is None:base=float(f.time)
   t=float(f.time)-base
   if t<tick:continue
   tick=t+4
   im=cv2.resize(f.to_ndarray(format='bgr24'),(960,540));name=f'{t:08.2f}.jpg';cv2.imwrite(str(folder/name),im,[cv2.IMWRITE_JPEG_QUALITY,85]);fs.append(dict(t=round(t,3),image=str((folder/name).relative_to(out))))
  c.close();marker.write_text(json.dumps(dict(source=r['source'],basename=r['basename'],date=r['date'],frames=fs)))
 except Exception as e:errors.append(dict(source=r['basename'],error=str(e)))
 (out/'progress.json').write_text(json.dumps(dict(completed=i+1,total=len(rs),elapsed=round(time.time()-start),errors=errors)))
 if (i+1)%50==0:print('camera15',i+1,len(rs),flush=True)
(out/'complete.json').write_text(json.dumps(dict(completed=len(rs),errors=errors)))
