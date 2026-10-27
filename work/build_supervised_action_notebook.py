import pathlib,json,ast
R=pathlib.Path('outputs/facility_dataset/temporal_pipeline/supervised_actions')
examples=json.loads((R/'examples.json').read_text());review=json.loads((R/'dataset_review.json').read_text())
source=pathlib.Path('work/train_supervised_facility_actions.py').read_text(encoding='utf-8-sig');ast.parse(source)
embedded='import json\nEXAMPLES=json.loads('+repr(json.dumps(examples))+')\nDATASET_REVIEW=json.loads('+repr(json.dumps(review))+')\n'
cells=[{'cell_type':'markdown','metadata':{},'source':[
 '# Reviewed facility hand-action pilot\n',
 'Uses the completed full-source VideoMAE checkpoint and manually reviewed temporal events. Compare a frozen-feature head with supervised fine-tuning of the final two encoder layers.\n',
 'Attach both the original private camera dataset and output of facility-temporal-video-pretraining-full-sources version 361412417.\n',
 'All October 3 sources stay in the held-out test. B019 is reserved for supervised validation. Labels are assistant annotations, not independently expert verified.\n',
 'This is an action-proposal pilot. It does not predict block quantities, assume two blocks per gesture, impose a tank total, or produce daily production counts.\n']},
 {'cell_type':'code','metadata':{},'source':["%pip -q install 'transformers>=4.44,<5' safetensors scikit-learn\n"],'outputs':[],'execution_count':None},
 {'cell_type':'code','metadata':{},'source':(embedded+source).splitlines(True),'outputs':[],'execution_count':None}]
out=R/'facility_reviewed_action_training.ipynb'
out.write_text(json.dumps({'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.11'}},'nbformat':4,'nbformat_minor':5},indent=1),encoding='utf-8')
print(out.resolve(),out.stat().st_size)
