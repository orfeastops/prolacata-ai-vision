"""User-confirmed arrival-counting scope, shared by report generators.

This is a specification, not a trained detector or implemented event counter.
"""
import json
import re
from pathlib import Path

CONTRACT = {
    'version': '2026-10-30-filling-to-storage-cycle-v2',
    'status': 'user_confirmed_requirements_not_implemented_counter',
    'objective': 'Maintain one record per new cheese production-load cycle: filling station in room11, loaded departure, entry into room15 with timestamp, scale handling, then storage placement that closes the cycle. Report daily arrivals and completed versus pending cycles separately.',
    'counted_event': 'One production load has one cycle_id and at most one counted room15 arrival. Retain its original entry timestamp when the cycle later closes at storage. Empty crossings never create a production count. Closing the cycle does not increment the arrival count again.',
    'color_policy': 'Tank detection and content assessment must cover all body colors and covers. Color alone must not determine eligibility or identity.',
    'camera_roles': {
        '11': 'Establish the load cycle at the two-worker filling station, follow the same tank through filling and loaded departure. Merely passing or waiting near the filling station does not establish a filled load.',
        '15': 'Primary evidence for the requested room15 entry event and its entry timestamp. Match with camera11 when available.'
    },
    'entry_rule': 'Associate a cheese-loaded departure from the two-worker filling station with the same load entering room15. Observe the doorway-to-interior transition and add at most one arrival to that cycle. Entry without sufficient content/origin evidence remains an unresolved candidate, not a confirmed production arrival.',
    'content_rule': 'Use visible load evidence and filling-origin history over multiple frames. Keep empty, scrap and unknown-content cases separate; a white top or lid alone does not prove a cheese production load.',
    'opening_inventory': 'Tanks already present when processing starts, whether loaded or empty, belong to opening inventory. Initialize the arrival count at zero and do not count their later internal movements.',
    'subsequent_states': {
        'scale': 'Track placement and handling at the scale and subsequent departure as part of this cycle. A visible scale visit is process evidence, not proof of a numeric weight or successful scale measurement.',
        'storage': 'After the scale visit, track placement in a storage position. This closes the visually observed filling-to-storage cycle; it does not create a second arrival. A cycle with missing scale/storage evidence stays pending or partially observed.',
        'departure_next_stage': 'Outside the closed counting cycle. Later movements retain the completed-cycle history and neither create a new production arrival nor subtract from the historical arrivals for that day.'
    },
    'cycle_states': [
        {'state':'filling_observed','evidence':'Same tank is being loaded with cheese at the two-worker filling station.','arrival_increment':0},
        {'state':'loaded_departure_11','evidence':'That loaded tank is collected and leaves room11.','arrival_increment':0},
        {'state':'entered_room15','evidence':'Matched production load crosses into room15. Store the entry timestamp once.','arrival_increment':'1 only if this cycle has no arrival record'},
        {'state':'scale_visit_observed','evidence':'Same load is placed/handled on the scale and subsequently removed.','arrival_increment':0},
        {'state':'stored_cycle_closed','evidence':'Same load is placed in storage after the scale visit. Preserve identity history.','arrival_increment':0}
    ],
    'excluded_from_new_production_arrivals': [
        'Existing loaded or empty room15 tanks',
        'Empty-tank deliveries and returns',
        'Scrap tanks',
        'Moves onto or off the scale after entry',
        'Moves between storage positions',
        'A previously counted load returning or reappearing',
        'Tracker ID changes, clip boundaries, reconnects and repeated export segments'
    ],
    'identity_policy': 'Use a persistent cycle_id for the production load, linked to temporary track IDs in both cameras. Repeated empty crossings contribute zero. A loaded tank exiting and re-entering with the same load retains its cycle and contributes no additional arrival. After storage, internal relocation cannot reopen a cycle. The same physical container can start a new cycle only when a demonstrably new filling operation occurs; uncertain reuse or identity remains a review case.',
    'count_commit_policy': 'Record an observed eligible entry once, with cycle_status in_progress. Close that same record at storage following the scale visit. Report completed_cycle_count and pending_cycle_count alongside arrival_count; never present a partial route as a completed filling-to-storage cycle.',
    'timestamp_policy': {
        'primary': 'Entry time in camera15, not camera11 exit time, scale time or storage time.',
        'definition': 'Store the earliest supported interior-entry timestamp after verifying the doorway-to-interior transition; retain the preceding/following frame bracket where exact crossing time is uncertain.',
        'local_day_timezone': 'Europe/Athens',
        'provenance': 'Store original camera clock, source video ID and PTS, calibrated clock offset where known, and timestamp uncertainty. Do not assume filename start plus PTS is a verified wall-clock time.',
        'day_boundary': 'Group by the local date of entry. Carry identity/event state across midnight; only the daily aggregation changes.'
    },
    'missing_footage': 'Do not invent missing cycle stages or join identity across recording gaps without evidence. Camera11 exit without camera15 entry stays pending with unknown entry time. Observed eligible entry without scale/storage coverage remains a recorded arrival with an incomplete cycle. Report missing-origin, missing-entry and missing-completion cases separately.',
    'required_report_fields': ['local_date','daily_confirmed_arrivals','completed_cycle_count','pending_cycle_count','pending_or_uncertain_arrivals','coverage_status','cycle_id','arrival_id','cycle_status','filling_origin_evidence','entry_time_camera15','entry_time_bracket','camera11_exit_time_if_observed','scale_visit_interval_if_observed','storage_time_if_observed','missing_stages','source_video_and_pts','evidence_clip','verification_status'],
    'historical_audit': 'The corrected45 on21/10 is an assistant visual count of camera11 exits. It must not be renamed as45 independently confirmed camera15 arrivals or model predictions.',
    'acceptance': 'Evaluate one-to-one room15 arrival-event precision/recall, false arrivals, missed arrivals, duplicate arrivals, timestamp error and false/missed cycle completions on held-out days. Include repeated empty crossings, the same loaded tank returning, and post-storage relocation as hard negative sequences. A matching daily total alone is insufficient.'
}

