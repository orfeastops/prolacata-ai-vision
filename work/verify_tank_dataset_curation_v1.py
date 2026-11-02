"""Check curation provenance and local review links without releasing training."""
import argparse
import collections
import datetime as dt
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse
from record_tank_boundary_review_20261031 import read, save

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/tank_transfer_training_v1'
OUT=BASE/'dataset_v1'


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links=set()

    def handle_starttag(self,tag,attrs):
        self.links.update(v for k,v in attrs if k in ['href','src'] and v)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--name',required=True)
    args=parser.parse_args()
    assert args.name.replace('_','').isalnum()
    quality=read(OUT/'quality_report.json')
    state=read(OUT/'continuation_state.json')
    records=read(OUT/'image_annotations_draft.json')['records']
    review_registry=read(OUT/'object_review_decisions.json')
    registry={r['id']:r for r in review_registry['reviews']}
    reviews=read(OUT/'screening_source_reviews.json')
    labels=read(OUT/'reviewed_sequence_labels.json')
    inventory=read(BASE/'archive_inventory.json')['records']
    protocol=read(OUT/'annotation_protocol.json')
    splits=protocol['split_policy']
    sets=[set(splits[k]) for k in ['archive_train_days','validation_days','locked_test_days']]
    def normalized_split(split):
        assert split in ['train','val','validation'],split
        return 'val' if split=='validation' else split

    def check_partition(date, split):
        assert date not in sets[2]
        assert date in (sets[0] if normalized_split(split)=='train' else sets[1]),(date,split)
    assert all(not a&b for i,a in enumerate(sets) for b in sets[i+1:])
    assert not any(r['pixel_inspected'] for r in inventory if r['split']=='test')
    assert not quality['training_ready'] and not quality['training_started'] and not state['dataset_ready']
    assert state['active_extraction_processes']==[]
    assert len({r['id'] for r in records})==len(records)
    image_splits={}
    accepted=[]
    native_still_hash_checks=0

    def check_native_still(provenance, member, date, split):
        nonlocal native_still_hash_checks
        source=ROOT/provenance['native_source_image']
        assert digest(source)==provenance['source_sha256']
        entries=read(ROOT/provenance['context_manifest'])
        matching=[e for e in entries if e['native_image']==provenance['native_source_image']]
        assert len(matching)==1
        context=matching[0]
        assert context['source_member']==member and context['source_sha256']==provenance['source_sha256']
        assert context['date']==date and context['split']==split
        assert context['date'] not in sets[2]
        native_still_hash_checks+=1

    for r in records:
        check_partition(r['date'],r['split'])
        assert (ROOT/r['image']).exists() and digest(ROOT/r['image'])==r['sha256']
        image_splits.setdefault(r['sha256'],set()).add(r['split'])
        for x1,y1,x2,y2 in r['boxes_xyxy'] or []:
            assert 0<=x1<x2<=r['width'] and 0<=y1<y2<=r['height']
        if r['annotation_status']=='roi_boxes_reviewed_assistant':
            decision=registry[r['id']]
            assert decision['image_sha256']==r['sha256']
            assert decision['boxes_sha256']==hashlib.sha256(json.dumps(r['boxes_xyxy'],separators=(',',':')).encode()).hexdigest()
            # Earlier decisions carry image/box hashes only. Their source is
            # retained in the candidate record; newer decisions add file refs.
            assert all((ROOT/p).exists() for p in decision.get('evidence',[]))
            if decision.get('frozen_overlay'):
                overlay=decision['frozen_overlay']
                frozen=read(ROOT/overlay['manifest'])
                assert digest(ROOT/overlay['image'])==overlay['sha256']==frozen['overlay_sha256']
                assert frozen['source_image_sha256']==r['sha256'] and frozen['boxes_xyxy']==r['boxes_xyxy']
                assert frozen['id']==r['id'] and frozen['boxes_sha256']==decision['boxes_sha256']
            if decision.get('source_provenance'):
                check_native_still(decision['source_provenance'], r['source'], r['date'], r['split'])
            accepted.append(r)
        if r.get('native_source_image'):
            check_native_still(r, r['source'], r['date'], r['split'])
        if r.get('source_frame_sha256'):
            assert digest(ROOT/r['source_frame'])==r['source_frame_sha256']
            m=read(ROOT/r['frames_manifest'])
            s=m['samples'][r['sample_index']]
            assert r['source_sha256']==m['source_sha256'] and r['source']==m['source']['member']
            assert r['source_frame']==s['image'] and r['source_frame_sha256']==s['image_sha256']
    assert all(len(v)==1 for v in image_splits.values())
    assert len(accepted)==quality['accepted_images']
    assert sum(len(r['boxes_xyxy']) for r in accepted)==quality['accepted_object_boxes']
    by_id={r['id']:r for r in records}
    overlay_manifest=BASE/'detector_v1/overlay_sheet_manifest.json'
    if overlay_manifest.exists():
        om=read(overlay_manifest)
        assert set(om['included_ids'])=={r['id'] for r in records if r['annotation_status']!='excluded_uncertain_instance_boundaries'}
        assert len(om['sheets'])==(len(om['included_ids'])+5)//6
        assert all((ROOT/p).exists() for p in om['sheets'])
    for excluded in review_registry.get('excluded_roi_reviews',[]):
        r=by_id[excluded['id']]
        assert r['annotation_status']=='excluded_uncertain_instance_boundaries'
        assert r['sha256']==excluded['image_sha256'] and excluded['reason']
        assert all((ROOT/p).exists() for p in excluded['evidence'])
    assert len(reviews)==quality['reviewed_source_windows']
    assert len({r['source_sha256'] for r in reviews})==quality['reviewed_source_video_count']
    assert sum(r['sampled_frames_visually_reviewed'] for r in reviews)==quality['reviewed_temporal_sample_presentations']
    hash_checks=0
    for r in reviews:
        check_partition(r['date'],r['split'])
        m=read(ROOT/r['frames_manifest'])
        assert m['source']['date']==r['date'] and normalized_split(m['source']['split'])==normalized_split(r['split'])
        assert m['source_sha256']==r['source_sha256'] and m['source']['member']==r['source_member']
        assert len(m['samples'])==r['sampled_frames_visually_reviewed']
        assert all((ROOT/p).exists() for p in r['reviewed_sheets'])
        for s in m['samples']:
            assert (ROOT/s['image']).exists()
            if s.get('image_sha256'):
                assert digest(ROOT/s['image'])==s['image_sha256']
                hash_checks+=1
        for a in r['visible_clock_anchors']:
            s=m['samples'][a['sample_index']]
            assert a['image']==s['image'] and a['source_pts_seconds']==s['source_pts_seconds']
            assert a['relative_pts_seconds']==s['relative_pts_seconds']
    evidence_checks=0

    def walk(node, expected_date=None, expected_split=None):
        nonlocal evidence_checks
        if isinstance(node,dict):
            if 'frames_manifest' in node and 'sample_index_interval' in node:
                m=read(ROOT/node['frames_manifest'])
                assert m['source']['date'] not in sets[2]
                check_partition(m['source']['date'],m['source']['split'])
                if expected_date is not None:
                    assert m['source']['date']==expected_date
                    assert normalized_split(m['source']['split'])==normalized_split(expected_split)
                assert node['source_sha256']==m['source_sha256']
                assert node['source_member_or_path']==m['source']['member']
                a,b=node['sample_index_interval']
                assert 0<=a<=b<len(m['samples'])
                samples=[m['samples'][a],m['samples'][b]]
                assert node['relative_pts_interval']==[s['relative_pts_seconds'] for s in samples]
                assert node['source_pts_interval']==[s['source_pts_seconds'] for s in samples]
                assert node['image_evidence']==[s['image'] for s in samples]
                evidence_checks+=1
            for v in node.values():
                walk(v,expected_date,expected_split)
        elif isinstance(node,list):
            for v in node:
                walk(v,expected_date,expected_split)

    assert len({s['sequence_id'] for s in labels})==len(labels)
    for split in ['train','val']:
        counts=dict(collections.Counter(s['review_status'] for s in labels if s['split']==split))
        assert counts==quality['sequence_counts_by_split'][split]
    for s in labels:
        check_partition(s['date'],s['split'])
        if s['review_status']=='accepted_complete_cycle':
            assert s['cycle_id'] and s['production_entry_count_target']==1
            assert set(protocol['sequence_annotation']['stages'])<={st['stage'] for st in s['stages']}
        elif s['review_status']=='accepted_negative_sequence':
            assert s['production_entry_count_target']==0 and s['negative_class'] in protocol['sequence_annotation']['negative_cases']
        elif s['review_status']=='reviewed_partial_sequence':
            assert s['production_entry_count_target'] is None and s['cycle_id'] is None
        elif s['review_status']=='reviewed_context_existing_cycle':
            assert s['production_entry_count_target'] is None and s['cycle_id'] is None
            linked = [c for c in labels if c['sequence_id']==s['linked_sequence_id']]
            assert len(linked)==1 and linked[0]['review_status']=='accepted_complete_cycle'
            assert linked[0]['cycle_id']==s['linked_cycle_id']
            assert linked[0]['date']==s['date'] and linked[0]['split']==s['split']
        walk(s,s['date'],s['split'])
    followup_path=OUT/'sequence_followup_queue.json'
    if followup_path.exists():
        for candidate in read(followup_path):
            check_partition(candidate['date'],candidate['split'])
            assert candidate['cycle_id'] is None and candidate['production_entry_count_target'] is None
            walk(candidate,candidate['date'],candidate['split'])
    # The workspace builder used to overwrite this reviewed case summary.
    # Once native labels exist, a generic needs-review summary is a regression.
    case=read(OUT/'sequence_review_case_20261021_390.json')
    if any(s['sequence_id']=='20261021_beige_entry_scale_partial_1341' for s in labels):
        assert case['status']=='native_review_complete_two_partial_tracks_and_two_empty_returns'
        assert set(case['reviewed_sequence_ids'])<={s['sequence_id'] for s in labels}
        assert case['storage_placement'] is None
    text=(OUT/'review.html').read_text('utf8')
    assert '\ufffd' not in text
    links=Links()
    links.feed(text)
    checked=0
    for link in links.links:
        url=urlparse(link)
        if url.scheme or link.startswith('#'):
            continue
        assert (OUT/unquote(url.path)).resolve().exists(),link
        checked+=1
    result=dict(status='curation_integrity_checks_passed_not_dataset_release',reviewed_at=dt.datetime.now(dt.timezone.utc).isoformat(),
        accepted_roi_images=quality['accepted_images'],accepted_roi_boxes=quality['accepted_object_boxes'],
        accepted_complete_cycles=quality['accepted_complete_cycles'],accepted_negative_sequences=quality['accepted_negative_sequences'],
        reviewed_partial_sequences=quality['reviewed_partial_sequences'],temporal_sample_presentations=quality['reviewed_temporal_sample_presentations'],
        source_video_count=quality['reviewed_source_video_count'],source_windows=len(reviews),local_review_links_checked=checked,
        temporal_image_hash_checks=hash_checks,native_still_hash_checks=native_still_hash_checks,
        sequence_evidence_checks=evidence_checks,test_pixels_inspected=0,training_started=False,training_ready=False,
        coverage_note='Curation integrity only. Complete-cycle day coverage and object-image collection remain incomplete; negative counts alone do not establish scenario coverage. Uncertain trajectories remain partial.')
    target=OUT/(args.name+'.json')
    save(target,result)
    state['latest_integrity_check']=str(target.relative_to(ROOT))
    save(OUT/'continuation_state.json',state)
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
