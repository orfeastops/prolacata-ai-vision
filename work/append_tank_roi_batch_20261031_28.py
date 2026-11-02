"""Append inspected native crops without regenerating prior annotations."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'outputs/tank_transfer_training_v1'
DET = BASE / 'detector_v1'
CHOICES = [
    ('20261008','early_pair_context_0518_cam11',1,[580,315,730,455]),
    ('20261008','early_production_screen_0545_cam11',10,[570,320,725,465]),
    ('20261017','midday_1314_cam15',14,[452,125,568,210]),
    ('20261017','midday_tank_unloading_1316_cam11',21,[430,170,545,250]),
    ('20261017','midday_tank_unloading_1316_cam11',20,[235,265,350,380]),
]


def main():
    path = DET / 'candidate_manifest.json'
    manifest = json.loads(path.read_text('utf8'))
    existing = {r['id']:r for r in manifest['records']}
    rows = []
    for num,(day,window,index,roi) in zip(range(206,211),CHOICES):
        ident = f'{num:03d}'
        mp = BASE / 'dataset_v1/sequence_review' / day / window / 'frames.json'
        m = json.loads(mp.read_text('utf8'))
        s = m['samples'][index]
        assert m['source']['date']==day and day in ['20261008','20261017']
        split = 'val' if day=='20261017' else 'train'
        assert m['source']['split']==('validation' if split=='val' else 'train')
        if ident in existing:
            r = existing[ident]
            assert r['source_frame_sha256']==s['image_sha256'] and r['roi_on_960x540']==roi
            rows.append(r)
            continue
        im = Image.open(ROOT/s['image'])
        assert im.size==(1920,1080)
        crop = im.crop(tuple(v*2 for v in roi))
        target = DET / 'candidates' / (ident+'.jpg')
        assert not target.exists()
        crop.save(target,quality=96)
        r = dict(id=ident,date=day,camera=m['source']['camera'],split=split,
            source=m['source']['member'],source_sha256=m['source_sha256'],
            source_pts_seconds=s['source_pts_seconds'],relative_pts_seconds=s['relative_pts_seconds'],
            source_frame=s['image'],source_frame_sha256=s['image_sha256'],
            frames_manifest=str(mp.relative_to(ROOT)),sample_index=index,event_reference=None,
            image=str(target.relative_to(ROOT)),sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
            roi_on_960x540=roi,width=crop.width,height=crop.height,object_class='tank',
            annotation_status='unreviewed',
            provenance='Native chronological context inspected. Crop and proposed boxes require separate overlay review.')
        rows.append(r)
        manifest['records'].append(r)
    path.write_text(json.dumps(manifest,indent=2),encoding='utf8')
    sheet = Image.new('RGB',(1080,1080),'#202020')
    draw = ImageDraw.Draw(sheet)
    for i,r in enumerate(rows):
        x,y = i%3*360,i//3*360
        sheet.paste(Image.open(ROOT/r['image']),(x,y+30))
        draw.text((x+4,y+5),r['id'],fill='white')
    sheet.save(DET/'sheets/candidate_batch28.jpg',quality=96)
    print(json.dumps(dict(candidate_count=len(manifest['records']),new_ids=[r['id'] for r in rows])))


if __name__=='__main__':main()
