"""Single frozen full-video evaluation. Never train or tune on September frames."""
import time
from pathlib import Path
import cv2,torch,numpy as np
from ultralytics import YOLO
from evaluate_payload_counter_v5 import Counter,CONFIG,ROOT,BASE,OUT
from train_transfer_events_v4 import save,load,digest
WEB=BASE/'sequence_annotation_v4/object_model_review'
def main():
    torch.set_num_threads(4);cv2.setNumThreads(2);WEB.mkdir(parents=True,exist_ok=True)
    if (OUT/'september_results.json').exists():raise RuntimeError('Frozen September result already exists')
    complete=load(OUT/'training_complete.json');checkpoint=Path(complete['checkpoint'])
    assert digest(checkpoint)==complete['checkpoint_sha256']
    old=BASE/'unseen_test_20260926/two_tank_counter_v1'
    source=Path(load(old/'report.json')['source']);reference=load(old/'blind_prediction_report.json')
    sha=digest(source);assert sha==reference['source_sha256']
    assert sha not in {r['source_sha256'] for r in load(OUT/'dataset_manifest.json')['rows']}
    intervals=reference['manual_tank_intervals']
    save(OUT/'september_frozen_before_test.json',dict(config=CONFIG,checkpoint_sha256=digest(checkpoint),
        source_sha256=sha,manual_tank_intervals=intervals,tank_intervals_source='Preserved pre-existing manual review; not detected by model',
        script_sha256=digest(__file__),decoder_sha256=digest(Path(__file__).with_name('evaluate_payload_counter_v5.py')),
        user_counts_received=False,training_on_test=False,threshold_tuning_on_test=False,frozen_at_unix=time.time()))
    cap=cv2.VideoCapture(str(source));assert cap.isOpened()
    model=YOLO(str(checkpoint));counter=Counter();n=0;times=[];frame_outputs=[]
    preview=WEB/'september_two_tanks_v5.webm'
    writer=None;initial=[];first_pts=None;last_pts=-1
    def consume(batch,pts):
        nonlocal n,writer,initial
        results=model.predict(source=batch,imgsz=640,device='cpu',conf=CONFIG['detection_confidence'],
            iou=CONFIG['nms_iou'],agnostic_nms=True,verbose=False)
        for frame,t,result in zip(batch,pts,results):
            ds=[dict(bbox=[float(v) for v in b],confidence=float(s),quantity=CONFIG['quantity_class_map'][int(c)])
                for b,s,c in zip(result.boxes.xyxy.cpu().numpy(),result.boxes.conf.cpu().numpy(),result.boxes.cls.cpu().numpy())]
            linked=counter.step(t,ds);frame_outputs.append(dict(time_s=t,detections=linked));times.append(t);n+=1
            canvas=np.full((438,640,3),(24,18,15),np.uint8);canvas[:360]=frame
            for d in linked:
                x1,y1,x2,y2=map(int,d['bbox']);color=(50,220,90) if d['quantity'] else (30,150,245)
                cv2.rectangle(canvas,(x1,y1),(x2,y2),color,1)
                cv2.putText(canvas,f"#{d['track_id']} q={d['quantity'] or '?'}",(x1,max(12,y1-3)),cv2.FONT_HERSHEY_SIMPLEX,.4,color,1,cv2.LINE_AA)
            totals={a['tank_id']:sum(e['predicted_quantity'] for e in counter.events if a['start_s']<=e['time_s']<a['end_s']) for a in intervals}
            cv2.putText(canvas,f"V5 MODEL | {t:.2f}s | A +{totals['A']} | B +{totals['B']}",(9,383),cv2.FONT_HERSHEY_SIMPLEX,.55,(230,230,230),1,cv2.LINE_AA)
            cv2.putText(canvas,'Experimental additions; manual tank boundaries; not verified totals',(9,407),cv2.FONT_HERSHEY_SIMPLEX,.41,(100,200,255),1,cv2.LINE_AA)
            cv2.putText(canvas,f'Unresolved tracks: {len(counter.rejected)}',(9,429),cv2.FONT_HERSHEY_SIMPLEX,.42,(200,200,200),1,cv2.LINE_AA)
            if writer is None:
                initial.append(canvas)
                if len(initial)>=16:
                    fps=(len(times)-1)/(times[-1]-times[0]);writer=cv2.VideoWriter(str(preview),cv2.VideoWriter_fourcc(*'VP80'),fps,(640,438));assert writer.isOpened()
                    for f in initial:writer.write(f)
                    initial=[]
            else:writer.write(canvas)
        save(OUT/'september_progress.json',dict(status='running',native_frames=n,processed_seconds=times[-1],source_sha256=sha))
    batch=[];pts=[];i=0
    while True:
        ok,full=cap.read()
        if not ok:break
        current=cap.get(cv2.CAP_PROP_POS_MSEC)/1000
        if first_pts is None:first_pts=current
        t=float(current-first_pts)
        assert t>last_pts or i==0,(i,t,last_pts)
        last_pts=t;i+=1;batch.append(full[720:1080,800:1440].copy());pts.append(t)
        if len(batch)==8:consume(batch,pts);batch=[];pts=[]
    if batch:consume(batch,pts)
    cap.release();assert writer is not None;writer.release();assert n==i
    counter.finish(times[-1])
    totals={a['tank_id']:sum(e['predicted_quantity'] for e in counter.events if a['start_s']<=e['time_s']<a['end_s']) for a in intervals}
    unassigned=[e for e in counter.events if not any(a['start_s']<=e['time_s']<a['end_s'] for a in intervals)]
    check=cv2.VideoCapture(str(preview));verified=0
    while True:
        ok,_=check.read()
        if not ok:break
        verified+=1
    check.release();assert verified==n
    save(OUT/'september_frame_predictions.json',frame_outputs)
    save(OUT/'september_results.json',dict(status='completed_experimental_not_validated',source_sha256=sha,
        frames_processed=n,duration_processed_s=times[-1],first_decoded_pts_s=first_pts,
        predicted_additions_by_tank=totals,accepted_events=counter.events,unresolved_tracks=counter.rejected,
        unassigned_events=unassigned,manual_tank_intervals=intervals,preview=str(preview),preview_verified_frames=verified,
        sampling='every native decoded frame, original PTS; preview encoded at measured average fps',
        model_accuracy=None,user_counts_received=False,training_on_test=False,threshold_tuning_on_test=False,
        exact_tank_totals=None,production_ready=False,test_status='Never trained; visually inspected in previous diagnostic work, not pristine acceptance data',
        checkpoint_sha256=digest(checkpoint)))
if __name__=='__main__':main()
