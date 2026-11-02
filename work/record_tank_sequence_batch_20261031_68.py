import datetime as dt,hashlib,json
from pathlib import Path
from record_tank_boundary_review_20261031 import read,save
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'outputs/tank_transfer_training_v1';OUT=BASE/'dataset_v1';RUN='sequence_review_20261031_68'
def main():
 state=read(OUT/'continuation_state.json')
 if RUN in state.get('completed_curation_runs',[]):return
 stamp=dt.datetime.now(dt.timezone.utc).isoformat();reg=read(OUT/'object_review_decisions.json');save(OUT/'review_history/object_decisions_before_20261031_68.json',reg)
 drafts={r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
 for ident,sheet in [('297','39')]:
  r=drafts[ident];assert not any(x['id']==ident for x in reg['reviews'])
  reg['reviews'].append(dict(id=ident,image_sha256=r['sha256'],boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',load_state_reviewed=False,sequence_reviewed=False,instance_attributes=[dict(box_index=k,truncated=False,occluded=(k==2),load_state='unknown_not_annotated') for k in range(len(r['boxes_xyxy']))],evidence=[r['source_frame'],r['frames_manifest'],'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_'+sheet+'.jpg'],note='Native full context and independent overlay inspected. Three distinct staging tanks; rear tank occluded by front pair. No load label or fresh-production assignment.298 separately excluded for unclear boundaries.'))
 save(OUT/'object_review_decisions.json',reg)
 state['last_completed'].append('Batch68:6Oct camera15 ROI297 approved with3 boxes;298 excluded after overlay review because truncation and blur obscure boundaries.239 accepted images/313 boxes,60 exclusions. No temporal or cycle count added.')
 state['priority_next']=['Batch68 ROI297 approved;298 excluded. Avoid these selected frames. Continue camera15 native-context object annotation and seek complete cycles across additional training days.']+[x for x in state['priority_next'] if x.startswith('Known gaps') or x.startswith('25/28')]
 state.update(updated_at=stamp,dataset_ready=False);state.setdefault('completed_curation_runs',[]).append(RUN);state['scripts']+=['work/append_tank_roi_batch_20261031_68.py','work/record_tank_sequence_batch_20261031_68.py'];save(OUT/'continuation_state.json',state)
if __name__=='__main__':main()
