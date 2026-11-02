"""Bounded local validation clip with original relative timestamps."""
import json,hashlib,zipfile,io,msvcrt
from pathlib import Path
from fractions import Fraction
import av
R=Path(__file__).resolve().parents[1];B=R/'outputs/tank_transfer_training_v1/dataset_v2'
P=B/'counting_validation'; ref=json.loads((P/'val_001.json').read_text())
assert ref['date']=='20261017' and ref['split']=='val'
lock=(B/'extraction.lock').open('a+b');lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
dest=P/'val_001.mp4';assert not dest.exists(),'Do not overwrite existing clip'
source=ref['source'];start,end=ref['relative_pts_interval']
with zipfile.ZipFile(source['archive']) as z:data=z.read(source['member'])
assert hashlib.sha256(data).hexdigest()==ref['source_sha256']
times=[];origin=None
with av.open(io.BytesIO(data)) as inp, av.open(str(dest),'w') as out:
    stream=out.add_stream('libx264',rate=25);stream.width=1920;stream.height=1080;stream.pix_fmt='yuv420p';stream.time_base=Fraction(1,1000000);stream.options={'crf':'18','preset':'veryfast'}
    inp.streams.video[0].codec_context.thread_count=2
    for frame in inp.decode(video=0):
        if frame.time is None:continue
        t=float(frame.time)
        if origin is None:origin=t
        rel=t-origin
        if rel>end+1e-6:break
        if rel<start-1e-6:continue
        times.append(rel);frame.pts=round((rel-start)*1000000);frame.time_base=Fraction(1,1000000)
        for packet in stream.encode(frame):out.mux(packet)
    for packet in stream.encode():out.mux(packet)
decoded=[]
with av.open(str(dest)) as c:
    for f in c.decode(video=0):decoded.append(float(f.time))
assert len(decoded)==len(times)>0
assert max(abs(a-(b-start)) for a,b in zip(decoded,times))<0.002
assert all(a<b for a,b in zip(decoded,decoded[1:]))
report=dict(status='clip_export_verified',file='val_001.mp4',sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),frames=len(times),source_relative_pts=times,output_relative_pts=decoded,max_timestamp_error_seconds=max(abs(a-(b-start)) for a,b in zip(decoded,times)),source_sha256=ref['source_sha256'],manual_count_reference='val_001.json',labels_for_every_video_frame=False,all_frames_visually_reviewed=False,training_use=False)
(P/'val_001_clip_manifest.json').write_text(json.dumps(report,indent=2))
ref.update(status='manual_sampled_reference_with_verified_video_clip',video='val_001.mp4',video_manifest='val_001_clip_manifest.json');(P/'val_001.json').write_text(json.dumps(ref,indent=2))
lock.close();print(json.dumps({k:v for k,v in report.items() if k not in ['source_relative_pts','output_relative_pts']}))
