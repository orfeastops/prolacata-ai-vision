"""Assistant visual box annotations for individually inspected candidate images.

Coordinates refer to saved ROI pixels. These are object annotations, not load
state labels, transfer labels, or independently verified production counts.
"""
import json,shutil,hashlib,collections
from pathlib import Path
from PIL import Image,ImageDraw
from build_tank_detector_candidates_v1 import ROOT,OUT,save,digest

# Visible identifiable tank bodies, including truncated ones. Flat covers/stacked
# trays, pallet jacks and isolated unidentifiable fragments are not tank boxes.
BOXES={
0:[[0,278,98,445],[83,316,302,500],[0,447,51,500]],
1:[[0,278,99,443],[93,350,254,500],[262,340,500,500],[0,446,60,500]],
2:[[211,41,353,139],[267,114,410,239],[80,150,310,325]],
3:[[208,39,338,130],[267,98,410,235],[80,148,310,325]],
4:[[0,277,99,443]],
5:[[0,278,100,443],[207,145,330,276]],
6:[[267,114,410,239],[80,150,310,325]],
7:[[267,114,410,239],[80,150,310,325]],
8:[[0,278,99,443]],
9:[[0,278,99,443],[81,250,272,444]],
10:[[267,114,410,239],[80,150,310,325]],
11:[[267,114,410,239],[80,150,310,325]],
12:[],
13:[[0,405,181,500]],
14:[[61,0,134,87],[128,0,251,109],[248,0,322,61],[145,151,310,288],[277,122,410,228],[272,232,410,360]],
15:[[60,0,138,83],[128,0,250,105],[145,150,310,287],[277,121,410,227],[272,232,410,360]],
16:[],17:[],
18:[[0,0,94,109],[87,0,221,139],[216,0,308,100],[207,143,364,255],[281,115,410,237],[273,233,410,360]],
19:[[0,0,94,109],[87,0,221,139],[216,0,308,100],[207,143,364,255],[281,115,410,237],[273,233,410,360]],
20:[],21:[],
22:[[0,48,75,169],[54,28,134,154],[116,0,201,131],[186,0,252,108],[237,0,302,89],[251,115,410,236]],
23:[[0,48,75,169],[54,28,134,154],[116,0,201,131],[186,0,252,108],[237,0,302,89],[251,115,410,236]],
24:[[0,280,49,401]],25:[[0,280,49,401]],
26:[[0,84,78,190],[64,52,145,173],[126,30,203,148],[187,4,255,120],[235,0,296,98],[253,111,410,239],[245,53,321,127]],
27:[[0,84,78,190],[64,52,145,173],[126,30,203,148],[187,4,255,120],[235,0,296,98],[253,111,410,239],[208,47,313,143]],
28:[],29:[[21,184,199,350]],
30:[[0,84,78,190],[64,52,145,173],[126,30,203,148],[187,4,255,120],[235,0,296,98],[253,111,410,239],[34,112,169,247]],
31:[[0,84,78,190],[64,52,145,173],[126,30,203,148],[187,4,255,120],[235,0,296,98],[253,111,410,239],[202,50,308,133]],
32:[[0,250,91,384],[0,338,184,500]],33:[],
34:[[0,0,119,61],[103,0,207,80],[199,0,312,104],[269,108,410,242],[104,244,289,360],[257,309,410,360]],
35:[[48,4,228,154],[214,0,304,107],[281,113,410,242]],
36:[[177,4,284,130]],37:[],
38:[[0,0,105,62],[88,0,196,83],[176,0,306,104],[279,110,410,242]],
39:[[0,55,88,174],[75,37,187,152],[172,0,306,93],[250,141,410,263]],
40:[[178,29,254,129],[0,255,97,444]],
41:[[181,29,300,149],[0,326,87,448]],
42:[[0,0,105,105],[88,22,222,140],[205,0,307,105],[278,98,410,236],[151,287,345,360]],
43:[[0,48,76,177],[67,25,153,157],[137,0,223,132],[208,0,299,100],[232,141,410,269]],
44:[[0,249,93,378],[0,347,182,500]],45:[],
46:[[0,0,95,74],[74,0,162,92],[145,0,306,104],[269,126,410,258]],
47:[[0,56,77,180],[69,38,154,159],[137,13,222,132],[208,0,299,99],[279,111,410,249],[102,169,276,253]],
48:[[47,181,201,351],[0,300,180,500]],49:[[0,247,97,380],[0,340,180,500]],
50:[[0,0,91,66],[76,0,168,86],[150,0,307,100],[267,110,410,240]],
51:[[0,0,118,123],[107,10,220,140],[206,0,300,132]],
52:[[0,245,98,378],[0,337,186,500]],
53:[[174,7,285,117]],
54:[[180,0,281,105]],55:[],
56:[[0,137,82,259],[0,0,94,63],[79,0,171,85],[151,0,308,101],[213,151,255,247]],
57:[[0,0,103,70],[90,0,173,86],[156,0,299,117],[209,148,253,249]],
58:[[0,20,78,119],[65,32,169,153],[157,0,299,98],[236,44,360,133],[209,149,250,248]],
59:[[0,66,77,188],[65,48,150,166],[139,21,222,137],[207,0,301,113],[210,148,253,248]]
}

