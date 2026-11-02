"""Package reviewed detector ROIs separately from production-cycle evidence."""
import json, hashlib, shutil, html
from pathlib import Path
from collections import Counter
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/tank_transfer_training_v1/dataset_v1'
OUT=BASE/'pilot_v1'
def read(p): return json.loads(p.read_text(encoding='utf8'))
def save(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
OUT.mkdir(exist_ok=True)
records=read(BASE/'image_annotations_draft.json')['records']
manifest=[]
for r in records:
    if r['annotation_status']!='roi_boxes_reviewed_assistant': continue
    review=r['object_review']
    assert review['decision']=='accepted_for_roi_tank_detection'
    assert r['date'] not in ['20261025','20261028']
    split='val' if r['date']=='20261017' else 'train'
    assert r['split'] in ([split,'validation'] if split=='val' else [split])
    src=ROOT/r['image']; assert digest(src)==r['sha256']==review['image_sha256']
    overlay=review['frozen_overlay']; assert digest(ROOT/overlay['image'])==overlay['sha256']
    with Image.open(src) as im: w,h=im.size
    assert (w,h)==(r['width'],r['height'])
    lines=[]
    for x1,y1,x2,y2 in r['boxes_xyxy']:
        assert 0<=x1<x2<=w and 0<=y1<y2<=h
        lines.append(f'0 {(x1+x2)/(2*w):.9f} {(y1+y2)/(2*h):.9f} {(x2-x1)/w:.9f} {(y2-y1)/h:.9f}')
    images=OUT/'images'/split; labels=OUT/'labels'/split
    images.mkdir(parents=True,exist_ok=True); labels.mkdir(parents=True,exist_ok=True)
    dst=images/(r['id']+'.jpg'); shutil.copy2(src,dst)
    label=labels/(r['id']+'.txt'); label.write_text('\n'.join(lines)+ ('\n' if lines else ''),encoding='utf8')
    assert digest(dst)==r['sha256']
    manifest.append(dict(id=r['id'],date=r['date'],camera=r['camera'],split=split,image=str(dst.relative_to(OUT)),label=str(label.relative_to(OUT)),image_sha256=r['sha256'],label_sha256=digest(label),box_count=len(lines),source=r['source'],source_pts_seconds=r['source_pts_seconds'],roi_on_960x540=r['roi_on_960x540'],original_annotation=r))
train={r['image_sha256'] for r in manifest if r['split']=='train'}
val={r['image_sha256'] for r in manifest if r['split']=='val'}
assert not train&val
save(OUT/'detector_manifest.json',manifest)
(OUT/'data.yaml').write_text('path: '+OUT.as_posix()+'\ntrain: images/train\nval: images/val\nnames:\n  0: tank\n',encoding='utf8')
sequences=read(BASE/'reviewed_sequence_labels.json')
save(OUT/'sequence_evidence.json',{'scope':'Existing reviewed evidence preserved, not new labels. Stage observations are independent of complete-cycle acceptance. Missing stages remain missing.','sequences':sequences})
report=dict(status='pilot_detector_package_verified_not_production_system_release',images=len(manifest),boxes=sum(r['box_count'] for r in manifest),images_by_split=dict(Counter(r['split'] for r in manifest)),images_by_day=dict(Counter(r['date'] for r in manifest)),images_by_camera=dict(Counter(r['camera'] for r in manifest)),empty_roi_images=sum(r['box_count']==0 for r in manifest),complete_cycles=sum(r['review_status']=='accepted_complete_cycle' for r in sequences),training_started=False,test_pixels_used=0,scope='Single-class tank detection on the saved ROIs only. Does not train cheese/load recognition, cross-camera identity, weight, tracking or production counting.',limitations=['Small pilot sample; model performance has not been measured.','Inference must use matching camera crops or separately validated full-frame handling.','Day-disjoint validation retained; complete production-event validation remains incomplete.','50 cycles and1000 images were planning targets, not detector release prerequisites.'],checks={'source_and_export_image_hashes':True,'approved_overlay_hashes':True,'box_geometry':True,'day_split':True,'exact_image_split_duplicates_absent':True})
save(OUT/'package_report.json',report)
cards=[]
for s in sequences:
    if s['review_status']!='accepted_complete_cycle': continue
    stages=[]
    for st in s.get('stages',[]):
        pics=[p for e in st.get('evidence',[]) for p in e.get('image_evidence',[])][:1]
        pic=''
        if pics:
            import os
            rel=Path(os.path.relpath(ROOT/pics[0],OUT)).as_posix()
            pic=f'<img loading="lazy" src="{html.escape(rel)}">'
        stages.append('<div><b>'+html.escape(st['stage'])+'</b><p>'+html.escape(str(st.get('visible_camera_clock_interval','')))+ '</p>'+pic+'</div>')
    cards.append('<h2>'+html.escape(s['sequence_id'])+'</h2><section>'+''.join(stages)+'</section>')
(OUT/'review.html').write_text('<!doctype html><meta charset="utf-8"><title>Tank pilot v1</title><style>body{font:16px system-ui;margin:30px}section{display:flex;gap:12px;flex-wrap:wrap}section div{width:300px}img{width:300px}pre{white-space:pre-wrap}</style><h1>Πιλοτικό σύνολο ανίχνευσης και διαδρομών</h1><p>Οι εικόνες εκπαιδεύουν την ανίχνευση δεξαμενής στο συγκεκριμένο ROI. Οι παρακάτω διαδρομές παρουσιάζουν ήδη ελεγμένα στοιχεία. Δεν έχει γίνει εκπαίδευση ή μέτρηση ακρίβειας. Κάθε εικόνα σταδίου είναι ενδεικτική· η τεκμηρίωση περιλαμβάνει τις ακολουθίες.</p><a href="package_report.json">Έλεγχοι πακέτου</a> · <a href="detector_manifest.json">Πηγές εικόνων</a> · <a href="sequence_evidence.json">Στοιχεία διαδρομών</a><pre>'+html.escape(json.dumps(report,ensure_ascii=False,indent=2))+'</pre>'+''.join(cards),encoding='utf8')
print(json.dumps(report,ensure_ascii=False,indent=2))
