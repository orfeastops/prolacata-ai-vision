"""Show raw detections from two checkpoints, never label them production counts."""
import os,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];B=R/'outputs/facility_dataset/temporal_pipeline';O=B/'placement_counter_v2/individual_blocks_expanded_v1'
os.environ.update(YOLO_CONFIG_DIR=str(R/'outputs/feta_training/runtime_config'),YOLO_AUTOINSTALL='false')
def main(new_run='individual_blocks_expanded_v1',previous_run='individual_block_learning_diagnostic'):
 import cv2,numpy as np,torch
 from ultralytics import YOLO
 torch.set_num_threads(4);cv2.setNumThreads(2)
 output=B/'placement_counter_v2'/new_run
 assert (output/'summary.json').exists() or (output/'training_complete.json').exists(),'Training must finish first'
 models=[YOLO(str(B/'placement_counter_v2'/previous_run/'run/weights/last.pt')),YOLO(str(output/'run/weights/last.pt'))]
 cap=cv2.VideoCapture(str(B/'sequence_annotation_v2/B023/hands.mp4'))
 ff=R/'work/video_decoder/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
 path=output/'model_comparison_B023.mp4'
 cmd=[str(ff),'-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','bgr24','-s','1280x400','-r','8','-i','-','-an','-c:v','libx264','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(path)]
 records=[]
 with subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE) as proc:
  for i in range(64):
   t=13+i/8;cap.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,frame=cap.read();assert ok
   tiles=[];entry=dict(time_s=t,models=[])
   for index,model in enumerate(models):
    p=model.predict(frame,conf=.25,imgsz=640,device='cpu',verbose=False)[0]
    tile=np.zeros((400,640,3),dtype=np.uint8);tile[40:]=p.plot()
    title=('PREVIOUS' if index==0 else 'EXPANDED')+f' | {t:.3f}s | DETECTIONS, NOT DEPOSIT COUNTS'
    cv2.putText(tile,title,(8,24),cv2.FONT_HERSHEY_SIMPLEX,.40,(255,255,255),1,cv2.LINE_AA)
    tiles.append(tile);entry['models'].append(dict(boxes=p.boxes.xyxy.tolist(),confidence=p.boxes.conf.tolist(),classes=p.boxes.cls.tolist(),names=p.names))
   proc.stdin.write(np.concatenate(tiles,axis=1).tobytes());records.append(entry)
  proc.stdin.close();error=proc.stderr.read().decode();code=proc.wait();assert code==0,error
 cap.release()
 (output/'comparison_raw_predictions.json').write_text(json.dumps(dict(source='B023',previous_run=previous_run,new_run=new_run,start_s=13,end_s=21,fps=8,confidence=.25,quantity_or_deposits_measured=False,frames=records),indent=2))
 test=cv2.VideoCapture(str(path));assert test.isOpened() and int(test.get(cv2.CAP_PROP_FRAME_COUNT))==64;test.release()
 print(str(path))
if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser();parser.add_argument('--new-run',default='individual_blocks_expanded_v1');parser.add_argument('--previous-run',default='individual_block_learning_diagnostic');args=parser.parse_args()
 main(args.new_run,args.previous_run)
