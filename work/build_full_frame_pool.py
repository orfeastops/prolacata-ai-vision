import pathlib,json,subprocess,re,concurrent.futures,time,shutil,hashlib,collections
from PIL import Image,ImageStat
ROOT=pathlib.Path('outputs/facility_dataset').resolve()
FFMPEG=pathlib.Path('work/video_decoder/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe').resolve()
media=json.loads((ROOT/'media_manifest.json').read_text())
frames=ROOT/'frames';crops=ROOT/'camera11_crops';jobs=ROOT/'extraction_records'
for p in (frames,crops,jobs):p.mkdir(exist_ok=True)
started=time.time()

def finish_image(path,source,origin,relative=None,keyframe=False):
 with Image.open(path) as im:
  im=im.convert('RGB');gray=im.resize((160,90)).convert('L');stat=ImageStat.Stat(gray)
  quality=dict(mean_luma=round(stat.mean[0],2),luma_std=round(stat.stddev[0],2),needs_quality_review=stat.stddev[0]<5)
  crop_path=None
  if source['camera']==11 and im.width>=1440 and im.height>=1080:
   crop_path=crops/path.name
   im.crop((800,720,1440,1080)).save(crop_path,quality=95)
  size=im.size
 return dict(image=str(path.relative_to(ROOT)).replace('\\','/'),camera11_crop=str(crop_path.relative_to(ROOT)).replace('\\','/') if crop_path else None,
             width=size[0],height=size[1],camera=source['camera'],date=source['date'],source_sha256=source['sha256'],source_basename=source['basename'],
             origin=origin,relative_pts_seconds=relative,source_keyframe=keyframe,quality=quality,
             labels_status='unlabelled',partition_group=f"{source['camera']}_{source['date']}_{source['filename_start'][8:10]}",split='unassigned',clock_verified=False)

def process(source):
 marker=jobs/(source['sha256']+'.json')
 if marker.exists():return json.loads(marker.read_text())
 records=[];errors=[];local=pathlib.Path(source['local_path']);ident=source['sha256'][:16]
 if source['extension'] in ('.jpg','.jpeg','.png'):
  dest=frames/f'{ident}_source.jpg'
  try:
   with Image.open(local) as im:im.convert('RGB').save(dest,quality=95)
   records.append(finish_image(dest,source,'provided_image'))
  except Exception as exc:errors.append(str(exc))
 else:
  folder=frames/ident;folder.mkdir(exist_ok=True)
  # Keyframes are sampled for object labels only. The complete video stays available
  # in media_manifest for temporal action learning; 30-second samples cannot count actions.
  command=[str(FFMPEG),'-hide_banner','-loglevel','info','-threads','2','-skip_frame','nokey','-i',str(local),
           '-vf',"setpts=PTS-STARTPTS,select='isnan(prev_selected_t)+gte(t-prev_selected_t,30)',showinfo",
           '-fps_mode','vfr','-q:v','3','-threads','1','-y',str(folder/'frame_%05d.jpg')]
  result=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace')
  times=[float(x) for x in re.findall(r'\bn:\s*\d+\s+pts:\s*-?\d+\s+pts_time:([-+\d.eE]+)',result.stderr)]
  images=sorted(folder.glob('frame_*.jpg'))
  if result.returncode or not images:
   errors.append('ffmpeg return='+str(result.returncode)+' '+result.stderr[-1500:])
  if len(times)!=len(images):errors.append(f'Timestamp/frame mismatch: {len(times)} vs {len(images)}')
  for i,path in enumerate(images):
   unique=path.with_name(f'{ident}_{path.name}')
   # Crop names are globally unique; full frames remain grouped by source hash.
   if path!=unique:path.rename(unique)
   try:records.append(finish_image(unique,source,'video_keyframe',times[i] if i<len(times) else None,True))
   except Exception as exc:errors.append(str(exc))
 result=dict(source_sha256=source['sha256'],frames=records,errors=errors)
 marker.write_text(json.dumps(result,indent=2))
 return result

all_frames=[];failures=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 futures={pool.submit(process,r):r for r in media}
 for i,future in enumerate(concurrent.futures.as_completed(futures),1):
  source=futures[future]
  try:
   result=future.result();all_frames.extend(result['frames'])
   if result['errors']:failures.append(dict(source=source['basename'],errors=result['errors']))
  except Exception as exc:failures.append(dict(source=source['basename'],errors=[str(exc)]))
  if i%40==0 or i==len(media):
   progress=dict(processed_media=i,total_media=len(media),frames=len(all_frames),failures=len(failures),elapsed_seconds=round(time.time()-started))
   (ROOT/'frame_pool_progress.json').write_text(json.dumps(progress,indent=2));print(json.dumps(progress),flush=True)
all_frames.sort(key=lambda r:(r['date'],r['camera'],r['source_basename'],r['relative_pts_seconds'] or 0))
(ROOT/'frame_manifest.json').write_text(json.dumps(all_frames,indent=2))
(ROOT/'extraction_failures.json').write_text(json.dumps(failures,indent=2))
groups=collections.defaultdict(collections.Counter)
for r in all_frames:
 groups[(r['date'],r['camera'])][r['origin']]+=1
summary=dict(unique_media_sources=len(media),frame_count=len(all_frames),camera11_crops=sum(r['camera11_crop'] is not None for r in all_frames),
             failures=len(failures),elapsed_seconds=round(time.time()-started),
             groups=[dict(date=d,camera=c,**v) for (d,c),v in sorted(groups.items())],
             labels_status='unlabelled',training_completed_on_full_pool=False,
             note='All unique supplied media processed. Sampled keyframes are for detector annotation, not for counting placements. Full videos retained for temporal annotation. Splits unassigned until event groups are checked.')
(ROOT/'frame_pool_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2),flush=True)
