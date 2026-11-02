"""Experimental video integration: payload movement -> tank episode -> exit.

No reference event windows/counts are read. Vision output is a proposal until
independently evaluated. The frozen day28 evaluator is never modified.
"""
import argparse
import hashlib
import json
import os
import time
from pathlib import Path

os.environ['YOLO_AUTOINSTALL'] = 'false'
os.environ['YOLO_OFFLINE'] = 'true'
import av
import cv2
import numpy as np
import torch
from ultralytics import YOLO
from evaluate_payload_counter_v5 import Counter, CONFIG as PAYLOAD_CONFIG

ROOT = Path(__file__).resolve().parents[1]
TANK = ROOT/'outputs/tank_transfer_training_v1/dataset_v2/heldout_counting/best.pt'
PAYLOAD = ROOT/'outputs/facility_dataset/temporal_pipeline/placement_counter_v5/object_expansion/detector_run/weights/last.pt'
CONFIG = dict(tank_conf=.25, tank_imgsz=640, track_gap_s=1., min_iou=.1,
              optical_flow_bridge_s=6., min_flow_features=8,
              use_optical_flow=False,
              station_episode_timeout_s=60.,
              station=[.38,.70,.61,1.], gate_x=[.49,.60],
              approach_y=.52, exit_y=.46, payload_crop=[800,720,1440,1080],
              placement='experimental carried-cheese trajectory into tank; disappearance proxy',
              identity='one-to-one tank track plus single-use filling-station episode; gaps over0.5s reset filling',
              workers='operational filling station, not biometric worker identification')


def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def save(p,obj):
    tmp=p.with_suffix(p.suffix+'.tmp')
    tmp.write_text(json.dumps(obj,indent=2),encoding='utf-8');tmp.replace(p)


def iou(a,b):
    lo=np.maximum(a[:2],b[:2]);hi=np.minimum(a[2:],b[2:])
    inter=np.maximum(hi-lo,0).prod()
    return float(inter/(np.maximum(a[2:]-a[:2],0).prod()+np.maximum(b[2:]-b[:2],0).prod()-inter+1e-9))


class PresenceCounter(Counter):
    def close(self,track,now,cutoff=False):
        before=len(self.events)
        super().close(track,now,cutoff)
        if len(self.events)>before:
            self.events[-1]['destination_xy']=np.median(
                [x['center'] for x in track['history'][-3:]],axis=0).tolist()


