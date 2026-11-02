"""Append native10Oct crops without resetting the curated manifest."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/tank_transfer_training_v1'
DET=BASE/'detector_v1'
CHOICES=[
    ('screening_1022_cam11',4,[340,195,440,350]),
    ('screening_1022_cam11',38,[420,150,575,280]),
    ('screening_1021_cam15',18,[465,78,635,155]),
    ('screening_1022_cam11',4,[420,405,590,540]),
    ('screening_1022_cam11',4,[565,315,710,460]),
    ('candidate_1050_cam15',12,[680,45,855,145]),
]

def main():
    path=DET/'candidate_manifest.json'
    manifest=json.loads(path.read_text('utf8'))
    existing={r['id']:r for r in manifest['records']}
    rows=[]
    for ident,(window,index,roi) in zip(range(94,100),CHOICES):
        ident=f'{ident:03d}'
        mp=BASE/'dataset_v1/sequence_review/20261010'/window/'frames.json'
        meta=json.loads(mp.read_text('utf8')); s=meta['samples'][index]
        assert meta['source']['split']=='train' and meta['source']['date']=='20261010'
        if ident in existing:
            r=existing[ident]
            assert r['source_frame_sha256']==s['image_sha256'] and r['roi_on_960x540']==roi
            rows.append(r); continue
        im=Image.open(ROOT/s['image']); assert im.size==(1920,1080)
        crop=im.crop(tuple(v*2 for v in roi))
        target=DET/'candidates'/(ident+'.jpg'); assert not target.exists()
        crop.save(target,quality=96)
        r=dict(id=ident,date='20261010',camera=meta['source']['camera'],split='train',source=meta['source']['member'],
            source_sha256=meta['source_sha256'],source_pts_seconds=s['source_pts_seconds'],relative_pts_seconds=s['relative_pts_seconds'],
            source_frame=s['image'],source_frame_sha256=s['image_sha256'],frames_manifest=str(mp.relative_to(ROOT)),sample_index=index,
            event_reference=None,image=str(target.relative_to(ROOT)),sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
            roi_on_960x540=roi,width=crop.width,height=crop.height,object_class='tank',annotation_status='unreviewed',
            provenance='Native crop after chronological empty-return and stationary-context inspection. Object detection only; no production label inferred.')
        rows.append(r);manifest['records'].append(r)
    path.write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf8')
    sheet=Image.new('RGB',(1080,720),'#202020');d=ImageDraw.Draw(sheet)
    for i,r in enumerate(rows):
        x=i%3*360;y=i//3*360
        sheet.paste(Image.open(ROOT/r['image']),(x,y+30));d.text((x+4,y+5),r['id'],fill='white')
    sheet.save(DET/'sheets/candidate_batch07.jpg',quality=96)
    print(json.dumps(dict(candidate_count=len(manifest['records']),new_ids=[r['id'] for r in rows])))

if __name__=='__main__':main()
