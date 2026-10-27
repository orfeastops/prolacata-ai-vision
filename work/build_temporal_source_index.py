import pathlib,json,subprocess,re,concurrent.futures,collections,datetime,time
ROOT=pathlib.Path('outputs/facility_dataset');OUT=ROOT/'temporal_pipeline';OUT.mkdir(exist_ok=True)
CACHE=pathlib.Path('work/temporal_probe');CACHE.mkdir(exist_ok=True)
ff=str(pathlib.Path('work/video_decoder/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe').resolve())
sources=[r for r in json.loads((ROOT/'media_manifest.json').read_text()) if r['extension']=='.mp4']
def probe(r):
 p=CACHE/(r['sha256']+'.json')
 if p.exists():return json.loads(p.read_text())
 try:
  s=subprocess.run([ff,'-hide_banner','-i',r['local_path']],capture_output=True,text=True,errors='replace',timeout=20).stderr
  m=re.search(r'Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)',s)
  duration=(int(m[1])*3600+int(m[2])*60+float(m[3])) if m else None
  start=datetime.datetime.strptime(r['filename_start'],'%Y%m%d%H%M%S');end=datetime.datetime.strptime(r['filename_end'],'%Y%m%d%H%M%S')
  nominal=(end-start).total_seconds()
  v={'sha256':r['sha256'],'camera':r['camera'],'date':r['date'],'basename':r['basename'],
     'media_path':'media/'+pathlib.Path(r['local_path']).name,'local_path':r['local_path'],
     'filename_start':r['filename_start'],'filename_end':r['filename_end'],
     'probed_duration_s':duration,'filename_interval_s':nominal,'clock_verified':False,
     'duration_review_required':duration is None or abs(duration-nominal)>max(5,.1*max(nominal,1)),
     'label_status':'unlabelled','split':'unassigned; reserve complete event groups'}
 except Exception as e:v={'sha256':r['sha256'],'camera':r['camera'],'date':r['date'],'error':str(e),'probed_duration_s':None}
 p.write_text(json.dumps(v,indent=2));return v
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 for i,r in enumerate(pool.map(probe,sources),1):
  results.append(r)
  if i%100==0:print('Probed',i,'/',len(sources),flush=True)
results.sort(key=lambda r:(r['camera'],r['date'],r.get('filename_start','')))
(OUT/'temporal_media_index.json').write_text(json.dumps(results,indent=2))
windows=[];groups=collections.defaultdict(lambda:{'videos':0,'duration_s':0,'windows':0})
for r in results:
 g=groups[(r['camera'],r['date'])];g['videos']+=1;d=r.get('probed_duration_s')
 if d is None or d<=0:continue
 g['duration_s']+=d
 starts=list(range(0,max(1,int(d)-15),8)) if d>=16 else [0]
 # Add last window without crossing file boundaries. These are annotation candidates, not labels.
 if d>=16 and (not starts or d-16-starts[-1]>1):starts.append(round(d-16,3))
 for start in starts:
  windows.append({'window_id':r['sha256'][:16]+f'_{start:010.3f}','source_sha256':r['sha256'],
    'camera':r['camera'],'date':r['date'],'media_path':r['media_path'],'start_s':start,
    'end_s':round(min(d,start+16),3),'labels_status':'unlabelled',
    'source_duration_review_required':r['duration_review_required'],
    'event_group':r['sha256'],'split':'unassigned','clock_verified':False})
  g['windows']+=1
(OUT/'temporal_windows.jsonl').write_text('\n'.join(json.dumps(w,separators=(',',':')) for w in windows)+'\n')
summary={'unique_video_sources':len(results),'probed_sources':sum(r.get('probed_duration_s') is not None for r in results),
 'review_flagged_sources':sum(r.get('duration_review_required',True) for r in results),
 'total_media_duration_hours':round(sum(r.get('probed_duration_s') or 0 for r in results)/3600,3),
 'duration_basis':'encoded media timeline from FFmpeg, not wall-clock elapsed recording time',
 'candidate_windows':len(windows),'window_s':16,'stride_s':8,
 'groups':[{'camera':c,'date':date,**g} for (c,date),g in sorted(groups.items())],
 'training_completed':False,
 'notes':['Duration is probed from supplied files, not a guarantee of continuous coverage of a day.',
          'Overlapping windows share source/event groups; never split them randomly across training and test.',
          'Each video stays intact and available. Windows index every source for temporal review/training.',
          'No labels are inferred from the standard tank count of 228 or tray capacity 10.',
          'DVR encoded playback durations can differ from filename clock intervals; use verified overlay clock mapping for event times.']}
(OUT/'temporal_index_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2),flush=True)
