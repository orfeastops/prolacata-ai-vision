"""Append native training crops from the reviewed15Oct departure and storage context."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'outputs/tank_transfer_training_v1'
DET = BASE / 'detector_v1'
CHOICES = [
    ('late_origin_1230_cam11',54,[399,238,504,347]),
    ('late_origin_1230_cam11',55,[386,352,535,505]),
    ('late_production_1234_cam11',14,[486,88,545,146]),
    ('late_transfer_1240_cam15',3,[497,104,600,173]),
    ('late_production_1234_cam11',57,[235,247,351,363]),
]

def main():
    path = DET / 'candidate_manifest.json'
    manifest = json.loads(path.read_text('utf8'))
    existing = {r['id']:r for r in manifest['records']}
    rows = []
    for num,(window,index,roi) in zip(range(215,220),CHOICES):
        ident = f'{num:03d}'
        mp = BASE / 'dataset_v1/sequence_review/20261015' / window / 'frames.json'
        m = json.loads(mp.read_text('utf8'))
        s = m['samples'][index]
        assert m['source']['date']=='20261015' and m['source']['split']=='train'
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
        r = dict(id=ident,date='20261015',camera=m['source']['camera'],split='train',
            source=m['source']['member'],source_sha256=m['source_sha256'],
            source_pts_seconds=s['source_pts_seconds'],relative_pts_seconds=s['relative_pts_seconds'],
            source_frame=s['image'],source_frame_sha256=s['image_sha256'],
            frames_manifest=str(mp.relative_to(ROOT)),sample_index=index,event_reference=None,
            image=str(target.relative_to(ROOT)),sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
            roi_on_960x540=roi,width=crop.width,height=crop.height,object_class='tank',
            annotation_status='unreviewed',
            provenance='Native context inspected. Proposed ROI boxes require separate overlay review. Training-day evidence only; no release.')
        rows.append(r)
        manifest['records'].append(r)
    path.write_text(json.dumps(manifest,indent=2),encoding='utf8')
    sheet = Image.new('RGB',(1440,900),'#202020')
    draw = ImageDraw.Draw(sheet)
    for i,r in enumerate(rows):
        x,y=i%3*480,i//3*450
        sheet.paste(Image.open(ROOT/r['image']),(x,y+30))
        draw.text((x+4,y+5),r['id'],fill='white')
    sheet.save(DET/'sheets/candidate_batch30.jpg',quality=96)
    print(json.dumps(dict(candidate_count=len(manifest['records']),new_ids=[r['id'] for r in rows])))

if __name__=='__main__':main()
