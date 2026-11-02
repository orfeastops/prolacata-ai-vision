"""Individual conveyor-position labels, not hand/load or tank labels.

Assistant-authored position geometry is used for training annotations only.
Inference uses one fixed camera crop, never per-image crop centers or counts.
"""
import json,hashlib
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/facility_dataset/temporal_pipeline'
AUDIT=BASE/'sequence_annotation_v4/tray_inventory_review'
OUT=BASE/'arrival_counter_v7'
ROI=[180,190,450,360]
NAMES=['cheese_on_tray','empty_tray_position','tray','obscured_position']
# Head is the far-row position furthest along the conveyor; offsets follow
# visible physical positions. Classes: C cheese, E empty, U obstructed.
GRIDS=[
 ('O01',3,(350,240),(-27,23),(39,40),'CCCCC','CCCCC'),
 ('O01',20.8,(351,247),(-28,23),(40,40),'CCCCC','CCCCC'),
 ('O01',30,(351,251),(-30,21),(38,40),'EEEEE','EEEEE'),
 ('O01',39,(365,258),(-29,23),(40,40),'CCCCC','CCCCC'),
 ('O01',57.5,(351,247),(-28,23),(39,40),'CCCCC','CCCCC'),
 ('O01',76,(357,243),(-31,23),(36,40),'EEEEE','EEEEE'),
 ('O01',150,(359,234),(-31,23),(35,40),'CECCC','CCCCC'),
 ('O01',157,(359,242),(-31,23),(35,40),'UCCCC','ECCCC'),
 ('O01',159,(359,242),(-31,23),(35,40),'EE CUU'.replace(' ',''),'ECCCC'),
 ('O01',162,(359,242),(-31,23),(35,40),'EEEEE','EECCC'),
 ('O01',164,(359,242),(-31,23),(35,40),'EEEEE','EECEE'),
 # Validation boxes are development annotations; never optimizer input.
 ('O21',37,(354,236),(-29.5,23),(39,40),'CCCCC','CCCCC'),
 ('O21',151.5,(350,242),(-28,23),(39,40),'UEEEE','EEEEE'),
]

def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2),encoding='utf-8')
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def crop(frame):
    return frame[ROI[1]:ROI[3],ROI[0]:ROI[2]].copy()

def labels(head,step,near,far_states,near_states):
    rows=[];all_boxes=[]
    for side,states in enumerate([far_states,near_states]):
        assert len(states)==5
        for n,state in enumerate(states):
            x=head[0]+step[0]*n+near[0]*side;y=head[1]+step[1]*n+near[1]*side
            # Axis-aligned envelope of a rotated rectangular position.
            raw=[x-27,y-29,x+27,y+29]
            b=[max(raw[0],ROI[0]),max(raw[1],ROI[1]),min(raw[2],ROI[2]),min(raw[3],ROI[3])]
            if b[2]-b[0]<8 or b[3]-b[1]<8:continue
            local=[b[0]-ROI[0],b[1]-ROI[1],b[2]-ROI[0],b[3]-ROI[1]]
            rows.append(dict(class_id={'C':0,'E':1,'U':3}[state],bbox=local,slot=f'{side}:{n}',
                clipped=(raw!=b),label_author='assistant_grid_proposal'))
            all_boxes.append(local)
    if all_boxes:
        boxes=np.array(all_boxes)
        rows.append(dict(class_id=2,bbox=[float(boxes[:,0].min()),float(boxes[:,1].min()),
            float(boxes[:,2].max()),float(boxes[:,3].max())],label_author='assistant_visible_tray_extent'))
    return rows

