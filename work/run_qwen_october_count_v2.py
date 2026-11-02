"""Inference-only diagnostic: 4fps, compact events, same official Qwen weights.

Use run(model, processor, INPUT_CLIPS) after the v1 source verification/model
setup. This intentionally keeps references local. The first v1 attempt failed
to return a complete answer; v2 is a documented development revision, not a
preregistered independent acceptance test.
"""
import gc
import hashlib
import json
import time
import traceback
import zipfile
from pathlib import Path
import numpy as np
import torch
from torch.nn.attention import sdpa_kernel, SDPBackend
from transformers import LogitsProcessor, LogitsProcessorList
from transformers.generation.streamers import BaseStreamer

OUT2 = Path('/kaggle/working/qwen_october_count_v2')
TEMP2 = Path('/kaggle/temp/qwen_october_count_v1')
PROMPT2 = '''Count whole cheese blocks newly released into the production filling
tank during this video. Observe both workers. Follow each block from tray pickup
through carrying to release. Determine the quantity from visible objects, with
no fixed quantity per hand or tray. Count each block once. Exclude crumbs,
salting, empty hands, gestures, moving empty trays, separator sheets, and
rearranging cheese already inside the tank. Exclude loads still carried at the
end. A pickup before the clip is allowed only if quantity and release are visible.
Return ONLY compact JSON: {"events":[{"t":0.0,"q":1,"s":"left"}],"uncertain":[]}.
That event is a schema example, not a required event. Replace it with your actual
observations. t is the release time in seconds, q is the number of blocks,
s is left or right worker in the image. For uncertainty use {"t":0.0,"q":null}.
Empty lists are valid. Do not give prose, repeat events, or continue inventing
events. The clip contains only the visible actions; stop after its last action.'''


def write2(name, value):
    (OUT2/name).write_text(json.dumps(value, indent=2), encoding='utf-8')


class FiniteScores(LogitsProcessor):
    def __call__(self, input_ids, scores):
        if not torch.isfinite(scores).all():
            raise RuntimeError('Non-finite model scores: refuse a meaningless count')
        return scores


class ProgressStream(BaseStreamer):
    def __init__(self, processor, clip_id):
        self.processor, self.clip_id = processor, clip_id
        self.first, self.ids, self.begin = True, [], time.time()

    def put(self, value):
        if self.first:
            self.first = False
            return
        self.ids.extend(value.detach().cpu().reshape(-1).tolist())
        if len(self.ids) % 32 == 0:
            write2('token_progress.json', dict(id=self.clip_id, generated_tokens=len(self.ids),
                seconds=round(time.time()-self.begin,1)))

    def end(self):
        pass


