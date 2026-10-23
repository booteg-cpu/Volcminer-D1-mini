# Volcminer D1 mini — experimental fan fix and LED controls

[中文说明](README.zh-CN.md)

Unofficial experimental firmware for **D1 Mini / D1 Mini Pre Ethernet**, based on vendor firmware **2025-11-10 13:22:38**. It includes two fan-controller fixes and independent LED controls with settings that survive reboot.

## What was fixed

1. **Fan PWM stuck at a previously learned minimum.** During sustained cooling, the original controller decrements PWM but can immediately clamp it back to a stale learned lower bound. The patch lets that bound decrease with a confirmed cooling step instead of overwriting the newly reduced PWM.
2. **Failure to leave maximum fan duty after an emergency transition from 99%.** The original controller saves the previous duty when entering 100% and restores `saved + 1` after cooling. A saved value of 99 therefore restores 100 indefinitely along that path. The patch restores `saved` itself, allowing the normal cooling algorithm to continue reducing duty.

It does not change the configured frequency, voltage, memory parameter, pools, temperature thresholds, cooling delay or cooling step. Forced protective 100% operation is retained; this does not mean every protection path has been validated on hardware.

## LED controls

Two switches appear to the left of the language selector, styled to match the Volcminer interface:

- **ASIC LED** controls only the blinking green status indicator. **Off** stops green blinking; **On** restores normal automatic blinking. The red alarm indicator remains automatic. Blue and yellow indicators keep their normal event-driven behavior.
- **Ethernet LED** switches the Ethernet port indicators on or off without disabling the network connection.

Both settings are saved and automatically restored after reboot. LED switching does not restart mining or change mining settings.

## Download

[Download the experimental firmware with LED controls](https://github.com/booteg-cpu/Volcminer-D1-mini/releases/download/v2025.11.10-fanfix-led.1/EXPERIMENTAL_D1-MINI_20251110_fanfix_led.tar.gz)

[Release notes (English / 中文)](https://github.com/booteg-cpu/Volcminer-D1-mini/releases/tag/v2025.11.10-fanfix-led.1)

SHA-256:

```text
e0f29ac3db875163aa1560012c66983f8f44b6689787368b9c300ac6493c64cd
```

Use only with the matching D1 Mini hardware and base firmware. Back up the device configuration and have a recovery method before updating. The original compile-time version string is preserved, so identify this archive by its checksum. Manufacturer support page: https://volcminer.com/TechnicalSupport

## Validation and limitations

- All **16 ARM emulation tests pass** on the patched binary. The original binary reproduces the stale-floor and `99 → 100 → 100` failures.
- Uploaded through the standard web updater to **one D1 Mini Pre Ethernet on 2026-10-18**. Both boards started and mining resumed.
- During the short hardware check, fan PWM decreased from 50 to 44 and later increased to 52 at a logged temperature of 65 °C. Subsequent dashboard samples showed approximately **2640–2670 RPM**, **61/60 °C PCB temperatures**, and **2.21–2.33 GH/s** with zero rejected shares at those readings.
- Startup fan warnings occurred, followed by `check_fan_speed OK`; one additional early fan error was logged. No later fan-error recurrence appeared in the inspected current log.

- The LED build was installed and reboot-tested on the same device on **2026-10-23**. The written root filesystem image was read back and verified before reboot. Both switches worked after reboot, and the owner physically confirmed that the saved Off settings were restored. Mining continued during LED switching, with accepted shares increasing and the miner process remaining running. Final readings were approximately **2.23 GH/s**, **55/54 °C PCB temperatures**, **2970/2970 RPM**, and **278 accepted / 0 rejected shares**. These are point-in-time readings, not guaranteed performance. Startup power-read and fan warnings occurred before normal operation resumed.

**Long-term reliability and elimination of the user's intermittent incident are not yet established.** The emergency-temperature scenario was not deliberately triggered on hardware. Validation covers one device; the evidence confirms the software defects and observed operation, not a guarantee for every cause of maximum fan speed.

## Donations

If this work helps you, voluntary donations are welcome. Use the correct network.

- **TRX (TRON):** `TBhFJKbh7E7o2ezh3x8RwJiAoPVKF94aVw`
- **ETH (Ethereum):** `0x0cAd5052B15b06aF62140e329A6684FaC27fB4C0`
- **BTC (Bitcoin):** `bc1qprxtn8j6y7adjnc0vw2jgnyj48eg39y65phfr2`
- **SOL (Solana):** `CCHEzR6hVU3JigCGUdB278gGc2L21Vu2smQZHiNoQuCY`
