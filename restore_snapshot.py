"""Restore packaged artifacts into this checkout; no network access."""
import argparse,hashlib,json,zipfile
from pathlib import Path

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--verify-only',action='store_true')
    parser.add_argument('--overwrite',action='store_true')
    args=parser.parse_args();root=Path(__file__).resolve().parent
    manifest=json.loads((root/'snapshot_manifest.json').read_text(encoding='utf-8'))
    count=0
    for arc in manifest['archives']:
        p=root/arc['file']
        if hashlib.sha256(p.read_bytes()).hexdigest()!=arc['sha256']:raise RuntimeError('Archive checksum mismatch: '+p.name)
        with zipfile.ZipFile(p) as z:
            for info in z.infolist():
                target=(root/info.filename).resolve()
                if not target.is_relative_to(root.resolve()):raise RuntimeError('Unsafe archive path')
                data=z.read(info.filename)
                if hashlib.sha256(data).hexdigest()!=arc['members'][info.filename]:raise RuntimeError('Member checksum mismatch')
                if not args.verify_only:
                    if target.exists() and target.read_bytes()!=data and not args.overwrite:
                        raise RuntimeError('Existing file differs; keep your edits or explicitly use --overwrite: '+str(target))
                    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
                count+=1
    print(('Verified ' if args.verify_only else 'Restored ')+str(count)+' artifact files')

if __name__=='__main__':main()
