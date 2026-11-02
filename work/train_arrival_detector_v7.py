"""Fine-tune individual on-tray cheese/empty-position detection.

No per-image reference geometry is supplied at inference. Final checkpoint is
fixed in advance; source-disjoint arrival count scoring happens afterwards.
"""
import os
os.environ['YOLO_AUTOINSTALL']='false';os.environ['YOLO_OFFLINE']='true'
os.environ['OMP_NUM_THREADS']='4';os.environ['MPLBACKEND']='Agg'
import time,json,traceback
import torch,cv2
from ultralytics import YOLO
from ultralytics.models.yolo.detect import DetectionTrainer
from build_arrival_detector_v7 import ROOT,OUT,digest,save

CONFIG=dict(epochs=80,imgsz=384,batch=4,nbs=4,rect=True,workers=0,device='cpu',
    optimizer='AdamW',lr0=.001,lrf=.1,weight_decay=.0005,warmup_epochs=3,
    freeze=0,seed=291027,deterministic=True,patience=0,cos_lr=True,
    mosaic=0,mixup=0,copy_paste=0,fliplr=0,flipud=0,degrees=0,
    translate=.04,scale=.12,hsv_h=0,hsv_s=.1,hsv_v=.12,
    cache=False,amp=False,plots=False,save_period=40,val=True,verbose=False)

def main():
    if (OUT/'training_started.json').exists():raise RuntimeError('An arrival training run already exists')
    approval=json.loads((OUT/'annotation_review_approval.json').read_text())
    assert approval['manifest_sha256']==digest(OUT/'dataset_manifest.json')
    m=json.loads((OUT/'dataset_manifest.json').read_text())
    assert not {r['source_sha256'] for r in m['records'] if r['split']=='train'} & {r['source_sha256'] for r in m['records'] if r['split']=='val'}
    torch.set_num_threads(4);cv2.setNumThreads(2)
    weights=ROOT/'outputs/feta_training/yolo26n.pt'
    save(OUT/'training_config.json',dict(config=CONFIG,initial_weights_sha256=digest(weights),
        manifest_sha256=digest(OUT/'dataset_manifest.json'),training_code_sha256=digest(__file__),
        final_checkpoint='last.pt after 80 epochs, no count-based selection',
        no_fixed_count=True,september_used=False,training_source_files=1,validation_source_files=1))
    start=time.time();save(OUT/'training_started.json',dict(pid=os.getpid(),started_unix=start))
    class Trainer(DetectionTrainer):
        def optimizer_step(self):
            super().optimizer_step();self.real_updates=getattr(self,'real_updates',0)+1
    model=YOLO(str(weights))
    def epoch_end(t):
        save(OUT/'training_progress.json',dict(status='training',completed_epochs=t.epoch+1,total_epochs=CONFIG['epochs'],
            elapsed_s=time.time()-start,optimizer_updates=getattr(t,'real_updates',0),
            metrics={k:float(v) for k,v in t.metrics.items()}))
    model.add_callback('on_fit_epoch_end',epoch_end)
    try:
        model.train(trainer=Trainer,data=str(OUT/'dataset/data.yaml'),project=str(OUT),name='detector_run',exist_ok=False,**CONFIG)
        checkpoint=OUT/'detector_run/weights/last.pt';assert checkpoint.exists()
        save(OUT/'training_complete.json',dict(status='complete',epochs=80,elapsed_s=time.time()-start,
            checkpoint=str(checkpoint),checkpoint_sha256=digest(checkpoint),
            optimizer_updates=getattr(model.trainer,'real_updates',0),
            training_images=sum(r['split']=='train' for r in m['records']),validation_images=sum(r['split']=='val' for r in m['records']),
            manifest_sha256=digest(OUT/'dataset_manifest.json'),september_used=False,production_ready=False))
    except Exception as e:
        save(OUT/'training_failure.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()));raise
if __name__=='__main__':main()
