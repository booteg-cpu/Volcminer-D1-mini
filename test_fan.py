"""Execute the vendor ARM fan routine; no miner or network access."""
import pathlib, sys, struct, unittest
ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'analysis-deps'))
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM
from unicorn.arm_const import UC_ARM_REG_SP, UC_ARM_REG_LR
from elftools.elf.elffile import ELFFile

ORIGINAL = ROOT / 'rootfs/usr/bin/cgminer'
TARGET = pathlib.Path(sys.argv.pop(1)) if len(sys.argv) > 1 and not sys.argv[1].startswith('-') else ORIGINAL
CFG, STATE, DATA = 0x1a03fc, 0x1437a0, 0x13f208

class FanMachine:
    def __init__(self, path=TARGET, pwm=80, floor=80, ceiling=100, backup=60):
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        self.uc.mem_map(0x8000, 0x1c0000)
        self.uc.mem_map(0x200000, 0x1000)
        self.uc.mem_map(0x300000, 0x100000)
        with path.open('rb') as f:
            for segment in ELFFile(f).iter_segments():
                if segment['p_type'] == 'PT_LOAD':
                    self.uc.mem_write(segment['p_vaddr'], segment.data())
        self.put(CFG+0x966, 0x200000)
        # External logging is excluded; real PWM setters and MMIO remain executed.
        self.put(0x13edfc, 0)
        self.put(0x13ee00, 0)
        self.uc.mem_write(0x14379c, b'\x00\x00')
        self.uc.mem_write(0x147f60, b'\x00')
        self.put(DATA+0x1cc, pwm)
        self.put(DATA+0x1d0, backup)
        self.put(DATA+0x1d4, ceiling)
        self.put(STATE+0x84, floor)
        self.uc.mem_write(STATE+0x88, b'\x01')
        self.uc.mem_write(CFG+0x910, bytes([pwm,pwm]))
    def put(self, addr, value):
        self.uc.mem_write(addr, struct.pack('<I',value))
    def get(self, addr):
        return struct.unpack('<I',self.uc.mem_read(addr,4))[0]
    def step(self, temp, n=1):
        self.put(CFG+0x8da,temp)
        for _ in range(n):
            self.uc.reg_write(UC_ARM_REG_SP, 0x3ff000)
            self.uc.reg_write(UC_ARM_REG_LR, 0x400000)
            self.uc.emu_start(0x89128, 0x400000, count=10000)
        return self.get(DATA+0x1cc)
    def duty(self):
        word = self.get(0x200010)
        return word & 255, (word >> 8) & 255

class FanTests(unittest.TestCase):
    def test_cooling_escapes_stale_floor(self):
        m = FanMachine()
        self.assertEqual(m.step(59,20),79)
        self.assertEqual(m.duty(),(79,79))
        self.assertEqual(m.step(58,20),78)
    def test_normal_cooling_above_floor(self):
        m=FanMachine(pwm=80,floor=50)
        self.assertEqual(m.step(59,20),79)
    def test_decrease_requires_sustained_cooling(self):
        m=FanMachine()
        self.assertEqual(m.step(59,19),80)
        self.assertEqual(m.step(60),80)
        self.assertEqual(m.step(59,19),80)
    def test_deadband_does_not_reduce_duty(self):
        for temp in range(60,65):
            with self.subTest(temp=temp):
                m=FanMachine()
                self.assertEqual(m.step(temp,40),80)
    def test_emergency_heat_full_duty(self):
        for temp in (68,75,100):
            with self.subTest(temp=temp):
                m=FanMachine()
                self.assertEqual(m.step(temp),100)
                self.assertEqual(m.duty(),(100,100))
    def test_emergency_recovery_preserved(self):
        m=FanMachine(pwm=70,floor=60)
        self.assertEqual(m.step(68),100)
        self.assertEqual(m.step(58),70)
        self.assertEqual(m.duty(),(70,70))
    def test_emergency_from_99_escapes_maximum_when_cooled(self):
        m=FanMachine(pwm=99,floor=80)
        self.assertEqual(m.step(68),100)
        self.assertEqual(m.step(58),99)
        self.assertEqual(m.step(58,20),98)
    def test_manual_mode_preserved(self):
        m=FanMachine()
        m.uc.mem_write(CFG+0x90f,b'\x01')
        m.uc.mem_write(CFG+0x910,bytes([45,55]))
        m.step(59,40)
        self.assertEqual(m.duty(),(45,55))
    def test_warming_increases_after_five_cycles(self):
        m=FanMachine()
        self.assertEqual(m.step(65,4),80)
        self.assertEqual(m.step(65),81)
        self.assertEqual(m.duty(),(81,81))
    def test_minimum_duty_preserved(self):
        m=FanMachine(pwm=10,floor=10)
        self.assertEqual(m.step(30,200),10)
        self.assertEqual(m.duty(),(10,10))
    def test_hot_and_deadband_behavior_matches_vendor(self):
        for temp in (60,61,64,65,67,68,80):
            for pwm in (30,60,80,99):
                with self.subTest(temp=temp,pwm=pwm):
                    orig=FanMachine(ORIGINAL,pwm=pwm,floor=50)
                    new=FanMachine(pwm=pwm,floor=50)
                    self.assertEqual(new.step(temp,25),orig.step(temp,25))
                    self.assertEqual(new.duty(),orig.duty())
    def test_cooling_changes_one_point_per_twenty_cycles(self):
        for pwm in (40,57,80,99):
            for temp in (55,58,59):
                with self.subTest(pwm=pwm,temp=temp):
                    m=FanMachine(pwm=pwm,floor=pwm)
                    self.assertEqual(m.step(temp,19),pwm)
                    self.assertEqual(m.step(temp),pwm-1)
                    self.assertEqual(m.duty(),(pwm-1,pwm-1))
    def test_manual_emergency_policy_matches_vendor(self):
        for temp in (30,58,65,75):
            orig=FanMachine(ORIGINAL)
            new=FanMachine()
            for m in (orig,new):
                m.uc.mem_write(CFG+0x90f,b'\x01')
                m.uc.mem_write(CFG+0x910,bytes([45,55]))
            self.assertEqual(new.step(temp,25),orig.step(temp,25))
            self.assertEqual(new.duty(),orig.duty())
    def test_fault_forces_hardware_full_duty_despite_cooling(self):
        m=FanMachine()
        m.uc.mem_write(STATE+0x75,b'\x01')
        m.step(59,20)
        self.assertEqual(m.duty(),(100,100))
    def test_startup_adaptation_disabled_matches_vendor(self):
        for temp in (20,35,45,55,59,60,65,68):
            orig=FanMachine(ORIGINAL)
            new=FanMachine()
            for m in (orig,new):
                m.uc.mem_write(STATE+0x88,b'\x00')
            self.assertEqual(new.step(temp,25),orig.step(temp,25))
            self.assertEqual(new.duty(),orig.duty())
    def test_learning_trajectory_cannot_raise_pwm_when_cooling(self):
        m=FanMachine(pwm=80,floor=0)
        m.step(65,6)
        m.step(64)
        m.step(59,21)
        m.step(60)
        m.step(65,6)
        m.step(64)
        before=m.get(DATA+0x1cc)
        self.assertEqual(before,80)
        self.assertEqual(m.step(59,20),79)

if __name__ == '__main__':
    print('Testing', TARGET)
    unittest.main(verbosity=2)
