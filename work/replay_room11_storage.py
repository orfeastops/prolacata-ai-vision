"""Development-only association replay from cached detections; no inference."""
import argparse,json
from pathlib import Path
import numpy as np
import cv2,av
from run_room11_storage import TankLinker,PresenceCounter,PAYLOAD_CONFIG,save,digest

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--out',required=True)
    p.add_argument('--video')
    a=p.parse_args();root=Path(a.run);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    if (out/'result.json').exists():raise RuntimeError('Do not overwrite previous replay')
    cv2.setNumThreads(1)
    pc=PresenceCounter(dict(PAYLOAD_CONFIG));tc=TankLinker();seen=0;links=[];lastsave=-100
    video=av.open(a.video) if a.video else None
    if video:video.streams.video[0].codec_context.thread_count=2
    frames=iter(video.decode(video=0)) if video else None
    origin=None
    if video:
        first=next(frames);origin=float(first.time)
        with (root/'observations.jsonl').open() as handle:start=json.loads(next(handle))['pts_s']
        video.seek(int((origin+max(0,start-60))*av.time_base))
        frames=iter(video.decode(video=0))
    for line in (root/'observations.jsonl').open():
        r=json.loads(line);t=r['pts_s'];gray=None
        if frames is not None:
            while True:
                f=next(frames)
                if f.time is None:continue
                if origin is None:origin=float(f.time)
                if float(f.time)-origin>=t-.001:break
            assert abs(float(f.time)-origin-t)<.01
            gray=cv2.cvtColor(cv2.resize(f.to_ndarray(format='bgr24'),(640,360)),cv2.COLOR_BGR2GRAY)
        tc.step(t,[np.array(b) for b in r['tanks'].values()],gray)
        pc.step(t,r['payload'])
        for e in pc.events[seen:]:
            i=tc.placement(e,t);links.append(dict(event=e,tank_track=i));seen+=1
        if t-lastsave>5:
            save(out/'progress.json',dict(pts_s=t,placements=seen,exits=len(tc.exits)))
            lastsave=t
    pc.finish(t)
    if video:video.close()
    old=json.loads((root/'result.json').read_text())
    for e in tc.exits:
        candidates=[v for v in old['exits'] if abs(v['pts_s']-e['pts_s'])<.2]
        if len(candidates)==1:
            import shutil
            for k in ['evidence','clock_evidence']:
                e[k]=candidates[0][k];shutil.copyfile(root/e[k],out/e[k])
    save(out/'result.json',dict(status='development_cached_replay',exits=tc.exits,links=links,
        unlinked_placements=tc.unlinked,storage_proposals=sum(bool(e['placement_evidence']) for e in tc.exits),
        code_sha256=digest(Path(__file__).with_name('run_room11_storage.py')),
        source_predictions=str(root),production_ready=False))
    print(json.dumps({'exits':len(tc.exits),'storage_proposals':sum(bool(e['placement_evidence']) for e in tc.exits),'links':[v['tank_track'] for v in links]}))

if __name__=='__main__':main()
