"""Append inspected native crops without regenerating prior annotations."""
import hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]; BASE=ROOT/'outputs/tank_transfer_training_v1'; DET=BASE/'detector_v1'
CHOICES=[
 ('20261015','origin_scan_0951_cam11',38,[435,225,535,330]),
 ('20261015','origin_scan_0951_cam11',2,[420,175,535,275]),
 ('20261015','origin_scan_0951_cam11',27,[375,365,530,520]),
 ('20261015','early_storage_1001_cam15',2,[605,46,680,120]),
 ('20261015','early_storage_1002_cam15',14,[461,69,535,145]),
 ('20261015','origin_scan_0951_cam11',38,[190,181,287,265]),
]

def main():
 p=DET/'candidate_manifest.json'; manifest=json.loads(p.read_text('utf8')); existing={r['id']:r for r in manifest['records']}; rows=[]
 for num,(day,window,index,roi) in zip(range(152,158),CHOICES):
  ident=f'{num:03d}'; mp=BASE/'dataset_v1/sequence_review'/day/window/'frames.json'; m=json.loads(mp.read_text('utf8')); s=m['samples'][index]
  assert m['source']['date']==day and m['source']['split']=='train'
  if ident in existing:
   r=existing[ident]; assert r['source_frame_sha256']==s['image_sha256'] and r['roi_on_960x540']==roi; rows.append(r); continue
  im=Image.open(ROOT/s['image']); assert im.size==(1920,1080); crop=im.crop(tuple(v*2 for v in roi)); target=DET/'candidates'/(ident+'.jpg'); assert not target.exists(); crop.save(target,quality=96)
  r=dict(id=ident,date=day,camera=m['source']['camera'],split='train',source=m['source']['member'],source_sha256=m['source_sha256'],source_pts_seconds=s['source_pts_seconds'],relative_pts_seconds=s['relative_pts_seconds'],source_frame=s['image'],source_frame_sha256=s['image_sha256'],frames_manifest=str(mp.relative_to(ROOT)),sample_index=index,event_reference=None,image=str(target.relative_to(ROOT)),sha256=hashlib.sha256(target.read_bytes()).hexdigest(),roi_on_960x540=roi,width=crop.width,height=crop.height,object_class='tank',annotation_status='unreviewed',provenance='Native chronological context inspected. Crop and proposed boxes require separate overlay review.')
  rows.append(r); manifest['records'].append(r)
 p.write_text(json.dumps(manifest,indent=2),encoding='utf8')
 sheet=Image.new('RGB',(1080,720),'#202020'); d=ImageDraw.Draw(sheet)
 for i,r in enumerate(rows):
  x=i%3*360; y=i//3*360; sheet.paste(Image.open(ROOT/r['image']),(x,y+30)); d.text((x+4,y+5),r['id'],fill='white')
 sheet.save(DET/'sheets/candidate_batch18.jpg',quality=96)
 print(json.dumps(dict(candidate_count=len(manifest['records']),new_ids=[r['id'] for r in rows])))
if __name__=='__main__': main()
