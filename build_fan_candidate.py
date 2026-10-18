"""Reproducible offline candidate. Never connects to or flashes a miner."""
import pathlib, hashlib, json
ROOT = pathlib.Path(__file__).resolve().parent
EXPECTED = '5569cf7ae10df4550b61e59f3060b1ca67bde0551d446a7ea747c3f3bda155b3'
archive = ROOT / 'upgrade_altcoin_VOLCMiner_rootfs_D1-MINI-2025-11-10-13-22-38.tar.gz'
assert hashlib.sha256(archive.read_bytes()).hexdigest() == EXPECTED
binary = bytearray((ROOT / 'rootfs/usr/bin/cgminer').read_bytes())
assert hashlib.sha256(binary).hexdigest() == '44550a0d560ee08a65c26b4481e680e4fa6bffbee85b0bfa4e29b0f2a26941dd'
edits = [
    # The learned floor follows a confirmed, cooler 1-point PWM decrement.
    (0x893a4, '0230a0c1', '843084c5', 'movgt r3,r2 -> strgt r3,[r4,#0x84]'),
    # Do not restore the stale floor over the newly reduced current PWM.
    (0x893a8, 'cc2186c5', '0000a0e1', 'strgt r2,[r6,#0x1cc] -> nop'),
    # Restore the pre-emergency PWM itself: 99+1 would remain in the 100% state.
    (0x89774, '010080e2', '0000a0e1', 'add r0,r0,#1 -> nop (restore backup without increment)'),
]
for addr, old, new, desc in edits:
    offset = addr - 0x8000
    assert binary[offset:offset+4] == bytes.fromhex(old), hex(addr)
    binary[offset:offset+4] = bytes.fromhex(new)
out = ROOT / 'candidate'
out.mkdir(exist_ok=True)
(out / 'cgminer').write_bytes(binary)
(out / 'patch.json').write_text(json.dumps({
    'status':'EXPERIMENTAL - ARM emulation only; no physical miner validation',
    'upstream_archive_sha256':EXPECTED,
    'original_binary_sha256':hashlib.sha256((ROOT/'rootfs/usr/bin/cgminer').read_bytes()).hexdigest(),
    'candidate_binary_sha256':hashlib.sha256(binary).hexdigest(),
    'edits':[dict(address=hex(a),before=b,after=c,description=d) for a,b,c,d in edits],
},indent=2))
print('Created offline candidate:', out / 'cgminer')
