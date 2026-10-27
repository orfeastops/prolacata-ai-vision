import pathlib,json,collections,subprocess,concurrent.futures
from PIL import Image,ImageDraw,ImageFont
ROOT=pathlib.Path('outputs/facility_dataset');OUT=ROOT/'temporal_pipeline/review_batch_01';OUT.mkdir(parents=True,exist_ok=True)
ff=str(pathlib.Path('work/video_decoder/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe').resolve())
index=json.loads((ROOT/'temporal_pipeline/temporal_media_index.json').read_text())
by_source=collections.defaultdict(list)
for p in (ROOT/'annotation_audit/raw/annotation_proposals').glob('*.json'):
 r=json.loads(p.read_text());f=r['frame']
 if f['camera']!=11 or f['origin']!='video_keyframe':continue
 v=next((v for v in r['proposals'] if v['view']=='filling_crop'),None)
 if not v:continue
 scores=[score for label,score in zip(v['labels'],v['scores']) if 'gloved hand' in label]
 # Ranking aid only: known false glove predictions are still unverified.
 rank=sum(s for s in scores if s>=.4)
 by_source[f['source_sha256']].append((rank,f))
grouped=collections.defaultdict(list)
for r in index:
 if r['camera']==11 and r.get('probed_duration_s',0)>=10 and r['sha256'] in by_source:
  if r['sha256'].startswith('68cafd7e99a93137'):continue
  grouped[r['date']].append(r)
chosen=[]
for date,rs in sorted(grouped.items()):
 rs=sorted(rs,key=lambda r:r['filename_start'])
 for band in range(8):
  group=rs[len(rs)*band//8:len(rs)*(band+1)//8]
  if not group:continue
  src=max(group,key=lambda s:max(x[0] for x in by_source[s['sha256']]))
  rank,f=max(by_source[src['sha256']],key=lambda x:x[0])
  duration=min(16,src['probed_duration_s']);start=max(0,min(f['relative_pts_seconds']-4,src['probed_duration_s']-duration))
  chosen.append({'clip_id':f'B{len(chosen)+1:03d}','source_sha256':src['sha256'],'source_basename':src['basename'],
    'date':date,'camera':11,'local_path':src['local_path'],'media_path':src['media_path'],
    'source_relative_start_s':round(start,3),'duration_s':round(duration,3),
    'source_video_group':src['sha256'],'filename_time_band':band,
    'selection_score':rank,'selection_status':'unverified teacher ranking; may include hard negatives',
    'clock_verified':False,'labels_status':'pending visual review','split':'unassigned',
    'targets':['tray identity and corner motion','visible raised versus cleared slots','each hand carrying a block',
       'release destination','crumb disposal','separator handling','unknown/occluded'],
    'tray_capacity_prior':10,'occupied_slot_count':None,'placed_block_count':None})
def process(r):
 dest=OUT/r['clip_id'];dest.mkdir(exist_ok=True);clip=dest/'filling_action.mp4'
 if not clip.exists():
  indexed=pathlib.Path('work/temporal_review_indexed')/(r['source_sha256'][:16]+'.mp4');indexed.parent.mkdir(exist_ok=True)
  subprocess.run([ff,'-hide_banner','-loglevel','error','-y','-i',r['local_path'],'-map','0:v:0','-c:v','copy',str(indexed)],check=True,capture_output=True)
  subprocess.run([ff,'-hide_banner','-loglevel','error','-y','-ss',str(r['source_relative_start_s']),'-i',str(indexed),
   '-t',str(r['duration_s']),'-vf','crop=640:360:800:720','-an','-c:v','libx264','-threads','2','-preset','fast','-crf','19',str(clip)],check=True,capture_output=True)
  subprocess.run([ff,'-hide_banner','-loglevel','error','-y','-i',str(clip),'-vf','fps=1','-frames:v','16',str(dest/'s_%02d.jpg')],check=True,capture_output=True)
 font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14);sheet=Image.new('RGB',(1280,4*270),'white');draw=ImageDraw.Draw(sheet)
 for j,p in enumerate(sorted(dest.glob('s_*.jpg'))[:12]):
  x=j%3*426;y=j//3*270;sheet.paste(Image.open(p).resize((426,240)),(x,y+30))
  draw.text((x+3,y+5),f'{r["clip_id"]} {r["date"]} clip ~{j+.5}s',font=font,fill='black')
 sheet.save(dest/'triage.jpg',quality=92)
 portable={k:v for k,v in r.items() if k!='local_path'};portable['clip_path']=str(clip.relative_to(ROOT)).replace('\\','/')
 (dest/'annotation.json').write_text(json.dumps(portable,indent=2));return portable
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 for r in pool.map(process,chosen):results.append(r);print(r['clip_id'],r['date'],'ready',flush=True)
(OUT/'batch_manifest.json').write_text(json.dumps(results,indent=2))
summary={'clips':len(results),'unique_sources':len({r['source_sha256'] for r in results}),
 'dates':dict(collections.Counter(r['date'] for r in results)),'duration_s':sum(r['duration_s'] for r in results),
 'status':'prepared for review, not labelled or trained','triage_note':'1 fps sheets select clips only. Use full native-rate clips to annotate/count hand actions.'}
(OUT/'batch_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2),flush=True)
