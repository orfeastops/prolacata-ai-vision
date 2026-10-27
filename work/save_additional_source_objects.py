"""Visual object annotations from additional sources; no old quantities copied."""
import json
from pathlib import Path
from PIL import Image, ImageDraw
R=Path(__file__).resolve().parents[1]
O=R/'outputs/facility_dataset/temporal_pipeline/placement_counter_v2/object_review'
rows=json.loads((O/'additional_source_candidates.json').read_text())
boxes={
 'B004_19.625.jpg':[('left',[187,166,263,244],None)],
 'B006_10.000.jpg':[('right',[267,166,335,224],None)],
 'B006_11.750.jpg':[('left',[125,244,205,316],None)],
 'B020_10.750.jpg':[('right',[255,188,318,239],None)],
 'B020_14.250.jpg':[('right',[236,164,378,229],2)],
 'B021_08.750.jpg':[('left',[172,251,232,303],None),('right',[273,168,331,224],None)],
 'B021_10.750.jpg':[('left',[179,228,276,315],None)],
 'B022_20.500.jpg':[('right',[263,101,376,191],2)],
 'B023_14.250.jpg':[('left',[169,229,226,291],None)],
 'B023_15.375.jpg':[('right',[251,155,406,250],None)],
}
annotations=[]
for page in range((len(rows)+5)//6):
 sheet=Image.new('RGB',(1280,1170),'white');draw=ImageDraw.Draw(sheet)
 for j,row in enumerate(rows[page*6:page*6+6]):
  path=Path(row['image_path']);im=Image.open(path).convert('RGB');pen=ImageDraw.Draw(im)
  for position,box,quantity in boxes[path.name]:
   assert 0<=box[0]<box[2]<=640 and 0<=box[1]<box[3]<=360
   annotations.append(dict(annotation_id=path.stem+'_'+position,clip_id=row['clip_id'],
    source_sha256=row['source_sha256'],source_encoded_time_s=row['source_encoded_time_s'],
    review_media=row['clip_id']+'/hands.mp4',review_time_s=row['time_s'],image_path=str(path),
    bbox_xyxy=box,quantity=quantity,object_kind='carried_whole_feta_group',
    bbox_reviewer='assistant visual inspection',
    quantity_basis='Two distinct carried blocks visible' if quantity==2 else 'Unknown; historical paired-hand draft not accepted as quantity evidence',
    quantity_independently_frame_confirmed_by_user=False,
    object_tracking_id=None,release_verified=False,production_count_increment=None,
    full_frame_annotation_exhaustive=False,full_frame_detector_training_eligible=False,
    spatial_annotation_is_model_prediction=False))
   pen.rectangle(box,outline=(0,255,70) if quantity else (255,190,0),width=2)
   pen.text((box[0],max(0,box[1]-13)),f'QTY {quantity if quantity else "UNKNOWN"}',fill='red')
  x=j%2*640;y=j//2*390;sheet.paste(im,(x,y+30));draw.text((x+5,y+7),path.stem+' | MANUAL REVIEW',fill='black')
 sheet.save(O/f'additional_sources_annotated_{page+1}.jpg')
(O/'additional_source_annotations.json').write_text(json.dumps(annotations,indent=2))
base=json.loads((O/'object_dataset_manifest.json').read_text())
all_objects=[]
for name in ['carried_object_annotations.json','carried_object_annotations_expansion.json','additional_source_annotations.json']:
 all_objects+=json.loads((O/name).read_text())
assert len({x['annotation_id'] for x in all_objects})==len(all_objects)
base.update(object_regions=all_objects,original_sources=len({x['source_sha256'] for x in all_objects+base['negative_frames']}),
 quantity_known_regions=sum(x['quantity'] is not None for x in all_objects),quantity_unknown_regions=sum(x['quantity'] is None for x in all_objects))
(O/'object_dataset_manifest.json').write_text(json.dumps(base,indent=2))
summary=dict(object_regions=len(all_objects),positive_frames=len({x['image_path'] for x in all_objects}),negative_frames=len(base['negative_frames']),
 original_sources=base['original_sources'],quantity_known_regions=base['quantity_known_regions'],quantity_unknown_regions=base['quantity_unknown_regions'],
 detector_training_started=False,remaining_gate='Review full-frame coverage and ambiguous object regions before detector export')
(O/'object_annotation_progress.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
