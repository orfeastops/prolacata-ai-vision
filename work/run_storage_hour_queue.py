"""Frozen per-file baseline for candidate held-out hour; never aggregate raw totals."""
import json,subprocess,sys,hashlib,msvcrt,time
from pathlib import Path
base=Path('D:/Codex/tank-storage');work=Path(__file__).parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):
    tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(d,indent=2),encoding='utf-8');tmp.replace(p)
full=base/'test28_full_run01'
assert (full/'pipeline_complete.json').exists(),'Existing full run must finish first'
lock=(full/'run.lock').open('r+b');lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
frozen=read(full/'frozen_config.json')
assert sha(work/'run_room11_storage.py')==frozen['code_sha256']
assert sha(work/'evaluate_payload_counter_v5.py')==frozen['payload_counter_sha256']
assert sha(work/'export_room11_storage_v2.py')==read(full/'pipeline_complete.json')['clock_export_sha256']
plan=read(base/'one_hour_plan.json');root=base/'hour_per_file_run01';root.mkdir(exist_ok=True)
status={'status':'running','completed':[],'reused_fullclip':62,'started':time.time(),
    'aggregate_count':None,'scored_hour_complete':False,'cross_file_state':False,
    'limitations':['Full source context retained, including footage outside scoring hour.',
    'Per-file baseline only: boundary-spanning placement may be missed. No hidden state continuity.',
    'Overlaps and visible-clock window require reconciliation before scoring; do not add raw counts.']}
try:
    for item in plan['files']:
        i=item['index']
        if i==62:continue
        out=root/f'clip_{i:03d}';status['active_clip']=i;save(root/'status.json',status)
        if (out/'pipeline_complete.json').exists():
            assert read(out/'frozen_config.json')['code_sha256']==frozen['code_sha256']
            status['completed'].append(i);continue
        if (out/'result.json').exists():raise RuntimeError('Partial pipeline requires inspection; refusing inference restart')
        with (root/f'clip_{i:03d}.log').open('a',encoding='utf-8') as log:
            subprocess.run([sys.executable,str(work/'run_storage_video.py'),'--video',item['source'],
                '--date','2026-10-28','--out',str(out)],stdout=log,stderr=subprocess.STDOUT,check=True)
        status['completed'].append(i);save(root/'status.json',status)
    status['status']='inference_complete_reconciliation_pending';save(root/'status.json',status)
except Exception as e:
    status.update(status='error',error=repr(e));save(root/'status.json',status);raise
finally:lock.close()
