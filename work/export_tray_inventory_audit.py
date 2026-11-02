"""Export authored visual observations, explicitly separate from model results.

Numbers below were proposed by the assistant after inspecting source evidence.
This script formats those observations; it does not infer cheese counts.
"""
import json,html
from datetime import datetime,timezone
from build_tray_inventory_audit import OUT
from tray_audit_selection import SELECTION

# Initial quantity proposals refer to the entire tray's entry sequence, not
# necessarily a single image: the near row often begins below the image edge.
# Every proposal is explicitly unverified, and the irregular stack is masked.
OBSERVATIONS={
 'T01':(10,[4,14], 'White tray. Repeated paired removals expose low white bases; the outgoing tray is empty.'),
 'T02':(10,[21,30], 'White tray. Hands obscure parts of pickup; elevated cheese and exposed bases must be distinguished across frames.'),
 'T03':(10,[40,51], 'White tray. Carry to the production tank is visible; bending and arranging continue after the last removal.'),
 'T04':(10,[58,77], 'White tray. A long pause for salting/separator handling interrupts removal; remaining stock must persist during the pause.'),
 'T05':(10,[80,92], 'White tray. Multiple removals and two different worker paths; absence in one frame is insufficient release evidence.'),
 'T06':(10,[95,104], 'White tray. Outgoing tray movement overlaps the final placement; tray-empty time is not final-release time.'),
 'T07':(10,[109,119], 'White tray. Clear raised-to-flat transitions; subsequent salting and sheet handling are negatives.'),
 'T08':(9,[158,170], 'Blue tray with one initially empty position. Around 151-153 s one block is moved to another position on the same tray while no production tank is present. Inventory remains nine; tank additions remain zero during that move.'),
 'T09':(10,[173,183], 'White tray. Three-block handling is possible; quantity must not be fixed at two per transfer. Deep tank wall/body hide part of placement.'),
 'T10':(10,[185,203], 'White tray. Late carrying/arranging overlaps tray clearing. Keep quantity proposal separate from per-block release timestamps.'),
 'T11':(10,[6.5,16], 'White tray. Raised blocks disappear in stages and leave an empty tray. First incoming frame is partly below the image edge.'),
 'T12':(10,[22,29], 'Blue tray. Exposed blue positions make remaining quantity easier to read. Both workers carry towards the production tank.'),
 'T13':(10,[37,46], 'White tray. The first left-side lift starts while the tray is arriving. Use the entry sequence, not a later snapshot as initial stock.'),
 'T14':(10,[55,64], 'White tray. Salting and empty-tray handling follow removal and must not create new whole-block additions.'),
 'T15':(None,[73.5,99], 'Irregular stacked and partly broken-looking pieces lie above occupied positions. Exact whole-block quantity unresolved. Do not use ten occupied positions as ten blocks or label this as zero.'),
 'T16':(10,[116,125], 'White tray. A long crumb-cleaning interval follows emptying; source count remains zero while hands continue moving.'),
 'T17':(7,[147.5,154], 'Seven-block incoming tray, followed by removal of four then three. Final three are not all released together. This source interval was already discussed with the user; it is diagnostic, not blind evaluation.'),
 'T18':(10,[167,178], 'White tray. Salting occurs while cheese remains on the tray; source inventory and destination events must be separate states.'),
 'T19':(10,[181,190], 'White tray. The outgoing empty tray and the next incoming loaded tray coexist. Count each tray identity separately.'),
 'T20':(10,[192,204], 'White tray. Worker cleans the previous tray while the other starts on the current tray. Further crumb cleaning after emptying is not production.'),
}

NEGATIVES=[
 ('N01','O01',[60.25,67.25],'salting_separator_and_existing_cheese',0,[60.5,62,64,66]),
 ('N02','O01',[120,139],'salting_covering_and_tank_removal',0,[122,124,130,136]),
 ('N03','O01',[143,150.5],'loaded_tray_waiting_without_destination_tank',0,[143,145,148,150]),
 ('N04','O01',[150.5,154],'within_tray_relocation',0,[150.5,151.5,152,153.5]),
 ('N05','O21',[64,72.5],'salting_and_empty_tray_cleaning',0,[64,66,70,72]),
 ('N06','O21',[100,113.5],'empty_tray_crumb_cleanup',0,[100,104,108,112]),
 ('N07','O21',[126,144.5],'empty_tray_crumb_cleanup',0,[126,132,138,144]),
 ('N08','O21',[204,215],'empty_tray_cleanup_and_gestures',0,[204,208,210,214]),
]

