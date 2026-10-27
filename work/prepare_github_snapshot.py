"""Package project code, annotations/results and all local checkpoints for GitHub.

Raw camera media, environments, browser captures and credentials are excluded.
The live workspace is not modified. Artifact archives retain original paths.
"""
import argparse,hashlib,importlib.metadata,json,os,re,shutil,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'github_export/prolacata-ai-vision'
TEXT={'.json','.jsonl','.yaml','.yml','.txt','.csv','.ipynb','.py','.html','.md'}
TOKEN=re.compile(r'(?:github_pat_[A-Za-z0-9_]{30,}|gh[pousr]_[A-Za-z0-9]{30,}|hf_[A-Za-z0-9]{25,}|sk-(?:proj-)?[A-Za-z0-9_-]{30,})')

def sha(data):return hashlib.sha256(data).hexdigest()

def sanitize(text):
    for prefix in sorted({str(ROOT),str(ROOT).replace('\\','/'),str(ROOT).replace('\\','\\\\')},key=len,reverse=True):
        text=text.replace(prefix,'.')
    text=re.sub(r'https?://[^\s"<>]+[?&]X-Goog-[^\s"<>]+','[signed-download-url-removed]',text)
    if TOKEN.search(text):raise RuntimeError('Credential-like token detected; inspect and exclude this file before upload')
    if re.search(r'(?m)^-----BEGIN (?:RSA )?PRIVATE KEY-----\s*\n[A-Za-z0-9+/=\r\n]{20,}',text):
        raise RuntimeError('Private key detected')
    return text

RESTORE=r'''"""Restore packaged artifacts into this checkout; no network access."""
import argparse,hashlib,json,zipfile
from pathlib import Path

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--verify-only',action='store_true')
    parser.add_argument('--overwrite',action='store_true')
    args=parser.parse_args();root=Path(__file__).resolve().parent
    manifest=json.loads((root/'snapshot_manifest.json').read_text(encoding='utf-8'))
    count=0
    for arc in manifest['archives']:
        p=root/arc['file']
        if hashlib.sha256(p.read_bytes()).hexdigest()!=arc['sha256']:raise RuntimeError('Archive checksum mismatch: '+p.name)
        with zipfile.ZipFile(p) as z:
            for info in z.infolist():
                target=(root/info.filename).resolve()
                if not target.is_relative_to(root.resolve()):raise RuntimeError('Unsafe archive path')
                data=z.read(info.filename)
                if hashlib.sha256(data).hexdigest()!=arc['members'][info.filename]:raise RuntimeError('Member checksum mismatch')
                if not args.verify_only:
                    if target.exists() and target.read_bytes()!=data and not args.overwrite:
                        raise RuntimeError('Existing file differs; keep your edits or explicitly use --overwrite: '+str(target))
                    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
                count+=1
    print(('Verified ' if args.verify_only else 'Restored ')+str(count)+' artifact files')

if __name__=='__main__':main()
'''

