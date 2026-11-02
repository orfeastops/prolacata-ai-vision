"""Create a small, fully reviewable first detector batch; never open test pixels."""
import json, hashlib, zipfile
from pathlib import Path
from PIL import Image, ImageDraw
import io

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/tank_transfer_training_v1/detector_v1'
AUDIT=ROOT/'outputs/tank_door_audit'
ROIS={11:[400,85,650,335],15:[580,0,785,180]} # doorway/approach detector, not whole-room storage tracking

def save(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False),encoding='utf8')
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    OUT.mkdir(exist_ok=True);(OUT/'candidates').mkdir(exist_ok=True);(OUT/'sheets').mkdir(exist_ok=True)
    records=[];seen=set()
    def add(im,day,cam,split,source,provenance,pts=None,event=None):
        assert day not in ['20261025','20261028']
        key=(str(source),pts)
        if key in seen:return
        seen.add(key)
        im=im.convert('RGB').resize((960,540)).crop(ROIS[cam]);im=im.resize((im.width*2,im.height*2))
        ident=f'{len(records):03d}';path=OUT/'candidates'/f'{ident}.jpg';im.save(path,quality=95)
        records.append(dict(id=ident,date=day,camera=cam,split=split,source=str(source),source_pts_seconds=pts,event_reference=event,
                            image=str(path.relative_to(ROOT)),sha256=digest(path),roi_on_960x540=ROIS[cam],width=im.width,height=im.height,
                            provenance=provenance,annotation_status='unreviewed',object_class='tank'))
    # Actual saved video frames near known exits/entries, without using event counts as image labels.
    proposals=json.loads((AUDIT/'proposals/20261021/proposals.json').read_text())
    for idx in [120,131,135,182,223,302,366,390]:
        g=proposals[idx];scan=json.loads((AUDIT/Path(g['peak']['image']).parent/'scan.json').read_text())
        fs=[f for f in scan['candidates'] if g['start']<=f['t']<=g['end']]
        for frac in [.35,.65]:
            f=fs[round(frac*(len(fs)-1))];p=AUDIT/f['image']
            add(Image.open(p),'20261021',11,'train',scan['basename'],'Previously decoded video frame; object boxes require fresh visual review.',f['t'],str(idx))
        fs=json.loads((AUDIT/f'camera15_matches/20261021/{idx}.json').read_text())
        # Samples from first arrival clip, later position as well as doorway.
        first=[f for f in fs if f['basename']==fs[0]['basename']]
        for frac in [.6,1.0]:
            f=first[round(frac*(len(first)-1))]
            add(Image.open(AUDIT/'camera15'/f['image']),'20261021',15,'train',f['basename'],'Previously decoded video frame; no new transfer count inferred.',f['t'],str(idx))
    inv=json.loads((OUT.parent/'archive_inventory.json').read_text(encoding='utf8'))
    with zipfile.ZipFile(inv['archive']) as z:
        # Distinct export stills from several training days; selection never uses detector outputs.
        for day in ['20261006','20261010','20261013','20261015','20261023','20261017']:
            for cam in [11,15]:
                rows=sorted([r for r in inv['records'] if r['date']==day and r['camera']==cam and r['media_type']=='export_still'],key=lambda r:r['filename_start'])
                fractions=[.2,.4,.6,.8] if day=='20261017' else [.35,.7]
                for frac in fractions:
                    r=rows[round(frac*(len(rows)-1))]
                    add(Image.open(io.BytesIO(z.read(r['member']))),day,cam,'val' if day=='20261017' else 'train',r['member'],
                        'Export still; actual within-file timestamp not assumed equal to filename start.')
        # Early scenes before dense storage rows accumulate provide identifiable
        # individual camera15 tanks, including validation-day examples.
        for day in ['20261006','20261010','20261013','20261015','20261017']:
            rows=sorted([r for r in inv['records'] if r['date']==day and r['camera']==15 and r['media_type']=='export_still'],key=lambda r:r['filename_start'])
            for frac in [.05,.10,.15]:
                r=rows[round(frac*(len(rows)-1))]
                add(Image.open(io.BytesIO(z.read(r['member']))),day,15,'val' if day=='20261017' else 'train',r['member'],
                    'Early export still for instance-boundary review; selected before model predictions.')
    save(OUT/'candidate_manifest.json',dict(status='awaiting_visual_boxes',records=records,roi_policy=ROIS,test_pixels_used=0,
         limitations='First ROI detector batch. One tank class, no inferred full/empty labels. Does not implement tank counting or prove transfer completion.'))
    for start in range(0,len(records),6):
        sheet=Image.new('RGB',(1680,1280),'#202020');draw=ImageDraw.Draw(sheet)
        for j,r in enumerate(records[start:start+6]):
            x=(j%3)*560;y=(j//3)*640
            im=Image.open(ROOT/r['image']);d=ImageDraw.Draw(im)
            for gx in range(0,im.width,50):
                d.line((gx,0,gx,im.height),fill=(120,120,20),width=1);d.text((gx+1,1),str(gx),fill='yellow')
            for gy in range(50,im.height,50):
                d.line((0,gy,im.width,gy),fill=(120,120,20),width=1);d.text((1,gy+1),str(gy),fill='yellow')
            sheet.paste(im,(x,y+40));draw.text((x+4,y+3),f'{r["id"]} | {r["date"]} cam{r["camera"]} {r["split"]}',fill='white')
            draw.text((x+4,y+19),f'{r["width"]}x{r["height"]} | event {r["event_reference"]} | PTS {r["source_pts_seconds"]}',fill='white')
        sheet.save(OUT/'sheets'/f'{start//6:02d}.jpg',quality=96)
    print(json.dumps({'images':len(records),'train':sum(r['split']=='train' for r in records),'val':sum(r['split']=='val' for r in records),'test_pixels':0}))
if __name__=='__main__':main()
