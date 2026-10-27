"""Kaggle: learn video representations from supplied, unlabelled facility media.

This is masked reconstruction pretraining, NOT a production/event counter.
No downloaded pretrained weights or unverified object proposals are used.
"""
import os, json, pathlib, zipfile, subprocess, io, time, random, collections
import concurrent.futures, threading, math
import numpy as np
from PIL import Image
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import VideoMAEConfig, VideoMAEForPreTraining
from transformers.image_utils import IMAGENET_DEFAULT_MEAN, IMAGENET_DEFAULT_STD

SEED=42
random.seed(SEED);np.random.seed(SEED);torch.manual_seed(SEED)
os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
assert torch.cuda.is_available(), 'GPU required: do not start bulk training on CPU.'
OUT=pathlib.Path('/kaggle/working/facility_video_pretraining');OUT.mkdir(exist_ok=True)
CACHE=pathlib.Path('/kaggle/temp/facility_video_cache');CACHE.mkdir(parents=True,exist_ok=True)
matches=list(pathlib.Path('/kaggle/input').rglob('bundle_manifest.json'))
if not matches:
    archives=list(pathlib.Path('/kaggle/input').rglob('facility_gpu_bundle.zip'))
    assert len(archives)==1,'Attach the private facility dataset.'
    target=pathlib.Path('/kaggle/temp/facility_data');target.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archives[0]) as z:
        assert all((target/x.filename).resolve().is_relative_to(target.resolve()) for x in z.infolist())
        z.extractall(target)
    matches=list(target.rglob('bundle_manifest.json'))
assert len(matches)==1
ROOT=matches[0].parent
media=json.loads((ROOT/'media_manifest_portable.json').read_text())
assert len(media)==2082
test=[r for r in media if r['date']=='2026-10-03']
train=[r for r in media if r['date']!='2026-10-03']
assert not ({x['sha256'] for x in test}&{x['sha256'] for x in train})
assert len({x['sha256'] for x in train})==len(train)
videos=[r for r in train if r['extension'].lower() in ('.mp4','.avi','.mov','.mkv')]
photos=[r for r in train if r not in videos]
assert len(videos)+len(photos)==len(train)
manifest={'stage':'self_supervised_video_pretraining','training_media':len(train),
 'training_videos':len(videos),'training_photos':len(photos),'heldout_media':len(test),
 'heldout_day':'2026-10-03','heldout_used_for_training_or_selection':False,
 'initialization':'random VideoMAE base architecture; no external pretrained weights',
 'target':'masked pixel reconstruction, not event counts',
 'photos_usage':'Repeated still frames teach appearance only; not hand motion.',
 'clock_verified':False,'uses_unverified_teacher_proposals':False,
 'production_ready':False,'seed':SEED}
(OUT/'training_manifest.json').write_text(json.dumps(manifest,indent=2))
(OUT/'heldout_sources.json').write_text(json.dumps(test,indent=2))
print('MANIFEST',json.dumps(manifest),flush=True)

def ff_filter(camera):
    # A dedicated filling crop is essential for hands. Camera15 keeps the room.
    prefix='crop=640:360:800:720,' if camera==11 else ''
    return prefix+'fps=4,scale=224:224:force_original_aspect_ratio=decrease,pad=224:224:(ow-iw)/2:(oh-ih)/2'

