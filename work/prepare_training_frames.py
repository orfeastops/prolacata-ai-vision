import json, pathlib, zipfile, subprocess
from PIL import Image,ImageDraw
root=pathlib.Path('outputs/feta_training'); staging=root/'candidate_images';staging.mkdir(parents=True,exist_ok=True)
records=[]
ffmpeg=pathlib.Path('work/video_decoder/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe')
video=pathlib.Path('outputs/feta_pilot/filling_60s.mp4')
for sec in (0,4,8,12,16,20,24,28,32,40,48,56):
 p=staging/f'day01_s{sec:03d}.jpg'
 subprocess.run([str(ffmpeg),'-loglevel','error','-ss',str(sec),'-i',str(video),'-frames:v','1','-vf','crop=640:360:800:720','-y',str(p)],capture_output=True,check=True)
 records.append(dict(image=p.name,date='2026-10-01',split='train',source_video='Camera_11_DVR_20261001090810_20261001093612_3781498.mp4',relative_seconds=sec,crop_xyxy=[800,720,1440,1080]))
rows=json.loads(pathlib.Path('outputs/new_camera_inventory.json').read_text())
photos=sorted([r for r in rows if r['camera']==11 and r['start'].startswith('20261021') and r['extension']=='.jpg' and '060000' <= r['start'][8:] <= '130000'],key=lambda r:r['start'])
for i in range(12):
 r=photos[int(i*(len(photos)-1)/11)]
 with zipfile.ZipFile(r['archive']) as z:
  import io
  im=Image.open(io.BytesIO(z.read(r['file']))).convert('RGB')
 p=staging/f'day21_{r["start"][8:]}.jpg';im.crop((800,720,1440,1080)).save(p,quality=95)
 records.append(dict(image=p.name,date='2026-10-21',split='val',source_archive=r['archive'],source_image=r['file'],crop_xyxy=[800,720,1440,1080]))
(root/'frame_manifest.json').write_text(json.dumps(records,indent=2))
for group in range(2):
 rs=records[group*12:(group+1)*12];sheet=Image.new('RGB',(1920,400*4),'white')
 for i,r in enumerate(rs):
  im=Image.open(staging/r['image']);tile=Image.new('RGB',(640,400),'white');tile.paste(im,(0,30));ImageDraw.Draw(tile).text((5,5),r['image'],fill='black');sheet.paste(tile,((i%3)*640,(i//3)*400))
 sheet.save(root/f'candidate_sheet_{group+1}.jpg')
print('Prepared',len(records),'candidate crops; no labels yet.')
