import pathlib,json,zipfile,collections,time,hashlib
ROOT=pathlib.Path('outputs/facility_dataset').resolve()
media=json.loads((ROOT/'media_manifest.json').read_text())
frames=json.loads((ROOT/'frame_manifest.json').read_text())
summary=json.loads((ROOT/'frame_pool_summary.json').read_text())
audit=json.loads((ROOT/'audit_summary.json').read_text())
portable=[]
for r in media:
 portable.append({k:v for k,v in r.items() if k not in ('local_path','occurrences')}|{'media_path':'media/'+pathlib.Path(r['local_path']).name,
  'source_archive_names':sorted({pathlib.Path(o['source']).name for o in r['occurrences']})})
(ROOT/'media_manifest_portable.json').write_text(json.dumps(portable,indent=2))
sequence_sources=[dict(media_path=r['media_path'],source_sha256=r['sha256'],camera=r['camera'],date=r['date'],
                      filename_start=r['filename_start'],filename_end=r['filename_end'],
                      annotation_status='unlabelled_continuous_video',clock_verified=False)
                  for r in portable if r['extension'] in ('.mp4','.avi','.dav','.mov')]
(ROOT/'continuous_video_manifest.json').write_text(json.dumps(sequence_sources,indent=2))
quality_count=sum(f['quality']['needs_quality_review'] for f in frames)
manifest=dict(unique_source_files=len(media),videos=len(sequence_sources),provided_images=len(media)-len(sequence_sources),
              frame_pool=len(frames),camera11_crops=summary['camera11_crops'],quality_review_flags=quality_count,
              labels_status='unlabelled',full_pool_training_completed=False,remote_upload_authorized=False,
              paid_compute_authorized=False,original_sources_unmodified=True,
              use='Full-source object annotation and continuous action/transfer learning. Private GPU preparation only; no remote upload performed.')
