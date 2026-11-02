"""Assistant-authored visual audit, held-out test evidence, NOT training data.

Times below are approximate observed pickup / completed-deposit brackets.
These observations must not be represented as independently verified ground truth.
"""
import json
import hashlib
from html import escape
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/facility_dataset/temporal_pipeline/unseen_test_20260926/assistant_count_audit_20261029'
# group: tank, start, end, [(image side, pickup seconds, last placement seconds, quantity)]
GROUPS=[
('A01','A',45,57,[('L',46,49,2),('R',47,49,2),('L',50,52,2),('R',51,53,2),('L',53,57,2)]),
('A02','A',59,78,[('L',60,64,2),('R',61,65,2),('L',66,68,2),('R',70,73,2),('R',75,77,2)]),
('A03','A',79,90,[('L',80,83,2),('R',81,83,2),('L',83,86,2),('R',84,86,2),('L',86,90,2)]),
('A04','A',91,102,[('L',92,94,2),('R',93,96,2),('L',94,97,2),('L',98,100,2),('R',99,101,2)]),
('A05','A',106,117,[('L',107,110,2),('R',108,111,2),('L',110,113,2),('R',113,116,2),('L',115,117,2)]),
('A06','A',130,139,[('L',131,133,2),('R',131,133,2),('L',134,136,2),('R',135,138,2),('L',137,139,2)]),
('A07','A',147,156,[('R',148,150,2),('L',148,150,2),('R',150,153,2),('L',151,153,2),('L',153,156,2)]),
('A08','A',171,188,[('R',173,176,2),('R',178,181,2),('L',178,181,2),('L',181,183,2),('R',184,188,2)]),
('A09','A',201,214,[('L',202,205,2),('R',203,206,2),('L',205,207,2),('L',208,211,2),('R',212,214,2)]),
('A10','A',218,227,[('L',219,221,2),('R',219,222,2),('L',221,223,2),('R',223,225,2),('L',224,227,2)]),
('A11','A',229,242,[('L',230,232,2),('L',233,234,2),('R',234,236,2),('L',235.25,237.25,2),('R',239,241,1)]),
('A12','A',260,270,[('L',261,263,2),('R',262,265,2),('L',263,265,2),('L',266,269,2),('R',267,270,2)]),
('A13','A',278,284,[('L',279,281,2),('R',279,282,2),('L',282,284,2)]),
('B01','B',305,312,[('L',306,309,2),('R',309,312,2)]),
('B02','B',318,330,[('L',319,321,2),('R',319,321,2),('L',322,325,2),('R',323,326,2),('L',325,330,2)]),
('B03','B',359,371,[('L',360,363,2),('R',361,363,2),('L',363,366,2),('R',365,367,2),('L',367,371,2)]),
('B04','B',372,383,[('L',373,375,2),('R',373,376,2),('L',376,378,2),('R',378,380,2),('L',379,383,2)]),
('B05','B',391,407,[('L',392,395,2),('R',394,397,2),('L',397,399,2),('L',401,403,2),('R',403,407,2)]),
('B06','B',411,424,[('R',411,413,2),('L',414,416,2),('R',415,417,2),('L',417,420,2),('R',419,422,2)]),
('B07','B',428,438,[('L',429,431,2),('R',429,433,2),('L',432,434,2),('R',435,437,2),('L',435,438,2)]),
('B08','B',446,455,[('L',446,448,2),('R',447,449,2),('L',449,451,2),('R',451,453,2),('L',452,455,2)]),
('B09','B',460,469,[('L',460,462,2),('R',462,464,2),('L',463,465,2),('R',466,469,2),('L',466,468,2)]),
('B10','B',489,498,[('L',490,492,2),('R',490,492,2),('L',492,494,2),('R',493,495,2),('L',495,498,2)]),
('B11','B',508,517,[('L',509,511,2),('R',509,511,2),('L',511,513,2),('R',513,515,2),('L',514,516,2)]),
('B12','B',527,539,[('R',528,530,2),('L',528,531,2),('R',532,535,2),('L',532,534,2),('L',535,538,2)]),
('B13','B',548,558,[('R',549,551,2),('L',551,552,2),('L',552.5,554,2),('R',553,555.5,2),('L',556,557,2)]),
('B14','B',559,567,[('L',560,562,2),('R',560,562,2),('L',562,564,2),('R',563,565,2),('L',565,567,2)]),
('B15','B',569,578,[('L',569,571,2),('R',570,572,2),('L',571,573,2),('L',574,577,2),('R',575,577,2)]),
('B16','B',580,588,[('L',580,582,2),('R',580,583,2),('L',584,586,2),('R',586,588,2)]),
]

