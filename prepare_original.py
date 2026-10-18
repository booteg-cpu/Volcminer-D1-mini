"""Validate vendor input and extract only cgminer; no unsafe archive extraction."""
import gzip
import hashlib
import pathlib
import tarfile

ROOT = pathlib.Path(__file__).resolve().parent
source = ROOT / 'upgrade_altcoin_VOLCMiner_rootfs_D1-MINI-2025-11-10-13-22-38.tar.gz'
assert hashlib.sha256(source.read_bytes()).hexdigest() == '5569cf7ae10df4550b61e59f3060b1ca67bde0551d446a7ea747c3f3bda155b3'
with tarfile.open(source, 'r:gz') as archive:
    member = next(m for m in archive.getmembers() if m.name.lstrip('./') == 'initramfs.bin.SD')
    cpio = gzip.decompress(archive.extractfile(member).read()[64:])
pos = 0
while pos + 110 <= len(cpio):
    header = cpio[pos:pos + 110]
    assert header[:6] == b'070701'
    fields = [int(header[i:i + 8], 16) for i in range(6, 110, 8)]
    name = cpio[pos + 110:pos + 110 + fields[11] - 1].decode()
    pos = (pos + 110 + fields[11] + 3) & ~3
    if name == 'TRAILER!!!':
        break
    if name.lstrip('./') == 'usr/bin/cgminer':
        binary = cpio[pos:pos + fields[6]]
        assert hashlib.sha256(binary).hexdigest() == '44550a0d560ee08a65c26b4481e680e4fa6bffbee85b0bfa4e29b0f2a26941dd'
        target = ROOT / 'rootfs/usr/bin/cgminer'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(binary)
        print('Validated original cgminer:', target)
        break
    pos = (pos + fields[6] + 3) & ~3
else:
    raise ValueError('cgminer not found')
assert (ROOT / 'rootfs/usr/bin/cgminer').is_file()
