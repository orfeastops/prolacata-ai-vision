"""Export reviewed visual notes and bounded evidence without training a model."""
from pathlib import Path
import copy
import hashlib
import json
from datetime import datetime, timezone
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from assistant_visual_labels_v4 import CLIPS

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'outputs/facility_dataset/temporal_pipeline/sequence_annotation_v4'
OUT = BASE / 'assistant_visual_review'

# Individual carried-object boxes authored by visual inspection of these frames.
# Coordinates are native ROI pixels, not coordinates of the enlarged overview.
ANCHORS = [
 ('C03',23.2,'right',[[231,119,285,149]]),
 ('C04',21.0,'right',[[233,143,290,175],[309,159,345,202]]),
 ('C05',16.0,'right',[[271,159,316,197],[335,166,378,220]]),
 ('C06',16.0,'right',[[251,149,308,178],[311,167,350,211]]),
]

def nearest(meta, t):
    i=min(range(len(meta['files'])),key=lambda k:abs(meta['relative_times_s'][k]-t))
    return dict(cache_frame_index=i, source_frame_index=meta['source_frame_indices'][i],
                clip_relative_pts_s=meta['relative_times_s'][i],
                source_pts_s=round(meta['original_first_clip_pts_s']+meta['relative_times_s'][i],6),
                image=f"{meta['clip_id']}/{meta['files'][i]}")

