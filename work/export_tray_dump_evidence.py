import json, subprocess, cv2
from pathlib import Path
root=Path.cwd()
out=root/'outputs/tray_dump_evidence';out.mkdir(exist_ok=True)
ff=root/'work/video_decoder/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
records=json.loads((root/'outputs/camera_video_collection/inventory.json').read_text())['records']
events=[]
for name,start,end,label in [
 ('Camera_11_DVR_20261001135328_20261001135855_117680788.mp4',175,204,'oct01'),
 ('Camera_11_DVR_20261021141803_20261021142941_2899458.mp4',560,628,'oct21')]:
 source=next(r['source'] for r in records if r['basename']==name)
 dest=out/f'{label}_cheese_to_scrap.webm'
 reader=cv2.VideoCapture(source)
 writer=cv2.VideoWriter(str(dest),cv2.VideoWriter_fourcc(*'VP80'),12.5,(1280,720))
 assert writer.isOpened()
 tick=float(start)
 while reader.grab():
  t=reader.get(cv2.CAP_PROP_POS_MSEC)/1000
  if t>end:break
  if t<tick:continue
  ok,frame=reader.retrieve()
  if not ok:continue
  frame=cv2.resize(frame,(1280,720))
  while tick<=t and tick<end:
   writer.write(frame);tick+=.08
 reader.release();writer.release()
 cap=cv2.VideoCapture(str(dest));ok,frame=cap.read()
 assert ok, dest
 cv2.imwrite(str(out/f'{label}_first_frame.jpg'),frame)
 events.append(dict(source=source,clip=str(dest),source_start_seconds=start,source_end_seconds=end,frames=cap.get(cv2.CAP_PROP_FRAME_COUNT),fps=cap.get(cv2.CAP_PROP_FPS),observation='Whole cheese blocks transferred individually from conveyor tray to scrap tank. Plastic tray itself is not discarded.'))
 cap.release()
 print(label,'complete',flush=True)
(out/'findings.json').write_text(json.dumps(dict(events=events,scope='83 late-day camera11 source videos on September26, October1 and October21; 912 coarse samples at approximately 8-second spacing, followed by 1-second visual review of candidate intervals. Not exhaustive continuous review of all footage; absence of other events is not established.'),indent=2),encoding='utf-8')
