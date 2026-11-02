"""Inventory camera.zip without unpacking video or exposing held-out pixels."""
import collections, datetime as dt, hashlib, html, json, re, shutil, zipfile
from pathlib import Path
from PIL import Image, ImageDraw
import io
from tank_counting_contract import apply_contract

archive=Path('C:/Users/evant/Desktop/camera.zip')
out=Path('outputs/tank_transfer_training_v1');out.mkdir(exist_ok=True)
pat=re.compile(r'Camera_(11|15)_DVR_(\d{14})_(\d{14})_')
split={'20261017':'validation','20261025':'test','20261028':'test'}
old=json.loads(Path('outputs/camera_video_collection/inventory.json').read_text())['records']
old_intervals=set()
for row in old:
    m=pat.search(row['basename'])
    if m:old_intervals.add(m.groups())
records=[]; groups=collections.defaultdict(list)
with zipfile.ZipFile(archive) as z:
    for info in z.infolist():
        ext=Path(info.filename).suffix.lower()
        if info.is_dir() or ext not in {'.mp4','.jpg'}:continue
        m=pat.search(Path(info.filename).name)
        if not m:continue
        camera,start,end=m.groups();date=start[:8]
        r=dict(archive=str(archive),member=info.filename,basename=Path(info.filename).name,
               media_type='video' if ext=='.mp4' else 'export_still',camera=int(camera),date=date,
               filename_start=start,filename_end=end,uncompressed_bytes=info.file_size,
               zip_crc32=f'{info.CRC:08x}',split=split.get(date,'train'),
               same_camera_time_range_in_prior_inventory=m.groups() in old_intervals,
               sha256=None,pixel_inspected=False)
        records.append(r)
        if ext=='.mp4':groups[(date,int(camera))].append(r)
    coverage=[]
    for (date,camera),rs in sorted(groups.items()):
        intervals=sorted((dt.datetime.strptime(r['filename_start'],'%Y%m%d%H%M%S'),dt.datetime.strptime(r['filename_end'],'%Y%m%d%H%M%S')) for r in rs)
        merged=[]
        for a,b in intervals:
            if merged and a<=merged[-1][1]:merged[-1][1]=max(merged[-1][1],b)
            else:merged.append([a,b])
        coverage.append(dict(date=date,camera=camera,videos=len(rs),first=str(merged[0][0].time()),last=str(merged[-1][1].time()),
                             filename_interval_union_hours=round(sum((b-a).total_seconds() for a,b in merged)/3600,3),
                             filename_gap_count=len(merged)-1,split=split.get(date,'train'),
                             prior_interval_matches=sum(r['same_camera_time_range_in_prior_inventory'] for r in rs),
                             caveat='Filename intervals only. Actual decoded coverage and camera clock offsets remain to be checked.'))
    # Small chronological survey from training dates only; test/validation media are untouched.
    stills=collections.defaultdict(list)
    for r in records:
        if r['media_type']=='export_still' and r['split']=='train':stills[(r['date'],r['camera'])].append(r)
    sample_rows=[]
    for (date,camera),rs in sorted(stills.items()):
        rs.sort(key=lambda r:r['filename_start'])
        selected=[rs[round(i*(len(rs)-1)/5)] for i in range(6)]
        sheet=Image.new('RGB',(1440,600))
        for j,r in enumerate(selected):
            raw=z.read(r['member']);im=Image.open(io.BytesIO(raw)).convert('RGB')
            sha=hashlib.sha256(raw).hexdigest()
            folder=out/'training_scene_samples'/date/f'camera{camera}';folder.mkdir(parents=True,exist_ok=True)
            image_path=folder/f'{r["filename_start"]}_{sha[:10]}.jpg'
            image_path.write_bytes(raw)
            sample_rows.append(dict(member=r['member'],local_path=str(image_path),sha256=sha,split='train',
                                    annotation_status='unlabelled_survey_only',not_a_training_label=True))
            r['sha256']=sha
            tile=Image.new('RGB',(480,300))
            im.thumbnail((480,270));tile.paste(im,((480-im.width)//2,30))
            ImageDraw.Draw(tile).text((5,6),f'{date} camera{camera} file start {r["filename_start"][8:]}',fill='white')
            sheet.paste(tile,((j%3)*480,(j//3)*300))
        sheet_dir=out/'training_scene_samples';sheet_dir.mkdir(exist_ok=True)
        sheet.save(sheet_dir/f'{date}_camera{camera}.jpg')
    stat=archive.stat()
    inventory=dict(archive=str(archive),archive_bytes=stat.st_size,archive_mtime_ns=stat.st_mtime_ns,
                   media_records=len(records),videos=sum(r['media_type']=='video' for r in records),
                   export_stills=sum(r['media_type']=='export_still' for r in records),coverage=coverage,records=records,
                   duplicate_policy='Camera and filename start/end identify possible repeated exports, not byte identity. Do not count prior and new exports twice. Hash extracted media before dataset release; ZIP CRC is not a cryptographic identity.')
    (out/'archive_inventory.json').write_text(json.dumps(inventory,indent=2,ensure_ascii=False),encoding='utf-8')
    (out/'scene_sample_manifest.json').write_text(json.dumps(sample_rows,indent=2,ensure_ascii=False),encoding='utf-8')
    for name in ['train','validation','test']:
        (out/f'{name}_sources.json').write_text(json.dumps([r for r in records if r['media_type']=='video' and r['split']==name],indent=2,ensure_ascii=False),encoding='utf-8')

plan=dict(
    status='source_inventory_and_day_split_prepared_not_trained',
    objective='One production transfer event for a cheese-loaded tank leaving the filling station in camera11 and entering camera15. Keep later scale dwell and storage placement as states of the same event.',
    proposed_initial_baseline=dict(detector='YOLO26s (yolo26s.pt), fine-tuned on tank boxes. Ultralytics 8.4.184 is installed locally. Record checkpoint SHA256 before the first run; checkpoint has not been downloaded or trained by this preparation.',
                                  tracker='ByteTrack, within each camera; compare BoT-SORT only if measured ID fragmentation warrants it.',
                                  count_logic='A tank observed at the filling station crosses ordered inside/door/outside zones in the outbound direction. Persist the event ledger; a new track ID alone is not a new tank.',
                                  load_state='Use filling-station origin plus several visible frames. Annotate cheese, empty, scrap and obscured/unknown separately. A white cover alone is insufficient.',
                                  camera15='Calibrate timestamp offset; link observed entries by time, direction and visual sequence. Preserve unmatched/ambiguous events. Confirm scale-zone dwell and later storage separately.',
                                  gaps='Do not infer an unobserved crossing from a new ID or stitch across missing time. Record coverage uncertainty.'),
    split_policy=dict(unit='Entire calendar day, both cameras and all adjacent clips together.',
                      archive_train_days=sorted({r['date'] for r in records if r['split']=='train'}),
                      validation_days=['20261017'],locked_test_days=['20261025','20261028'],
                      test_policy='No labels, test predictions, sampled pixels, prompt/threshold selection or training on held-out days before the detector and event rules are frozen. Labels may later be built independently for scoring without feeding model development.',
                      prior_data='Previously inspected 2026-10-01,03,21 are development data. The corrected count45 on21/10 is diagnostic only, not a blind acceptance test. Keep previous Sept26 cheese-block test isolated.'),
    labels=dict(image='Boxes for every visible tank in the chosen image/ROI. Object identity tank, plus content attributes when observable. Include empty returns, scrap, stationary rows, people without tanks, covered returns and forklift relocation.',
                sequence='Track identities, direction, filling-origin evidence, exit and entry timestamps, duplicate links, gaps and uncertain identity. Sample before/during/after real crossings, not only export thumbnails.',
                quality='Assistant-generated proposals require visual review before becoming training labels. Pseudo-labels remain marked until reviewed. More correlated frames do not replace distinct events.'),
    evaluation=dict(primary=['Matched transfer-event precision','Matched transfer-event recall','False events','Missed events','Duplicate counts','Daily count error','Cross-camera match errors','Unknown/unmatched event rate','Runtime and latency'],
                    matching='One-to-one predicted/reference event matching; fix timestamp tolerance on validation. Correct totals may hide compensating errors.',
                    secondary='Image mAP is a detector diagnostic, not counting accuracy.',
                    independent_reference='Known daily totals are an aggregate check; timestamped reference events are required to diagnose false/missed/duplicate events.'),
    runtime=dict(video='Decode sequentially with original timestamps. Initial transfer-tracking evaluation should keep native frames; only reduce sampling after validating event-level equivalence.',
                 storage='Archive remains in place. Selective extraction/cache only; no extraction or execution of bundled EXE/DLL files.',
                 training_compute='GPU training is preferable once reviewed annotations exist; no GPU session or upload started by this preparation.'),
    next_step='Build reviewed tank boxes and transfer-event sequences from training days; prepare a runnable GPU training package, validate on17/10, freeze, then evaluate25/10 and28/10.'
)
(out/'training_protocol.json').write_text(json.dumps(plan,indent=2,ensure_ascii=False),encoding='utf-8')
e=html.escape
rows=[]
for date in sorted({c['date'] for c in coverage}):
    cs={c['camera']:c for c in coverage if c['date']==date}
    rows.append(f'<tr><td>{date[6:8]}/{date[4:6]}/{date[:4]}</td><td>{cs[11]["videos"]}</td><td>{cs[15]["videos"]}</td><td>{cs[11]["first"]}–{cs[11]["last"]}</td><td>{cs[15]["first"]}–{cs[15]["last"]}</td><td>{split.get(date,"train")}</td></tr>')
page='''<!doctype html><html lang="el"><meta charset="utf-8"><title>Υλικό δεξαμενών · camera.zip</title><style>body{font:16px/1.6 system-ui;background:#f4f6f8;color:#172a3b;max-width:1200px;margin:auto;padding:32px}table{border-collapse:collapse;background:white;width:100%}td,th{padding:10px;border-bottom:1px solid #dde5ea;text-align:left}.note{padding:18px;background:#fff2cd}a{color:#006489}img{max-width:100%}details{margin:18px 0;background:white;padding:16px}</style><h1>camera.zip · υλικό για καταμέτρηση δεξαμενών</h1><p><b>4.087 βίντεο + 4.087 συνοδευτικές εικόνες, 11 ημέρες, κάμερες 11 και 15.</b></p><p class="note">Έγιναν απογραφή και διαχωρισμός ημερών. Δεν έχει εκπαιδευτεί μοντέλο δεξαμενών. Οι ώρες προέρχονται από τα ονόματα αρχείων και δεν αποδεικνύουν συνεχή κάλυψη.</p><table><tr><th>Ημέρα</th><th>Βίντεο 11</th><th>Βίντεο 15</th><th>Εύρος 11</th><th>Εύρος 15</th><th>Χρήση</th></tr>'''+''.join(rows)+'''</table><p>train: ανάπτυξη/εκπαίδευση · validation: επιλογή ρυθμίσεων · test: τελικός ανεξάρτητος έλεγχος. Όλα τα αρχεία της ίδιας ημέρας και των δύο καμερών ανήκουν στο ίδιο σύνολο. Οι 25/10 και 28/10 διατηρήθηκαν χωρίς οπτική επιθεώρηση. Η 21/10 έχει ήδη εξεταστεί και δεν είναι ανεξάρτητο τεστ.</p><h2>Προτεινόμενη μέθοδος</h2><p>Ανιχνευτής δεξαμενών YOLO → παρακολούθηση ByteTrack → καταγραφή της διαδρομής θέση γεμίσματος / πόρτα / έξοδος → αντιστοίχιση εισόδου στην 15 → στάση ζυγαριάς → αποθήκευση. Κάθε μεταφορά αποκτά μία εγγραφή, με ώρες και οπτικά τεκμήρια.</p><p>Οι άδειες, τα τρίμματα, οι κινήσεις ήδη αποθηκευμένων δεξαμενών και οι αβέβαιες περιπτώσεις πρέπει να σημειώνονται χωριστά. Η στάση στη ζυγαριά δεν παρέχει από μόνη της αριθμητικό βάρος.</p><p><a href="archive_inventory.json">Απογραφή</a> · <a href="training_protocol.json">Πρωτόκολλο εκπαίδευσης και αξιολόγησης</a></p>'''
for path in sorted((out/'training_scene_samples').glob('*.jpg')):
    page+=f'<details><summary>Δείγματα ανάπτυξης: {e(path.stem)}</summary><img loading="lazy" src="training_scene_samples/{e(path.name)}"><p>Συνοδευτικές εικόνες εξαγωγής · χωρίς ετικέτες εκπαίδευσης.</p></details>'
(out/'inventory_review.html').write_text(page+'</html>',encoding='utf-8')
apply_contract(out)
print(json.dumps(dict(videos=inventory['videos'],stills=inventory['export_stills'],coverage=coverage,
                     selected_training_stills=len(sample_rows),free_bytes=shutil.disk_usage('.').free,
                     output=str(out.resolve())),indent=2))
