"""Frozen diagnostic baseline: carried-object detections -> transfer hypotheses.

This is deliberately separate from BlockCounter's verified evidence API. A
short-lived detector track is not a certified physical identity, and disappearance
is not observed release. Output counts are hypotheses with unresolved tracks.
No model training or parameter search is performed by this program.
"""
import os
import json
import hashlib
import time
import subprocess
import argparse
from pathlib import Path
from functools import lru_cache

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'outputs/facility_dataset/temporal_pipeline'
OUT = BASE / 'unseen_test_20260926/object_trajectory_test_v1'
CHECKPOINT = BASE / 'placement_counter_v2/carried_cheese_uncertainty_v2/run/weights/last.pt'
FFMPEG = ROOT / 'work/video_decoder/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
os.environ.update(YOLO_CONFIG_DIR=str(ROOT / 'outputs/feta_training/runtime_config'), YOLO_AUTOINSTALL='false')

# Geometry, sampling, travel and gap limits inherited from the October baseline.
# These are fixed engineering choices, not fitted to September counts.
CONFIG = dict(fps=8, detector_confidence=.25, detector_iou=.7,
              match_distance_px=65, max_speed_px_s=500, max_gap_s=.5,
              min_source_observations=2, min_tank_observations=2,
              min_single_observations=3, min_travel_px=35,
              overlap_ambiguity_iou=.3,
              tank_polygon=[[40,180],[180,120],[310,265],[140,350]],
              source_polygon=[[190,330],[450,170],[530,225],[310,359]])


