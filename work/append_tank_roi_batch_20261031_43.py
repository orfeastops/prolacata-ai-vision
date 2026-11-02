"""Append three native-context reviewed tank ROIs; preserve previous candidates."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/tank_transfer_training_v1'
DET=BASE/'detector_v1'
CHOICES=[
    ('morning_departure0903_cam11',16,[397,214,507,318]),
    ('morning_departure0903_cam11',23,[340,292,480,428]),
    ('morning_storage0909_cam15',3,[599,29,679,86]),
]

def main():
    path=DET/'candidate_manifest.json'
    manifest=json.loads(path.read_text('utf8'))
    existing={r['id']:r for r in manifest['records']}
    rows=[]
    for num,(window,index,roi) in zip(range(269,272),CHOICES):
        ident=f'{num:03d}'
        mp=BASE/'dataset_v1/sequence_review/20261006'/window/'frames.json'
        m=json.loads(mp.read_text('utf8'));s=m['samples'][index]
        assert m['source']['date']=='20261006' and m['source']['split']=='train'
        if ident in existing:
            r=existing[ident]
            assert r['source_frame_sha256']==s['image_sha256'] and r['roi_on_960x540']==roi
            rows.append(r);continue
        im=Image.open(ROOT/s['image']);assert im.size==(1920,1080)
        crop=im.crop(tuple(v*2 for v in roi));target=DET/'candidates'/(ident+'.jpg')
        assert not target.exists();crop.save(target,quality=96)
        r=dict(id=ident,date='20261006',camera=m['source']['camera'],split='train',
            source=m['source']['member'],source_sha256=m['source_sha256'],source_pts_seconds=s['source_pts_seconds'],
            relative_pts_seconds=s['relative_pts_seconds'],source_frame=s['image'],source_frame_sha256=s['image_sha256'],
            frames_manifest=str(mp.relative_to(ROOT)),sample_index=index,event_reference=None,
            image=str(target.relative_to(ROOT)),sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
            roi_on_960x540=roi,width=crop.width,height=crop.height,object_class='tank',annotation_status='unreviewed',
            provenance='Native context visually inspected; proposed ROI box requires separate overlay review. Dataset release pending.')
        rows.append(r);manifest['records'].append(r)
    path.write_text(json.dumps(manifest,indent=2),encoding='utf8')
    sheet=Image.new('RGB',(1440,400),'#202020');draw=ImageDraw.Draw(sheet)
    for i,r in enumerate(rows):
        sheet.paste(Image.open(ROOT/r['image']),(i*480,30));draw.text((i*480+4,5),r['id'],fill='white')
    sheet.save(DET/'sheets/candidate_batch43.jpg',quality=96)
    print(json.dumps(dict(candidate_count=len(manifest['records']),new_ids=[r['id'] for r in rows])))

if __name__=='__main__':main()
