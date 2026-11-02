"""Build a label-free Kaggle inference notebook; references remain local."""
import ast, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'outputs/facility_dataset/temporal_pipeline'
OUT = BASE/'pretrained_video_count_v1'
OUT.mkdir(exist_ok=True)
rows = json.loads((BASE/'placement_counter_v4/event_quantity_diagnostic/dataset.json').read_text())['rows']
segments = {r['segment_id']:r for r in json.loads((BASE/'placement_counter_v3/interval_supervision.json').read_text())['segments']}
inputs=[]
references=[]
for row in rows:
    if row['role'] != 'historical_source_check':
        continue
    segment=segments[row['id']]
    ids=row['source_frame_indices']
    assert ids == list(range(ids[0],ids[-1]+1))
    source_files=list((ROOT/'work/facility_media').glob(row['source_sha256'][:16]+'*'))
    assert len(source_files)==1,(row['id'],source_files)
    ident=f'V{len(inputs)+1:02d}'
    inputs.append(dict(id=ident,source_sha256=row['source_sha256'],source_basename=source_files[0].name,
        date=segment['date'],first_source_frame=ids[0],last_source_frame=ids[-1],
        native_relative_pts_s=row['timestamps'],clip_duration_s=row['original_end_s']))
    references.append(dict(id=ident,original_segment_id=row['id'],reference_count=row['reference_count'],
        provenance='Prior user-confirmed complete-clip totals; event times partly assistant-reviewed.',
        source_sha256=row['source_sha256']))
assert len(inputs)==12
(OUT/'input_clips.json').write_text(json.dumps(inputs,indent=2),encoding='utf-8')
(OUT/'local_reference_counts_DO_NOT_UPLOAD.json').write_text(json.dumps(references,indent=2),encoding='utf-8')
code=(ROOT/'work/run_qwen_october_count_v1.py').read_text(encoding='utf-8')
ast.parse(code)
embedded='INPUT_CLIPS = '+repr(inputs)+'\n'+code
ast.parse(embedded)
cells=[dict(cell_type='markdown',metadata={},source=['# Facility Qwen3-VL October counting test\n',
    'Frozen official Qwen3-VL-8B-Instruct, inference only. Twelve October clips, all native frames, no facility fine-tuning.\n',
    'Reference quantities are kept locally and are absent from this notebook and model messages. September 26 is excluded.\n',
    'Attach the existing private Facility Production Camera 11 and 15 October 2026 dataset. GPU T4 x2; Internet on for official model download.\n',
    'Raw answers, parsed events, uncertainty, frame coverage, model revision and errors are saved. No automatic retry with changed prompts.\n']),
    dict(cell_type='code',metadata={},execution_count=None,outputs=[],source=["%pip -q install 'transformers==4.57.6' 'accelerate>=1.10,<2' 'huggingface_hub>=0.34,<1' safetensors\n"]),
    dict(cell_type='code',metadata={},execution_count=None,outputs=[],source=embedded.splitlines(True))]
nb=dict(cells=cells,metadata=dict(kernelspec=dict(display_name='Python 3',language='python',name='python3'),
    language_info=dict(name='python',version='3.11')),nbformat=4,nbformat_minor=5)
path=OUT/'facility_qwen3_vl_october_counting_test.ipynb'
path.write_text(json.dumps(nb,indent=1),encoding='utf-8')
(OUT/'local_run_plan.json').write_text(json.dumps(dict(model_id='Qwen/Qwen3-VL-8B-Instruct',
    clips=12,positive_clips=sum(r['reference_count']>0 for r in references),negative_clips=sum(r['reference_count']==0 for r in references),
    reference_blocks=sum(r['reference_count'] for r in references),native_frames=sum(len(c['native_relative_pts_s']) for c in inputs),
    notebook_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),notebook=str(path),
    reference_counts_uploaded=False,september_used=False,training=False),indent=2),encoding='utf-8')
print(path)
print((OUT/'local_run_plan.json').read_text())