# Border-heavy stored rows have uncertain instance separation. Exclude these
# whole images rather than treating uncertain rectangles as clean supervision.
EXCLUDE={14,15,18,19,22,23,26,27,30,31,34,35,38,39,42,43,46,47,50,51,56,57,58,59}

# Batch reviewed against archive-native stills, 2026-10-30. Two neighboring
# bins must remain separate; covers, white tray stacks and bags are not tanks.
BOXES.update({
63:[[284,120,410,244],[321,85,410,174]],
64:[[284,120,410,244],[321,85,410,174]],
65:[[284,120,410,244],[321,85,410,174]],
66:[[232,143,410,273],[278,85,410,199]],
67:[[232,143,410,273],[278,85,410,199],[0,150,28,244]],
68:[[232,143,410,273],[278,85,410,199],[0,160,24,244]],
70:[[217,138,385,277],[0,118,63,249]],
71:[[217,138,385,277],[0,118,63,249]],
})

# Full-context audit: camera15 doorway crops also contain visible tanks in
# room11. These are detection instances, not new room15 entries.
for ident in [63,64,65]:
    BOXES[ident] += [[339,0,389,67],[384,13,410,85]]
BOXES[68] += [[340,0,409,73],[399,13,410,91]]
BOXES[70] += [[340,0,402,74]]
BOXES[71] += [[340,0,403,74],[397,6,410,94]]

# Native-source magnification confirmed TWO adjacent containers (beige front,
# gray rear), not one large object. Correct all repeated views consistently.
for ident in [2,3,6,7,10,11]:
    BOXES[ident]=[b for b in BOXES[ident] if b[0]!=80]+[[145,145,310,285],[79,174,265,325]]

# 15/10 native-sequence crops: loaded beige exit and two empty gray returns.
# Neighboring tanks through the doorway are detection instances as well.
BOXES.update({
    75:[[31,315,206,500]],
    76:[[91,197,278,370]],
    77:[[176,143,324,288]],
    78:[[258,106,321,220]],
    79:[],  # second gray body mostly hidden by the first tank and doorpost
    80:[[181,14,286,119],[0,214,159,373],[75,166,264,321]],
    81:[[180,14,286,119],[0,216,135,402],[0,406,186,500]],
    82:[],  # scale-side beige body mostly hidden by two people
})
EXCLUDE.update({79,82})

# 6/10 blue body at the shared door and 15/10 empty gray body in room15.
# Object-only labels; the later scale tank is not asserted to be the same load.
BOXES.update({
    83:[[9,292,195,485]],
    84:[[134,155,319,313]],
    85:[[233,119,323,257]],
    86:[[240,77,324,198]],
    87:[[11,12,221,183]],
})