def main():
    cv2.setNumThreads(2)
    result=dict(schema_version='assistant-visual-events-v1',
        created_utc=datetime.now(timezone.utc).isoformat(),
        provenance='assistant_visual_inspection_of_original_frames',
        is_trained_counter_output=False, is_human_verified_ground_truth=False,
        training_run_started=False, evaluation_ground_truth_eligible=False,
        scope='October training candidates C03-C06 only; September 26 and October 3 are untouched.',
        timing='Intervals of observed pickup/deposit; no claim of frame-exact release. Negative times and times after the original end are context only.',
        coverage='All native frames cached. Visual review used 0.5-second overviews plus 0.1-0.4-second detail sheets at selected movements/boundaries. Not every cached frame was inspected.',
        policy='No fixed blocks-per-hand or blocks-per-tray prior. Unknown material and ambiguous clip boundaries are masked, never silently converted to zero. Left/right means image side, not worker identity.',
        clips=[], object_anchors=[])
    metas={}
    for clip, notes in CLIPS.items():
        meta=json.loads((OUT/clip/'frames.json').read_text());metas[clip]=meta
        original=json.loads((BASE/clip/'annotation.json').read_text())
        # Read the actual last original clip PTS instead of assuming 30 seconds.
        clip_end=float(original['native_relative_timestamps_s'][-1])
        events=[]
        for n, raw in enumerate(notes,1):
            e=copy.deepcopy(raw); e['event_id']=f'{clip}-E{n:02d}'
            e['review_status']='assistant_proposal';e['evaluation_eligible']=False
            e['source_sha256']=meta['source_sha256'];e['actor_reference']='image_side_only'
            if e['action']=='whole_block_transfer':
                p,d=e['pickup_interval_s'],e['deposit_interval_s']
                assert p[0] <= p[1] <= d[1] and d[0] <= d[1]
                if d[1] < 0: status='before_original_clip'
                elif d[0] > clip_end: status='after_original_clip'
                elif d[0] < 0 or d[1] > clip_end: status='boundary_ambiguous'
                else: status='inside_original_clip'
                e['original_clip_attribution']=status
                e['original_clip_proposed_additions']=e['quantity'] if status=='inside_original_clip' else (None if status=='boundary_ambiguous' else 0)
                e['candidate_for_silver_training']=status!='boundary_ambiguous' and e['quantity_confidence']=='high'
                targets=[p[0],p[1],(p[1]+d[0])/2,d[1]]
                e['carry_window_s']=[p[1],d[0]] if d[0]>=p[1] else None
            else:
                a,b=e['interval_s'];targets=[a,(a+b)/2,b]
                e['original_clip_attribution']='non_transfer_or_unresolved'
                e['original_clip_proposed_additions']=e['quantity']
                e['candidate_for_silver_training']=e['quantity'] is not None
            e['evidence_frames']=[nearest(meta,t) for t in targets]
            events.append(e)
        positives=[e for e in events if e['action']=='whole_block_transfer']
        unresolved=[e for e in events if e['quantity'] is None or e['original_clip_attribution']=='boundary_ambiguous']
        subtotal=sum(e['original_clip_proposed_additions'] or 0 for e in positives)
        c=dict(clip_id=clip,source_sha256=meta['source_sha256'],source_file=Path(meta['source_file']).name,
            original_first_source_pts_s=meta['original_first_clip_pts_s'],original_end_relative_pts_s=clip_end,
            roi_xyxy=meta['roi_xyxy'],native_cached_frames=len(meta['files']),
            original_clip_proposed_addition_subtotal=subtotal,
            original_clip_proposed_total=None if unresolved else subtotal,
            unresolved_event_ids=[e['event_id'] for e in unresolved],
            whole_transfer_sequences=len(positives),negative_intervals=sum(e['quantity']==0 for e in events),
            events=events)
        result['clips'].append(c)
    for clip,t,side,boxes in ANCHORS:
        c=next(c for c in result['clips'] if c['clip_id']==clip)
        candidates=[e for e in c['events'] if e['action']=='whole_block_transfer' and e['side']==side and e['pickup_interval_s'][0]<=t<=e['deposit_interval_s'][1]]
        assert len(candidates)==1,(clip,t,side)
        e=candidates[0]
        assert len(boxes)==e['quantity']
        for box in boxes:
            x1,y1,x2,y2=box;assert 0<=x1<x2<=640 and 0<=y1<y2<=360
        result['object_anchors'].append(dict(clip_id=clip,event_id=e['event_id'],side=side,
            frame=nearest(metas[clip],t),class_name='carried_whole_feta_block',
            bbox_format='xyxy',bbox_coordinates='native_640x360_ROI',boxes=boxes,
            annotation_status='assistant_authored_approximate_visible_extent',
            dense_track=False,occluded_extent_inferred=False,
            note='Sparse evidence anchors only; not a fully annotated detector dataset. Do not treat unlabelled tray/tank cheese as detector background.'))
    result['summary']=dict(clips=len(result['clips']),
        transfer_sequences=sum(c['whole_transfer_sequences'] for c in result['clips']),
        negative_intervals=sum(c['negative_intervals'] for c in result['clips']),
        unresolved_cases=sum(len(c['unresolved_event_ids']) for c in result['clips']),
        sparse_object_boxes=sum(len(a['boxes']) for a in result['object_anchors']),
        model_accuracy=None)
    (OUT/'assistant_annotations.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    # Sparse visual anchors, rendered on the inspected native frames.
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
    contact=Image.new('RGB',(1280,784),'#111827'); cd=ImageDraw.Draw(contact)
    for n,(clip,t) in enumerate([('C03',23.2),('C04',21.0),('C05',16.0),('C06',16.0)]):
        frame=nearest(metas[clip],t);im=Image.open(OUT/frame['image']).convert('RGB');d=ImageDraw.Draw(im)
        for a in result['object_anchors']:
            if a['clip_id']==clip:
                for j,b in enumerate(a['boxes'],1):
                    d.rectangle(b,outline='#12f19a',width=2)
                    d.text((b[0],max(0,b[1]-20)),a['side'][0].upper()+str(j),font=font,fill='#12f19a',stroke_width=1,stroke_fill='black')
        im.save(OUT/clip/'object_anchors.jpg',quality=97)
        x=(n%2)*640;y=(n//2)*392
        cd.text((x+7,y+4),f'{clip} t={frame["clip_relative_pts_s"]:.3f}s | ASSISTANT LABELS',font=font,fill='white')
        contact.paste(im,(x,y+32))
    contact.save(OUT/'object_anchor_examples.jpg',quality=97)
    # Supplemental C02 boundary evidence; the original human record is immutable.
    c02=json.loads((OUT/'C02/frames.json').read_text())
    supplement=dict(clip_id='C02',provenance='assistant_visual_boundary_review',
        linked_human_record='../expert_feedback/EXPERT_FEEDBACK_C02.json',
        human_quantity=2,side='left',assistant_pickup_interval_s=[30.2,30.8],
        assistant_deposit_interval_s=[31.4,32.1],
        original_clip_additions_for_this_transfer=0,
        note='Human contact/pickup entry is 29.96 s at cutoff. Additional context shows lift and deposit after the original end. Original expert export was not modified.',
        evidence_frames=[nearest(c02,t) for t in [29.959,30.4,30.8,31.6,32.0]])
    (OUT/'C02_boundary_supplement.json').write_text(json.dumps(supplement,indent=2),encoding='utf-8')
    (OUT/'review_data.js').write_text('const REVIEW_DATA = '+json.dumps(result,ensure_ascii=False)+';\n',encoding='utf-8')
    print(json.dumps(result['summary']))
    for c in result['clips']:
        print(c['clip_id'],c['original_clip_proposed_addition_subtotal'],c['unresolved_event_ids'])

if __name__=='__main__': main()