def pack2():
    with zipfile.ZipFile('/kaggle/working/qwen_october_experiment_outputs.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for folder in Path('/kaggle/working').glob('qwen_october_count_v*'):
            if folder.is_dir():
                for p in folder.rglob('*'):
                    if p.is_file():
                        z.write(p, p.relative_to('/kaggle/working'))


def run(model, processor, clips):
    OUT2.mkdir(exist_ok=True)
    assert not (OUT2/'predictions.json').exists(), 'Do not overwrite frozen predictions'
    source_config = json.loads(Path('/kaggle/working/qwen_october_count_v1/frozen_config.json').read_text())
    config = dict(model_id=source_config['model_id'], model_revision=source_config['model_revision'],
        dtype='float16', weights_unchanged=True, training=False, reference_counts_used=False,
        september_used=False, sampling='nearest original frame to each 0.25 second tick; no interpolation',
        crop=[800,720,1440,1080], spatial_padding='bottom 24px edge padding; no resizing',
        decoding={'do_sample':False,'max_new_tokens':1024,'max_time_s':600},
        prompt_sha256=hashlib.sha256(PROMPT2.encode()).hexdigest(),
        purpose='Development revision after verbose v1 hit token limit; not independent acceptance')
    write2('frozen_config.json', config)
    (OUT2/'prompt.txt').write_text(PROMPT2, encoding='utf-8')
    write2('input_clips.json', clips)
    results=[]
    try:
        for clip in clips:
            ident=clip['id']
            begin=time.time()
            original=np.load(TEMP2/(ident+'.npy'), mmap_mode='r')
            pts=np.array(clip['native_relative_pts_s']);pts=pts-pts[0]
            duration=float(pts[-1])
            indices=sorted(set(int(np.argmin(np.abs(pts-t))) for t in np.arange(0,duration+0.001,.25)))
            frames=np.array(original[indices]);native_frames=len(original)
            del original
            frames=np.pad(frames,((0,0),(0,24),(0,0),(0,0)),mode='edge')
            metadata=dict(fps=(native_frames-1)/duration,total_num_frames=native_frames,frames_indices=indices)
            message=[{'role':'user','content':[{'type':'video','video':'native_frames'}, {'type':'text','text':PROMPT2}]}]
            text=processor.apply_chat_template(message,tokenize=False,add_generation_prompt=True)
            inputs=processor(text=[text],videos=[frames],video_metadata=[metadata],
                do_sample_frames=False,do_resize=False,return_tensors='pt')
            grid=inputs['video_grid_thw'][0].tolist()
            assert grid==[(len(indices)+1)//2,24,40], grid
            n=int(inputs['input_ids'].shape[1])
            write2('progress.json',dict(stage='generating',current_clip=ident,complete_clips=len(results),
                total_clips=len(clips),selected_frames=len(indices),available_native_frames=native_frames,input_tokens=n))
            print('V2_GENERATING',ident,'frames',len(indices),'tokens',n,flush=True)
            inputs=inputs.to('cuda:0')
            stream=ProgressStream(processor,ident)
            with torch.inference_mode(), sdpa_kernel(SDPBackend.EFFICIENT_ATTENTION):
                generated=model.generate(**inputs,max_new_tokens=1024,max_time=600,do_sample=False,
                    use_cache=True,streamer=stream,logits_processor=LogitsProcessorList([FiniteScores()]))
            new=generated[0,n:]
            raw=processor.decode(new,skip_special_tokens=True,clean_up_tokenization_spaces=False)
            (OUT2/(ident+'_raw.txt')).write_text(raw,encoding='utf-8')
            record=dict(id=ident,source_sha256=clip['source_sha256'],native_frames=native_frames,
                selected_frame_indices=indices,selected_frames=len(indices),input_tokens=n,output_tokens=len(new),
                generation_seconds=round(time.time()-begin,3),video_grid_thw=grid,predicted_additions=None)
            try:
                ends=model.generation_config.eos_token_id
                if isinstance(ends,int):ends=[ends]
                if len(new)>=1024 or int(new[-1]) not in ends:
                    raise ValueError('Generation stopped at resource limit, without a complete answer')
                clean=raw.strip()
                if clean.startswith('```'):clean=clean.split('\n',1)[1].rsplit('```',1)[0].strip()
                answer=json.loads(clean)
                assert isinstance(answer['events'],list) and isinstance(answer['uncertain'],list)
                events=[]
                for e in answer['events']:
                    assert type(e['q']) is int and e['q']>0
                    assert type(e['t']) in (float,int) and 0<=e['t']<=duration+.15
                    assert e['s'] in ('left','right')
                    events.append(dict(release_s=e['t'],quantity=e['q'],side=e['s'],destination='production_tank'))
                record.update(status='parsed',predicted_additions=sum(e['quantity'] for e in events),
                    answer=dict(events=events,uncertain_events=answer['uncertain']),uncertain_event_count=len(answer['uncertain']))
            except Exception as exc:
                record.update(status='invalid_model_output',error=repr(exc))
            results.append(record)
            write2(ident+'_prediction.json',record);write2('predictions.json',results)
            print('V2_RESULT',ident,record['status'],record['predicted_additions'],flush=True)
            del inputs,generated,new,frames
            gc.collect();torch.cuda.empty_cache()
            pack2()
        write2('complete.json',dict(completed=True,clips_attempted=len(results),
            clips_parsed=sum(r['status']=='parsed' for r in results),training=False,reference_counts_used=False))
        write2('progress.json',dict(stage='complete',complete_clips=len(results),total_clips=len(clips)))
    except BaseException as exc:
        write2('failure.json',dict(error=repr(exc),traceback=traceback.format_exc()))
        print('V2_FAILURE',repr(exc),flush=True)
    finally:
        pack2()
