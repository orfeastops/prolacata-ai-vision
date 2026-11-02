"""Record a specific visually established correction, retaining the original audit."""
import json, shutil
from fractions import Fraction
from pathlib import Path
import av
from PIL import Image, ImageDraw

root=Path('outputs/tank_door_audit')
dest=root/'recheck_20261030'
dest.mkdir(exist_ok=True)
review=root/'reviewed_20261021.json'
backup=dest/'reviewed_20261021_before_correction.json'
if not backup.exists():
    shutil.copy2(review,backup)
doc=json.loads(review.read_text(encoding='utf-8'))
g=json.loads((root/'proposals/20261021/proposals.json').read_text())[257]
event={
    'proposal_id':g['id'], 'basename':g['basename'], 'source':g['source'],
    'candidate_start':g['start'],'candidate_end':g['end'],
    'camera_clock_crossing_interval':'10:51:10-10:51:16',
    'load':'production_cheese','direction':'outbound',
    'visual_review':'Rechecked chronological 2-second full-scene frames. Workers finish filling the gray tank. It leaves filling station at about 10:51:04 and crosses the doorway around 10:51:10–16. A different empty beige tank replaces it. This is an additional production exit, not a return or scrap tank.',
    'evidence_sheet':'event_review/20261021/257.jpg',
    'camera15_match':'no_overlap',
    'note':'Added after recheck on 2026-10-30. Omitted in the original assistant visual audit (44). No camera15 frames in the selected matching window; final storage has not been separately verified.',
    'recheck_evidence':['recheck_20261030/missing1051/sheet00.jpg','recheck_20261030/missing1051/sheet01.jpg','recheck_20261030/missing1051/sheet02.jpg'],
    'evidence_video':'recheck_20261030/extra_exit_105110.mp4',
}
if not any(e['proposal_id']==g['id'] for e in doc['events']):
    doc['events'].append(event)
doc['events'].sort(key=lambda e:e['camera_clock_crossing_interval'])
doc['observed_production_exits']=sum(e['load']=='production_cheese' for e in doc['events'])
doc['observed_loaded_outbound']=len(doc['events'])
correction=dict(date='2026-10-21',review_date='2026-10-30',original_assistant_visual_count=44,
               user_suggested_total=45,revised_assistant_visual_count=doc['observed_production_exits'],
               added_event=event,reason='A real outbound tank crossing was omitted during the original visual review.',
               limitations='This corrects an assistant visual audit, not an automatic model prediction or independent accuracy evaluation. Camera15 storage is not established for this added event.')
doc['recheck_20261030']={k:v for k,v in correction.items() if k!='added_event'}
review.write_text(json.dumps(doc,indent=2,ensure_ascii=False),encoding='utf-8')
clocks=root/'20261021_clock_notes.json'
notes=json.loads(clocks.read_text())
notes['257']='10:51:10-10:51:16'
clocks.write_text(json.dumps(dict(sorted(notes.items(),key=lambda x:int(x[0]))),indent=2),encoding='utf-8')
(dest/'correction.json').write_text(json.dumps(correction,indent=2,ensure_ascii=False),encoding='utf-8')

clip=dest/'extra_exit_105110.mp4'
if not clip.exists():
    # Continuous decoded original frames, no inferred or generated scene content.
    start,end=350.0,430.0
    inp=av.open(g['source']); stream=inp.streams.video[0]
    stream.thread_type='AUTO';stream.codec_context.thread_count=2
    out=av.open(str(clip),'w',options={'movflags':'+faststart'})
    enc=out.add_stream('libx264',rate=15)
    enc.width=960; enc.height=540; enc.pix_fmt='yuv420p'
    enc.options={'crf':'23','preset':'fast'}
    enc.time_base=Fraction(1,90000)
    base=None;origin=None;n=0
    for f in inp.decode(stream):
        if f.time is None:continue
        if base is None:base=float(f.time)
        t=float(f.time)-base
        if t<start:continue
        if t>end:break
        if origin is None:origin=t
        frame=f.reformat(width=960,height=540,format='yuv420p')
        frame.pts=round((t-origin)*90000);frame.time_base=Fraction(1,90000)
        for packet in enc.encode(frame):out.mux(packet)
        n+=1
    for packet in enc.encode():out.mux(packet)
    out.close();inp.close()
    check=av.open(str(clip));count=sum(1 for _ in check.decode(video=0));duration=check.duration/1e6;check.close()
    assert count==n and duration>75,(count,n,duration)
    (dest/'video_verification.json').write_text(json.dumps(dict(frames=count,duration_seconds=duration,source=g['source'],source_pts_interval=[start,end],audio=False),indent=2))

# Four unambiguous full-scene stills, with the original camera clock visible.
scan=json.loads((root/Path(g['peak']['image']).parent/'scan.json').read_text())
sheet=Image.new('RGB',(1920,1160))
for j,t in enumerate([392.423,398.423,404.423,410.423]):
    f=min(scan['candidates'],key=lambda f:abs(f['t']-t))
    im=Image.open(root/f['image']).resize((960,540))
    tile=Image.new('RGB',(960,580));tile.paste(im,(0,40))
    ImageDraw.Draw(tile).text((10,10),f"Camera 11 | source PTS {f['t']:.3f} seconds",fill='white')
    sheet.paste(tile,((j%2)*960,(j//2)*580))
sheet.save(dest/'extra_exit_evidence.jpg')
print(json.dumps({'revised_count':doc['observed_production_exits'],'added_event':g['id'],'video':str(clip.resolve())}))
