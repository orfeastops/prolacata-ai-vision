import json, pathlib, collections, random, zipfile, shutil, sys
from PIL import Image, ImageDraw, ImageFont

ROOT=pathlib.Path('outputs/facility_dataset')
OUT=ROOT/'annotation_audit';OUT.mkdir(exist_ok=True)
ARCHIVE=OUT/'kaggle_output.zip'
RAW=OUT/'raw';RAW.mkdir(exist_ok=True)
if ARCHIVE.exists():
    with zipfile.ZipFile(ARCHIVE) as z:
        for member in z.infolist():
            if member.filename.startswith('annotation_proposals/') and member.filename.endswith('.json'):
                assert (RAW/member.filename).resolve().is_relative_to(RAW.resolve())
                z.extract(member,RAW)
files=sorted((RAW/'annotation_proposals').glob('*.json'))
assert len(files)==3460 or '--partial' in sys.argv, f'Expected complete result, found {len(files)}'
records=[json.loads(p.read_text()) for p in files]
groups=collections.defaultdict(list);labels=collections.Counter();counts=collections.Counter()
for r in records:
    f=r['frame'];groups[(f['camera'],f['date'])].append(r)
    for view in r['proposals']:
        assert len(view['boxes'])==len(view['scores'])==len(view['labels'])
        for label in view['labels']:labels[(f['camera'],view['view'],label)]+=1
        counts[(f['camera'],f['date'],view['view'])]+=len(view['boxes'])
summary={'proposal_files':len(records),'complete_download':len(files)==3460,'review_status':'unverified; structural audit only',
         'group_frames':{f'{c}_{d}':len(v) for (c,d),v in groups.items()},
         'label_counts':{'|'.join(map(str,k)):v for k,v in labels.most_common()},
         'box_counts':{'|'.join(map(str,k)):v for k,v in counts.items()}}
(OUT/'structural_audit.json').write_text(json.dumps(summary,indent=2))
if '--structure-only' in sys.argv:
    print(json.dumps({'proposal_files':len(files),'complete_download':len(files)==3460}));sys.exit(0)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',12)
selected=[]
for (camera,date),rs in sorted(groups.items()):
    rng=random.Random(f'{camera}_{date}_audit_v1')
    # Include distinct times across each camera/day; all remain unverified.
    rs=sorted(rs,key=lambda r:r['frame']['image'])
    sample=rng.sample(rs,min(12,len(rs)))
    for r in sample:
        view=next((x for x in r['proposals'] if x['view']=='filling_crop'),r['proposals'][0])
        selected.append({'frame':r['frame'],'view':view,'audit_id':f'A{len(selected)+1:03d}'})
    for page in range(0,len(sample),6):
        sheet=Image.new('RGB',(1280,3*405),'#eeeeee');draw=ImageDraw.Draw(sheet)
        for j,r in enumerate(sample[page:page+6]):
            view=next((x for x in r['proposals'] if x['view']=='filling_crop'),r['proposals'][0])
            im=Image.open(ROOT/view['image']).convert('RGB');sx=640/im.width;sy=360/im.height
            im=im.resize((640,360));di=ImageDraw.Draw(im)
            for k,(box,score,label) in enumerate(zip(view['boxes'],view['scores'],view['labels'])):
                b=[box[0]*sx,box[1]*sy,box[2]*sx,box[3]*sy]
                color=['#ff3030','#00ff55','#00bfff','#ffb000'][k%4]
                di.rectangle(b,outline=color,width=2)
                txt=f'{k+1}:{label} {score:.2f}'
                x=max(0,min(b[0],500));y=max(0,b[1]-15)
                di.rectangle((x,y,x+min(630-x,len(txt)*7),y+15),fill='black')
                di.text((x,y),txt,font=small,fill=color)
            x=(j%2)*640;y=(j//2)*405
            sheet.paste(im,(x,y+45))
            f=r['frame'];audit_id=next(s['audit_id'] for s in selected if s['frame']['image']==f['image'])
            draw.text((x+5,y+3),f'{audit_id} Camera {camera} {date} {view["view"]} UNVERIFIED',font=font,fill='black')
            draw.text((x+5,y+23),f['image'][-78:],font=small,fill='black')
        sheet.save(OUT/f'audit_cam{camera}_{date}_page{page//6+1}.jpg',quality=92)
(OUT/'review_sample.json').write_text(json.dumps(selected,indent=2))
print(json.dumps({'files':len(files),'sample':len(selected),'sheets':len(list(OUT.glob('audit_cam*.jpg')))},indent=2))
