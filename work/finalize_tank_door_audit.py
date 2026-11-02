"""Publish the assistant's visual audit; never label motion proposals as model counts."""
import collections
import datetime as dt
import html
import json
import re
from pathlib import Path

ROOT = Path('outputs/tank_door_audit')
DESKTOP = Path('C:/Users/evant/Desktop/Facility_Camera_Videos')
DATES = ['20260926', '20261001', '20261003', '20261021']
DIRECT = {
    '20261001': {139, 203, 390, 437, 519},
    '20261003': {34},
    '20261021': {120, 131, 135, 182, 223, 234, 302, 366, 383, 390},
}
SUPPORT = {'20261001': {300, 410, 468, 511}, '20261003': {13}, '20261021': {128, 284}}
LABELS = {
    'direct_entry_observed': 'Φαίνεται η είσοδος στην 15',
    'post_entry_support': 'Εικόνα μετά την είσοδο · με κενό στη συνέχεια',
    'insufficient': 'Υπάρχει εικόνα, ανεπαρκής για ταύτιση',
    'no_overlap': 'Χωρίς καρέ στο χρονικό παράθυρο ελέγχου',
    'no_camera15': 'Δεν υπάρχει κάμερα 15 για αυτή την ημέρα',
}
NOTES15 = {
    '20261001_139': 'Door entry visible around 07:18:10–07:18:17.',
    '20261001_203': 'Entry 08:33:14–08:33:18; handling/covering follows.',
    '20261001_271': 'Tank waits in the doorway. Later camera15 frames show activity after 09:16:29, but do not independently establish the crossing or weighing.',
    '20261001_300': 'No tank at 09:58:18; tank present near scale area at 09:58:38. Recording gap prevents continuous identification.',
    '20261001_390': 'Entry around 11:48:56; handling/covering around 11:49:15.',
    '20261001_410': 'Tank already near scale area at 12:08:11, then moved at 12:08:32–36. Door entry is absent from selected footage.',
    '20261001_437': 'Door entry 12:48:04–12:48:12; handling follows.',
    '20261001_468': 'Before/after evidence around 13:23:25–13:23:46, with a recording gap.',
    '20261001_511': 'Repacked tank near scale area around 13:43:26–36 and relocation around 13:43:40–56. Not a new conveyor filling cycle.',
    '20261001_519': 'Entry 13:48:47–13:48:54; handling around 13:49:02–14.',
    '20261003_13': 'Before/after evidence at 08:00:10 and 08:00:23; crossing itself is not recorded.',
    '20261003_34': 'Entry around 08:26:11–20; covering/handling 08:26:24–41.',
    '20261021_120': 'Entry around 07:09:06–10; tank moves into room at 07:09:14–18.',
    '20261021_128': 'Tank already emerged at 07:17:24, pulled toward scale area at 07:17:28; crossing not continuously visible.',
    '20261021_131': 'Door arrival 07:25:20–24; handling through 07:25:36.',
    '20261021_135': 'Door arrival 07:32:44–48; movement into room 07:32:52–56.',
    '20261021_182': 'Loaded tank at door around 08:45:48–56; handling follows.',
    '20261021_223': 'Loaded tank at door 09:35:51, then by scale area 09:36:04–12.',
    '20261021_234': 'Loaded tank at door around 09:52:00–04.',
    '20261021_284': 'Tank already at scale area at 11:40:00; handling until 11:40:19, door crossing absent.',
    '20261021_302': 'Door entry 12:05:36–44; handling 12:05:48–12:06:00.',
    '20261021_366': 'Door arrival 12:52:35; tank moved inside by 12:52:49–53.',
    '20261021_383': 'New tank enters 13:26:35–43. Another previously covered tank is moved by forklift nearby; that movement is not counted again.',
    '20261021_390': 'New loaded tank enters 13:41:24–32 after a different covered tank is relocated.',
}

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def write(p, data):
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')

def rel(p):
    return p.relative_to(ROOT).as_posix()

# Preserve the recorded initial arrival separately from the final door clearance.
clocks = read(ROOT/'oct01_clock_notes.json')
clocks['271'] = '09:15:08-09:15:28'
write(ROOT/'oct01_clock_notes.json', clocks)

