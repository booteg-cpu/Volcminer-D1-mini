"""Build an experimental firmware archive, preserving all other vendor members."""
import pathlib, tarfile, io, gzip, struct, zlib, hashlib, json
ROOT=pathlib.Path(__file__).resolve().parent
source=ROOT/'upgrade_altcoin_VOLCMiner_rootfs_D1-MINI-2025-11-10-13-22-38.tar.gz'
out=ROOT/'candidate/EXPERIMENTAL_D1-MINI_20251110_fanfix.tar.gz'
original=(ROOT/'rootfs/usr/bin/cgminer').read_bytes()
patched=(ROOT/'candidate/cgminer').read_bytes()
assert len(original)==len(patched)
with tarfile.open(source,'r:gz') as archive:
    members=archive.getmembers()
    images={m.name:archive.extractfile(m).read() for m in members if m.isfile()}
    key=next(k for k in images if k.lstrip('./')=='initramfs.bin.SD')
    image=images[key]
    header=bytearray(image[:64])
    fields=struct.unpack('>7I4B32s',header)
    assert fields[0]==0x27051956 and fields[3]==len(image)-64
    assert fields[6]==zlib.crc32(image[64:])
    header[4:8]=bytes(4)
    assert fields[1]==zlib.crc32(header)
    cpio=bytearray(gzip.decompress(image[64:]))
    # Patch only the cgminer regular-file payload. Keep cpio metadata and links.
    pos=0
    changed=0
    while pos+110<=len(cpio):
        hdr=cpio[pos:pos+110]
        assert hdr[:6]==b'070701'  # newc without per-file CRC
        f=[int(hdr[i:i+8],16) for i in range(6,110,8)]
        name=cpio[pos+110:pos+110+f[11]-1].decode()
        pos=(pos+110+f[11]+3)&~3
        if name=='TRAILER!!!':
            break
        if name.lstrip('./')=='usr/bin/cgminer':
            assert cpio[pos:pos+f[6]]==original
            cpio[pos:pos+f[6]]=patched
            changed+=1
        pos=(pos+f[6]+3)&~3
    assert changed==1
    payload=gzip.compress(cpio,mtime=fields[2])
    struct.pack_into('>I',header,12,len(payload))
    struct.pack_into('>I',header,24,zlib.crc32(payload))
    struct.pack_into('>I',header,4,zlib.crc32(header))
    newimage=bytes(header)+payload
    with tarfile.open(out,'w:gz',format=tarfile.GNU_FORMAT) as dest:
        for m in members:
            if m.isfile():
                data=newimage if m.name==key else images[m.name]
                m.size=len(data)
                dest.addfile(m,io.BytesIO(data))
            else:
                dest.addfile(m)

# Independent round-trip verification of payloads and U-Boot checksums.
with tarfile.open(source,'r:gz') as a,tarfile.open(out,'r:gz') as b:
    assert a.getnames()==b.getnames()
    for m in a.getmembers():
        other=b.getmember(m.name)
        for attr in ('mode','uid','gid','uname','gname','type','linkname','mtime'):
            assert getattr(m,attr)==getattr(other,attr),(m.name,attr)
        if not m.isfile():
            continue
        left,right=a.extractfile(m).read(),b.extractfile(m.name).read()
        if m.name!=key:
            assert left==right,m.name
        else:
            h=bytearray(right[:64])
            stored=struct.unpack_from('>I',h,4)[0]
            h[4:8]=bytes(4)
            assert stored==zlib.crc32(h)
            assert struct.unpack_from('>I',h,24)[0]==zlib.crc32(right[64:])
            before,after=gzip.decompress(left[64:]),gzip.decompress(right[64:])
            diffs=[i for i,(x,y) in enumerate(zip(before,after)) if x!=y]
            binary_diffs=sum(x!=y for x,y in zip(original,patched))
            assert len(before)==len(after) and len(diffs)==binary_diffs
            assert binary_diffs>0
metadata={'archive':out.name,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
          'changed_tar_member':key,'changed_arm_instructions':3,
          'changed_cpio_bytes':binary_diffs,'cpio_metadata_preserved':True,
          'uboot_header_crc_valid':True,'uboot_data_crc_valid':True,
          'hardware_tested':False}
(ROOT/'candidate/package-verification.json').write_text(json.dumps(metadata,indent=2))
print(json.dumps(metadata,indent=2))
