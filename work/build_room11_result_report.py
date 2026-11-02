"""Summarize saved predictions without changing inference or reference labels."""
import argparse,json,html,hashlib
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--base',required=True);a=p.parse_args()
    b=Path(a.base);rows=[]
    for folder,role,reference in [('dev10_station07','10/10 — ανάπτυξη',1),
                                  ('validation17_run02','17/10 — validation',1),
                                  ('test28_180_run01','28/10 — τρίλεπτο test',1)]:
        root=b/folder
        if not (root/'result.json').exists():raise RuntimeError(f'{folder} is not complete')
        export=root/'clock_v2' if (root/'clock_v2').exists() else root
        r=json.loads((root/'result.json').read_text());events=json.loads((export/'storage_predictions.json').read_text())
        clocks=json.loads((export/'clock_audit.json').read_text())
        rows.append(dict(run=folder,role=role,automatic_storages=len(events),
                         manually_observed_loaded_departures=reference,
                         automatic_exit_proposals=len(r['exits']),events=events,
                         pending_clock=len(clocks['pending']),records=str((export/'storage_predictions.json').relative_to(b)).replace('\\','/')))
    frozen=json.loads((b/'test28_180_run01/frozen_config.json').read_text())
    source=Path(__file__).with_name('run_room11_storage.py')
    assert hashlib.sha256(source.read_bytes()).hexdigest()==frozen['code_sha256'], 'Code changed after test started'
    summary=dict(status='experimental_integration_evaluated',production_ready=False,rows=rows,
        test28_tuned=False,whole_day_evaluated=False,old_manual25_not_automatic_result=True,
        rule='Cheese placement at production station linked to one outward tank trajectory; record date and exit time.',
        important_limit='Station memory bridges detector-ID fragmentation heuristically. Incomplete recording or unrecognized placement can miss an otherwise loaded departure.',
        validation_reference_note='The17Oct excerpt starts with an already loaded tank; its prior manual label is one loaded exit, not a verified complete filling sequence.',
        checkpoint_hashes={k:v for k,v in frozen.items() if k.endswith('sha256')})
    (b/'evaluation_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    cells=''.join('<tr><td>'+html.escape(row['role'])+'</td><td>'+str(row['automatic_storages'])+'</td><td>'+str(row['manually_observed_loaded_departures'])+'</td><td><a href="'+row['records']+'">Καταγραφές</a></td></tr>' for row in rows)
    events=''.join('<li>'+html.escape(e['date']+' '+e['time'])+' — Αποθήκευση δεξαμενής</li>' for e in rows[-1]['events'])
    text='''<!doctype html><html lang="el"><meta charset="utf-8"><title>Μετρητής αποθήκευσης — δοκιμή</title><style>body{font:18px system-ui;max-width:1000px;margin:40px auto;padding:0 20px;line-height:1.6}td,th{padding:10px;border-bottom:1px solid #ccc;text-align:left}img{max-width:100%}</style><h1>Μετρητής αποθήκευσης δεξαμενών</h1><p>Κανόνας: τοποθέτηση τυριού στον σταθμό παραγωγής → εξερχόμενη διαδρομή δεξαμενής από το δωμάτιο11 → μία ημερομηνία και ώρα.</p><h2>Αποτελέσματα δοκιμών</h2><table><tr><th>Απόσπασμα</th><th>Αυτόματες αποθηκεύσεις</th><th>Οπτικά παρατηρημένες φορτωμένες έξοδοι</th><th>Αρχείο</th></tr>'''+cells+'''</table><h2>Αυτόματες καταγραφές28/10</h2><ul>'''+events+'''</ul><p>Πειραματική έκδοση, όχι αποδεδειγμένη αξιοπιστία ημέρας. Η17/10 ξεκινά με ήδη φορτωμένη δεξαμενή και δεν αναγνωρίστηκε προηγούμενη τοποθέτηση μέσα στο απόσπασμα. Η αντιστοίχιση μέσω σταθμού παραγωγής είναι εκτίμηση όταν αλλάζει το ID του detector. Τα κενά καταγραφής καθαρίζουν τη μνήμη. Δεν μεταφέρεται ακόμη κατάσταση μεταξύ αρχείων.</p><p>Η δοκιμή28/10 αφορά μόνο180 δευτερόλεπτα. Οι παλιές25 χειροκίνητα επιβεβαιωμένες έξοδοι δεν είναι αποτέλεσμα αυτού του αυτόματου συστήματος. Δεν υπολογίζεται ποσότητα, πληρότητα ή βάρος.</p><p><a href="evaluation_summary.json">Σύνοψη και hashes</a> · <a href="implementation_manifest.json">Κώδικας και έλεγχοι</a></p><h2>Καρέ εξόδου28/10</h2><img src="test28_180_run01/exit_0000.jpg" alt="Overlay εξόδου"></html>'''
    (b/'review.html').write_text(text,encoding='utf-8')
    print(json.dumps({'rows':rows,'report':str(b/'review.html')},ensure_ascii=False))

if __name__=='__main__':main()
