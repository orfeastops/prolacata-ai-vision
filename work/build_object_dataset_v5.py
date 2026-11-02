"""Build auditable payload detection labels; no inference-produced ground truth."""
import json, hashlib, shutil, argparse
import cv2, numpy as np
from pathlib import Path
from collections import Counter
from PIL import Image,ImageDraw,ImageFont
from object_labels_v5 import LABELS
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/facility_dataset/temporal_pipeline'
OUT=BASE/'placement_counter_v5/object_expansion'
FONT=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16)
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,o):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def review():
    rows={r['id']:r for r in read(OUT/'candidates.json')}
    tiles=[]
    for key,labels in sorted(LABELS.items()):
        assert key in rows,key
        for side,q,box in labels:
            im=Image.open(rows[key]['image']).convert('RGB');x1,y1,x2,y2=box
            assert 0<=x1<x2<=640 and 0<=y1<y2<=360
            cx=(x1+x2)//2;cy=(y1+y2)//2;size=max(110,x2-x1+30,y2-y1+30)
            left=max(0,min(640-size,cx-size//2));top=max(0,min(360-size,cy-size//2))
            crop=im.crop((left,top,left+size,top+size)).resize((236,236))
            d=ImageDraw.Draw(crop);s=236/size
            d.rectangle(((x1-left)*s,(y1-top)*s,(x2-left)*s,(y2-top)*s),outline='lime',width=2)
            tile=Image.new('RGB',(240,264),'#111827');tile.paste(crop,(2,28))
            ImageDraw.Draw(tile).text((3,4),f'{key} {side} q={q}',font=FONT,fill='white');tiles.append(tile)
    target=OUT/'box_review';target.mkdir(exist_ok=True)
    for k in range(0,len(tiles),16):
        sheet=Image.new('RGB',(960,1056),'#111827')
        for j,t in enumerate(tiles[k:k+16]):sheet.paste(t,((j%4)*240,(j//4)*264))
        sheet.save(target/f'boxes_{k//16:02d}.jpg',quality=96)
    print(json.dumps(dict(frames=len(LABELS),positive=sum(bool(v) for v in LABELS.values()),negative=sum(not v for v in LABELS.values()),loads=len(tiles),quantities=dict(Counter(str(q) for v in LABELS.values() for s,q,b in v)),pages=(len(tiles)+15)//16)),flush=True)
def build():
    candidates={r['id']:r for r in read(OUT/'candidates.json')}
    sequences=read(OUT/'sequences.json');selection=read(OUT/'selection.json')
    forbidden=set(selection['forbidden_sources']);rows=[];seen=set()
    validation_clips={'D03','D07','D08'}
    for key,labels in sorted(LABELS.items()):
        r=dict(candidates[key]);r.update(labels=labels,provenance='assistant_visual_anchor',anchor=key,
            split='val' if r['clip'] in validation_clips else 'train')
        rows.append(r);seen.add(key)
    # Only one native frame in either direction, never a long tracker-generated label.
    # Unknown quantity and widely separated loads are not propagated. Validation
    # remains anchor-only. Complete frames are accepted only if every box passes.
    propagated=[]
    for key,labels in sorted(LABELS.items()):
        r=candidates[key];seq=sequences[r['clip']]
        if not labels or r['clip'] in validation_clips or any(q==0 or b[2]-b[0]>145 for s,q,b in labels):continue
        original=cv2.imread(r['image'])
        for delta in [-1,1]:
            i=r['frame_index']+delta;newkey=f"{r['clip']}_{i:04d}"
            if newkey in seen or not 0<=i<len(seq['files']):continue
            if abs(seq['times'][i]-r['time_s'])>.121:continue
            target=cv2.imread(seq['files'][i]);newlabels=[];scores=[]
            for side,q,(x1,y1,x2,y2) in labels:
                template=original[y1:y2,x1:x2]
                a=max(0,x1-22);b=max(0,y1-22);c=min(640,x2+22);d=min(360,y2+22)
                match=cv2.matchTemplate(target[b:d,a:c],template,cv2.TM_CCOEFF_NORMED)
                _,score,_,location=cv2.minMaxLoc(match)
                if score<.88:break
                dx=a+location[0]-x1;dy=b+location[1]-y1
                if abs(dx)>=21 or abs(dy)>=21:break
                newlabels.append((side,q,[x1+dx,y1+dy,x2+dx,y2+dy]));scores.append(score)
            if len(newlabels)!=len(labels):continue
            nr=dict(r,id=newkey,frame_index=i,source_frame_index=seq['source_frame_indices'][i],
                time_s=seq['times'][i],image=seq['files'][i],labels=newlabels,anchor=key,
                provenance='one_native_frame_template_propagation',matching_scores=scores,split='train')
            propagated.append(nr);seen.add(newkey)
    write(OUT/'propagation_proposals.json',propagated)
    # This list is filled only after the resulting frame crops are visually checked.
    approved_path=OUT/'propagation_approved.json'
    approved=set(read(approved_path)['approved_ids']) if approved_path.exists() else set()
    rows.extend(r for r in propagated if r['id'] in approved)
    for r in rows:assert r['source_sha256'] not in forbidden
    train_sha={r['source_sha256'] for r in rows if r['split']=='train'}
    val_sha={r['source_sha256'] for r in rows if r['split']=='val'}
    assert not train_sha&val_sha
    dataset=OUT/'dataset';mapping={1:0,2:1,3:2,0:3}
    for r in rows:
        imgdir=dataset/'images'/r['split'];lbldir=dataset/'labels'/r['split']
        imgdir.mkdir(parents=True,exist_ok=True);lbldir.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(r['image'],imgdir/f"{r['id']}.jpg")
        lines=[]
        for side,q,(x1,y1,x2,y2) in r['labels']:
            lines.append(f'{mapping[q]} {(x1+x2)/1280:.8f} {(y1+y2)/720:.8f} {(x2-x1)/640:.8f} {(y2-y1)/360:.8f}')
        (lbldir/f"{r['id']}.txt").write_text('\n'.join(lines),encoding='utf-8')
        r['image_sha256']=sha(imgdir/f"{r['id']}.jpg")
    (dataset/'data.yaml').write_text(f'path: {dataset.as_posix()}\ntrain: images/train\nval: images/val\nnames:\n  0: carried_load_1\n  1: carried_load_2\n  2: carried_load_3\n  3: carried_load_quantity_unknown\n',encoding='utf-8')
    manifest=dict(schema=5,rows=rows,source_split_disjoint=True,forbidden_sources=sorted(forbidden),
        validation_clips=sorted(validation_clips),native_roi=[800,720,1440,1080],
        counting_unit='one carried payload, not one hand or one frame',
        unknown_quantity_label=0,labels_author='assistant visual review; quantity partly expert-confirmed on C01',
        note='Approximate boxes; assistant annotations are not independent expert ground truth. Adjacent frames are not independent events.',
        annotation_script_sha256=sha(Path(__file__).with_name('object_labels_v5.py')),
        counts={split:dict(frames=sum(r['split']==split for r in rows),positive=sum(r['split']==split and bool(r['labels']) for r in rows),negative=sum(r['split']==split and not r['labels'] for r in rows),sources=len({r['source_sha256'] for r in rows if r['split']==split})) for split in ['train','val']},
        manual_anchor_frames=len(LABELS),approved_neighbor_frames=len(approved),proposed_neighbor_frames=len(propagated))
    write(OUT/'dataset_manifest.json',manifest)
    # Native context (complete frame), anchor/neighbor pairs, to verify that no other
    # load was silently introduced and that translation has not moved onto a tray.
    tiles=[]
    for r in propagated:
        im=Image.open(r['image']).convert('RGB');d=ImageDraw.Draw(im)
        for side,q,box in r['labels']:
            d.rectangle(box,outline='lime',width=2);d.text((box[0],max(0,box[1]-16)),f'{side}:{q}',font=FONT,fill='lime')
        tile=Image.new('RGB',(640,392),'#111827');tile.paste(im,(0,32))
        ImageDraw.Draw(tile).text((5,4),f"{r['id']} <- {r['anchor']}",font=FONT,fill='white');tiles.append(tile)
    dest=OUT/'neighbor_review';dest.mkdir(exist_ok=True)
    for k in range(0,len(tiles),6):
        sheet=Image.new('RGB',(1280,1176),'#111827')
        for j,t in enumerate(tiles[k:k+6]):sheet.paste(t,((j%2)*640,(j//2)*392))
        sheet.save(dest/f'neighbors_{k//6:02d}.jpg',quality=94)
    print(json.dumps({k:v for k,v in manifest.items() if k in ['counts','manual_anchor_frames','approved_neighbor_frames','proposed_neighbor_frames']}),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',action='store_true');a=p.parse_args()
    build() if a.build else review()
