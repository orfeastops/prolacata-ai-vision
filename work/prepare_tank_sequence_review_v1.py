"""Prepare real training-day sequence evidence; no labels or model inference."""
import io,json,time,traceback,hashlib,os
from pathlib import Path
import zipfile
import datetime as dt
import av
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/tank_transfer_training_v1'
OUT=BASE/'dataset_v1/sequence_review'
def save(p,x):
    tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(x,indent=2,ensure_ascii=False),encoding='utf8');tmp.replace(p)
def parse(t):return dt.datetime.strptime(t,'%Y%m%d%H%M%S')

def main():
    OUT.mkdir(exist_ok=True)
    inv=json.loads((BASE/'archive_inventory.json').read_text(encoding='utf8'))
    rows=[r for r in inv['records'] if r['media_type']=='video']
    selections=[]
    for day in ['20261006','20261013','20261015']:
        rs=[r for r in rows if r['date']==day and r['camera']==15 and '070000'<=r['filename_start'][8:]<='140000']
        r=max(rs,key=lambda r:(parse(r['filename_end'])-parse(r['filename_start'])).total_seconds())
        assert r['split']=='train'
        peers=[q['member'] for q in rows if q['date']==day and q['camera']==11 and q['filename_start']<r['filename_end'] and q['filename_end']>r['filename_start']]
        selections.append(dict(**r,camera11_candidate_members=peers))
    save(OUT/'selection_manifest.json',dict(selections=selections,test_pixels_used=0,
         reason='Longest daytime camera15 clips on three training days; selection independent of predictions or desired counts.',
         clock_policy='Filename overlap only proposes camera11 sources. No cross-camera identity or clock alignment has been asserted.'))
    started=time.time();done=[]
    save(OUT/'progress.json',dict(status='running',pid=os.getpid(),completed_sources=0,total_sources=len(selections),started_unix=started))
    with zipfile.ZipFile(inv['archive']) as z:
        for r in selections:
            folder=OUT/r['date'];folder.mkdir(exist_ok=True)
            if (folder/'frames.json').exists():done.append(json.loads((folder/'frames.json').read_text()));continue
            raw=z.read(r['member']);sha=hashlib.sha256(raw).hexdigest()
            c=av.open(io.BytesIO(raw));s=c.streams.video[0];s.thread_type='AUTO';s.codec_context.thread_count=2
            frames=[];base=None;tick=0;native=0
            for f in c.decode(s):
                native+=1
                if f.time is None:continue
                if base is None:base=float(f.time)
                t=float(f.time)-base
                if t+1e-4<tick:continue
                tick=t+4
                full=f.to_image().convert('RGB');small=full.resize((960,540))
                name=f'{len(frames):04d}_{t:09.3f}.jpg'
                small.save(folder/name,quality=94)
                # The larger field includes the entry, scale and nearby storage;
                # full source frame is retained separately for all other regions.
                tile=Image.new('RGB',(600,440));d=ImageDraw.Draw(tile)
                d.text((4,3),f'{r["date"]} cam15 | sample {len(frames)} | video PTS +{t:.3f}s',fill='white')
                tile.paste(small.crop((0,10,310,50)).resize((600,60)),(0,20))
                tile.paste(small.crop((330,0,960,378)).resize((600,360)),(0,80))
                tile.save(folder/('tile_'+name),quality=94)
                frames.append(dict(index=len(frames),source_pts_seconds=round(float(f.time),6),relative_pts_seconds=round(t,6),
                      image=str((folder/name).relative_to(ROOT)),tile=str((folder/('tile_'+name)).relative_to(ROOT)),
                      visible_clock=None,clock_status='needs_visual_reading'))
                if len(frames)%20==0:
                    save(OUT/'progress.json',dict(status='running',pid=os.getpid(),completed_sources=len(done),total_sources=len(selections),
                         current_date=r['date'],sampled_frames=len(frames),native_frames=native,elapsed_seconds=round(time.time()-started,1)))
            c.close()
            sheets=[]
            for i in range(0,len(frames),8):
                sheet=Image.new('RGB',(2400,880))
                for j,fr in enumerate(frames[i:i+8]):sheet.paste(Image.open(ROOT/fr['tile']),(j%4*600,j//4*440))
                p=folder/f'sheet_{i//8:03d}.jpg';sheet.save(p,quality=94);sheets.append(str(p.relative_to(ROOT)))
            result=dict(source=r,source_sha256=sha,native_frames_decoded=native,samples=frames,sheets=sheets,
                    status='unlabelled_sequence_for_visual_review',sample_interval_pts_seconds=4,
                    limitation='Sampled frames are for screening, not proof of continuous action. Refine native source around each candidate before accepting temporal boundaries.')
            save(folder/'frames.json',result);done.append(result)
            print(r['date'],len(frames),'samples',len(sheets),'sheets',flush=True)
            save(OUT/'progress.json',dict(status='running',pid=os.getpid(),completed_sources=len(done),total_sources=len(selections),elapsed_seconds=round(time.time()-started,1)))
    save(OUT/'extraction_complete.json',dict(status='sequence_evidence_extracted_not_labelled',sources=len(done),
        sampled_frames=sum(len(x['samples']) for x in done),elapsed_seconds=round(time.time()-started,1),test_pixels_used=0))
    save(OUT/'progress.json',dict(status='extraction_complete',completed_sources=len(done),total_sources=len(selections),dataset_ready=False))
if __name__=='__main__':
    try:main()
    except Exception as e:
        OUT.mkdir(exist_ok=True);save(OUT/'extraction_failure.json',dict(error=str(e),traceback=traceback.format_exc()));raise
