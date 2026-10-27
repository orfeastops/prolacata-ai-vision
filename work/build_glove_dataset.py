import json,pathlib,shutil
from PIL import Image,ImageDraw
root=pathlib.Path('outputs/feta_training')
# Manual visual annotations in 640x360 crop coordinates. Blue caps/rims excluded.
boxes={
'day01_s000.jpg':[[191,301,218,327],[344,205,378,237],[424,130,455,152]],
'day01_s004.jpg':[[282,257,316,289],[222,288,267,330],[290,153,326,187],[259,139,280,161]],
'day01_s008.jpg':[[242,164,265,185],[261,209,298,235],[159,276,184,303]],
'day01_s012.jpg':[[226,150,247,181],[244,185,280,214],[149,264,173,288]],
'day01_s016.jpg':[[189,292,218,321],[344,183,383,215],[422,130,456,155]],
'day01_s020.jpg':[[164,260,204,283],[196,330,232,359],[326,202,349,228],[391,177,414,211]],
'day01_s024.jpg':[[144,222,165,244],[334,260,368,298],[394,244,424,282]],
'day01_s028.jpg':[[312,306,335,337],[263,348,292,360],[345,230,380,259],[287,191,306,217]],
'day01_s032.jpg':[[158,267,195,295],[176,91,199,114],[182,119,220,146]],
'day01_s040.jpg':[[281,153,301,181],[315,203,340,229]],
'day01_s048.jpg':[[260,257,287,274],[346,205,380,239],[428,131,456,151]],
'day01_s056.jpg':[[138,237,162,273],[344,205,380,241],[428,131,456,151]],
'day21_060247.jpg':[],
'day21_064214.jpg':[],
'day21_072014.jpg':[[252,141,287,176],[340,202,377,244],[177,301,226,337]],
'day21_080016.jpg':[[258,158,287,189],[339,196,379,251],[179,301,230,337]],
'day21_093700.jpg':[[0,120,18,143],[238,181,258,210],[264,223,284,244]],
'day21_100642.jpg':[],
'day21_103811.jpg':[],
'day21_110008.jpg':[[257,156,282,189],[339,194,378,244],[185,298,223,341]],
'day21_115130.jpg':[[383,145,416,174],[409,160,437,193],[170,302,192,338],[185,315,210,348]],
'day21_121304.jpg':[],
'day21_122225.jpg':[],
'day21_125548.jpg':[[404,154,436,194],[346,195,387,225],[178,296,216,335]],
}
manifest=json.loads((root/'frame_manifest.json').read_text())
for r in manifest:
 name=r['image'];split=r['split'];b=boxes[name]
 for kind in ('images','labels'):(root/'dataset'/kind/split).mkdir(parents=True,exist_ok=True)
 shutil.copyfile(root/'candidate_images'/name,root/'dataset/images'/split/name)
 lines=[]
 for x1,y1,x2,y2 in b:
  assert 0<=x1<x2<=640 and 0<=y1<y2<=360
  lines.append(f'0 {(x1+x2)/1280:.7f} {(y1+y2)/720:.7f} {(x2-x1)/640:.7f} {(y2-y1)/360:.7f}')
 (root/'dataset/labels'/split/pathlib.Path(name).with_suffix('.txt')).write_text('\n'.join(lines))
 r['boxes_xyxy']=b;r['annotation_method']='assistant_manual_visual';r['class']='gloved_hand';r['human_expert_review']=False
(root/'manual_annotations.json').write_text(json.dumps(manifest,indent=2))
dataset=(root/'dataset').resolve().as_posix()
(root/'dataset.yaml').write_text(f'path: {dataset}\ntrain: images/train\nval: images/val\nnames:\n  0: gloved_hand\n')
for page in range(6):
 sheet=Image.new('RGB',(1280,800),'white')
 for j,r in enumerate(manifest[page*4:(page+1)*4]):
  tile=Image.new('RGB',(640,400),'white');tile.paste(Image.open(root/'candidate_images'/r['image']),(0,30));d=ImageDraw.Draw(tile);d.text((5,5),r['image']+' | '+r['split'],fill='black')
  for box in r['boxes_xyxy']:
   x1,y1,x2,y2=box;d.rectangle((x1,y1+30,x2,y2+30),outline='#00ff77',width=2)
  sheet.paste(tile,((j%2)*640,(j//2)*400))
 sheet.save(root/f'reviewed_labels_{page+1}.jpg')
print({s:{'images':sum(r['split']==s for r in manifest),'hands':sum(len(r['boxes_xyxy']) for r in manifest if r['split']==s)} for s in ('train','val')})
