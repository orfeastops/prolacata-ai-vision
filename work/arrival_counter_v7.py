"""Online arrival proposals from model-detected trays and tray positions.

No manual positions or reference counts enter this decoder. Ten is the known
number of tray positions, not the number of cheeses. Missing positions remain
unresolved; an empty position does not become cheese. This first implementation
assumes a single layer and requires evaluation of automatic tray identities.
"""
import math
from collections import deque
import numpy as np

CONFIG=dict(detection_confidence=.25,model_nms_iou=.4,position_nms_iou=.4,
    physical_positions=10,stable_observations=3,track_gap_s=.6,minimum_tray_iou=.15,
    bottom_entry_margin_px=5,minimum_tray_width_px=45,minimum_tray_height_px=12,
    empty_rearm_observations=5,
    counting='one single-layer cheese block per detected occupied tray position',
    count_not_clamped=True,reference_counts_used=False,manual_per_frame_localization=False)

def iou(a,b):
    a=np.asarray(a);b=np.asarray(b)
    inter=float(np.prod(np.maximum(0,np.minimum(a[2:],b[2:])-np.maximum(a[:2],b[:2]))))
    union=float(np.prod(a[2:]-a[:2])+np.prod(b[2:]-b[:2]))-inter
    return inter/union if union>0 else 0.

def deduplicate_positions(positions):
    kept=[]
    for p in sorted(positions,key=lambda p:-p['confidence']):
        if all(iou(p['bbox'],q['bbox'])<CONFIG['position_nms_iou'] for q in kept):kept.append(p)
    return kept

def group_detections(detections,width=270,height=170):
    trays=[d for d in detections if d['class_id']==2 and
        d['bbox'][2]-d['bbox'][0]>=CONFIG['minimum_tray_width_px'] and
        d['bbox'][3]-d['bbox'][1]>=CONFIG['minimum_tray_height_px']]
    positions=deduplicate_positions([d for d in detections if d['class_id'] in (0,1,3)])
    groups=[dict(bbox=d['bbox'],tray_confidence=d['confidence'],positions=[]) for d in trays]
    for d in positions:
        x=(d['bbox'][0]+d['bbox'][2])/2;y=(d['bbox'][1]+d['bbox'][3])/2
        candidates=[(j,g) for j,g in enumerate(groups) if g['bbox'][0]-3<=x<=g['bbox'][2]+3 and g['bbox'][1]-3<=y<=g['bbox'][3]+3]
        if candidates:
            j,_=min(candidates,key=lambda z:(x-(z[1]['bbox'][0]+z[1]['bbox'][2])/2)**2+(y-(z[1]['bbox'][1]+z[1]['bbox'][3])/2)**2)
            groups[j]['positions'].append(d)
    for g in groups:
        g['cheese']=sum(d['class_id']==0 for d in g['positions'])
        g['empty']=sum(d['class_id']==1 for d in g['positions'])
        g['obscured']=sum(d['class_id']==3 for d in g['positions'])
        g['position_count']=len(g['positions'])
        g['complete_positions']=len(g['positions'])==CONFIG['physical_positions'] and g['obscured']==0
    return groups

class ArrivalCounter:
    def __init__(self,width=270,height=170):
        self.width=width;self.height=height;self.active={};self.records=[];self.next_id=1;self.last_time=None

    def new_track(self,t,g):
        ident=self.next_id;self.next_id+=1
        tr=dict(id=ident,first_seen_s=t,last_seen_s=t,bbox=g['bbox'],observations=0,
            entered_at_bottom=g['bbox'][3]>=self.height-CONFIG['bottom_entry_margin_px'],
            recent=deque(maxlen=CONFIG['stable_observations']),candidate=None,empty_streak=0,
            maximum_visible_cheese=0,maximum_visible_positions=0)
        self.active[ident]=tr;return tr

    def close(self,ident,reason):
        tr=self.active.pop(ident);candidate=tr['candidate']
        self.records.append(dict(tray_id=ident,first_seen_s=tr['first_seen_s'],last_seen_s=tr['last_seen_s'],
            count=candidate['count'] if candidate else None,
            count_source_time_s=candidate['time_s'] if candidate else None,
            frame_index=candidate['frame_index'] if candidate else None,
            candidate_snapshot=candidate,entered_at_bottom=tr['entered_at_bottom'],
            status='automatic_arrival_proposal' if candidate and tr['entered_at_bottom'] else 'unresolved_or_not_entry',
            closed_reason=reason,observations=tr['observations'],
            maximum_visible_cheese=tr['maximum_visible_cheese'],maximum_visible_positions=tr['maximum_visible_positions'],
            verified_by_human=False,stacking_validated=False))

    def step(self,t,detections,frame_index):
        if not math.isfinite(t) or self.last_time is not None and t<=self.last_time:raise ValueError('Increasing source timestamps required')
        self.last_time=t
        for ident,tr in list(self.active.items()):
            if t-tr['last_seen_s']>CONFIG['track_gap_s']:self.close(ident,'detection_gap')
        groups=group_detections(detections,self.width,self.height)
        pairs=sorted([(iou(tr['bbox'],g['bbox']),ident,j) for ident,tr in self.active.items() for j,g in enumerate(groups)],reverse=True)
        matched={};used=set()
        for overlap,ident,j in pairs:
            if overlap<CONFIG['minimum_tray_iou']:break
            if ident in used or j in matched:continue
            matched[j]=ident;used.add(ident)
        outputs=[]
        for j,g in enumerate(groups):
            tr=self.active[matched[j]] if j in matched else self.new_track(t,g)
            if tr['empty_streak']>=CONFIG['empty_rearm_observations'] and g['cheese']>=2 and g['bbox'][3]>=self.height-CONFIG['bottom_entry_margin_px']:
                self.close(tr['id'],'empty_to_loaded_transition');tr=self.new_track(t,g)
            tr['last_seen_s']=t;tr['bbox']=g['bbox'];tr['observations']+=1
            tr['maximum_visible_cheese']=max(tr['maximum_visible_cheese'],g['cheese'])
            tr['maximum_visible_positions']=max(tr['maximum_visible_positions'],g['position_count'])
            if g['empty']>=8 and g['cheese']==0 and g['obscured']==0:tr['empty_streak']+=1
            else:tr['empty_streak']=0
            value=g['cheese'] if g['complete_positions'] else None
            tr['recent'].append(value)
            stable=len(tr['recent'])==CONFIG['stable_observations'] and value is not None and all(v==value for v in tr['recent'])
            if stable and tr['candidate'] is None:
                tr['candidate']=dict(count=value,time_s=t,frame_index=frame_index,
                    bbox=g['bbox'],positions=g['positions'],rule='ten model-detected positions, none obscured, same count for three native observations')
            outputs.append(dict(tray_id=tr['id'],bbox=g['bbox'],cheese=g['cheese'],empty=g['empty'],obscured=g['obscured'],
                position_count=g['position_count'],complete_positions=g['complete_positions'],
                initial_count=tr['candidate']['count'] if tr['candidate'] else None))
        return outputs

    def finish(self):
        for ident in list(self.active):self.close(ident,'end_of_video')
        return self.records
