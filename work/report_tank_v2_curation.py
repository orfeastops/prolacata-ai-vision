"""Rebuild auditable curation counters without changing extraction manifests."""
import json, hashlib
from pathlib import Path
from datetime import datetime, timezone
from PIL import Image

R = Path(__file__).resolve().parents[1]
B = R / 'outputs/tank_transfer_training_v1/dataset_v2'
def read(p):
    return json.loads(p.read_text(encoding='utf8'))
def save(p, d):
    p.write_text(json.dumps(d, indent=2), encoding='utf8')

manifests = {p.parent.name: p for folder in ['screening','supplemental_screening']
             for p in (B/folder).glob('*/*/*/frames.json')}
reviewed, dense = set(), set()
for p in [B/'initial_visual_triage.json', *sorted(B.glob('visual_triage_batch*.json'))]:
    data = read(p)
    rows = data if isinstance(data, list) else data.get('observations', [data])
    for row in rows:
        if not row.get('dense_manifest') and row.get('source_id') not in manifests:
            continue  # Annotation follow-ups must not inflate screening coverage.
        target = dense if row.get('dense_manifest') else reviewed
        for i in row.get('sample_indices', []):
            if row.get('dense_manifest'):
                ref = Path(row['dense_manifest'])
                if not ref.is_absolute(): ref = R/ref if (R/ref).exists() else B/ref
                target.add((str(ref.resolve()), i))
            else:
                target.add((row['source_id'], i))
checks = []
for p in (B/'object_review').glob('*.json'):
    a = read(p)
    if not a.get('approved_for_roi_detection'):
        continue
    im = R/a['image']
    w,h = Image.open(im).size
    boxes = a.get('boxes_xyxy', [b['xyxy'] for b in a.get('boxes', [])])
    checks.append(dict(id=a['id'], boxes=len(boxes), date=a['date'], camera=a['camera'],
        hash_ok=hashlib.sha256(im.read_bytes()).hexdigest()==a['image_sha256'],
        geometry_ok=bool(boxes) and all(0<=x1<x2<=w and 0<=y1<y2<=h for x1,y1,x2,y2 in boxes),
        split_ok=a['date']!='20261028' and a['split']==('val' if a['date']=='20261017' else 'train')))
index = {}
candidate_count = 0
coverage = {}
source_bucket = {}
source_lengths = {}
manifest_cache = {}
for p in manifests.values():
    m=read(p);candidate_count+=len(m['samples'])
    manifest_cache[p.parent.name] = m
    key = str(m['source']['date']) + '/cam' + str(m['source']['camera'])
    source_bucket[p.parent.name] = key
    source_lengths[p.parent.name] = len(m['samples'])
    c = coverage.setdefault(key, dict(date=m['source']['date'], camera=m['source']['camera'], split=m['split'], candidate_frames=0, screening_triaged=0, approved_unique_native_frames=0))
    c['candidate_frames'] += len(m['samples'])
    if 'supplemental_screening' not in p.parts:
        index.setdefault(m['source_sha256'], []).append(str(p.relative_to(B)))
rows=[]
for a in read(B/'supplemental_availability_audit.json')['records']:
    rows.append(dict(sha256=a['sha256'], date=a['date'], camera=a['camera'],
        available_path=a['available_path'], archive_manifest_matches=index.get(a['sha256'], [])))
matched=sum(bool(r['archive_manifest_matches']) for r in rows)
save(B/'supplemental_hash_overlap_progress.json', dict(archive_hashes_compared=len(index),
    supplemental_records_compared=len(rows), exact_matches=matched, records=rows,
    scope='Inventory supplemental hashes versus extracted archive byte hashes. Non-matches remain pending, not proven unique.'))
negative_checks=[]
for p in (B/'negative_review').glob('*.json'):
    a=read(p)
    if not a.get('approved_for_detection'): continue
    negative_checks.append(dict(id=a['id'],
        hash_ok=hashlib.sha256((R/a['image']).read_bytes()).hexdigest()==a['image_sha256'],
        empty_labels_ok=a['boxes']==[],
        split_ok=a['date']!='20261028' and a['split']==('val' if a['date']=='20261017' else 'train')))
