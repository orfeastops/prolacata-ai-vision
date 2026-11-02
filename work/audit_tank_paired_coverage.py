"""Compare export time ranges and decode a small training-only integrity sample."""
import collections, datetime as dt, io, json, re, zipfile
from pathlib import Path
import av
from PIL import Image,ImageDraw

root=Path('outputs/tank_transfer_training_v1')
inv=json.loads((root/'archive_inventory.json').read_text(encoding='utf-8'))
archive=Path(inv['archive']);stat=archive.stat()
assert stat.st_size==inv['archive_bytes'] and stat.st_mtime_ns==inv['archive_mtime_ns'], 'Archive changed; refresh its inventory before auditing.'
rs=[r for r in inv['records'] if r['media_type']=='video']
parse=lambda s:dt.datetime.strptime(s,'%Y%m%d%H%M%S')
fmt=lambda t:t.isoformat(sep=' ')
groups=collections.defaultdict(list)
for r in rs:groups[(r['date'],r['camera'])].append(r)
for items in groups.values():items.sort(key=lambda r:r['filename_start'])

def merge(items):
    merged=[]
    for a,b in sorted((parse(r['filename_start']),parse(r['filename_end'])) for r in items):
        if merged and a<=merged[-1][1]:merged[-1][1]=max(merged[-1][1],b)
        else:merged.append([a,b])
    return merged

def overlap(a,b):
    out=[];i=j=0
    while i<len(a) and j<len(b):
        lo=max(a[i][0],b[j][0]);hi=min(a[i][1],b[j][1])
        if lo<hi:out.append([lo,hi])
        if a[i][1]<b[j][1]:i+=1
        else:j+=1
    return out

coverage=[];pairs=[]
for day in sorted({r['date'] for r in rs}):
    left,right=groups[(day,11)],groups[(day,15)]
    m11,m15=merge(left),merge(right);both=overlap(m11,m15)
    coverage.append(dict(date=day,split=left[0]['split'],camera11_files=len(left),camera15_files=len(right),
                         camera11_outer_range=[fmt(m11[0][0]),fmt(m11[-1][1])],camera15_outer_range=[fmt(m15[0][0]),fmt(m15[-1][1])],
                         common_filename_ranges=[[fmt(a),fmt(b)] for a,b in both],
                         common_filename_union_minutes=round(sum((b-a).total_seconds() for a,b in both)/60,2),
                         common_interval_count=len(both),
                         caveat='Approximate filename-based overlap, not continuous decoded footage or proven clock synchronisation.'))
    for l in left:
        for r in right:
            a=max(parse(l['filename_start']),parse(r['filename_start']))
            b=min(parse(l['filename_end']),parse(r['filename_end']))
            if a<b:
                pairs.append(dict(date=day,split=l['split'],camera11_member=l['member'],camera15_member=r['member'],
                                  approximate_overlap=[fmt(a),fmt(b)],clock_calibration_status='not_calibrated',pixel_inspected=False))

# Check the actual final video of the three short camera11 days, plus paired
# beginning/end and mid-production samples from development days. No held-out pixels.
chosen=[]
for day in ['20261005','20261008','20261023']:
    chosen.append((groups[(day,11)][-1],'last_available_camera11_file'))
    chosen.append((groups[(day,15)][-1],'last_available_camera15_file'))
for day in ['20261006','20261013']:
    for camera in [11,15]:
        target=parse(day+'080000')
        chosen.append((min(groups[(day,camera)],key=lambda r:abs((parse(r['filename_start'])-target).total_seconds())),'development_clock_sample'))

