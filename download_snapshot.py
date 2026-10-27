"""Download the seven public research archives and verify their SHA-256 hashes."""
import hashlib
import json
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

RELEASE = 'https://github.com/orfeastops/prolacata-ai-vision/releases/download/v0.0.0-research-20261027/'

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def main():
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / 'snapshot_manifest.json').read_text(encoding='utf-8'))
    for archive in manifest['archives']:
        name = archive['file']
        if Path(name).name != name or not name.startswith('snapshot-') or not name.endswith('.zip'):
            raise ValueError('Unexpected archive filename: ' + name)
        target = root / name
        if target.exists():
            if digest(target) != archive['sha256']:
                raise RuntimeError('Existing archive differs; preserve it separately before retrying: ' + name)
            print('Already verified:', name)
            continue
        temporary = root / (name + '.part')
        print('Downloading:', name, flush=True)
        request = Request(RELEASE + quote(name), headers={'User-Agent': 'prolacata-snapshot-restore'})
        with urlopen(request, timeout=60) as source, temporary.open('wb') as output:
            for block in iter(lambda: source.read(1024 * 1024), b''):
                output.write(block)
        if temporary.stat().st_size != archive['bytes'] or digest(temporary) != archive['sha256']:
            raise RuntimeError('Downloaded archive failed integrity verification: ' + name)
        temporary.replace(target)
        print('Verified:', name, flush=True)
    print('All archives available. Next: python restore_snapshot.py --verify-only')

if __name__ == '__main__':
    main()