# Native still context reveals border instances omitted from the early drafts.
BOXES[66] += [[397,0,410,92],[0,339,36,360]]
BOXES[67] += [[339,0,388,65],[385,0,410,94]]
# Keep occluded tray/row/stack crops out of clean object supervision. The
#17Oct sources stay validation; clearer ROIs from those sources are appended.
for ident in [60,61,62,69,72,73,74]:
    BOXES[ident]=[]
EXCLUDE.update({60,61,62,69,72,73,74})
BOXES.update({88:[[38,26,193,133]],89:[[6,44,375,320]]})

# Second13Oct cycle: filling, covered departure, scale dwell and empty
# replacement. Border tanks remain separate detection instances in093.
BOXES.update({
    90:[[13,1,304,270]],
    91:[[55,150,202,307]],
    92:[[17,19,108,146]],
    93:[[54,62,290,313],[0,0,111,136],[91,0,203,94],[0,120,47,277]],
})

#10Oct: separate empty tanks moving together, stationary cheese/scrap tanks,
# and fixed blue containers. Crop-edge instances remain separate objects.
BOXES.update({
    94:[[39,18,184,164],[6,103,190,299]],
    95:[[15,65,216,244],[131,23,281,193],[0,169,41,224],[0,211,82,260]],
    96:[[12,0,210,134],[183,0,322,111]],
    97:[[14,3,310,270]],
    98:[[11,25,273,280]],
    99:[[28,34,234,183],[210,43,350,171],[124,0,262,84],[0,0,42,36]],
})

#10Oct filled station, covered departure, occluded scale and empty replacement.
# Later room15 gray is object evidence only; its production identity is unresolved.
BOXES.update({
    100:[[6,8,294,270]],
    101:[[0,8,210,232]],
    102:[[2,11,177,173]],
    103:[[5,2,71,146]],
    104:[],  # background body boundaries remain uncertain after overlay review
    105:[[7,1,325,270]],
})

EXCLUDE.add(104)

#21Oct: filled station, covered departure, empty replacement and shared door.
#111 retains the stationary blue crop-edge tank as a separate instance.
BOXES.update({
    106:[[14,4,293,270]],
    107:[[0,8,198,244]],
    108:[[7,0,301,281]],
    109:[[0,38,174,190]],
    110:[],  # doorway/worker hide side and neighboring background boundaries
    111:[[0,12,166,128],[107,74,170,134]],
})
EXCLUDE.add(110)

#21Oct two later transfers; keep cropped stationary/background instances.
BOXES.update({
    112:[[12,2,320,270],[282,0,320,43]],
    113:[[9,8,250,252]],
    114:[[16,4,330,280]],
    115:[[28,0,330,260]],
    116:[],  # tank/cart boundaries remain ambiguous behind the fixed blue bin
    117:[[14,40,196,185],[80,10,246,154],[195,0,260,88]],
})
EXCLUDE.add(116)

#21Oct gray scale approach and beige filled/empty tracks. Border instance
# in122 is the separate stationary covered tank, not a second replacement.
BOXES.update({
    118:[[48,21,170,114]],
    119:[[53,11,326,280]],
    120:[[5,17,296,301]],
    121:[[28,0,208,148]],
    122:[[17,19,267,272],[0,233,39,290]],
})

#21Oct native empty-return and storage examples. Background row tanks remain
# separate instances; a covered top does not supply a cheese-load label.
BOXES.update({
    123:[],  # overlapping liner/row boundary not certain after overlay review
    124:[[18,12,220,246]],
    125:[[0,0,289,292]],
    126:[],  # occluded background instance extents remain ambiguous
})
EXCLUDE.update({123,126})

