import datetime as dt
from record_tank_boundary_review_20261031 import read,save,merge,ROOT,BASE,OUT
run='sequence_review_20261101_77';state=read(OUT/'continuation_state.json')
if run in state.get('completed_curation_runs',[]):raise SystemExit('Already recorded')
stamp=dt.datetime.now(dt.timezone.utc).isoformat();name='screening045350_cam11';p=OUT/'sequence_review/20261005'/name/'frames.json';m=read(p)
clocks=['04:53:49','04:54:20','04:54:50','04:55:20','04:55:50','04:56:20','04:56:50','04:57:20','04:57:50','04:58:20','04:58:50','04:59:20','04:59:50','05:00:20','05:00:50','05:01:20'];assert len(m['samples'])==16
merge(OUT/'screening_source_reviews.json',[dict(review_id='20261005/'+name,date='20261005',split='train',camera=11,reviewer='assistant_visual_review',reviewed_at=stamp,source_member=m['source']['member'],source_sha256=m['source_sha256'],frames_manifest=str(p.relative_to(ROOT)),sampled_frames_visually_reviewed=16,reviewed_sheets=m['sheets'],accepted_complete_cycle=False,review_scope='All16 chronological full-field sample tiles and clocks inspected;30-second sampling does not resolve intervening transport.',observation='Many open gray and beige tanks already present at first sample. Workers place and unfold blue plastic liners in the tanks; plastic must not be classified as product filling. Some tank positions change between samples; no new production cycle or precise crossing assigned. No fresh product filling observed. Useful candidate native object images, not yet box-annotated.',visible_clock_anchors=[dict(sample_index=i,source_pts_seconds=s['source_pts_seconds'],relative_pts_seconds=s['relative_pts_seconds'],visible_camera_clock=clocks[i],clock_read_uncertainty_seconds=1,image=s['image'],usable_for_clock_alignment=False) for i,s in enumerate(m['samples'])])],'review_id')
inv=read(BASE/'archive_inventory.json')
for r in inv['records']:
 if r['member']==m['source']['member']:r.update(pixel_inspected=True,sha256=m['source_sha256'])
save(BASE/'archive_inventory.json',inv)
state['last_completed'].append('Batch77:16 new5Oct camera11 samples04:53:49-05:01:20 reviewed. Existing tanks and blue liner installation observed, not fresh product filling. No new cycle or box annotations; native frames suitable for later instance review.')
state['priority_next']=['Review remaining other-day production candidates for complete-cycle diversity.5Oct screening045350_cam11 is liner preparation, not product filling; avoid rechecking as a fresh-fill candidate. Native5Oct images may add early/empty tank coverage after separate box overlay review.']+[x for x in state['priority_next'] if x.startswith('25/28')]
state['completed_curation_runs'].append(run);state['updated_at']=stamp;save(OUT/'continuation_state.json',state)
