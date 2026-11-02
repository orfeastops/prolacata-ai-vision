"""Run fixed camera ROI detection on every native frame of October 21.

The automatic episode decoder receives only model detections. Separately
selected arrival snapshots are diagnostic illustrations, never decoder input.
"""
import os
os.environ['YOLO_AUTOINSTALL']='false';os.environ['YOLO_OFFLINE']='true'
os.environ['OMP_NUM_THREADS']='4'
import json,time,traceback
from pathlib import Path
import cv2,numpy as np,torch
from ultralytics import YOLO
from build_arrival_detector_v7 import ROOT,OUT,AUDIT,ROI,crop,save,digest
from arrival_counter_v7 import ArrivalCounter,CONFIG,group_detections

# Chosen from the previously reviewed October arrival sequence before inference.
# They are not passed to the model or online episode decoder.
SNAPSHOTS=[('T11',6.,10),('T12',21.5,10),('T13',37.,10),('T14',55.5,10),
 ('T15',73.75,None),('T16',115.5,10),('T17',147.,7),('T18',166.75,10),('T19',180.,10),('T20',191.5,10)]

def overlay(frame,detections,t,index,groups):
    canvas=np.zeros((416,640,3),np.uint8);canvas[56:]=frame
    colors={0:(60,230,80),1:(240,220,0),2:(0,220,255),3:(0,140,255)}
    for d in detections:
        b=d['bbox'];x1,y1,x2,y2=[int(round(v)) for v in b]
        color=colors[d['class_id']]
        cv2.rectangle(canvas,(x1+ROI[0],y1+ROI[1]+56),(x2+ROI[0],y2+ROI[1]+56),color,1)
        if d['class_id']!=2:cv2.putText(canvas,['C','E','T','?'][d['class_id']],(x1+ROI[0],max(60,y1+ROI[1]+54)),cv2.FONT_HERSHEY_SIMPLEX,.35,color,1)
    best=max(groups,key=lambda g:g['position_count'],default=None)
    summary=f"visible cheese={best['cheese']} empty={best['empty']} unknown={best['obscured']}" if best else 'tray not detected'
    cv2.putText(canvas,f'OCT21  source={t:.3f}s frame={index} | MODEL',{(0):0}.get(1,(8,20)),cv2.FONT_HERSHEY_SIMPLEX,.5,(255,255,255),1)
    cv2.putText(canvas,summary,(8,44),cv2.FONT_HERSHEY_SIMPLEX,.5,(255,255,255),1)
    return canvas

