"""Reconcile existing reviewed evidence; does not add visual labels."""
import json, datetime, html, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/tank_transfer_training_v1/dataset_v1'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
labels=read(OUT/'reviewed_sequence_labels.json')
inv=read(OUT.parent/'archive_inventory.json')
reviews=read(OUT/'screening_source_reviews.json')
partials=[x for x in labels if x.get('date') in ['20261006','20261015'] and x.get('review_status')=='reviewed_partial_sequence']
cases=[]
for day,start,end,request,ids in [
 ('20261006','093555','093643','09:35:30–09:37:30',['20261006/blue_before_departure_0935','20261006/blue_arrival_followup_0936']),
 ('20261015','111546','111623','11:15:00–11:17:30',['20261015/scale_continuity_cam11_review','20261015/after_scale_gap_1116_review','20261015/storage_settle_1116_review'])]:
 rows=[r for r in inv['records'] if r['date']==day and r['camera']==15 and r['media_type']=='video']
 overlap=[r['member'] for r in rows if r['filename_start']<day+end and r['filename_end']>day+start]
 before=max((r for r in rows if r['filename_end']<=day+start),key=lambda r:r['filename_end'],default=None)
 after=min((r for r in rows if r['filename_start']>=day+end),key=lambda r:r['filename_start'],default=None)
 cases.append(dict(date=day,camera=15,filename_search_interval=[start,end],overlapping_video_members=overlap,previous_member=before['member'] if before else None,next_member=after['member'] if after else None,requested_continuous_export_clock=request,reviewed_evidence=[r for r in reviews if r['review_id'] in ids],conclusion='Existing visual reviews leave trajectory unresolved. Filename search only; not synchronization proof. Request additional continuous export if available; do not repeat same gap search without new evidence.'))
stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
audit=dict(updated_at=stamp,scope='Evidence-ledger and inventory audit only; no new pixels reviewed or accepted labels.',partial_count=len(partials),source_label_sha256=hashlib.sha256((OUT/'reviewed_sequence_labels.json').read_bytes()).hexdigest(),priority_cases=cases,partial_records=partials)
save(OUT/'cycle_gap_audit.json',audit)
esc=html.escape
page='<html lang="el"><meta charset="utf-8"><title>Κενά διαδρομών</title><style>body{font:16px/1.6 system-ui;max-width:1100px;margin:30px auto}article{border:1px solid #bbb;padding:18px;margin:15px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style><h1>Έλεγχος κενών διαδρομών — 6 και 15/10</h1><p>Διασταύρωση προηγούμενων οπτικών σημειώσεων με την απογραφή αρχείων. Δεν προστέθηκαν νέοι οπτικοί έλεγχοι ή πλήρεις κύκλοι. Οι χρόνοι αρχείων δεν αποδεικνύουν συγχρονισμό καμερών.</p>'
for c in cases:
 page+=f'<article><h2>{c["date"]} — κάμερα 15</h2><p>Πρόσθετη συνεχής εξαγωγή προς αναζήτηση: {c["requested_continuous_export_clock"]} (ένδειξη ρολογιού της κάμερας, όχι υπόθεση κοινού ρολογιού).</p><p>Αρχεία που επικαλύπτουν αυστηρά το εσωτερικό του διαστήματος αναζήτησης βάσει ονόματος: {len(c["overlapping_video_members"])}</p>'
 for r in c['reviewed_evidence']: page+=f'<h3>{esc(r["review_id"])}</h3><p>{esc(r["observation"])}</p>'
 page+='</article>'
page+=f'<p>Συνολικά {len(partials)} ελλιπείς εγγραφές στις δύο ημέρες. Οι υπάρχουσες αποφάσεις διατηρούνται αυτούσιες στο <a href="cycle_gap_audit.json">αρχείο τεκμηρίωσης</a>. <a href="review.html">Επιστροφή στην αναφορά</a>.</p></html>'
(OUT/'cycle_gap_audit.html').write_text(page,encoding='utf-8')
state=read(OUT/'continuation_state.json')
state['cycle_gap_audit']='outputs/tank_transfer_training_v1/dataset_v1/cycle_gap_audit.json'
state['priority_next']=['Read cycle_gap_audit.json first. Two priority gaps have existing reviewed boundary evidence; do not repeat the same search without additional media. Request continuous camera15 exports for6Oct09:35:30–09:37:30 and15Oct11:15:00–11:17:30 if available. Other partial trajectories remain queued; no new visual labels in this ledger audit.']+state['priority_next']
state['updated_at']=stamp
save(OUT/'continuation_state.json',state)
print(json.dumps({'partial_count':len(partials),'priority_cases':[{k:c[k] for k in ['date','overlapping_video_members','previous_member','next_member']} for c in cases]},indent=2))
