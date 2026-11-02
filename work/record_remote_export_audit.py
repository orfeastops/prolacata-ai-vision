import json, datetime, html
from pathlib import Path
root=Path(__file__).resolve().parents[1]
out=root/'outputs/tank_transfer_training_v1/dataset_v1'
audit=out/'remote_export_audit'
records=json.loads((audit/'manifest.json').read_text())
clocks=[['09:35:22','09:35:31','09:35:42','09:35:55'],['09:36:42','09:37:00','09:37:06','09:37:13'],['11:16:23','11:16:33','11:16:38','11:16:46'],['11:16:37','11:16:48','11:17:08','11:17:30']]
for r,cs in zip(records,clocks):
 for s,c in zip(r['samples'],cs): s['visible_camera_clock']=c
 r['review_scope']='Four boundary/context samples visually inspected; all frames decoded for integrity, not all visually inspected.'
report={'updated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'requested_intervals':['2026-10-06 09:35:30–09:37:30','2026-10-15 11:15:00–11:17:30'],'source':'iVMS4200 camera15 remote export, transferred through AnyDesk','records':records,'result':'Neither re-export supplies the missing trajectory interval. Keep both cycles partial. This establishes missing coverage in these exports, not proof that every DVR stream or backup lacks it.','limitations':['Initial frames can show stale clocks: 09:36:42 followed by 09:37:00; 11:16:37 followed by 11:16:48. PTS and filenames are not camera synchronization.','No new object labels, complete cycles, negatives or training release. Existing reviewed labels preserved.','16 audit sample presentations are tracked separately from the existing dataset review counters.']}
(audit/'review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
page='<html lang="el"><meta charset="utf-8"><title>Έλεγχος νέων εξαγωγών</title><body><h1>Έλεγχος νέων εξαγωγών iVMS</h1><p>Οι δύο νέες εξαγωγές δεν κάλυψαν τα ζητούμενα κενά διαδρομής. Οι δύο κύκλοι παραμένουν μερικοί. Αυτό δεν αποδεικνύει απουσία από κάθε άλλη ροή ή αντίγραφο του DVR.</p><p>Ελέγχθηκαν οπτικά 16 δείγματα από 4 αρχεία. Αποκωδικοποιήθηκαν όλα τα καρέ για έλεγχο αρχείων. Δεν έγινε εκπαίδευση.</p><a href="review.json">Πηγές, hashes, PTS και παρατηρήσεις</a>'
for r in records:
 page+='<h2>'+html.escape(Path(r['source']).name)+'</h2><p>'+html.escape(', '.join(s['visible_camera_clock'] for s in r['samples']))+'</p><img style="max-width:960px;width:100%" src="'+Path(r['sheet']).name+'">'
(audit/'review.html').write_text(page+'</body></html>',encoding='utf8')
p=out/'continuation_state.json';state=json.loads(p.read_text(encoding='utf8'));state['remote_export_audit']='outputs/tank_transfer_training_v1/dataset_v1/remote_export_audit/review.json';state['last_completed'].append('Two requested camera15 iVMS re-exports downloaded via AnyDesk; four MP4 files decoded and16 boundary/context samples visually checked. Neither bridges the requested6/15Oct trajectory gap. Existing partial labels and counts unchanged; separate provenance report saved.');state['updated_at']=report['updated_at'];p.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf8')
p=out/'review.html';page=p.read_text(encoding='utf8');page=page.replace('</html>','<section><h2>Νέες εξαγωγές iVMS</h2><a href="remote_export_audit/review.html">Έλεγχος των τεσσάρων MP4: τα δύο κενά παραμένουν ακάλυπτα</a></section></html>');p.write_text(page,encoding='utf8')
