"""Stage a user-supplied export as test-only media, never training input."""
import collections
import hashlib
import json
import pathlib
import shutil
import zipfile

root=pathlib.Path('outputs/facility_dataset/temporal_pipeline/unseen_test_20260926')
media=pathlib.Path('work/unseen_test_20260926/media')
root.mkdir(parents=True,exist_ok=True);media.mkdir(parents=True,exist_ok=True)
known={r['sha256'] for r in json.loads(pathlib.Path('outputs/facility_dataset/media_manifest.json').read_text())}
records=[];seen=set()
with zipfile.ZipFile('C:/Users/evant/Desktop/camera11 test.zip') as archive:
    entries=[i for i in archive.infolist() if not i.is_dir()]
    print('Archive entries',len(entries),collections.Counter(pathlib.Path(i.filename).suffix.lower() for i in entries),flush=True)
    for i,entry in enumerate(entries):
        name=pathlib.PurePosixPath(entry.filename).name
        if pathlib.Path(name).suffix.lower() not in {'.mp4','.jpg','.jpeg','.png','.avi','.dav'}:continue
        with archive.open(entry) as src:
            raw=src.read()
        sha=hashlib.sha256(raw).hexdigest();target=media/(sha[:16]+'_'+name)
        if not target.exists():target.write_bytes(raw)
        records.append({'basename':name,'archive_member':entry.filename,'sha256':sha,'bytes':len(raw),
          'media_path':'media/'+target.name,'local_path':str(target.resolve()),'already_in_original_dataset':sha in known,
          'duplicate_in_test_archive':sha in seen,'role':'test_only_do_not_train'})
        seen.add(sha)
        if i%200==0:print('Staged',i+1,flush=True)
summary={'role':'held-out user supplied export; no training or threshold tuning on these sources',
 'source_archive':'C:/Users/evant/Desktop/camera11 test.zip','files':len(records),'unique_media':len(seen),
 'extensions':dict(collections.Counter(pathlib.Path(r['basename']).suffix for r in records)),
 'matches_original_dataset':sum(r['already_in_original_dataset'] for r in records),
 'dates_from_names':dict(collections.Counter(r['basename'].split('_')[3][:8] for r in records)),
 'test_predictions_generated':False,'manual_ground_truth_complete':False,'block_counting_validated':False}
(root/'media_manifest.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
(root/'test_contract.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2),flush=True)
