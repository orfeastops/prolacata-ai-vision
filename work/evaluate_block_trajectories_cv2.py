"""Same frozen model/tracker, using the installed in-process video codec.

External FFmpeg execution became inaccessible. This runs a separately recorded
evaluation with OpenCV timestamp sampling; it does not modify or replace the
first backend's observations or parameters.
"""
import json,time,argparse
from pathlib import Path
import evaluate_block_trajectories as original
from evaluate_block_trajectories import ROOT,BASE,CHECKPOINT,CONFIG,HypothesisTracker,save,sha

OUT=original.OUT/'opencv_run'


def sampled_frames(source,crop):
    import cv2
    cap=cv2.VideoCapture(str(source))
    if not cap.isOpened(): raise RuntimeError(f'Cannot decode {source}')
    rate=cap.get(cv2.CAP_PROP_FPS)
    n=cap.get(cv2.CAP_PROP_FRAME_COUNT)
    if rate<=0 or n<=0: raise RuntimeError('Missing video timing metadata')
    target=0;index=0
    try:
        while True:
            ok,frame=cap.read()
            if not ok:break
            stamp=cap.get(cv2.CAP_PROP_POS_MSEC)/1000
            # Indexed source has regular encoded timestamps; save actual time.
            if stamp+1e-6>=target/CONFIG['fps']:
                if crop:frame=frame[720:1080,800:1440]
                if frame.shape[:2]!=(360,640):raise RuntimeError(f'Unexpected dimensions {frame.shape}')
                yield target/CONFIG['fps'],stamp,frame
                target+=1
            index+=1
        if index<int(n)-2:raise RuntimeError(f'Decoder ended early: {index}/{n}')
    finally:cap.release()


def analyze(model,source,dest,crop):
    import cv2,numpy as np
    dest.mkdir(parents=True,exist_ok=True)
    if (dest/'report.json').exists():return json.loads((dest/'report.json').read_text())
    writer=cv2.VideoWriter(str(dest/'trajectory_preview.webm'),cv2.VideoWriter_fourcc(*'VP80'),8,(640,420))
    if not writer.isOpened():raise RuntimeError('VP8 encoder unavailable')
    tracker=HypothesisTracker();start=time.time();count=0;max_time_offset=0;last_actual=None
    def process(batch,stream):
        nonlocal count,max_time_offset,last_actual
        predictions=model.predict([r[2] for r in batch],conf=CONFIG['detector_confidence'],iou=CONFIG['detector_iou'],imgsz=640,device='cpu',verbose=False,rect=True)
        for (t,actual,frame),pred in zip(batch,predictions):
            if actual-t>.15:raise RuntimeError(f'Unexpected sampling time discrepancy {actual-t}')
            max_time_offset=max(max_time_offset,abs(actual-t));last_actual=actual
            detections=[dict(box=b,cls=int(c),confidence=float(p)) for b,c,p in zip(pred.boxes.xyxy.tolist(),pred.boxes.cls.tolist(),pred.boxes.conf.tolist())]
            tracks=tracker.update(t,detections)
            stream.write(json.dumps(dict(time_s=t,source_time_s=actual,detections=tracks))+'\n')
            for r in tracks:
                x1,y1,x2,y2=map(int,r['box']);color=(0,160,255) if r['ambiguous'] or r['cls'] else (0,230,0)
                cv2.rectangle(frame,(x1,y1),(x2,y2),color,1)
                cv2.putText(frame,f"T{r['track_id']} {'1?' if r['cls']==0 else 'qty?'}",(x1,max(12,y1-3)),0,.4,color,1)
            for name,color in [('tank_polygon',(0,255,255)),('source_polygon',(255,130,0))]:
                cv2.polylines(frame,[np.array(CONFIG[name],np.int32)],True,color,1)
            canvas=np.zeros((420,640,3),np.uint8);canvas[60:]=frame
            candidate=sum(e['candidate_quantity'] or 0 for e in tracker.events)
            unresolved=sum(e['candidate_quantity'] is None for e in tracker.events)
            cv2.putText(canvas,f'{t:.2f}s | Transfer hypotheses: {candidate} | Unresolved tracks: {unresolved}',(7,20),0,.45,(255,255,255),1)
            cv2.putText(canvas,'EXPERIMENTAL - incomplete count; disappearance is not verified release',(7,44),0,.4,(0,180,255),1)
            writer.write(canvas);count+=1
        progress=dict(status='running',frames=count,video_seconds=count/8,elapsed_seconds=round(time.time()-start,1))
        save(dest/'progress.json',progress)
        if count%240==0:print(dest.name,json.dumps(progress),flush=True)
    try:
        with (dest/'observations.jsonl').open('w',encoding='utf-8') as stream:
            batch=[]
            for row in sampled_frames(source,crop):
                batch.append(row)
                if len(batch)==8:process(batch,stream);batch=[]
            if batch:process(batch,stream)
    finally:writer.release()
    tracker.close()
    save(dest/'events.json',tracker.events)
    report=dict(status='complete_experimental',frames_processed=count,duration_processed_s=count/8,
        last_actual_source_time_s=last_actual,max_source_sample_offset_s=max_time_offset,
        transfer_hypothesis_count=sum(e['candidate_quantity'] or 0 for e in tracker.events),
        unresolved_tracks=sum(e['candidate_quantity'] is None for e in tracker.events),
        complete_block_count=None,count_complete=False,production_ready=False,
        elapsed_seconds=round(time.time()-start,1),video='trajectory_preview.webm')
    save(dest/'report.json',report);save(dest/'progress.json',dict(report,status='complete'))
    return report


