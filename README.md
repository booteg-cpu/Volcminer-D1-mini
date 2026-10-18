# Volcminer D1 mini — experimental fan control fix

[中文说明](README.zh-CN.md)

An unofficial binary patch for the **D1 Mini / D1 Mini Pre Ethernet** firmware dated **2025-11-10 13:22:38**. It addresses two fan-controller defects reproduced by executing the original ARM instructions in an emulator.

## What was fixed

1. **Fan PWM stuck at a previously learned minimum.** During sustained cooling, the original controller decrements PWM but can immediately clamp it back to a stale learned lower bound. The patch lets that bound decrease with a confirmed cooling step instead of overwriting the newly reduced PWM.
2. **Failure to leave maximum fan duty after an emergency transition from 99%.** The original controller saves the previous duty when entering 100% and restores `saved + 1` after cooling. A saved value of 99 therefore restores 100 indefinitely along that path. The patch restores `saved` itself, allowing the normal cooling algorithm to continue reducing duty.

The patch changes **three ARM instructions, totaling 10 differing bytes**, in `/usr/bin/cgminer`. It does not change the configured frequency, voltage, memory parameter, pools, temperature thresholds, cooling delay or cooling step. Forced protective 100% operation is retained; this does not mean every protection path has been validated on hardware.

## Download

[Download the experimental firmware](EXPERIMENTAL_D1-MINI_20251110_fanfix.tar.gz?raw=true)

SHA-256:

```text
2b9c6699571902c70a5b659d33224a1fb55a65cbf5f5a35bb500948a647e9b56
```

Use only with the matching D1 Mini hardware and base firmware. Back up the device configuration and have a recovery method before updating. The original compile-time version string is preserved, so identify this archive by its checksum. Manufacturer support page: https://volcminer.com/TechnicalSupport

## Validation and limitations

- All **16 ARM emulation tests pass** on the patched binary. The original binary reproduces the stale-floor and `99 → 100 → 100` failures.
- Packaging verification confirms that the firmware contains the exact tested binary. Other archive components are unchanged; CPIO metadata is preserved and U-Boot checksums are recalculated.
- Uploaded through the standard web updater to **one D1 Mini Pre Ethernet on 2026-10-18**. Both boards started and mining resumed.
- During the short hardware check, fan PWM decreased from 50 to 44 and later increased to 52 at a logged temperature of 65 °C. Subsequent dashboard samples showed approximately **2640–2670 RPM**, **61/60 °C PCB temperatures**, and **2.21–2.33 GH/s** with zero rejected shares at those readings.
- Startup fan warnings occurred, followed by `check_fan_speed OK`; one additional early fan error was logged. No later fan-error recurrence appeared in the inspected current log.

**Long-term reliability and elimination of the user's intermittent incident are not yet established.** The emergency-temperature scenario was not deliberately triggered on hardware. The installed device binary was not independently read back and hashed. The evidence confirms the software defects and short-term operation, not a guarantee for every cause of maximum fan speed.

## Reproduce the patch and tests

Use Python 3.10+ and the exact original vendor archive. The scripts run offline and never connect to or flash a miner.

```sh
python -m pip install -r requirements.txt
# Place upgrade_altcoin_VOLCMiner_rootfs_D1-MINI-2025-11-10-13-22-38.tar.gz here.
python prepare_original.py
python build_fan_candidate.py
python package_candidate.py
python verify_release.py
```

`prepare_original.py` validates the original archive and extracts only the original cgminer payload. `patch.json` lists the exact instruction edits and binary hashes. The packaging script generates a fresh archive; its gzip timestamp can make its archive hash differ from the published download even when the patched cgminer is identical. Its generated metadata describes an offline build; the physical-test observations are documented above.

Original archive SHA-256:
`5569cf7ae10df4550b61e59f3060b1ca67bde0551d446a7ea747c3f3bda155b3`

Original cgminer SHA-256:
`44550a0d560ee08a65c26b4481e680e4fa6bffbee85b0bfa4e29b0f2a26941dd`

Patched cgminer SHA-256:
`b800274a58fb37e886a06afce83ee0404e404ef77b76b8f20db06ed28683709a`

The vendor firmware remains third-party software. This repository does not claim ownership of the vendor components and is not an official Volcminer release.

## Donations

If this work helps you, voluntary donations are welcome. Use the correct network.

- **TRX (TRON):** `TBhFJKbh7E7o2ezh3x8RwJiAoPVKF94aVw`
- **ETH (Ethereum):** `0x0cAd5052B15b06aF62140e329A6684FaC27fB4C0`
- **BTC (Bitcoin):** `bc1qprxtn8j6y7adjnc0vw2jgnyj48eg39y65phfr2`
- **SOL (Solana):** `CCHEzR6hVU3JigCGUdB278gGc2L21Vu2smQZHiNoQuCY`
