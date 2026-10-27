import sys, json, zipfile, pathlib, subprocess
sys.path.insert(0, str(pathlib.Path('work/python_packages').resolve()))
import imageio_ffmpeg
from PIL import Image, ImageDraw

root = pathlib.Path('work/samples')
root.mkdir(parents=True, exist_ok=True)
rows = json.loads(pathlib.Path('outputs/camera_inventory.json').read_text())
selected = []
for camera in (11,15):
    group = sorted([r for r in rows if r['camera']==camera],key=lambda r:r['start'])
    selected.extend([group[0], max(group,key=lambda r:r['seconds']),group[len(group)//2]])
ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
tiles=[]
with zipfile.ZipFile(r'C:\Users\evant\Desktop\cameradata.zip') as archive:
    for i,row in enumerate(selected):
        video=root/row['file']
        if not video.exists():
            with archive.open(row['file']) as src,video.open('wb') as dst:
                import shutil
                shutil.copyfileobj(src,dst)
        for j,seconds in enumerate((5,15,30)):
            target=root/f'frame_{i}_{j}.jpg'
            subprocess.run([ffmpeg,'-loglevel','error','-i',str(video),'-ss',str(min(seconds,row['seconds']*0.8)),'-frames:v','1','-y',str(target)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
            im=Image.open(target).convert('RGB'); im.thumbnail((640,360))
            tile=Image.new('RGB',(640,400),'white'); tile.paste(im,(0,30))
            ImageDraw.Draw(tile).text((5,5),f"Camera {row['camera']} | {row['start']} | +{min(seconds,row['seconds']*0.8):.0f}s",fill='black')
            tiles.append(tile)
sheet=Image.new('RGB',(1920,400*len(selected)),'#ddd')
for k,tile in enumerate(tiles):sheet.paste(tile,((k%3)*640,(k//3)*400))
sheet.save('outputs/camera_samples.jpg')
print('Saved contact sheet and',len(tiles),'sample frames')
