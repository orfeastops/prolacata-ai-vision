"""Extract a bounded native-video evidence window; never assigns labels.

Each output directory is single-use to prevent duplicate extraction. PTS are
kept separately from the camera clock, which must be read from image evidence.
"""
import argparse
import hashlib
import io
import json
import os
import zipfile
from pathlib import Path

import av
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'outputs/tank_transfer_training_v1'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--day', required=True)
    p.add_argument('--camera', type=int, required=True)
    p.add_argument('--peer-index', type=int, default=0)
    p.add_argument('--start', type=float, required=True)
    p.add_argument('--end', type=float, required=True)
    p.add_argument('--step', type=float, default=1)
    p.add_argument('--name', required=True)
    p.add_argument('--member', help='Explicit inventoried training source; used for adjacent context.')
    p.add_argument('--validation-only', action='store_true', help='Permit17Oct annotation extraction, retaining the validation split. Never permits test days.')
    p.add_argument('--roi', type=int, nargs=4, help='Optional crop on the 960x540 reference; full native images are always retained.')
    a = p.parse_args()
    assert a.day not in ('20261025', '20261028')
    assert (a.day == '20261017') == a.validation_only
    assert a.camera in (11, 15) and 0 <= a.start < a.end and a.step > 0
    assert a.name.replace('_', '').replace('-', '').isalnum()
    if a.roi:
        assert 0 <= a.roi[0] < a.roi[2] <= 960 and 0 <= a.roi[1] < a.roi[3] <= 540
    if a.member:
        member = a.member
    else:
        source_meta = json.loads((BASE / f'dataset_v1/sequence_review/{a.day}/frames.json').read_text())
        member = source_meta['source']['member'] if a.camera == 15 else source_meta['source']['camera11_candidate_members'][a.peer_index]
    out = BASE / 'dataset_v1/sequence_review' / a.day / a.name
    if (out / 'frames.json').exists():
        print('Already completed:', out)
        return
    out.mkdir(parents=True, exist_ok=True)
    with (out / 'extraction_started.json').open('x', encoding='utf8') as f:
        json.dump(dict(pid=os.getpid(), member=member, args=vars(a)), f, indent=2)
    inv = json.loads((BASE / 'archive_inventory.json').read_text(encoding='utf8'))
    src = next(r for r in inv['records'] if r['member'] == member)
    expected_split = 'validation' if a.validation_only else 'train'
    assert src['split'] == expected_split and src['date'] == a.day and src['camera'] == a.camera
    with zipfile.ZipFile(src['archive']) as z:
        raw = z.read(member)
    sha = hashlib.sha256(raw).hexdigest()
    samples = []
    with av.open(io.BytesIO(raw)) as c:
        stream = c.streams.video[0]
        stream.thread_type = 'AUTO'
        stream.codec_context.thread_count = 2
        first = None
        tick = a.start
        for native_i, frame in enumerate(c.decode(stream)):
            if frame.time is None:
                continue
            if first is None:
                first = float(frame.time)
            t = float(frame.time) - first
            if t > a.end + 0.1:
                break
            if t + 0.0001 < tick:
                continue
            tick = t + a.step
            full = frame.to_image().convert('RGB')
            name = f'{len(samples):04d}_{t:09.3f}.jpg'
            full.save(out / name, quality=95)
            # Geometry expressed on the 960x540 reference, cropped directly
            # from native pixels (no invented image detail).
            roi = a.roi or ((565, 0, 960, 300) if a.camera == 15 else (320, 70, 760, 510))
            scale_x, scale_y = full.width / 960, full.height / 540
            crop = lambda box: full.crop(tuple(round(v * (scale_x if i % 2 == 0 else scale_y)) for i, v in enumerate(box)))
            tile = Image.new('RGB', (600, 600))
            d = ImageDraw.Draw(tile)
            d.text((5, 3), f'{a.day} cam{a.camera} sample {len(samples)} PTS +{t:.3f}', fill='white')
            tile.paste(crop((0, 10, 320, 50)).resize((600, 70)), (0, 20))
            tile.paste(crop(roi).resize((600, 510)), (0, 90))
            tile.save(out / ('tile_' + name), quality=95)
            samples.append(dict(index=len(samples), native_frame_index=native_i,
                source_pts_seconds=round(float(frame.time), 6), relative_pts_seconds=round(t, 6),
                image=str((out / name).relative_to(ROOT)), tile=str((out / ('tile_' + name)).relative_to(ROOT)),
                image_sha256=hashlib.sha256((out / name).read_bytes()).hexdigest(),
                visible_camera_clock=None, review_status='unreviewed', native_size=list(full.size)))
    sheets = []
    for i in range(0, len(samples), 6):
        sheet = Image.new('RGB', (1800, 1200))
        for j, sample in enumerate(samples[i:i+6]):
            with Image.open(ROOT / sample['tile']) as im:
                sheet.paste(im, (j % 3 * 600, j // 3 * 600))
        path = out / f'sheet_{i//6:03d}.jpg'
        sheet.save(path, quality=94)
        sheets.append(str(path.relative_to(ROOT)))
    result = dict(source=src, source_sha256=sha, samples=samples, sheets=sheets,
        status='extraction_complete_requires_visual_review', requested_window=vars(a),
        clock_policy='PTS are decoder positions, not verified camera-clock timestamps or cross-camera synchronization.',
        test_pixels_used=0)
    (out / 'frames.json').write_text(json.dumps(result, indent=2), encoding='utf8')
    print(json.dumps(dict(output=str(out), frames=len(samples), sheets=len(sheets))))


if __name__ == '__main__':
    main()
