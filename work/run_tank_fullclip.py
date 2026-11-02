"""Run the frozen counter once; never promote proposals to confirmed loads."""
from pathlib import Path
import subprocess,sys,json,hashlib,datetime,msvcrt,traceback
b=Path('outputs/tank_transfer_training_v1/dataset_v2/heldout_counting')
out=b/'test28_fullclip';out.mkdir(exist_ok=True)
lock=(out/'run.lock').open('a+b');lock.seek(0)
try:msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
except OSError:raise SystemExit('Full clip evaluation already running')
def save(status,**kw):
 (out/'run_status.json').write_text(json.dumps(dict(status=status,updated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),**kw),indent=2),encoding='utf-8')
try:
 if (out/'result.json').exists():raise SystemExit('Existing result preserved')
 frozen=json.loads((b/'frozen_test_protocol.json').read_text())
 for path,key in [(b/'best.pt','model_sha256'),(b/'test28_camera11_094400.mp4','test_source_sha256'),(Path('work/evaluate_tank_departures_v2.py'),'counter_code_sha256')]:
  assert hashlib.sha256(path.read_bytes()).hexdigest()==frozen[key],key
 save('running',scope='Whole source clip, including first 180s already evaluated; do not add previous count.',content_review='pending',daily_count=None)
 subprocess.run([sys.executable,'work/evaluate_tank_departures_v2.py','--video',str(b/'test28_camera11_094400.mp4'),'--out',str(out)],check=True)
 r=json.loads((out/'result.json').read_text())
 queue=[dict(e,review_status='pending',load_evidence=None,confirmed_loaded_departure=None) for e in r['events']]
 (out/'content_review_queue.json').write_text(json.dumps(queue,indent=2),encoding='utf-8')
 save('automatic_pass_complete_manual_review_pending',automatic_proposals=len(queue),confirmed_loaded_count=None,daily_count=None)
except Exception:
 save('failed',error=traceback.format_exc());raise
