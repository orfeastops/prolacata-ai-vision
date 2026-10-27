"""Small localization diagnostic; boxes represent groups, never production counts."""
import os, json, shutil, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'outputs/facility_dataset/temporal_pipeline/placement_counter_v2'
REVIEW = BASE/'object_review'
OUT = BASE/'carried_group_bootstrap'
os.environ['YOLO_CONFIG_DIR'] = str(ROOT/'outputs/feta_training/runtime_config')
os.environ['YOLO_AUTOINSTALL'] = 'false'
os.environ['MPLBACKEND'] = 'Agg'
os.environ['MPLCONFIGDIR'] = str(ROOT/'outputs/feta_training/matplotlib_config')
SELECTED = set('N21_05_03.75 N21_05_07.50 N21_02_05.00 N21_02_08.00 B004_19.625 B006_10.000 B006_11.750 B020_10.750 B020_14.250 B021_10.750 B022_20.500'.split())

def save(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding='utf-8')

def main():
    import torch
    from PIL import Image
    from ultralytics import YOLO
    torch.set_num_threads(4)
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT/'summary.json').exists():
        raise RuntimeError('Completed experiment exists; refusing to retrain silently')
    annotations = json.loads((REVIEW/'object_dataset_manifest.json').read_text(encoding='utf-8-sig'))['object_regions']
    frames = {}
    for a in annotations:
        if Path(a['image_path']).stem not in SELECTED:
            continue
        row = frames.setdefault(a['image_path'], dict(image_path=a['image_path'], clip_id=a['clip_id'], source_sha256=a['source_sha256'], boxes=[], review='assistant full-frame visual coverage audit; carried groups only'))
        row['boxes'].append(a['bbox_xyxy'])
    assert len(frames) == len(SELECTED)
    for a in json.loads((REVIEW/'reviewed_hard_negatives.json').read_text(encoding='utf-8-sig')):
        assert a['image_review_complete']
        frames[a['image_path']] = dict(image_path=a['image_path'],clip_id=a['clip_id'],source_sha256=a['source_sha256'],boxes=[],review=a['reviewer'])
    held = {r['source_sha256'] for r in frames.values() if r['clip_id'] in {'B006','N01_04'}}
    for row in frames.values():
        row['split'] = 'val' if row['source_sha256'] in held else 'train'
        src = Path(row['image_path'])
        w,h = Image.open(src).size
        assert (w,h) == (640,360)
        dest = OUT/'dataset/images'/row['split']/src.name
        labels = OUT/'dataset/labels'/row['split']/(src.stem+'.txt')
        dest.parent.mkdir(parents=True,exist_ok=True)
        labels.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,dest)
        lines=[]
        for x1,y1,x2,y2 in row['boxes']:
            assert 0 <= x1 < x2 <= w and 0 <= y1 < y2 <= h
            lines.append(f'0 {(x1+x2)/2/w:.8f} {(y1+y2)/2/h:.8f} {(x2-x1)/w:.8f} {(y2-y1)/h:.8f}')
        labels.write_text('\n'.join(lines),encoding='utf-8')
    train_sources={r['source_sha256'] for r in frames.values() if r['split']=='train'}
    assert not train_sources & held
    manifest=dict(frames=list(frames.values()),class_name='carried_feta_group', quantity_target=None, production_ready=False, excluded_positive_frames=sorted({Path(a['image_path']).stem for a in annotations}-SELECTED),split_policy='Hold out original sources B006 and N01_04; fixed before training; September26 absent')
    save(OUT/'dataset_manifest.json',manifest)
    yaml=OUT/'dataset.yaml'
    yaml.write_text(f'path: {str(OUT / "dataset").replace(chr(92), "/")}\ntrain: images/train\nval: images/val\nnames:\n  0: carried_feta_group\n',encoding='utf-8')
    config=dict(epochs=20,imgsz=640,batch=4,device='cpu',workers=0,freeze=11,optimizer='AdamW',lr0=.0007,patience=0,seed=43,deterministic=True,mosaic=0.0,mixup=0.0,fliplr=0.0,flipud=0.0,degrees=0.0,translate=.05,scale=.1,cache=False,plots=False)
    save(OUT/'config.json',dict(**config,checkpoint_policy='last epoch, no model selection',evaluation_confidence=.25))
    start=time.time()
    model=YOLO(str(ROOT/'outputs/feta_training/yolo26n.pt'))
    def progress(trainer):
        save(OUT/'progress.json',dict(status='training',epoch=trainer.epoch+1,epochs=20,elapsed_seconds=round(time.time()-start)))
    model.add_callback('on_fit_epoch_end',progress)
    model.train(data=str(yaml),project=str(OUT),name='run',exist_ok=True,**config)
    trained=YOLO(str(OUT/'run/weights/last.pt'))
    results=[]
    for row in frames.values():
        if row['split']!='val': continue
        pred=trained.predict(row['image_path'],conf=.25,imgsz=640,device='cpu',verbose=False)[0]
        target=OUT/'validation_previews'/Path(row['image_path']).name
        target.parent.mkdir(exist_ok=True)
        pred.save(filename=str(target))
        boxes=pred.boxes.xyxy.cpu().tolist()
        matched=set(); tp=0
        for box in boxes:
            scores=[]
            for i,gt in enumerate(row['boxes']):
                ix=max(0,min(box[2],gt[2])-max(box[0],gt[0])); iy=max(0,min(box[3],gt[3])-max(box[1],gt[1]))
                inter=ix*iy; union=(box[2]-box[0])*(box[3]-box[1])+(gt[2]-gt[0])*(gt[3]-gt[1])-inter
                scores.append((inter/union if union else 0,i))
            candidates=[(v,i) for v,i in scores if i not in matched and v>=.5]
            if candidates:
                _,i=max(candidates); matched.add(i); tp+=1
        results.append(dict(image=Path(row['image_path']).name,ground_truth_groups=len(row['boxes']),predicted_groups=len(boxes),true_positives=tp,false_positives=len(boxes)-tp,missed_groups=len(row['boxes'])-tp,boxes=boxes,confidence=pred.boxes.conf.cpu().tolist()))
    summary=dict(status='complete',elapsed_seconds=round(time.time()-start),training_images=sum(r['split']=='train' for r in frames.values()),validation_images=len(results),training_sources=len(train_sources),validation_sources=len(held),evaluation=results,production_ready=False,block_counting_available=False,limitation='Tiny assistant-annotated localization bootstrap. Group boxes are not quantities or verified releases. Validation is diagnostic, not a production accuracy estimate.')
    save(OUT/'summary.json',summary)
    save(OUT/'progress.json',dict(status='complete',epochs=20,elapsed_seconds=summary['elapsed_seconds']))
    print(json.dumps(summary,ensure_ascii=False),flush=True)

if __name__=='__main__':
    main()
