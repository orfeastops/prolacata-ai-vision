"""Extract native evidence for manual object review; no automatic truth labels."""
import json,hashlib,re
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/facility_dataset/temporal_pipeline'
V4=BASE/'sequence_annotation_v4/assistant_visual_review'
OUT=BASE/'placement_counter_v5/object_expansion'
FONT=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,o):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,indent=2),encoding='utf-8')
def photo_sheet(rows,name):
    canvas=Image.new('RGB',(1280,392*((len(rows)+1)//2)),'#111827');d=ImageDraw.Draw(canvas)
    for n,r in enumerate(rows):
        x=(n%2)*640;y=(n//2)*392
        d.text((x+5,y+5),f"{r['id']} | t={r['time_s']:.3f} | {r.get('context','candidate')}",font=FONT,fill='white')
        canvas.paste(Image.open(r['image']).convert('RGB'),(x,y+32))
    path=OUT/'review_sheets'/f'{name}.jpg';path.parent.mkdir(parents=True,exist_ok=True);canvas.save(path,quality=95)
    return str(path)

def main():
    cv2.setNumThreads(2);OUT.mkdir(parents=True,exist_ok=True)
    index=read(BASE/'temporal_media_index.json');byhash={r['sha256']:r for r in index}
    old=read(BASE/'placement_counter_v4/event_quantity_diagnostic/dataset.json')
    forbidden=set(old['excluded_sources'])
    forbidden.update(r['source_sha256'] for r in read(BASE/'placement_counter_v2/individual_block_validation/frozen_labels.json')['frames'])
    forbidden_intervals=[byhash[s] for s in forbidden if s in byhash]
    existing={r['source_sha256'] for r in old['rows']}
    def overlaps(r):
        return any(r['camera']==f['camera'] and max(r['filename_start'],f['filename_start'])<min(r['filename_end'],f['filename_end']) for f in forbidden_intervals)
    chosen=[]
    for date in ['2026-10-01','2026-10-21']:
        pool=sorted([r for r in index if r['camera']==11 and r['date']==date and r['sha256'] not in forbidden|existing
            and 45<=r.get('probed_duration_s',0)<=900 and '064500'<=r['filename_start'][8:]<='143000' and not overlaps(r)],key=lambda r:r['filename_start'])
        for q in [.1,.35,.65,.9]:chosen.append(pool[int((len(pool)-1)*q)])
    candidates=[];sequences={};pages=[]
    proposed=read(V4/'assistant_annotations.json')
    for clip in ['C01','C03','C04','C05','C06']:
        meta=read(V4/clip/'frames.json');times=np.array(meta['relative_times_s'])
        row=next(r for r in old['rows'] if r['id']==clip)
        targets=[]
        for e in row['events']:
            a,b=e['carry_interval'] or e['release_interval']
            if b>a:
                targets.extend([(a+.25*(b-a),'carry'),(a+.75*(b-a),'carry')])
        for e in row['negatives']:
            a,b=e['interval'];targets.append(((a+b)/2,e['action']))
        used=set();local=[]
        for t,ctx in sorted(targets):
            i=int(np.argmin(abs(times-t)))
            if i in used:continue
            used.add(i)
            r=dict(id=f'{clip}_{i:04d}',clip=clip,time_s=float(times[i]),frame_index=i,
                source_frame_index=meta['source_frame_indices'][i],source_sha256=meta['source_sha256'],
                image=str(V4/clip/meta['files'][i]),context=ctx,role='train_candidate')
            candidates.append(r);local.append(r)
        sequences[clip]=dict(source_sha256=meta['source_sha256'],source_file=meta['source_file'],
            first_source_pts_s=meta['original_first_clip_pts_s'],times=meta['relative_times_s'],
            source_frame_indices=meta['source_frame_indices'],files=[str(V4/clip/f) for f in meta['files']])
        for offset in range(0,len(local),6):pages.append(photo_sheet(local[offset:offset+6],f'{clip}_{offset//6:02d}'))
    for n,source in enumerate(chosen,1):
        clip=f'D{n:02d}';dest=OUT/'native'/clip;dest.mkdir(parents=True,exist_ok=True)
        start=min(source['probed_duration_s']*.45,source['probed_duration_s']-22)
        meta_path=dest/'frames.json'
        if meta_path.exists():meta=read(meta_path)
        else:
            p=Path(source['local_path'])
            with p.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==source['sha256']
            cap=cv2.VideoCapture(str(p));assert cap.isOpened();i=0;ts=[];ids=[];files=[]
            while True:
                ok,frame=cap.read()
                if not ok:break
                pts=cap.get(cv2.CAP_PROP_POS_MSEC)/1000
                if pts>start+20:break
                if pts>=start-1:
                    target=dest/f'frame_{len(files):04d}.jpg'
                    assert cv2.imwrite(str(target),frame[720:1080,800:1440],[cv2.IMWRITE_JPEG_QUALITY,97])
                    ts.append(round(pts-start,6));ids.append(i);files.append(str(target))
                i+=1
            cap.release();assert len(ts)>280 and np.all(np.diff(ids)==1)
            meta=dict(source_sha256=source['sha256'],source_file=str(p),first_source_pts_s=start,
                times=ts,source_frame_indices=ids,files=files)
            write(meta_path,meta)
        sequences[clip]=meta;local=[];times=np.array(meta['times'])
        for t in np.arange(0,20,1.):
            i=int(np.argmin(abs(times-t)))
            r=dict(id=f'{clip}_{i:04d}',clip=clip,time_s=float(times[i]),frame_index=i,
                source_frame_index=meta['source_frame_indices'][i],source_sha256=source['sha256'],
                image=meta['files'][i],context='new source, unlabelled',role='train_candidate')
            candidates.append(r);local.append(r)
        for offset in range(0,len(local),6):pages.append(photo_sheet(local[offset:offset+6],f'{clip}_{offset//6:02d}'))
        write(OUT/'preparation_progress.json',dict(stage='native_evidence',completed_new_sources=n,total_new_sources=len(chosen)))
        print(clip,source['basename'],len(meta['times']),flush=True)
    assert not {r['source_sha256'] for r in candidates}&forbidden
    write(OUT/'candidates.json',candidates);write(OUT/'sequences.json',sequences)
    write(OUT/'selection.json',dict(new_sources=chosen,forbidden_sources=sorted(forbidden),
        candidate_frames=len(candidates),source_count=len(sequences),pages=pages,
        source_interval_overlap_excluded=True,labels_not_yet_generated=True))
    print('Candidate frames',len(candidates),'pages',len(pages),flush=True)

if __name__=='__main__':main()
