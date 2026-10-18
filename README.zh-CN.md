# Volcminer D1 mini — 实验性风扇控制修复

[English](README.md)

本项目为 **D1 Mini / D1 Mini Pre Ethernet** 的 **2025-11-10 13:22:38** 版本固件提供非官方二进制补丁。通过在模拟器中执行原始 ARM 指令，复现并修复了两个风扇控制问题。

## 修复内容

1. **PWM 被旧的自适应下限锁住。** 持续降温时，原控制器虽然尝试降低 PWM，却可能立即将其限制回之前记录的下限。补丁使该下限随确认后的降速步骤一起降低，不再覆盖刚刚降低的 PWM。
2. **从 99% 进入紧急全速后无法退出 100%。** 原代码在进入 100% 前保存 PWM，冷却后恢复为 `保存值 + 1`。如果保存的是 99，恢复结果仍为 100，此路径会不断重复。补丁直接恢复保存值，让正常的降温调速逻辑继续工作。

仅修改 `/usr/bin/cgminer` 中的 **3 条 ARM 指令，共 10 个不同字节**。配置的频率、电压、内存参数、矿池、温度阈值、降速延时和降速步长均未修改。强制保护性全速机制仍保留，但这并不代表所有保护路径都已完成实机验证。

## 下载

[下载实验性固件](EXPERIMENTAL_D1-MINI_20251110_fanfix.tar.gz?raw=true)

SHA-256：

```text
2b9c6699571902c70a5b659d33224a1fb55a65cbf5f5a35bb500948a647e9b56
```

仅适用于匹配的 D1 Mini 硬件及基础固件。更新前请备份配置，并准备恢复方法。编译时间版本字符串保持原样，因此应通过校验值确认此固件。厂商支持页面：https://volcminer.com/TechnicalSupport

## 验证结果与限制

- 补丁通过全部 **16 项 ARM 模拟测试**；原始程序可复现旧下限锁定和 `99 → 100 → 100` 问题。
- 打包校验确认固件内包含经过测试的同一二进制文件。其他组件保持不变，保留 CPIO 元数据，并重新计算 U-Boot 校验值。
- **2026-10-18** 已通过标准网页更新功能安装到 **一台 D1 Mini Pre Ethernet**，两块算力板正常启动并恢复挖矿。
- 短时间实机观察中，PWM 从 50 降到 44，随后在日志温度达到 65 °C 时升至 52。后续状态页面显示风扇约 **2640–2670 转/分**、PCB 温度 **61/60 °C**、算力约 **2.21–2.33 GH/s**，相应采样时拒绝份额为 0。
- 启动时出现过风扇警告，之后显示 `check_fan_speed OK`；启动早期另有一次风扇错误。所检查的当前日志中未发现后续同类错误再次出现。

**尚未证明长期稳定性，也不能确认用户遇到的偶发故障已彻底消失。** 未在实机上故意触发紧急高温场景，也未从设备回读并校验已安装的程序。当前证据确认了软件缺陷及短期运行情况，不能保证解决所有导致风扇全速的问题。

## 复现方法

需要 Python 3.10+ 及完全匹配的厂商原始固件。脚本离线运行，不连接矿机，也不执行刷机。

```sh
python -m pip install -r requirements.txt
# 将 upgrade_altcoin_VOLCMiner_rootfs_D1-MINI-2025-11-10-13-22-38.tar.gz 放在此目录。
python prepare_original.py
python build_fan_candidate.py
python package_candidate.py
python verify_release.py
```

`prepare_original.py` 校验原始固件，并只提取 cgminer。`patch.json` 记录准确的指令修改和程序校验值。重新打包时，gzip 时间戳可能导致压缩包校验值与下载版本不同，即使补丁后的 cgminer 完全一致。脚本生成的元数据描述离线构建，实机验证情况以本说明为准。

原始固件 SHA-256：
`5569cf7ae10df4550b61e59f3060b1ca67bde0551d446a7ea747c3f3bda155b3`

原始 cgminer SHA-256：
`44550a0d560ee08a65c26b4481e680e4fa6bffbee85b0bfa4e29b0f2a26941dd`

补丁后 cgminer SHA-256：
`b800274a58fb37e886a06afce83ee0404e404ef77b76b8f20db06ed28683709a`

厂商固件属于第三方软件。本项目不主张拥有厂商组件的所有权，也不是 Volcminer 官方发布。

## 捐赠

如果本项目对您有帮助，欢迎自愿捐赠。请确认使用正确的网络。

- **TRX（TRON）：** `TBhFJKbh7E7o2ezh3x8RwJiAoPVKF94aVw`
- **ETH（Ethereum）：** `0x0cAd5052B15b06aF62140e329A6684FaC27fB4C0`
- **BTC（Bitcoin）：** `bc1qprxtn8j6y7adjnc0vw2jgnyj48eg39y65phfr2`
- **SOL（Solana）：** `CCHEzR6hVU3JigCGUdB278gGc2L21Vu2smQZHiNoQuCY`