#17Oct validation only: empty setup, loaded departure, empty replacement and
#the separate scrap receptacle. These images never become training samples.
BOXES.update({
    127:[[25,20,280,300]],
    128:[[13,12,193,224]],
    129:[[8,13,260,250]],
    130:[[18,10,279,245]],
})

#6Oct: empty waiting tank, covered departure, empty replacement, scrap tank.
#132 is kept out because workers/conveyor hide the station-body extent.
BOXES.update({
    131:[[14,13,230,220]],
    132:[],
    133:[[10,14,283,295]],
    134:[[13,13,310,280]],
    135:[[10,16,279,224]],
})
EXCLUDE.add(132)

#23Oct native empty-tank examples, plus final disposition of six old drafts.
#Their low-resolution doorway crops have uncertain overlapping/background
#instance extents. Previous proposed boxes are preserved in review_history.
for ident in [2,3,6,7,10,11]:
    BOXES[ident]=[]
EXCLUDE.update({2,3,6,7,10,11})
BOXES.update({
    136:[[10,7,320,270]],
    137:[[10,8,287,270]],
    138:[[6,15,179,192]],
    139:[],  # small adjacent blue tank fragment has uncertain border extent
})
EXCLUDE.add(139)

# Batch16:6Oct fresh departures and an internal inverted/covered stack.
BOXES.update({
    140:[[0,8,187,216],[0,0,21,100]],
    141:[[38,30,222,193]],
    142:[[10,18,230,239],[0,0,98,67]],
    143:[],  # tiny background fragment at doorway cannot be bounded reliably
    144:[[96,0,240,79]],
    145:[[5,0,211,158],[22,112,214,244]],
})
EXCLUDE.add(143)

# Batch17: dense13Oct crossing views; three15 crops retain unresolved
# background/row fragments and are excluded as whole images, not negatives.
BOXES.update({
    146:[],
    147:[[36,20,218,223]],
    148:[[18,21,176,156],[152,19,320,164]],
    149:[],
    150:[[88,19,222,173]],
    151:[],
})
EXCLUDE.update({146,149,151})


# Batch18:15Oct fresh covered load, empty return/replacement and waiting tank.
#155 includes uncertain background row fragments; exclude the entire image.
BOXES.update({
    152:[[17,8,183,202]],
    153:[[22,14,213,187]],
    154:[[23,7,293,298]],
    155:[],
    156:[[0,0,147,143]],
    157:[[18,12,180,159]],
})
EXCLUDE.add(155)

# Batch19: fresh gray departure, empty replacement, filling and scrap tank.
#160/162 contain ambiguous cropped background instances; exclude whole ROIs.
BOXES.update({
    158:[[16,20,199,202]],
    159:[[12,18,210,248]],
    160:[],
    161:[[20,4,300,270]],
    162:[],
    163:[[35,8,280,235]],
})
EXCLUDE.update({160,162})

# Batch20: 13Oct loaded departure, empty replacement, scrap tank, scale
# view, storage transit and three separate waiting tanks. Filling crop166
# is excluded because people and the conveyor obscure its instance extent.
BOXES.update({
    164:[[24,24,203,220]],
    165:[[25,29,233,250]],
    166:[],
    167:[[12,17,270,244]],
    168:[[20,10,106,140]],
    169:[[33,0,190,85]],
    170:[[11,18,148,141],[34,101,190,244],[57,166,238,356]],
})
EXCLUDE.add(166)

# Batch21:15Oct covered departures, two separate empty waiting tanks,
# a genuine no-tank crop of stacked metal containers, and truncated gray
# storage transit. Only class=tank is labelled; cargo is not an empty tank.
BOXES.update({
    171:[[18,14,207,255]],
    172:[[22,10,214,242]],
    173:[[12,14,155,164],[87,90,262,248]],
    174:[],
    175:[[12,0,170,85]],
})

# Batch22:15Oct covered departures, empty waiting/return and scrap tank.
#179/180 are top-truncated single-instance crops;181 has conveyor occlusion.
BOXES.update({
    176:[[18,19,212,220]],
    177:[[17,11,179,164]],
    178:[[19,17,198,209]],
    179:[[10,0,202,131]],
    180:[[7,0,168,78]],
    181:[[15,14,278,245]],
})

