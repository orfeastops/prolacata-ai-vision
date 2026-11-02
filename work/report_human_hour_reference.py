import json
from pathlib import Path
b=Path('D:/Codex/tank-storage')
u=json.loads((b/'human_annotations/reviewed_submission_01.json').read_text(encoding='utf-8'))
s=b/'evaluation_summary.json';d=json.loads(s.read_text(encoding='utf-8'))
d['human_hour_reference']={
    'received':True,'submitted_events':len(u['events']),
    'user_storage_annotations':sum(e['kind']=='storage' for e in u['events']),
    'user_uncertain_annotations':sum(e['kind']=='uncertain' for e in u['events']),
    'coverage_flags_present':list(u['coverage']),
    'coverage_flags_missing':[f'clip_{i:03d}' for i in range(58,65) if f'clip_{i:03d}' not in u['coverage']],
    'reviewed_copy':'human_annotations/reviewed_submission_01.json',
    'additional_sampled_reference':'human_annotations/supplemental_0932_review.json',
    'reconciled_count':None,'final_metrics':None}
s.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
p=b/'review.html';h=p.read_text(encoding='utf-8');marker='<!-- human-hour-reference -->'
section=marker+'''<section><h2>Σημειώσεις χρήστη για την ώρα</h2><p>Παραλήφθηκαν 7 σημειώσεις: 5 ως αποθηκεύσεις και 2 αβέβαιες. Δηλώθηκαν πλήρως ελεγμένα τα 058–062· τα 063–064 δεν έχουν αντίστοιχη δήλωση. Η ώρα21:23:09 επιβεβαιώθηκε οπτικά ως09:23:09 σε χωριστό αντίγραφο.</p><p>Η επιπλέον έξοδος περίπου09:32 συνδέθηκε δειγματοληπτικά με προηγούμενο γέμισμα, με δηλωμένο κενό ορίου αρχείων. Δεν προστέθηκε στις αρχικές σημειώσεις του χρήστη. Δεν υπάρχει ακόμη τελικό συμφιλιωμένο πλήθος ή ποσοστό επιτυχίας της ώρας.</p><p><a href="human_annotations/reviewed_submission_01.json">Σημειώσεις και εκκρεμότητες</a></p></section>'''
if marker not in h:p.write_text(h.replace('</html>',section+'</html>'),encoding='utf-8')
print('Report updated; no final count inferred.')
