"""Frozen native-frame payload tracking/counting development check.

No expert event windows, expected counts, old temporal probabilities or test
annotations enter the decoder. Metrics are computed only after predictions.
"""
import os
os.environ['YOLO_AUTOINSTALL']='false';os.environ['YOLO_OFFLINE']='true'
import json,time,hashlib
from pathlib import Path
import cv2,numpy as np,torch
from ultralytics import YOLO
from train_transfer_events_v4 import save,digest,load
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'outputs/facility_dataset/temporal_pipeline'
OUT=BASE/'placement_counter_v5/object_expansion'
CONFIG=dict(detection_confidence=.30,nms_iou=.4,agnostic_nms=True,minimum_observations=3,
    maximum_gap_s=.40,maximum_match_distance_px=85,minimum_projection_drop_px=35,
    source_projection_min=425,destination_projection_max=430,
    projection='x + 0.8*y in native 640x360 crop',quantity_vote_fraction=.60,
    tank_polygon=[[45,175],[225,105],[345,235],[180,355],[60,285]],
    quantity_class_map={0:1,1:2,2:3,3:0},sampling='all native frames; original PTS',
    event='load disappeared after observed movement from pickup corridor into tank polygon',
    association='greedy minimum-distance one-to-one matching using short velocity prediction',
    limitations='Disappearance is an experimental release proxy; physical release is not verified. Groups can split/occlude. This is not an accepted production counter.')
class Counter:
    def __init__(self,config=CONFIG):
        self.c=config;self.active={};self.next_id=1;self.events=[];self.rejected=[]
    def close(self,track,now,cutoff=False):
        h=track['history'];points=np.array([v['center'] for v in h]);pr=points[:,0]+.8*points[:,1]
        first=float(np.median(pr[:min(3,len(pr))]));last=float(np.median(pr[-min(3,len(pr)):]))
        end=np.median(points[-min(3,len(points)):],axis=0)
        in_tank=cv2.pointPolygonTest(np.asarray(self.c['tank_polygon'],np.float32),tuple(map(float,end)),False)>=0
        votes={q:sum(v['confidence'] for v in h if v['quantity']==q) for q in [0,1,2,3]}
        q=max(votes,key=votes.get);share=votes[q]/max(sum(votes.values()),1e-12)
        reasons=[]
        if len(h)<self.c['minimum_observations']:reasons.append('too_few_visible_frames')
        if first<self.c['source_projection_min']:reasons.append('pickup_corridor_not_observed')
        if first-last<self.c['minimum_projection_drop_px']:reasons.append('no_clear_motion_toward_tank')
        if not in_tank or last>self.c['destination_projection_max']:reasons.append('no_visible_destination_in_tank')
        if q==0 or share<self.c['quantity_vote_fraction']:reasons.append('quantity_uncertain')
        if cutoff:reasons.append('track_continues_at_clip_end')
        event=dict(track_id=track['id'],side=track['side'],first_seen_s=h[0]['time_s'],
            time_s=h[-1]['time_s'],emitted_at_s=float(now),predicted_quantity=int(q),
            quantity_vote_fraction=float(share),observations=len(h),first_projection=first,last_projection=last,
            reasons=reasons,accepted=not reasons)
        (self.rejected if reasons else self.events).append(event)
    def step(self,t,detections):
        for ident,tr in list(self.active.items()):
            if t-tr['history'][-1]['time_s']>self.c['maximum_gap_s']:
                self.close(tr,t);del self.active[ident]
        ds=[]
        for d in detections:
            b=np.array(d['bbox']);p=(b[:2]+b[2:])/2
            ds.append(dict(d,center=p.tolist(),time_s=float(t)))
        ids=list(self.active);cost=np.full((len(ids),len(ds)),1e6)
        for i,ident in enumerate(ids):
            h=self.active[ident]['history'];last=h[-1];p=np.array(last['center'])
            if len(h)>1:
                dt=last['time_s']-h[-2]['time_s']
                velocity=(p-np.array(h[-2]['center']))/max(dt,.02)
                p=p+np.clip(velocity,-350,350)*min(t-last['time_s'],.15)
            for j,d in enumerate(ds):
                distance=float(np.linalg.norm(p-d['center']))
                if distance<=self.c['maximum_match_distance_px']:cost[i,j]=distance
        matches=[]
        if cost.size:
            used_tracks=set();used_detections=set()
            for distance,i,j in sorted((float(cost[i,j]),i,j) for i in range(len(ids)) for j in range(len(ds))):
                if distance>=1e5:break
                if i in used_tracks or j in used_detections:continue
                used_tracks.add(i);used_detections.add(j);matches.append((ids[i],j))
        used=set();output=[]
        for ident,j in matches:
            self.active[ident]['history'].append(ds[j]);used.add(j)
            output.append(dict(ds[j],track_id=ident))
        for j,d in enumerate(ds):
            if j in used:continue
            ident=self.next_id;self.next_id+=1;x,y=d['center']
            self.active[ident]=dict(id=ident,side='L' if y>.7*x+80 else 'R',history=[d])
            output.append(dict(d,track_id=ident))
        return output
    def finish(self,t):
        for tr in self.active.values():self.close(tr,t,cutoff=True)
        self.active={}