all_events, daily, revisions = [], [], []
for date in DATES:
    doc = read(ROOT/f'reviewed_{date}.json')
    if 'recheck_20261030' in doc:
        revisions.append(doc['recheck_20261030'])
    for number, e in enumerate(doc['events'], 1):
        pid = int(e['proposal_id'].rsplit('_', 1)[1])
        e['day_sequence'] = number
        e['count_basis'] = 'assistant_visual_review_not_automatic_model'
        e['note'] = e.get('note', '')
        e['extra_evidence'] = []
        if date == '20261001' and pid == 271:
            e['camera_clock_crossing_interval'] = '09:15:08-09:15:28'
            e['note'] = 'Arrives at door about 09:10:59 and waits there. Door clearance occurs between 09:15:08 and 09:15:28; counted once.'
            e['extra_evidence'] = ['event_review/20261001/271_range_206_490.jpg']
        if date == '20261021' and pid == 383:
            e['note'] = 'Tank first parked in front of the door at 13:25:23 (proposal 382), then exits. Counted once.'
            e['extra_evidence'] = ['event_review/20261021/382.jpg']
        if date == '20261021' and pid == 415:
            e['note'] = 'Proposals 415 and 416 describe the same exit; counted once.'
            e['extra_evidence'] = ['event_review/20261021/416.jpg']
        if (date, pid) in {('20260926', 195), ('20261001', 525), ('20261021', 423)}:
            last_note = 'Last tank contains whole cheese; capacity/fullness is not established.'
            e['note'] = e['note'].replace(last_note, '').strip() + ' ' + last_note
        e['extra_evidence'] = [p for p in e['extra_evidence'] if (ROOT/p).exists()]
        desktop_path = DESKTOP/doc['date']/'Camera_11'/e['basename']
        e['review_source'] = str(desktop_path if desktop_path.exists() else Path(e['source']))
        match_name = f'{pid:03}'
        match_dir = ROOT/'camera15_matches'/date
        if not (match_dir/f'{match_name}.json').exists() and (match_dir/f'{date}_{pid:03}.json').exists():
            match_name = f'{date}_{pid:03}'
        match_file = match_dir/f'{match_name}.json'
        frames = read(match_file) if match_file.exists() else []
        if date == '20260926':
            status = 'no_camera15'
        elif pid in DIRECT.get(date, set()):
            status = 'direct_entry_observed'
        elif pid in SUPPORT.get(date, set()):
            status = 'post_entry_support'
        elif frames:
            status = 'insufficient'
        else:
            status = 'no_overlap'
        e['camera15_match'] = status
        e['camera15_note'] = NOTES15.get(e['proposal_id'], '')
        e['camera15_evidence'] = [rel(p) for p in sorted(match_dir.glob(f'{match_name}_*.jpg'))]
        e['camera15_source_files'] = sorted({f['basename'] for f in frames})
        if date == '20261001' and pid == 271:
            e['camera15_evidence'] += [rel(p) for p in sorted(match_dir.glob('271_clearance_*.jpg'))]
        e['stages'] = {
            'camera11_exit': 'observed',
            'camera15_entry': status,
            'scale_dwell': 'not_verified_per_tank',
            'weighing_measurement': 'not_available',
            'final_storage_placement': 'not_verified_per_tank',
        }
        all_events.append(e)
    production = sum(e['load'] == 'production_cheese' for e in doc['events'])
    repacked = sum(e['load'] == 'repacked_cheese' for e in doc['events'])
    doc['observed_production_exits'] = production
    doc['observed_repacked_exits'] = repacked
    doc['observed_loaded_outbound'] = len(doc['events'])
    doc['scope'] = 'Preliminary assistant visual audit in supplied footage. Recording gaps and unvalidated candidate recall prevent a certified daily total. No independent accuracy estimate.'
    doc['method'] = 'Camera11 sampling every 2 seconds, color/motion proposals and chronological visual review; camera15 selected 4-second samples for cross-camera evidence. This is not a trained tank counter.'
    write(ROOT/f'reviewed_{date}.json', doc)
    daily.append(dict(date=doc['date'], production=production, repacked=repacked,
                      total_observed=len(doc['events']),
                      camera15_status_counts=dict(collections.Counter(e['camera15_match'] for e in doc['events']))))

# Filename time ranges describe supplied exports, not continuous decoded recording.
inventory = read(Path('outputs/camera_video_collection/inventory.json'))['records']
coverage = []
groups = collections.defaultdict(list)
for item in inventory:
    m = re.search(r'_(\d{14})_(\d{14})_', item['basename'])
    if m:
        groups[(item['date'], item['camera'])].append(tuple(dt.datetime.strptime(x, '%Y%m%d%H%M%S') for x in m.groups()))
