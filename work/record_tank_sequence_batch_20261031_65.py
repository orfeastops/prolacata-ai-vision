import datetime as dt,hashlib,json
from pathlib import Path
from record_tank_boundary_review_20261031 import read,save
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'outputs/tank_transfer_training_v1';OUT=BASE/'dataset_v1';RUN='sequence_review_20261031_65'
def main():
 state=read(OUT/'continuation_state.json')
 if RUN in state.get('completed_curation_runs',[]):return
 stamp=dt.datetime.now(dt.timezone.utc).isoformat();reg=read(OUT/'object_review_decisions.json');save(OUT/'review_history/object_decisions_before_20261031_65.json',reg)
 drafts={r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
 for ident,sheet in [('289','38'),('290','38'),('291','38')]:
  r=drafts[ident];assert not any(x['id']==ident for x in reg['reviews'])
  reg['reviews'].append(dict(id=ident,image_sha256=r['sha256'],boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',load_state_reviewed=False,sequence_reviewed=False,instance_attributes=[dict(box_index=0,truncated=ident in ('289','291'),occluded=False,load_state='unknown_not_annotated')],evidence=[r['source_frame'],r['frames_manifest'],'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_'+sheet+'.jpg'],note='Native full-frame context and separate overlay inspected. One gray tank per declared ROI.289 and291 top-truncated;290 fully contained with white top covering. Load state not assigned from color, liner or cover. Prior temporal labels unchanged.'))
 save(OUT/'object_review_decisions.json',reg)
 state['last_completed'].append('Batch65: three native15Oct camera11 ROIs289-291 and three boxes separately reviewed.289/291 top truncation explicit;290 full covered-tank geometry.233 accepted images/299 boxes; no new temporal presentation or production count.')
 state['priority_next']=['Batch65 ROIs289-291 accepted; continue native-context object collection across6/13/15Oct and seek paired complete-cycle evidence. Do not duplicate reviewed frames or infer identity through known gaps.','Batch63 local storage34:36-56 reviewed; direct entry and scale-to-staging identity remain missing. Seek continuous paired sequences for additional complete-cycle days.']+[x for x in state['priority_next'] if x.startswith('Known gaps') or x.startswith('25/28')]
 state.update(updated_at=stamp,dataset_ready=False);state.setdefault('completed_curation_runs',[]).append(RUN);state['scripts']+=['work/append_tank_roi_batch_20261031_65.py','work/record_tank_sequence_batch_20261031_65.py'];save(OUT/'continuation_state.json',state)
if __name__=='__main__':main()
