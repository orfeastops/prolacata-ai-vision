"""Render the current curation ledger without hard-coded progress claims."""
import html
import json
import os
from pathlib import Path


def render_review(root, out, quality, records, sequence_labels, source_reviews):
    esc = html.escape
    rel = lambda p: Path(os.path.relpath(p, out)).as_posix()
    link = lambda p, title: f'<a href="{esc(rel(root/p))}">{esc(title)}</a>'
    def stage_clock(stage):
        interval = stage.get('visible_camera_clock_interval')
        if interval:
            return ' - '.join(interval)
        if stage.get('arrival_observed_by'):
            return 'Arrival visible by ' + stage['arrival_observed_by'] + '; threshold crossing not sampled'
        return 'Exact clock interval not established'

    q = quality
    page = '''<!doctype html><html lang="el"><meta charset="utf-8">
<title>Dataset μεταφορών δεξαμενών — οπτικός έλεγχος</title>
<style>body{font:16px/1.6 system-ui;max-width:1250px;margin:auto;padding:24px;background:#f1f4f7;color:#183044}section,article{background:white;padding:18px;border-radius:10px;margin:15px 0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:16px}img{max-width:100%;max-height:440px}.status{background:#fff0bf;padding:16px}a{color:#00678d}details{overflow-wrap:anywhere}table{border-collapse:collapse;width:100%}td,th{padding:8px;text-align:left;border-bottom:1px solid #ddd}code{overflow-wrap:anywhere}small{color:#536575}</style>
<h1>Dataset μεταφορών δεξαμενών</h1>
<p class="status"><b>Η σημείωση συνεχίζεται. Το dataset δεν έχει ακόμη ολοκληρωθεί και η εκπαίδευση δεν έχει ξεκινήσει.</b> Οι παρακάτω αριθμοί αφορούν έλεγχο δεδομένων, όχι ακρίβεια μοντέλου.</p>'''
    page += f'''<section><h2>Τεκμηριωμένη πρόοδος</h2><table>
<tr><th>Έλεγχος</th><th>Πλήθος</th></tr>
<tr><td>Υποψήφιες εικόνες</td><td>{q['candidate_images']}</td></tr>
<tr><td>Εικόνες με ελεγμένα κουτιά στην επιλεγμένη περιοχή</td><td>{q['accepted_images']}</td></tr>
<tr><td>Ολοκληρωμένοι κύκλοι με ελεγμένα στάδια</td><td>{q['accepted_complete_cycles']}</td></tr>
<tr><td>Αρνητικές ακολουθίες συγκεκριμένου αντικειμένου</td><td>{q['accepted_negative_sequences']}</td></tr>
<tr><td>Χωριστές ελλιπείς ακολουθίες</td><td>{q.get('reviewed_partial_sequences',0)}</td></tr>
<tr><td>Προβολές χρονικών δειγμάτων που εξετάστηκαν</td><td>{q['reviewed_temporal_sample_presentations']} από {q['reviewed_source_video_count']} βίντεο</td></tr></table>
<p>Τα χρονικά δείγματα περιέχουν και επικαλυπτόμενα παράθυρα. Δεν είναι ισάριθμες ανεξάρτητες εικόνες εκπαίδευσης ούτε σημαίνουν ότι ελέγχθηκε κάθε φυσικό καρέ.</p>
<p>Εκπαίδευση: 5, 6, 8, 10, 13, 15, 21, 23/10. Validation: 17/10. Οι 25 και 28/10 παραμένουν κλειδωμένες, χωρίς οπτική επιθεώρηση.</p>
<p>Απομένουν περισσότερες διαφορετικές μεταφορές, άδειες διελεύσεις, επιστροφές του ίδιου φορτίου, μετακινήσεις μετά την αποθήκευση και ακολουθίες ελέγχου της 17/10.</p>
<p><a href="quality_report.json">Έλεγχοι ποιότητας</a> · <a href="annotation_protocol.json">Πρωτόκολλο</a> · <a href="continuation_state.json">Συνέχεια εργασίας</a></p></section>
<section><h2>Κανόνας καταμέτρησης</h2><p>Γέμισμα στην 11 → έξοδος → μία νέα είσοδος στην 15 → επίσκεψη στη ζυγαριά → αποθήκευση. Η μετακίνηση από τη ζυγαριά στη θέση αποθήκευσης δεν είναι δεύτερη είσοδος. Αρχικό απόθεμα, άδειες δεξαμενές και επαναμετακινήσεις καταγράφονται χωριστά.</p>
<p>Το λευκό κάλυμμα μόνο του δεν αποδεικνύει φέτα. Η επίσκεψη στη ζυγαριά δεν αποδεικνύει βάρος σε κιλά. Οι ώρες των αρχείων και τα PTS δεν χρησιμοποιούνται ως απόδειξη συγχρονισμού.</p></section>'''
    page += '<section><h2>Ελεγμένες ακολουθίες και πηγές</h2><p><a href="reviewed_sequence_labels.json">Πλήρης αναλυτική σημείωση</a> · <a href="screening_source_reviews.json">Οπτικές παρατηρήσεις ανά πηγή</a></p>'
    status_names = {'accepted_complete_cycle':'Ολοκληρωμένος κύκλος με ελεγμένα στάδια',
                    'accepted_negative_sequence':'Αρνητικό παράδειγμα συγκεκριμένης διαδρομής',
                    'reviewed_partial_sequence':'Ελλιπής ακολουθία — χωρίς συνολικό στόχο καταμέτρησης'}
    page += '<h3>Διαχωρισμός εκπαίδευσης και επικύρωσης</h3><table><tr><th>Σύνολο</th><th>Πλήρεις κύκλοι</th><th>Αρνητικές ακολουθίες</th><th>Ελλιπείς ακολουθίες</th></tr>'
    for split, counts in q.get('sequence_counts_by_split',{}).items():
        title = 'Εκπαίδευση' if split=='train' else 'Επικύρωση — 17/10, εκτός εκπαίδευσης'
        page += f'<tr><td>{title}</td><td>{counts.get("accepted_complete_cycle",0)}</td><td>{counts.get("accepted_negative_sequence",0)}</td><td>{counts.get("reviewed_partial_sequence",0)}</td></tr>'
    page += '</table>'
    status_names['reviewed_context_existing_cycle'] = 'Συνδεδεμένο πλαίσιο υπάρχοντος κύκλου — χωρίς πρόσθετη μέτρηση'
    for s in sequence_labels:
        page += f'<article><h3>{esc(s["sequence_id"])}</h3><b>{esc(status_names.get(s["review_status"],s["review_status"]))}</b>'
        page += f'<p><b>Partition: {esc(s["split"])}</b></p>'
        if s.get('linked_cycle_id'):
            page += f'<p>Συνδέθηκε στον ήδη καταγραμμένο κύκλο <b>{esc(s["linked_cycle_id"])}</b>. Αυτό το απόσπασμα δεν έχει ξεχωριστό στόχο καταμέτρησης.</p>'
        if s.get('cycle_id'):
            interval = s.get('entry_clock_interval') or []
            page += f'<p>Στόχος: <b>{s["production_entry_count_target"]} νέα είσοδος</b>. Ώρα στην κάμερα 15: <b>{esc(" – ".join(interval))}</b>. Η χρονική αβεβαιότητα παραμένει ρητή.</p>'
            page += '<table><tr><th>Στάδιο</th><th>Ορατή ώρα κάμερας</th><th>Τεκμήρια</th></tr>'
            for st in s['stages']:
                refs = [link(e['frames_manifest'],f'Κάμερα {e["camera"]} / PTS {e["relative_pts_interval"][0]}–{e["relative_pts_interval"][1]}') for e in st['evidence']]
                page += f'<tr><td>{esc(st["stage"])}</td><td>{esc(stage_clock(st))}</td><td>{"<br>".join(refs)}</td></tr>'
            page += '</table><p><b>Περιορισμοί:</b></p><ul>' + ''.join(f'<li>{esc(x)}</li>' for x in s.get('limitations',[])) + '</ul>'
        else:
            page += f'<p>{esc(s.get("observation",""))}</p><p>{esc(s.get("label_scope",s.get("partial_reason","")))}</p>'
            if s.get('stages'):
                page += '<table><tr><th>Τεκμηριωμένο στάδιο</th><th>Ώρα της αντίστοιχης κάμερας</th><th>Πηγή</th></tr>'
                for st in s['stages']:
                    refs = [link(e['frames_manifest'],f'Camera {e["camera"]} / PTS {e["relative_pts_interval"][0]}–{e["relative_pts_interval"][1]}') for e in st['evidence']]
                    page += f'<tr><td>{esc(st["stage"])}</td><td>{esc(stage_clock(st))}</td><td>{"<br>".join(refs)}</td></tr>'
                page += '</table><p><b>Μερική διαδρομή: δεν προσμετράται στους ολοκληρωμένους κύκλους του dataset.</b></p>'
            if s.get('tracked_object_count'):
                page += f'<p>Δεξαμενές στη συγκεκριμένη αρνητική ακολουθία: {s["tracked_object_count"]}. Νέες παραγωγικές είσοδοι: {s["production_entry_count_target"]}.</p>'
            if s.get('unlinked_followup'):
                follow = s['unlinked_followup']
                page += f'<details><summary>Μεταγενέστερη κίνηση χωρίς επιβεβαιωμένη αντιστοίχιση</summary><p>{esc(follow["observation"])}</p>'
                for e in follow['evidence']:
                    page += '<p>'+link(e['frames_manifest'],'Πηγή προς περαιτέρω έλεγχο')+'</p>'
                page += '</details>'
            for e in s.get('evidence',[]):
                page += '<p>'+link(e['frames_manifest'],'Πηγή και χρονικά δείγματα')+'</p>'
        page += '<small>Η αποδοχή της σημείωσης δεν αποτελεί έγκριση εκπαίδευσης ή ολοκλήρωση ολόκληρου του dataset.</small></article>'
    page += '</section>'
    storage = out/'sequence_review/20261013/storage_boundary_review/sheet_006.jpg'
    if storage.exists():
        page += f'<section><h2>Τεκμήριο αποθήκευσης 13/10</h2><p>Η μπεζ δεξαμενή παραμένει στη θέση της και απομακρύνεται το χειροκίνητο παλετοφόρο.</p><a href="{rel(storage)}"><img src="{rel(storage)}" loading="lazy"></a></section>'
    page += '<section><h2>Ιστορικό οπτικού ελέγχου</h2>'
    for review in source_reviews:
        page += f'<details><summary>{esc(review["review_id"])} — Κάμερα {review["camera"]}, {review["sampled_frames_visually_reviewed"]} δείγματα</summary><p>{esc(review["observation"])}</p>'
        for sh in review['reviewed_sheets']:
            page += f'<a href="{rel(root/sh)}"><img loading="lazy" src="{rel(root/sh)}"></a>'
        page += '</details>'
    page += '</section><section><h2>Έλεγχος κουτιών αντικειμένων</h2><p>Διορθώθηκαν παραλείψεις σε δεξαμενές που φαίνονται μέσα από την πόρτα. Η παρουσία κουτιού δεν είναι γεγονός εισόδου. Οι προηγούμενες αποφάσεις και οι διορθώσεις διατηρούνται.</p><p><a href="object_review_decisions.json">Αποφάσεις ελέγχου και ιστορικό</a> · <a href="image_annotations_draft.json">Κουτιά και προέλευση</a></p>'
    sheet_manifest=root/'outputs/tank_transfer_training_v1/detector_v1/overlay_sheet_manifest.json'
    current_sheets=([root/p for p in json.loads(sheet_manifest.read_text('utf8'))['sheets']] if sheet_manifest.exists() else sorted((root/'outputs/tank_transfer_training_v1/detector_v1/sheets').glob('labels_*.jpg')))
    for sh in current_sheets:
        page += f'<a href="{rel(sh)}"><img src="{rel(sh)}" loading="lazy"></a>'
    page += '</section><h2>Υποψήφιες εικόνες</h2><div class="grid">'
    for r in records:
        frozen=r.get('object_review',{}).get('frozen_overlay')
        if frozen:
            page += '<p>'+link(frozen['image'],'ROI '+r['id']+' / approved overlay')+'</p>'
        if r.get('exclusion_review'):
            page += f'<p><b>ROI {esc(r["id"])}:</b> {esc(r["exclusion_review"]["reason"])}</p>'
        page += f'<article><b>{esc(r["id"])} — {r["date"]} — Camera {r["camera"]} — {esc(r["split"])}</b><p>{esc(r["annotation_status"])}</p><img src="{rel(root/r["image"])}" loading="lazy"><details><summary>Προέλευση</summary>{esc(r["source"])}</details></article>'
    if (out/'cycle_gap_audit.html').exists():
        page += '<section><h2>Κενά διαδρομών 6 και 15/10</h2><p><a href="cycle_gap_audit.html">Συγκεκριμένα κενά, προηγούμενα τεκμήρια και πρόσθετα αρχεία προς αναζήτηση</a></p></section>'
    if (out/'remote_export_audit/review.html').exists():
        page += '<section><h2>Νέες εξαγωγές iVMS</h2><a href="remote_export_audit/review.html">Έλεγχος τεσσάρων MP4: τα δύο κενά παραμένουν ακάλυπτα</a></section>'
    page += '</div></html>'
    (out/'review.html').write_text(page,encoding='utf8')
