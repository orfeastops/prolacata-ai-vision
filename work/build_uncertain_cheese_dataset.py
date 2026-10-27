"""Add carried cheese whose visible silhouette does not justify a block count."""
import json,shutil
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];B=R/'outputs/facility_dataset/temporal_pipeline/placement_counter_v2';O=B/'carried_cheese_uncertainty_v2';O.mkdir(exist_ok=True)
base=json.loads((B/'individual_blocks_expanded_v1/manifest.json').read_text())
rows=base['frames']
for row in rows:
 row['objects']=[dict(class_id=0,bbox_xyxy=b['bbox_xyxy'],quantity_hint=1,release_verified=False) for b in row['individual_blocks']]
# class 1 deliberately has no quantity target, including when sequence totals are known.
labels={
 'N21_05_014.50':[(1,[198,248,270,326]),(0,[289,185,322,239]),(0,[319,214,374,250])],
 'N21_05_014.75':[(1,[176,227,240,286]),(0,[265,177,320,219]),(0,[313,218,376,253])],
 'B021_009.00':[(1,[168,233,238,309]),(0,[258,169,310,213]),(0,[324,164,369,217])],
 'B004_019.50':[(1,[182,169,258,249])],
 'B004_020.00':[(1,[207,209,282,270])],
 'N01_02_000.50':[(1,[135,214,210,330])],
 'N01_05_013.00':[(1,[200,84,294,157])],
 'N21_02_005.00':[(1,[253,169,327,201])],
 'N21_02_008.00':[(1,[169,238,226,292]),(1,[331,185,401,221])],
}
candidates=json.loads((B/'individual_block_review/candidates.json').read_text())
added=[]
for r in candidates:
 stem=Path(r['image_path']).stem
 if stem not in labels:continue
 r.update(objects=[dict(class_id=c,bbox_xyxy=box,quantity_hint=1 if c==0 else None,release_verified=False) for c,box in labels[stem]],reviewer='assistant manual inspection of carried silhouettes with adjacent frame context',expert_frame_verification=False,detector_export_eligible=True)
 added.append(r)
assert len(added)==len(labels)
rows+=added
assert len({Path(r['image_path']).name for r in rows})==len(rows)
assert not set(base['held_out_sources'])&{r['source_sha256'] for r in rows}
for r in rows:
 p=Path(r['image_path']);dest=O/'dataset/images'/p.name;label=O/'dataset/labels'/(p.stem+'.txt')
 dest.parent.mkdir(parents=True,exist_ok=True);label.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
 lines=[]
 for obj in r['objects']:
  x1,y1,x2,y2=obj['bbox_xyxy'];assert 0<=x1<x2<=640 and 0<=y1<y2<=360
  lines.append(f'{obj["class_id"]} {(x1+x2)/1280} {(y1+y2)/720} {(x2-x1)/640} {(y2-y1)/360}')
 label.write_text('\n'.join(lines))
for page in range((len(added)+3)//4):
 sheet=Image.new('RGB',(1280,780),'white');draw=ImageDraw.Draw(sheet)
 for i,r in enumerate(added[page*4:page*4+4]):
  im=Image.open(r['image_path']);d=ImageDraw.Draw(im)
  for obj in r['objects']:
   box=obj['bbox_xyxy'];color='orange' if obj['class_id']==1 else 'lime';d.rectangle(box,outline=color,width=2)
   d.text((box[0],max(0,box[1]-12)),'QTY ?' if obj['class_id']==1 else 'SINGLE',fill=color)
  x=i%2*640;y=i//2*390;sheet.paste(im,(x,y+30));draw.text((x+5,y+7),Path(r['image_path']).stem+' MANUAL LABELS',fill='black')
 sheet.save(O/f'new_annotations_{page+1}.jpg')
manifest=dict(frames=rows,training_images=len(rows),new_frames=len(added),single_boxes=sum(o['class_id']==0 for r in rows for o in r['objects']),unresolved_regions=sum(o['class_id']==1 for r in rows for o in r['objects']),held_out_sources=base['held_out_sources'],september26_used=False,production_ready=False,policy='A predicted single silhouette is not a verified deposit. Class 1 must never increment block count.')
(O/'manifest.json').write_text(json.dumps(manifest,indent=2))
(O/'dataset.yaml').write_text(f'path: {(O/"dataset").as_posix()}\ntrain: images\nval: images\nnames:\n  0: single_block\n  1: cheese_qty_unknown\n')
print({k:v for k,v in manifest.items() if k!='frames'})
