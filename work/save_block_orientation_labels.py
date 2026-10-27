import json
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];O=R/'outputs/facility_dataset/temporal_pipeline/placement_counter_v2/block_orientation_expansion'
boxes={
 'N01_02_006.25':[[251,155,298,211]],
 'N01_02_006.50':[[246,188,291,239]],
 'B022_019.75':[[307,135,359,170],[404,133,448,179]],
 'B022_020.25':[[265,120,326,152],[360,137,397,184]],
 'B022_020.75':[[262,122,321,155],[303,158,354,202]],
 'B022_021.25':[[208,177,254,215],[241,221,293,256]],
 'B020_014.25':[[230,189,285,225],[318,168,375,212]],
 'N21_03_002.25':[[227,241,284,278],[242,282,302,323]],
}
rows=json.loads((O/'candidates.json').read_text());out=[]
for r in rows:
 stem=Path(r['image_path']).stem
 if stem not in boxes:continue
 r.update(individual_blocks=[dict(bbox_xyxy=b,category='carried_feta_block',release_verified=False,track_id=None) for b in boxes[stem]],detector_export_eligible=True,expert_frame_verification=False,reviewer='assistant visual review of individual frame and neighboring sequence',production_count_increment=None)
 out.append(r)
for page in range((len(out)+3)//4):
 sheet=Image.new('RGB',(1280,780),'white');d=ImageDraw.Draw(sheet)
 for i,r in enumerate(out[page*4:page*4+4]):
  im=Image.open(r['image_path']);pen=ImageDraw.Draw(im)
  for block in r['individual_blocks']:pen.rectangle(block['bbox_xyxy'],outline='lime',width=2)
  x=i%2*640;y=i//2*390;sheet.paste(im,(x,y+30));d.text((x+5,y+8),Path(r['image_path']).stem+' MANUAL LABELS',fill='black')
 sheet.save(O/f'reviewed_{page+1}.jpg')
(O/'annotations.json').write_text(json.dumps(out,indent=2))
print(f'{len(out)} fully labelled frames, {sum(len(r["individual_blocks"]) for r in out)} boxes')
