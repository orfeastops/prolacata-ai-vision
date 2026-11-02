"""Check original-file hashes and filename-interval overlap before evaluation."""
import hashlib,json,re
from pathlib import Path
from datetime import datetime

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/facility_dataset/temporal_pipeline'
OUT=BASE/'placement_counter_v4/event_quantity_diagnostic'

def main():
    data=json.loads((OUT/'dataset.json').read_text(encoding='utf-8'))
    index={r['sha256']:r for r in json.loads((BASE/'temporal_media_index.json').read_text())}
    records=[]
    for r in data['rows']:
        p=Path(r.get('source_file') or index[r['source_sha256']]['local_path'])
        m=re.search(r'Camera_(\d+)_DVR_(\d{14})_(\d{14})',p.name);assert m
        start=datetime.strptime(m[2],'%Y%m%d%H%M%S');stop=datetime.strptime(m[3],'%Y%m%d%H%M%S')
        verified=None
        if r['id'].startswith('C'):
            with p.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
            assert actual==r['source_sha256'];verified=True
        records.append(dict(id=r['id'],role=r['role'],camera=m[1],start=start.isoformat(),end=stop.isoformat(),
            source_sha256=r['source_sha256'],original_hash_verified_this_run=verified))
    overlaps=[]
    for a in records:
        if a['role']!='train':continue
        for b in records:
            if b['role']=='train' or a['camera']!=b['camera']:continue
            if max(a['start'],b['start'])<min(a['end'],b['end']):overlaps.append([a['id'],b['id']])
    assert not overlaps,overlaps
    report=dict(records=records,train_eval_filename_interval_overlaps=overlaps,
        original_C01_C06_hashes_verified=True,filename_times_are_not_verified_camera_wall_clock=True,
        source_split_passed=True)
    (OUT/'source_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('Source audit passed: six original-file hashes, no training/evaluation filename interval overlap.')

if __name__=='__main__':main()
