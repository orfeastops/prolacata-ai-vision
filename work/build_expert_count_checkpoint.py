"""Materialize expert segment counts without inventing per-frame labels."""
import json, pathlib, hashlib, collections, subprocess
import cv2

R = pathlib.Path(__file__).resolve().parents[1]
D = R / 'outputs/facility_dataset/temporal_pipeline/sequence_annotation_v2'
O = D / 'count_checkpoint_v2'
O.mkdir(exist_ok=True)
FF = R / 'work/video_decoder/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

def save(p, x):
    p.write_text(json.dumps(x, ensure_ascii=False, indent=2), encoding='utf-8')

feedback = read(D / 'expert_feedback.json')
groups = collections.defaultdict(list)
excluded = []
for e in feedback:
    if e['role'] != 'training_candidate':
        excluded.append(e['event_id'])
        continue
    groups[(e['clip_id'], e['review_clip'], tuple(e['sequence_annotation_interval_s']))].append(e)

rows = []
for (cid, media, interval), labels in groups.items():
    a = read(D / cid / 'annotation.json')
    assert a['date'] in ('2026-10-01', '2026-10-21')
    # B007 has separate left/right user annotations for the same media interval.
    if len(labels) > 1:
        assert cid == 'B007' and len(labels) == 2
        assert {e['actor_scope'] for e in labels} == {'filling_left_only', 'filling_right_only'}
    total = sum(e['whole_feta_block_increment'] for e in labels)
    source = D / media
    out = O / f'{cid}_{interval[0]:g}_{interval[1]:g}.mp4'
    cap = cv2.VideoCapture(str(source))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, n-1); ok, _ = cap.read(); cap.release()
    assert ok and abs(n/fps - (interval[1]-interval[0])) <= .13, source
    # Reviewed copies with timestamp header require removal, not scaling.
    assert (w, h) in [(640,360), (640,400)]
    command = [str(FF), '-loglevel','error','-y','-i',str(source)]
    if h == 400:
        command += ['-vf','crop=640:360:0:40']
    command += ['-an','-c:v','libx264','-crf','18','-threads','2',str(out)]
    subprocess.run(command, check=True)
    start = a['source_encoded_start_s'] + interval[0]
    rows.append(dict(segment_id=out.stem, clip_id=cid, media_path=str(out),
        source_sha256=a['source_sha256'], date=a['date'],
        source_encoded_interval_s=[start,start+n/fps], duration_s=n/fps,
        confirmed_count=total, feedback_ids=[e['event_id'] for e in labels],
        supervision='segment_count_only', role='development_checkpoint_not_independent_test',
        dense_release_labels_available=False, actor_count_labels=labels,
        label_warning='Do not distribute count over frames, count hands, or add nested actions to segment total.'))

assert len({v['segment_id'] for v in rows}) == len(rows)
# Source-level grouping is mandatory for any later cross-validation.
source_groups = collections.defaultdict(list)
for row in rows:
    source_groups[row['source_sha256']].append(row['segment_id'])
save(O/'segments.json', rows)
save(O/'source_groups.json', source_groups)
report = dict(segments=len(rows), sources=len(source_groups),
    positive_segments=sum(v['confirmed_count']>0 for v in rows),
    zero_segments=sum(v['confirmed_count']==0 for v in rows),
    sum_segment_counts=sum(v['confirmed_count'] for v in rows),
    summed_review_duration_s=sum(v['duration_s'] for v in rows),
    excluded_development_feedback=excluded, independent_test=False,
    note='Review durations include overlapping context. Counts are segment targets, not facility production.',
    model_audit={'v1_quantity':'Hardcoded quantity=1 per accepted hand cycle in Tracker.finish',
      'v1_limitation':'Cannot represent several blocks carried by one hand or jointly by two hands; threshold tuning cannot repair this representation.',
      'next_model_requirements':['visible whole-block multiplicity', 'pickup-to-deposit continuity', 'crumb/tray/glove negatives', 'unknown quantities retained as unknown']},
    training_started=False, production_ready=False,
    pending=['Dense object/quantity annotation for positive events', 'Source-separated model development', 'Fresh independent count evaluation'])
save(O/'preparation_report.json', report)
print(json.dumps(report, indent=2))