README=r'''# Prolacata AI Vision

Πειραματικό έργο καταμέτρησης μπλοκ φέτας και μεταφοράς δεξαμενών από την κάμερα 11 στην κάμερα 15.

**Κατάσταση: δεν είναι έτοιμο για χρήση στην παραγωγή.** Οι αποτυχίες και οι περιορισμοί των δοκιμών διατηρούνται μαζί με τον κώδικα. Τα κουτιά ανίχνευσης και οι ταξινομήσεις κινήσεων δεν αποτελούν επιβεβαιωμένη καταμέτρηση.

## Τι περιέχει

- `work/`: κώδικας προετοιμασίας δεδομένων, επισημάνσεων, εκπαίδευσης, αξιολόγησης και έλεγχοι.
- `snapshot-data.zip`: οι επισημάνσεις, τα ευρετήρια, τα notebooks, τα αποτελέσματα και οι διαμορφώσεις, με την αρχική δομή φακέλων `outputs/`.
- `snapshot-models-*.zip`: όλα τα τοπικά checkpoints και η σταθερή προβολή χαρακτηριστικών, επίσης με τις αρχικές διαδρομές.
- `snapshot_manifest.json`: SHA-256 των αρχείων και αναλυτικός κατάλογος περιεχομένων.
- `restore_snapshot.py`: ελέγχει και αποκαθιστά τα αρχεία των πακέτων.

Τα archives χωρίζονται σε μικρά αρχεία για μεταφορά μέσω GitHub. Ο αρχικός κώδικας παραμένει προσβάσιμος στο `work/`. Τα δεδομένα μοντέλων περιλαμβάνουν αποτυχημένες και παλαιότερες εκδόσεις· δεν χαρακτηρίζονται όλα κατάλληλα για χρήση.

## Αποκατάσταση και έλεγχος

Από τον κεντρικό φάκελο του αποθετηρίου:

```powershell
python restore_snapshot.py --verify-only
python restore_snapshot.py
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-core.txt
.\.venv\Scripts\python.exe work/test_block_transfer_counter.py
.\.venv\Scripts\python.exe work/test_native_temporal_counter_v3.py
```

Το `runtime_versions.json` καταγράφει τις εγκατεστημένες εκδόσεις της τοπικής δοκιμής. GPU/CUDA και οι παλιές εκτελέσεις Kaggle απαιτούν την αντίστοιχη ρύθμιση περιβάλλοντος. Ορισμένα παλιότερα βοηθητικά scripts έχουν διαδρομές των αρχικών εισαγωγών ή εξάρτηση από FFmpeg και χρειάζονται ρύθμιση σε άλλο υπολογιστή. Η μεταφορά του snapshot δεν αποτελεί επιβεβαίωση ότι κάθε ιστορικό script εκτελείται ανεξάρτητα.

## Δεδομένα καμερών

Τα αρχικά βίντεο, οι φωτογραφίες εγκατάστασης, οι προεπισκοπήσεις με εργαζομένους, τα προσωρινά αρχεία εικόνων και το Python environment παραμένουν εκτός αυτού του αποθετηρίου. Χρειάζονται ξεχωριστά για νέα εκπαίδευση. Δεν περιέχονται κωδικοί ή tokens.

Τα ευρετήρια συνδέουν τα αρχικά αρχεία με SHA-256. Τα διαθέσιμα τοπικά αρχεία αναφέρονται συνήθως στο `work/facility_media/`. Όπου έχει αφαιρεθεί το αρχικό απόλυτο workspace prefix, οι διαδρομές ερμηνεύονται από τη ρίζα του έργου.

## Τελευταία ολοκληρωμένη δοκιμή — 27/10/2026

`outputs/facility_dataset/temporal_pipeline/placement_counter_v3/native_temporal_diagnostic/results.json`

- 12 σύντομα αποσπάσματα από 10 αρχικά βίντεο, με 53 επιβεβαιωμένα μπλοκ.
- Κάθε αρχικό βίντεο αποκλείστηκε ολόκληρο από την εκπαίδευση της δικής του πρόβλεψης ελέγχου.
- Χρησιμοποιήθηκαν όλα τα αρχικά καρέ: 2.687 παρουσίες καρέ στα αποσπάσματα, 2.643 διαφορετικά καρέ λόγω επικάλυψης. Περίπου 15 fps με πραγματικές χρονοσφραγίδες.
- Μέσο απόλυτο σφάλμα: **2,364 μπλοκ ανά απόσπασμα**.
- Σωστό στρογγυλοποιημένο σύνολο: **1/7 θετικά αποσπάσματα**.
- Ψεύτικο θετικό σύνολο: **2/5 μηδενικά αποσπάσματα**.
- Στα ίδια τα παραδείγματα εκπαίδευσης το τελικό μοντέλο ταιριάζει 12/12 στρογγυλοποιημένα σύνολα· αυτό δεν αποτελεί γενίκευση.

Πρόκειται για χρονικό μοντέλο εκτίμησης πλήθους με παγωμένα γενικά χαρακτηριστικά εικόνας YOLO, όχι ολοκληρωμένο ανιχνευτή και ιχνηλάτη κάθε φυσικού μπλοκ. Οι δεκαδικές έξοδοι είναι αναμενόμενα πλήθη. Τα διαστήματα απόθεσης είναι προσεγγιστικές επισημάνσεις του βοηθού· τα συνολικά πλήθη προέρχονται από τις επιβεβαιώσεις του χρήστη.

Οι ίδιες μικρές ομάδες ανάπτυξης έχουν εξεταστεί σε προηγούμενες προσεγγίσεις. Δεν αποτελούν νέο ανεξάρτητο τεστ αποδοχής. Επειδή άλλαξαν και η αρχιτεκτονική και οι επισημάνσεις, δεν αποδίδουμε διαφορά μόνο στα fps.

## Κανόνες επισημάνσεων

1. Μετράμε πραγματικά μπλοκ που αφήνονται στη δεξαμενή, μία φορά ανά ολοκληρωμένη απόθεση.
2. Δεν υποθέτουμε δύο ανά κίνηση, δέκα ανά παλέτα ή 228 ανά δεξαμενή.
3. Σημειώνουμε ποσότητα, σήκωμα, μεταφορά, απόθεση και προορισμό. Το τρίμμα και οι κινήσεις με κενά χέρια είναι διαφορετικές περιπτώσεις.
4. Ό,τι δεν φαίνεται παραμένει άγνωστο. Μια κίνηση που κόβεται στο όριο αποσπάσματος δεν γίνεται μηδενικό γεγονός.
5. Οι πλευρές αριστερά/δεξιά διακρίνουν ταυτόχρονες κινήσεις· δεν ταυτοποιούν εργαζομένους.
6. Η 26/9 και η δεσμευμένη 3/10 δεν χρησιμοποιούνται για εκπαίδευση αυτής της νέας παρτίδας.
7. Η 26/9 έχει ήδη εξεταστεί για διάγνωση σφαλμάτων, άρα δεν την παρουσιάζουμε ως τελείως ανέγγιχτο τυφλό τεστ.

Η νέα παρτίδα `sequence_annotation_v4` έχει έξι μη επιβεβαιωμένα αποσπάσματα με χρόνο και φόρμα αξιολόγησης. Δεν έχουν μετατραπεί σε ετικέτες εκπαίδευσης χωρίς απαντήσεις χρήστη.

## Εκκρεμότητες

Αξιόπιστη γενίκευση καταμέτρησης μπλοκ, αυτόματη αλλαγή δεξαμενής, αντιστοίχιση καμερών 11/15, επαλήθευση ώρας κάμερας και έλεγχος συνεχούς ζωντανής λειτουργίας. Η μέχρι τώρα υλοποίηση και οι δοκιμές δεν τεκμηριώνουν ότι έχουν λυθεί.

Τα τρίτα πακέτα και τα αρχικά προεκπαιδευμένα βάρη διατηρούν τις άδειες των δημιουργών τους. Αυτό το snapshot δεν ορίζει νέα άδεια για το έργο.
'''

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--refresh',action='store_true');args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'work').mkdir(exist_ok=True)
    if (OUT/'snapshot_manifest.json').exists() and not args.refresh:raise RuntimeError('Existing snapshot; use explicit --refresh only for this prepared export')
    copied=[]
    for p in sorted((ROOT/'work').glob('*.py')):
        data=sanitize(p.read_text(encoding='utf-8-sig'))
        compile(data,str(p),'exec')
        dest=OUT/'work'/p.name;dest.write_text(data,encoding='utf-8');copied.append(dest)
    archives=[];excluded=0;removed_notebook_outputs=0
    package=OUT/'snapshot-data.zip';members={}
    with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        candidates=list((ROOT/'outputs').rglob('*'))
        skip={'feta_env','python_packages','video_decoder','__pycache__','facility_media','.git'}
        for base,dirs,files in os.walk(ROOT/'work'):
            dirs[:]=[d for d in dirs if d not in skip]
            candidates.extend(Path(base)/name for name in files)
        for p in sorted(candidates):
            if not p.is_file():continue
            if p.suffix.lower() not in TEXT or p.name.lower() in ('kaggle.json','credentials.json'):
                excluded+=1;continue
            text=p.read_text(encoding='utf-8-sig',errors='strict')
            if p.suffix=='.ipynb':
                obj=json.loads(text)
                for cell in obj.get('cells',[]):
                    if cell.get('cell_type')=='code':
                        removed_notebook_outputs+=len(cell.get('outputs',[]));cell['outputs']=[];cell['execution_count']=None
                obj.get('metadata',{}).pop('widgets',None)
                text=json.dumps(obj,ensure_ascii=False,indent=1)
            data=sanitize(text).encode('utf-8');name=p.relative_to(ROOT).as_posix()
            z.writestr(name,data);members[name]=sha(data)
    archives.append(dict(file=package.name,sha256=sha(package.read_bytes()),bytes=package.stat().st_size,members=members))
    model_files=sorted(p for p in (ROOT/'outputs').rglob('*') if p.is_file() and p.suffix.lower() in ('.pt','.pth','.safetensors','.npy'))
    groups=[];group=[];size=0
    for p in model_files:
        if group and size+p.stat().st_size>18*1024*1024:groups.append(group);group=[];size=0
        group.append(p);size+=p.stat().st_size
    if group:groups.append(group)
    for i,group in enumerate(groups,1):
        package=OUT/f'snapshot-models-{i:02d}.zip';members={}
        with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED,compresslevel=4) as z:
            for p in group:
                data=p.read_bytes();name=p.relative_to(ROOT).as_posix();z.writestr(name,data);members[name]=sha(data)
        archives.append(dict(file=package.name,sha256=sha(package.read_bytes()),bytes=package.stat().st_size,members=members))
    (OUT/'restore_snapshot.py').write_text(RESTORE,encoding='utf-8')
    handoff=ROOT/'work/project_handoff'
    assert (handoff/'README.md').exists(),'English handoff documents are required'
    for p in handoff.iterdir():
        if p.is_file() and p.suffix.lower() in ('.md','.json'):
            (OUT/p.name).write_text(sanitize(p.read_text(encoding='utf-8')),encoding='utf-8')
    (OUT/'.gitignore').write_text('.venv/\n__pycache__/\n*.pyc\n.env\n.env.*\nwork/facility_media/\nwork/unseen_test_20260926/\nwork/feta_env/\noutputs/\n',encoding='utf-8')
    packages=['numpy','opencv-python','Pillow','torch','torchvision','ultralytics','transformers','safetensors','imageio-ffmpeg']
    versions={}
    for name in packages:
        try:versions[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:versions[name]=None
    core=['numpy','opencv-python','Pillow','torch','torchvision','ultralytics']
    (OUT/'requirements-core.txt').write_text('\n'.join(n+'=='+versions[n] for n in core if versions[n])+'\n',encoding='utf-8')
    (OUT/'runtime_versions.json').write_text(json.dumps(versions,indent=2),encoding='utf-8')
    report=dict(schema_version=1,project='orfeastops/prolacata-ai-vision',snapshot_date='2026-10-27',
        original_scripts=len(copied),archives=archives,raw_media_included=False,credentials_included=False,
        excluded_output_files=excluded,notebook_output_cells_removed=removed_notebook_outputs,
        raw_workspace_unchanged=True,production_ready=False,
        path_note='Original workspace prefix replaced with dot in text copies; relative paths resolve from repository root',
        direct_files={p.relative_to(OUT).as_posix():sha(p.read_bytes()) for p in copied})
    (OUT/'snapshot_manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(folder=str(OUT),scripts=len(copied),archives=[dict(file=a['file'],MiB=round(a['bytes']/1048576,2),members=len(a['members'])) for a in archives],raw_media_included=False),indent=2))

if __name__=='__main__':main()
