"""Collect original camera videos into a desktop folder, without moving sources."""
import json,re,hashlib,shutil,time,zipfile,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DESKTOP=Path('C:/Users/evant/Desktop')
DEST=DESKTOP/'Facility_Camera_Videos'
REPORT=ROOT/'outputs/camera_video_collection'
VIDEO={'.mp4','.avi','.mov','.mkv','.dav','.h264','.h265','.264','.265','.wmv','.asf','.mpeg','.mpg','.ts'}
PATTERN=re.compile(r'(Camera_(\d+)_DVR_(\d{8})\d{6}_.*)',re.I)
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def main():
    REPORT.mkdir(parents=True,exist_ok=True)
    expected={}; candidates={}
    for name in ['outputs/facility_dataset/media_manifest.json',
                 'outputs/facility_dataset/temporal_pipeline/temporal_media_index.json',
                 'outputs/facility_dataset/temporal_pipeline/unseen_test_20260926/media_manifest.json']:
        for r in json.loads((ROOT/name).read_text(encoding='utf-8')):
            p=Path(r['local_path'])
            if p.suffix.lower() in VIDEO:
                expected[str(p).lower()]=r['sha256']
                candidates[str(p).lower()]=p
    scan_roots=[ROOT/'work']+[p for p in DESKTOP.iterdir() if p.is_dir() and
        (p.name.lower().startswith('camera') or p.name.lower().startswith('wetransfer_'))]
    for base in scan_roots:
        for p in base.rglob('*'):
            if p.is_file() and p.suffix.lower() in VIDEO and PATTERN.search(p.name):candidates[str(p).lower()]=p
    unique={};missing=[];checked=0
    for key,p in sorted(candidates.items()):
        if not p.exists():missing.append(str(p));continue
        m=PATTERN.search(p.name)
        if not m:continue
        h=digest(p)
        if key in expected:assert h==expected[key],f'Source differs from indexed hash: {p}'
        record=unique.setdefault(h,dict(sha256=h,basename=m[1],camera=int(m[2]),date=m[3],
                                      bytes=p.stat().st_size,source=str(p),occurrences=[]))
        record['occurrences'].append(str(p));checked+=1
        if checked%250==0:print('Hashed',checked,'candidate files; unique',len(unique),flush=True)
    # Confirm desktop archives do not contain extra camera videos missing from disk.
    namesizes={(r['basename'].lower(),r['bytes']) for r in unique.values()}
    archive_missing=[]
    for z in DESKTOP.glob('*.zip'):
        if 'camera' not in z.name.lower() and 'wetransfer' not in z.name.lower():continue
        with zipfile.ZipFile(z) as archive:
            for info in archive.infolist():
                name=Path(info.filename).name
                if Path(name).suffix.lower() not in VIDEO or not PATTERN.search(name):continue
                if (name.lower(),info.file_size) not in namesizes:archive_missing.append(dict(archive=str(z),member=info.filename,bytes=info.file_size))
    if missing or archive_missing:
        save(REPORT/'inventory_gaps.json',dict(missing_indexed_sources=missing,archive_only_videos=archive_missing))
    if missing:raise RuntimeError(f'Missing indexed sources: {len(missing)}')
    if archive_missing:
        staging=ROOT/'work/desktop_video_archive_sources';staging.mkdir(exist_ok=True)
        assert shutil.disk_usage(staging).free>sum(r['bytes'] for r in archive_missing)+500_000_000
        for item in archive_missing:
            basename=Path(item['member']).name
            prefix=hashlib.sha256(item['archive'].encode()).hexdigest()[:12]
            extracted=staging/(prefix+'_'+basename)
            # Only basename is used; archive paths cannot escape the staging folder.
            if not extracted.exists():
                with zipfile.ZipFile(item['archive']) as z, z.open(item['member']) as src, extracted.open('xb') as dst:
                    shutil.copyfileobj(src,dst)
            assert extracted.stat().st_size==item['bytes']
            h=digest(extracted);m=PATTERN.search(basename)
            record=unique.setdefault(h,dict(sha256=h,basename=m[1],camera=int(m[2]),date=m[3],
                bytes=item['bytes'],source=str(extracted),occurrences=[]))
            record['occurrences'].append(item['archive']+' :: '+item['member']);checked+=1
        print('Included archive-only video entries:',len(archive_missing),flush=True)
    records=sorted(unique.values(),key=lambda r:(r['date'],r['camera'],r['basename']))
    total=sum(r['bytes'] for r in records);free=shutil.disk_usage(DESKTOP).free
    save(REPORT/'inventory.json',dict(candidate_files=checked,unique_videos=len(records),total_bytes=total,free_bytes=free,records=records))
    print('Unique videos:',len(records),'Bytes:',total,'Free bytes:',free,flush=True)
    copy_records(records,checked)

