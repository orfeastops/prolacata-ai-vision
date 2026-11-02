"""Kaggle inference only. INPUT_CLIPS is embedded without reference counts.

Official Qwen3-VL-8B-Instruct, one fixed zero-shot prompt, native frames.
No labels, optimizer, detector predictions, September video, or count targets.
"""
import os
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
import gc, json, time, hashlib, traceback, zipfile
from pathlib import Path
import cv2
import numpy as np
import torch
from torch.nn.attention import sdpa_kernel, SDPBackend
import transformers.integrations.sdpa_attention as hf_sdpa
from huggingface_hub import model_info
from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

MODEL_ID = 'Qwen/Qwen3-VL-8B-Instruct'
OUT = Path('/kaggle/working/qwen_october_count_v1')
if (OUT / 'failure.json').exists() and not (OUT / 'complete.json').exists():
    # Preserve failed runtime attempts instead of mixing stale failures/results.
    OUT.rename(OUT.with_name(OUT.name + '_failed_' + str(time.time_ns())))
OUT.mkdir(exist_ok=True)
TEMP = Path('/kaggle/temp/qwen_october_count_v1')
TEMP.mkdir(parents=True, exist_ok=True)
PROMPT = '''Examine this overhead factory video carefully in temporal order.
The scene contains white rectangular cheese blocks on trays on a conveyor,
blue-gloved hands, a production filling tank beside the workers, and a separate
crumb/waste tank. Count NEW whole cheese blocks actually released into the
production filling tank during the clip. Observe both workers, including
simultaneous transfers. Do not count a hand movement without a lifted block,
rearranging cheese already inside the tank, salt sprinkling, separator sheets,
empty trays, gestures, crumbs, or cheese sent to the crumb/waste tank.
Determine each quantity from the visible objects. Do not assume any fixed
number per hand, transfer, tray, layer, or tank. A load may contain one, two,
three, or another visually supported quantity. Do not count the same block
twice. If a load is released in parts, record the separate releases with their
respective quantities. If a block is still being carried at clip end, do not
count it as deposited. A pickup can be outside the clip if the carried quantity
and release are visible; report pickup_s as null in that case.
Provide elapsed times in seconds relative to the video you are shown. The
production tank is the tank receiving neatly arranged rectangular blocks;
identify it visually rather than using a fixed screen coordinate.
Return ONLY one JSON object with keys events, uncertain_events, exclusions.
events is a list of {pickup_s:number|null, release_s:number,
quantity:integer, destination:"production_tank", side:"left"|"right",
visual_evidence:string}. Include only visually supported completed releases.
uncertain_events is a list of {time_s:number, possible_quantity:integer|null,
reason:string}. exclusions is a list of {time_s:number,
type:"crumbs"|"salt"|"empty_hands"|"tray"|"rearrangement"|"sheet"|"other",
reason:string}. An empty event list is a valid answer. Do not invent events
or fill in quantities from expectations. Keep each evidence sentence brief.'''


def save(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2), encoding='utf-8')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def parse_answer(raw, duration):
    text = raw.strip()
    if text.startswith('```'):
        text = text.split('\n', 1)[1].rsplit('```', 1)[0].strip()
    data = json.loads(text)
    if not isinstance(data, dict) or not isinstance(data.get('events'), list):
        raise ValueError('Missing JSON events list')
    for e in data['events']:
        q = e.get('quantity')
        t = e.get('release_s')
        if isinstance(q, bool) or not isinstance(q, int) or q < 1:
            raise ValueError('Invalid event quantity')
        if not isinstance(t, (float, int)) or not 0 <= t <= duration + 0.15:
            raise ValueError('Release timestamp outside clip')
        if e.get('destination') != 'production_tank':
            raise ValueError('Wrong destination in counted event')
        if e.get('side') not in ('left', 'right'):
            raise ValueError('Invalid image-side bookkeeping label')
    for key in ('uncertain_events', 'exclusions'):
        if not isinstance(data.get(key), list):
            raise ValueError('Missing ' + key)
    return data


