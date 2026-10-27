import pathlib,json,shutil
from PIL import Image,ImageDraw
root=pathlib.Path('outputs/feta_training');records=json.loads((root/'manual_annotations.json').read_text())
extra={
'day01_extra_061238.jpg':[],
'day01_extra_063143.jpg':[],
'day01_extra_064048.jpg':[[297,236,332,272],[326,224,351,261]],
'day01_extra_074941.jpg':[[189,293,215,322],[344,225,381,255],[267,166,287,189]],
'day01_extra_084510.jpg':[[269,162,300,191],[311,214,342,238]],
'day01_extra_085239.jpg':[[72,48,101,85]],
'day01_extra_085834.jpg':[],
'day01_extra_095605.jpg':[[60,58,97,86],[102,38,129,64],[110,270,137,298],[189,298,221,326],[280,181,313,209],[418,130,454,163]],
'day01_extra_105257.jpg':[],
'day01_extra_132705.jpg':[],
}
for r in json.loads((root/'extra_manifest.json').read_text()):
 if r['image'] not in extra:continue
 r.update(boxes_xyxy=extra[r['image']],annotation_method='assistant_manual_visual',human_expert_review=False,**{'class':'gloved_hand'})
 records.append(r)
for r in records:
 name=r['image'];split=r['split'];src=root/('extra_images' if 'extra_' in name else 'candidate_images')/name
 for kind in ('images','labels'):(root/'dataset_v2'/kind/split).mkdir(parents=True,exist_ok=True)
 shutil.copyfile(src,root/'dataset_v2/images'/split/name)
 lines=[]
 for x1,y1,x2,y2 in r['boxes_xyxy']:
  assert 0<=x1<x2<=640 and 0<=y1<y2<=360
  lines.append(f'0 {(x1+x2)/1280:.7f} {(y1+y2)/720:.7f} {(x2-x1)/640:.7f} {(y2-y1)/360:.7f}')
 (root/'dataset_v2/labels'/split/pathlib.Path(name).with_suffix('.txt')).write_text('\n'.join(lines))
(root/'manual_annotations_v2.json').write_text(json.dumps(records,indent=2))
(root/'dataset_v2.yaml').write_text(f'path: {(root/"dataset_v2").resolve().as_posix()}\ntrain: images/train\nval: images/val\nnames:\n  0: gloved_hand\n')
sheet=Image.new('RGB',(1280,400*5),'white')
for i,r in enumerate(records[24:]):
 tile=Image.new('RGB',(640,400),'white');tile.paste(Image.open(root/'extra_images'/r['image']),(0,30));d=ImageDraw.Draw(tile);d.text((5,5),r['image'],fill='black')
 for x1,y1,x2,y2 in r['boxes_xyxy']:d.rectangle((x1,y1+30,x2,y2+30),outline='#00ff77',width=2)
 sheet.paste(tile,((i%2)*640,(i//2)*400))
sheet.save(root/'extra_reviewed_labels.jpg')
print({s:{'images':sum(r['split']==s for r in records),'hands':sum(len(r['boxes_xyxy']) for r in records if r['split']==s)} for s in ('train','val')})