def main():
    if (OUT/'training_started.json').exists():raise RuntimeError('Do not change a started experiment dataset')
    OUT.mkdir(exist_ok=True);dataset=OUT/'dataset'
    metas={sid:json.loads((AUDIT/sid/'frames.json').read_text()) for sid in ['O01','O21']}
    records=[];font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15)
    tiles=[]
    for sid,t,head,step,near,far,front in GRIDS:
        meta=metas[sid];r=min(meta['inspection_frames'],key=lambda r:abs(r['pts_s']-t))
        frame=cv2.imread(str(AUDIT/sid/r['image']));im=crop(frame)
        split='train' if sid=='O01' else 'val';ident=f'{sid}_{t:g}'
        dest=dataset/'images'/split;dest.mkdir(parents=True,exist_ok=True)
        labeldir=dataset/'labels'/split;labeldir.mkdir(parents=True,exist_ok=True)
        cv2.imwrite(str(dest/f'{ident}.png'),im)
        obs=labels(head,step,near,far,front);lines=[]
        for o in obs:
            x1,y1,x2,y2=o['bbox'];h,w=im.shape[:2]
            lines.append(f"{o['class_id']} {(x1+x2)/(2*w):.8f} {(y1+y2)/(2*h):.8f} {(x2-x1)/w:.8f} {(y2-y1)/h:.8f}")
        (labeldir/f'{ident}.txt').write_text('\n'.join(lines))
        records.append(dict(id=ident,split=split,source_id=sid,source_sha256=meta['source_sha256'],
            source_pts_s=r['pts_s'],source_frame_index=r['source_frame_index'],image=str(dest/f'{ident}.png'),
            labels=obs,human_verified=False,approved_after_visual_review=False))
        panel=Image.new('RGB',(540,380),'#101824');pic=Image.fromarray(cv2.cvtColor(im,cv2.COLOR_BGR2RGB)).resize((540,340))
        panel.paste(pic,(0,40));d=ImageDraw.Draw(panel)
        d.text((8,7),f'{ident} | {split} | assistant draft boxes',font=font,fill='white')
        for o in obs:
            b=o['bbox'];b=[b[0]*2,b[1]*2+40,b[2]*2,b[3]*2+40]
            color=['lime','cyan','yellow','orange'][o['class_id']];d.rectangle(b,outline=color,width=2)
            if o['class_id']!=2:d.text((b[0]+2,b[1]+2),['C','E','T','U'][o['class_id']],font=font,fill=color,stroke_width=1,stroke_fill='black')
        tiles.append(panel)
    # The source starts with an empty conveyor in this calibrated camera area.
    for sid,t in [('O01',0)]:
        meta=metas[sid];r=min(meta['inspection_frames'],key=lambda r:abs(r['pts_s']-t))
        frame=cv2.imread(str(AUDIT/sid/r['image']));im=crop(frame);ident=f'{sid}_{t:g}_background'
        dest=dataset/'images/train';cv2.imwrite(str(dest/f'{ident}.png'),im)
        (dataset/'labels/train'/f'{ident}.txt').write_text('')
        records.append(dict(id=ident,split='train',source_id=sid,source_sha256=meta['source_sha256'],
            source_pts_s=r['pts_s'],source_frame_index=r['source_frame_index'],image=str(dest/f'{ident}.png'),
            labels=[],human_verified=False,approved_after_visual_review=False))
        panel=Image.new('RGB',(540,380),'#101824');panel.paste(Image.fromarray(cv2.cvtColor(im,cv2.COLOR_BGR2RGB)).resize((540,340)),(0,40))
        ImageDraw.Draw(panel).text((8,7),ident+' | empty belt proposal',font=font,fill='white');tiles.append(panel)
    # Only the manifest-listed images enter training. Draft files left on disk
    # from annotation QA are not part of either split.
    for split in ['train','val']:
        (dataset/f'{split}.txt').write_text('\n'.join(r['image'] for r in records if r['split']==split),encoding='utf-8')
    for start in range(0,len(tiles),6):
        sheet=Image.new('RGB',(1080,380*((min(6,len(tiles)-start)+1)//2)),'#101824')
        for j,panel in enumerate(tiles[start:start+6]):sheet.paste(panel,((j%2)*540,(j//2)*380))
        sheet.save(OUT/f'annotation_review_{start//6:02d}.jpg',quality=96)
    (dataset/'data.yaml').write_text(f'path: {dataset.as_posix()}\ntrain: train.txt\nval: val.txt\nnames:\n'+''.join(f'  {i}: {n}\n' for i,n in enumerate(NAMES)),encoding='utf-8')
    save(OUT/'dataset_manifest.json',dict(records=records,roi_xyxy_in_640_crop=ROI,
        classes=NAMES,source_disjoint=True,training_source='O01',validation_source='O21',
        annotations='Assistant draft boxes, require overlay review before training',
        inference_has_manual_positions=False,september_used=False,code_sha256=digest(__file__)))
    print('Prepared',len(records),'anchor images; visual approval pending')

if __name__=='__main__':main()
