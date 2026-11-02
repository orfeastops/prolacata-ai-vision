"""Freeze a candidate selection; no training/upload or release approval."""
import json, hashlib, re
from pathlib import Path
from collections import Counter, defaultdict
from PIL import Image

R=Path(__file__).resolve().parents[1]
B=R/'outputs/tank_transfer_training_v1/dataset_v2'
V=B.parent/'dataset_v1/pilot_v1'
def read(p): return json.loads(p.read_text(encoding='utf8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]; excluded=[]
for r in read(V/'detector_manifest.json'):
    a=r['original_annotation']; o=a['object_review']['frozen_overlay']
    assert sha(R/o['image'])==o['sha256']
    assert a['object_review']['decision']=='accepted_for_roi_tank_detection'
    assert sha(V/r['image'])==r['image_sha256']==sha(R/a['image'])
    assert sha(V/r['label'])==r['label_sha256']
    rows.append(dict(id='v1_'+r['id'],origin='v1_pilot',date=r['date'],camera=r['camera'],split=r['split'],image=str((V/r['image']).relative_to(R)),image_sha256=r['image_sha256'],boxes=a['boxes_xyxy'],source_name=r['source'],source_sample_group=f"{r['source']}|{r['source_pts_seconds']}",native_sha256=None,overlay=str(o['image']),overlay_sha256=o['sha256'],annotation=a))
for folder,flag in [('frame_review','approved_for_full_frame_detection'),('object_review','approved_for_roi_detection'),('negative_review','approved_for_detection')]:
    for p in sorted((B/folder).glob('*.json')):
        a=read(p)
        if not a.get(flag):
            excluded.append(dict(annotation=str(p.relative_to(B)),reason='not_approved'));continue
        assert sha(R/a['image'])==a['image_sha256']
        if 'sample' not in a: a['sample']=a['source_frame']
        if 'boxes' not in a: a['boxes']=[{'xyxy':x} for x in a['boxes_xyxy']]
        if 'overlay_review' not in a:
            assert sha(R/a['overlay'])==a['overlay_sha256']
            a['overlay_review']={'image':str((R/a['overlay']).relative_to(B))}
        assert sha(R/a['sample']['image'])==a['sample']['sha256']
        overlay=B/a['overlay_review']['image']; assert overlay.exists()
        rows.append(dict(id=a['id'],origin=folder,date=a['date'],camera=a['camera'],split=a['split'],image=a['image'],image_sha256=a['image_sha256'],boxes=[x['xyxy'] for x in a['boxes']],source_name=a['source'].get('basename',Path(a['source'].get('available_path','')).name),source_sample_group=a['sample']['sha256'],native_sha256=a['sample']['sha256'],source_sha256=a.get('source_sha256'),overlay=str(overlay.relative_to(R)),overlay_sha256=sha(overlay),annotation_file=str(p.relative_to(R)),annotation=a))

# Keep full-frame labels rather than overweighting the same scene with its ROI.
full_hashes={r['native_sha256'] for r in rows if r['origin']=='frame_review'}
selected=[]; seen={}
for r in rows:
    assert r['date']!='20261028'
    assert r['split']==('val' if r['date']=='20261017' else 'train')
    with Image.open(R/r['image']) as im: w,h=im.size
    r.update(width=w,height=h)
    for x1,y1,x2,y2 in r['boxes']: assert 0<=x1<x2<=w and 0<=y1<y2<=h, r['id']
    if r['origin']=='object_review' and r['native_sha256'] in full_hashes:
        excluded.append(dict(id=r['id'],reason='native_frame_already_selected_as_full_frame'));continue
    digest=r['image_sha256']
    if digest in seen:
        prev=seen[digest];assert prev['split']==r['split']
        assert prev['boxes']==r['boxes'], 'Conflicting labels on identical image'
        excluded.append(dict(id=r['id'],reason='exact_image_duplicate',kept=prev['id']));continue
    seen[digest]=r;selected.append(r)

groups=defaultdict(list)
for r in selected: groups[r['source_sample_group']].append(r)
assert all(len({r['split'] for r in g})==1 for g in groups.values())
# Filename intervals flag possible overlapping clips; they do not certify clocks.
sources={}
unparsed=[]
for r in selected:
    m=re.search(r'DVR_(\d{14})_(\d{14})_',r['source_name'])
    if m:
        start,end=m.groups();assert start[:8]==end[:8]==r['date']
        sources[(r['camera'],r['source_name'])]=(start,end,r['split'])
    else: unparsed.append(r['source_name'])
overlaps=[]
items=list(sources.items())
for i,((cam,name),(s,e,split)) in enumerate(items):
    for ((cam2,name2),(s2,e2,split2)) in items[i+1:]:
        if cam==cam2 and max(s,s2)<=min(e,e2):
            assert split==split2
            overlaps.append(dict(camera=cam,source_a=name,source_b=name2,split=split,status='possible_temporal_overlap_same_split'))
out=dict(status='selection_audited_export_pending',records=selected,excluded=excluded,counts_by_origin=dict(Counter(r['origin'] for r in selected)),counts_by_split=dict(Counter(r['split'] for r in selected)),images=len(selected),boxes=sum(len(r['boxes']) for r in selected),native_or_source_sample_groups=len(groups),same_sample_multiple_crops=[dict(group=k,ids=[r['id'] for r in g]) for k,g in groups.items() if len(g)>1],possible_source_time_overlaps=overlaps,unparsed_source_names=sorted(set(unparsed)),checks=dict(image_hashes=True,native_hashes_v2=True,legacy_frozen_overlay_hashes=True,overlay_files_frozen=True,geometry=True,day_splits=True,exact_image_duplicates_removed=True,cross_split_source_time_overlap_absent=not unparsed),limitations=['Filename intervals are not synchronized camera clocks.','Same-day temporal redundancy is flagged, not certified absent.','Legacy source PTS group is not reconciled to v2 decoded-frame hashes.','Single-class detector labels do not train content classification.','Separate sequence count validation remains pending.'],release_ready=False)
(B/'finite_package_selection_draft.json').write_text(json.dumps(out,indent=2),encoding='utf8')
print(json.dumps({k:out[k] for k in ['images','boxes','counts_by_origin','counts_by_split','native_or_source_sample_groups']}))
print('Possible same-split source interval overlaps:',len(overlaps),'unparsed sources:',len(set(unparsed)))
