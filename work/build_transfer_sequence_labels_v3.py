"""Interval supervision from existing expert counts plus visual sequence review.

Counts remain attributed to the user. Newly reviewed time bounds are attributed
to the assistant; they are NOT exact per-frame release labels or object boxes.
"""
import json,hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/facility_dataset/temporal_pipeline'
OUT=BASE/'placement_counter_v3';OUT.mkdir(exist_ok=True)

# Position is an annotation coordinate, not a personal worker identity.
# (position, pickup interval or None, release interval, quantity or None, group)
EVENTS={
 'B007_11_18': [('left',[0,.75],[2,3.375],2,'L1')],
 'N21_04_3_11': [
  ('left',[0,.875],[1.25,2.375],2,'L1'),('right',[.25,1.125],[1.625,2.75],2,'R1'),
  ('left',[2.5,3.5],[3.875,4.875],2,'L2'),('right',[3.25,4.5],[4.75,6.25],2,'R2'),
  ('left',[5,6.25],[6.375,7.375],2,'L3')],
 'N21_05_11_25': [
  ('left',[2.5,3.625],[4,4.875],2,'L1'),('right',[2.5,3.625],[4.5,5.25],2,'R1'),
  ('left',[5.5,6.375],[6.5,7.25],1,'L2'),('right',[6,6.875],[7.75,8.25],1,'R2'),
  ('left',[5.5,6.375],[7.75,9.125],1,'L2')],
 'N21_03_0_20': [('right',None,[.25,1.375],2,'R1'),('left',[1.25,2.5],[2.625,3.5],2,'L1')],
 'N21_02_0_20': [
  ('left',[3.5,4.625],[4.875,5.875],2,'L1'),('right',[3.5,4.875],[5.375,6.625],2,'R1'),
  ('left',[6,7.125],[7.375,8.75],2,'L2'),('right',[7,8.25],[8.625,10.125],2,'R2'),
  ('left',[8.75,9.875],[9.875,12.25],2,'L3')],
 'N01_05_0_20': [
  ('right',[7,8.25],[8.75,10],2,'R1'),('left',[7.5,9],[9.125,10.5],2,'L1'),
  ('right',[11,12.5],[13,17],3,'R2'),('left',[14,15.25],[15.25,17.5],2,'L2'),
  ('right',[18,19],[19.625,19.9375],1,'R3')],
 'N01_02_0_20': [
  ('left',[0,.5],[.5,1.875],None,'L1'),('right',None,[0,1.125],2,'R1'),
  ('right',[1.25,2.5],[3,3.875],2,'R2'),
  ('left',[4,5.5],[5.5,7.625],None,'L2'),('right',[4.5,5.75],[6,6.875],1,'R3')]
}
TOTALS={'B007_11_18':[2,0],'N21_04_3_11':[6,4],'N21_05_11_25':[4,3],
        'N21_03_0_20':[2,2],'N21_02_0_20':[6,4],'N01_05_0_20':[4,6],'N01_02_0_20':[5,5]}

def main():
    segments=json.loads((BASE/'sequence_annotation_v2/count_checkpoint_v2/segments.json').read_text())
    rows=[]
    for s in segments:
        assert s['date'] in ['2026-10-01','2026-10-21']
        totals=TOTALS.get(s['segment_id'],[0,0]);assert sum(totals)==s['confirmed_count']
        events=[]
        for i,(position,pickup,release,quantity,group) in enumerate(EVENTS.get(s['segment_id'],[])):
            assert 0<=release[0]<release[1]<=s['duration_s']
            events.append(dict(event_id=f"{s['segment_id']}_E{i+1}",position=position,
                transfer_group_id=f"{s['segment_id']}_{group}",pickup_interval_s=pickup,
                release_interval_s=release,quantity=quantity,destination='filling_tank',
                pickup_left_censored=pickup is None,
                quantity_basis='Existing expert counts and assistant visual review of the corresponding sequence' if quantity is not None else 'User confirms five on left across these two transfers; which transfer contains three has not been verified',
                timing_reviewed_by='assistant',exact_release_frame_verified=False,
                object_boxes_provided=False,physical_object_ids_provided=False))
        for k,pos in enumerate(['left','right']):
            es=[e for e in events if e['position']==pos]
            if all(e['quantity'] is not None for e in es):assert sum(e['quantity'] for e in es)==totals[k]
        rows.append(dict(**s,position_totals=totals,events=events,
            supervision_v3='Counts constrained within visually reviewed release intervals; no fabricated per-frame allocation',
            full_individual_object_tracks_available=False,
            quantity_model_training_eligible=True,certified_event_counter_training_complete=False,
            no_deposit_outside_reviewed_intervals=True,
            annotation_scope='Native-source time alignment is audited separately; totals are inherited, not re-counted from detector outputs'))
    path=OUT/'interval_supervision.json'
    data=dict(schema_version=3,segments=rows,september_used=False,october3_used=False,
        annotation_warning='Intervals are assistant-reviewed bounds, not exact user-verified event timestamps. This supports a diagnostic temporal count experiment, not claims of verified object tracking.',
        sampling_policy='Every original decoded frame, using native timestamps; no 8fps or 16fps resampling',
        alternative_representation='Transfer groups can contain multiple physical blocks. A group may have multiple releases; its quantity is not the number of hands.',
        unknown_event_quantities=2,model_training_started=False)
    if path.exists():raise RuntimeError('Do not overwrite reviewed interval supervision')
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(segments=len(rows),total_blocks=sum(s['confirmed_count'] for s in rows),
        release_groups=sum(len(s['events']) for s in rows),unknown_group_quantities=2,
        labels_sha256=hashlib.sha256(path.read_bytes()).hexdigest())))

if __name__=='__main__':main()
