"""Render assistant-authored temporal labels; no model inference or tracking."""
from pathlib import Path
import json
import cv2
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/facility_dataset/temporal_pipeline/sequence_annotation_v4/assistant_visual_review'

def main():
    cv2.setNumThreads(2)
    data=json.loads((OUT/'assistant_annotations.json').read_text())
    records=[]
    for c in data['clips']:
        clip=c['clip_id'];meta=json.loads((OUT/clip/'frames.json').read_text())
        times=meta['relative_times_s'];fps=len(times)/(times[-1]-times[0]+float(np.median(np.diff(times))))
        target=OUT/clip/'annotated_review.webm'
        writer=cv2.VideoWriter(str(target),cv2.VideoWriter_fourcc(*'VP80'),fps,(960,690));assert writer.isOpened()
        for i,t in enumerate(times):
            frame=cv2.imread(str(OUT/clip/meta['files'][i]));assert frame is not None
            canvas=np.full((690,960,3),(30,23,16),np.uint8)
            canvas[70:610]=cv2.resize(frame,(960,540))
            def text(s,y,color=(235,235,235),scale=.55):
                cv2.putText(canvas,s,(12,y),cv2.FONT_HERSHEY_SIMPLEX,scale,color,1,cv2.LINE_AA)
            text('ASSISTANT VISUAL LABELS - NOT MODEL INFERENCE',23,(120,220,255),.62)
            text(f'{clip} | original clip time: {t:+07.3f}s | source frame: {meta["source_frame_indices"][i]}',49)
            subtotal=sum(e['quantity'] for e in c['events'] if e['action']=='whole_block_transfer' and e['original_clip_attribution']=='inside_original_clip' and e['deposit_interval_s'][1]<=t)
            suffix=' | UNRESOLVED CASE PRESENT' if c['unresolved_event_ids'] else ' | assistant proposal, unverified'
            text(f'Reviewed additions within original clip: {subtotal}'+suffix,635,(120,220,255))
            active=[]
            for e in c['events']:
                if e['action']=='whole_block_transfer':
                    p,d=e['pickup_interval_s'],e['deposit_interval_s']
                    if p[0]<=t<=d[1]:
                        phase='PICKUP' if t<=p[1] else ('DEPOSIT WINDOW' if t>=d[0] else 'CARRY')
                        active.append(f'{e["side"]}: {e["quantity"]} blocks / {phase}')
                else:
                    a,b=e['interval_s']
                    if a<=t<=b:active.append(f'{e["side"]}: {e["action"]}')
            if t<0 or t>c['original_end_relative_pts_s']:active.insert(0,'CONTEXT OUTSIDE ORIGINAL CLIP')
            text(' | '.join(active)[:140],662,scale=.45)
            writer.write(canvas)
        writer.release()
        cap=cv2.VideoCapture(str(target));n=0
        while cap.read()[0]:n+=1
        cap.release();assert n==len(times),(clip,n,len(times))
        records.append(dict(clip_id=clip,file=f'{clip}/annotated_review.webm',frames=n,preview_fps=fps,
                            first_relative_pts_s=times[0],last_relative_pts_s=times[-1],
                            timing='All native frames, constant preview spacing; burned original PTS authoritative. Subtotal increments after the end of each annotated deposit interval.'))
        print(f'{clip}: rendered and decoded {n} frames',flush=True)
    (OUT/'preview_manifest.json').write_text(json.dumps(records,indent=2))
    (OUT/'preview_data.js').write_text('const PREVIEWS = '+json.dumps(records)+';\n')

if __name__=='__main__':main()
