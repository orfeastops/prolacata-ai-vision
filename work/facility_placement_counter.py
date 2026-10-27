"""Experimental image-to-event counter, with explicit abstention.

October-only hand-state classifier + YOLO hands + short-lived hand trajectories.
No worker identification. A counted candidate needs source contact, observed
block appearance, travel to the tank, and an empty-hand observation afterwards.
Hand cycles are motion proposals only. This legacy image model cannot predict
block multiplicity. Quantity remains unknown until object-level evidence exists.
"""
import os,json,pathlib,argparse,hashlib,collections,time,subprocess
os.environ['YOLO_AUTOINSTALL']='false'
os.environ['YOLO_CONFIG_DIR']='outputs/feta_training/runtime_config'
import cv2,numpy as np
from functools import lru_cache

def linear_sum_assignment(cost):
    """Small gated bipartite matching; allow unmatched tracks/detections."""
    if cost.shape[1]>12:
        pairs=[];used=set()
        for i in np.argsort(cost.min(axis=1)):
            for j in np.argsort(cost[i]):
                if j not in used and cost[i,j]<65:pairs.append((int(i),int(j)));used.add(j);break
        return ([p[0] for p in pairs],[p[1] for p in pairs])
    @lru_cache(None)
    def solve(i,mask):
        if i==len(cost):return 0.,()
        base,tail=solve(i+1,mask);best=(65+base,tail)
        for j in range(cost.shape[1]):
            if mask&(1<<j) or cost[i,j]>=65:continue
            value,pairs=solve(i+1,mask|(1<<j));candidate=(float(cost[i,j])+value,((i,j),)+pairs)
            if candidate[0]<best[0]:best=candidate
        return best
    pairs=solve(0,0)[1]
    return ([p[0] for p in pairs],[p[1] for p in pairs])

ROOT=pathlib.Path('outputs/facility_dataset/temporal_pipeline')
OUT=ROOT/'placement_counter_v1'
FF=pathlib.Path('work/video_decoder/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe')
class AppearanceModel:
    def __init__(self,path=None):
        if path:
            data=np.load(path);self.mean=data['mean'];self.scale=data['scale'];self.weight=data['weight'];self.bias=data['bias']
    def fit(self,X,y):
        import torch
        torch.manual_seed(73);torch.set_num_threads(4)
        self.mean=X.mean(axis=0);self.scale=np.maximum(.05,X.std(axis=0))
        x=torch.tensor((X-self.mean)/self.scale,dtype=torch.float32);target=torch.tensor(y,dtype=torch.float32)
        layer=torch.nn.Linear(X.shape[1],1);optimizer=torch.optim.Adam(layer.parameters(),lr=.01)
        for _ in range(200):
            optimizer.zero_grad();logits=layer(x).flatten()
            loss=torch.nn.functional.binary_cross_entropy_with_logits(logits,target,pos_weight=torch.tensor(y.count(0)/y.count(1)))+.1*layer.weight.square().sum()
            loss.backward();optimizer.step()
        self.weight=layer.weight.detach().numpy().flatten();self.bias=layer.bias.detach().numpy()
    def predict_proba(self,X):
        p=1/(1+np.exp(-np.clip(((X-self.mean)/self.scale)@self.weight+self.bias,-30,30)))
        return np.stack([1-p,p],axis=1)
    def save(self,path):np.savez(path,mean=self.mean,scale=self.scale,weight=self.weight,bias=self.bias)
CONFIG=dict(fps=8,detector_confidence=.25,carrying_threshold=.65,empty_threshold=.35,
            max_gap_s=.5,max_speed_px_s=500,match_distance_px=65,min_source_observations=2,
            min_carry_observations=2,min_tank_observations=2,min_empty_observations=2,
            max_episode_s=25,min_travel_px=35,
            tank_polygon=[[40,180],[180,120],[310,265],[140,350]],
            source_polygon=[[190,330],[450,170],[530,225],[310,359]],
            recipe='Fixed from October camera geometry; not tuned on September test')

def roi(frame,box):
    cx=(box[0]+box[2])/2;cy=(box[1]+box[3])/2
    x=max(0,min(528,int(cx-56)));y=max(0,min(248,int(cy-56)))
    return frame[y:y+112,x:x+112]

