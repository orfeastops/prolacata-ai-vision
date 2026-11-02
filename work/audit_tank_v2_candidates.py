"""Audit extracted candidates only; never open protected test material."""
from pathlib import Path
from collections import defaultdict,Counter
from datetime import datetime,timezone
import json,hashlib
from PIL import Image
B=Path('outputs/tank_transfer_training_v1/dataset_v2')
rows=[]
for folder in ['screening','supplemental_screening']:
 for p in (B/folder).glob('*/*/*/frames.json'):
  m=json.loads(p.read_text(encoding='utf8'));date=m['source']['date']
  assert date!='20261028', 'Protected day in extraction manifests: stop before pixels'
  assert m['split']==('val' if date=='20261017' else 'train')
  for i,s in enumerate(m['samples']):rows.append((p,m,i,s,date))
errors=[];index=defaultdict(list);coverage=Counter();dimensions=Counter()
for p,m,i,s,date in rows:
 f=Path(s['image'])
 try:
  actual=hashlib.sha256(f.read_bytes()).hexdigest()
  if actual!=s['sha256']:errors.append({'image':str(f),'error':'hash_mismatch'})
  with Image.open(f) as im:dimensions[str(im.size)]+=1;im.verify()
  index[actual].append(dict(image=str(f),source_id=p.parent.name,sample_index=i,date=date,split=m['split']))
  coverage[f"{date}/cam{m['source']['camera']}/{m['split']}"]+=1
 except Exception as e:errors.append({'image':str(f),'error':str(e)})
dups=[v for v in index.values() if len(v)>1]
out=dict(updated_at=datetime.now(timezone.utc).isoformat(),scope='Candidate screening images only; no label approval or release certification',candidate_images=len(rows),unique_byte_hashes=len(index),hash_or_jpeg_errors=errors,dimensions=dict(dimensions),coverage=dict(sorted(coverage.items())),exact_duplicate_groups=dups,cross_split_exact_duplicate_groups=[v for v in dups if len({r['split'] for r in v})>1],protected_test_pixels_opened=0,temporal_near_duplicate_review_pending=True,release_ready=False)
(B/'candidate_integrity_audit.json').write_text(json.dumps(out,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in out.items() if k not in ['exact_duplicate_groups','coverage']}))
