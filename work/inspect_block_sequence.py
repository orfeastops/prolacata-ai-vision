import sys,json,zipfile,pathlib,subprocess
sys.path.insert(0,'work/video_decoder')
import imageio_ffmpeg
from PIL import Image,ImageDraw
rows=json.loads(pathlib.Path('outputs/new_camera_inventory.json').read_text())
r=next(r for r in rows if r['start']=='20261001090810' and r['extension']=='.mp4')
p=pathlib.Path('work/new_samples')/pathlib.Path(r['file']).name
with zipfile.ZipFile(r['archive']) as z:p.write_bytes(z.read(r['file']))
dest=pathlib.Path('work/block_frames');dest.mkdir(exist_ok=True)
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-loglevel','error','-i',str(p),'-t','18','-vf','fps=1','-y',str(dest/'block_%03d.jpg')],check=True,capture_output=True)
frames=sorted(dest.glob('block_*.jpg'))
sheet=Image.new('RGB',(1800,420*((len(frames)+2)//3)),'white')
for i,f in enumerate(frames):
 im=Image.open(f);w,h=im.size
 im=im.crop((int(w*.38),int(h*.50),w,h));im.thumbnail((600,390))
 tile=Image.new('RGB',(600,420),'white');tile.paste(im,(0,25));ImageDraw.Draw(tile).text((5,5),f'Camera 11 | clip 01/10 09:08:10 | sample {i+1}',fill='black');sheet.paste(tile,((i%3)*600,(i//3)*420))
sheet.save('outputs/block_placement_sequence.jpg')
print('Extracted',len(frames),'successive frames from',r['file'])