def feature(im):
    small=cv2.resize(im,(64,64)); hsv=cv2.cvtColor(small,cv2.COLOR_BGR2HSV)
    hist=cv2.calcHist([hsv],[0,1],None,[12,8],[0,180,0,256]).flatten()
    hist/=max(1,hist.sum())
    # Preserve local arrangement, not camera position or source filename.
    colors=cv2.resize(small,(8,8)).flatten().astype(np.float32)/255
    gray=cv2.cvtColor(small,cv2.COLOR_BGR2GRAY).astype(np.float32)/255
    gy,gx=np.gradient(gray);magnitude=np.hypot(gx,gy);bins=((np.arctan2(gy,gx)%np.pi)*9/np.pi).astype(int)%9
    gradients=[]
    for y in range(0,64,8):
        for x in range(0,64,8):
            cell=np.bincount(bins[y:y+8,x:x+8].ravel(),weights=magnitude[y:y+8,x:x+8].ravel(),minlength=9)
            gradients.extend(cell/max(.1,np.linalg.norm(cell)))
    return np.concatenate((gradients,colors,hist)).astype(np.float32)

def train():
    rows=json.loads((OUT/'carry_review_candidates.json').read_text())
    # Visual review of the hand at the red centre marker; uncertain crops excluded.
    positive={3,6,10,11,15,16,18,19,20,22,23,24,25,33,35,37,38,42,58,60,68,72,73,74,75}
    uncertain={13,28,29,30,39,50,66}
    for i,r in enumerate(rows):
        r['label']=None if i in uncertain else int(i in positive)
        r['label_meaning']='one whole block touching/held by target hand' if r['label']==1 else ('no whole block at target hand' if r['label']==0 else 'uncertain; excluded')
        r['reviewer']='assistant visual review, not independently expert verified'
        r['split']='validation' if r['clip_id'] in ['B009','B019'] else 'train'
        a=json.loads((ROOT/'review_batch_01'/r['clip_id']/'annotation.json').read_text())
        r['source_sha256']=a['source_sha256'];r['date']=a['date']
        assert r['date']!='2026-09-26'
    (OUT/'carry_review_labels.json').write_text(json.dumps(rows,indent=2))
    trainrows=[r for r in rows if r['label'] is not None and r['split']=='train']
    valrows=[r for r in rows if r['label'] is not None and r['split']=='validation']
    assert not ({r['source_sha256'] for r in trainrows}&{r['source_sha256'] for r in valrows})
    X=np.array([feature(cv2.imread(r['image'])) for r in trainrows]);y=[r['label'] for r in trainrows]
    model=AppearanceModel()
    model.fit(X,y);model.save(OUT/'hand_object_state.npz')
    vp=model.predict_proba(np.array([feature(cv2.imread(r['image'])) for r in valrows]))[:,1]
    truth=[r['label'] for r in valrows]
    matrix=np.zeros((2,2),int)
    for a,b in zip(truth,(vp>=.5).astype(int)):matrix[a,b]+=1
    report=dict(training_crops=len(trainrows),validation_crops=len(valrows),
        training_sources=len({r['source_sha256'] for r in trainrows}),
        validation_sources=len({r['source_sha256'] for r in valrows}),
        training_label_counts=dict(collections.Counter(map(str,y))),
        validation_confusion_at_half=matrix.tolist(),
        validation_balanced_accuracy=float(np.mean(np.diag(matrix)/np.maximum(1,matrix.sum(axis=1)))),
        validation_predictions=[dict(id=r['id'],truth=r['label'],probability=float(p)) for r,p in zip(valrows,vp)],
        probability_calibrated=False,block_counting_accuracy=None,production_ready=False,
        limitations=['Small hand-state baseline, not a validated release detector',
          'A hand beside a stationary block can look like a carrying hand',
          'No reviewed crumbs-in-hand training examples; no reliable crumb rejection claim',
          'Only one-block-in-one-hand supported; occluded or stacked quantities require review'])
    (OUT/'carry_model_report.json').write_text(json.dumps(report,indent=2))
    (OUT/'frozen_config.json').write_text(json.dumps(CONFIG,indent=2))
    print(json.dumps(report,indent=2),flush=True)

