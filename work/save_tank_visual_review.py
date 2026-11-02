"""Persist assistant visual decisions made from chronological evidence sheets."""
import json, sys
from pathlib import Path
root = Path('outputs/tank_door_audit')
date = sys.argv[1]
notes = json.loads((root/f'{date}_clock_notes.json').read_text())
groups = json.loads((root/'proposals'/date/'proposals.json').read_text())
events = []
for key, interval in notes.items():
    idx = int(key)
    g = groups[idx]
    events.append(dict(proposal_id=g['id'], basename=g['basename'], source=g['source'],
        candidate_start=g['start'], candidate_end=g['end'],
        camera_clock_crossing_interval=interval, load='production_cheese', direction='outbound',
        visual_review='Chronological source frames visually reviewed; loaded tank travels from filling area through door.',
        evidence_sheet=f'event_review/{date}/{idx:03}.jpg',
        camera15_match='pending visual cross-camera review', note=''))
result=dict(date=f'{date[:4]}-{date[4:6]}-{date[6:]}',events=events,
    observed_production_exits=len(events),
    scope='Observed exits in available footage. Gaps and unvalidated proposal recall mean this is not a certified full-day total.',
    method='Assistant visual review of motion proposals from 2-second camera11 sampling; not a trained automatic tank counter.')
(root/f'reviewed_{date}.json').write_text(json.dumps(result,indent=2))
print(date,len(events))
