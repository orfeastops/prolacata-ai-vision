"""Read frozen predictions over explicit intervals; never train or alter results."""
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/facility_dataset/temporal_pipeline/placement_counter_v5/object_expansion'
def interval_count(result,start,end,tank=None):
    if not 0<=start<=end<=result['duration_processed_s']:
        raise ValueError('Interval must lie within the processed video, in elapsed seconds.')
    requested=[start,end]
    if tank is not None:
        intervals=[i for i in result['manual_tank_intervals'] if i['tank_id']==tank]
        if len(intervals)!=1:raise ValueError('Unknown tank ID')
        start=max(start,intervals[0]['start_s']);end=min(end,intervals[0]['end_s'])
    selected=[e for e in result['accepted_events'] if start<=e['time_s']<end]
    return dict(tank=tank,requested_interval_s=requested,
        effective_interval_s=[start,end] if end>start else None,
        interval_convention='start inclusive, end exclusive',
        predicted_additions=sum(e['predicted_quantity'] for e in selected),
        accepted_track_ids=[e['track_id'] for e in selected],
        unresolved_tracks=sum(start<=e['time_s']<end for e in result['unresolved_tracks']),
        time_semantics='model last-visible time is an experimental release proxy',
        user_count=None,absolute_error=None,verified_production=False)
def main():
    p=argparse.ArgumentParser();p.add_argument('--start-seconds',type=float,default=0)
    p.add_argument('--end-seconds',type=float,required=True);p.add_argument('--tank',choices=['A','B'])
    a=p.parse_args();path=OUT/'september_results.json'
    if not path.exists():raise SystemExit('Frozen full-video result is not available yet; no count fabricated.')
    result=json.loads(path.read_text(encoding='utf-8'))
    print(json.dumps(interval_count(result,a.start_seconds,a.end_seconds,a.tank),indent=2))
if __name__=='__main__':main()
