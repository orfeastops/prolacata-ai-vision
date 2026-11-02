"""Read the visible DVR clock; export linked experimental storage predictions."""
import argparse
import json
import re
import subprocess
from datetime import date,datetime
from pathlib import Path
import cv2


def clock_read(crop,path):
    # Input is the unscaled original frame[45:95,25:550].
    gray=cv2.cvtColor(crop[16:37,341:513],cv2.COLOR_BGR2GRAY)
    readings=[]
    for threshold,scale in ((90,4),(120,4),(90,6)):
        _,binary=cv2.threshold(gray,threshold,255,cv2.THRESH_BINARY)
        binary=cv2.copyMakeBorder(binary,12,12,12,12,cv2.BORDER_CONSTANT,value=255)
        cv2.imwrite(str(path),cv2.resize(binary,None,fx=scale,fy=scale))
        proc=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass',
             '-File',str(Path(__file__).with_name('read_dvr_clock.ps1')),
             '-ImagePath',str(path.resolve())],capture_output=True,text=True,timeout=30)
        if proc.returncode:raise RuntimeError(proc.stderr)
        text=json.loads(proc.stdout)['text']
        match=re.search(r'(?<!\d)(\d{2})\s*:\s*(\d{2})\s*:\s*(\d{2})(?!\d)',text)
        value=':'.join(match.groups()) if match else None
        if value:
            try:datetime.strptime(value,'%H:%M:%S')
            except ValueError:value=None
        readings.append(dict(threshold=threshold,scale=scale,text=text,time=value))
    valid=[r['time'] for r in readings if r['time']]
    accepted=valid[0] if len(valid)>=2 and len(set(valid))==1 else None
    return accepted,readings


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--date',required=True);p.add_argument('--export-dir',required=True)
    a=p.parse_args();date.fromisoformat(a.date)
    out=Path(a.run);destination=Path(a.export_dir);destination.mkdir(parents=True,exist_ok=True);result=json.loads((out/'result.json').read_text());records=[];pending=[];audit=[]
    for e in result['exits']:
        if e['status']!='storage_proposal':continue
        crop=cv2.imread(str(out/e['clock_evidence']))
        clock,readings=clock_read(crop,destination/f"ocr_track_{e['track']}.png")
        audit.append(dict(track=e['track'],pts_s=e['pts_s'],readings=readings,accepted_clock=clock))
        if clock:records.append(dict(event='tank_storage',date=a.date,time=clock))
        else:pending.append(dict(track=e['track'],reason='unreadable_or_disagreeing_clock'))
    (destination/'storage_predictions.json').write_text(json.dumps(records,indent=2))
    (destination/'clock_audit.json').write_text(json.dumps(dict(readings=audit,pending=pending,
        date_provenance='Explicit source date; time from visible DVR glyphs, not PTS',
        warning='Two preprocessing agreements do not prove OCR accuracy; independent visual check required.'),indent=2))
    print(json.dumps(dict(storage_predictions=len(records),pending_clock=len(pending))))


if __name__=='__main__':main()
