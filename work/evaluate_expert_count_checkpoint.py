"""Run unchanged v1 on expert review clips; development diagnostics only."""
import pathlib, json, hashlib, time, importlib.util
import cv2, numpy as np, torch
from ultralytics import YOLO

R=pathlib.Path(__file__).resolve().parents[1]
T=R/'outputs/facility_dataset/temporal_pipeline'
D=T/'sequence_annotation_v2/count_checkpoint_v2'
O=D/'unchanged_v1'; O.mkdir(exist_ok=True)
snapshot=O/'counter_source_snapshot.py'
spec=importlib.util.spec_from_file_location('frozen_counter_v1',snapshot)
legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
AppearanceModel,Tracker,bridge_flow,feature,roi=(getattr(legacy,k) for k in ['AppearanceModel','Tracker','bridge_flow','feature','roi'])
rows=json.loads((D/'segments.json').read_text())
cfg=json.loads((T/'placement_counter_v1/frozen_config.json').read_text())
torch.set_num_threads(4);cv2.setNumThreads(2)
detector=YOLO(str(R/'outputs/feta_training/hands_detector.pt'))
state_path=T/'placement_counter_v1/hand_object_state.npz'
state=AppearanceModel(state_path)
results=[];started=time.time()
for row in rows:
    cap=cv2.VideoCapture(row['media_path']);fps=cap.get(cv2.CAP_PROP_FPS)
    assert fps==16 and cfg['fps']==8
    tracker=Tracker(cfg);previous=None;frame_idx=0;processed=0
    while True:
        ok,frame=cap.read()
        if not ok:break
        frame_idx+=1
        if (frame_idx-1)%2:continue
        t=processed/8
        prediction=detector.predict(frame,conf=cfg['detector_confidence'],iou=.35,imgsz=640,device='cpu',verbose=False)[0]
        boxes=bridge_flow(previous,frame,tracker,prediction.boxes.xyxy.cpu().numpy(),t)
        probs=state.predict_proba(np.array([feature(roi(frame,b)) for b in boxes]))[:,1] if len(boxes) else []
        tracker.update(t,boxes,probs);previous=frame.copy();processed+=1
    cap.release();tracker.close(processed/8)
    assert abs(processed/8-row['duration_s']) <= .13
    count=sum(e['predicted_quantity'] or 0 for e in tracker.events)
    result=dict(segment_id=row['segment_id'],confirmed_count=row['confirmed_count'],
        predicted_count=count,signed_error=count-row['confirmed_count'],
        absolute_error=abs(count-row['confirmed_count']),frames=processed,
        unresolved=sum(e['predicted_quantity'] is None for e in tracker.events))
    results.append(result)
    (O/(row['segment_id']+'_events.json')).write_text(json.dumps(tracker.events,indent=2))
    (O/'progress.json').write_text(json.dumps(dict(completed=len(results),total=len(rows),elapsed_s=time.time()-started)))
    print(json.dumps(result),flush=True)
report=dict(role='Development diagnostics on user-reviewed clips, not an independent accuracy estimate',
    rows=results,segments=len(results),confirmed_sum=sum(r['confirmed_count'] for r in results),
    predicted_sum=sum(r['predicted_count'] for r in results),
    mean_absolute_count_error=float(np.mean([r['absolute_error'] for r in results])),
    exact_count_segments=sum(r['absolute_error']==0 for r in results),
    false_counts_on_zero_segments=sum(r['predicted_count'] for r in results if r['confirmed_count']==0),
    event_precision=None,event_recall=None,
    caveats=['Segment totals can hide cancelling misses and false detections.',
      'Clip boundaries can truncate pickup evidence.',
      'These clips are reviewed development material, not unseen test data.'],
    state_model_sha256=hashlib.sha256(state_path.read_bytes()).hexdigest(),
    training_performed=False,thresholds_changed=False,production_ready=False)
(O/'report.json').write_text(json.dumps(report,indent=2))
print('FINISHED '+json.dumps({k:v for k,v in report.items() if k!='rows'}),flush=True)
