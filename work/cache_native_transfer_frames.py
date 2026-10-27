"""Decode original sources sequentially, preserving every frame and timestamp.

Do not seek in camera exports: HEVC seeks produced missing-reference warnings.
Do not trust nominal fps/frame-count metadata from the camera export container.
"""
import json,time,hashlib,collections
from pathlib import Path
import cv2,numpy as np

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/facility_dataset/temporal_pipeline'
OUT=BASE/'placement_counter_v3/native_frames'

def main():
    cv2.setNumThreads(2);OUT.mkdir(parents=True,exist_ok=True)
    rows=json.loads((BASE/'placement_counter_v3/interval_supervision.json').read_text(encoding='utf-8'))['segments']
    index={r['sha256']:r for r in json.loads((BASE/'temporal_media_index.json').read_text())}
    groups=collections.defaultdict(list)
    for row in rows:groups[row['source_sha256']].append(row)
    reports=[];started=time.time()
    for digest,group in groups.items():
        if all((OUT/(r['segment_id']+'.json')).exists() and (OUT/(r['segment_id']+'.npz')).exists() for r in group):
            reports.extend(json.loads((OUT/(r['segment_id']+'.json')).read_text()) for r in group);continue
        path=Path(index[digest]['local_path'])
        with path.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest
        cap=cv2.VideoCapture(str(path));assert cap.isOpened()
        nominal_fps=cap.get(cv2.CAP_PROP_FPS)
        buffers={r['segment_id']:dict(images=[],timestamps=[],indices=[]) for r in group}
        end=max(r['source_encoded_interval_s'][1] for r in group)
        count=0;previous=None;duplicates=0
        while True:
            ok,frame=cap.read()
            if not ok:raise RuntimeError(f'Source ended before requested interval: {path.name}')
            timestamp=cap.get(cv2.CAP_PROP_POS_MSEC)/1000
            if previous is not None and timestamp<previous-1e-6:raise RuntimeError('Non-monotonic native timestamps')
            if previous is not None and timestamp==previous:duplicates+=1
            previous=timestamp
            if timestamp>=end:break
            for row in group:
                start,stop=row['source_encoded_interval_s']
                if start<=timestamp<stop:
                    b=buffers[row['segment_id']];crop=frame[720:1080,800:1440]
                    assert crop.shape==(360,640,3)
                    b['images'].append(crop.copy());b['timestamps'].append(timestamp);b['indices'].append(count)
            count+=1
            if count%1500==0:print(path.name,'decoded',count,'through',round(timestamp,2),flush=True)
        cap.release()
        for row in group:
            b=buffers[row['segment_id']];ts=np.array(b['timestamps']);ix=np.array(b['indices'])
            assert len(ts)>1 and np.all(np.diff(ix)==1), 'A native frame was omitted inside the interval'
            assert np.all(np.diff(ts)>0), 'Repeated native timestamps require explicit handling'
            deltas=np.diff(ts);start,stop=row['source_encoded_interval_s']
            assert 0<=ts[0]-start<.2 and 0<stop-ts[-1]<.2
            dest=OUT/(row['segment_id']+'.npz')
            np.savez_compressed(dest,frames=np.stack(b['images']),timestamps=ts,
                source_frame_indices=ix,source_sha256=digest,source_interval=np.array([start,stop]))
            report=dict(segment_id=row['segment_id'],source_sha256=digest,cache_file=str(dest),
                native_frames=len(ts),nominal_header_fps=nominal_fps,
                measured_frames_per_second=(len(ts)-1)/(ts[-1]-ts[0]),
                min_frame_interval_s=float(deltas.min()),max_frame_interval_s=float(deltas.max()),
                median_frame_interval_s=float(np.median(deltas)),first_source_time_s=ts[0],last_source_time_s=ts[-1],
                source_frame_indices_contiguous=True,frames_deliberately_skipped=0,
                frames_artificially_duplicated=0,decode_method='sequential from original source start; no seek',
                cache_pixels='lossless numpy compression of native 640x360 crop',
                temporal_resampling=False,source_clock_is_camera_wall_clock=False)
            (OUT/(row['segment_id']+'.json')).write_text(json.dumps(report,indent=2),encoding='utf-8');reports.append(report)
            print(json.dumps(report),flush=True)
        (OUT/'progress.json').write_text(json.dumps(dict(status='running',completed_segments=len(reports),total_segments=len(rows),elapsed_seconds=round(time.time()-started))),encoding='utf-8')
    (OUT/'manifest.json').write_text(json.dumps(dict(segments=reports,sampling_policy='all native frames; no temporal resampling',
        frames=sum(r['native_frames'] for r in reports),september_used=False),indent=2),encoding='utf-8')
    (OUT/'progress.json').write_text(json.dumps(dict(status='complete',completed_segments=len(reports),elapsed_seconds=round(time.time()-started))),encoding='utf-8')

if __name__=='__main__':main()