for (date, camera), intervals in sorted(groups.items()):
    merged = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(end, merged[-1][1])
        else:
            merged.append([start, end])
    coverage.append(dict(date=dt.datetime.strptime(date, '%Y%m%d').date().isoformat(), camera=camera,
                         files=len(intervals), first=str(merged[0][0].time()), last=str(merged[-1][1].time()),
                         filename_union_hours=round(sum((b-a).total_seconds() for a,b in merged)/3600, 3),
                         disjoint_ranges=len(merged),
                         limitation='Filename ranges only; not proof of continuous video frames or all-day recording.'))

report = dict(
    type='assistant_visual_baseline', daily=daily, coverage=coverage, events=all_events, revisions=revisions,
    process_from_user=['Filled tank leaves camera11', 'Same tank arrives in camera15 and is prepared/weighed', 'Same tank leaves scale and is stored'],
    counting_rule='One event per outbound filled-station tank. Scale handling and storage are later states of the same tank, not additional production. Empty returns, scrap tanks and moves of previously counted tanks are excluded. Repacked cheese is separate.',
    limitations=['No trained tank model or accuracy estimate in this audit.', 'Gaps may conceal exits or the camera15 continuation.', 'Whiteness or a cover alone does not establish full cheese content.', 'Scale dwell, numeric weight and final storage are not verified for every tank.', 'Clock intervals are visual brackets, not frame-exact timestamps; cross-camera clocks have not been calibrated.'],
    excluded_examples=[
        dict(date='2026-09-26', proposals=[95,202,214], reason='95 already beyond door; 202/214 same scrap tank'),
        dict(date='2026-10-01', proposals=[470,531,538], reason='470 prior covered tank returning; 531/538 scrap tank'),
        dict(date='2026-10-03', proposals=[92], reason='Scrap tank'),
        dict(date='2026-10-21', proposals=[380,384,416,425,430,434], reason='380/384 previously counted tank relocated; 416 same as415; 425 same as423; 430/434 scrap tank')])
write(ROOT/'tank_transfer_audit.json', report)

esc = lambda s: html.escape(str(s), quote=True)
parts = ['''<!doctype html><html lang="el"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Δεξαμενές · Κάμερα 11 → 15</title>
<style>body{margin:0;background:#f4f6f8;color:#172a3b;font:16px/1.55 system-ui,sans-serif}main{max-width:1250px;margin:auto;padding:32px}h1{font-size:32px;margin-bottom:8px}h2{margin-top:38px}p{max-width:1000px}.callout{background:#fff3d5;border-left:5px solid #c38c20;padding:15px 20px}.flow{padding:18px;background:#dfeef0;border-radius:10px}table{border-collapse:collapse;width:100%;background:white;margin:18px 0}th,td{padding:12px;text-align:left;border-bottom:1px solid #dce4e8}th{background:#e9f0f3}details{background:white;border:1px solid #dbe3e8;border-radius:8px;margin:12px 0;padding:14px}summary{cursor:pointer;font-weight:650}img{width:100%;height:auto;margin:12px 0}.tag{display:inline-block;border-radius:6px;background:#edf2f5;padding:3px 8px;font-size:13px}.direct_entry_observed{background:#d7ecdf}.post_entry_support{background:#fff0c7}a{color:#006489}small{color:#526979}select{font:inherit;padding:8px;margin-left:8px}.muted{color:#526979}code{overflow-wrap:anywhere}footer{margin:36px 0;font-size:14px;color:#526979}@media(max-width:650px){main{padding:16px}table{font-size:13px}th,td{padding:6px}}</style>
<main><h1>Δεξαμενές από την 11 προς την 15</h1><p>Πρώτη οπτική καταγραφή των διελεύσεων στα διαθέσιμα βίντεο. Κάθε εγγραφή έχει ώρα κάμερας, αρχείο πηγής και διαδοχικά καρέ για έλεγχο.</p>
<p class="flow"><b>Μία δεξαμενή, τρία στάδια:</b> έξοδος από την 11 / είσοδος στην 15 → προετοιμασία και ζυγαριά → θέση στο ωριμαντήριο. Μετριέται μία φορά.</p>
<div class="callout"><b>Οι αριθμοί είναι προκαταρκτική οπτική καταμέτρηση του βοηθού, όχι αποτέλεσμα εκπαιδευμένου μοντέλου.</b> Τα εξαγόμενα βίντεο έχουν κενά. Η ανίχνευση υποψηφίων δεν έχει ανεξάρτητο έλεγχο πληρότητας. Δεν τεκμηριώνεται πλήρες σύνολο ημέρας ή ποσοστό ακρίβειας. Η ζύγιση και η τελική αποθήκευση δεν έχουν επιβεβαιωθεί ξεχωριστά για κάθε εγγραφή.</div>
<h2>Διελεύσεις που εντοπίστηκαν</h2><table><tr><th>Ημέρα</th><th>Από θέση γεμίσματος</th><th>Επιπλέον επανατοποθέτηση φέτας</th><th>Είσοδος ορατή και στην 15</th></tr>''']
for d in daily:
    parts.append(f"<tr><td>{esc(d['date'])}</td><td><b>{d['production']}</b></td><td>{d['repacked']}</td><td>{d['camera15_status_counts'].get('direct_entry_observed',0)} / {d['total_observed']}</td></tr>")