HTML = '''<!-- tank-arrival-contract:start -->
<section id="arrival-counting-rule"><h2>Τι ακριβώς θα μετρά το μοντέλο</h2>
<p><b>Ένας κύκλος γεμίσματος → μία εγγραφή: γέμισμα στην 11 → είσοδος στην 15 με ώρα → ζυγαριά → αποθήκευση και κλείσιμο κύκλου.</b></p>
<ul><li>Αναγνώριση δεξαμενών όλων των χρωμάτων, με έλεγχο του φορτίου και της προέλευσής τους.</li>
<li>Οι δεξαμενές που υπάρχουν ήδη στην 15 αποτελούν αρχικό απόθεμα και δεν προσμετρώνται στις νέες εισόδους.</li>
<li>Μια άδεια δεξαμενή μπορεί να μπαινοβγαίνει πολλές φορές: προσθέτει μηδέν στη μέτρηση παραγωγής.</li>
<li>Παρακολουθούμε τη δεξαμενή που γεμίζουν οι δύο εργαζόμενοι μέχρι την παραλαβή της και την είσοδο στην 15. Η ίδια δεξαμενή με το ίδιο φορτίο κρατά την ίδια εγγραφή σε τυχόν επιστροφή και επανείσοδο.</li>
<li>Καταγράφουμε μία φορά την ώρα εισόδου. Η ίδια εγγραφή ολοκληρώνεται όταν φαίνεται η συνέχεια ζυγαριά → αποθήκευση. Η ολοκλήρωση δεν προσθέτει δεύτερη είσοδο.</li>
<li>Μετά την αποθήκευση ο κύκλος έχει κλείσει. Οι επόμενες μετακινήσεις δεν τον ξανανοίγουν. Νέος κύκλος για το ίδιο δοχείο απαιτεί νέο γέμισμα.</li>
<li>Η ώρα αφορά την είσοδο που φαίνεται στην 15. Η κάμερα 11 βοηθά να επιβεβαιώσουμε ότι πρόκειται για φορτίο από τη θέση γεμίσματος.</li>
<li>Άδειες δεξαμενές, τρίμμα και επανεμφανίσεις ήδη καταμετρημένου φορτίου παραμένουν χωριστά.</li></ul>
<p>Η αναφορά ξεχωρίζει τις καταγεγραμμένες εισόδους, τους ολοκληρωμένους κύκλους και όσους παραμένουν σε εξέλιξη ή έχουν κενά εικόνας. Αν λείπει η εικόνα εισόδου στην 15, δεν επινοούμε ώρα. Αν λείπει ζυγαριά ή αποθήκευση, δεν δηλώνουμε ολοκληρωμένο κύκλο. Οι 45 της 21/10 παραμένουν οπτική καταμέτρηση εξόδων της 11.</p>
<p><a href="counting_contract.json">Αναλυτικοί κανόνες καταμέτρησης</a></p></section>
<!-- tank-arrival-contract:end -->'''

