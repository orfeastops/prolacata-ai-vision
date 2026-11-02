import av, hashlib, json
from pathlib import Path
from PIL import Image, ImageDraw
root=Path(__file__).resolve().parents[1]
base=root/'outputs/tank_transfer_training_v1'
out=base/'dataset_v1/remote_export_audit'
out.mkdir(exist_ok=True)
manifest=[]
for folder in ['Camera_15_DVR_DVR_20261031180252','Camera_15_DVR_DVR_20261031181453']:
 for p in sorted((base/folder).glob('*.mp4')):
  times=[]
  with av.open(str(p)) as c:
   for f in c.decode(video=0): times.append(float(f.time))
  indices=sorted(set([0,min(25,len(times)-1),len(times)//2,len(times)-1]))
  frames={}
  with av.open(str(p)) as c:
   for i,f in enumerate(c.decode(video=0)):
    if i in indices: frames[i]=(float(f.time),f.to_image())
  sheet=Image.new('RGB',(960,560*len(indices)),'white'); d=ImageDraw.Draw(sheet)
  samples=[]
  for row,i in enumerate(indices):
   t,im=frames[i]; im.thumbnail((960,540));sheet.paste(im,(0,row*560+20));d.text((5,row*560),f'{p.name} frame={i} PTS={t}',fill='black');samples.append({'frame':i,'pts':t})
  dest=out/(p.stem+'.jpg');sheet.save(dest)
  manifest.append({'source':str(p.relative_to(root)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'decoded_frames':len(times),'first_pts':times[0],'last_pts':times[-1],'sheet':str(dest.relative_to(root)),'samples':samples})
(out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
print(json.dumps(manifest,indent=2))