(ROOT/'bundle_manifest.json').write_text(json.dumps(manifest,indent=2))
text=f'''ΕΝΟΠΟΙΗΜΕΝΑ ΔΕΔΟΜΕΝΑ ΜΟΝΑΔΑΣ — ΟΛΕΣ ΟΙ ΠΗΓΕΣ

Έγινε έλεγχος SHA256 όλων των αρχείων ZIP και κάθε αρχείου πολυμέσων.
Μοναδικά αρχεία: {len(media)}. Βίντεο: {len(sequence_sources)}. Εικόνες: {len(media)-len(sequence_sources)}.
Δύο αρχεία ZIP ήταν ακριβή αντίγραφα και 196 εγγραφές πολυμέσων ήταν διπλότυπες.
Τα πρωτότυπα στην επιφάνεια εργασίας δεν τροποποιήθηκαν.

Κάμερα 11: 1/10, 3/10, 21/10.
Κάμερα 15: 1/10, 3/10, 5/10, 21/10, 22/10.

Εξήχθησαν συνολικά {len(frames)} εικόνες αναφοράς από όλες τις μοναδικές πηγές,
με 2126 επιπλέον crops της περιοχής γεμίσματος της κάμερας 11.
Όλα τα {len(sequence_sources)} βίντεο διατηρούνται πλήρη για εκμάθηση χρονικών ακολουθιών.
Τα καρέ βίντεο επιλέχθηκαν από καθαρά keyframes, ανά τουλάχιστον 30 δευτερόλεπτα,
για την προετοιμασία επισημάνσεων αντικειμένων. Δεν χρησιμοποιούνται για να μετρήσουν κινήσεις.
Οι κινήσεις πρέπει να παρακολουθούνται στο συνεχόμενο βίντεο.
Αποτυχίες εξαγωγής: {summary['failures']}. Σημαίες ελέγχου αντίθεσης: {quality_count}.
Τα ρολόγια και τα ονόματα αρχείων δεν έχουν ακόμη επαληθευτεί μεταξύ καμερών.

ΣΗΜΑΝΤΙΚΗ ΚΑΤΑΣΤΑΣΗ
Αυτά είναι ενοποιημένα δεδομένα και όχι ήδη επισημασμένη αλήθεια αναφοράς.
Δεν έχει ολοκληρωθεί εκπαίδευση μοντέλου πάνω σε όλη τη νέα βάση.
Δεν έχει επιλεγεί τελικό καλύτερο μοντέλο για καταμέτρηση μπλοκ και δεξαμενών.
Η προηγούμενη εκπαίδευση χεριών παραμένει ξεχωριστή μικρή αρχική δοκιμή.

ΑΡΧΕΙΑ
audit_summary.json / archive_audit.json: απογραφή και έλεγχος αντιγράφων.
frame_manifest.json: πλήρης προέλευση καρέ, camera/date, σχετικός χρόνος βίντεο και ποιότητα.
continuous_video_manifest.json: πλήρη βίντεο για επισημάνσεις ενεργειών.
media_manifest_portable.json: διαδρομές πολυμέσων μέσα στο πακέτο GPU.
facility_gpu_workflow.ipynb: notebook για μαζικές προτάσεις επισημάνσεων με Grounding DINO,
  έλεγχο των επισημάνσεων και σύγκριση υποψήφιων ανιχνευτών μετά τον έλεγχο.
model_comparison/: πραγματική πρώτη τοπική δοκιμή διαφορετικού προεκπαιδευμένου μοντέλου.

ΟΛΟΚΛΗΡΩΜΕΝΟΣ ΣΤΟΧΟΣ
Αναγνώριση χεριού και μπλοκ → παρακολούθηση μέχρι τον προορισμό → μία μέτρηση ανά τοποθέτηση.
Απόθεση τρίμματος ξεχωριστά από ολόκληρη φέτα. Διαχωριστικά και διορθώσεις δεν αυξάνουν τα μπλοκ.
Κάθε δεξαμενή πρέπει να συνδεθεί με πλήρη κύκλο γεμίσματος και μεταφορά 11→15.
Οι δεξαμενές τρίμματος μετρώνται κατά την ολοκλήρωση/απομάκρυνση, όχι ανά απόρριψη.
Η έξοδος φορτωμένης παλέτας στις 22/10 διακρίνεται από εσωτερική μετακίνηση.
Η τελική επιλογή μοντέλου απαιτεί έλεγχο ανά ολόκληρη δεξαμενή, μεταφορά και ημέρα.
Κάποια δεδομένα πρέπει να παραμείνουν εκτός εκπαίδευσης για ανεξάρτητη αξιολόγηση.

ΠΑΚΕΤΟ GPU
facility_gpu_bundle.zip περιέχει όλα τα μοναδικά βίντεο/εικόνες, τα καρέ, τα crops και τα manifests.
Έχει προετοιμαστεί τοπικά. Δεν έχει ανέβει στο Kaggle ή σε άλλη υπηρεσία.
Η μαζική ανάλυση με μεγάλο προεκπαιδευμένο μοντέλο είναι πολύ ταχύτερη σε GPU.
Το notebook δεν παρουσιάζει ανελεγμένες αυτόματες προτάσεις ως σωστές επισημάνσεις.
Δεν ξεκινά εποπτευόμενη εκπαίδευση πριν τον έλεγχο επισημάνσεων και διαχωρισμού συμβάντων.
'''
(ROOT/'STATUS_EL.txt').write_text(text,encoding='utf-8')
archive=pathlib.Path('outputs/facility_gpu_bundle.zip')
started=time.time();count=0
with zipfile.ZipFile(archive,'w',zipfile.ZIP_STORED,allowZip64=True) as z:
 for p in [ROOT/'bundle_manifest.json',ROOT/'media_manifest_portable.json',ROOT/'continuous_video_manifest.json',ROOT/'frame_manifest.json',ROOT/'frame_pool_summary.json',ROOT/'audit_summary.json',ROOT/'STATUS_EL.txt',ROOT/'facility_gpu_workflow.ipynb']:
  z.write(p,'facility_dataset/'+p.name);count+=1
 for folder in ('frames','camera11_crops'):
  for p in sorted((ROOT/folder).rglob('*')):
   if p.is_file():z.write(p,'facility_dataset/'+str(p.relative_to(ROOT)).replace('\\','/'));count+=1
 for i,r in enumerate(media):
  p=pathlib.Path(r['local_path']);z.write(p,'facility_dataset/media/'+p.name);count+=1
  if i%250==0:print('PACKAGING MEDIA',i,'/',len(media),flush=True)
print(json.dumps(dict(archive=str(archive.resolve()),bytes=archive.stat().st_size,files=count,elapsed_seconds=round(time.time()-started)),indent=2),flush=True)
