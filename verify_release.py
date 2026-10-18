import pathlib, sys, subprocess, tarfile, gzip, hashlib, json
ROOT=pathlib.Path(__file__).resolve().parent
results={}
for name,target in [('original','rootfs/usr/bin/cgminer'),('candidate','candidate/cgminer')]:
    result=subprocess.run([sys.executable,str(ROOT/'test_fan.py'),str(ROOT/target)],capture_output=True,text=True)
    (ROOT/'candidate'/f'tests-{name}.txt').write_text(result.stdout+result.stderr,encoding='utf-8')
    results[name]=result.returncode
    if name=='original':
        assert result.returncode==1
        assert 'test_cooling_escapes_stale_floor' in result.stderr
        assert 'AssertionError: 80 != 79' in result.stderr
        assert 'test_emergency_from_99_escapes_maximum_when_cooled' in result.stderr
        assert 'AssertionError: 100 != 99' in result.stderr
    else:
        assert result.returncode==0,result.stderr
        assert 'Ran 16 tests' in result.stderr
metadata=json.loads((ROOT/'candidate/package-verification.json').read_text())
release=ROOT/'candidate'/metadata['archive']
assert hashlib.sha256(release.read_bytes()).hexdigest()==metadata['sha256']
with tarfile.open(release,'r:gz') as a:
    image=a.extractfile('./initramfs.bin.SD').read()
cpio=gzip.decompress(image[64:])
pos=0
found=False
while pos+110<=len(cpio):
    hdr=cpio[pos:pos+110]
    fields=[int(hdr[i:i+8],16) for i in range(6,110,8)]
    name=cpio[pos+110:pos+110+fields[11]-1].decode()
    pos=(pos+110+fields[11]+3)&~3
    if name.lstrip('./')=='usr/bin/cgminer':
        assert cpio[pos:pos+fields[6]]==(ROOT/'candidate/cgminer').read_bytes()
        found=True
        break
    if name=='TRAILER!!!':
        break
    pos=(pos+fields[6]+3)&~3
assert found
print('PASS: original reproduces floor and 99->100 latch failures')
print('PASS: candidate passes all 16 ARM emulator tests')
print('PASS: packaged firmware contains the exact tested candidate binary')
print('SHA256:',metadata['sha256'])