OLD_FLOW = 'Ανιχνευτής δεξαμενών YOLO → παρακολούθηση ByteTrack → καταγραφή της διαδρομής θέση γεμίσματος / πόρτα / έξοδος → αντιστοίχιση εισόδου στην 15 → στάση ζυγαριάς → αποθήκευση. Κάθε μεταφορά αποκτά μία εγγραφή, με ώρες και οπτικά τεκμήρια.'
PREVIOUS_FLOW = 'Ανιχνευτής δεξαμενών YOLO → παρακολούθηση ByteTrack → επιβεβαίωση προέλευσης από την 11 → μία καταγραφή κατά την είσοδο στην 15, με ώρα και αποδεικτικό απόσπασμα. Η ζυγαριά και η αποθήκευση μπορούν να προστεθούν ως μεταγενέστερες πληροφορίες της ίδιας καταγραφής.'
NEW_FLOW = 'Ανιχνευτής δεξαμενών YOLO → παρακολούθηση ByteTrack → αναγνώριση κύκλου γεμίσματος στην 11 → μία εγγραφή εισόδου στην 15 → ζυγαριά → αποθήκευση και κλείσιμο της ίδιας εγγραφής. Το ιστορικό κύκλου διατηρείται ώστε οι επανεμφανίσεις και οι εσωτερικές μετακινήσεις να μην προσθέτουν μετρήσεις.'

def update_protocol(plan):
    plan['objective'] = CONTRACT['objective']
    plan['counting_contract'] = CONTRACT
    baseline = plan['proposed_initial_baseline']
    baseline['count_logic'] = CONTRACT['entry_rule'] + ' ' + CONTRACT['identity_policy'] + ' ' + CONTRACT['count_commit_policy']
    baseline['load_state'] = CONTRACT['color_policy'] + ' ' + CONTRACT['content_rule']
    baseline['camera15'] = CONTRACT['camera_roles']['15'] + ' ' + CONTRACT['subsequent_states']['storage']
    baseline['gaps'] = CONTRACT['missing_footage']
    plan['evaluation']['primary'] = ['Room15 arrival-event precision','Room15 arrival-event recall','False arrivals','Missed arrivals','Duplicate arrivals','Daily arrival-count error','Entry timestamp error','Cross-camera association errors','False/missed cycle completions','Unknown/pending cycle rate','Runtime and latency']
    plan['labels']['sequence'] = 'Label the same production cycle across filling, loaded departure, room15 entry, scale visit and storage. Store cycle_id separately from temporary camera track IDs. Annotate missing/uncertain stages. Include repeated empty crossings, same-load re-entry, post-storage relocation and genuinely new filling of a reused tank. Opening inventory is not an arrival event.'
    plan['next_step'] = 'Build reviewed tank boxes across colors and filling-to-storage sequence labels on training days. Include repeated empty and same-load movements as hard negatives. Validate on17/10, freeze, then evaluate25/10 and28/10.'
    return plan

def update_html(page):
    page=page.replace(OLD_FLOW, NEW_FLOW).replace(PREVIOUS_FLOW, NEW_FLOW)
    if '<!-- tank-arrival-contract:start -->' in page:
        return re.sub(r'<!-- tank-arrival-contract:start -->.*?<!-- tank-arrival-contract:end -->',HTML,page,flags=re.S)
    return page.replace('<h2>Προτεινόμενη μέθοδος</h2>',HTML+'<h2>Προτεινόμενη μέθοδος</h2>')

def apply_contract(output):
    output=Path(output)
    protocol=output/'training_protocol.json'
    data=update_protocol(json.loads(protocol.read_text(encoding='utf-8')))
    protocol.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    (output/'counting_contract.json').write_text(json.dumps(CONTRACT,ensure_ascii=False,indent=2),encoding='utf-8')
    page=output/'inventory_review.html'
    if page.exists():page.write_text(update_html(page.read_text(encoding='utf-8')),encoding='utf-8')
    return data

if __name__=='__main__':
    data=apply_contract('outputs/tank_transfer_training_v1')
    assert data['split_policy']['locked_test_days']==['20261025','20261028']
    assert data['status']=='source_inventory_and_day_split_prepared_not_trained'
    page=Path('outputs/tank_transfer_training_v1/inventory_review.html').read_text(encoding='utf-8')
    assert page.count('id="arrival-counting-rule"')==1
    print(json.dumps({'status':'requirements_updated','objective':data['objective'],'training_started':False,'test_split_unchanged':True}))
