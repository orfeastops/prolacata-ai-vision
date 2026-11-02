import json,hashlib,zipfile
from pathlib import Path
root=Path.cwd(); base=root/'outputs/tank_transfer_training_v1/dataset_v2/pilot_v2_local'; out=base/'kaggle'; out.mkdir(exist_ok=True)
m=json.loads((base/'detector_manifest.json').read_text()); assert len(m)==334
records=[]
with zipfile.ZipFile(out/'tank-pilot-v2.zip','w',zipfile.ZIP_DEFLATED) as z:
 for r in m:
  assert r['date'] not in ['20261028']
  assert (r['split']=='val')==(r['date']=='20261017')
  for field,h in [('image','image_sha256'),('label','label_sha256')]:
   p=base/r[field]; assert hashlib.sha256(p.read_bytes()).hexdigest()==r[h]; z.write(p,r[field].replace('\\','/'))
  records.append({k:r[k] for k in ['id','date','camera','split','image','label','image_sha256','label_sha256']})
 z.writestr('manifest.json',json.dumps(records,indent=2))
 z.write(root/'outputs/feta_training/yolo26n.pt','yolo26n.pt')
code='''from pathlib import Path
import json, hashlib, shutil, torch
from ultralytics import YOLO
assert torch.cuda.is_available(), 'Enable a GPU accelerator in Kaggle settings'
manifests=list(Path('/kaggle/input').rglob('manifest.json'))
roots=[p.parent for p in manifests if (p.parent/'yolo26n.pt').exists()]
assert len(roots)==1, roots
src=roots[0]; dst=Path('/kaggle/working/tank_dataset'); dst.mkdir(exist_ok=True)
rows=json.loads((src/'manifest.json').read_text())
assert len(rows)==334
for r in rows:
    assert r['date'] not in ['20261028']
    assert (r['split']=='val')==(r['date']=='20261017')
    for key in ['image','label']:
        rel=r[key].replace(chr(92),'/'); p=src/rel
        assert hashlib.sha256(p.read_bytes()).hexdigest()==r[key+'_sha256']
        target=dst/rel; target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,target)
(dst/'data.yaml').write_text(f'path: {dst}\\ntrain: images/train\\nval: images/val\\nnames:\\n  0: tank\\n')
model=YOLO(str(src/'yolo26n.pt'))
model.train(data=str(dst/'data.yaml'), epochs=60, patience=15, imgsz=640, batch=16, device=0, workers=2, seed=42, deterministic=True, optimizer='AdamW', lr0=0.001, mosaic=0, mixup=0, fliplr=0, flipud=0, degrees=0, translate=0.04, scale=0.12, project='/kaggle/working/tank_training', name='pilot_v2', exist_ok=False, plots=True)
best=YOLO('/kaggle/working/tank_training/pilot_v2/weights/best.pt')
metrics=best.val(data=str(dst/'data.yaml'),split='val',device=0,plots=True)
Path('/kaggle/working/validation_metrics.json').write_text(json.dumps(metrics.results_dict,indent=2))
# Validation only: these are not independent test or production-counting results.
'''
cells=[{'cell_type':'markdown','metadata':{},'source':['# Tank detector pilot v2\nPrivate training: 300 train images, 34 validation images (17 October). No locked test data. Single-class tank detection; mixed crops and full frames. Does not classify cheese/fullness or validate daily counting.']},{'cell_type':'code','metadata':{},'execution_count':None,'outputs':[],'source':['%pip install -q ultralytics==8.4.184']},{'cell_type':'code','metadata':{},'execution_count':None,'outputs':[],'source':code.splitlines(True)}]
nb={'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}},'nbformat':4,'nbformat_minor':5}
(out/'tank-pilot-v2-training.ipynb').write_text(json.dumps(nb,indent=2)); compile(code,'notebook','exec')
print(json.dumps({'images':len(m),'zip_bytes':(out/'tank-pilot-v2.zip').stat().st_size,'directory':str(out)}))