def metrics(predictions):
    benchmark=[p for p in predictions if p['reference_count'] is not None]
    positives=[p for p in benchmark if p['reference_count']>0];negatives=[p for p in benchmark if p['reference_count']==0]
    return dict(complete_count_clips=len(benchmark),mean_absolute_count_error=float(np.mean([abs(p['accepted_additions']-p['reference_count']) for p in benchmark])),
        positive_clips=len(positives),positive_exact=sum(p['accepted_additions']==p['reference_count'] for p in positives),
        negative_clips=len(negatives),negative_false_counts=sum(p['accepted_additions']>0 for p in negatives),
        reference_blocks=sum(p['reference_count'] for p in benchmark),accepted_blocks=sum(p['accepted_additions'] for p in benchmark))
def main():
    torch.set_num_threads(4);cv2.setNumThreads(2)
    if (OUT/'count_results.json').exists():raise RuntimeError('Frozen predictions already exist; no implicit rerun.')
    complete=load(OUT/'training_complete.json');checkpoint=Path(complete['checkpoint'])
    assert digest(checkpoint)==complete['checkpoint_sha256']
    manifest=load(OUT/'dataset_manifest.json')
    assert digest(OUT/'dataset_manifest.json')==complete['dataset_manifest_sha256']
    rows=[r for r in load(BASE/'placement_counter_v4/event_quantity_diagnostic/dataset.json')['rows'] if r['role']!='train']
    training={r['source_sha256'] for r in manifest['rows'] if r['split']=='train'}
    assert not training&{r['source_sha256'] for r in rows}
    save(OUT/'counter_frozen_before_test.json',dict(config=CONFIG,checkpoint_sha256=digest(checkpoint),
        code_sha256=digest(__file__),manifest_sha256=digest(OUT/'dataset_manifest.json'),
        test_sources=[r['source_sha256'] for r in rows],frozen_at_unix=time.time(),
        no_test_data_training=True,no_expected_count_used_by_decoder=True))
    model=YOLO(str(checkpoint));predictions=[];total=0
    for row in rows:
        if 'native_npz' in row:
            with np.load(row['native_npz']) as z:frames=z['frames'].copy()
        else:frames=[cv2.imread(p) for p in row['image_files']]
        times=row['timestamps'];assert len(times)==len(frames)
        counter=Counter();frame_outputs=[]
        for offset in range(0,len(frames),8):
            result=model.predict(source=list(frames[offset:offset+8]),imgsz=640,device='cpu',
                conf=CONFIG['detection_confidence'],iou=CONFIG['nms_iou'],agnostic_nms=True,verbose=False)
            for j,r in enumerate(result):
                t=times[offset+j];detections=[]
                for box,confidence,cls in zip(r.boxes.xyxy.cpu().numpy(),r.boxes.conf.cpu().numpy(),r.boxes.cls.cpu().numpy()):
                    detections.append(dict(bbox=[float(v) for v in box],confidence=float(confidence),quantity=CONFIG['quantity_class_map'][int(cls)]))
                linked=counter.step(float(t),detections)
                frame_outputs.append(dict(time_s=float(t),detections=linked))
        counter.finish(times[-1]);accepted=[e for e in counter.events if 0<=e['time_s']<=row['original_end_s']]
        prediction=dict(id=row['id'],role=row['role'],source_sha256=row['source_sha256'],
            frames=len(frames),accepted_additions=sum(e['predicted_quantity'] for e in accepted),
            accepted_events=counter.events,unresolved_tracks=counter.rejected,
            original_end_s=row['original_end_s'],reference_count=row['reference_count'])
        if row['id']=='C02':
            prediction['reference_note']='Expert listed transfers, not an independently exhaustive full-clip count; no full-clip count metric.'
        save(OUT/'predictions'/f"{row['id']}.json",dict(**prediction,frame_outputs=frame_outputs))
        predictions.append(prediction);total+=len(frames)
        save(OUT/'evaluation_progress.json',dict(completed_clips=len(predictions),total_clips=len(rows),native_frames=total,last_clip=row['id']))
        print(row['id'],prediction['accepted_additions'],'reference',row['reference_count'],flush=True)
    summary=dict(config=CONFIG,predictions=predictions,metrics=metrics(predictions),native_frame_instances=total,
        checkpoint_sha256=digest(checkpoint),independent_acceptance=False,september_used=False,
        production_ready=False,interpretation='Source-disjoint development screen; historical clips have been inspected before. Automatic disappearance events are not verified placements.')
    save(OUT/'count_results.json',summary);print(json.dumps(summary['metrics']),flush=True)
if __name__=='__main__':main()