def main():
 metas={s:json.loads((OUT/s/'frames.json').read_text()) for s in ['O01','O21']}
 def evidence(sid,t):
  r=min(metas[sid]['inspection_frames'],key=lambda r:abs(r['pts_s']-t))
  return dict(source_pts_s=r['pts_s'],source_frame_index=r['source_frame_index'],image=sid+'/'+r['image'])
 cycles=[]
 for ident,sid,a,b,ts in SELECTION:
  q,window,note=OBSERVATIONS[ident]
  cycles.append(dict(id=ident,source_id=sid,source_sha256=metas[sid]['source_sha256'],source_interval_s=[a,b],
      initial_whole_blocks_proposal=q,final_whole_blocks_on_tray_proposal=0,
      removed_whole_blocks_proposal=q,confirmed_tank_additions=None,
      review_transfer_window_s=window,release_times_exact=False,
      status='unresolved_quantity' if q is None else 'assistant_quantity_proposal',
      tray_color='blue' if ident in ('T08','T12') else 'white',
      occupancy_only_applicable=q is not None,
      note=note,evidence=[evidence(sid,t) for t in ts],
      sheet=sid+'/sheets/'+ident+'.jpg',video='clips/'+ident+'.webm',
      candidate_for_weak_supervision=q is not None,approved_for_training=False,
      independent_evaluation_eligible=False,human_verified=False))
 negatives=[dict(id=ident,source_id=sid,source_interval_s=interval,action=action,
     proposed_completed_whole_block_additions=q,evidence=[evidence(sid,t) for t in ts],
     label_provenance='assistant_visual_review',human_verified=False)
     for ident,sid,interval,action,q,ts in NEGATIVES]
 # These state anchors have direct, particularly useful visual evidence.
 anchors=[
  dict(id='blue_before_relocation',source_id='O01',**evidence('O01',150),whole_blocks_on_tray=9),
  dict(id='blue_after_relocation',source_id='O01',**evidence('O01',153.5),whole_blocks_on_tray=9),
  dict(id='blue_one_remaining',source_id='O01',**evidence('O01',164),whole_blocks_on_tray=1),
  dict(id='blue_empty',source_id='O01',**evidence('O01',170),whole_blocks_on_tray=0),
  dict(id='seven_incoming',source_id='O21',**evidence('O21',147),whole_blocks_on_tray=7),
  dict(id='three_remaining',source_id='O21',**evidence('O21',149.5),whole_blocks_on_tray=3),
  dict(id='empty_with_cheese_still_carried',source_id='O21',**evidence('O21',151.5),whole_blocks_on_tray=0),
  dict(id='irregular_stack',source_id='O21',**evidence('O21',73),whole_blocks_on_tray=None),
 ]
 for a in anchors:a.update(label_provenance='assistant_visual_review',human_verified=False,approved_for_training=False)
 report=dict(schema='tray-inventory-feasibility-v1',created_utc=datetime.now(timezone.utc).isoformat(),
    purpose='Evaluate visual observability before fitting another counter',
    methodology='Sequentially decoded both original sources. Inspected 2-second overviews, eight selected native images per cycle, and 0.5-second detail sheets for the seven-block tray and relocation. Not every decoded frame was visually inspected.',
    model_inference=False,training_started=False,september_used=False,
    no_fixed_blocks_per_tray=True,no_fixed_blocks_per_hand=True,
    exact_release_annotation_complete=False,independent_accuracy_measured=False,
    reviewed_cycles=len(cycles),quantity_proposals=sum(c['initial_whole_blocks_proposal'] is not None for c in cycles),
    unresolved_cycles=['T15'],sources=list(metas),cycles=cycles,negative_intervals=negatives,state_anchors=anchors,
    conclusion='The existing view contains useful occupancy changes, including nine- and seven-block trays. Occupancy is useful auxiliary evidence, not a standalone completed-placement counter: relocation, stacked pieces, moving trays and hidden release remain explicit failure modes.')
 (OUT/'audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 (OUT/'review_data.js').write_text('const AUDIT = '+json.dumps(report)+';\n',encoding='utf-8')
 print(json.dumps({k:report[k] for k in ['reviewed_cycles','quantity_proposals','unresolved_cycles','model_inference','training_started']}))

if __name__=='__main__':main()
