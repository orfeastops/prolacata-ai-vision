"""Apply explicit assistant visual decisions, export only approved training data."""
import copy,collections,json,re,shutil,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from prepare_arrival_expansion_v8 import ROOT,OUT,save,sha

BASE=OUT.parent
REVIEW=ROOT/'outputs/facility_dataset/temporal_pipeline/sequence_annotation_v4/arrival_dataset_v8_review'
APPROVED_NATIVE={
 'S00_00':'Ten raised blocks with individually visible top faces.',
 'S01_03':'Empty patterned tray positions; no cheese on conveyor.',
 'S03_02':'Empty patterned tray positions.', 'S03_03':'Empty tray, different hand/background configuration.',
 'S04_00':'Empty tray positions.', 'S04_01':'Empty conveyor; white cheese in the tank is background.',
 'S04_02':'Two raised blocks remain on near row; other visible positions empty.',
 'S04_03':'Empty tray positions.',
 'S05_00':'Empty tray; remove two extra boxes on background objects outside tray.',
 'S05_02':'Empty conveyor; cheese and gloves in tank are background.',
 'S05_03':'Four raised blocks; remaining positions empty.',
 'S07_00':'Empty belt and tank corner; hard negative.',
 'S08_00':'Two raised blocks; eight empty positions.',
 'S08_01':'Empty tray.',
 'S08_03':'Empty-looking tray with one glove-obscured position; mark that position unknown.',
 'S10_00':'Four raised blocks along near row; six empty positions.',
 'S11_00':'Empty belt with cheese in background tank.',
 'S11_03':'Empty belt with glove and cheese in background tank.',
 'S12_02':'False empty-position box lies in tank, not conveyor: remove it.',
 'S02_02':'Validation: empty tray.',
 'S02_03':'Validation: two raised blocks; nine visible positions, tenth beyond image edge.',
 'S09_00':'Validation: three raised blocks along near row.',
 'S06_00':'Validation: empty conveyor.',
 'S06_01':'Validation: cleaning motion over empty conveyor.',
 'S13_00':'Validation: empty conveyor on the second day.',
 'S13_03':'Validation: worker and gloves beside empty conveyor.',
}
VALIDATION_SOURCES={'S02','S06','S09','S13'}

def normalize_tray(labels):
    positions=[d for d in labels if d['class_id']!=2]
    if not positions:return []
    # Same convention as v7: extent of visible annotated positions, one tray.
    boxes=[d['bbox'] for d in positions]
    return positions+[dict(class_id=2,bbox=[min(b[0] for b in boxes),min(b[1] for b in boxes),
        max(b[2] for b in boxes),max(b[3] for b in boxes)],label_origin='union_of_reviewed_visible_positions')]

