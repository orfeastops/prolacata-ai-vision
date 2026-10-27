"""Six new October review clips with native timestamps and no model labels."""
import json,hashlib,time
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/facility_dataset/temporal_pipeline/sequence_annotation_v4'

def main():
    cv2.setNumThreads(2)
    sources=json.loads((OUT/'candidate_sources.json').read_text())
    manifest=[];started=time.time()
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22)
    small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17)
    for number,source in enumerate(sources,1):
        sid=f'C{number:02d}';dest=OUT/sid;dest.mkdir(exist_ok=True)
        prior=json.loads((dest/'annotation.json').read_text(encoding='utf-8')) if (dest/'annotation.json').exists() else None
        if prior is not None and (dest/'timed_review.webm').exists():
            manifest.append(prior);continue
        assert source['date'] in ('2026-10-01','2026-10-21')
        start=max(0,source['probed_duration_s']/2-15);stop=start+30
        path=Path(source['local_path'])
        with path.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==source['sha256']
        cap=cv2.VideoCapture(str(path));assert cap.isOpened()
        images=[];times=[];indices=[];i=0
        while True:
            ok,frame=cap.read()
            if not ok:raise RuntimeError(f'Source ended before requested interval {sid}')
            t=cap.get(cv2.CAP_PROP_POS_MSEC)/1000
            if t>=stop:break
            if t>=start:
                images.append(frame[720:1080,800:1440].copy());times.append(t);indices.append(i)
            i+=1
        cap.release()
        assert len(images)>200 and np.all(np.diff(indices)==1) and np.all(np.diff(times)>0)
        relative=np.array(times)-times[0]
        display_duration=times[-1]-times[0]+float(np.median(np.diff(times)))
        fps=len(images)/display_duration
        video=dest/'timed_review.webm'
        writer=cv2.VideoWriter(str(video),cv2.VideoWriter_fourcc(*'VP80'),fps,(1280,820))
        assert writer.isOpened()
        for j,frame in enumerate(images):
            canvas=Image.new('RGB',(1280,820),(17,24,39));d=ImageDraw.Draw(canvas)
            d.text((20,10),f'{sid}  |  {source["date"]}  |  ΧΡΟΝΟΣ: {relative[j]:06.2f} s  |  ΚΑΡΕ: {j:04d}',font=font,fill='white')
            d.text((20,43),'Σημειώνουμε πραγματικές μεταφορές μπλοκ. Δεν εμφανίζονται προβλέψεις μοντέλου.',font=small,fill='#bfdbfe')
            canvas.paste(Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)).resize((1280,720)),(0,80))
            writer.write(cv2.cvtColor(np.asarray(canvas),cv2.COLOR_RGB2BGR))
        writer.release()
        sheet=Image.new('RGB',(1280,4*270),'white');sd=ImageDraw.Draw(sheet)
        for k,target in enumerate(np.linspace(0,float(relative[-1]),12)):
            j=int(np.argmin(abs(relative-target)));x=k%3*426;y=k//3*270
            sheet.paste(Image.fromarray(cv2.cvtColor(images[j],cv2.COLOR_BGR2RGB)).resize((426,240)),(x,y+30))
            sd.text((x+5,y+4),f'{sid}  t={relative[j]:.2f}s',font=small,fill='black')
        sheet.save(dest/'overview.jpg',quality=92)
        check=cv2.VideoCapture(str(video));decoded=0
        while check.read()[0]:decoded+=1
        check.release();assert decoded==len(images)
        record=dict(clip_id=sid,date=source['date'],source_sha256=source['sha256'],
            source_basename=source['basename'],source_encoded_interval_s=[start,stop],
            original_first_pts_s=times[0],original_last_pts_s=times[-1],
            native_frame_count=len(images),native_source_indices=[indices[0],indices[-1]],
            native_relative_timestamps_s=np.round(relative,6).tolist(),
            playback_fps=fps,playback_duration_s=display_duration,
            all_native_frames_preserved=True,preview_spacing='constant playback spacing; burned timestamps and annotation UI use original variable PTS',
            media_path=f'{sid}/timed_review.webm',source_clock_verified=False,
            selection='New October source not in earlier review batches; time-stratified selection',
            role='training_candidate_pending_expert_review',expert_review_complete=False,
            total_added_blocks=None,events=[],negatives=[],
            boundary_instruction='Mark a pickup already in progress or a release beyond the clip as boundary/unknown, not zero',
            september_used=False,october3_used=False)
        if prior is not None:
            assert prior['source_sha256']==record['source_sha256'],'Do not apply prior reviews to a different source'
            for key in ('expert_review_complete','total_added_blocks','events','negatives','role'):
                if key in prior:record[key]=prior[key]
        (dest/'annotation.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
        manifest.append(record)
        (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
        (OUT/'progress.json').write_text(json.dumps(dict(stage='preparing',completed=len(manifest),total=len(sources),elapsed_s=time.time()-started)),encoding='utf-8')
        print(f'{sid} ready: {len(images)} original frames, verified video decode',flush=True)
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'progress.json').write_text(json.dumps(dict(stage='complete',completed=len(manifest),total=len(sources),elapsed_s=time.time()-started)),encoding='utf-8')

if __name__=='__main__':main()