def inside(p,poly):return cv2.pointPolygonTest(np.array(poly,np.int32),tuple(map(float,p)),False)>=0

def bridge_flow(previous,frame,tracker,boxes,t):
    """Observed forward/backward optical flow bridges detector misses, not occlusions."""
    if previous is None:return boxes
    old=cv2.cvtColor(previous,cv2.COLOR_BGR2GRAY);new=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    hsv=cv2.cvtColor(previous,cv2.COLOR_BGR2HSV)
    blue=cv2.inRange(hsv,np.array([85,70,45]),np.array([135,255,255]))
    additions=[]
    for tr in tracker.tracks.values():
        tr.pop('flow_point',None)
        if abs(t-tr['last']-1/tracker.c['fps'])>.001 or 'box' not in tr:continue
        b=np.array(tr['box']);x1,y1,x2,y2=np.round(b).astype(int)
        mask=np.zeros_like(old);mask[max(0,y1):min(360,y2),max(0,x1):min(640,x2)]=blue[max(0,y1):min(360,y2),max(0,x1):min(640,x2)]
        points=cv2.goodFeaturesToTrack(old,maxCorners=20,qualityLevel=.01,minDistance=2,mask=mask)
        if points is None or len(points)<3:continue
        nxt,valid,_=cv2.calcOpticalFlowPyrLK(old,new,points,None,winSize=(25,25),maxLevel=3)
        back,validback,_=cv2.calcOpticalFlowPyrLK(new,old,nxt,None,winSize=(25,25),maxLevel=3)
        ok=(valid.ravel()>0)&(validback.ravel()>0)&(np.linalg.norm(back-points,axis=2).ravel()<1.5)
        if ok.sum()<3:continue
        delta=np.median((nxt-points).reshape(-1,2)[ok],axis=0)
        if np.linalg.norm(delta)>80:continue
        shifted=b+np.tile(delta,2);p=(shifted[:2]+shifted[2:])/2
        if not (0<=p[0]<640 and 0<=p[1]<360):continue
        tr['flow_point']=p
        centres=(boxes[:,:2]+boxes[:,2:])/2 if len(boxes) else np.empty((0,2))
        if len(centres) and np.min(np.linalg.norm(centres-p,axis=1))<22:continue
        # Verify current blue glove pixels, avoiding drift onto stationary cheese.
        current=cv2.cvtColor(roi(frame,shifted),cv2.COLOR_BGR2HSV)
        if cv2.countNonZero(cv2.inRange(current,np.array([85,70,45]),np.array([135,255,255])))<30:continue
        additions.append(shifted)
    return np.concatenate([boxes,np.array(additions)],axis=0) if additions else boxes