parts.append('''</table><p>Η τελευταία στήλη αφορά τη διαθέσιμη οπτική διασταύρωση, <b>όχι την ακρίβεια μοντέλου</b>. Στις 26/9 δεν υπάρχει υλικό της 15. Στις 3/10 η 11 φτάνει μόνο έως 09:50. Στις 1/10, μία επιπλέον έξοδος αφορά φέτα που μεταφέρθηκε σε άλλη δεξαμενή μέσα στο δωμάτιο· παραμένει χωριστή από τους νέους κύκλους γεμίσματος. Οι τελευταίες δεξαμενές μπορεί να έχουν μερικό φορτίο.</p>
<h2>Υλικό ανά ημέρα και κάμερα</h2><table><tr><th>Ημέρα</th><th>Κάμερα</th><th>Αρχεία</th><th>Από–έως, ονόματα εξαγωγών</th><th>Ώρες ένωσης διαστημάτων</th></tr>''')
for c in coverage:
    parts.append(f"<tr><td>{c['date']}</td><td>{c['camera']}</td><td>{c['files']}</td><td>{c['first']}–{c['last']}</td><td>{c['filename_union_hours']:.2f}</td></tr>")
parts.append('''</table><p class="muted">Τα παραπάνω είναι διαστήματα από τα ονόματα αρχείων, όχι συνεχής κάλυψη. Στον συγκεκριμένο φάκελο δεν βρέθηκαν οι 6, 8, 10, 13, 15 και 17/10. Στις 5/10 και 22/10 υπάρχει μόνο κάμερα 15, οπότε δεν βγαίνει από αυτήν τη μέθοδο αριθμός εξόδων από την 11.</p>
<h2>Αναλυτικός έλεγχος</h2><label>Ημέρα<select id="date"><option value="all">Όλες</option>''')
for date in DATES:
    parts.append(f'<option value="{date}">{date[6:8]}/{date[4:6]}/{date[:4]}</option>')
