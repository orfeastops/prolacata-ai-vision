"""Audit all supplied camera sources, deduplicate exact content, extract canonical media.
Never treats source JPGs or automatic detections as approved training labels.
"""
import pathlib,zipfile,hashlib,json,re,collections,time
DESKTOP=pathlib.Path(r'C:\Users\evant\Desktop')
OUT=pathlib.Path('outputs/facility_dataset');OUT.mkdir(parents=True,exist_ok=True)
CACHE=pathlib.Path('work/facility_media');CACHE.mkdir(parents=True,exist_ok=True)
pattern=re.compile(r'Camera_(\d+)_DVR_(\d{14})_(\d{14})')
archives=[DESKTOP/'cameradata.zip',*sorted(DESKTOP.glob('wetransfer*camera*.zip'))]
directory=DESKTOP/'camera11.1.10.2026'
archive_hashes={};archive_audit=[];media={};occurrences=0;started=time.time()

def sha_file(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
 return h.hexdigest()

def accept(data,name,source):
 global occurrences
 base=pathlib.PurePosixPath(name.replace('\\','/')).name
 ext=pathlib.Path(base).suffix.lower();m=pattern.search(base)
 if ext not in ('.jpg','.jpeg','.png','.mp4','.avi','.dav','.mov') or not m:return
 occurrences+=1
 digest=hashlib.sha256(data).hexdigest()
 occurrence=dict(source=source,member=name)
 if digest in media:
  media[digest]['occurrences'].append(occurrence);return
 camera,start,end=m.groups()
 dest=CACHE/f'{digest[:16]}_{base}'
 if not dest.exists():dest.write_bytes(data)
 media[digest]=dict(sha256=digest,camera=int(camera),date=f'{start[:4]}-{start[4:6]}-{start[6:8]}',filename_start=start,filename_end=end,
                   basename=base,extension=ext,bytes=len(data),local_path=str(dest.resolve()),occurrences=[occurrence],
                   labels_status='unlabelled',clock_verified=False)

for archive in archives:
 digest=sha_file(archive)
 audit=dict(path=str(archive),bytes=archive.stat().st_size,sha256=digest)
 if digest in archive_hashes:
  audit['exact_duplicate_of']=archive_hashes[digest]
  archive_audit.append(audit);print('EXACT DUPLICATE ARCHIVE',archive.name,flush=True);continue
 archive_hashes[digest]=str(archive);archive_audit.append(audit)
 with zipfile.ZipFile(archive) as z:
  entries=[e for e in z.infolist() if pattern.search(pathlib.PurePosixPath(e.filename).name) and pathlib.Path(e.filename).suffix.lower() in ('.jpg','.jpeg','.png','.mp4','.avi','.dav','.mov')]
  for n,e in enumerate(entries):
   accept(z.read(e),e.filename,str(archive))
   if n%200==0:print('AUDIT',archive.name,n,'/',len(entries),'unique',len(media),flush=True)
 if archive.name=='cameradata.zip':print('INITIAL ARCHIVE COMPLETED',flush=True)

if directory.exists():
 for n,p in enumerate(sorted(directory.rglob('*'))):
  if p.is_file() and p.suffix.lower() in ('.jpg','.jpeg','.png','.mp4','.avi','.dav','.mov'):
   accept(p.read_bytes(),str(p.relative_to(directory)),str(directory))
   if n%200==0:print('AUDIT directory',n,'unique',len(media),flush=True)

records=list(media.values())
(OUT/'media_manifest.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
(OUT/'archive_audit.json').write_text(json.dumps(archive_audit,indent=2),encoding='utf-8')
groups=collections.defaultdict(collections.Counter)
for r in records:groups[(r['date'],r['camera'])]['videos' if r['extension'] in ('.mp4','.avi','.dav','.mov') else 'images']+=1
summary=dict(unique_media=len(records),media_occurrences_in_canonical_archives_and_directory=occurrences,
             exact_media_duplicates=occurrences-len(records),archive_count=len(archives),exact_archive_duplicates=sum('exact_duplicate_of' in a for a in archive_audit),
             total_unique_bytes=sum(r['bytes'] for r in records),elapsed_seconds=round(time.time()-started),
             groups=[dict(date=d,camera=c,**counts) for (d,c),counts in sorted(groups.items())],
             note='Full content SHA256 deduplication. Filename dates are not clock-verified. No labels inferred.')
(OUT/'audit_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2),flush=True)
