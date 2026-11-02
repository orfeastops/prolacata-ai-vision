"""Fine-tune the whole YOLO detector on reviewed payload images, source split."""
import os
os.environ['YOLO_AUTOINSTALL']='false'
os.environ['YOLO_OFFLINE']='true'
os.environ['OMP_NUM_THREADS']='4'
os.environ['YOLO_CONFIG_DIR']=os.path.abspath('outputs/feta_training/runtime_config')
os.environ['MPLCONFIGDIR']=os.path.abspath('outputs/feta_training/matplotlib_config')
os.environ['MPLBACKEND']='Agg'
import time, json, hashlib
from pathlib import Path
import torch,cv2
from ultralytics import YOLO
from ultralytics.models.yolo.detect import DetectionTrainer
from train_transfer_events_v4 import save,digest
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/facility_dataset/temporal_pipeline/placement_counter_v5/object_expansion'
CONFIG=dict(epochs=60,imgsz=640,batch=8,nbs=8,rect=True,workers=0,device='cpu',
    optimizer='AdamW',lr0=.001,lrf=.1,weight_decay=.0005,warmup_epochs=3,
    freeze=0,seed=2910,deterministic=True,patience=0,cos_lr=True,
    mosaic=0,mixup=0,copy_paste=0,fliplr=0,flipud=0,degrees=0,
    translate=.04,scale=.12,hsv_h=0,hsv_s=.1,hsv_v=.12,
    cache=False,amp=False,plots=False,save_period=20,val=True,verbose=False)
def main():
    torch.set_num_threads(4);cv2.setNumThreads(2)
    if (OUT/'training_complete.json').exists():raise RuntimeError('Frozen run exists; do not overwrite.')
    if (OUT/'training_started.json').exists():raise RuntimeError('Run already started; inspect progress before restarting.')
    manifest=json.loads((OUT/'dataset_manifest.json').read_text())
    generic=ROOT/'outputs/feta_training/yolo26n.pt'
    save(OUT/'training_config.json',dict(config=CONFIG,initial_weights=str(generic),initial_sha256=digest(generic),
        initial_weights_provenance='generic pretrained model, never a facility fine-tuned checkpoint',
        training_manifest_sha256=digest(OUT/'dataset_manifest.json'),validation='D03, D07, D08 source files; no optimizer updates',
        final_checkpoint='last.pt after all 60 epochs; no checkpoint selection on counting benchmark',
        september_training=False,october3_training=False))
    start=time.time();save(OUT/'training_started.json',dict(started_at_unix=start,pid=os.getpid()))
    class Trainer(DetectionTrainer):
        def optimizer_step(self):
            super().optimizer_step();self.real_updates=getattr(self,'real_updates',0)+1
    model=YOLO(str(generic))
    def epoch_end(t):
        save(OUT/'training_progress.json',dict(status='training',completed_epochs=t.epoch+1,total_epochs=CONFIG['epochs'],
            optimizer_updates=getattr(t,'real_updates',0),elapsed_s=time.time()-start,
            loss={str(k):float(v) for k,v in t.tloss.items()} if isinstance(t.tloss,dict) else [float(x) for x in t.tloss],
            metrics={k:float(v) for k,v in t.metrics.items()}))
    model.add_callback('on_fit_epoch_end',epoch_end)
    try:
        model.train(trainer=Trainer,data=str(OUT/'dataset/data.yaml'),project=str(OUT),name='detector_run',exist_ok=False,**CONFIG)
        last=OUT/'detector_run/weights/last.pt';assert last.exists()
        save(OUT/'training_complete.json',dict(status='complete',epochs=CONFIG['epochs'],optimizer_updates=getattr(model.trainer,'real_updates',0),
            elapsed_s=time.time()-start,checkpoint=str(last),checkpoint_sha256=digest(last),
            dataset_manifest_sha256=digest(OUT/'dataset_manifest.json'),counts=manifest['counts'],production_ready=False))
    except Exception as e:
        save(OUT/'training_failure.json',dict(type=type(e).__name__,message=str(e),elapsed_s=time.time()-start));raise
if __name__=='__main__':main()