parts.append('</select></label><p class="muted">Οι ώρες είναι διαστήματα παρατήρησης στο ρολόι της κάμερας. Τα καρέ της 15 αναζητήθηκαν σε κοντινό χρονικό παράθυρο· η απουσία τους δεν αποδεικνύει ότι δεν μπήκε η δεξαμενή. Η ημερήσια αρίθμηση περιλαμβάνει και τη μία χωριστή μεταφορά επανατοποθετημένης φέτας.</p>')
for e in all_events:
    date = e['proposal_id'].split('_')[0]
    category = ' · επανατοποθετημένη φέτα' if e['load'] == 'repacked_cheese' else ''
    source = Path(e['review_source']).resolve().as_uri()
    parts.append(f'<details id="{e["proposal_id"]}" data-date="{date}"><summary>{date[6:8]}/{date[4:6]} · #{e["day_sequence"]:02} · {esc(e["camera_clock_crossing_interval"])}{category} <span class="tag {e["camera15_match"]}">{LABELS[e["camera15_match"]]}</span></summary>')
    parts.append(f'<p><a href="{esc(source)}#t={max(0,e["candidate_start"]-15):.1f}">Άνοιγμα αρχικού βίντεο</a> · σημείο υποψηφίου περίπου {e["candidate_start"]:.1f} δευτ. του αρχείου</p><small>{esc(e["basename"])}</small>')
    if e['note']:
        parts.append(f'<p>Σημείωση ελέγχου: {esc(e["note"])}</p>')
    if e.get('evidence_video'):
        parts.append(f'<p><b>Προσθήκη στον επανέλεγχο 30/10:</b> αυτή η έξοδος είχε παραλειφθεί στην πρώτη καταγραφή. Το σύνολο της 21/10 διορθώθηκε από 44 σε 45.</p><video controls preload="none" style="width:100%" src="{esc(e["evidence_video"])}"></video><p><a href="{esc(e["evidence_video"])}">Άνοιγμα αποσπάσματος 80 δευτερολέπτων</a></p>')
    parts.append(f'<h3>Κάμερα 11 · διαδοχικά καρέ</h3><img loading="lazy" src="{esc(e["evidence_sheet"])}" alt="Διέλευση {e["proposal_id"]}">')
    for p in e['extra_evidence']:
        parts.append(f'<img loading="lazy" src="{esc(p)}" alt="Επιπλέον χρονική συνέχεια">')
    if e['camera15_evidence']:
        parts.append(f'<details><summary>Κάμερα 15 · υλικό διασταύρωσης</summary><p>{LABELS[e["camera15_match"]]}</p><p>{esc(e["camera15_note"])}</p>')
        for p in e['camera15_evidence']:
            parts.append(f'<img loading="lazy" src="{esc(p)}" alt="Καρέ κάμερας 15 για {e["proposal_id"]}">')
        parts.append('</details>')
    parts.append('<p class="muted">Ζυγαριά: δεν έχει επιβεβαιωθεί ανά δεξαμενή · Τελική θέση αποθήκευσης: δεν έχει επιβεβαιωθεί ανά δεξαμενή · Κιλά: δεν διατίθενται.</p></details>')
parts.append('''<footer>Μέθοδος: δειγματοληψία 2 δευτ. στην 11, υποψήφια κίνηση στην πόρτα και οπτικός έλεγχος διαδοχικών καρέ. Διασταύρωση επιλεγμένων καρέ ανά 4 δευτ. στην 15. Άδειες επιστροφές, δεξαμενές τριμμάτων και επαναμετακινήσεις ήδη μετρημένης δεξαμενής εξαιρέθηκαν. Δεν έγινε εκπαίδευση μοντέλου.<p><a href="tank_transfer_audit.json">Πλήρες αρχείο δεδομένων JSON</a></p></footer></main><script>document.getElementById('date').onchange=function(){document.querySelectorAll('[data-date]').forEach(e=>{e.hidden=this.value!=='all'&&e.dataset.date!==this.value})}</script></html>''')
report_html=''.join(parts)
if revisions:
    report_html=report_html.replace('<h2>Διελεύσεις που εντοπίστηκαν</h2>', '<p class="flow"><b>Διόρθωση 30/10: 45 έξοδοι στις 21/10.</b> Βρέθηκε η παραλειφθείσα μεταφορά στις 10:51:10–10:51:16. <a href="recheck_20261030/extra_exit_105110.mp4">Δείτε το συγκεκριμένο απόσπασμα</a>. Η αρχική καταγραφή των 44 διατηρήθηκε για το ιστορικό ελέγχου.</p><h2>Διελεύσεις που εντοπίστηκαν</h2>')
(ROOT/'review.html').write_text(report_html, encoding='utf-8')

# Validate the deliverable's linked evidence, event IDs and computed totals.
assert len({e['proposal_id'] for e in all_events}) == len(all_events)
missing = []
for e in all_events:
    for p in [e['evidence_sheet'], *e['extra_evidence'], *e['camera15_evidence']]:
        if not (ROOT/p).is_file(): missing.append(p)
    if not Path(e['review_source']).is_file(): missing.append(e['review_source'])
    if e.get('evidence_video') and not (ROOT/e['evidence_video']).is_file():
        missing.append(e['evidence_video'])
    if e['camera15_match'] in {'direct_entry_observed', 'post_entry_support'}:
        assert e['camera15_evidence'], e['proposal_id']
assert not missing, missing
write(ROOT/'report_verification.json', dict(event_records=len(all_events), linked_evidence_exists=True, daily=daily))
print(json.dumps({'events': len(all_events), 'daily': daily, 'report': str((ROOT/'review.html').resolve())}, ensure_ascii=False))