class Tracker:
    def __init__(self,config):self.c=config;self.tracks={};self.next_id=1;self.events=[]
    def update(self,t,boxes,probs):
        # No bridging a long occlusion: unresolved evidence is recorded instead.
        for k,tr in list(self.tracks.items()):
            if t-tr['last']>self.c['max_gap_s']:
                if tr['episode'] is not None:self.finish(tr,t,'unresolved_track_lost')
                del self.tracks[k]
        centres=[np.array([(b[0]+b[2])/2,(b[1]+b[3])/2]) for b in boxes]
        tids=list(self.tracks);assign={}
        if tids and centres:
            cost=np.array([[np.linalg.norm(self.tracks[k].get('flow_point',self.tracks[k]['point']+self.tracks[k]['velocity']*(t-self.tracks[k]['last']))-p) for p in centres] for k in tids])
            ii,jj=linear_sum_assignment(cost)
            for i,j in zip(ii,jj):
                tr=self.tracks[tids[i]];actual=np.linalg.norm(tr['point']-centres[j]);dt=t-tr['last']
                if cost[i,j]<self.c['match_distance_px'] and actual<max(20,dt*self.c['max_speed_px_s']):assign[j]=tids[i]
        result=[]
        for j,(p,box,prob) in enumerate(zip(centres,boxes,probs)):
            if j not in assign:
                k=self.next_id;self.next_id+=1
                self.tracks[k]=dict(id=k,last=t,point=p,velocity=np.zeros(2),episode=None,source_hits=0,carry_hits=0)
            else:k=assign[j]
            tr=self.tracks[k];dt=t-tr['last']
            if dt>0:tr['velocity']=.5*tr['velocity']+.5*(p-tr['point'])/dt
            tr['last']=t;tr['point']=p;tr['box']=list(map(float,box))
            tank=inside(p,self.c['tank_polygon']);source=inside(p,self.c['source_polygon']) and not tank
            carrying=prob>=self.c['carrying_threshold'];empty=prob<=self.c['empty_threshold']
            if tr['episode'] is None:
                tr['source_hits']=tr['source_hits']+1 if source else 0
                tr['carry_hits']=tr['carry_hits']+1 if source and carrying else 0
                if tr['source_hits']>=self.c['min_source_observations'] and tr['carry_hits']>=self.c['min_carry_observations']:
                    tr['episode']=dict(start=t,source_point=p.tolist(),tank_hits=0,empty_hits=0,tank_time=None,carry_max=float(prob))
            else:
                e=tr['episode'];e['carry_max']=max(e['carry_max'],float(prob))
                if tank and np.linalg.norm(p-np.array(e['source_point']))>=self.c['min_travel_px']:
                    e['tank_hits']+=1
                    if e['tank_time'] is None:e['tank_time']=t
                if e['tank_hits']>=self.c['min_tank_observations']:
                    e['empty_hits']=e['empty_hits']+1 if empty else 0
                    if e['empty_hits']>=self.c['min_empty_observations']:
                        self.finish(tr,t,'candidate_deposit_quantity_unknown')
                if tr['episode'] is not None and t-e['start']>self.c['max_episode_s']:
                    self.finish(tr,t,'unresolved_episode_timeout')
            result.append(dict(track_id=k,box=list(map(float,box)),one_block_probability=float(prob),zone='tank' if tank else ('source' if source else 'other'),armed=tr['episode'] is not None))
        return result
    def finish(self,tr,t,status):
        e=tr['episode']
        self.events.append(dict(event_id=f"hand{tr['id']}_{e['start']:.3f}",hand_track=tr['id'],start_s=e['start'],end_s=t,
            tank_contact_s=e['tank_time'],status=status,predicted_quantity=None,
            certified_quantity=None,quantity_basis='unavailable_from_hand_state',
            requires_block_evidence=True,evidence=e.copy()))
        tr['episode']=None;tr['source_hits']=0;tr['carry_hits']=0
    def close(self,t):
        for tr in self.tracks.values():
            if tr['episode'] is not None:self.finish(tr,t,'unresolved_video_boundary')

