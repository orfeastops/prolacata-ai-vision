"""Save user totals for a specific eight-second segment, not an assumed tray."""
import json,pathlib,subprocess
import cv2
R=pathlib.Path(__file__).resolve().parents[1]
D=R/'outputs/facility_dataset/temporal_pipeline/sequence_annotation_v2'
p=D/'first_questions/next_transfer_question.json';q=json.loads(p.read_text())
q.update(status='answered',left_added=6,right_added=4,total_added=10,
         count_basis='User counted deposits in this specific eight-second clip, not tray capacity')
p.write_text(json.dumps(q,indent=2))
p=D/'N21_04/annotation.json';a=json.loads(p.read_text())
event=dict(event_id='N21_04_user_count_3_11',clip_id='N21_04',
    source_sha256=a['source_sha256'],action='whole_block_deposits_segment_total',
    review_clip='first_questions/next_transfer.mp4',review_clip_interval_s=[0,8],
    sequence_annotation_interval_s=[3,11],
    source_encoded_interval_s=[round(a['source_encoded_start_s']+3,3),round(a['source_encoded_start_s']+11,3)],
    actor_scope='both_filling_positions',left_whole_blocks_added=6,right_whole_blocks_added=4,
    whole_feta_block_increment=10,confirmed_by='user',semantic_label_confirmed=True,
    count_basis='Direct user report for this segment; not inferred from hands or tray capacity',
    exact_contact_lift_release_times_verified=False,individual_events_annotated=False,
    role='training_candidate',training_eligible=False,
    scope_note='Segment-level count supervision only. Does not establish total for entire 20-second source clip or for a tank.')
p=D/'expert_feedback.json';feedback=json.loads(p.read_text(encoding='utf-8'))
feedback=[e for e in feedback if e['event_id']!=event['event_id']]+[event]
p.write_text(json.dumps(feedback,ensure_ascii=False,indent=2),encoding='utf-8')
a['expert_confirmed_actions']=[e for e in feedback if e['clip_id']=='N21_04']
(D/'N21_04/annotation.json').write_text(json.dumps(a,indent=2))
ff=R/'work/video_decoder/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
out=D/'first_questions/transfer_following.mp4'
subprocess.run([str(ff),'-loglevel','error','-y','-ss','11','-i',str(D/'N21_04/hands.mp4'),
                '-t','9','-an','-c:v','libx264','-crf','19','-threads','2',str(out)],check=True)
c=cv2.VideoCapture(str(out));n=int(c.get(cv2.CAP_PROP_FRAME_COUNT));fps=c.get(cv2.CAP_PROP_FPS)
c.set(cv2.CAP_PROP_POS_FRAMES,n-1);ok,_=c.read();c.release()
assert ok and fps==16 and abs(n/fps-9)<=1/fps
question=dict(status='awaiting_user_clarification',source_clip_id='N21_04',
    source_clip_interval_s=[11,11+n/fps],review_duration_s=n/fps,review_clip='first_questions/transfer_following.mp4',
    question='How many whole blocks are deposited by each worker, and what does the opposite worker do when turning toward the rear tank?',
    left_added=None,right_added=None,rear_motion=None,exact_boundaries_verified=False)
(D/'first_questions/transfer_following_question.json').write_text(json.dumps(question,indent=2))
assert sum([event['left_whole_blocks_added'],event['right_whole_blocks_added']])==event['whole_feta_block_increment']
print('Recorded user totals 6 + 4 for segment only; verified nine-second continuation. No model trained.')
