import pathlib,json,subprocess
from PIL import Image,ImageDraw,ImageFont
ROOT=pathlib.Path('outputs/facility_dataset');OUT=ROOT/'annotation_audit/action_review';OUT.mkdir(parents=True,exist_ok=True)
r=next(r for r in json.loads((ROOT/'annotation_audit/review_sample.json').read_text()) if r['audit_id']=='A028')
m=next(m for m in json.loads((ROOT/'media_manifest.json').read_text()) if m['sha256']==r['frame']['source_sha256'])
ff=str(pathlib.Path('work/video_decoder/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe').resolve())
indexed=pathlib.Path('work/first_action_indexed.mp4')
subprocess.run([ff,'-hide_banner','-loglevel','error','-y','-i',m['local_path'],'-map','0:v:0','-c:v','copy',str(indexed)],check=True)
start=122;duration=12
clip=OUT/'camera11_21oct_action_122_134.mp4'
subprocess.run([ff,'-hide_banner','-loglevel','error','-y','-ss',str(start),'-i',str(indexed),'-t',str(duration),'-vf','crop=640:360:800:720','-an','-c:v','libx264','-preset','fast','-crf','18',str(clip)],check=True)
subprocess.run([ff,'-hide_banner','-loglevel','error','-y','-i',str(clip),'-vf','fps=4',str(OUT/'t_%03d.jpg')],check=True)
frames=sorted(OUT.glob('t_*.jpg'));font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15)
for page in range(0,len(frames),12):
 sheet=Image.new('RGB',(1280,4*270),'white');d=ImageDraw.Draw(sheet)
 for j,p in enumerate(frames[page:page+12]):
  # 3 columns, four rows; dense temporal view plus exact relative clip times.
  x=j%3*426;y=j//3*270
  im=Image.open(p).resize((426,240));sheet.paste(im,(x,y+30))
  t=(page+j+.5)/4
  d.text((x+4,y+5),f'clip {t:.3f}s | source {start+t:.3f}s',font=font,fill='black')
 sheet.save(OUT/f'timeline_{page//12+1}.jpg',quality=94)
info={'source_sha256':m['sha256'],'source_basename':m['basename'],'camera':11,'date':m['date'],
 'source_relative_start_seconds':start,'duration_seconds':duration,'clock_verified':False,
 'crop_xyxy':[800,720,1440,1080],'label_status':'pending continuous event review',
 'important':'A visible hand does not imply a cheese placement. Label destination and release, distinguish crumb disposal, permit unknown.'}
(OUT/'clip_manifest.json').write_text(json.dumps(info,indent=2))
print('Temporal review clip and sheets ready',len(frames))
