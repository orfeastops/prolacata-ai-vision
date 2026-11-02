"""Append source-backed blue doorway and empty gray tank ROI examples."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'outputs/tank_transfer_training_v1'
OUT = BASE / 'detector_v1'


def main():
    path = OUT / 'candidate_manifest.json'
    manifest = json.loads(path.read_text('utf8'))
    existing = {r['id']: r for r in manifest['records']}
    choices = [('20261006', 'blue_departure_door_detail', i, [400,85,650,335]) for i in [8,10,12,43]]
    choices += [('20261015', 'storage_settle_1116_review', 18, [350,95,510,215])]
    new = []
    for n, (day,window,index,roi) in enumerate(choices,83):
        ident = f'{n:03d}'
        mp = BASE/'dataset_v1/sequence_review'/day/window/'frames.json'
        meta = json.loads(mp.read_text('utf8'))
        sample = meta['samples'][index]
        assert meta['source']['split']=='train' and meta['source']['date']==day
        if ident in existing:
            assert existing[ident]['source_frame_sha256']==sample['image_sha256']
            assert existing[ident]['roi_on_960x540']==roi
            new.append(existing[ident])
            continue
        native = Image.open(ROOT/sample['image'])
        assert native.size==(1920,1080)
        target = OUT/'candidates'/(ident+'.jpg')
        assert not target.exists()
        crop = native.crop(tuple(v*2 for v in roi))
        crop.save(target,quality=96)
        r = dict(id=ident,date=day,camera=meta['source']['camera'],split='train',
                 source=meta['source']['member'],source_sha256=meta['source_sha256'],
                 source_pts_seconds=sample['source_pts_seconds'],relative_pts_seconds=sample['relative_pts_seconds'],
                 source_frame=sample['image'],source_frame_sha256=sample['image_sha256'],
                 frames_manifest=str(mp.relative_to(ROOT)),sample_index=index,event_reference=None,
                 image=str(target.relative_to(ROOT)),sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                 roi_on_960x540=roi,width=crop.width,height=crop.height,
                 provenance='Native-source crop following chronological sequence review; object detection only.',
                 annotation_status='unreviewed',object_class='tank')
        manifest['records'].append(r)
        new.append(r)
    path.write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf8')
    sheet = Image.new('RGB',(1680,1160),'#202020')
    draw = ImageDraw.Draw(sheet)
    for k,r in enumerate(new):
        x,y=k%3*560,k//3*580
        sheet.paste(Image.open(ROOT/r['image']),(x,y+35))
        draw.text((x+4,y+4),f'{r["id"]} cam{r["camera"]} sample {r["sample_index"]}',fill='white')
    sheet.save(OUT/'sheets/candidate_batch04.jpg',quality=96)
    print(json.dumps(dict(candidate_count=len(manifest['records']),new_ids=[r['id'] for r in new])))


if __name__=='__main__':
    main()
