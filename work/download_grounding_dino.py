import pathlib,urllib.request,json,time
dest=pathlib.Path('work/models/grounding-dino-tiny');dest.mkdir(parents=True,exist_ok=True)
files=['config.json','preprocessor_config.json','tokenizer_config.json','tokenizer.json','special_tokens_map.json','added_tokens.json','vocab.txt','model.safetensors']
for name in files:
 target=dest/name
 if target.exists() and (name!='model.safetensors' or target.stat().st_size>600_000_000):continue
 print('Downloading official model file',name,flush=True)
 with urllib.request.urlopen('https://huggingface.co/IDEA-Research/grounding-dino-tiny/resolve/main/'+name,timeout=60) as src,target.with_suffix(target.suffix+'.partial').open('wb') as out:
  while chunk:=src.read(4*1024*1024):out.write(chunk)
 target.with_suffix(target.suffix+'.partial').replace(target)
print('Official Grounding DINO files downloaded',flush=True)