# Batch23: two separate moving tanks, waiting beige, empty return and scrap.
#184 is too blurred and truncated for a reliable body boundary.
BOXES.update({
    182:[[21,90,244,312],[213,14,399,201]],
    183:[[7,18,177,173]],
    184:[],
    185:[[8,0,162,80]],
    186:[[14,9,288,237]],
})
EXCLUDE.add(184)

# Batch24: covered departure, empty replacement, two body-only15 views.
BOXES.update({
    187:[[15,11,205,188]],
    188:[[14,11,261,282]],
    189:[[10,0,178,100]],
    190:[[6,0,165,74]],
})

# Batch25: distinguish the two physical bodies in forklift stacks.
#191 lower feet and192 upper cover are truncated by the declared ROI.
BOXES.update({
    191:[[10,8,208,183],[7,143,201,274]],
    192:[[20,0,200,145],[28,112,194,230]],
    193:[[24,20,255,259]],
    194:[[12,15,285,238]],
    195:[[20,18,212,230]],
})

# Batch26: departure at two distances, scale through doorway, empty waiting
# tank and two separate bodies in a gray-over-beige moving stack.
BOXES.update({
    196:[[18,16,197,204]],
    197:[[12,6,168,157]],
    198:[[12,7,77,109]],
    199:[[12,11,243,248]],
    200:[[20,9,249,223],[14,198,224,254]],
})

# Batch27:21Oct loaded departure, empty replacement, doorway transit,
# empty blue-lined waiting tank and the separate fixed scrap tank.
BOXES.update({
    201:[[5,17,207,239]],
    202:[[10,27,309,309]],
    203:[[3,9,172,174]],
    204:[[8,14,205,188]],
    205:[[16,24,282,245]],
})

# Batch28:8Oct preparation and17Oct validation.208/209 are truncated.
BOXES.update({
    206:[[18,14,279,247]],
    207:[[6,15,287,285]],
    208:[[0,0,190,159]],
    209:[[18,16,205,160]],
    210:[[7,13,220,216]],
})

# Batch29: validation-only scale, aisle filling, covered transit and empty
# foreground inventory.213 has its top clipped;214 has its bottom clipped.
BOXES.update({
    211:[[9,9,98,116]],
    212:[[12,8,219,177]],
    213:[[15,0,215,104]],
    214:[[30,15,409,292]],
})

# Batch30:15Oct covered departure, empty replacement, scale body,
# covered storage transit (top truncated) and returned empty waiting tank.
BOXES.update({
    215:[[16,12,197,209]],
    216:[[15,18,287,296]],
    217:[[5,7,109,101]],
    218:[[14,0,197,125]],
    219:[[16,16,221,224]],
})

# Batch31: second15Oct gray departure, scale and empty doorway return.
#223 is a top/left-truncated body view;224 contains an uncertain adjacent
#beige fragment and is excluded rather than silently omitting that instance.
BOXES.update({
    220:[[11,8,190,229]],
    221:[[5,7,110,101]],
    222:[[14,6,209,193]],
    223:[[0,0,169,85]],
    224:[],
})
EXCLUDE.add(224)

# Batch32:6Oct morning filled departure, doorway transit, empty replacement,
# and separate fixed scrap tank. Boxes label physical tanks only.
BOXES.update({
    225:[[17,17,220,257]],
    226:[[10,14,181,176]],
    227:[[16,14,272,283]],
    228:[[13,14,287,241]],
})

# Batch33: adjacent empty returns and station filling/replacement on21Oct.
#231 is excluded: blurred adjacent boundaries plus a background stock fragment.
#232/233 are right-truncated, partially occluded physical tank views.
BOXES.update({
    229:[[17,18,180,158],[158,18,339,163]],
    230:[[23,61,219,235],[112,12,270,175]],
    231:[],
    232:[[14,7,288,210]],
    233:[[34,4,308,266]],
})
EXCLUDE.add(231)

