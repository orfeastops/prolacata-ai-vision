"""Non-destructive GitHub handoff; media stay local, no credentials copied."""
import os,json,re,hashlib,zipfile,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT/'github_export/verified_github_checkout'
OUT=REPO/'handoff_20261102'; OUT.mkdir(exist_ok=True)
SKIP={'.git','__pycache__','feta_env','python_packages','video_decoder','.venv','node_modules'}
TEXT={'.py','.ps1','.js','.html','.md','.json','.yaml','.yml','.csv','.txt','.ipynb','.toml'}
BAD=re.compile(r'(?:github_pat_[A-Za-z0-9_]{30,}|gh[pousr]_[A-Za-z0-9]{30,}|hf_[A-Za-z0-9]{25,}|sk-(?:ant-|proj-)?[A-Za-z0-9_-]{30,}|AIza[A-Za-z0-9_-]{30,}|AQ\.[A-Za-z0-9_-]{35,})')
roots={'workspace_work':ROOT/'work','workspace_outputs':ROOT/'outputs','tank_day28':Path('D:/Codex/tank-day28'),'tank_storage':Path('D:/Codex/tank-storage')}
inventory=[]; included=[]; exclusions=[]; archives=[]; z=None; size=0
def close():
 global z
 if z:
  p=Path(z.filename);z.close();archives.append({'file':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()});z=None
for label,base in roots.items():
 for folder,dirs,files in os.walk(base):
  dirs[:]=sorted(d for d in dirs if d not in SKIP)
  for name in sorted(files):
   p=Path(folder)/name
   if p.is_symlink():continue
   st=p.stat(); rel=label+'/'+p.relative_to(base).as_posix()
   inventory.append({'path':str(p),'snapshot_path':rel,'bytes':st.st_size,'mtime_ns':st.st_mtime_ns})
   if p.suffix.lower() not in TEXT or st.st_size>2_000_000:continue
   if name.lower() in {'kaggle.json','credentials.json','user.conf'} or name.startswith('.env'):
    exclusions.append({'path':str(p),'reason':'credential filename'});continue
   try:text=p.read_text(encoding='utf-8-sig')
   except UnicodeError:continue
   if BAD.search(text) or '-----BEGIN PRIVATE KEY-----' in text:
    exclusions.append({'path':str(p),'reason':'credential-like content; not uploaded'});continue
   if p.suffix=='.ipynb':
    obj=json.loads(text)
    for cell in obj.get('cells',[]):
     if cell.get('cell_type')=='code':cell['outputs']=[];cell['execution_count']=None
    text=json.dumps(obj,ensure_ascii=False)
   text=re.sub(r'https?://[^\s"<>]+[?&]X-Goog-[^\s"<>]+','[signed-url-removed]',text)
   data=text.encode('utf-8')
   if z and size+len(data)>25_000_000:close()
   if not z:z=zipfile.ZipFile(OUT/f'metadata-{len(archives)+1:03d}.zip','w',zipfile.ZIP_DEFLATED);size=0
   z.writestr(rel,data);size+=len(data)
   included.append({'path':rel,'sha256':hashlib.sha256(data).hexdigest()})
   if label=='workspace_work' and p.parent==base and p.suffix in {'.py','.ps1','.js'}:
    dest=REPO/'work'/p.name;dest.write_bytes(data)
close()
external=set()
for name in ['camera_inventory.json','new_camera_inventory.json','tank_transfer_training_v1/archive_inventory.json']:
 p=ROOT/'outputs'/name
 if p.exists():
  def visit(x):
   if isinstance(x,dict):
    for k,v in x.items():
     if k in {'archive','archive_path'} and isinstance(v,str):external.add(v)
     visit(v)
   elif isinstance(x,list):
    for v in x:visit(v)
  visit(json.loads(p.read_text(encoding='utf-8-sig')))
report={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'roots':{k:str(v) for k,v in roots.items()},'files':inventory,'external_archives':[{'path':p,'exists_now':Path(p).exists(),'bytes':Path(p).stat().st_size if Path(p).exists() else None} for p in sorted(external)],'excluded_directories':sorted(SKIP),'credentials_excluded':exclusions,'note':'Inventory is local paths/sizes at snapshot, not proof every large file was hashed. Media/models and files >2MB remain local. ZIP members have hashes; runtime/notebook outputs excluded. Active inference may change files after snapshot.'}
(OUT/'LOCAL_FILE_INDEX.json').write_text(json.dumps(report,ensure_ascii=False,indent=1),encoding='utf-8')
(OUT/'SNAPSHOT_MANIFEST.json').write_text(json.dumps({'archives':archives,'members':included},indent=1),encoding='utf-8')
for arc in archives:
 with zipfile.ZipFile(OUT/arc['file']) as check:
  assert check.testzip() is None
print(json.dumps({'indexed_files':len(inventory),'included_metadata':len(included),'archives':len(archives),'excluded_sensitive_count':len(exclusions),'output':str(OUT)}))
