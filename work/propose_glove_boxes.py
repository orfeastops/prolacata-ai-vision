import cv2,json,pathlib
from PIL import Image,ImageDraw
root=pathlib.Path('outputs/feta_training');images=root/'candidate_images'; records=[]
for p in sorted(images.glob('*.jpg')):
 im=cv2.imread(str(p));hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
 mask=cv2.inRange(hsv,(85,65,40),(120,255,255))
 mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3)))
 n,lab,stats,cent=cv2.connectedComponentsWithStats(mask)
 boxes=[]
 for x,y,w,h,area in stats[1:]:
  if 35<=area<=1600 and 5<=w<=95 and 5<=h<=70:
   boxes.append([max(0,int(x)-3),max(0,int(y)-3),min(640,int(x+w)+3),min(360,int(y+h)+3)])
 records.append(dict(image=p.name,boxes=boxes))
(root/'glove_candidates.json').write_text(json.dumps(records,indent=2))
for page in range(6):
 sheet=Image.new('RGB',(1280,800),'white')
 for j,r in enumerate(records[page*4:(page+1)*4]):
  tile=Image.new('RGB',(640,400),'white');tile.paste(Image.open(images/r['image']),(0,30));d=ImageDraw.Draw(tile);d.text((5,5),r['image'],fill='black')
  for i,(x1,y1,x2,y2) in enumerate(r['boxes']):
   d.rectangle((x1,y1+30,x2,y2+30),outline='#ff2222',width=2);d.text((x1,y1+30),str(i),fill='yellow',stroke_width=1,stroke_fill='black')
  sheet.paste(tile,((j%2)*640,(j//2)*400))
 sheet.save(root/f'glove_candidates_{page+1}.jpg')
print('Generated visual-review candidates, not accepted labels')
