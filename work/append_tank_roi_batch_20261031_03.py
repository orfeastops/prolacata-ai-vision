"""Append eight source-backed ROI candidates; never reset earlier curation."""
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
    choices = [('filling_departure_1110_review', i) for i in [61, 62, 63, 64]]
    choices += [('empty_return_1111_review', i) for i in [6, 7, 8, 10]]
    new = []
    for n, (window, index) in enumerate(choices, 75):
        ident = f'{n:03d}'
        meta_path = BASE / 'dataset_v1/sequence_review/20261015' / window / 'frames.json'
        meta = json.loads(meta_path.read_text('utf8'))
        sample = meta['samples'][index]
        assert meta['source']['split'] == 'train' and meta['source']['date'] == '20261015'
        if ident in existing:
            assert existing[ident]['source_frame_sha256'] == sample['image_sha256']
            new.append(existing[ident])
            continue
        roi = [400, 85, 650, 335]
        native = Image.open(ROOT / sample['image'])
        assert native.size == (1920, 1080)
        target = OUT / 'candidates' / (ident + '.jpg')
        assert not target.exists(), target
        native.crop(tuple(v * 2 for v in roi)).save(target, quality=96)
        r = dict(id=ident, date='20261015', camera=11, split='train',
                 source=meta['source']['member'], source_sha256=meta['source_sha256'],
                 source_pts_seconds=sample['source_pts_seconds'], relative_pts_seconds=sample['relative_pts_seconds'],
                 source_frame=sample['image'], source_frame_sha256=sample['image_sha256'],
                 frames_manifest=str(meta_path.relative_to(ROOT)), sample_index=index,
                 event_reference=None, image=str(target.relative_to(ROOT)),
                 sha256=hashlib.sha256(target.read_bytes()).hexdigest(), roi_on_960x540=roi,
                 width=500, height=500, provenance='Source-backed crop selected after chronological sequence inspection; no inferred box or load label.',
                 annotation_status='unreviewed', object_class='tank')
        manifest['records'].append(r)
        new.append(r)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf8')
    for start in range(0, len(new), 4):
        sheet = Image.new('RGB', (1040, 1100), '#202020')
        draw = ImageDraw.Draw(sheet)
        for k, r in enumerate(new[start:start+4]):
            x, y = k % 2 * 520, k // 2 * 550
            sheet.paste(Image.open(ROOT / r['image']), (x, y + 40))
            draw.text((x+5,y+5), f'{r["id"]} | source sample {r["sample_index"]}', fill='white')
        sheet.save(OUT / 'sheets' / f'candidate_batch03_{start//4}.jpg', quality=96)
    print(json.dumps(dict(candidate_count=len(manifest['records']), new_ids=[r['id'] for r in new])))


if __name__ == '__main__':
    main()
