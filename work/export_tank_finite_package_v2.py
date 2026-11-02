"""Local, audited single-class detector export. No training or upload."""
import json,hashlib,re,shutil,html
from pathlib import Path
from collections import Counter,defaultdict
from PIL import Image
R=Path(__file__).resolve().parents[1];B=R/'outputs/tank_transfer_training_v1/dataset_v2'
S=json.loads((B/'finite_package_selection_draft.json').read_text()); rows=S['records']
O=B/'pilot_v2_local'
assert not O.exists(), 'Existing export must be reviewed, not overwritten'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def interval(r):
    m=re.search(r'DVR_(\d{14})_(\d{14})_',r['source_name']);assert m
    return m.groups()
# Connected components conservatively keep all overlapping source intervals
# together. They are correlated observations, never independent evaluation units.
parent=list(range(len(rows)))
def root(i):
    while parent[i]!=i:
        parent[i]=parent[parent[i]];i=parent[i]
    return i
for i,a in enumerate(rows):
    s,e=interval(a)
    for k,b in enumerate(rows[:i]):
        if a['camera']!=b['camera']:continue
        t,u=interval(b)
        if max(s,t)<=min(e,u):
            assert a['date']==b['date'] and a['split']==b['split']
            parent[root(i)]=root(k)
groups=defaultdict(list)
for i,r in enumerate(rows):groups[root(i)].append(r['id'])
group_ids={k:f'source_group_{n:03d}' for n,k in enumerate(sorted(groups))}
manifest=[];O.mkdir()
for i,r in enumerate(rows):
    assert r['date']!='20261028' and r['split']==('val' if r['date']=='20261017' else 'train')
    src=R/r['image'];assert sha(src)==r['image_sha256'];assert sha(R/r['overlay'])==r['overlay_sha256']
    with Image.open(src) as im:w,h=im.size
    lines=[]
    for x1,y1,x2,y2 in r['boxes']:
        assert 0<=x1<x2<=w and 0<=y1<y2<=h
        lines.append(f'0 {(x1+x2)/(2*w):.10f} {(y1+y2)/(2*h):.10f} {(x2-x1)/w:.10f} {(y2-y1)/h:.10f}')
    dest=O/'images'/r['split']/(r['id']+'.jpg');label=O/'labels'/r['split']/(r['id']+'.txt')
    dest.parent.mkdir(parents=True,exist_ok=True);label.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(src,dest);label.write_text('\n'.join(lines)+ ('\n' if lines else ''),encoding='utf8')
    assert sha(dest)==r['image_sha256']
    # Decode written normalized labels back to pixel geometry.
    for line,expected in zip(label.read_text().splitlines(),r['boxes']):
        c,x,y,bw,bh=map(float,line.split());assert c==0
        actual=[(x-bw/2)*w,(y-bh/2)*h,(x+bw/2)*w,(y+bh/2)*h]
        assert max(abs(a-b) for a,b in zip(actual,expected))<0.001
    manifest.append(dict(id=r['id'],origin=r['origin'],date=r['date'],camera=r['camera'],split=r['split'],image=str(dest.relative_to(O)),label=str(label.relative_to(O)),image_sha256=sha(dest),label_sha256=sha(label),boxes=len(lines),source_name=r['source_name'],source_sample_group=r['source_sample_group'],temporal_source_group=group_ids[root(i)],native_sha256=r['native_sha256'],original_image=r['image'],reviewed_overlay=r['overlay'],reviewed_overlay_sha256=r['overlay_sha256']))
assert len(list((O/'images').rglob('*.jpg')))==len(manifest)
assert len(list((O/'labels').rglob('*.txt')))==len(manifest)
assert len({r['image_sha256'] for r in manifest})==len(manifest)
(O/'data.yaml').write_text('path: '+O.as_posix()+'\ntrain: images/train\nval: images/val\nnames:\n  0: tank\n',encoding='utf8')
(O/'detector_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
(O/'temporal_groups.json').write_text(json.dumps([dict(id=group_ids[k],images=v) for k,v in groups.items()],indent=2))
report=dict(status='local_detector_export_verified_counting_validation_pending',images=len(manifest),boxes=sum(r['boxes'] for r in manifest),by_split=dict(Counter(r['split'] for r in manifest)),by_origin=dict(Counter(r['origin'] for r in manifest)),days=sorted({r['date'] for r in manifest}),cameras=sorted({r['camera'] for r in manifest}),temporal_source_groups=len(groups),exact_image_duplicates=0,cross_split_temporal_groups=0,test_day_pixels_opened=0,training_started=False,uploaded=False,release_ready=False,checks=['image and overlay hashes','box geometry and YOLO round trip','one label file per image','day-disjoint validation17/test28 excluded','exact image deduplication','overlapping filename intervals grouped within same split'],limitations=['Overlapping source clips and repeated crops are correlated; temporal grouping is conservative and does not establish camera synchronization.','Mixed crops and12full frames; full-frame deployment performance must be measured.','Class0 tank only; this export does not train cheese/fullness recognition.','Separate held-out sequence manual counts still required for counting evaluation.'])
(O/'package_report.json').write_text(json.dumps(report,indent=2))
(O/'review.html').write_text('<!doctype html><meta charset="utf-8"><h1>Local detector package — counting validation pending</h1><pre>'+html.escape(json.dumps(report,indent=2))+'</pre><a href="detector_manifest.json">Manifest</a> · <a href="temporal_groups.json">Correlated source groups</a>',encoding='utf8')
print(json.dumps(report))
