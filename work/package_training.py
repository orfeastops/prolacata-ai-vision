import pathlib,json,hashlib,zipfile
root=pathlib.Path('outputs/feta_training')
report=json.loads((root/'model_report.json').read_text())
provenance=dict(model='YOLO26n',trained_class='gloved_hand',selected_training_run=report['selected'],
 source_weights_url='https://huggingface.co/Ultralytics/YOLO26/resolve/main/yolo26n.pt',
 source_weights_sha256=hashlib.sha256((root/'yolo26n.pt').read_bytes()).hexdigest(),
 trained_weights_sha256=hashlib.sha256((root/'hands_detector.pt').read_bytes()).hexdigest(),
 camera=11,crop_xyxy=[800,720,1440,1080],training_date='2026-10-23',
 block_counting_trained=False,tank_counting_trained=False,production_ready=False)
(root/'provenance.json').write_text(json.dumps(provenance,indent=2))
result='''ΠΡΑΓΜΑΤΙΚΑ ΑΠΟΤΕΛΕΣΜΑΤΑ ΠΡΩΤΗΣ ΕΚΠΑΙΔΕΥΣΗΣ

Έγιναν δύο τοπικές εκπαιδεύσεις YOLO26n και επιλέχθηκε η έκδοση v2.
Το μοντέλο αναγνωρίζει χέρια με γάντια στην περιοχή γεμίσματος της κάμερας 11.
Εκπαίδευση v2: 22 εικόνες της 1/10, 52 επισημασμένα χέρια.
Επικύρωση: 12 εικόνες της 21/10, 19 επισημασμένα χέρια.

Στη μικρή επικύρωση, όριο εμπιστοσύνης 0.25 και επικάλυψη IoU >= 0.5:
13 σωστές ανιχνεύσεις, 6 χαμένα χέρια, 3 λανθασμένες ανιχνεύσεις.
Precision 81.25%, recall 68.42%. Αυτά δεν είναι ακρίβεια καταμέτρησης φέτας.
Οι επισημάνσεις έγιναν από τον βοηθό, χωρίς ακόμη έλεγχο ειδικού παραγωγής.
Δεν υπάρχει ανεξάρτητο τελικό test set. Το δείγμα είναι πολύ μικρό για τελικό συμπέρασμα.

Το demo_21oct/hands_preview.mp4 περιέχει αυτόματες ανιχνεύσεις σε βίντεο της 21/10.
Χρησιμοποιεί χαμηλότερο όριο 0.10 για την προεπισκόπηση, επομένως μπορεί να δείχνει
περισσότερες λανθασμένες ή διπλές ανιχνεύσεις από το παραπάνω όριο 0.25.
Το βίντεο προέρχεται από clip που έχει και εικόνα στο validation, δεν είναι ανεξάρτητο test.

Δεν έχει εκπαιδευτεί ακόμη αναγνώριση μπλοκ φέτας, περιεχομένου χεριού, απόρριψης τρίμματος,
δεξαμενών, μεταφοράς 11→15, ζύγισης ή εξόδου παλετών.
Το μοντέλο δεν είναι έτοιμο για καθημερινή αναφορά παραγωγής.
Είναι πρώτο πραγματικό εκπαιδευμένο υπομοντέλο και σημείο εκκίνησης για περαιτέρω εκπαίδευση.
'''
(root/'RESULTS_EL.txt').write_text(result,encoding='utf-8')
files=[]
for pattern in ('*.py','*.yaml','*.txt','*.json','hands_detector.pt','yolo26n.pt','validation_comparison_*.jpg'):
 files.extend(root.glob(pattern))
for dirname in ('dataset','dataset_v2'):
 files.extend(p for p in (root/dirname).rglob('*') if p.is_file() and p.suffix in ('.jpg','.txt'))
files.extend(p for p in (root/'demo_21oct').glob('*') if p.suffix in ('.mp4','.json','.jpg'))
for version in ('v1','v2'):
 files.extend(p for p in (root/f'runs/hands_{version}').glob('*') if p.suffix in ('.csv','.yaml','.png'))
with zipfile.ZipFile('outputs/feta_training_model.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(set(files)):z.write(p,'feta_training/'+str(p.relative_to(root)).replace('\\','/'))
print('Selected',report['selected'],'checkpoint SHA256',provenance['trained_weights_sha256'])
print('Packaged files',len(set(files)),'zip bytes',pathlib.Path('outputs/feta_training_model.zip').stat().st_size)