def copy_records(records,checked):
    total=sum(r['bytes'] for r in records);free=shutil.disk_usage(DESKTOP).free
    if free<total+500_000_000:raise RuntimeError('Insufficient free disk space for independent copies')
    DEST.mkdir(exist_ok=True);used={};start=time.time()
    for i,r in enumerate(records):
        day=f"{r['date'][:4]}-{r['date'][4:6]}-{r['date'][6:]}"
        folder=DEST/day/f"Camera_{r['camera']}";folder.mkdir(parents=True,exist_ok=True)
        target=folder/r['basename']
        if str(target).lower() in used and used[str(target).lower()]!=r['sha256']:
            target=folder/(Path(r['basename']).stem+'_'+r['sha256'][:12]+Path(r['basename']).suffix)
        used[str(target).lower()]=r['sha256']
        if target.exists():
            assert digest(target)==r['sha256'],f'Existing destination differs; refusing overwrite: {target}'
        else:
            shutil.copy2(r['source'],target)
            assert target.stat().st_size==r['bytes'] and digest(target)==r['sha256'],f'Copy verification failed: {target}'
        r['destination']=str(target)
        r['verified_sha256']=True
        r['role_note']='September test-only footage; do not train' if r['date']=='20260926' else ('Reserved holdout for arrival v8; do not train/tune' if r['date']=='20261003' else 'Original source footage')
        if (i+1)%100==0:
            print('Copied and verified',i+1,'/',len(records),flush=True)
            save(REPORT/'progress.json',dict(copied=i+1,total=len(records),elapsed_s=time.time()-start))
    groups={}
    for r in records:
        key=f"{r['date']} Camera {r['camera']}";groups[key]=groups.get(key,0)+1
    report=dict(destination=str(DEST),videos=len(records),candidate_files=checked,total_bytes=total,
        duplicates_collapsed=checked-len(records),groups=groups,all_copies_sha256_verified=True,
        source_files_moved_or_deleted=False,records=records)
    save(DEST/'video_manifest.json',report);save(REPORT/'complete.json',report)
    (DEST/'README.txt').write_text(
        f'FACILITY CAMERA VIDEOS\n\n{len(records)} unique original camera videos, organized by date and camera.\n'
        f'Total bytes: {total}\nAll copies verified against source SHA-256 hashes.\n'
        'Original files were not moved or deleted. Identical duplicates are included once.\n'
        'Generated review clips, annotated previews, and photos are not original camera videos and are not included.\n'
        'September 26: test-only footage; do not use for training.\n'
        'October 3: reserved holdout for the arrival-counter v8 experiment.\n'
        'video_manifest.json records original locations, hashes and verification.\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='records'},indent=2),flush=True)
if __name__=='__main__':
    if '--copy-inventory' in sys.argv:
        inventory=json.loads((REPORT/'inventory.json').read_text(encoding='utf-8'))
        copy_records(inventory['records'],inventory['candidate_files'])
    else:main()
