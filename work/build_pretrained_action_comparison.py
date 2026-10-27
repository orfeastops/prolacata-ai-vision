"""Build a private Kaggle notebook; no camera data leaves Kaggle for Hugging Face."""
import ast
import json
from pathlib import Path

root = Path('outputs/facility_dataset/temporal_pipeline/supervised_actions')
previous = Path('work/train_supervised_facility_actions.py').read_text(encoding='utf-8-sig')
decode = previous[previous.index('indexed={};arrays=[];decode_review=[]'):previous.index('mean=torch.tensor')]
decode = decode.replace('224', '256')
source = '''import os,json,pathlib,subprocess,random
os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
import numpy as np
import torch
from transformers import AutoModelForVideoClassification
from transformers.image_utils import IMAGENET_DEFAULT_MEAN,IMAGENET_DEFAULT_STD
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score,classification_report,confusion_matrix
import joblib
random.seed(42);np.random.seed(42);torch.manual_seed(42)
assert torch.cuda.is_available(),'Enable the free GPU accelerator.'
OUT=pathlib.Path('/kaggle/working/pretrained_action_comparison');OUT.mkdir(exist_ok=True)
TMP=pathlib.Path('/kaggle/temp/pretrained_action_comparison');TMP.mkdir(parents=True,exist_ok=True)
labels=['whole_block_transfer','separator_handling','other_or_idle'];class_ids={v:i for i,v in enumerate(labels)}
groups={s:{r['source_sha256'] for r in EXAMPLES if r['split']==s} for s in ('train','val','test')}
assert not(groups['train']&groups['val'] or groups['train']&groups['test'] or groups['val']&groups['test'])
assert all(r['date']=='2026-10-03' for r in EXAMPLES if r['split']=='test')
roots=list(pathlib.Path('/kaggle/input').rglob('bundle_manifest.json'))
assert len(roots)==1,'Attach the original private facility camera dataset.'
ROOT=roots[0].parent
(OUT/'examples.json').write_text(json.dumps(EXAMPLES,indent=2))
(OUT/'dataset_review.json').write_text(json.dumps(DATASET_REVIEW,indent=2))
print('REVIEWED CLIPS',len(EXAMPLES),DATASET_REVIEW['counts'],flush=True)
'''+decode+'''
MODEL_ID='facebook/vjepa2-vitl-fpc16-256-ssv2'
print('DOWNLOADING OFFICIAL MIT MODEL',MODEL_ID,flush=True)
model=AutoModelForVideoClassification.from_pretrained(MODEL_ID,torch_dtype=torch.float16,attn_implementation='sdpa').cuda().eval()
for p in model.parameters():p.requires_grad=False
mean=torch.tensor(IMAGENET_DEFAULT_MEAN).view(1,3,1,1)
std=torch.tensor(IMAGENET_DEFAULT_STD).view(1,3,1,1)
features=[]
with torch.inference_mode():
    for i,frames in enumerate(arrays):
        x=torch.from_numpy(frames).permute(0,3,1,2).float()/255
        x=((x-mean)/std).unsqueeze(0).to('cuda',dtype=torch.float16)
        z=model.vjepa2(pixel_values_videos=x,skip_predictor=True).last_hidden_state
        pooled=model.pooler(z)
        assert pooled.ndim==2 and pooled.shape[0]==1,pooled.shape
        features.append(pooled[0].float().cpu().numpy())
        if i%10==0:print('PRETRAINED FEATURES',i+1,'/',len(arrays),flush=True)
features=np.stack(features)
np.save(OUT/'features.npy',features)
y=np.array([class_ids[r['label']] for r in EXAMPLES])
ids={s:np.array([i for i,r in enumerate(EXAMPLES) if r['split']==s]) for s in groups}
trials=[];best=None
# Select regularization on validation only; keep the same held-out sources.
for c in [.001,.01,.1,1.,10.,100.]:
    classifier=make_pipeline(StandardScaler(),LogisticRegression(C=c,class_weight='balanced',max_iter=3000,random_state=42))
    classifier.fit(features[ids['train']],y[ids['train']])
    pred=classifier.predict(features[ids['val']])
    f=float(f1_score(y[ids['val']],pred,labels=[0,1,2],average='macro',zero_division=0))
    trials.append({'C':c,'validation_macro_f1':f})
    if best is None or f>best[0]:best=(f,c,classifier)
classifier=best[2]
testpred=classifier.predict(features[ids['test']])
testscore=float(f1_score(y[ids['test']],testpred,labels=[0,1,2],average='macro',zero_division=0))
report={'model_id':MODEL_ID,'license':'MIT','feature_extractor_frozen':True,'preprocessing':'same worker crops, aspect-preserving 256 square padding, 16 uniform frames, ImageNet default mean/std',
 'selection':'Regularization selected by validation macro F1 only; no refit on validation.',
 'validation_trials':trials,'selected_C':best[1],'validation_macro_f1':best[0],'test_macro_f1':testscore,
 'test_confusion_matrix_true_rows':confusion_matrix(y[ids['test']],testpred,labels=[0,1,2]).tolist(),
 'test_classification_report':classification_report(y[ids['test']],testpred,labels=[0,1,2],target_names=labels,zero_division=0,output_dict=True),
 'prior_scratch_videomae_pilot':{'run_version':361524639,'selected_validation_macro_f1':0.4296296296296296,'selected_test_macro_f1':0.4444444444444445},
 'limitations':['Only 76 assistant-reviewed clips; no independent expert verification.','Validation has one source; test 18 clips, including 5 whole-block transfers.','Trimmed action classification is not block-counting accuracy.','Quantity is never inferred from the gesture label or a standard tank capacity.','Continuous video detection, camera association and end-to-end tank counts remain unevaluated.'],
 'production_counter_ready':False}
(OUT/'comparison_results.json').write_text(json.dumps(report,indent=2))
joblib.dump(classifier,OUT/'facility_action_head.joblib')
predictions=[{'example_id':EXAMPLES[int(i)]['example_id'],'true_label':labels[int(y[i])],'predicted_label':labels[int(p)]} for i,p in zip(ids['test'],testpred)]
(OUT/'test_predictions.json').write_text(json.dumps(predictions,indent=2))
(OUT/'inference_contract.json').write_text(json.dumps({'purpose':'offline action candidate review only','model_id':MODEL_ID,'quantity_prediction':False,'automatic_tank_counts':False,'continuous_state':'External persistent tank and hand tracking required; windows never reset counts.'},indent=2))
print('COMPARISON COMPLETE',json.dumps(report),flush=True)
'''
ast.parse(source)
Path('work/compare_pretrained_facility_actions.py').write_text(source,encoding='utf-8')
embedded='EXAMPLES='+repr(json.loads((root/'examples.json').read_text()))+'\nDATASET_REVIEW='+repr(json.loads((root/'dataset_review.json').read_text()))+'\n'
cells=[{'cell_type':'markdown','metadata':{},'source':['# Pretrained video action comparison\n','Compare official MIT V-JEPA2 Something-Something-V2 features against the completed full-source scratch VideoMAE action pilot using identical reserved sources. Private camera data stays on Kaggle.\n','This is a small action-recognition pilot, not a validated quantity counter. No fixed blocks per gesture or tank.\n']},
 {'cell_type':'code','metadata':{},'source':["%pip -q install 'transformers>=5,<6' safetensors scikit-learn joblib\n"],'outputs':[],'execution_count':None},
 {'cell_type':'code','metadata':{},'source':(embedded+source).splitlines(True),'outputs':[],'execution_count':None}]
out=root/'facility_pretrained_action_comparison.ipynb'
out.write_text(json.dumps({'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.11'}},'nbformat':4,'nbformat_minor':5},indent=1),encoding='utf-8')
print(out.resolve(),out.stat().st_size)
