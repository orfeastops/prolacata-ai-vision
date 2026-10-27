"""Manual visible-instance annotations, never inferred from hand count."""
import json
from pathlib import Path
from PIL import Image, ImageDraw
R=Path(__file__).resolve().parents[1]
O=R/'outputs/facility_dataset/temporal_pipeline/placement_counter_v2/individual_block_review'
# A box encloses one visually separable carried block, not a worker's load.
# Partial frames cannot be exported as ordinary fully labelled detector images.
LABELS={
 'B020_014.00': ([[223,215,292,260],[364,190,425,226]],True),
 'B020_014.50': ([[225,165,268,204],[249,178,297,224]],True),
 'B022_019.00': ([[394,137,444,187]],False),
 'B022_019.50': ([[335,160,368,212],[414,133,460,181]],True),
 'B022_020.00': ([[276,122,335,155],[383,129,423,178]],True),
 'B022_020.50': ([[265,101,325,145],[326,143,370,188]],True),
 'B022_021.00': ([[230,139,283,177],[272,172,324,218]],True),
 'N21_05_014.50': ([[289,185,322,239],[319,214,374,250]],False),
 'N21_05_014.75': ([[265,177,320,219],[313,218,376,253]],False),
 'N21_05_015.00': ([[258,168,311,211],[318,181,361,226]],False),
 'N21_05_018.00': ([[177,247,237,279],[268,202,323,240]],False),
 'N21_05_018.50': ([[178,233,234,272],[198,122,248,165]],True),
 'B021_009.00': ([[258,169,310,213],[324,164,369,217]],False),
 'B021_010.50': ([[231,226,313,268],[265,265,333,305]],True),
 'N21_02_001.00': ([],True),
 'N21_02_002.00': ([],True),
 'N01_02_006.00': ([[249,163,295,220]],True),
 'N21_03_002.00': ([[243,253,310,291],[285,298,346,345]],True),
 'N01_02_010.00': ([],True),
 'N01_02_012.00': ([],True),
 'N01_02_014.00': ([],True),
 'N01_05_001.00': ([],True),
 'N01_05_003.00': ([],True),
 'N01_05_005.00': ([],True),
 'N21_03_004.00': ([],True),
 'N21_03_005.00': ([],True),
 'N21_03_007.00': ([],True),
 'N21_03_009.00': ([],True),
 'N21_03_011.00': ([],True),
}
confirmation=json.loads((O/'expert_confirmation.json').read_text(encoding='utf-8'))
CONFIRMED_EXAMPLES={Path(r['image']).stem:r['boxes'] for r in confirmation['approved_labels']}
rows=json.loads((O/'candidates.json').read_text(encoding='utf-8'))
out=[]
for row in rows:
 stem=Path(row['image_path']).stem
 boxes,complete=LABELS.get(stem,([],False))
 row.update(individual_blocks=[dict(bbox_xyxy=b,category='carried_feta_block',track_id=None,release_verified=False) for b in boxes],
  review_status='annotated' if boxes else ('reviewed_negative' if complete else 'excluded_ambiguous_contact_or_occlusion'),
  full_frame_coverage_complete=complete,detector_export_eligible=complete,
  reviewer='assistant visual inspection with adjacent frame context',
  expert_frame_verification=stem in CONFIRMED_EXAMPLES and boxes==CONFIRMED_EXAMPLES[stem],production_count_increment=None,
  expert_confirmation_scope='User approved examples linked in individual_annotations_1.jpg; no approval inferred for other pages or unseen frames' if stem in CONFIRMED_EXAMPLES and boxes==CONFIRMED_EXAMPLES[stem] else None,
  note='Repeated frames do not represent new blocks. Partial labels must not be treated as exhaustive negatives.')
 for x1,y1,x2,y2 in boxes:
  assert 0<=x1<x2<=640 and 0<=y1<y2<=360
 out.append(row)
(O/'annotations.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
selected=[r for r in out if r['individual_blocks']]
for page in range((len(selected)+5)//6):
 sheet=Image.new('RGB',(1280,1170),'white');draw=ImageDraw.Draw(sheet)
 for i,row in enumerate(selected[page*6:page*6+6]):
  im=Image.open(row['image_path']).convert('RGB');pen=ImageDraw.Draw(im)
  for j,b in enumerate(row['individual_blocks']):
   box=b['bbox_xyxy'];pen.rectangle(box,outline=(0,255,60),width=2)
   pen.text((box[0],max(0,box[1]-12)),f'block {j+1}',fill=(255,0,0))
  x=i%2*640;y=i//2*390;sheet.paste(im,(x,y+30))
  draw.text((x+5,y+8),Path(row['image_path']).stem+(' | COMPLETE' if row['full_frame_coverage_complete'] else ' | PARTIAL - NOT TRAINING'),fill='black')
 sheet.save(O/f'individual_annotations_{page+1}.jpg')
summary=dict(reviewed_candidate_frames=len(out),annotated_frames=len(selected),individual_block_boxes=sum(len(r['individual_blocks']) for r in out),
 complete_positive_frames=sum(r['full_frame_coverage_complete'] and bool(r['individual_blocks']) for r in out),negative_frames=sum(r['full_frame_coverage_complete'] and not r['individual_blocks'] for r in out),partial_frames=sum(bool(r['individual_blocks']) and not r['full_frame_coverage_complete'] for r in out),
 source_videos=len({r['source_sha256'] for r in out}),trained=False,september26_used=False,
 next_gate='Expand distinct source coverage and review occlusions; do not retrain using this small batch alone',
 limitation='Assistant spatial labels, not expert-verified counts; no completed-release labels yet.')
(O/'progress.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
