"""Append four native crops from the visually reviewed second13Oct cycle."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'outputs/tank_transfer_training_v1'
OUT = BASE/'detector_v1'

def main():
    path = OUT/'candidate_manifest.json'
    manifest = json.loads(path.read_text('utf8'))
    existing = {r['id']:r for r in manifest['records']}
    choices = [
        ('next_origin_1055_cam11',30,[420,405,580,540]),
        ('gray_departure_1056_cam11',10,[460,85,585,250]),
        ('gray_scale_cam11_1057',46,[480,80,560,160]),
        ('next_origin_1055_cam11',44,[330,270,475,440]),
    ]
    rows=[]
    for n,(window,index,roi) in enumerate(choices,90):
        ident=f'{n:03d}'
        mp=BASE/'dataset_v1/sequence_review/20261013'/window/'frames.json'
        meta=json.loads(mp.read_text('utf8')); s=meta['samples'][index]
        assert meta['source']['split']=='train' and meta['source']['date']=='20261013'
        if ident in existing:
            assert existing[ident]['source_frame_sha256']==s['image_sha256']
            assert existing[ident]['roi_on_960x540']==roi
            rows.append(existing[ident]); continue
        native=Image.open(ROOT/s['image']); assert native.size==(1920,1080)
        target=OUT/'candidates'/(ident+'.jpg'); assert not target.exists()
        crop=native.crop(tuple(v*2 for v in roi)); crop.save(target,quality=96)
        r=dict(id=ident,date='20261013',camera=11,split='train',source=meta['source']['member'],
            source_sha256=meta['source_sha256'],source_pts_seconds=s['source_pts_seconds'],
            relative_pts_seconds=s['relative_pts_seconds'],source_frame=s['image'],source_frame_sha256=s['image_sha256'],
            frames_manifest=str(mp.relative_to(ROOT)),sample_index=index,event_reference=None,
            image=str(target.relative_to(ROOT)),sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
            roi_on_960x540=roi,width=crop.width,height=crop.height,
            provenance='Native crop after chronological cycle review; ROI object annotation only.',
            annotation_status='unreviewed',object_class='tank')
        manifest['records'].append(r); rows.append(r)
    path.write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf8')
    sheet=Image.new('RGB',(800,820),'#202020'); d=ImageDraw.Draw(sheet)
    for k,r in enumerate(rows):
        x,y=k%2*400,k//2*410
        sheet.paste(Image.open(ROOT/r['image']),(x,y+30));d.text((x+4,y+5),r['id'],fill='white')
    sheet.save(OUT/'sheets/candidate_batch06.jpg',quality=96)
    print(json.dumps(dict(candidate_count=len(manifest['records']),new_ids=[r['id'] for r in rows])))

if __name__=='__main__':main()