def main():
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['development','september']);args=parser.parse_args()
    import torch,cv2
    from ultralytics import YOLO
    torch.set_num_threads(4);cv2.setNumThreads(2)
    original.freeze();OUT.mkdir(parents=True,exist_ok=True)
    config=dict(config=CONFIG,checkpoint_sha256=sha(CHECKPOINT),counter_sha256=sha(Path(original.__file__)),
        decoder_runner_sha256=sha(Path(__file__)),backend='OpenCV decoded timestamps, first source frame at or after each 8Hz target',
        change_reason='External FFmpeg directory Access denied; authorized in-process codec available',
        training_on_test=False,threshold_tuning_on_test=False,prior_test_exposure=True)
    if (OUT/'frozen_config.json').exists():assert json.loads((OUT/'frozen_config.json').read_text())==config
    else:save(OUT/'frozen_config.json',config)
    model=YOLO(str(CHECKPOINT))
    if args.stage=='development':
        segments=json.loads((BASE/'sequence_annotation_v2/count_checkpoint_v2/segments.json').read_text());results=[]
        for s in segments:
            r=analyze(model,Path(s['media_path']),OUT/'october_development'/s['segment_id'],False)
            results.append(dict(segment_id=s['segment_id'],confirmed_deposits=s['confirmed_count'],
                hypotheses=r['transfer_hypothesis_count'],unresolved_tracks=r['unresolved_tracks'],
                absolute_count_difference=abs(r['transfer_hypothesis_count']-s['confirmed_count'])))
        report=dict(segments=results,confirmed_deposits=sum(r['confirmed_deposits'] for r in results),
            hypotheses=sum(r['hypotheses'] for r in results),
            mean_absolute_count_difference=sum(r['absolute_count_difference'] for r in results)/len(results),
            exact_segment_matches=sum(r['confirmed_deposits']==r['hypotheses'] for r in results),
            independent_test=False,production_ready=False,scope='October development; training source overlap; hypotheses are not complete counts')
        save(OUT/'october_development_report.json',report);print(json.dumps(report),flush=True)
    else:
        previous=json.loads((BASE/'unseen_test_20260926/two_tank_counter_v1/blind_prediction_report.json').read_text())
        manifest=json.loads((BASE/'placement_counter_v2/carried_cheese_uncertainty_v2/manifest.json').read_text())
        assert previous['source_sha256'] not in {r['source_sha256'] for r in manifest['frames']}
        source=BASE/'unseen_test_20260926/two_tank_counter_v1/indexed.mp4'
        report=analyze(model,source,OUT/'september_full_video',True)
        events=json.loads((OUT/'september_full_video/events.json').read_text())
        intervals=previous['manual_tank_intervals'];by_tank={r['tank_id']:dict(hypotheses=0,unresolved_tracks=0) for r in intervals}
        unassigned=dict(hypotheses=0,unresolved_tracks=0)
        for e in events:
            matches=[r for r in intervals if r['start_s']<=e['first_s'] and e['last_s']<=r['end_s']]
            e['tank_id']=matches[0]['tank_id'] if len(matches)==1 else None
            target=by_tank[e['tank_id']] if e['tank_id'] else unassigned
            target['hypotheses']+=e['candidate_quantity'] or 0;target['unresolved_tracks']+=e['candidate_quantity'] is None
        save(OUT/'september_full_video/events_with_manual_tanks.json',events)
        report.update(hypotheses_by_manual_tank=by_tank,unassigned=unassigned,tank_intervals=intervals,
            tank_change_detection='manual, approximately 2-second boundaries',original_source_sha256=previous['source_sha256'],
            indexed_sha256=sha(source),user_tank_counts_received=False,independent_count_accuracy=None,
            training_on_test=False,threshold_tuning_on_test=False,prior_test_exposure=True)
        save(OUT/'september_full_video/frozen_prediction_report.json',report);print(json.dumps(report),flush=True)

if __name__=='__main__':main()
