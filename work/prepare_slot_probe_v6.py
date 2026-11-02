"""Coordinate inspection aids for assistant-authored local tray-slot labels."""
import json
from pathlib import Path
import cv2
ROOT=Path(__file__).resolve().parents[1]
AUDIT=ROOT/'outputs/facility_dataset/temporal_pipeline/sequence_annotation_v4/tray_inventory_review'
OUT=ROOT/'outputs/facility_dataset/temporal_pipeline/placement_counter_v6/slot_probe'
SAMPLES={'O01':[3,14,20.8,30,39,52,57.5,76,150,157,159,162,164,170],
         'O21':[5,16,37,48,147,149.5,151.5,154]}

def main():
    (OUT/'coordinate_review').mkdir(parents=True,exist_ok=True)
    rows=[]
    for sid,ts in SAMPLES.items():
        meta=json.loads((AUDIT/sid/'frames.json').read_text())
        for t in ts:
            r=min(meta['inspection_frames'],key=lambda r:abs(r['pts_s']-t))
            im=cv2.imread(str(AUDIT/sid/r['image']))
            panel=cv2.resize(im,(1280,720),interpolation=cv2.INTER_NEAREST)
            for x in range(150,481,25):
                cv2.line(panel,(x*2,400),(x*2,719),(60,60,60),1)
                cv2.putText(panel,str(x),(x*2+1,430),cv2.FONT_HERSHEY_SIMPLEX,.42,(0,255,255),1)
            for y in range(225,360,25):
                cv2.line(panel,(300,y*2),(960,y*2),(60,60,60),1)
                cv2.putText(panel,str(y),(302,y*2-2),cv2.FONT_HERSHEY_SIMPLEX,.5,(0,255,255),1)
            ident=f'{sid}_{t:g}'
            cv2.putText(panel,ident,(20,30),cv2.FONT_HERSHEY_SIMPLEX,.8,(255,255,255),2)
            cv2.imwrite(str(OUT/'coordinate_review'/f'{ident}.jpg'),panel)
            rows.append(dict(id=ident,source_id=sid,source_sha256=meta['source_sha256'],
                source_frame_index=r['source_frame_index'],source_pts_s=r['pts_s'],image=str(AUDIT/sid/r['image'])))
    (OUT/'selected_frames.json').write_text(json.dumps(rows,indent=2))
    print(len(rows),'coordinate frames prepared')
if __name__=='__main__':main()
