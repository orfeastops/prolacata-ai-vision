import json,zipfile,pathlib,io
from PIL import Image,ImageDraw
root=pathlib.Path('outputs/feta_training');dest=root/'extra_images';dest.mkdir(exist_ok=True)
rows=json.loads(pathlib.Path('outputs/new_camera_inventory.json').read_text())
photos=sorted([r for r in rows if r['camera']==11 and r['start'].startswith('20261001') and r['extension']=='.jpg' and '060000'<=r['start'][8:]<='133000'],key=lambda r:r['start'])
records=[]
for i in range(12):
 r=photos[int(i*(len(photos)-1)/11)]
 with zipfile.ZipFile(r['archive']) as z:im=Image.open(io.BytesIO(z.read(r['file']))).convert('RGB').crop((800,720,1440,1080))
 name=f'day01_extra_{r["start"][8:]}.jpg';im.save(dest/name,quality=95)
 records.append(dict(image=name,date='2026-10-01',split='train',source_archive=r['archive'],source_image=r['file'],crop_xyxy=[800,720,1440,1080]))
(root/'extra_manifest.json').write_text(json.dumps(records,indent=2))
for page in range(3):
 sheet=Image.new('RGB',(1280,800),'white')
 for j,r in enumerate(records[page*4:(page+1)*4]):
  tile=Image.new('RGB',(640,400),'white');tile.paste(Image.open(dest/r['image']),(0,30));ImageDraw.Draw(tile).text((5,5),r['image'],fill='black');sheet.paste(tile,((j%2)*640,(j//2)*400))
 sheet.save(root/f'extra_candidates_{page+1}.jpg')
print([r['image'] for r in records])
