import av,json,time,msvcrt
from pathlib import Path
from fractions import Fraction

base=Path('D:/Codex/tank-storage')
outdir=base/'review_proxies';outdir.mkdir(exist_ok=True)
lock=(outdir/'encode.lock').open('a+b');lock.seek(0);lock.write(b'0');lock.flush();lock.seek(0)
msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
plan=json.loads((base/'one_hour_plan.json').read_text(encoding='utf-8'))
status={'status':'running','completed':[],'started':time.time()}
def save():
    (outdir/'status.json').write_text(json.dumps(status,indent=2),encoding='utf-8')
try:
    for item in plan['files']:
        idx=item['index'];source=Path(item['source']);dest=outdir/f'clip_{idx:03d}.mp4'
        status['active_clip']=idx;save()
        if not dest.exists():
            temp=outdir/f'clip_{idx:03d}.partial.mp4'
            inp=av.open(str(source));inp.streams.video[0].thread_type='AUTO';inp.streams.video[0].codec_context.thread_count=4
            out=av.open(str(temp),'w',options={'movflags':'frag_keyframe+empty_moov'})
            stream=out.add_stream('libx264',rate=inp.streams.video[0].average_rate or 15)
            stream.width=1280;stream.height=720;stream.pix_fmt='yuv420p'
            stream.codec_context.thread_count=4
            stream.options={'preset':'ultrafast','crf':'22','tune':'zerolatency'}
            origin=None;last=-1;n=0;skipped=[]
            for frame in inp.decode(video=0):
                t=float(frame.time)
                if origin is None:origin=t
                pts=round((t-origin)*90000)
                if pts<=last:
                    skipped.append({'source_seconds':t,'reason':'non-increasing PTS omitted from browser proxy only'})
                    continue
                last=pts
                f=frame.reformat(width=1280,height=720,format='yuv420p');f.pts=pts;f.time_base=Fraction(1,90000)
                for packet in stream.encode(f):out.mux(packet)
                n+=1
                if n%1500==0:status.update(frames=n,video_seconds=t-origin);save()
            for packet in stream.encode():out.mux(packet)
            out.close();inp.close()
            with av.open(str(temp)) as check:
                assert check.streams.video[0].codec_context.name=='h264'
                assert next(check.decode(video=0)).width==1280
            temp.rename(dest)
            (outdir/f'clip_{idx:03d}_timing.json').write_text(json.dumps({'source':str(source),'origin_seconds':origin,'frames':n,'omitted_nonincreasing_pts':skipped,'note':'Review proxy only; original video and inference unchanged. Use visible DVR clock for annotations.'},indent=2),encoding='utf-8')
        page=base/'hour_manual_review.html'
        html=page.read_text(encoding='utf-8').replace(source.as_uri(),dest.as_uri())
        page.write_text(html,encoding='utf-8')
        status['completed'].append(idx);save()
        print(f'Ready clip {idx:03d}',flush=True)
    status['status']='complete';save()
except Exception as e:
    status.update(status='error',error=str(e));save();raise
