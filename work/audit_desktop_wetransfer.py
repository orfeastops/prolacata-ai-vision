from pathlib import Path
import zipfile,re,json,collections,os
roots=[Path.home()/'Desktop',Path('C:/Users/Public/Desktop')]
roots += [p/'Desktop' for p in Path.home().glob('OneDrive*') if p.is_dir()]
reports=[];errors=[]
def summarize(names):
 groups=collections.Counter();other=[];nested=[]
 for n in names:
  if n.endswith('/'):continue
  m=re.search(r'Camera_(\d+)_DVR_(\d{8})(\d{6})',n,re.I)
  if m:groups[(m[2],m[1],Path(n).suffix.lower())]+=1
  else:other.append(n)
  if Path(n).suffix.lower() in ('.zip','.rar','.7z'):nested.append(n)
 return dict(groups=[dict(date=k[0],camera=k[1],extension=k[2],count=v) for k,v in sorted(groups.items())],unmatched=other,nested_archives=nested)
for root in roots:
 if not root.exists():continue
 for base,dirs,files in os.walk(root,onerror=lambda e:errors.append(str(e))):
  p=Path(base)
  if 'wetransfer' in p.name.lower():
   names=[]
   for b,ds,fs in os.walk(p,onerror=lambda e:errors.append(str(e))):
    names += [str((Path(b)/f).relative_to(p)) for f in fs]
   reports.append(dict(path=str(p),kind='directory',entries=len(names),**summarize(names)))
  for f in files:
   if 'wetransfer' not in f.lower():continue
   path=p/f
   if zipfile.is_zipfile(path):
    with zipfile.ZipFile(path) as z:
     names=z.namelist()
     reports.append(dict(path=str(path),kind='zip',entries=len(names),**summarize(names)))
   else:reports.append(dict(path=str(path),kind='other'))
out=Path('outputs/tray_dump_evidence/desktop_wetransfer_audit.json')
out.write_text(json.dumps(dict(roots=[str(r) for r in roots],reports=reports,errors=errors),ensure_ascii=False,indent=2),encoding='utf-8')
print(out)
for r in reports:
 print(json.dumps(r,ensure_ascii=True))
print('ERRORS',errors)
