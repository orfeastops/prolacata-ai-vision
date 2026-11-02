import datetime as dt,hashlib,json
from pathlib import Path
from record_tank_boundary_review_20261031 import read,save
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'outputs/tank_transfer_training_v1';OUT=BASE/'dataset_v1';RUN='sequence_review_20261031_71'
def main():
 state=read(OUT/'continuation_state.json')
 if RUN in state.get('completed_curation_runs',[]):return
 stamp=dt.datetime.now(dt.timezone.utc).isoformat();reg=read(OUT/'object_review_decisions.json');save(OUT/'review_history/object_decisions_before_20261031_71.json',reg)
 drafts={r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
 for ident,sheet in [('303','40'),('304','40')]:
  r=drafts[ident];assert not any(x['id']==ident for x in reg['reviews'])
  reg['reviews'].append(dict(id=ident,image_sha256=r['sha256'],boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',load_state_reviewed=False,sequence_reviewed=False,instance_attributes=[dict(box_index=k,truncated=False,occluded=(ident=='304' and k in (2,3)),load_state='unknown_not_annotated') for k in range(len(r['boxes_xyxy']))],evidence=[r['source_frame'],r['frames_manifest'],'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_'+sheet+'.jpg'],note='Native full context and separate overlays inspected.303 single beige tank;304 four distinct staging/scale-area tanks with rear instances partly occluded. Plastic covers and white insert do not establish load state. No new event, weight or cross-camera match inferred.'))
 save(OUT/'object_review_decisions.json',reg)
 state['last_completed'].append('Batch71:two native15Oct camera15 ROIs303-304 with5 boxes approved after independent overlays.244 accepted images/324 boxes;61 exclusions. Prior temporal evidence and cycle counts preserved.')
 state['priority_next']=['Batch71 ROIs303-304 approved from15Oct fifth_route1317/gray_route_1052 sample5. Do not duplicate these frames. Resume chronological review and paired-source search beyond documented gaps; object-only additions do not resolve complete-cycle day coverage.']+[x for x in state['priority_next'] if x.startswith('Known gaps') or x.startswith('25/28')]
 state.update(updated_at=stamp,dataset_ready=False);state.setdefault('completed_curation_runs',[]).append(RUN);state['scripts']+=['work/append_tank_roi_batch_20261031_71.py','work/record_tank_sequence_batch_20261031_71.py'];save(OUT/'continuation_state.json',state)
if __name__=='__main__':main()
