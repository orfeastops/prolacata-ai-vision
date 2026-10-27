import sys,json,pathlib,zipfile,shutil,subprocess
sys.path.insert(0,'work/python_packages')
import imageio_ffmpeg
from PIL import Image,ImageDraw
rows=json.loads(pathlib.Path('outputs/camera_inventory.json').read_text())
selected=[]
for day in sorted({r['start'][:10] for r in rows if r['camera']==15}):
    selected.extend(sorted([r for r in rows if r['camera']==15 and r['start'].startswith(day)],key=lambda r:r['start'])[-2:])
tiles=[]
with zipfile.ZipFile(r'C:\Users\evant\Desktop\cameradata.zip') as z:
    for i,r in enumerate(selected):
        p=pathlib.Path('work/samples')/r['file']
        if not p.exists():
            with z.open(r['file']) as src,p.open('wb') as dst: shutil.copyfileobj(src,dst)
        for j,sec in enumerate((5,max(6,r['seconds']-12))):
            out=pathlib.Path(f'work/samples/late15_{i}_{j}.jpg')
            result=subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-loglevel','error','-i',str(p),'-ss',str(sec),'-frames:v','1','-y',str(out)],capture_output=True)
            if result.returncode or not out.exists():
                print('Failed',r['file'],sec);continue
            im=Image.open(out).convert('RGB');im.thumbnail((960,540))
            tile=Image.new('RGB',(960,570),'white');tile.paste(im,(0,30))
            ImageDraw.Draw(tile).text((8,8),f"Camera 15 | filename start {r['start']} | +{sec:.0f}s",fill='black');tiles.append(tile)
sheet=Image.new('RGB',(1920,570*((len(tiles)+1)//2)),'white')
for i,t in enumerate(tiles):sheet.paste(t,((i%2)*960,(i//2)*570))
sheet.save('outputs/camera15_late_samples.jpg')
print('Saved',len(tiles),'frames from the latest available clips on each date')