def main():
    if (OUT / 'complete.json').exists():
        raise RuntimeError('Completed prediction exists; refuse an implicit rerun.')
    assert torch.cuda.is_available(), 'Enable a Kaggle GPU.'
    assert torch.cuda.device_count() >= 2, 'Select GPU T4 x2 for this fixed FP16 experiment.'
    torch.set_num_threads(4)
    cv2.setNumThreads(2)
    torch.manual_seed(2910)
    np.random.seed(2910)
    # On T4, native SDPA GQA falls back to a dense math attention matrix.
    # Use the library's equivalent explicit KV expansion and efficient kernel.
    hf_sdpa.use_gqa_in_sdpa = lambda attention_mask, key: False
    q = torch.randn(1, 4, 16, 64, device='cuda:0', dtype=torch.float16)
    k = torch.randn(1, 2, 16, 64, device='cuda:0', dtype=torch.float16)
    v = torch.randn_like(k)
    with sdpa_kernel(SDPBackend.MATH):
        expected = torch.nn.functional.scaled_dot_product_attention(q, k, v, is_causal=True, enable_gqa=True)
    with sdpa_kernel(SDPBackend.EFFICIENT_ATTENTION):
        actual = torch.nn.functional.scaled_dot_product_attention(q,
            k.repeat_interleave(2, dim=1), v.repeat_interleave(2, dim=1), is_causal=True)
    max_attention_error = float((actual-expected).abs().max())
    torch.testing.assert_close(actual, expected, atol=0.01, rtol=0.01)
    del q, k, v, expected, actual
    torch.cuda.empty_cache()
    assert all(c['date'] in ('2026-10-01', '2026-10-21') for c in INPUT_CLIPS)
    assert len(INPUT_CLIPS) == 12
    assert all(not any(k in c for k in ('reference_count', 'confirmed_count', 'events', 'position_totals')) for c in INPUT_CLIPS)
    config = dict(model_id=MODEL_ID, dtype='float16', quantization=None,
        attention='sdpa efficient kernel, explicit KV expansion for T4; unchanged attention semantics',
        attention_preflight_max_absolute_error=max_attention_error,
        sampling='all consecutive native decoded frames, no frame subsampling',
        crop=[800,720,1440,1080], processor_spatial_resize=False,
        spatial_padding='bottom edge replicated from 360 to 384 pixels, no image rescaling',
        decoding=dict(do_sample=False, max_new_tokens=3072),
        prompt_sha256=hashlib.sha256(PROMPT.encode()).hexdigest(),
        reference_counts_available_to_model=False, training=False,
        september_used=False, test_kind='historically reviewed October development benchmark',
        event_timing='model video timestamps use measured mean native fps; original per-frame PTS retained for audit',
        gpu_names=[torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())])
    save('input_clips.json', INPUT_CLIPS)
    (OUT / 'prompt.txt').write_text(PROMPT, encoding='utf-8')
    save('progress.json', dict(stage='locating_existing_private_camera_sources', complete_clips=0, total_clips=12))
    files = [p for p in Path('/kaggle/input').rglob('*') if p.is_file() and p.suffix.lower() in ('.mp4','.avi','.dav','.mkv')]
    source_paths = {}
    source_hash_checks = []
    for clip in INPUT_CLIPS:
        digest = clip['source_sha256']
        if digest in source_paths:
            continue
        candidates = [p for p in files if p.name.startswith(digest[:16]) or p.name == clip['source_basename']]
        if len(candidates) != 1:
            raise FileNotFoundError(f"Expected one source for {clip['id']} {digest[:16]}, found {len(candidates)}")
        path = candidates[0]
        actual = sha(path)
        if actual != digest:
            raise ValueError(f'Source hash mismatch for {clip["id"]}')
        source_paths[digest] = path
        source_hash_checks.append(dict(source_sha256=digest, path=str(path)))
    save('source_verification.json', source_hash_checks)
    save('progress.json', dict(stage='decoding_native_clips', complete_clips=0, total_clips=12))
    for digest, source in source_paths.items():
        clips = [c for c in INPUT_CLIPS if c['source_sha256'] == digest]
        buffers = {c['id']:[] for c in clips}
        cap = cv2.VideoCapture(str(source))
        if not cap.isOpened():
            raise RuntimeError('Cannot decode ' + str(source))
        i = 0
        stop = max(c['last_source_frame'] for c in clips)
        while i <= stop:
            ok, frame = cap.read()
            if not ok:
                break
            for c in clips:
                if c['first_source_frame'] <= i <= c['last_source_frame']:
                    crop = frame[720:1080,800:1440]
                    if crop.shape != (360,640,3):
                        raise ValueError('Unexpected source resolution')
                    buffers[c['id']].append(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
            i += 1
        cap.release()
        for c in clips:
            frames = np.asarray(buffers[c['id']], dtype=np.uint8)
            if len(frames) != len(c['native_relative_pts_s']):
                raise ValueError('Native frame count mismatch for ' + c['id'])
            np.save(TEMP / (c['id'] + '.npy'), frames)
        del buffers
    config['model_revision'] = model_info(MODEL_ID).sha
    save('frozen_config.json', config)
    save('progress.json', dict(stage='loading_official_model', model_revision=config['model_revision'], complete_clips=0, total_clips=12))
    print('LOADING', MODEL_ID, config['model_revision'], flush=True)
    processor = AutoProcessor.from_pretrained(MODEL_ID, revision=config['model_revision'])
    model = Qwen3VLForConditionalGeneration.from_pretrained(MODEL_ID, revision=config['model_revision'],
        torch_dtype=torch.float16, device_map='balanced', max_memory={0:'12GiB',1:'12GiB'},
        attn_implementation='sdpa', low_cpu_mem_usage=True).eval()
    if any(str(v) in ('cpu','disk') for v in model.hf_device_map.values()):
        raise RuntimeError('Model was offloaded outside GPUs; refusing an unexpectedly slow run.')
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    save('device_map.json', {k:str(v) for k,v in model.hf_device_map.items()})
    predictions = []
    for clip in INPUT_CLIPS:
        begin = time.time()
        ident = clip['id']
        save('progress.json', dict(stage='inference', current_clip=ident, complete_clips=len(predictions), total_clips=12))
        frames = np.load(TEMP / (ident + '.npy'))
        pts = np.asarray(clip['native_relative_pts_s'])
        duration = float(pts[-1] - pts[0])
        fps = (len(frames)-1) / duration
        # Pad to a patch-aligned shape without reducing native detail.
        frames = np.pad(frames, ((0,0),(0,24),(0,0),(0,0)), mode='edge')
        messages = [{'role':'user','content':[{'type':'video','video':'native_frames'}, {'type':'text','text':PROMPT}]}]
        text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        metadata = dict(fps=fps, total_num_frames=len(frames), frames_indices=list(range(len(frames))))
        inputs = processor(text=[text], videos=[frames], video_metadata=[metadata],
            do_sample_frames=False, do_resize=False, return_tensors='pt')
        grid = inputs['video_grid_thw'][0].tolist()
        if grid[0] != (len(frames)+1)//2 or grid[1:] != [24,40]:
            raise ValueError(f'Unexpected temporal/spatial resampling: {grid}')
        input_tokens = int(inputs['input_ids'].shape[1])
        save('progress.json', dict(stage='generating', current_clip=ident, native_frames=len(frames),
            input_tokens=input_tokens, complete_clips=len(predictions), total_clips=12))
        print('GENERATING',ident,'frames',len(frames),'tokens',input_tokens,flush=True)
        inputs = inputs.to('cuda:0')
        with torch.inference_mode(), sdpa_kernel(SDPBackend.EFFICIENT_ATTENTION):
            generated = model.generate(**inputs, max_new_tokens=3072, do_sample=False, use_cache=True)
        new_ids = generated[0,inputs['input_ids'].shape[1]:]
        raw = processor.decode(new_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
        (OUT / (ident + '_raw.txt')).write_text(raw, encoding='utf-8')
        record = dict(id=ident, source_sha256=clip['source_sha256'], native_frames=len(frames),
            input_tokens=input_tokens, output_tokens=len(new_ids), generation_seconds=round(time.time()-begin,3),
            video_grid_thw=grid, mean_fps=fps, native_first_relative_pts_s=float(pts[0]),
            max_timestamp_linearization_error_s=float(np.max(np.abs(np.arange(len(pts))/fps-(pts-pts[0])))),
            raw_output_file=ident+'_raw.txt')
        try:
            if len(new_ids) >= 3072:
                raise ValueError('Output reached token limit; no silently truncated count')
            answer = parse_answer(raw, duration)
            record.update(status='parsed', answer=answer,
                predicted_additions=sum(e['quantity'] for e in answer['events']),
                uncertain_event_count=len(answer['uncertain_events']))
        except Exception as exc:
            record.update(status='invalid_model_output', error=str(exc), predicted_additions=None)
        save(ident+'_prediction.json', record)
        predictions.append(record)
        save('predictions.json', predictions)
        print('RESULT', ident, record.get('predicted_additions'), record['status'],flush=True)
        del inputs, generated, new_ids, frames
        gc.collect();torch.cuda.empty_cache()
    save('complete.json', dict(completed=True, model_id=MODEL_ID, clips_attempted=len(predictions),
        clips_parsed=sum(p['status']=='parsed' for p in predictions),
        invalid_outputs=sum(p['status']!='parsed' for p in predictions),
        native_frames=sum(p['native_frames'] for p in predictions),
        training=False, reference_counts_used=False, september_used=False,
        production_ready=False, automatic_metrics_available=False))
    save('progress.json', dict(stage='complete_predictions_ready_for_local_scoring', complete_clips=12, total_clips=12))
    print('QWEN_OCTOBER_COMPLETE', (OUT/'complete.json').read_text(), flush=True)


try:
    main()
except Exception as exc:
    save('failure.json', dict(error=repr(exc), traceback=traceback.format_exc()))
    raise
finally:
    with zipfile.ZipFile('/kaggle/working/qwen_october_count_v1_outputs.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for path in OUT.rglob('*'):
            if path.is_file():
                archive.write(path, path.relative_to(OUT))
