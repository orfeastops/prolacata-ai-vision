"""Native-frame October evidence clips; labels are assistant review, not inference."""
import json,time
from pathlib import Path
import cv2,numpy as np
from build_tray_inventory_audit import OUT
from tray_audit_selection import SELECTION

def main():
 cv2.setNumThreads(2);dest=OUT/'clips';dest.mkdir(exist_ok=True)
 done=[]
 for sid in ['O01','O21']:
  meta=json.loads((OUT/sid/'frames.json').read_text());allpts=np.asarray(meta['all_native_pts_s'])
  rows=[r for r in SELECTION if r[1]==sid];writers={};info={}
  for ident,_,a,b,_ in rows:
   ix=np.flatnonzero((allpts>=a)&(allpts<b));ts=allpts[ix]
   fps=len(ts)/(ts[-1]-ts[0]+float(np.median(np.diff(ts))))
   writer=cv2.VideoWriter(str(dest/(ident+'.webm')),cv2.VideoWriter_fourcc(*'VP80'),fps,(640,416))
   assert writer.isOpened();writers[ident]=writer
   info[ident]=dict(id=ident,source_id=sid,path='clips/'+ident+'.webm',
       native_frames_expected=len(ix),native_frames_written=0,first_source_frame=int(ix[0]),last_source_frame=int(ix[-1]),
       first_source_pts_s=float(ts[0]),last_source_pts_s=float(ts[-1]),preview_fps=fps,
       timing='All native frames retained; constant playback spacing. Burned original source PTS is authoritative.',
       model_inference=False)
  cap=cv2.VideoCapture(meta['source_file']);i=0;started=time.time()
  while True:
   ok,frame=cap.read()
   if not ok:break
   t=cap.get(cv2.CAP_PROP_POS_MSEC)/1000
   if t>=max(r[3] for r in rows):break
   for ident,_,a,b,_ in rows:
    if a<=t<b:
     im=np.zeros((416,640,3),np.uint8);im[56:416]=frame[720:1080,800:1440]
     cv2.putText(im,f'{ident} | {sid} source {t:.3f}s | frame {i}',(10,21),cv2.FONT_HERSHEY_SIMPLEX,.5,(245,245,245),1,cv2.LINE_AA)
     cv2.putText(im,'VISUAL EVIDENCE / NO MODEL COUNT',(10,44),cv2.FONT_HERSHEY_SIMPLEX,.48,(110,220,255),1,cv2.LINE_AA)
     writers[ident].write(im);info[ident]['native_frames_written']+=1
   i+=1
   if i%1500==0:print(sid,i,round(t,2),round(time.time()-started,1),flush=True)
  cap.release()
  for ident,writer in writers.items():
   writer.release();r=info[ident];assert r['native_frames_expected']==r['native_frames_written']
   check=cv2.VideoCapture(str(OUT/r['path']));n=0
   while check.read()[0]:n+=1
   check.release();assert n==r['native_frames_written'],(ident,n,r)
   r['decoded_frames_verified']=n;done.append(r)
  (OUT/'preview_verification.json').write_text(json.dumps(done,indent=2),encoding='utf-8')
  print('VERIFIED',sid,len(writers),flush=True)
 print('ALL_COMPLETE',len(done),sum(r['decoded_frames_verified'] for r in done),flush=True)

if __name__=='__main__':main()
