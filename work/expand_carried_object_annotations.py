"""Additional assistant-reviewed object regions and explicit hard negatives."""
import json
from pathlib import Path
from PIL import Image, ImageDraw

R=Path(__file__).resolve().parents[1]
D=R/'outputs/facility_dataset/temporal_pipeline/sequence_annotation_v2'
O=R/'outputs/facility_dataset/temporal_pipeline/placement_counter_v2/object_review'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,x):p.write_text(json.dumps(x,indent=2),encoding='utf-8')

# Quantities are deliberately unknown: the user confirmed clip totals, not
# the number visible at each of these instants. Pickup boundaries are flagged.
specs=[
 ('N21_04',1.,'first_questions/next_transfer.mp4',3,
  [('left',[180,239,244,289],'carried'),('right',[283,174,386,251],'pickup_or_carry_boundary')]),
 ('N21_04',4.,'first_questions/next_transfer.mp4',3,
  [('left',[181,252,243,300],'carried'),('right',[333,207,433,301],'pickup_or_carry_boundary')]),
 ('N21_02',5.,'N21_02/hands.mp4',0,
  [('right',[253,169,327,201],'carried')]),
 ('N21_02',8.,'N21_02/hands.mp4',0,
  [('left',[169,238,226,292],'carried'),('right',[331,185,401,221],'carried')]),
]
expanded=[];sheet=Image.new('RGB',(1280,800),'white');draw=ImageDraw.Draw(sheet)
for j,(cid,t,media,offset,objects) in enumerate(specs):
 a=read(D/cid/'annotation.json');image_path=O/f'{cid}_{t:05.2f}.jpg'
 im=Image.open(image_path).convert('RGB');pen=ImageDraw.Draw(im)
 for position,box,state in objects:
  ident=f'{cid}_{t:05.2f}_{position}'
  assert 0<=box[0]<box[2]<=640 and 0<=box[1]<box[3]<=360
  expanded.append(dict(annotation_id=ident,source_sha256=a['source_sha256'],clip_id=cid,
    review_media=media,review_time_s=t,source_encoded_time_s=round(a['source_encoded_start_s']+offset+t,4),
    image_path=str(image_path),bbox_xyxy=box,object_kind='whole_feta_group',quantity=None,
    handling_state=state,bbox_reviewer='assistant visual inspection',
    quantity_basis='Unknown at this instant; clip total must not be distributed across images',
    release_verified=False,production_count_increment=None,full_frame_annotation_exhaustive=False,
    full_frame_detector_training_eligible=False,spatial_annotation_is_model_prediction=False))
  pen.rectangle(box,outline=(255,190,0),width=2)
  pen.text((box[0],max(0,box[1]-13)),'QTY UNKNOWN',fill=(255,100,0))
 x=j%2*640;y=j//2*400;sheet.paste(im,(x,y+30));draw.text((x+5,y+7),f'{cid} {t}s | OBJECT REVIEW',fill='black')
sheet.save(O/'expanded_object_annotations.jpg')
save(O/'carried_object_annotations_expansion.json',expanded)

negatives=[]
for item in read(O/'negative_review_candidates.json'):
 a=read(D/item['clip_id']/'annotation.json')
 negatives.append(dict(**item,source_sha256=a['source_sha256'],
    source_encoded_time_s=round(a['source_encoded_start_s']+item['sequence_offset_s']+item['review_time_s'],4),
    annotation_scope='carried whole-feta groups only; stationary cheese remains visible',
    carried_group_boxes=[],reviewer='assistant image inspection plus user-confirmed sequence semantics',
    image_review_complete=True,quantity_model_target=None,
    note='Zero carried groups in this frame, not an empty image or a claim of no cheese anywhere.'))
save(O/'reviewed_hard_negatives.json',negatives)
combined=read(O/'carried_object_annotations.json')+expanded
assert len({r['annotation_id'] for r in combined})==len(combined)
sources={r['source_sha256'] for r in combined+negatives}
manifest=dict(object_regions=combined,negative_frames=negatives,
    original_sources=len(sources),quantity_known_regions=sum(r['quantity'] is not None for r in combined),
    quantity_unknown_regions=sum(r['quantity'] is None for r in combined),
    split_policy='Assign complete original source hashes together; no adjacent frames across splits',
    detector_export_enabled=False,
    export_block_reason='Positive frames have partial or ambiguous coverage. Do not treat unlabelled objects as background.',
    training_started=False)
save(O/'object_dataset_manifest.json',manifest)
print(json.dumps(dict(object_regions=len(combined),positive_frames=len({r['image_path'] for r in combined}),
    negative_frames=len(negatives),original_sources=len(sources),
    quantity_known_regions=manifest['quantity_known_regions'],quantity_unknown_regions=manifest['quantity_unknown_regions']),indent=2))