def main():
    dataset=BASE/'dataset'
    if (BASE/'training_started.json').exists():raise RuntimeError('Frozen dataset: training already started')
    new=[];decisions=[]
    native=json.loads((OUT/'candidates.json').read_text())
    mined=json.loads((BASE/'arrival_candidates/candidates.json').read_text())
    for batch,rows in [('native',native),('mined',mined)]:
        for r in rows:
            ident=r['id']
            approved=ident in APPROVED_NATIVE if batch=='native' else ident!='S08_M01'
            reason=APPROVED_NATIVE.get(ident,'Ten distinct raised blocks reviewed on the tray.') if approved else (
                'False box on tank/held cheese and uncertain lower tray extent.' if ident=='S08_M01' else
                'Not confidently approved: occlusion, partial tray extent or ambiguous/missing position labels. Excluded entirely.')
            decisions.append(dict(id=ident,batch=batch,approved=approved,reason=reason,reviewer='assistant_visual_review',human_verified=False))
            if not approved:continue
            r=copy.deepcopy(r);labels=r.pop('draft_labels')
            if ident=='S05_00':labels=[d for i,d in enumerate(labels) if i not in [10,11]]
            if ident=='S08_03':labels[9]['class_id']=3
            if ident=='S12_02':labels=[]
            labels=normalize_tray(labels)
            for d in labels:
                d.pop('confidence',None)
                d['label_origin']='assistant-reviewed model proposal, approximate box'
            r.update(labels=labels,approved=True,review_status='assistant_reviewed',human_verified=False,
                review_reason=reason,split='val' if r['source_id'] in VALIDATION_SOURCES else 'train')
            new.append(r)
    # Keep previously reviewed anchors with their original split; do not alter v7.
    old=json.loads((BASE.parent/'arrival_counter_v7/dataset_manifest.json').read_text())['records']
    records=[]
    for oldr in old:
        r=copy.deepcopy(oldr);r['id']='V7_'+r['id'];r['approved']=True
        r['review_reason']='Previously visually reviewed v7 anchor; unchanged labels.'
        r['label_origin']='legacy assistant-authored v7 grid envelope';records.append(r)
    records+=new
    # No source hash crosses splits; holdout date and September cannot enter.
    train_hashes={r['source_sha256'] for r in records if r['split']=='train'}
    val_hashes={r['source_sha256'] for r in records if r['split']=='val'}
    assert not train_hashes & val_hashes
    assert all(r.get('date','') not in ['20261003','20260926'] for r in records)
    sources=json.loads((OUT/'sources.json').read_text())
    paths={s['sha256']:s['path'] for s in sources}
    for sid in ['O01','O21']:
        meta=json.loads((BASE.parent/'sequence_annotation_v4/tray_inventory_review'/sid/'frames.json').read_text())
        paths[meta['source_sha256']]=meta['source_file']
    intervals={h:re.search(r'DVR_(\d{14})_(\d{14})',Path(paths[h]).name).groups() for h in train_hashes|val_hashes}
    for th in train_hashes:
        for vh in val_hashes:
            ta,tb=intervals[th];va,vb=intervals[vh]
            assert tb<=va or vb<=ta,('Overlapping train/val camera time',paths[th],paths[vh])
    REVIEW.mkdir(parents=True,exist_ok=True);(REVIEW/'images').mkdir(exist_ok=True)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16);panels=[]
    for r in records:
        im=Image.open(r['image']).convert('RGB');w,h=im.size;assert (w,h)==(270,170)
        folder=dataset/'images'/r['split'];folder.mkdir(parents=True,exist_ok=True)
        labelfolder=dataset/'labels'/r['split'];labelfolder.mkdir(parents=True,exist_ok=True)
        target=folder/(r['id']+'.png');im.save(target);r['original_image']=r['image'];r['image']=str(target)
        lines=[]
        for label in r['labels']:
            x1,y1,x2,y2=label['bbox'];assert 0<=x1<x2<=w and 0<=y1<y2<=h,(r['id'],label)
            lines.append(f"{label['class_id']} {(x1+x2)/(2*w):.8f} {(y1+y2)/(2*h):.8f} {(x2-x1)/w:.8f} {(y2-y1)/h:.8f}")
        (labelfolder/(r['id']+'.txt')).write_text('\n'.join(lines),encoding='utf-8')
        panel=Image.new('RGB',(540,400),'#101824');panel.paste(im.resize((540,340)),(0,60));d=ImageDraw.Draw(panel)
        count=sum(l['class_id']==0 for l in r['labels'])
        d.text((5,5),f"{r['id']} | {r['split']} | annotated visible cheese: {count}",font=font,fill='white')
        d.text((5,29),'REVIEWED ANNOTATION - NOT A NEW MODEL RESULT',font=font,fill='#fcd34d')
        for label in r['labels']:
            b=label['bbox'];b=[b[0]*2,b[1]*2+60,b[2]*2,b[3]*2+60];color=['lime','cyan','yellow','orange'][label['class_id']]
            d.rectangle(b,outline=color,width=2)
        panel.save(REVIEW/'images'/(r['id']+'.jpg'),quality=96);panels.append(panel)
    for split in ['train','val']:
        (dataset/(split+'.txt')).write_text('\n'.join(r['image'] for r in records if r['split']==split),encoding='utf-8')
    names=['cheese_on_tray','empty_tray_position','tray','obscured_position']
    (dataset/'data.yaml').write_text(f'path: {dataset.as_posix()}\ntrain: train.txt\nval: val.txt\nnames:\n'+''.join(f'  {i}: {name}\n' for i,name in enumerate(names)),encoding='utf-8')
    save(BASE/'annotation_decisions.json',decisions)
    save(BASE/'dataset_manifest.json',dict(records=records,source_files=paths,train_val_source_disjoint=True,
        train_val_camera_time_disjoint=True,heldout_date='2026-10-03',september_used=False,
        origin='Assistant visually reviewed labels; model proposals do not become truth without review.',
        box_precision='Approximate tray position envelopes, not segmentation masks.',
        no_automatic_training_from_pending_candidates=True))
    summary=dict(training_images=sum(r['split']=='train' for r in records),validation_images=sum(r['split']=='val' for r in records),
        training_videos=len(train_hashes),validation_videos=len(val_hashes),new_reviewed_images=len(new),
        clean_candidates_reviewed=len(decisions),new_candidates_excluded=sum(not d['approved'] for d in decisions),
        legacy_images=len(old),training_started=False,heldout_date='2026-10-03',test_date_extracted=False,
        training_visible_count_histogram=dict(sorted(collections.Counter(sum(l['class_id']==0 for l in r['labels']) for r in records if r['split']=='train').items())),
        manifest_sha256=sha(BASE/'dataset_manifest.json'),human_verified=False)
    save(BASE/'dataset_ready.json',summary)
    for start in range(0,len(panels),4):
        sheet=Image.new('RGB',(1080,800),'#101824')
        for j,panel in enumerate(panels[start:start+4]):sheet.paste(panel,((j%2)*540,(j//2)*400))
        sheet.save(BASE/f'approved_review_{start//4:02d}.jpg',quality=96)
    cards=[]
    for r in records:
        count=sum(l['class_id']==0 for l in r['labels'])
        cards.append(f"<article><h2>{r['id']} <small>{r['split']}</small></h2><img loading='lazy' src='images/{r['id']}.jpg' alt='Reviewed training annotation {r['id']}'><p>{r['review_reason']}</p><p>Visible cheese labels: {count}. This is an annotation, not a model prediction or arrival count.</p></article>")
    page=f"""<!doctype html><html lang='en'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>V8 reviewed arrival dataset</title>
    <style>body{{font:16px/1.5 system-ui;background:#101824;color:#eee;margin:0}}main{{max-width:1200px;margin:auto;padding:28px}}h1{{line-height:1.2}}h2{{font-size:20px}}small{{color:#93c5fd}}.notice{{padding:20px;border-left:4px solid #facc15;background:#253247}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:20px}}article{{background:#1e293b;padding:18px;border-radius:12px}}img{{width:100%;height:auto}}a{{color:#93c5fd}}pre{{white-space:pre-wrap}}@media(max-width:500px){{main{{padding:14px}}.grid{{grid-template-columns:1fr}}}}</style>
    <main><h1>V8 · Reviewed images for cheese-on-tray detection</h1><div class='notice'><b>Dataset preparation complete. No v8 training or accuracy result yet.</b><p>{summary['training_images']} training images from {summary['training_videos']} videos; {summary['validation_images']} validation images from {summary['validation_videos']} different videos. Dates: October 1 and October 21.</p><p>{len(new)} newly reviewed images, plus {len(old)} existing anchors. {summary['new_candidates_excluded']} uncertain candidates excluded. October 3 is reserved and has not been extracted for this experiment.</p></div>
    <p>These are assistant-reviewed annotations, not independently human-verified ground truth. Green = cheese; cyan = empty position; orange = obscured position; yellow = visible tray extent. Quantity labels refer to visible blocks in an image, including partially emptied trays, not confirmed arrival totals.</p>
    <p>Initial random-seek DVR images were rejected for decoding corruption. The replacement candidates were decoded sequentially. DVR nominal frame counts overstated native frames; the broad sequential pass retained 56 actual frames, followed by 19 targeted arrival candidates. Every one of these 75 candidates was visually reviewed. None of the damaged draft images enters this dataset.</p>
    <p>Uncertainty remains around small/occluded blocks and approximate bounding boxes. The next stage is training and continuous-video testing, with missed and repeated arrivals measured separately.</p>
    <p><a href='dataset_ready.json'>Dataset summary</a> · <a href='annotation_decisions.json'>All review decisions</a></p><div class='grid'>{''.join(cards)}</div></main></html>"""
    (REVIEW/'review.html').write_text(page,encoding='utf-8')
    for name in ['dataset_ready.json','annotation_decisions.json']:shutil.copy2(BASE/name,REVIEW/name)
    (BASE/'STATUS_EN.txt').write_text('V8 dataset prepared; training not started.\n'+json.dumps(summary,indent=2)+'\nUse only dataset/train.txt and dataset/val.txt. Never glob draft or rejected candidates.\n',encoding='utf-8')
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
