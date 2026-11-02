import json,hashlib
from pathlib import Path
base=Path('D:/Codex/tank-storage');run=base/'test28_full_run01'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
r=read(run/'result.json');a=read(run/'clock_v2/clock_audit.json')
records=read(run/'clock_v2/storage_predictions.json')
ref=read(Path('D:/Codex/tank-day28/heldout_counting/test28_fullclip/evaluation_summary.json'))
assert (run/'pipeline_complete.json').exists()
matches=[]
for e in r['exits']:
    candidates=[x for x in ref['events'] if abs(x['pts_s']-e['pts_s'])<.01]
    matches.append({'track':e['track'],'pts_s':e['pts_s'],'placement_proposals':len(e.get('placement_evidence',[])),
        'matching_reference_events':len(candidates),'reference_clock':candidates[0]['camera_clock'] if len(candidates)==1 else None,
        'placement_to_physical_tank_identity_independently_verified':False})
summary={'status':'inference_complete_clock_failures_and_identity_review_pending','frames':r['frames'],
    'automatic_linked_exit_proposals':len(r['exits']),'automatic_timestamped_records':len(records),
    'pending_clock':len(a['pending']),'events':records,'proposal_reference_matches':matches,
    'reference_exhaustive':False,'manual_hour_annotations_received':False,'hour_evaluation_complete':False,
    'do_not_sum_with_first180':True,'daily_count':None,
    'frozen_config':read(run/'frozen_config.json'),
    'artifacts_sha256':{str(p.relative_to(base)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [run/'result.json',run/'clock_v2/clock_audit.json',run/'pipeline_complete.json']}}
(run/'evaluation_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
p=base/'evaluation_summary.json';existing=read(p);existing['full20minute_run']=summary
p.write_text(json.dumps(existing,ensure_ascii=False,indent=2),encoding='utf-8')
p=base/'review.html';html=p.read_text(encoding='utf-8')
marker='<!-- full-run-update -->'
if marker not in html:
    section=marker+'''<section><h2>Νεότερο: ολοκληρώθηκε το πλήρες 20λεπτο</h2>
<p>18.555 καρέ: 3 αυτόματες προτάσεις εξόδου με σύνδεση σε τοποθέτηση τυριού, αλλά <b>1 τελική καταγραφή με αυτόματη ώρα</b> (09:47:12). Οι άλλες 2 κρατήθηκαν εκτός εξαγωγής λόγω αποτυχίας ανάγνωσης ρολογιού.</p>
<p>Οι 3 χρόνοι βίντεο αντιστοιχούν στις 3 εξόδους της προηγούμενης δειγματοληπτικής αναφοράς. Η αντιστοίχιση δεν αποδεικνύει από μόνη της ότι κάθε σύνδεση γεμίσματος αφορά την ίδια φυσική δεξαμενή. Ο ανεξάρτητος έλεγχος παραμένει ανοικτός. Δεν πρόκειται για ολοκληρωμένη ωριαία δοκιμή.</p>
<p>Το τρίλεπτο παρακάτω περιέχεται στο πλήρες απόσπασμα και δεν προστίθεται. Τα μοντέλα και τα όρια απόφασης δεν προσαρμόστηκαν.</p>
<p><a href="test28_full_run01/evaluation_summary.json">Αναλυτικό αποτέλεσμα</a> · <a href="test28_full_run01/clock_v2/clock_audit.json">Έλεγχος ρολογιού</a> · <a href="hour_manual_review.html">Επισήμανση από τον χρήστη</a></p></section><h2>Ιστορικό προηγούμενων δοκιμών</h2>'''
    html=html.replace('<h2>Αποτελέσματα δοκιμών</h2>',section+'<h2>Αποτελέσματα δοκιμών</h2>')
    p.write_text(html,encoding='utf-8')
p=base/'continuation.json';c=read(p);c['status']='fullclip_complete_hour_pending';c['next']='Continue hour evaluation; fullclip has 3 linked proposals but only 1 automatic timestamped record, 2 OCR pending. Do not tune on test28. Await user reference while preparing remaining sources.'
c['browser_fix']['exec_session']=20803
c['browser_fix']['instruction']='Encoder active under lock; consult review_proxies/status.json. First attempt failed on non-increasing PTS; corrected encoder logs omitted repeated PTS in clip timing JSON. Do not duplicate. User labels remain in browser storage; no received labels yet.'
p.write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'proposals':len(r['exits']),'exported_records':len(records),'pending_clock':len(a['pending']),'reference_matches':matches}))