# Batch34: validation-only17Oct departure, replacement and return.
#234 is top-truncated.235 includes an uncertain background-stock sliver.
BOXES.update({
    234:[[7,0,179,96]],
    235:[],
    236:[[11,9,205,191]],
    237:[[12,9,260,274]],
    238:[[13,9,208,181]],
})
EXCLUDE.add(235)

# Batch35:6Oct fresh departure, doorway passage, empty replacement,
# scale body and separate scrap tank. Only physical tank boxes are labeled.
BOXES.update({
    239:[[7,17,226,264]],
    240:[[18,20,207,182]],
    241:[[22,8,277,257]],
    242:[[11,7,84,112]],
    243:[[13,15,285,241]],
})

# Batch36: two distinct tanks per empty-return pair, both camera views.
#246/247 have crop-edge truncation;248/249 are station views clipped at right/bottom.
BOXES.update({
    244:[[14,57,211,237],[137,9,317,174]],
    245:[[16,59,203,231],[150,9,304,178]],
    246:[[0,40,222,227],[105,0,321,167]],
    247:[[0,62,171,242],[44,4,249,153]],
    248:[[12,4,300,272]],
    249:[[14,5,300,272]],
})

# Batch37:6Oct full station load, doorway body, empty replacement and
# independent scale body. Object boxes do not assert cross-camera identity.
BOXES.update({
    250:[[27,16,333,324]],
    251:[[17,12,198,187]],
    252:[[11,15,236,259]],
    253:[[20,14,89,121]],
})

# Batch38:6Oct covered departure, door crossing, distinct empty replacement,
# and independent scale body. No cross-camera identity is assigned by these boxes.
BOXES.update({
    254:[[11,9,222,246]],
    255:[[17,15,207,191]],
    256:[[12,13,268,281]],
    257:[[20,14,84,122]],
})

# Batch39:6Oct second fresh departure and its distinct empty replacement.
BOXES.update({
    258:[[13,10,195,211]],
    259:[[11,10,188,178]],
    260:[[14,13,283,286]],
})

# Batch40: validation-only17Oct filling, covered return and storage movement.
#263 is deliberately top-truncated; load state is not inferred from the cover.
BOXES.update({
    261:[[10,8,187,192]],
    262:[[8,7,163,139]],
    263:[[8,0,211,155]],
})

# Batch41: validation-only empty return and independent scale body.
BOXES.update({
    264:[[39,11,188,189]],
    265:[[11,12,113,110]],
})

# Batch42: native6Oct covered departure and distinct empty replacements.
BOXES.update({
    266:[[15,8,198,191]],
    267:[[18,18,239,252]],
    268:[[15,15,238,241]],
})

# Batch43:6Oct covered departure and empty replacement, native-context reviewed.
#271 retains tiny ambiguous background fragments; exclude the whole ROI.
BOXES.update({
    269:[[15,13,204,199]],
    270:[[16,13,267,265]],
    271:[],
})
EXCLUDE.add(271)

# Batch44:6Oct covered departure, empty local replacement and empty return.
BOXES.update({
    272:[[18,14,204,219]],
    273:[[9,8,255,256]],
    274:[[11,6,164,139]],
})

# Batch45:13Oct visually inspected native context. Front waiting tank occludes
# the rear body in279; scrap receptacle280 is bottom-truncated and occluded.
BOXES.update({
    275:[[12,6,186,204]],
    276:[[12,9,282,293]],
    277:[[12,11,162,169]],
    278:[[9,6,181,149]],
    279:[[8,10,160,134],[32,76,214,264]],
    280:[[7,7,260,218]],
})

# Batch46: native contexts and separate overlays reviewed.282 right edge truncated.
BOXES.update({281:[[9,8,201,242]],282:[[14,7,286,295]],283:[[8,8,179,151]]})

