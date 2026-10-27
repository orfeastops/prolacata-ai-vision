import pathlib,json,subprocess
from PIL import Image,ImageDraw
R=pathlib.Path('outputs/facility_dataset/temporal_pipeline/unseen_test_20260926')
D=R/'two_tank_counter_v1';D.mkdir(exist_ok=True)
rows=json.loads((R/'video_index.json').read_text())
r=next(r for r in rows if r['basename']=='Camera_11_DVR_20260926142542_20260926143911_94077690.mp4')
ff='work/video_decoder/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
subprocess.run([ff,'-loglevel','error','-y','-i',r['local_path'],'-map','0:v:0','-an','-c:v','copy',str(D/'indexed.mp4')],capture_output=True,check=True)
subprocess.run([ff,'-loglevel','error','-y','-i',str(D/'indexed.mp4'),'-vf','fps=1/30,scale=960:540','-q:v','3',str(D/'timeline_%03d.jpg')],capture_output=True,check=True)
frames=sorted(D.glob('timeline_*.jpg'))
for page in range((len(frames)+11)//12):
    sheet=Image.new('RGB',(1440,4*290),'white');d=ImageDraw.Draw(sheet)
    for j,p in enumerate(frames[page*12:(page+1)*12]):
        x=j%3*480;y=j//3*290
        sheet.paste(Image.open(p).resize((480,270)),(x,y+20))
        d.text((x+4,y+3),f'Encoded time approx {15+(page*12+j)*30}s | tank identity review only',fill='black')
    sheet.save(D/f'tank_timeline_{page+1}.jpg')
print(json.dumps({'timeline_frames':len(frames),'source':r['local_path']}))
