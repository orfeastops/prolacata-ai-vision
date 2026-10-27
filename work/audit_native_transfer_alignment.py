"""Check label timing against native source images, not fps metadata."""
import json
from pathlib import Path
import cv2,numpy as np

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/facility_dataset/temporal_pipeline/placement_counter_v3'

def small(frame):return cv2.resize(cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY),(160,90)).astype(np.float32)

def main():
    rows=json.loads((BASE/'interval_supervision.json').read_text(encoding='utf-8'))['segments'];results=[]
    for row in rows:
        data=np.load(BASE/'native_frames'/(row['segment_id']+'.npz'))
        times=data['timestamps'];frames=data['frames'];mini=np.stack([small(f) for f in frames])
        cap=cv2.VideoCapture(row['media_path']);fps=cap.get(cv2.CAP_PROP_FPS);anchors=[]
        for t in np.arange(1,row['duration_s']-1,1.0):
            cap.set(cv2.CAP_PROP_POS_FRAMES,round(t*fps));ok,frame=cap.read();assert ok
            expected=row['source_encoded_interval_s'][0]+t
            candidates=np.flatnonzero(abs(times-expected)<2)
            scores=np.mean((mini[candidates]-small(frame))**2,axis=(1,2))
            best=int(candidates[int(np.argmin(scores))])
            anchors.append(dict(review_time_s=float(t),matched_native_time_s=float(times[best]),
                offset_s=float(times[best]-expected),pixel_mse=float(scores.min()),native_index=best))
        cap.release()
        offsets=np.array([a['offset_s'] for a in anchors]);med=float(np.median(offsets))
        residual=np.abs(offsets-med)
        result=dict(segment_id=row['segment_id'],anchors=anchors,median_time_offset_s=med,
            max_residual_after_constant_offset_s=float(residual.max()),
            label_time_alignment_ok=abs(med)<.125 and float(np.quantile(residual,.9))<.15,
            timing_scope='Image matching on cached source crop; constant offset diagnostics, no changed labels')
        results.append(result)
        print(row['segment_id'],round(med,4),round(float(residual.max()),4),result['label_time_alignment_ok'],flush=True)
    (BASE/'native_alignment_audit.json').write_text(json.dumps(dict(segments=results,
        all_passed=all(r['label_time_alignment_ok'] for r in results)),indent=2),encoding='utf-8')

if __name__=='__main__':main()