def main():
    m=json.loads((OUT/'candidate_manifest.json').read_text(encoding='utf8'))
    rows=[]
    for r in m['records']:
        ident=int(r['id'])
        if ident not in BOXES:
            r['boxes_xyxy']=None;r['annotation_status']='pending_box_annotation';continue
        r['boxes_xyxy']=BOXES[ident]
        r['annotation_status']='excluded_uncertain_instance_boundaries' if ident in EXCLUDE else 'assistant_box_draft_requires_overlay_review'
        if ident in EXCLUDE:continue
        r['label_provenance']='Assistant examined candidate grid; draft boxes awaiting separate overlay review, not user-certified.'
        for b in r['boxes_xyxy']:
            assert 0<=b[0]<b[2]<=r['width'] and 0<=b[1]<b[3]<=r['height'], (ident,b)
        rows.append(r)
    # Validation must cover both cameras. Ambiguous camera15 scenes need new
    # easier-to-annotate validation frames before this dataset may train.
    save(OUT/'visual_annotation_draft.json',dict(records=m['records'],included_ids=[r['id'] for r in rows],
         policy='Exclude entire uncertain images; no guessed boxes used for learning.',test_pixels_used=0))
    current_sheets=[]
    for start in range(0,len(rows),6):
        sheet=Image.new('RGB',(1680,1160),'#202020');d=ImageDraw.Draw(sheet)
        for j,r in enumerate(rows[start:start+6]):
            im=Image.open(ROOT/r['image']);a=ImageDraw.Draw(im)
            for k,b in enumerate(r['boxes_xyxy']):a.rectangle(b,outline='#00ff66',width=3);a.text((b[0]+3,b[1]+3),str(k),fill='yellow')
            x=j%3*560;y=j//3*580;sheet.paste(im,(x,y+35));d.text((x+3,y+3),f'{r["id"]} {r["split"]} cam{r["camera"]} boxes={len(r["boxes_xyxy"])}',fill='white')
        sheet_path=OUT/'sheets'/f'labels_{start//6:02d}.jpg'
        sheet.save(sheet_path,quality=95)
        current_sheets.append(str(sheet_path.relative_to(ROOT)))
    save(OUT/'overlay_sheet_manifest.json',dict(sheets=current_sheets,included_ids=[r['id'] for r in rows]))
    print(json.dumps({'included':len(rows),'excluded':len(EXCLUDE),'boxes':sum(len(r['boxes_xyxy']) for r in rows)}))
BOXES.update({284:[[38,36,224,256]],285:[[29,23,261,290]]})

BOXES.update({286:[[16,16,219,258]],287:[[27,20,281,273]]})
BOXES.update({288:[[10,0,211,137]]})
BOXES.update({289:[[15,0,220,168]],290:[[20,10,210,241]],291:[[17,0,223,166]]})
BOXES.update({292:[[10,13,153,138],[28,80,211,266]],293:[[10,13,165,190]]})
BOXES.update({294:[[13,50,134,146],[97,15,234,140],[29,92,172,257],[132,59,283,220]],295:[[13,50,134,146],[97,15,237,144],[29,92,172,257]],296:[[13,19,141,162]]})
BOXES.update({297:[[18,40,176,164],[157,55,295,177],[68,6,208,77]],298:[[14,0,111,73]]})
EXCLUDE.add(298)
BOXES[298]=[]
BOXES.update({299:[[17,16,190,160]],300:[[17,16,190,160]]})
EXCLUDE.add(299)
BOXES[299]=[]
BOXES.update({301:[[10,10,144,126],[48,37,193,175],[95,70,260,225]],302:[[10,10,144,126],[48,37,193,175]]})
BOXES.update({303:[[10,10,145,140]],304:[[12,60,170,180],[165,65,310,185],[65,14,195,105],[264,12,375,131]]})
if __name__=='__main__':main()
