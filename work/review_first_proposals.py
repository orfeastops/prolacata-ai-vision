import pathlib,json,collections
from PIL import Image,ImageDraw,ImageFont
ROOT=pathlib.Path('outputs/facility_dataset');OUT=ROOT/'annotation_audit'
sample=json.loads((OUT/'review_sample.json').read_text())
# Visual assistant review of the original 640x360 crops. Hidden hands are not invented.
# These are an audit subset, not a facility-level independent test or approved training set.
boxes={
 'A001':[[139,244,157,269],[226,146,253,181],[295,187,321,218]],
 'A002':[],
 'A025':[[179,295,211,324],[241,84,283,130],[333,195,370,232]],
 'A026':[],
 'A027':[],
 'A028':[[202,218,231,257],[83,47,112,80],[120,23,149,54],[307,219,345,265],[354,189,385,227]],
}
def iou(a,b):
 x=max(0,min(a[2],b[2])-max(a[0],b[0]));y=max(0,min(a[3],b[3])-max(a[1],b[1]))
 inter=x*y;return inter/((a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-inter+1e-9)
review=[];tot=collections.Counter();canvas=Image.new('RGB',(1280,3*390),'white');font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15)
for i,(id,truth) in enumerate(boxes.items()):
 r=next(x for x in sample if x['audit_id']==id);v=r['view']
 pred=[(b,s,l) for b,s,l in zip(v['boxes'],v['scores'],v['labels']) if 'gloved hand' in l]
 matched=set();tp=0
 for b,s,l in sorted(pred,key=lambda x:-x[1]):
  candidates=[(iou(b,t),j) for j,t in enumerate(truth) if j not in matched]
  if candidates and max(candidates)[0]>=.5:matched.add(max(candidates)[1]);tp+=1
 stats={'tp':tp,'fp':len(pred)-tp,'fn':len(truth)-tp};tot.update(stats)
 review.append({'audit_id':id,'image':v['image'],'frame':r['frame'],'class':'gloved_hand',
  'boxes_xyxy':truth,'reviewer':'assistant visual review','status':'audit_only; not expert verified',
  'scope':'visible gloved hands only; other object classes remain unreviewed','teacher_audit_iou_0_5':stats})
 im=Image.open(ROOT/v['image']).convert('RGB');di=ImageDraw.Draw(im)
 for j,b in enumerate(truth):di.rectangle(b,outline='#00ff60',width=3);di.text((b[0],max(0,b[1]-17)),f'H{j+1}',fill='#00ff60',font=font)
 x=(i%2)*640;y=(i//2)*390;canvas.paste(im,(x,y+30));ImageDraw.Draw(canvas).text((x+5,y+5),f'{id} reviewed visible hands: {len(truth)} (green)',fill='black',font=font)
canvas.save(OUT/'first_corrected_hands.jpg',quality=94)
(OUT/'first_reviewed_hands.json').write_text(json.dumps(review,indent=2))
report={'scope':'Six deliberately selected camera 11 audit crops; not a random accuracy estimate',
 'class':'gloved_hand','iou':.5,'frames':len(review),'visible_hand_boxes':sum(map(len,boxes.values())),
 **dict(tot),'precision':tot['tp']/max(1,tot['tp']+tot['fp']),'recall':tot['tp']/max(1,tot['tp']+tot['fn']),
 'finding':'Do not approve the bulk teacher proposals as ground truth. Empty production scenes can contain false hand predictions on blue liners and other objects.',
 'supervised_training_approved':False}
(OUT/'first_hand_audit.json').write_text(json.dumps(report,indent=2))
notes={'overlay_frames_visually_inspected':['A001','A002','A003','A004','A005','A006','A025','A026','A027','A028','A029','A030','A073','A074','A075','A076','A077','A078','A085','A086','A087','A088','A089','A090'],
 'original_crops_reviewed':list(boxes),'review_status':'partial assistant visual audit',
 'findings':[
  'Camera 11: many overlapping cheese-block proposals, including conveyor surfaces and partly visible objects; these cannot be counted as placements.',
  'Camera 11: false gloved-hand detections on blue liner or head covering, including scenes without workers.',
  'Camera 15: foreground stationary stackable containers are repeatedly labelled pallet truck; detections are not exit events.',
  'Camera 15: proposals do not classify full versus empty tank state.',
  'The stationary crumb tank needs its own role and state labels; its white contents must not be treated as whole feta blocks.',
  'Next annotation unit is a continuous event: hand, origin, destination, visible object, start/end, tank cycle, and uncertainty.'],
 'approved_for_supervised_training':False}
(OUT/'review_findings.json').write_text(json.dumps(notes,indent=2))
print(json.dumps(report,indent=2))