def cache_source(r):
    dest=CACHE/(r['sha256']+'.zip')
    if dest.exists():
        with zipfile.ZipFile(dest) as z:return r['sha256'],len(z.namelist())
    tmp=CACHE/(r['sha256']+'.mp4')
    # DVR files are MPEG-PS despite their extension. Remux before seeking/decoding.
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(ROOT/r['media_path']),
        '-map','0:v:0','-an','-c:v','copy',str(tmp)],capture_output=True,check=True,timeout=180)
    process=subprocess.Popen(['ffmpeg','-hide_banner','-loglevel','error','-threads','2','-i',str(tmp),
        '-an','-vf',ff_filter(r['camera']),'-threads','2','-f','image2pipe','-vcodec','mjpeg','-q:v','5','pipe:1'],
        stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
    partial=dest.with_suffix('.partial');count=0;pending=b''
    try:
        with zipfile.ZipFile(partial,'w',compression=zipfile.ZIP_STORED) as z:
            while True:
                chunk=process.stdout.read(65536)
                if not chunk:break
                pending+=chunk
                while True:
                    begin=pending.find(b'\xff\xd8');end=pending.find(b'\xff\xd9',max(begin,0))
                    if begin<0 or end<0:break
                    z.writestr(f'{count:06d}.jpg',pending[begin:end+2]);count+=1;pending=pending[end+2:]
            assert process.wait(timeout=30)==0 and count>0, 'Video decode failed'
        partial.replace(dest)
    finally:
        if process.poll() is None:process.kill();process.wait()
        tmp.unlink(missing_ok=True)
        partial.unlink(missing_ok=True)
    return r['sha256'],count

# Decode every training video, not just the 24 review examples. Failures are
# recorded and stop training; do not silently report complete data coverage.
cache_counts={};failures=[];start_cache=time.time()
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    futures={pool.submit(cache_source,r):r for r in videos}
    for i,f in enumerate(concurrent.futures.as_completed(futures)):
        try:
            sha,n=f.result();cache_counts[sha]=n
        except Exception as exc:
            failures.append({'source_sha256':futures[f]['sha256'],'error':str(exc)[:800]})
        if i%25==0:print('CACHE',i+1,'/',len(videos),'elapsed_s',round(time.time()-start_cache),flush=True)
(OUT/'decode_failures.json').write_text(json.dumps(failures,indent=2))
assert not failures, 'Resolve recorded decoder failures before claiming complete coverage.'
(OUT/'cache_frame_counts.json').write_text(json.dumps(cache_counts,indent=2))

items=[]
for r in videos:
    n=cache_counts[r['sha256']]
    # Cover the whole encoded timeline. Tail/short videos are retained.
    starts=list(range(0,max(1,n-15),32))
    tail=max(0,n-16)
    if tail not in starts:starts.append(tail)
    for start in starts:items.append({'source_sha256':r['sha256'],'kind':'video','start_frame':start,'n_frames':n})
for r in photos:items.append({'source_sha256':r['sha256'],'kind':'photo','media_path':r['media_path'],'camera':r['camera']})
by_sha={r['sha256']:r for r in train}
assert {x['source_sha256'] for x in items}==set(by_sha)
(OUT/'training_items.json').write_text(json.dumps(items))
print('ALL TRAINING SOURCES DECODED',len(by_sha),'training items',len(items),flush=True)
mean=torch.tensor(IMAGENET_DEFAULT_MEAN).view(1,3,1,1)
std=torch.tensor(IMAGENET_DEFAULT_STD).view(1,3,1,1)

class MediaDataset(Dataset):
    def __len__(self):return len(items)
    def __getitem__(self,i):
        item=items[i]
        if item['kind']=='video':
            # 16 frames at 4fps (four seconds). Epoch jitter samples neighbouring
            # action phases within the complete-source eight-second grid.
            start=min(item['start_frame']+random.randint(0,16),max(0,item['n_frames']-16))
            ids=np.minimum(np.arange(start,start+16),item['n_frames']-1)
            with zipfile.ZipFile(CACHE/(item['source_sha256']+'.zip')) as z:
                frames=[np.asarray(Image.open(io.BytesIO(z.read(f'{j:06d}.jpg'))).convert('RGB')) for j in ids]
        else:
            im=Image.open(ROOT/item['media_path']).convert('RGB')
            if item['camera']==11:im=im.crop((800,720,1440,1080))
            im.thumbnail((224,224));canvas=Image.new('RGB',(224,224));canvas.paste(im,((224-im.width)//2,(224-im.height)//2))
            frames=[np.asarray(canvas)]*16
        x=torch.from_numpy(np.stack(frames).copy()).permute(0,3,1,2).float()/255
        return (x-mean)/std

config=VideoMAEConfig(image_size=224,num_frames=16,patch_size=16,tubelet_size=2,
 hidden_size=768,num_hidden_layers=12,num_attention_heads=12,intermediate_size=3072,
 decoder_hidden_size=384,decoder_num_hidden_layers=4,decoder_num_attention_heads=6,decoder_intermediate_size=1536)
model=VideoMAEForPreTraining(config).cuda()
optimizer=torch.optim.AdamW(model.parameters(),lr=1e-4,weight_decay=.05)
scaler=torch.amp.GradScaler('cuda')
gpu_count=torch.cuda.device_count()
loader=DataLoader(MediaDataset(),batch_size=4*gpu_count,shuffle=True,num_workers=2,pin_memory=True,drop_last=False)
runner=torch.nn.DataParallel(model) if gpu_count>1 else model
device_name=torch.cuda.get_device_name(0)
print('MODEL',sum(p.numel() for p in model.parameters()),'parameters',device_name,flush=True)
config.save_pretrained(OUT/'architecture')

def tube_mask(batch):
    spatial=196;masked=176
    order=torch.rand(batch,spatial,device='cuda').argsort(1)
    base=torch.zeros(batch,spatial,dtype=torch.bool,device='cuda')
    base.scatter_(1,order[:,:masked],True)
    return base[:,None,:].expand(-1,8,-1).reshape(batch,-1)

def checkpoint(epoch,step,completed=False):
    model.save_pretrained(OUT/'latest_model',safe_serialization=True)
    torch.save({'epoch':epoch,'step':step,'optimizer':optimizer.state_dict(),'scaler':scaler.state_dict(),
      'torch_rng':torch.get_rng_state(),'cuda_rng':torch.cuda.get_rng_state_all(),
      'python_rng':random.getstate(),'numpy_rng':np.random.get_state()},OUT/'optimizer_checkpoint.pt')
    state={'stage':'self_supervised_pretraining','epoch':epoch,'optimizer_steps':step,
      'completed_scheduled_epochs':completed,'production_ready':False,'counting_head_trained':False,
      'training_sources':len(train),'training_items':len(items),'heldout_sources':len(test),
      'device':device_name,'loss_is_not_counting_accuracy':True}
    (OUT/'training_status.json').write_text(json.dumps(state,indent=2))

MAX_EPOCHS=10;MAX_TRAIN_SECONDS=6*3600
step=0;started=time.time();stop=False
with (OUT/'losses.jsonl').open('w') as log:
    for epoch in range(MAX_EPOCHS):
        model.train()
        for x in loader:
            x=x.cuda(non_blocking=True);optimizer.zero_grad(set_to_none=True)
            with torch.autocast('cuda',dtype=torch.float16):loss=runner(pixel_values=x,bool_masked_pos=tube_mask(len(x))).loss.mean()
            assert torch.isfinite(loss),'Non-finite loss; inspect preprocessing and optimizer.'
            scaler.scale(loss).backward();scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(),1.)
            scaler.step(optimizer);scaler.update();step+=1
            if step%10==0:
                row={'epoch':epoch+1,'step':step,'loss':float(loss.detach()),'elapsed_s':round(time.time()-started,1)}
                log.write(json.dumps(row)+'\n');log.flush();print('TRAIN',json.dumps(row),flush=True)
            if step==1 or step%250==0:checkpoint(epoch+1,step)
            if time.time()-started>MAX_TRAIN_SECONDS:stop=True;break
        checkpoint(epoch+1,step,completed=epoch+1==MAX_EPOCHS)
        if stop:break
print('PRETRAINING SAVED. This checkpoint still requires supervised event training and independent counting evaluation.',flush=True)
