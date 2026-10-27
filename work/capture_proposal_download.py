import pathlib,time,zipfile,subprocess,sys
downloads=pathlib.Path(r'C:\Users\evant\Downloads')
target=pathlib.Path('outputs/facility_dataset/annotation_audit/kaggle_output.zip')
snapshot=target.with_suffix('.partial.zip')
last=0
for _ in range(1500):
    candidates=list(downloads.glob('Unconfirmed *.crdownload'))
    if candidates:
        p=max(candidates,key=lambda p:p.stat().st_mtime)
        try:
            size=p.stat().st_size
            if size>last:
                data=p.read_bytes();snapshot.write_bytes(data);last=len(data)
                try:
                    with zipfile.ZipFile(snapshot) as z:
                        names=[i for i in z.infolist() if i.filename.startswith('annotation_proposals/')]
                        if len(names)==3460 and z.testzip() is None:
                            target.write_bytes(data);print('Captured complete CRC-checked ZIP',len(data),flush=True);break
                except zipfile.BadZipFile:pass
        except FileNotFoundError:pass
    elif last:
        print('Download left temporary location; processing captured snapshot',last,flush=True);break
    time.sleep(.2)
if snapshot.exists():subprocess.run([sys.executable,'work/read_partial_proposal_zip.py',str(snapshot)],check=True)
