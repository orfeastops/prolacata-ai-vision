import pathlib,json,ast
source=pathlib.Path('work/facility_video_pretraining.py').read_text(encoding='utf-8-sig')
ast.parse(source)
cells=[{'cell_type':'markdown','metadata':{},'source':[
'# Facility video learning from complete supplied sources\n',
'Private experimental masked-video pretraining. This trains representations from unlabelled footage and photographs; it does not yet train cheese/tank/pallet counts.\n',
'All October 3 sources remain excluded. Every other supplied unique source is required to decode successfully; no silent omission is allowed.\n',
'Architecture: VideoMAE base, initialized from scratch, using the Apache-2.0 Transformers implementation. No external model weights. This is a candidate to evaluate, not a claim of best performance.\n',
'Training is capped at 10 epochs or six training hours. Weights, optimizer state, loss logs, coverage and exclusions are exported. Camera clocks are not yet verified.\n']},
{'cell_type':'code','metadata':{},'source':["%pip -q install 'transformers>=4.44,<5' safetensors\n"],'outputs':[],'execution_count':None},
{'cell_type':'code','metadata':{},'source':source.splitlines(True),'outputs':[],'execution_count':None}]
out=pathlib.Path('outputs/facility_dataset/facility_video_learning.ipynb')
out.write_text(json.dumps({'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.11'}},'nbformat':4,'nbformat_minor':5},indent=1),encoding='utf-8')
print(out.resolve(),out.stat().st_size)
