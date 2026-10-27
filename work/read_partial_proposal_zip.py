"""Read only complete, CRC-verified JSON entries from an active ZIP download."""
import pathlib,struct,zlib,sys
p=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else pathlib.Path(r'C:\Users\evant\Downloads\Unconfirmed 942925.crdownload')
out=pathlib.Path('outputs/facility_dataset/annotation_audit/raw')
blob=p.read_bytes();pos=0;count=0
while blob[pos:pos+4]==b'PK\x03\x04':
    if pos+30>len(blob):break
    _,version,flags,method,tm,dt,crc,cs,us,n,e=struct.unpack_from('<IHHHHHIIIHH',blob,pos)
    name=blob[pos+30:pos+30+n].decode('utf8');start=pos+30+n+e
    if method!=8:break
    d=zlib.decompressobj(-15)
    try:content=d.decompress(blob[start:])
    except zlib.error:break
    if not d.eof:break
    end=len(blob)-len(d.unused_data)
    if flags&8:
        desc=end+4 if blob[end:end+4]==b'PK\x07\x08' else end
        if desc+12>len(blob):break
        crc,cs,us=struct.unpack_from('<III',blob,desc);pos=desc+12
    else:pos=end
    assert zlib.crc32(content)==crc and len(content)==us
    if name.startswith('annotation_proposals/') and name.endswith('.json'):
        target=out/name
        assert target.resolve().is_relative_to(out.resolve())
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(content);count+=1
print('CRC-verified complete proposal entries available:',count)