def save(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def inside(p, poly):
    # Boundary-inclusive ray casting without a dependency on video libraries.
    x, y = p
    result = False
    for a, b in zip(poly, poly[1:] + poly[:1]):
        cross = (x-a[0])*(b[1]-a[1])-(y-a[1])*(b[0]-a[0])
        if abs(cross) < 1e-6 and min(a[0],b[0]) <= x <= max(a[0],b[0]) and min(a[1],b[1]) <= y <= max(a[1],b[1]):
            return True
        if (a[1] > y) != (b[1] > y) and x < (b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:
            result = not result
    return result


def iou(a, b):
    inter = max(0, min(a[2], b[2])-max(a[0], b[0])) * max(0, min(a[3], b[3])-max(a[1], b[1]))
    union = (a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-inter
    return inter / union if union else 0.


def distance(a, b):
    return ((a[0]-b[0])**2+(a[1]-b[1])**2)**.5


def assignment(cost):
    """Globally minimal gated matching; unmatched observations are permitted."""
    if not cost or not cost[0]:
        return []
    if len(cost[0]) > 12:
        # Unusual crowded detections are handled conservatively by no association.
        return []
    @lru_cache(None)
    def solve(i, used):
        if i == len(cost):
            return 0., ()
        value, pairs = solve(i+1, used)
        best = (65+value, pairs)
        for j, c in enumerate(cost[i]):
            if used & (1 << j) or c >= 65:
                continue
            value, pairs = solve(i+1, used | (1 << j))
            if c+value < best[0]:
                best = (c+value, ((i, j),)+pairs)
        return best
    return list(solve(0, 0)[1])


class HypothesisTracker:
    def __init__(self, config=None):
        self.config = dict(CONFIG if config is None else config)
        self.active, self.events, self.next_id = {}, [], 1

    def finish(self, key, boundary=False):
        track = self.active.pop(key)
        observations = track['observations']
        source = [o for o in observations if o['zone'] == 'source']
        first_source = source[0] if source else None
        tank = [o for o in observations if o['zone'] == 'tank' and first_source and o['t'] > first_source['t']]
        reasons = []
        c = self.config
        if boundary: reasons.append('video_boundary_no_release_observation')
        if len(source) < c['min_source_observations']: reasons.append('pickup_path_missing')
        if len(tank) < c['min_tank_observations']: reasons.append('tank_path_missing')
        if observations[-1]['zone'] != 'tank': reasons.append('last_seen_outside_tank')
        if not tank or max(distance(o['point'], first_source['point']) for o in tank) < c['min_travel_px']:
            reasons.append('insufficient_source_to_tank_travel')
        if any(o['cls'] != 0 for o in observations): reasons.append('quantity_unknown')
        if len([o for o in observations if o['cls'] == 0]) < c['min_single_observations']:
            reasons.append('insufficient_single_block_evidence')
        if track['overlap_ambiguous']: reasons.append('overlapping_object_or_class_hypotheses')
        if track['association_ambiguous']: reasons.append('ambiguous_track_association')
        if tank and any(o['zone'] == 'source' and o['t'] > tank[0]['t'] for o in observations):
            reasons.append('object_returned_towards_source')
        self.events.append(dict(track_id=key, first_s=observations[0]['t'], last_s=observations[-1]['t'],
            proposed_deposit_s=observations[-1]['t'] if not reasons else None,
            status='single_block_transfer_hypothesis' if not reasons else 'unresolved_track',
            candidate_quantity=1 if not reasons else None, reasons=reasons,
            observation_count=len(observations), source_observations=len(source), tank_observations=len(tank),
            verified_release=False, certified_physical_identity=False))

    def update(self, t, detections):
        c = self.config
        for key in list(self.active):
            if t-self.active[key]['observations'][-1]['t'] > c['max_gap_s']:
                self.finish(key)
        points = [[(d['box'][0]+d['box'][2])/2, (d['box'][1]+d['box'][3])/2] for d in detections]
        ambiguous = set()
        for i in range(len(detections)):
            for j in range(i):
                if iou(detections[i]['box'], detections[j]['box']) >= c['overlap_ambiguity_iou']:
                    ambiguous.update([i, j])
        keys = list(self.active)
        costs = []
        for key in keys:
            track = self.active[key]
            old = track['observations'][-1]
            dt = t-old['t']
            predicted = [old['point'][i]+track['velocity'][i]*dt for i in range(2)]
            costs.append([distance(predicted, p) if distance(old['point'], p) < max(20, dt*c['max_speed_px_s']) else 1e6 for p in points])
        associations = {j: keys[i] for i, j in assignment(costs)}
        rendered = []
        for j, (detection, point) in enumerate(zip(detections, points)):
            key = associations.get(j)
            if key is None:
                key = self.next_id
                self.next_id += 1
                self.active[key] = dict(observations=[], velocity=[0., 0.], overlap_ambiguous=False, association_ambiguous=False)
            track = self.active[key]
            if j in associations:
                i = keys.index(key)
                # Very similar alternatives make an identity-sensitive count unsafe.
                row = sorted(v for v in costs[i] if v < c['match_distance_px'])
                col = sorted(row_[j] for row_ in costs if row_[j] < c['match_distance_px'])
                track['association_ambiguous'] |= (len(row)>1 and row[1]-row[0]<10) or (len(col)>1 and col[1]-col[0]<10)
            if track['observations']:
                old = track['observations'][-1]
                dt = t-old['t']
                track['velocity'] = [.5*track['velocity'][i]+.5*(point[i]-old['point'][i])/dt for i in range(2)]
            zone = 'tank' if inside(point, c['tank_polygon']) else ('source' if inside(point, c['source_polygon']) else 'other')
            observation = dict(t=t, point=point, zone=zone, cls=detection['cls'])
            track['observations'].append(observation)
            track['overlap_ambiguous'] |= j in ambiguous
            rendered.append(dict(**detection, track_id=key, zone=zone,
                ambiguous=track['overlap_ambiguous'] or track['association_ambiguous']))
        return rendered

    def close(self):
        for key in list(self.active):
            self.finish(key, boundary=True)


def analyze(model, source, dest, crop, duration=None, preview=True):
    import cv2
    import numpy as np
    dest.mkdir(parents=True, exist_ok=True)
    if (dest / 'report.json').exists():
        return json.loads((dest / 'report.json').read_text(encoding='utf-8'))
    command = [str(FFMPEG), '-loglevel', 'error', '-i', str(source)]
    if duration: command += ['-t', str(duration)]
    command += ['-vf', ('crop=640:360:800:720,' if crop else '')+'fps=8', '-threads', '2', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-']
    with (dest / 'decoder.log').open('wb') as log:
        decoder = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=log)
        encoder = None
        if preview:
            encoder = subprocess.Popen([str(FFMPEG), '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '640x420', '-r', '8', '-i', '-', '-an', '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(dest / 'trajectory_preview.mp4')], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        tracker, i, start = HypothesisTracker(), 0, time.time()
        try:
            with (dest / 'observations.jsonl').open('w', encoding='utf-8') as stream:
                while True:
                    frames = []
                    for _ in range(8):
                        raw = decoder.stdout.read(640*360*3)
                        if not raw: break
                        if len(raw) != 640*360*3: raise RuntimeError('Partial decoded frame')
                        frames.append(np.frombuffer(raw, np.uint8).reshape(360,640,3).copy())
                    if not frames: break
                    predictions = model.predict(frames, conf=CONFIG['detector_confidence'], iou=CONFIG['detector_iou'], imgsz=640, device='cpu', verbose=False, rect=True)
                    for frame, prediction in zip(frames, predictions):
                        t = i/CONFIG['fps']
                        detections = [dict(box=b, cls=int(c), confidence=float(p)) for b,c,p in zip(prediction.boxes.xyxy.tolist(), prediction.boxes.cls.tolist(), prediction.boxes.conf.tolist())]
                        rendered = tracker.update(t, detections)
                        stream.write(json.dumps(dict(time_s=t, detections=rendered))+'\n')
                        if encoder:
                            for r in rendered:
                                x1,y1,x2,y2 = map(int, r['box'])
                                color = (0,160,255) if r['ambiguous'] or r['cls'] else (0,230,0)
                                cv2.rectangle(frame,(x1,y1),(x2,y2),color,1)
                                label = '1?' if r['cls']==0 else 'qty?'
                                cv2.putText(frame, f"T{r['track_id']} {label}",(x1,max(12,y1-3)),0,.4,color,1)
                            for name,color in [('tank_polygon',(0,255,255)),('source_polygon',(255,130,0))]:
                                cv2.polylines(frame,[np.array(CONFIG[name],np.int32)],True,color,1)
                            canvas=np.zeros((420,640,3),np.uint8)
                            canvas[60:]=frame
                            candidate=sum(e['candidate_quantity'] or 0 for e in tracker.events)
                            unresolved=sum(e['candidate_quantity'] is None for e in tracker.events)
                            cv2.putText(canvas,f'{t:.2f}s | Transfer hypotheses: {candidate} | Unresolved tracks: {unresolved}',(7,20),0,.45,(255,255,255),1)
                            cv2.putText(canvas,'EXPERIMENTAL - incomplete count; disappearance is not verified release',(7,44),0,.4,(0,180,255),1)
                            encoder.stdin.write(canvas.tobytes())
                        i+=1
                    if i%80==0:
                        progress=dict(status='running',frames=i,video_seconds=i/8,elapsed_s=round(time.time()-start,1))
                        save(dest/'progress.json',progress)
                        print(dest.name,json.dumps(progress),flush=True)
        finally:
            decoder.stdout.close()
            rc=decoder.wait()
            if encoder:
                encoder.stdin.close()
                err=encoder.stderr.read().decode()
                erc=encoder.wait()
                if erc: raise RuntimeError(err)
        if rc: raise RuntimeError((dest/'decoder.log').read_text())
    tracker.close()
    save(dest/'events.json',tracker.events)
    report=dict(status='complete_experimental',frames_processed=i,duration_processed_s=i/8,
        transfer_hypothesis_count=sum(e['candidate_quantity'] or 0 for e in tracker.events),
        unresolved_tracks=sum(e['candidate_quantity'] is None for e in tracker.events),
        complete_block_count=None, verified_release_count=None, count_complete=False,
        elapsed_seconds=round(time.time()-start,1), production_ready=False)
    save(dest/'report.json',report)
    save(dest/'progress.json',dict(status='complete',**{k:v for k,v in report.items() if k!='status'}))
    return report


def freeze():
    OUT.mkdir(parents=True,exist_ok=True)
    path=OUT/'frozen_config.json'
    metadata=dict(config=CONFIG,checkpoint=str(CHECKPOINT),checkpoint_sha256=sha(CHECKPOINT),
        counter_source_sha256=sha(Path(__file__)),training_on_test=False,threshold_tuning_on_test=False,
        geometry_origin='Previously saved October camera geometry',
        test_prior_exposure='September video and user-confirmed four-block error example were inspected before this baseline; not a pristine blind test. Entire-video tank totals remain hidden.',
        limitations=['Detector tracks can split or merge; track IDs are hypotheses, not physical identity guarantees',
            'Disappearance in a tank polygon is a release proxy, not directly observed release',
            'Unknown regions and incomplete tracks are not assigned invented quantities',
            'No source tray identity or tray inventory model; no automatic tank change',
            'Detector can confuse crumbs or stationary cheese with carried whole blocks'])
    if path.exists():
        old=json.loads(path.read_text())
        assert old['counter_source_sha256']==metadata['counter_source_sha256'], 'Frozen counter modified'
        assert old['checkpoint_sha256']==metadata['checkpoint_sha256'], 'Frozen model modified'
        assert old['config']==CONFIG, 'Frozen config modified'
    else:
        save(path,metadata)
        (OUT/'counter_source_snapshot.py').write_bytes(Path(__file__).read_bytes())


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('stage',choices=['development','september'])
    args=parser.parse_args()
    import cv2,torch
    from ultralytics import YOLO
    torch.set_num_threads(4); cv2.setNumThreads(2)
    freeze()
    model=YOLO(str(CHECKPOINT))
    if args.stage=='development':
        segments=json.loads((BASE/'sequence_annotation_v2/count_checkpoint_v2/segments.json').read_text())
        results=[]
        for row in segments:
            result=analyze(model,Path(row['media_path']),OUT/'october_development'/row['segment_id'],False,preview=True)
            results.append(dict(segment_id=row['segment_id'],confirmed_deposits=row['confirmed_count'],
                hypotheses=result['transfer_hypothesis_count'], unresolved_tracks=result['unresolved_tracks'],
                absolute_count_difference=abs(result['transfer_hypothesis_count']-row['confirmed_count'])))
        report=dict(segments=results,confirmed_deposits=sum(r['confirmed_deposits'] for r in results),
            hypotheses=sum(r['hypotheses'] for r in results),
            mean_absolute_count_difference=sum(r['absolute_count_difference'] for r in results)/len(results),
            exact_segment_matches=sum(r['confirmed_deposits']==r['hypotheses'] for r in results),
            independent_test=False,scope='October development; some detector training sources overlap. Hypotheses omit unresolved quantities.',production_ready=False)
        save(OUT/'october_development_report.json',report)
        print(json.dumps(report),flush=True)
    else:
        source=BASE/'unseen_test_20260926/two_tank_counter_v1/indexed.mp4'
        previous=json.loads((BASE/'unseen_test_20260926/two_tank_counter_v1/blind_prediction_report.json').read_text())
        manifest=json.loads((BASE/'placement_counter_v2/carried_cheese_uncertainty_v2/manifest.json').read_text())
        assert previous['source_sha256'] not in {r['source_sha256'] for r in manifest['frames']}
        report=analyze(model,source,OUT/'september_full_video',True)
        events=json.loads((OUT/'september_full_video/events.json').read_text())
        intervals=previous['manual_tank_intervals']
        by_tank={r['tank_id']:dict(hypotheses=0,unresolved_tracks=0) for r in intervals}
        unassigned=dict(hypotheses=0,unresolved_tracks=0)
        for e in events:
            matches=[r for r in intervals if r['start_s']<=e['first_s'] and e['last_s']<=r['end_s']]
            e['tank_id']=matches[0]['tank_id'] if len(matches)==1 else None
            target=by_tank[e['tank_id']] if e['tank_id'] else unassigned
            target['hypotheses']+=e['candidate_quantity'] or 0
            target['unresolved_tracks']+=e['candidate_quantity'] is None
        save(OUT/'september_full_video/events_with_manual_tanks.json',events)
        report.update(hypotheses_by_manual_tank=by_tank,unassigned=unassigned,
            tank_intervals=intervals,tank_change_detection='manual, approximately 2-second boundaries',
            original_source_sha256=previous['source_sha256'],indexed_sha256=sha(source),
            user_tank_counts_received=False,independent_count_accuracy=None,
            training_on_test=False,threshold_tuning_on_test=False)
        save(OUT/'september_full_video/frozen_prediction_report.json',report)
        print(json.dumps(report),flush=True)


if __name__=='__main__':main()
