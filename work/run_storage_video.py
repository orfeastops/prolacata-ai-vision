"""One command for video inference and the requested date/time event export."""
import argparse
import subprocess
import sys,json,hashlib
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--video',required=True);p.add_argument('--date',required=True)
    p.add_argument('--out',required=True);p.add_argument('--start',default='0');p.add_argument('--end',default='0')
    a=p.parse_args();base=Path(__file__).parent
    subprocess.run([sys.executable,str(base/'run_room11_storage.py'),'--video',a.video,
        '--out',a.out,'--start',a.start,'--end',a.end],check=True)
    clock=base/'export_room11_storage_v2.py'
    subprocess.run([sys.executable,str(clock),'--run',a.out,
        '--date',a.date,'--export-dir',str(Path(a.out)/'clock_v2')],check=True)
    (Path(a.out)/'pipeline_complete.json').write_text(json.dumps(dict(status='complete',
        clock_export_sha256=hashlib.sha256(clock.read_bytes()).hexdigest(),
        records='clock_v2/storage_predictions.json',production_ready=False),indent=2))

if __name__=='__main__':main()