def main():
    groups=[]
    for gid,tank,start,end,events in GROUPS:
        groups.append(dict(group_id=gid,tank=tank,start_s=start,end_s=end,
            predicted_by_reviewer=sum(e[3] for e in events),events=[dict(side=e[0],
                pickup_approx_s=e[1],placement_completed_by_approx_s=e[2],quantity=e[3]) for e in events],
            evidence_pages=[f'sheets/page_{p:02d}.jpg' for p in range(int(start)//16,int(end)//16+1)]))
    evidence=json.loads((OUT/'evidence_index.json').read_text(encoding='utf-8'))
    totals={t:sum(g['predicted_by_reviewer'] for g in groups if g['tank']==t) for t in ['A','B']}
    model_path=ROOT/'outputs/facility_dataset/temporal_pipeline/placement_counter_v5/object_expansion/september_results.json'
    model_bytes=model_path.read_bytes()
    model=json.loads(model_bytes)
    comparison={t:dict(assistant_visual_estimate=totals[t],frozen_model_count=model['predicted_additions_by_tank'][t],
        model_minus_visual=model['predicted_additions_by_tank'][t]-totals[t]) for t in totals}
    report=dict(status='completed_visual_estimate_not_ground_truth',reviewer='assistant visual inspection',
        user_totals_received=False,reviewer_already_aware_of_model_totals=True,
        use_for_training=False,use_for_threshold_tuning=False,independent_ground_truth=False,
        source=evidence['source'],source_sha256=model['source_sha256'],
        time_basis='Elapsed video PTS seconds, not the camera wall clock. Event times are approximate brackets, not frame-exact release labels.',
        coverage_reviewed_through_s=evidence['rows'][-1]['time_s'],counts_complete=True,
        native_frames_decoded_for_extraction=evidence['native_frames'],extracted_crop_count=len(evidence['rows']),
        first_pass_reviewed_sheets=[f'sheets/page_{p:02d}.jpg' for p in range(51)],
        visual_estimate_by_tank=totals,comparison=comparison,
        model_results_path=str(model_path),model_results_sha256=hashlib.sha256(model_bytes).hexdigest(),
        checkpoint_sha256=model['checkpoint_sha256'],
        explicit_ambiguity_only_range_by_tank={'A':[totals['A']-1,totals['A']],'B':[totals['B'],totals['B']]},
        range_is_statistical_confidence_interval=False,
        groups=groups,uncertainties=[dict(group_id='A11',side='R',interval_s=[238,241],
            quantity_range=[0,1],provisional_quantity=1,
            reason='One small rectangular/broken piece is lifted from the tray and lowered into the production tank. Whole-block versus broken-piece counting definition needs validation. No forced tray size.')],
        specific_exclusions=[
            dict(interval_s=[171,176],side='L',reason='Rearranging existing tank contents; no new pickup.'),
            dict(interval_s=[230,232],side='R',reason='Material thrown toward the rear crumb tank, not the production tank.'),
            dict(interval_s=[583,584.6],side='R',quantity_observed=2,reason='Two rectangular pieces lifted from the tray and thrown into the rear crumb tank. Excluded from tank B.'),
            dict(interval_s=[588,802.21],reason='No further block additions observed; salting, sheets, waiting, tank removal, cleaning.')],
        notes=['Initial tank contents excluded.',
            'Groups and sides are bookkeeping only; no worker identities.',
            'Four remaining blocks on the shared tray are transferred into tank B after the tank exchange.',
            'Frames at 1 second were reviewed throughout, with 0.25/0.5 second detail for ambiguous intervals. This is not a claim to have visually viewed every native frame.',
            'Left worker at 171-176s rearranges existing tank contents, no new pickup.',
            'Salt, separator sheets, crumb collection, tray handling, and rearrangement excluded.',
            'Tank A removed around 290-295s; tank B put in position around 302-304s and removed around 726-730s. Assignment is visual/manual, not an automatic tank-change result.',
            'The 124-125 range for A describes one explicitly flagged piece only. It does not guarantee that the reviewer made no other counting mistakes.',
            'No fixed ten-block tray, two-block load, 38-block layer, or 228-block tank rule was used to fill missing observations.',
            'This source was inspected in earlier diagnostic work. This audit is not blinded: the reviewer already knew the frozen model totals.',
            'Aggregate count differences are not event recall, precision, or a validated accuracy percentage. User reference counts are still needed.'])
    (OUT/'visual_count_ledger.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    lines=['SEPTEMBER 26 TEST VIDEO: ASSISTANT VISUAL COUNT AUDIT',
        'Status: completed visual estimate; not independently verified ground truth.',
        f"Tank A: visual estimate {totals['A']} (124 plus one ambiguous small/broken piece); frozen model 58; model minus visual -67 (-66 if the piece is excluded).",
        f"Tank B: visual estimate {totals['B']}; frozen model 82; model minus visual {comparison['B']['model_minus_visual']}.",
        'Counts are additions during this video only. Initial contents are excluded.',
        'The reviewer knew the model totals; the user has not disclosed their reference totals.',
        'Inspected 51 contact sheets spanning the video at 1-second intervals, with 0.25/0.5-second detail for ambiguous movements.',
        'Extraction decoded all 11,995 native frames and saved 3,209 crops; this is not a claim that every native frame was visually reviewed.',
        'Elapsed video times are approximate; they are not the wall clock in the camera overlay.',
        'Important: at about 583-585s, two rectangular pieces go into the rear crumb tank, so they are excluded from B.',
        'Four blocks left on the tray at the tank exchange are counted only after they enter B.',
        'No training, threshold tuning, or modification of the model output occurred.',
        'The explicit ambiguity range is not a statistical confidence interval; other visual counting errors remain possible.',
        '', 'Group | tank | elapsed seconds | additions | cumulative tank additions']
    running={'A':0,'B':0}
    table=[]
    for g in groups:
        t=g['tank'];running[t]+=g['predicted_by_reviewer']
        lines.append(f"{g['group_id']} | {t} | {g['start_s']}-{g['end_s']} | {g['predicted_by_reviewer']} | {running[t]}")
        links=' '.join(f'<a href="{p}">{Path(p).stem}</a>' for p in g['evidence_pages'])
        events='; '.join(f"{e['side']}: {e['quantity']} blocks, {e['pickup_approx_s']} to {e['placement_completed_by_approx_s']}s" for e in g['events'])
        table.append(f"<tr><td>{g['group_id']}</td><td>{t}</td><td>{g['start_s']}-{g['end_s']}</td><td>{g['predicted_by_reviewer']}</td><td>{running[t]}</td><td>{links}<details><summary>Observed transfer brackets</summary>{escape(events)}</details></td></tr>")
    (OUT/'VISUAL_COUNT_REPORT.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    details=[('A11: small/broken piece; 0-1 ambiguity','detail_229_242_0.5_1.jpg'),
        ('B13: separate loads confirmed','detail_548_558_0.5_0.jpg'),
        ('B13: remaining loads','detail_548_558_0.5_1.jpg'),
        ('B16: two pieces go to the crumb tank, excluded','detail_580_588_0.5_0.jpg'),
        ('B16: final two blocks placed in B','detail_580_588_0.5_1.jpg')]
    html='<!doctype html><html lang="en"><meta charset="utf-8"><title>September 26 visual count audit</title><style>body{font:17px/1.5 system-ui;margin:36px auto;max-width:1200px;padding:0 20px;color:#172333;background:#f6f8fb}h1{font-size:28px}table{border-collapse:collapse;width:100%;background:white}td,th{border:1px solid #ccd4df;padding:9px;text-align:left}details{margin-top:8px}a{color:#065bad}img{max-width:100%;height:auto}aside{padding:18px;background:#fff3d4}pre{white-space:pre-wrap}</style><h1>September 26: assistant visual count audit</h1>'
    html+='<aside><strong>Visual estimate, pending reference counts.</strong> A: 124 + one ambiguous piece (provisional 125). B: 152. Frozen model: A 58, B 82. These are additions during the clip only. The reviewer already knew the model totals; this is not blinded ground truth.</aside>'
    html+='<p>All times are elapsed video seconds. No fixed tray size or tank capacity was used. Source frames have no model overlays. Labels are for test auditing only, not training or threshold tuning.</p><p><a href="VISUAL_COUNT_REPORT.txt">Method and summary</a> | <a href="visual_count_ledger.json">Full event ledger</a></p>'
    html+='<table><thead><tr><th>Group</th><th>Tank</th><th>Seconds</th><th>Added</th><th>Cumulative</th><th>Original-frame evidence</th></tr></thead><tbody>'+''.join(table)+'</tbody></table><h2>Detailed checks</h2>'
    for label,path in details:
        html+=f'<details><summary>{escape(label)}</summary><a href="{path}"><img loading="lazy" src="{path}" alt="{escape(label)}"></a></details>'
    html+='<p>The one-piece ambiguity does not rule out other reviewer errors. Aggregate differences cannot establish event detection precision or recall. Compare with the user\'s withheld A/B totals before treating any count as reference truth.</p></html>'
    (OUT/'review.html').write_text(html,encoding='utf-8')
    print(json.dumps(dict(totals=totals,comparison=comparison,groups=len(groups),events=sum(len(g['events']) for g in groups)),indent=2))
if __name__=='__main__':main()
