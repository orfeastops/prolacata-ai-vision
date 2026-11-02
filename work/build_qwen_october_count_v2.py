"""Create a reproducible standalone notebook for the currently running v2."""
import ast, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/facility_dataset/temporal_pipeline'
OUT=BASE/'pretrained_video_count_v2'
OUT.mkdir(exist_ok=True)
inputs=json.loads((BASE/'pretrained_video_count_v1/input_clips.json').read_text())
setup=(ROOT/'work/run_qwen_october_count_v1.py').read_text().split('    predictions = []')[0]
setup=setup.replace("OUT = Path('/kaggle/working/qwen_october_count_v1')", "OUT = Path('/kaggle/working/qwen_october_count_v2_setup')")
setup+='    return model, processor\n\nmodel, processor = main()\n'
run=(ROOT/'work/run_qwen_october_count_v2.py').read_text()
(OUT/'launched_runner.py').write_text(run,encoding='utf-8')
run=run.replace("Path('/kaggle/working/qwen_october_count_v1/frozen_config.json')", "Path('/kaggle/working/qwen_october_count_v2_setup/frozen_config.json')")
run+='\nrun(model, processor, INPUT_CLIPS)\n'
setup='INPUT_CLIPS = '+repr(inputs)+'\n'+setup
ast.parse(setup);ast.parse(run)
def code(s):return dict(cell_type='code',metadata={},execution_count=None,outputs=[],source=s.splitlines(True))
cells=[dict(cell_type='markdown',metadata={},source=['# Qwen3-VL compact October diagnostic\n',
    'Same official 8B FP16 weights, T4 x2, private existing October sources, no reference counts.\n',
    'Development revision: v1 produced a repetitive answer reaching its token limit. This variant uses 4 fps and compact events. It is not an independent acceptance test.\n']),
    code("%pip -q install 'transformers==4.57.6' 'accelerate>=1.10,<2' 'huggingface_hub>=0.34,<1' safetensors\n"),code(setup),code(run)]
nb=dict(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}},nbformat=4,nbformat_minor=5)
p=OUT/'facility_qwen3_vl_compact_october_test.ipynb'
p.write_text(json.dumps(nb,indent=1),encoding='utf-8')
(OUT/'run_plan.json').write_text(json.dumps(dict(model='Qwen/Qwen3-VL-8B-Instruct',
    clips=12,sampling_fps=4,reference_counts_uploaded=False,training=False,september_used=False,
    run_location='Existing interactive Kaggle session, background Python thread v2_thread',
    url='https://www.kaggle.com/code/orfeastops/facility-qwen3-vl-october-counting-test/edit',
    remote_output='/kaggle/working/qwen_october_count_v2',
    notebook_sha256=hashlib.sha256(p.read_bytes()).hexdigest()),indent=2),encoding='utf-8')
print(p)
