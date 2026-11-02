"""Append two clear camera15 validation ROIs from already inspected17Oct stills."""
import hashlib
import json
from pathlib import Path
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/tank_transfer_training_v1'
DET=BASE/'detector_v1'
CTX=BASE/'dataset_v1/roi_context_batch05'


def main():
    manifest=json.loads((DET/'candidate_manifest.json').read_text('utf8'))
    context={r['id']:r for r in json.loads((CTX/'manifest.json').read_text('utf8'))}
    existing={r['id']:r for r in manifest['records']}
    rows=[]
    for ident,ref,roi in [('088','072',[480,15,585,95]),('089','073',[95,380,300,540])]:
        src=context[ref]
        assert src['split']=='val' and src['date']=='20261017'
        if ident in existing:
            assert existing[ident]['source']==src['source_member'] and existing[ident]['roi_on_960x540']==roi
            rows.append(existing[ident]);continue
        p=ROOT/src['native_image']
        assert hashlib.sha256(p.read_bytes()).hexdigest()==src['source_sha256']
        native=Image.open(p)
        assert native.size==(1920,1080)
        image=native.crop(tuple(v*2 for v in roi))
        target=DET/'candidates'/(ident+'.jpg')
        assert not target.exists()
        image.save(target,quality=97)
        r=dict(id=ident,date='20261017',camera=15,split='val',source=src['source_member'],source_sha256=src['source_sha256'],
               native_source_image=src['native_image'],context_manifest=str((CTX/'manifest.json').relative_to(ROOT)),
               source_pts_seconds=None,event_reference=None,image=str(target.relative_to(ROOT)),sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
               roi_on_960x540=roi,width=image.width,height=image.height,
               provenance='Clear ROI selected from an already inspected validation-day source still; same day stays entirely validation.',
               annotation_status='unreviewed',object_class='tank')
        manifest['records'].append(r);rows.append(r)
    (DET/'candidate_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    sheet=Image.new('RGB',(900,420),'#202020');d=ImageDraw.Draw(sheet)
    for i,r in enumerate(rows):
        sheet.paste(Image.open(ROOT/r['image']),(i*450,35));d.text((i*450+5,5),r['id']+' camera15 validation',fill='white')
    sheet.save(DET/'sheets/candidate_batch05_val.jpg',quality=97)
    print(json.dumps(dict(candidate_count=len(manifest['records']),added=[r['id'] for r in rows])))


if __name__=='__main__':main()
