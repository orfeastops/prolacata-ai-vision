"""Finalize only the requested short window from an interrupted owned extraction."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,zipfile,io,msvcrt,os
import av
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];B=R/'outputs/tank_transfer_training_v1/dataset_v2'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def save(p,d):p.write_text(json.dumps(d,indent=2),encoding='utf8')
lock=(B/'extraction.lock').open('a+b');lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
f=read(B/'next_dense_followup.json');assert f['source_id']=='346272a0dde746f6' and f['date']=='20261025'
m=read(B/f['manifest']);assert m['split']=='train'
o=B/'dense_review/20261025_cam11_346272a0dde746f6_door';assert not (o/'frames.json').exists()
end=min(m['decoded_last_relative_pts'],m['samples'][2]['relative_pts']+10)
old=read(B/'targeted_dense_progress.json');old.update(status='interrupted_owned_worker_to_restrict_window',scope_error='Full source end was queued instead of short event window; extra candidates are retained unreviewed, not approved.')
save(B/'targeted_dense_scope_correction.json',old)
f.update(end_relative_pts=end,status='restricted_window_metadata_recovery');save(B/'next_dense_followup.json',f)
state=dict(status='recovering_short_window',pid=os.getpid(),source_id=f['source_id'],output=str(o.relative_to(B)),errors=[]);save(B/'targeted_dense_progress.json',state)
try:
 with zipfile.ZipFile(m['source']['archive']) as z:data=z.read(m['source']['member'])
 assert hashlib.sha256(data).hexdigest()==m['source_sha256']
 ss=[];origin=None;tick=0;last=None
 with av.open(io.BytesIO(data)) as c:
  stream=c.streams.video[0];stream.codec_context.thread_count=2
  for fr in c.decode(stream):
   if fr.time is None:continue
   t=float(fr.time)
   if origin is None:origin=t
   rel=t-origin;last=rel
   if rel>end:break
   if rel+1e-6<tick:continue
   p=o/f'{len(ss):05d}.jpg';buf=io.BytesIO();fr.to_image().save(buf,format='JPEG',quality=93);expected=hashlib.sha256(buf.getvalue()).hexdigest()
   assert p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()==expected,'Existing candidate does not match decoded source frame'
   ss.append(dict(image=str(p.relative_to(R)),sha256=expected,relative_pts=rel,source_pts=t,review_status='unreviewed'));tick=rel+2
 extras=[p for p in sorted(o.glob('[0-9]*.jpg')) if int(p.stem)>=len(ss)]
 save(o/'unreviewed_extra_files.json',dict(status='outside_requested_window_unreviewed_unindexed',count=len(extras),note='Retained from interrupted over-wide extraction. Exact PTS not reconstructed; these files are excluded from approved labels and reviewed sample counts.',images=[dict(image=str(p.relative_to(R)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in extras]))
 save(o/'frames.json',dict(source=m['source'],source_sha256=m['source_sha256'],split='train',requested_start_relative_pts=0,requested_end_relative_pts=end,decoded_through_relative_pts=last,sampling='Sequential short-window PTS sampling every2 seconds; source frame bytes independently reverified against retained candidates.',samples=ss,labels_approved=False,outside_window_unreviewed_manifest='unreviewed_extra_files.json'))
 for start in range(0,len(ss),16):
  out=Image.new('RGB',(1600,1000),'#222');d=ImageDraw.Draw(out)
  for j,s in enumerate(ss[start:start+16]):
   im=Image.open(R/s['image']);im.thumbnail((400,225));x=j%4*400;y=j//4*250;out.paste(im,(x,y));d.text((x+3,y+227),f'{start+j} PTS+{s["relative_pts"]:.1f}',fill='white')
  out.save(o/f'sheet_{start}.jpg')
 state.update(status='extraction_finished_visual_review_pending',candidate_samples=len(ss),retained_outside_window_unreviewed=len(extras),completed_at=datetime.now(timezone.utc).isoformat());save(B/'targeted_dense_progress.json',state);print(json.dumps(state))
finally:lock.close()
