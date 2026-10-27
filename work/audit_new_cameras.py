import zipfile,re,json,pathlib,collections
from PIL import Image,ImageDraw
sources=[r'C:\Users\evant\Desktop\wetransfer_1-10-2026-camera15_2026-10-22_1742.zip',r'C:\Users\evant\Desktop\wetransfer_camera11-1-10-2026_2026-10-22_1825.zip']
rows=[]; samples=pathlib.Path('work/new_samples');samples.mkdir(exist_ok=True)
for source in sources:
 with zipfile.ZipFile(source) as z:
  for e in z.infolist():
   m=re.search(r'Camera_(\d+)_DVR_(\d{14})_(\d{14})',e.filename)
   if m and pathlib.Path(e.filename).suffix.lower() in ('.mp4','.jpg','.png'):
    c,a,b=m.groups();rows.append(dict(archive=source,file=e.filename,camera=int(c),start=a,end=b,extension=pathlib.Path(e.filename).suffix.lower(),bytes=e.file_size))
pathlib.Path('outputs/new_camera_inventory.json').write_text(json.dumps(rows,indent=2))
groups=collections.defaultdict(list)
for r in rows:groups[(r['start'][:8],r['camera'])].append(r)
tiles=[]
for key,rs in sorted(groups.items()):
 print(key,dict(collections.Counter(r['extension'] for r in rs)), 'range',min(r['start'] for r in rs),max(r['end'] for r in rs))
 photos=sorted([r for r in rs if r['extension'] in ('.jpg','.png')],key=lambda r:r['start'])
 for n in sorted(set([0,len(photos)//2,len(photos)-1])) if photos else []:
  r=photos[n]
  with zipfile.ZipFile(r['archive']) as z: data=z.read(r['file'])
  target=samples/pathlib.Path(r['file']).name;target.write_bytes(data)
  im=Image.open(target).convert('RGB');im.thumbnail((960,540))
  tile=Image.new('RGB',(960,570),'white');tile.paste(im,(0,30));ImageDraw.Draw(tile).text((6,6),f"Camera {r['camera']} | filename {r['start']}",fill='black');tiles.append(tile)
if tiles:
 sheet=Image.new('RGB',(1920,570*((len(tiles)+1)//2)),'white')
 for i,t in enumerate(tiles):sheet.paste(t,((i%2)*960,(i//2)*570))
 sheet.save('outputs/new_camera_samples.jpg')
print('Media files',len(rows))
