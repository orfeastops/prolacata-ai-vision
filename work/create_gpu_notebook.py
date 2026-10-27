import pathlib,json
ROOT=pathlib.Path('outputs/facility_dataset')
cells=[]
def md(s):cells.append(dict(cell_type='markdown',metadata={},source=s.splitlines(True)))
def code(s):cells.append(dict(cell_type='code',metadata={},source=s.splitlines(True),outputs=[],execution_count=None))
md('''# Facility vision: complete-source GPU workflow

This notebook uses the private bundle prepared from every unique supplied source.
It does not claim that unlabelled footage is already training ground truth.

Stages: locate bundle → verify GPU → propose object annotations over the full frame pool → review proposals → train and compare detectors on approved labels.
Full videos remain in `media/` for continuous hand-action and transfer annotations.
Sampled frames alone cannot measure block placements or daily production.
''')
code('''%pip -q install transformers safetensors ultralytics
import os, json, pathlib, zipfile, time, inspect
os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
os.environ['TOKENIZERS_PARALLELISM']='false'
os.environ['YOLO_CONFIG_DIR']='/kaggle/working/yolo_config'
import torch
assert torch.cuda.is_available(), 'Enable a GPU accelerator before running the bulk model.'
print(torch.cuda.get_device_name(0))
''')
code('''# Prefer an extracted private Kaggle dataset. If only the ZIP is mounted, extract locally.
matches=list(pathlib.Path('/kaggle/input').rglob('bundle_manifest.json'))
if not matches:
    archives=list(pathlib.Path('/kaggle/input').rglob('facility_gpu_bundle.zip'))
    assert len(archives)==1, 'Attach the prepared private facility dataset.'
    target=pathlib.Path('/kaggle/working/facility_data');target.mkdir(exist_ok=True)
    with zipfile.ZipFile(archives[0]) as z:
        for member in z.infolist():
            resolved=(target/member.filename).resolve()
            assert resolved.is_relative_to(target.resolve()), 'Unsafe archive path'
        z.extractall(target)
    matches=list(target.rglob('bundle_manifest.json'))
assert len(matches)==1, 'Select exactly one dataset bundle.'
ROOT=matches[0].parent
frames=json.loads((ROOT/'frame_manifest.json').read_text())
media=json.loads((ROOT/'media_manifest_portable.json').read_text())
print('Frame pool:',len(frames),'full media sources:',len(media))
assert all((ROOT/r['image']).exists() for r in frames)
''')
md('''## Annotation proposals — not ground truth
Grounding DINO is used as a teacher to reduce manual boxing work. Its predictions must be reviewed, especially blocks touching each other, blue bin liners mistaken for gloves, empty/full bin state, and loaded pallets. No standard total of 228 is inserted.
The output is resumable JSON. It must not be relabelled as verified simply because it has a high score.
''')
code('''from transformers import AutoProcessor,AutoModelForZeroShotObjectDetection
from PIL import Image
MODEL='IDEA-Research/grounding-dino-tiny'
processor=AutoProcessor.from_pretrained(MODEL)
teacher=AutoModelForZeroShotObjectDetection.from_pretrained(MODEL).to('cuda').eval()
OUT=pathlib.Path('/kaggle/working/annotation_proposals');OUT.mkdir(exist_ok=True)
prompts={11:'a gloved hand. a white cheese block. a plastic storage bin. a separator tray.',
         15:'a plastic storage bin. a pallet. a forklift. a pallet truck.'}
post_args=inspect.signature(processor.post_process_grounded_object_detection).parameters
for i,r in enumerate(frames):
    name=r['source_sha256'][:16]+'_'+pathlib.Path(r['image']).stem+'.json'
    dest=OUT/name
    if dest.exists():continue
    # Preserve the full room and use a separate crop on camera 11 for the small hand/block task.
    variants=[('full',r['image'])]
    if r.get('camera11_crop'):variants.append(('filling_crop',r['camera11_crop']))
    proposals=[]
    for view,relative_path in variants:
        image=Image.open(ROOT/relative_path).convert('RGB')
        inputs=processor(images=image,text=prompts[r['camera']],return_tensors='pt').to('cuda')
        with torch.inference_mode():outputs=teacher(**inputs)
        kwargs={'text_threshold':0.20,'target_sizes':[image.size[::-1]]}
        kwargs['threshold' if 'threshold' in post_args else 'box_threshold']=0.25
        pred=processor.post_process_grounded_object_detection(outputs,inputs.input_ids,**kwargs)[0]
        labels=pred.get('text_labels',pred.get('labels',[]))
        proposals.append({'view':view,'image':relative_path,
                          'boxes':pred['boxes'].detach().cpu().tolist(),
                          'scores':pred['scores'].detach().cpu().tolist(),
                          'labels':[str(x) for x in labels]})
    dest.write_text(json.dumps({'frame':r,'teacher':MODEL,'annotation_status':'unverified_model_proposals','proposals':proposals},indent=2))
    if i%100==0:print(i,'/',len(frames))
print('Proposal files:',len(list(OUT.glob('*.json'))))
''')
md('''## Supervised model comparison after annotation review

Supply `approved_dataset.yaml` and `annotation_review.json` after checking the proposed boxes and adding missed objects. Keep complete event groups out of training; do not randomly mix neighbouring frames across train/validation/test. Empty/full/crumb bin state needs explicit labels. Continuous event intervals need source video, start/end, worker/hand, destination and tank ID.

The following cell deliberately refuses to train on unreviewed proposals. This is a data-quality check, not a request to manually label every frame: proposals can be corrected in batches and propagated through video, but their quality must be measured.
''')
code('''review_path=pathlib.Path('/kaggle/working/approved_annotations/annotation_review.json')
dataset_yaml=pathlib.Path('/kaggle/working/approved_annotations/approved_dataset.yaml')
assert review_path.exists() and dataset_yaml.exists(), 'Finish annotation review before supervised training.'
review=json.loads(review_path.read_text())
assert review.get('approved_for_supervised_training') is True
assert review.get('event_groups_disjoint') is True
assert review.get('independent_test_labels_present') is True
from ultralytics import YOLO,RTDETR,settings
settings.update({k:False for k in ('sync','wandb','mlflow','clearml','comet','neptune','tensorboard') if k in settings})
reports={}
# Candidate architectures, not a declaration that either is best for this facility.
for name,model in [('yolo26s',YOLO('yolo26s.pt')),('rtdetr_l',RTDETR('rtdetr-l.pt'))]:
    model.train(data=str(dataset_yaml),epochs=100,imgsz=960,batch=4,device=0,workers=2,
                project='/kaggle/working/benchmark_runs',name=name,seed=42,patience=20)
    val=model.val(data=str(dataset_yaml),split='val',imgsz=960,device=0)
    reports[name]=val.results_dict
pathlib.Path('/kaggle/working/detector_comparison.json').write_text(json.dumps(reports,indent=2))
''')
md('''## Facility acceptance criteria

Detector mAP alone does not establish production accuracy. Evaluate complete unseen cycles:

- actual blocks placed per tank, including simultaneous hands and crumb-only actions;
- filled tanks leaving camera 11 and arriving for weighing in camera 15;
- crumb tank replacements, distinguished from individual crumb disposals;
- loaded pallets crossing the exit on 22 October, distinguished from repositioning;
- missed events, duplicate events, timestamps, recording gaps and uncertain associations.

Select the complete detection + tracking + temporal-action pipeline using these measurements. No facility-wide accuracy or zero-error guarantee follows from this notebook alone.
''')
notebook=dict(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.12'}},nbformat=4,nbformat_minor=5)
(ROOT/'facility_gpu_workflow.ipynb').write_text(json.dumps(notebook,indent=2),encoding='utf-8')
print('Created complete-source GPU notebook; not uploaded or run remotely.')
