import datetime as dt,hashlib,json
from pathlib import Path
from record_tank_boundary_review_20261031 import read,save
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'outputs/tank_transfer_training_v1';OUT=BASE/'dataset_v1';RUN='sequence_review_20261031_67'
def main():
 state=read(OUT/'continuation_state.json')
 if RUN in state.get('completed_curation_runs',[]):return
 stamp=dt.datetime.now(dt.timezone.utc).isoformat();reg=read(OUT/'object_review_decisions.json');save(OUT/'review_history/object_decisions_before_20261031_67.json',reg)
 drafts={r['id']:r for r in read(BASE/'detector_v1/visual_annotation_draft.json')['records']}
 for ident,sheet in [('294','39'),('295','39'),('296','39')]:
  r=drafts[ident];assert not any(x['id']==ident for x in reg['reviews'])
  reg['reviews'].append(dict(id=ident,image_sha256=r['sha256'],boxes_sha256=hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest(),reviewer='assistant_visual_review',review_date='2026-10-31',decision='accepted_for_roi_tank_detection',load_state_reviewed=False,sequence_reviewed=False,instance_attributes=[dict(box_index=k,truncated=False,occluded=((ident=='294' and k in (0,1)) or (ident=='295' and k==0)),load_state='unknown_not_annotated') for k in range(len(r['boxes_xyxy']))],evidence=[r['source_frame'],r['frames_manifest'],'outputs/tank_transfer_training_v1/detector_v1/sheets/labels_'+sheet+'.jpg'],note='Native full-frame context and independent overlay inspected.294 contains four distinct lined tanks with two rear instances occluded;295 contains three tanks with rear-left occlusion;296 contains one clear tank. All instances within declared ROI included. No new production, load-state or identity assignment from stationary arrangement.'))
 save(OUT/'object_review_decisions.json',reg)
 state['last_completed'].append('Batch67: three native6Oct camera11 ROIs294-296 and eight boxes independently reviewed. Stationary groups of4/3/1 separated, rear occlusions recorded.238 accepted images/310 boxes; no new temporal presentations or production counts.')
 state['priority_next']=['Batch67 ROIs294-296 accepted from6Oct morning_departure0853/0903/0927 sample5. Continue object coverage across both cameras, and prioritize paired continuous sequences for additional complete-cycle days. Do not re-review these selected samples.','Batch63 local storage34:36-56 reviewed; direct entry and scale-to-staging identity remain missing. Seek continuous paired sequences for additional complete-cycle days.']+[x for x in state['priority_next'] if x.startswith('Known gaps') or x.startswith('25/28')]
 state.update(updated_at=stamp,dataset_ready=False);state.setdefault('completed_curation_runs',[]).append(RUN);state['scripts']+=['work/append_tank_roi_batch_20261031_67.py','work/record_tank_sequence_batch_20261031_67.py'];save(OUT/'continuation_state.json',state)
if __name__=='__main__':main()
