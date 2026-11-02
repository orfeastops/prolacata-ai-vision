"""Assistant visual patch proposals: clear tray position, not block detection.

Coordinates are manually supplied and are a material limitation of this probe.
Labels are not independent human ground truth. No full-tray count is implied.
"""
import json,hashlib
from collections import Counter
import cv2
from PIL import Image,ImageDraw,ImageFont
from prepare_slot_probe_v6 import OUT

# Centers in the original 640x360 crop. Patches include top/edge/base context.
# 1 = raised cheese on this tray position; 0 = exposed tray position.
# None = obstructed challenge, cannot provide an occupancy target.
LABELS={
 'O01_3': {1:[(349,242),(317,265),(283,289),(248,311),(388,280),(355,305),(321,329)]},
 'O01_14': {0:[(498,152),(463,176),(429,201),(396,226),(539,194),(505,219),(470,245),(438,267)]},
 'O01_20.8': {1:[(350,248),(317,271),(282,294),(248,317),(389,287),(355,311)]},
 'O01_30': {0:[(350,251),(317,274),(283,297),(249,320),(389,291),(355,315)]},
 'O01_39': {1:[(365,259),(330,282),(295,306),(262,330),(404,297),(370,321)]},
 'O01_52': {0:[(465,177),(430,198),(397,220),(366,243),(497,214),(463,237),(431,259),(399,281)]},
 'O01_57.5': {1:[(350,249),(316,273),(282,295),(247,317),(388,288),(355,312)]},
 'O01_76': {0:[(357,242),(324,264),(290,287),(253,310),(392,280),(359,303),(326,326)]},
 'O01_150': {1:[(359,242),(299,273),(267,296),(234,321),(393,282),(362,307),(333,331)],0:[(329,263)]},
 'O01_157': {1:[(359,244),(329,265),(299,286),(267,307),(234,330),(364,311)],0:[(394,284)]},
 'O01_159': {1:[(299,286),(364,311)],0:[(360,244),(330,266),(394,284)],None:[(267,307),(234,330)]},
 'O01_162': {0:[(360,244),(330,266),(299,287),(267,308),(234,330),(364,310),(394,284)],1:[(334,330)]},
 'O01_164': {0:[(360,244),(330,266),(299,287),(267,308),(234,330),(364,310),(394,284)],1:[(334,330)]},
 'O01_170': {0:[(450,194),(417,216),(383,240),(465,250),(431,272),(396,294)],None:[(330,255)]},
 'O21_5': {1:[(375,260),(341,282),(307,305),(271,328),(411,303),(377,327)]},
 'O21_16': {0:[(571,129),(608,107),(604,170),(568,192)]},
 'O21_37': {1:[(354,236),(319,257),(285,280),(251,304),(391,275),(358,297),(325,321)]},
 'O21_48': {0:[(574,113),(605,92),(609,158),(575,183)]},
 'O21_147': {1:[(350,239),(318,263),(284,286),(250,310)],0:[(352,309),(388,284)]},
 'O21_149.5': {0:[(350,242),(316,265),(249,313),(352,307),(388,283)],1:[(285,288),(321,329)]},
 'O21_151.5': {0:[(316,265),(285,288),(249,313),(352,307),(388,283),(321,329)],None:[(350,242)]},
 'O21_154': {0:[(426,191),(392,216),(358,242),(324,268),(461,231),(428,256),(392,282),(358,308)]}
}

def main():
    frames={r['id']:r for r in json.loads((OUT/'selected_frames.json').read_text())}
    dest=OUT/'patches';dest.mkdir(exist_ok=True)
    rows=[];font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15)
    for ident,classes in LABELS.items():
        r=frames[ident];im=cv2.imread(r['image']);number=0
        for cls,points in classes.items():
            for x,y in points:
                bbox=[x-24,y-28,x+24,y+28]
                assert bbox[0]>=0 and bbox[1]>=0 and bbox[2]<=640 and bbox[3]<=360,(ident,bbox)
                name=f'{ident}_{number:02d}';number+=1
                patch=im[bbox[1]:bbox[3],bbox[0]:bbox[2]]
                cv2.imwrite(str(dest/f'{name}.png'),patch)
                rows.append(dict(id=name,frame_id=ident,source_id=r['source_id'],source_sha256=r['source_sha256'],
                    source_frame_index=r['source_frame_index'],source_pts_s=r['source_pts_s'],
                    image=r['image'],bbox=bbox,patch=str(dest/f'{name}.png'),label=cls,
                    split='train' if r['source_id']=='O01' else 'development_test',
                    label_author='assistant_visual_proposal',human_verified=False,
                    localization='manual center, fixed 48x56 crop; no automatic localization'))
    for split in ['train','development_test']:
        rs=[r for r in rows if r['split']==split]
        for start in range(0,len(rs),32):
            page=Image.new('RGB',(1024,((min(32,len(rs)-start)+7)//8)*165),'#101824');draw=ImageDraw.Draw(page)
            for j,r in enumerate(rs[start:start+32]):
                x=j%8*128;y=j//8*165
                patch=Image.open(r['patch']).resize((96,112),Image.Resampling.NEAREST)
                page.paste(patch,(x+16,y+43))
                draw.text((x+3,y+2),r['id'],font=font,fill='white')
                draw.text((x+3,y+21),{0:'EMPTY',1:'CHEESE',None:'OBSTRUCTED'}[r['label']],font=font,fill={0:'cyan',1:'lime',None:'orange'}[r['label']])
            page.save(OUT/f'labels_{split}_{start//32:02d}.jpg',quality=95)
    manifest=dict(rows=rows,source_disjoint=True,training_source='O01',test_source='O21',
        independent_accuracy=False,september_used=False,full_tray_labels=False,
        note='Small manually localized slot-appearance probe; neither full detector training nor tank counting. Multiple patches share a frame/tray.')
    # Hash actual annotation source, not its path.
    from pathlib import Path
    manifest['annotation_code_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps({s:dict(Counter(str(r['label']) for r in rows if r['split']==s)) for s in ['train','development_test']}))
if __name__=='__main__':main()