class TankLinker:
    def __init__(self):
        self.tracks={};self.next_id=1;self.exits=[];self.unlinked=[]
        self.previous_gray=None
        self.station_episode=None
        self.last_frame_time=None

    def step(self,t,boxes,gray=None):
        if self.last_frame_time is not None and t-self.last_frame_time>.5:
            self.station_episode=None
            for tr in self.tracks.values():tr['fill']=[]
        self.last_frame_time=t
        if gray is not None and self.previous_gray is not None:
            for tr in self.tracks.values():
                if t-tr['last']>CONFIG['optical_flow_bridge_s']:
                    tr['points']=None;tr['flow_valid']=False;continue
                points=tr.get('points')
                if points is None or len(points)<CONFIG['min_flow_features']:
                    tr['flow_valid']=False;continue
                moved,status,_=cv2.calcOpticalFlowPyrLK(self.previous_gray,gray,points,None,
                    winSize=(21,21),maxLevel=3)
                back,backstatus,_=cv2.calcOpticalFlowPyrLK(gray,self.previous_gray,moved,None,
                    winSize=(21,21),maxLevel=3)
                good=(status[:,0]>0)&(backstatus[:,0]>0)&(np.linalg.norm(back[:,0]-points[:,0],axis=1)<1.)
                old=points[good,0];new=moved[good,0]
                if len(new)<CONFIG['min_flow_features']:
                    tr['flow_valid']=False;tr['points']=None;continue
                delta=np.median(new-old,axis=0)
                consistent=np.linalg.norm((new-old)-delta,axis=1)<3
                tr['flow_valid']=bool(consistent.sum()>=CONFIG['min_flow_features'] and np.linalg.norm(delta)<20)
                tr['points']=new[consistent].reshape(-1,1,2)
                if tr['flow_valid']:
                    tr['flow_box']=tr.get('flow_box',tr['box'])+np.tile(delta/[640,360],2)
        # Remove nested/duplicate boxes before assigning identities. A partial
        # detection of the same tank must not start a second filling episode.
        kept=[]
        for b in sorted(boxes,key=lambda x:float(np.prod(x[2:]-x[:2])),reverse=True):
            area=float(np.prod(b[2:]-b[:2]))
            if any(iou(b,k)>.5 or float(np.maximum(np.minimum(b[2:],k[2:])-
                   np.maximum(b[:2],k[:2]),0).prod())/max(area,1e-9)>.9 for k in kept):
                continue
            kept.append(b)
        boxes=kept
        ids=[i for i,tr in self.tracks.items() if t-tr['last']<=CONFIG['track_gap_s'] or
             (tr.get('flow_valid') and t-tr['last']<=CONFIG['optical_flow_bridge_s'])]
        pairs={};used=set()
        for overlap,j,i in sorted([(iou(self.tracks[i].get('flow_box',self.tracks[i]['box']),b),j,i)
                                   for i in ids for j,b in enumerate(boxes)],reverse=True):
            required=CONFIG['min_iou'] if t-self.tracks[i]['last']<=CONFIG['track_gap_s'] else .5
            if overlap>=required and j not in pairs and i not in used:
                pairs[j]=i;used.add(i)
        for j,b in enumerate(boxes):
            i=pairs.get(j)
            if i is None:
                i=self.next_id;self.next_id+=1
                self.tracks[i]=dict(first=t,last=t,box=b,approach=False,counted=False,fill=[],station_origin=False)
            tr=self.tracks[i];tr.update(last=t,box=b)
            if .40<float((b[0]+b[2])/2)<.61 and float((b[1]+b[3])/2)>.78:
                tr['station_origin']=True
            tr['flow_box']=b.copy()
            if gray is not None and (tr['fill'] or (.38<float((b[0]+b[2])/2)<.61 and float((b[1]+b[3])/2)>.70)):
                mask=np.zeros_like(gray);x1,y1,x2,y2=(b*np.array([640,360,640,360])).astype(int)
                x1,x2=max(0,x1),min(640,x2);y1,y2=max(0,y1),min(360,y2)
                # Corners on the visible body; avoid relying only on changing contents.
                mask[max(y1,(y1+y2)//2):y2,x1:x2]=255
                tr['points']=cv2.goodFeaturesToTrack(gray,40,.02,4,mask=mask)
            x=float((b[0]+b[2])/2);y=float(b[3])
            if .44<x<.65 and y>CONFIG['approach_y']:tr['approach']=True
            if (tr['approach'] and not tr['counted'] and
                CONFIG['gate_x'][0]<x<CONFIG['gate_x'][1] and
                y<CONFIG['exit_y'] and b[3]-b[1]>.07):
                tr['counted']=True
                fills=list(tr['fill']);association='continuous_detector_track'
                episode=self.station_episode
                if (not fills and episode and tr['station_origin'] and
                    0<=t-episode['last_placement']<=CONFIG['station_episode_timeout_s']):
                    fills=list(episode['fill']);association='filling_station_episode_to_outbound_trajectory'
                self.exits.append(dict(track=i,pts_s=t,placement_evidence=fills,association=association,
                    status='storage_proposal' if fills else 'exit_without_linked_placement'))
                # Never lend a station filling episode to a second departure.
                if tr['station_origin']:
                    self.station_episode=None
                    for other in self.tracks.values():other['fill']=[]
        self.previous_gray=gray
        return {i:self.tracks[i]['box'] for i in self.tracks if self.tracks[i]['last']==t}

    def placement(self,event,t):
        x,y=event['destination_xy'];x=(x+800)/1920;y=(y+720)/1080
        candidates=[]
        for i,tr in self.tracks.items():
            b=tr['box'];cx=float((b[0]+b[2])/2);cy=float((b[1]+b[3])/2)
            if (tr['last']==t and not tr['counted']
                and .38<cx<.61 and cy>.70
                and b[0]<=x<=b[2] and b[1]<=y<=b[3]):
                candidates.append(i)
        if len(candidates)==1:
            self.tracks[candidates[0]]['fill'].append(event)
            if self.station_episode is None:
                self.station_episode=dict(fill=[],last_placement=t)
            self.station_episode['fill'].append(event)
            self.station_episode['last_placement']=t
            return candidates[0]
        self.unlinked.append(dict(event=event,candidate_tracks=candidates))
        return None


def run(a):
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    import msvcrt
    lock=(out/'run.lock').open('a+b');lock.seek(0);lock.write(b'0');lock.flush();lock.seek(0)
    msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    if (out/'result.json').exists():raise RuntimeError('Completed output exists; use a new run directory')
    torch.set_num_threads(4);cv2.setNumThreads(1)
    save(out/'frozen_config.json',dict(config=CONFIG,source_sha256=digest(a.video),
        tank_sha256=digest(TANK),payload_sha256=digest(PAYLOAD),code_sha256=digest(__file__),
        payload_counter_sha256=digest(Path(__file__).with_name('evaluate_payload_counter_v5.py')),
        clock_export_sha256=digest(Path(__file__).with_name('export_room11_storage.py')),
        clock_reader_sha256=digest(Path(__file__).with_name('read_dvr_clock.ps1')),
        start=a.start,end=a.end,reference_counts_used=False))
    models=[YOLO(str(TANK)),YOLO(str(PAYLOAD))]
    pc=PresenceCounter(dict(PAYLOAD_CONFIG,quantity_class_map={0:1,1:1,2:1,3:1}))
    tc=TankLinker();seen_placements=0;seen_exits=0;started=time.time();lastsave=-100;frames=0
    try:
        with av.open(a.video) as inp,(out/'observations.jsonl').open('w') as log:
            stream=inp.streams.video[0];stream.codec_context.thread_count=2
            origin=None
            for fi,f in enumerate(inp.decode(video=0)):
                if f.time is None:continue
                if origin is None:origin=float(f.time)
                t=float(f.time)-origin
                if t<a.start:continue
                if a.end and t>a.end:break
                im=f.to_ndarray(format='bgr24')
                if im.shape[:2]!=(1080,1920):raise ValueError('Calibrated for native1920x1080 only')
                det=models[0].predict(im,imgsz=640,conf=.25,verbose=False)[0]
                boxes=det.boxes.xyxy.cpu().numpy()/np.array([1920,1080,1920,1080])
                gray=cv2.cvtColor(cv2.resize(im,(640,360)),cv2.COLOR_BGR2GRAY) if CONFIG['use_optical_flow'] else None
                active=tc.step(t,boxes,gray)
                crop=im[720:1080,800:1440]
                pred=models[1].predict(crop,imgsz=640,conf=.30,iou=.4,agnostic_nms=True,verbose=False)[0]
                ds=[dict(bbox=b.tolist(),confidence=float(c),quantity=1)
                    for b,c in zip(pred.boxes.xyxy.cpu().numpy(),pred.boxes.conf.cpu().numpy())]
                pc.step(t,ds)
                for e in pc.events[seen_placements:]:
                    ident=tc.placement(e,t);e['tank_track']=ident
                    cv2.imwrite(str(out/f'placement_{seen_placements:04d}.jpg'),im)
                    seen_placements+=1
                for e in tc.exits[seen_exits:]:
                    name=f'exit_{seen_exits:04d}';cv2.imwrite(str(out/(name+'.jpg')),det.plot())
                    cv2.imwrite(str(out/(name+'_clock.png')),im[45:95,25:550])
                    e.update(evidence=name+'.jpg',clock_evidence=name+'_clock.png',
                             exited_at=None,clock_status='requires_visible_clock_reading')
                    seen_exits+=1
                log.write(json.dumps(dict(pts_s=t,tanks={i:b.tolist() for i,b in active.items()},
                                          payload=ds))+'\n')
                frames+=1
                if t-lastsave>=5:
                    save(out/'progress.json',dict(status='running',frames=frames,pts_s=t,
                        placements=len(pc.events),exits=len(tc.exits),elapsed_s=time.time()-started))
                    lastsave=t
        pc.finish(t)
        result=dict(status='completed_experimental_inference',frames=frames,
            placements=len(pc.events),exits=tc.exits,unlinked_placements=tc.unlinked,
            storage_proposals=sum(bool(e['placement_evidence']) for e in tc.exits),
            production_ready=False,automatic_clock_ready=False,
            limitations=['Placement disappearance is a proxy, not verified physical release.',
                         'Station-episode association across detector fragments is heuristic and needs independent evaluation.',
                         'No state carried across files; a filling outside the clip cannot qualify its exit.',
                         'Date/time must be read from visible clock, not filename plus PTS.'],
            elapsed_s=time.time()-started)
        save(out/'result.json',result);save(out/'progress.json',dict(status='complete',frames=frames))
        print(json.dumps({k:v for k,v in result.items() if k not in ['exits','unlinked_placements']}))
    except Exception as e:
        save(out/'error.json',dict(error=repr(e)));raise
    finally:
        lock.close()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--video',required=True);p.add_argument('--out',required=True)
    p.add_argument('--start',type=float,default=0);p.add_argument('--end',type=float,default=0)
    run(p.parse_args())