def infer(args):
    import torch
    from ultralytics import YOLO
    torch.set_num_threads(4);cv2.setNumThreads(2);cfg=json.loads((OUT/'frozen_config.json').read_text())
    dest=pathlib.Path(args.output);dest.mkdir(parents=True,exist_ok=True)
    source=pathlib.Path(args.video);sha=hashlib.file_digest(source.open('rb'),'sha256').hexdigest()
    detector=YOLO('outputs/feta_training/hands_detector.pt');state=AppearanceModel(OUT/'hand_object_state.npz')
    indexed=dest/'indexed.mp4'
    # Camera export container must be indexed before FFmpeg timeline handling.
    subprocess.run([str(FF),'-loglevel','error','-y','-i',str(source),'-map','0:v:0','-an','-c:v','copy',str(indexed)],capture_output=True,check=True)
    vf=('crop=640:360:800:720,' if not args.cropped else '')+f"fps={cfg['fps']}"
    command=[str(FF),'-loglevel','error','-i',str(indexed)]
    if args.seconds:command+=['-t',str(args.seconds)]
    command+=['-vf',vf,'-threads','2','-f','rawvideo','-pix_fmt','bgr24','pipe:1']
    log=(dest/'decode.log').open('wb');proc=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=log)
    avi=dest/'counter_preview.avi';writer=cv2.VideoWriter(str(avi),cv2.VideoWriter_fourcc(*'MJPG'),cfg['fps'],(640,400))
    assert writer.isOpened()
    tracker=Tracker(cfg);i=0;start=time.time();previous=None
    try:
      with (dest/'hand_tracks.jsonl').open('w') as stream:
        while True:
            raw=proc.stdout.read(640*360*3)
            if not raw:break
            if len(raw)!=640*360*3:raise RuntimeError('Truncated decoded frame')
            frame=np.frombuffer(raw,np.uint8).reshape(360,640,3).copy();t=i/cfg['fps']
            pred=detector.predict(frame,conf=cfg['detector_confidence'],iou=.35,imgsz=640,device='cpu',verbose=False)[0]
            boxes=pred.boxes.xyxy.cpu().numpy()
            boxes=bridge_flow(previous,frame,tracker,boxes,t)
            previous=frame.copy()
            probs=state.predict_proba(np.array([feature(roi(frame,b)) for b in boxes]))[:,1] if len(boxes) else []
            tracks=tracker.update(t,boxes,probs)
            stream.write(json.dumps(dict(time_s=t,tracks=tracks))+'\n')
            for tr in tracks:
                b=list(map(int,tr['box']));color=(0,220,0) if tr['armed'] else (0,170,255)
                cv2.rectangle(frame,tuple(b[:2]),tuple(b[2:]),color,1)
                cv2.putText(frame,f"h{tr['track_id']} {tr['one_block_probability']:.2f}",(b[0],max(10,b[1]-3)),0,.35,color,1)
            for poly,color in [(cfg['source_polygon'],(255,140,0)),(cfg['tank_polygon'],(0,255,255))]:cv2.polylines(frame,[np.array(poly)],True,color,1)
            n=sum(e['status']=='candidate_deposit_quantity_unknown' for e in tracker.events)
            recent=[e for e in tracker.events if e['predicted_quantity'] and 0<=t-e['end_s']<1]
            if recent:cv2.putText(frame,f"+{sum(e['predicted_quantity'] for e in recent)} predicted",(10,30),0,.75,(0,255,0),2)
            canvas=np.zeros((400,640,3),np.uint8);canvas[:360]=frame
            cv2.putText(canvas,f'REVIEW | {t:.2f}s | motion candidates: {n}',(8,378),0,.48,(255,255,255),1)
            cv2.putText(canvas,'Block count UNKNOWN: object quantity model required',(8,395),0,.42,(0,200,255),1)
            writer.write(canvas)
            if i%240==0:
                (dest/'progress.json').write_text(json.dumps(dict(frames=i,video_seconds=t,elapsed_s=round(time.time()-start,1))))
                print(f'{dest.name}: {t:.1f}s processed / {time.time()-start:.1f}s elapsed',flush=True)
            i+=1
    finally:
        writer.release();proc.stdout.close();proc.wait();log.close()
    if proc.returncode:raise RuntimeError(f'FFmpeg failed: {proc.returncode}')
    tracker.close(i/cfg['fps'])
    (dest/'events.json').write_text(json.dumps(tracker.events,indent=2))
    report=dict(source=str(source.resolve()),source_sha256=sha,frames=i,duration_processed_s=i/cfg['fps'],
        predicted_deposits=None,
        motion_candidates=sum(e['status']=='candidate_deposit_quantity_unknown' for e in tracker.events),
        quantity_model_available=False,
        unresolved_episodes=sum(e['predicted_quantity'] is None for e in tracker.events),
        exact_block_count=None,per_tank_counts=None,production_ready=False,
        state_model_sha256=hashlib.file_digest((OUT/'hand_object_state.npz').open('rb'),'sha256').hexdigest(),
        configuration=cfg,warning='Motion proposals only. Hand state does not establish block quantity. No automatic count is available; unknown is not zero. Tank change not yet associated.')
    (dest/'report.json').write_text(json.dumps(report,indent=2))
    subprocess.run([str(FF),'-loglevel','error','-y','-i',str(avi),'-c:v','libx264','-crf','23','-pix_fmt','yuv420p',str(dest/'counter_preview.mp4')],check=True)
    print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['train','infer']);p.add_argument('--video');p.add_argument('--output');p.add_argument('--cropped',action='store_true');p.add_argument('--seconds',type=float)
    args=p.parse_args();train() if args.mode=='train' else infer(args)
