import datetime as dt
import copy
from record_tank_boundary_review_20261031 import read, save, OUT

run = 'full_context_review_20261101_74'
state = read(OUT/'continuation_state.json')
if run in state.get('completed_curation_runs', []):
    raise SystemExit('Already recorded')
rows = read(OUT/'screening_source_reviews.json')
save(OUT/'review_history/screening_before_20261101_74.json', copy.deepcopy(rows))
stamp = dt.datetime.now(dt.timezone.utc).isoformat()
for row in rows:
    if row['review_id'] not in ['20261015/side_tank133552_cam11', '20261015/side_tank133604_cam11']:
        continue
    meta = read(OUT/'sequence_review'/row['review_id']/'frames.json')
    row['full_frame_context_review'] = {
        'reviewed_at': stamp,
        'reviewer': 'assistant_visual_review',
        'images': [{'image': s['image'], 'sha256': s['image_sha256']} for s in meta['samples']],
        'observation': 'All 11 native full-frame samples across the two windows inspected. Open beige tank remains by left wall; another tank partly visible beyond doorway; pallet jack parked at doorway. Worker walks from foreground to left wash area and back; another worker appears at doorway. No sampled tank crossing or fresh filling established. Foreground machinery occludes lower-right area; previously moved side-tank identity and route remain unresolved. No complete cycle, new distinct negative, or load classification added.',
        'scope': 'Full field of view of existing sampled frames; not exhaustive intervening video frames. Existing sample counts unchanged.'
    }
save(OUT/'screening_source_reviews.json', rows)
state['last_completed'].append('Batch74: full native field of view reviewed for all11 existing samples in side_tank133552_cam11 and side_tank133604_cam11. Worker movement and stationary tanks observed; side-tank route unresolved behind foreground machinery. No duplicate sample counts or new cycle labels.')
state['priority_next'] = ['Continue unreviewed15Oct camera11 source13:37:45 onward; full-context follow-up of two side_tank windows is complete. Skip confirmed6Oct gap; preserve partials.'] + [x for x in state['priority_next'] if x.startswith('25/28')]
state['completed_curation_runs'].append(run)
state['updated_at'] = stamp
state['pause_reason'] = 'Scheduler remains paused; active user-requested curation resumed. Previously requested exports were audited; confirmed gap is skipped.'
save(OUT/'continuation_state.json', state)