latest_batch=sorted(B.glob('visual_triage_batch*.json'))[-1].name
full_checks=[]
for p in (B/'frame_review').glob('*.json'):
    a=read(p)
    if not a.get('approved_for_full_frame_detection'): continue
    w,h=Image.open(R/a['image']).size
    full_checks.append(dict(id=a['id'],boxes=len(a['boxes']),
        hash_ok=hashlib.sha256((R/a['image']).read_bytes()).hexdigest()==a['image_sha256'],
        geometry_ok=all(0<=b['xyxy'][0]<b['xyxy'][2]<=w and 0<=b['xyxy'][1]<b['xyxy'][3]<=h for b in a['boxes']),
        split_ok=a['date']!='20261028' and a['split']==('val' if a['date']=='20261017' else 'train')))
extra_manifests = list((B/'dense_review').glob('*/unreviewed_extra_files.json'))
unindexed_extras = sum(read(p)['count'] for p in extra_manifests)
local_audit=read(B/'supplemental_local_hash_verification.json')
state=dict(updated_at=datetime.now(timezone.utc).isoformat(),release_ready=False,
    supplemental_extraction=read(B/'supplemental_progress.json') if (B/'supplemental_progress.json').exists() else None,
    supplemental_local_hashes_verified=local_audit['verified'],
    supplemental_local_hash_mismatches=local_audit['mismatches'],
    completed_manifests=len(manifests),candidate_frames=candidate_count,
    retained_unindexed_dense_extras_unreviewed=unindexed_extras,
    screening_frames_visually_triaged=len(reviewed),screening_frames_not_triaged=candidate_count-len(reviewed),
    dense_samples_visually_triaged=len(dense),approved_new_roi_images=len(checks),
    approved_new_boxes=sum(c['boxes'] for c in checks),full_frame_labels_approved=len(full_checks),
    full_frame_boxes_approved=sum(c['boxes'] for c in full_checks),full_frame_checks=full_checks,
    approved_full_frame_positives=sum(c['boxes']>0 for c in full_checks),
    approved_full_frame_negatives=sum(c['boxes']==0 for c in full_checks),
    supplemental_exact_hash_matches_in_partial_archive=matched,
    approved_new_negative_patches=len(negative_checks),negative_patch_checks=negative_checks,
    extraction_snapshot=read(B/'progress.json'),roi_checks=checks)
groups = {}
for folder, flag in [('object_review','approved_for_roi_detection'), ('frame_review','approved_for_full_frame_detection'), ('negative_review','approved_for_detection')]:
    for path in (B/folder).glob('*.json'):
        a = read(path)
        if not a.get(flag): continue
        sample = a.get('sample', a.get('source_frame', {}))
        h = sample.get('sha256') if isinstance(sample, dict) else None
        if not h: continue
        g = groups.setdefault(h, dict(native_frame_sha256=h, source_sha256=a.get('source_sha256'), date=a['date'], camera=a['camera'], split=a['split'], annotations=[]))
        assert g['split'] == a['split'], 'Related annotations cross splits'
        g['annotations'].append(str(path.relative_to(B)))
save(B/'reviewed_source_frame_groups.json', dict(updated_at=state['updated_at'], unique_native_frames=len(groups), groups=list(groups.values()), note='Only approved annotations. Crops and full frames of the same native image share one group; nearby temporal scenes are not proven independent.'))
state['approved_annotations_unique_native_frames_with_hash'] = len(groups)
for sid, i in reviewed:
    assert 0 <= i < source_lengths[sid], 'Triage index outside actual manifest'
    coverage[source_bucket[sid]]['screening_triaged'] += 1
for g in groups.values():
    key = str(g['date']) + '/cam' + str(g['camera'])
    if key in coverage: coverage[key]['approved_unique_native_frames'] += 1
state['coverage_by_day_camera'] = [coverage[k] for k in sorted(coverage)]
screening_triaged_hashes = {manifest_cache[sid]['samples'][i]['sha256'] for sid,i in reviewed}
dense_manifest_cache = {}
dense_triaged_hashes = set()
for ref,i in dense:
    if ref not in dense_manifest_cache: dense_manifest_cache[ref] = read(Path(ref))
    m = dense_manifest_cache[ref]
    assert m['source']['date'] != '20261028', 'Protected day in dense triage'
    assert m['split'] == ('val' if m['source']['date']=='20261017' else 'train')
    assert 0 <= i < len(m['samples']), 'Dense triage index outside manifest'
    dense_triaged_hashes.add(m['samples'][i]['sha256'])
