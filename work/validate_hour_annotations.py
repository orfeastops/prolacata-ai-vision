"""Validate user-exported observations without treating them as reconciled totals."""
import argparse,json,re,math,hashlib
from pathlib import Path

CLIPS={f'clip_{i:03d}' for i in range(58,65)}
KINDS={'storage','uncertain','not_storage','duplicate','filling_only'}
STATES={'unreviewed','partial','complete_events','complete_zero'}
def validate(data):
    errors=[];warnings=[];seen=set()
    if data.get('schema')!='room11-hour-manual-v1':errors.append('Unexpected schema')
    if data.get('date')!='2026-10-28':errors.append('Unexpected date')
    if data.get('window')!=['09:15:00','10:15:00']:errors.append('Unexpected scoring window')
    events=data.get('events',[]);coverage=data.get('coverage',{})
    if not isinstance(events,list) or not isinstance(coverage,dict):return {'errors':['Invalid events/coverage structure']}
    for n,e in enumerate(events):
        if not isinstance(e,dict):errors.append(f'Event {n}: invalid structure');continue
        ident=e.get('id')
        if not isinstance(ident,str) or not ident or ident in seen:errors.append(f'Event {n}: missing/duplicate id')
        if isinstance(ident,str):seen.add(ident)
        if e.get('kind') not in KINDS:errors.append(f'Event {n}: invalid kind')
        clock=e.get('camera_time','')
        if e.get('kind')=='filling_only' and clock is None:pass
        elif not isinstance(clock,str) or not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d',clock):errors.append(f'Event {n}: invalid clock')
        elif not '09:15:00'<=clock<'10:15:00':warnings.append(f'Event {n}: outside scored hour; keep as context only')
        for field in ['exit','placement']:
            pos=e.get(field)
            if field=='exit' and e.get('kind')=='filling_only':
                if pos is not None:errors.append(f'Event {n}: filling-only must not invent exit')
                continue
            if field=='placement' and pos is None and e.get('kind') not in {'storage','filling_only'}:continue
            if not isinstance(pos,dict):errors.append(f'Event {n}: missing {field}');continue
            seconds=pos.get('video_seconds')
            if pos.get('clip') not in CLIPS or isinstance(seconds,bool) or not isinstance(seconds,(float,int)) or not math.isfinite(seconds) or seconds<0:
                errors.append(f'Event {n}: invalid {field} position')
        if isinstance(e.get('placement'),dict) and isinstance(e.get('exit'),dict) and e['placement'].get('clip')!=e['exit'].get('clip'):
            warnings.append(f'Event {n}: cross-file association requires boundary evidence')
    for clip,c in coverage.items():
        if clip not in CLIPS or not isinstance(c,dict) or c.get('status') not in STATES:errors.append(f'Invalid coverage for {clip}');continue
        if c['status']=='complete_zero' and any(e.get('kind')=='storage' and e.get('exit',{}).get('clip')==clip for e in events if isinstance(e,dict)):
            errors.append(f'{clip}: zero storage conflicts with recorded storage event')
    return {'errors':errors,'warnings':warnings,'submitted_events':len(events),
        'fully_reviewed_clips':[c for c in sorted(CLIPS) if coverage.get(c,{}).get('status','').startswith('complete')],
        'reconciled_storage_total':None,'note':'Validation is structural only. Check duplicates, original clock, source/proxy time mapping and coverage before scoring.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('input',type=Path);a=p.parse_args()
    raw=a.input.read_bytes();result=validate(json.loads(raw.decode('utf-8-sig')))
    result['input_sha256']=hashlib.sha256(raw).hexdigest()
    print(json.dumps(result,ensure_ascii=True,indent=2))
    raise SystemExit(1 if result['errors'] else 0)
