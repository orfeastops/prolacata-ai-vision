"""Frozen September evaluation. Never converts detections into deposit counts."""
import os,json,hashlib,time,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];B=R/'outputs/facility_dataset/temporal_pipeline'
O=B/'unseen_test_20260926/counting_readiness_v2'
os.environ.update(YOLO_CONFIG_DIR=str(R/'outputs/feta_training/runtime_config'),YOLO_AUTOINSTALL='false')
def save(name,data):(O/name).write_text(json.dumps(data,indent=2),encoding='utf-8')
def main():
 import cv2,numpy as np,torch
 from ultralytics import YOLO
 torch.set_num_threads(4);cv2.setNumThreads(2);O.mkdir(exist_ok=True)
 if (O/'report.json').exists():raise RuntimeError('Frozen audit already exists; refusing silent rerun')
 source=B/'unseen_test_20260926/two_tank_counter_v1/indexed.mp4'
 checkpoint=B/'placement_counter_v2/carried_cheese_uncertainty_v2/run/weights/last.pt'
 source_report=json.loads((B/'unseen_test_20260926/two_tank_counter_v1/report.json').read_text())
 manifest=json.loads((B/'placement_counter_v2/carried_cheese_uncertainty_v2/manifest.json').read_text())
 assert source_report['source_sha256'] not in {r['source_sha256'] for r in manifest['frames']}
 cfg=dict(start_s=126,end_s=138,fps=16,confidence=.25,crop=[800,720,640,360],checkpoint=str(checkpoint),checkpoint_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest(),original_source_sha256=source_report['source_sha256'],indexed_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),training_on_test=False,threshold_tuning_on_test=False,deposit_counter_available=False,source_clock_note='Encoded-video seconds. User release interval is approximate relative to decoded sample timestamps.')
 save('frozen_config.json',cfg)
 ff=R/'work/video_decoder/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
 decoder=subprocess.Popen([str(ff),'-loglevel','error','-ss','126','-i',str(source),'-t','12','-vf','crop=640:360:800:720,fps=16','-f','rawvideo','-pix_fmt','bgr24','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 encoder=subprocess.Popen([str(ff),'-loglevel','error','-y','-f','rawvideo','-pix_fmt','bgr24','-s','1280x420','-r','16','-i','-','-an','-c:v','libx264','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(O/'four_block_test.mp4')],stdin=subprocess.PIPE,stderr=subprocess.PIPE)
 model=YOLO(str(checkpoint));rows=[];start=time.time()
 try:
  i=0
  while True:
   data=decoder.stdout.read(640*360*3)
   if not data:break
   assert len(data)==640*360*3
   frame=np.frombuffer(data,dtype=np.uint8).reshape(360,640,3).copy();t=126+i/16
   p=model.predict(frame,conf=.25,imgsz=640,device='cpu',verbose=False)[0]
   row=dict(time_s=t,boxes=p.boxes.xyxy.tolist(),classes=[int(x) for x in p.boxes.cls.tolist()],confidence=p.boxes.conf.tolist(),model_deposit_count=None)
   rows.append(row)
   canvas=np.zeros((420,1280,3),np.uint8);canvas[60:,:640]=frame;canvas[60:,640:]=p.plot()
   for x,title in [(8,'SOURCE'),(648,'FROZEN MODEL - DETECTIONS ONLY')]:cv2.putText(canvas,title,(x,22),0,.55,(255,255,255),1,cv2.LINE_AA)
   cv2.putText(canvas,f'Video {t:.3f}s | Deposit count: UNAVAILABLE | Not a block total',(8,48),0,.6,(0,200,255),1,cv2.LINE_AA)
   encoder.stdin.write(canvas.tobytes())
   if i%16==0:save('progress.json',dict(status='running',frames=i+1,total_expected=192,elapsed_seconds=round(time.time()-start)))
   if i in [64,72,80,88,96,102,104,112,120,128]:
    cv2.imwrite(str(O/f'frame_{t:.3f}.jpg'),canvas)
   i+=1
 finally:
  decoder.stdout.close();de=decoder.stderr.read().decode();dc=decoder.wait();encoder.stdin.close();ee=encoder.stderr.read().decode();ec=encoder.wait()
 assert dc==0 and ec==0,(de,ee)
 # The remux begins on a fractional timestamp; fps resampling can omit an endpoint frame.
 assert 190<=len(rows)<=192,len(rows)
 save('frame_predictions.json',rows)
 truth=json.loads((B/'unseen_test_20260926/two_tank_counter_v1/user_error_review_130_132.json').read_text())['user_annotation']
 event=[r for r in rows if 130<=r['time_s']<=133]
 report=dict(status='completed_counting_capability_gate_failed',frames_processed=len(rows),processed_interval_s=[126,138],user_confirmed_blocks=truth['whole_blocks_deposited'],user_reported_pickup_s=truth['pickup_s'],user_reported_release_interval_s=truth['release_interval_s'],predicted_deposited_blocks=None,count_error=None,count_accuracy=None,reason='Frozen trained network outputs per-frame regions/classes only. No connected physical-block association or deposit completion module. Missing count is not zero.',single_region_detections_in_event_frames=sum(c==0 for r in event for c in r['classes']),unknown_region_detections_in_event_frames=sum(c==1 for r in event for c in r['classes']),frame_detection_totals_are_not_unique_blocks=True,training_on_test=False,threshold_tuning_on_test=False,production_ready=False,full_two_tank_count_available=False,preview='four_block_test.mp4')
 report['last_sample_s']=rows[-1]['time_s']
 save('report.json',report);save('progress.json',dict(status='complete',frames=len(rows)));print(json.dumps(report))
if __name__=='__main__':main()