state['dense_triaged_unique_native_hashes'] = len(dense_triaged_hashes)
state['dense_triaged_hashes_already_in_screening_triage'] = len(dense_triaged_hashes & screening_triaged_hashes)
state['visually_triaged_unique_native_hashes_total'] = len(dense_triaged_hashes | screening_triaged_hashes)
save(B/'curation_progress.json',state)
save(B/'incremental_roi_checks.json',dict(scope='All approved v2 ROI records; not full release checks',records=checks))
html=f'''<meta charset="utf-8"><h1>Dataset v2: curation in progress</h1>
<p>Screening: {candidate_count} extracted frames; {len(reviewed)} visually triaged;
{candidate_count-len(reviewed)} not triaged. Dense sample entries triaged: {len(dense)} (may overlap screening).</p>
<p>Unique visually triaged native image hashes across screening and dense: {state["visually_triaged_unique_native_hashes_total"]}. Dense hashes already present in screening triage: {state["dense_triaged_hashes_already_in_screening_triage"]}. Unique pixels do not establish independent temporal scenes.</p>
<p>Retained out-of-window dense files, unindexed and unreviewed: {unindexed_extras}. Excluded from triage and approved labels; not part of the screening pool above.</p>
<p>Approved new ROI images: {len(checks)}; boxes: {sum(c['boxes'] for c in checks)}.
Full-frame images approved: {len(full_checks)} (positive: {state["approved_full_frame_positives"]}, negative: {state["approved_full_frame_negatives"]}); boxes: {sum(c['boxes'] for c in full_checks)}.
Related ROIs and full frames share a source group; these counts are not independent scenes.
Visual triage is not label approval. Release is NOT ready.</p>
<p>Approved detector-negative patches: {len(negative_checks)}. These are not negative temporal sequences.</p>
<p>Supplemental inventory: 1069 hashes compared against {len(index)} extracted archive hashes;
{matched} exact matches. Remaining records are not proven unique.</p>
<p>Local supplemental file content verified: {local_audit['verified']}/1069;
hash mismatches: {local_audit['mismatches']}. Byte-hash overlap audit is complete; temporal/content overlap review remains pending.</p>
<p><a href="temporal_discontinuity_observations.json">Observed clock/PTS discontinuities and uncertainty</a></p>
<p>28 October untouched final test; 17 October validation. Further annotation, temporal review,
supplemental coverage and release checks remain pending.</p>
<p><a href="curation_progress.json">Auditable counters and ROI checks</a> |
<a href="candidate_integrity_audit.json">Candidate hashes, JPEG integrity and exact duplicates</a> |
<a href="{latest_batch}">Latest visual observations</a></p>
<p>This durable curation report is also saved as curation_review.html.
Both screening extractions have finished. Candidate extraction is not annotation approval.</p>'''
html += '<h2>Coverage by day and camera</h2><p>Screening triage is not annotation approval. Approved native groups can include denser follow-ups. These are sample counts, not whole-day tracking coverage.</p><table border=1><tr><th>Date</th><th>Camera</th><th>Split</th><th>Candidates</th><th>Triaged</th><th>Approved native groups</th></tr>'
for c in state['coverage_by_day_camera']:
    html += f"<tr><td>{c['date']}</td><td>{c['camera']}</td><td>{c['split']}</td><td>{c['candidate_frames']}</td><td>{c['screening_triaged']}</td><td>{c['approved_unique_native_frames']}</td></tr>"
html += '</table>'
html += '<h2>Reviewed full-frame overlays</h2>'
for c in full_checks:
    html += f'<p><a href="frame_review/{c["id"]}_overlay.jpg">{c["id"]}: {c["boxes"]} boxes</a></p>'
(B/'curation_review.html').write_text(html,encoding='utf8')
(B/'review.html').write_text(html,encoding='utf8')
print(json.dumps({k:v for k,v in state.items() if k not in ['roi_checks','extraction_snapshot']}))
