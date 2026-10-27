"""Save visually reviewed object regions, not fabricated detector predictions.

Quantities refer to the pictured carried group, not increments to production.
Partial frame coverage must never become a full-frame YOLO negative label.
"""
from pathlib import Path
import json
from PIL import Image, ImageDraw

R=Path(__file__).resolve().parents[1]
D=R/'outputs/facility_dataset/temporal_pipeline/sequence_annotation_v2'
O=R/'outputs/facility_dataset/temporal_pipeline/placement_counter_v2/object_review'
specs=[
    ('N21_05',3.75,'first_questions/tray_pickup_continuation.mp4',11,
     [('left',2,[176,227,240,286]),('right',2,[266,176,374,255])]),
    ('N21_05',7.50,'first_questions/tray_pickup_continuation.mp4',11,
     [('left',1,[174,234,236,274]),('right',1,[198,122,248,165])]),
    ('N01_05',12.00,'N01_05/hands.mp4',0,
     [('right',3,[300,188,394,253])]),
    ('N01_02',.25,'N01_02/hands.mp4',0,
     [('left',3,[136,201,280,310])]),
]
rows=[];sheet=Image.new('RGB',(1280,800),'white');draw=ImageDraw.Draw(sheet)
for j,(cid,t,media,offset,objects) in enumerate(specs):
    a=json.loads((D/cid/'annotation.json').read_text(encoding='utf-8'))
    image_path=O/f'{cid}_{t:05.2f}.jpg';im=Image.open(image_path).convert('RGB')
    annotated=im.copy();pen=ImageDraw.Draw(annotated)
    for k,(position,quantity,box) in enumerate(objects):
        assert 0<=box[0]<box[2]<=im.width and 0<=box[1]<box[3]<=im.height
        ident=f'{cid}_{t:05.2f}_{position}'
        crop_path=O/(ident+'_object.jpg')
        im.crop(box).save(crop_path,quality=95)
        pen.rectangle(box,outline=(0,255,70),width=2)
        label=f'ANNOTATION: {quantity}'
        x,y=box[:2];pen.rectangle([x,max(0,y-17),min(639,x+112),y],fill='black')
        pen.text((x+2,max(0,y-16)),label,fill='white')
        rows.append(dict(annotation_id=ident,source_sha256=a['source_sha256'],
            clip_id=cid,review_media=media,review_time_s=t,
            source_encoded_time_s=round(a['source_encoded_start_s']+offset+t,4),
            image_path=str(image_path),object_crop=str(crop_path),bbox_xyxy=box,
            object_kind='carried_whole_feta_group',quantity=quantity,
            bbox_reviewer='assistant visual inspection',
            quantity_basis='User-confirmed sequence quantities and assistant frame/context association',
            quantity_independently_frame_confirmed_by_user=False,
            object_tracking_id=None,release_verified=False,
            production_count_increment=None,
            scope='Object group at one instant; repeated views are not additional blocks',
            full_frame_annotation_exhaustive=False,
            full_frame_detector_training_eligible=False,
            spatial_annotation_is_model_prediction=False))
    annotated.save(O/f'{cid}_{t:05.2f}_annotated.jpg',quality=95)
    x=j%2*640;y=j//2*400
    sheet.paste(annotated,(x,y+35))
    draw.text((x+5,y+8),f'{cid} {t:.2f}s | MANUAL OBJECT ANNOTATIONS',fill='black')
sheet.save(O/'carried_object_annotations.jpg',quality=95)
(O/'carried_object_annotations.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
report=dict(reviewed_candidate_frames=24,annotated_frames=len(specs),object_regions=len(rows),
    sources=len({v['source_sha256'] for v in rows}),quantity_classes=sorted({v['quantity'] for v in rows}),
    training_started=False,full_frame_detection_export_enabled=False,
    reason='Partial object annotations and too few independent sources; unlabelled objects are not background.',
    next_work='Expand exhaustive object annotations across sources and build source-separated detector validation.',
    labels_not_model_predictions=True)
(O/'object_annotation_progress.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