dest=root/'paired_coverage_audit';dest.mkdir(exist_ok=True)
probe=[]
with zipfile.ZipFile(archive) as z:
    for i,(r,why) in enumerate(chosen):
        assert r['split']=='train'
        try:
            raw=z.read(r['member']);c=av.open(io.BytesIO(raw));s=c.streams.video[0]
            s.thread_type='AUTO';s.codec_context.thread_count=2
            duration=None if c.duration is None else c.duration/1e6
            n=0;first=last=None;first_t=last_t=None
            for f in c.decode(s):
                if first is None:
                    first=f.to_image();first_t=f.time
                last=f;n+=1
            assert last is not None
            last_t=last.time;last_image=last.to_image()
            sheet=Image.new('RGB',(1920,620));draw=ImageDraw.Draw(sheet)
            for j,(im,label) in enumerate([(first,'FIRST FRAME'),(last_image,'LAST FRAME')]):
                im.thumbnail((960,540));sheet.paste(im,(j*960,80))
                draw.text((j*960+5,5),f'{label} | {r["date"]} camera{r["camera"]}',fill='white')
                draw.text((j*960+5,25),r['basename'],fill='white')
                draw.text((j*960+5,45),f'container duration {duration} sec | decoded frames {n}',fill='white')
            path=dest/f'{r["date"]}_camera{r["camera"]}_{why}.jpg';sheet.save(path)
            c.close()
            probe.append(dict(member=r['member'],date=r['date'],camera=r['camera'],purpose=why,split=r['split'],
                              decoded_frames=n,first_frame_time=first_t,last_frame_time=last_t,
                              decoded_pts_span_seconds=None if first_t is None or last_t is None else round(last_t-first_t,3),
                              container_duration_seconds=duration,filename_duration_seconds=(parse(r['filename_end'])-parse(r['filename_start'])).total_seconds(),
                              evidence=str(path),clock_verified=False))
            print(f'{i+1}/{len(chosen)} {r["date"]} camera{r["camera"]} frames={n}',flush=True)
        except Exception as ex:
            probe.append(dict(member=r['member'],error=str(ex)))

report=dict(archive=str(archive),archive_unchanged_since_inventory=True,
            user_export_intent='Same selected dates and clock ranges for both cameras, as stated by the user.',
            actual_export_limitation='The delivered files contain different clip boundaries and incomplete temporal coverage per camera. This does not establish whether the cause is recorder scheduling, motion recording or export behaviour.',
            coverage=coverage,decoded_development_sample=probe,locked_test_pixels_decoded=0,
            pairing_policy='Use timestamps and calibrated camera clock offsets, never file indices or file counts. Keep each day and both camera streams in the same train/validation/test partition. Only label a complete transfer cycle when the relevant footage exists.')
(root/'paired_coverage_audit.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
(root/'paired_source_windows.json').write_text(json.dumps(pairs,indent=2,ensure_ascii=False),encoding='utf-8')
rows=[]
for r in coverage:
    a,b=r['camera11_outer_range'],r['camera15_outer_range']
    rows.append(f'<tr><td>{r["date"][6:8]}/{r["date"][4:6]}</td><td>{a[0][11:]}–{a[1][11:]}</td><td>{b[0][11:]}–{b[1][11:]}</td><td>{r["common_filename_union_minutes"]:.1f}</td></tr>')
section='''<!-- paired-coverage:start --><section id="paired-coverage"><h2>Κοινή χρονική κάλυψη</h2><p>Η επιλογή ίδιων ημερομηνιών και ωρών στην εφαρμογή βοηθά στην αντιστοίχιση. Τα αρχεία που παραδόθηκαν έχουν διαφορετικά όρια αποσπασμάτων ανά κάμερα. Παρακάτω φαίνονται τα εξωτερικά χρονικά όρια και η ένωση των κοινών διαστημάτων από τα ονόματα αρχείων.</p><table><tr><th>Ημέρα</th><th>Κάμερα 11</th><th>Κάμερα 15</th><th>Κοινά λεπτά εξαγωγών*</th></tr>'''+''.join(rows)+'''</table><p>*Προσεγγιστική κάλυψη από ονόματα αρχείων, με κενά μεταξύ αποσπασμάτων. Δεν είναι μέτρηση συνεχούς βίντεο ούτε πιστοποίηση συγχρονισμού. Δεν έχει εξακριβωθεί η αιτία των κενών. Η αντιστοίχιση θα γίνεται με χρόνο και οπτική συνέχεια, όχι με τη σειρά ή το πλήθος των αρχείων.</p><p><a href="paired_coverage_audit.json">Αναλυτικός έλεγχος κάλυψης και δειγμάτων</a> · <a href="paired_source_windows.json">Ζεύγη χρονικά επικαλυπτόμενων αρχείων</a></p></section><!-- paired-coverage:end -->'''
page=root/'inventory_review.html';text=page.read_text(encoding='utf-8')
if '<!-- paired-coverage:start -->' in text:
    text=re.sub(r'<!-- paired-coverage:start -->.*?<!-- paired-coverage:end -->',lambda m:section,text,flags=re.S)
else:text=text.replace('<h2>Προτεινόμενη μέθοδος</h2>',section+'<h2>Προτεινόμενη μέθοδος</h2>')
page.write_text(text,encoding='utf-8')
print(json.dumps({'days':len(coverage),'overlapping_file_pairs':len(pairs),'sample_errors':[p for p in probe if 'error' in p],'locked_test_pixels_decoded':0}))
