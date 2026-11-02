"""Sequential frozen inference. Raw clip proposals must never be summed as daily loads."""
from pathlib import Path
import json,sys,subprocess,hashlib,zipfile,msvcrt,datetime,traceback
b=Path('outputs/tank_transfer_training_v1/dataset_v2/heldout_counting');out=b/'day28_runs';out.mkdir(exist_ok=True)
lock=(b/'test28_fullclip/run.lock').open('a+b');lock.seek(0)
try:msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
except OSError:raise SystemExit('Shared inference lock held; no second run started')
def write(path,obj):
 tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(obj,indent=2),encoding='utf-8');tmp.replace(path)
def status(state,**kw):write(out/'status.json',dict(status=state,updated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),daily_count=None,**kw))
f=json.loads((b/'frozen_test_protocol.json').read_text())
assert hashlib.sha256((b/'best.pt').read_bytes()).hexdigest()==f['model_sha256']
assert hashlib.sha256(Path('work/evaluate_tank_departures_v2.py').read_bytes()).hexdigest()==f['counter_code_sha256']
queue=json.loads((b/'day28_camera11_queue.json').read_text())
seen={f['test_source_sha256']:'test28_fullclip'};completed=0
try:
 for row in queue['files']:
  src=row['source'];idx=row['index']
  if row['status']=='active_fullclip':continue
  dest=out/f'clip_{idx:03}';dest.mkdir(exist_ok=True)
  if (dest/'source.json').exists():
   meta=json.loads((dest/'source.json').read_text());sha=meta['sha256']
  else:
   status('copying_source',active_index=idx,completed=completed)
   video=dest/'source.mp4'
   with zipfile.ZipFile(src['archive']) as z,z.open(src['member']) as source,video.open('wb') as target:
    while data:=source.read(1024*1024):target.write(data)
   sha=hashlib.sha256(video.read_bytes()).hexdigest();meta=dict(src,sha256=sha,metadata_overlap_s=row['overlap_with_previous_union_s'],metadata_gap_before_s=row['gap_before_s'],aggregation_allowed=False)
   write(dest/'source.json',meta)
  if sha in seen:
   write(dest/'duplicate.json',{'identical_sha256_to':seen[sha],'exclude_from_count':True});continue
  seen[sha]=str(dest)
  if not (dest/'result.json').exists():
   status('inference_running',active_index=idx,completed=completed,source=src['basename'])
   with (dest/'stdout.log').open('w') as so,(dest/'stderr.log').open('w') as se:
    subprocess.run([sys.executable,'work/evaluate_tank_departures_v2.py','--video',str(dest/'source.mp4'),'--out',str(dest)],stdout=so,stderr=se,check=True)
  result=json.loads((dest/'result.json').read_text());assert result['config']==f['config']
  if not (dest/'review_queue.json').exists():write(dest/'review_queue.json',{'review_status':'pending','automatic_proposals':result['events'],'confirmed_loaded_count':None,'boundary_review_required':True,'cross_clip_dedup_required':True,'aggregation_allowed':False})
  completed+=1
  status('clip_complete_review_pending',active_index=idx,completed=completed)
 status('all_automatic_passes_complete_review_pending',completed=completed)
except Exception:
 status('failed',completed=completed,error=traceback.format_exc());raise