def main():
    if (OUT/'inference_started.json').exists():raise RuntimeError('Inference already started; inspect saved state, do not duplicate')
    complete=json.loads((OUT/'training_complete.json').read_text());weights=Path(complete['checkpoint'])
    assert digest(weights)==complete['checkpoint_sha256']
    meta=json.loads((AUDIT/'O21/frames.json').read_text())
    refs=[dict(id=ident,source_time_s=t,initial_count_reference=n,
        provenance='previous assistant tray audit; seven-block case previously user-confirmed',
        not_fully_independent=True) for ident,t,n in SNAPSHOTS]
    save(OUT/'arrival_reference_schedule.json',refs)
    save(OUT/'counter_frozen_before_inference.json',dict(config=CONFIG,roi=ROI,checkpoint_sha256=digest(weights),
        source_sha256=meta['source_sha256'],code_sha256={n:digest(ROOT/'work'/n) for n in ['arrival_counter_v7.py','evaluate_arrival_detector_v7.py']},
        no_manual_position_input=True,no_reference_count_input=True,native_frames=True,
        source_not_in_optimizer_training=True,september_used=False,independent_acceptance=False))
    torch.set_num_threads(4);cv2.setNumThreads(2);model=YOLO(str(weights))
    (OUT/'snapshots').mkdir(exist_ok=True);start=time.time()
    save(OUT/'inference_started.json',dict(pid=os.getpid(),started_unix=start))
    counter=ArrivalCounter();snapshot_results=[];next_snapshot=0;total=0
    cap=cv2.VideoCapture(meta['source_file']);assert cap.isOpened()
    preview=OUT/'october21_arrivals_v7.webm';writer=cv2.VideoWriter(str(preview),cv2.VideoWriter_fourcc(*'VP80'),15.,(640,416))
    assert writer.isOpened();cache=(OUT/'frame_predictions.jsonl').open('w',encoding='utf-8')
    try:
        ended=False
        while not ended:
            batch=[];rois=[]
            for _ in range(8):
                ok,im=cap.read()
                if not ok:ended=True;break
                t=cap.get(cv2.CAP_PROP_POS_MSEC)/1000;frame=im[720:1080,800:1440].copy()
                batch.append((total,t,frame));rois.append(crop(frame));total+=1
            if not batch:break
            predicted=model.predict(source=rois,imgsz=384,device='cpu',conf=CONFIG['detection_confidence'],
                iou=CONFIG['model_nms_iou'],agnostic_nms=False,verbose=False)
            for (index,t,frame),r in zip(batch,predicted):
                detections=[dict(bbox=[float(v) for v in b],confidence=float(s),class_id=int(c))
                    for b,s,c in zip(r.boxes.xyxy.cpu().numpy(),r.boxes.conf.cpu().numpy(),r.boxes.cls.cpu().numpy())]
                groups=counter.step(t,detections,index)
                record=dict(frame_index=index,time_s=t,detections=detections,groups=groups)
                cache.write(json.dumps(record)+'\n')
                picture=overlay(frame,detections,t,index,groups);writer.write(picture)
                if next_snapshot<len(SNAPSHOTS) and t>=SNAPSHOTS[next_snapshot][1]:
                    ident,_,_=SNAPSHOTS[next_snapshot];next_snapshot+=1
                    path=OUT/'snapshots'/f'{ident}.jpg';cv2.imwrite(str(path),picture,[cv2.IMWRITE_JPEG_QUALITY,96])
                    best=max(groups,key=lambda g:g['position_count'],default=None)
                    snapshot_results.append(dict(id=ident,time_s=t,frame_index=index,
                        predicted_visible_cheese=best['cheese'] if best else None,
                        observed_positions=best['position_count'] if best else 0,
                        observed_empty=best['empty'] if best else 0,
                        observed_unknown=best['obscured'] if best else None,
                        complete_positions=best['complete_positions'] if best else False,
                        automatic_initial_count=best['initial_count'] if best else None,
                        image=str(path),detections=detections))
            if total%200<8:
                save(OUT/'inference_progress.json',dict(native_frames=total,total_expected=meta['native_frames_decoded'],
                    source_time_s=t,elapsed_s=time.time()-start,closed_tracks=len(counter.records),snapshots=len(snapshot_results)))
                print('native frames',total,'source seconds',round(t,2),'elapsed',round(time.time()-start,1),flush=True)
        records=counter.finish();cap.release();writer.release();cache.close()
        assert total==meta['native_frames_decoded'],(total,meta['native_frames_decoded'])
        # Seal predictions before joining count references.
        save(OUT/'predictions_frozen.json',dict(native_frames=total,records=records,snapshots=snapshot_results,
            checkpoint_sha256=digest(weights),elapsed_s=time.time()-start,video=str(preview)))
        score_snapshot(snapshot_results,refs,records)
        save(OUT/'inference_complete.json',dict(native_frames=total,elapsed_s=time.time()-start,
            prediction_sha256=digest(OUT/'predictions_frozen.json'),preview=str(preview),september_used=False))
    except Exception as e:
        cap.release();writer.release();cache.close()
        save(OUT/'inference_failure.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()));raise

def score_snapshot(predictions,refs,records):
    refs={r['id']:r for r in refs};scored=[]
    for p in predictions:
        r=refs[p['id']];expected=r['initial_count_reference']
        scored.append(dict(**p,reference_count=expected,
            exact_snapshot=(p['predicted_visible_cheese']==expected) if expected is not None else None))
    eligible=[p for p in scored if p['reference_count'] is not None]
    available=[p for p in eligible if p['predicted_visible_cheese'] is not None]
    proposals=[r for r in records if r['status']=='automatic_arrival_proposal']
    # Match automatic episode time to reviewed arrivals only for diagnostics.
    matched=[];used=set()
    for p in scored:
        target=p['time_s'];candidates=[(abs(r['count_source_time_s']-target),i,r) for i,r in enumerate(proposals)
            if i not in used and r['count'] is not None and abs(r['count_source_time_s']-target)<=3]
        candidate=min(candidates,key=lambda x:x[0]) if candidates else None
        if candidate:used.add(candidate[1])
        matched.append(dict(id=p['id'],reference_count=p['reference_count'],
            automatic_count=candidate[2]['count'] if candidate else None,
            automatic_time_s=candidate[2]['count_source_time_s'] if candidate else None,
            matched_tray_id=candidate[2]['tray_id'] if candidate else None))
    automatic_eligible=[r for r in matched if r['reference_count'] is not None]
    result=dict(snapshot_rows=scored,snapshot_metrics=dict(arrivals=len(eligible),
            exact=sum(p['exact_snapshot'] for p in eligible),model_returned_count=len(available),
            mean_absolute_error_on_returned_counts=sum(abs(p['predicted_visible_cheese']-p['reference_count']) for p in available)/len(available) if available else None),
        automatic_rows=matched,automatic_metrics=dict(reviewed_arrivals=len(automatic_eligible),
            exact=sum(r['automatic_count']==r['reference_count'] for r in automatic_eligible),
            no_matched_automatic_count=sum(r['automatic_count'] is None for r in automatic_eligible),
            automatic_records_in_full_video=len(proposals),unmatched_records_in_full_video=len(proposals)-len(used)),
        interpretation='Snapshot intervals are manually selected development diagnostics. Automatic episode results are separate and may duplicate or miss trays. No full-day reference count is available.',
        no_count_clamp=True,source_disjoint_from_training=True,independent_acceptance=False,
        production_ready=False,september_used=False)
    save(OUT/'count_results.json',result)
    print(json.dumps({k:v for k,v in result.items() if k.endswith('metrics')},indent=2),flush=True)

if __name__=='__main__':main()
