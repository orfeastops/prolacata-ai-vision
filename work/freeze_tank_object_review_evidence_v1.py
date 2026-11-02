"""Persist per-image overlays so regenerated contact sheets cannot change evidence.

Renders the already approved hashes/boxes. Does not claim another visual review
or approve previously unreviewed annotations. Previous registry is retained.
"""
import hashlib,json,datetime as dt
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'outputs/tank_transfer_training_v1';OUT=BASE/'dataset_v1'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=OUT/'object_review_decisions.json';registry=json.loads(p.read_text('utf8'));draft={r['id']:r for r in json.loads((BASE/'detector_v1/visual_annotation_draft.json').read_text('utf8'))['records']}
 history=OUT/'review_history/object_decisions_before_frozen_overlays_20261031.json'
 if not history.exists():history.write_text(json.dumps(registry,ensure_ascii=False,indent=2),encoding='utf8')
 target=OUT/'accepted_object_overlays';target.mkdir(exist_ok=True)
 created=0
 for d in registry['reviews']:
  r=draft[d['id']];assert digest(ROOT/r['image'])==d['image_sha256']==r['sha256']
  assert hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest()==d['boxes_sha256']
  if d.get('frozen_overlay'):
   assert digest(ROOT/d['frozen_overlay']['image'])==d['frozen_overlay']['sha256'];continue
  stem=f"{d['id']}_{d['image_sha256'][:12]}_{d['boxes_sha256'][:12]}";impath=target/(stem+'.png');mp=target/(stem+'.json')
  im=Image.open(ROOT/r['image']).convert('RGB');draw=ImageDraw.Draw(im)
  for i,b in enumerate(r['boxes_xyxy']):draw.rectangle(b,outline='#00ff66',width=3);draw.text((b[0]+3,b[1]+3),str(i),fill='yellow')
  im.save(impath)
  data=dict(id=d['id'],source_image=r['image'],source_image_sha256=d['image_sha256'],boxes_xyxy=r['boxes_xyxy'],boxes_sha256=d['boxes_sha256'],overlay=str(impath.relative_to(ROOT)),overlay_sha256=digest(impath),rendered_at=dt.datetime.now(dt.timezone.utc).isoformat(),policy='Re-render of previously approved image and box hashes; no new annotation or renewed visual-review claim.')
  mp.write_text(json.dumps(data,indent=2),encoding='utf8')
  old=d.get('evidence',[]);volatile=[x for x in old if '/sheets/labels_' in x.replace('\\','/')]
  if volatile:d['prior_contact_sheet_evidence']=volatile
  d['evidence']=[x for x in old if x not in volatile]+[str(impath.relative_to(ROOT)),str(mp.relative_to(ROOT))]
  d['frozen_overlay']=dict(image=str(impath.relative_to(ROOT)),sha256=data['overlay_sha256'],manifest=str(mp.relative_to(ROOT)))
  created+=1
 p.write_text(json.dumps(registry,indent=2,ensure_ascii=False),encoding='utf8')
 print(json.dumps(dict(frozen_review_overlays=len(registry['reviews']),newly_rendered=created,annotations_changed=0)))
if __name__=='__main__':main()
