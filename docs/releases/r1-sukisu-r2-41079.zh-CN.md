# SukiSU Ultra v4.2.1-r2 (41079)

本次 `r1` Release 的通用 GKI LTS 产物固定使用 SukiSU Ultra `v4.2.1-r2 (41079)`，不是旧版 `41050`，也不跟随上游未来提交自动漂移。

## 固定版本

| 组件 | 版本或提交 |
| --- | --- |
| SukiSU Ultra 内核端 | `a864d15ab8984c15bf585fb9e4dfbc6ccc8aaee1` |
| SukiSU Ultra 管理器 | `5b4835bc20a528fd06b2a6c6571a35f9b61cff42` |
| 管理器 APK | `SukiSU_v4.2.1-r2_41079-release.apk` |
| SUSFS | `v2.3.0` |
| UAPI | `6` |

## 通用 GKI 功能

7 个 LTS 目标均启用：

- SUSFS
- NoMount
- Baseband Guard
- Networking
- DroidSpaces
- NTSync
- Ptrace Leak Fix
- Unicode Fix
- BPF

Performance 补丁保持关闭。上述功能仅适用于本节列出的通用 GKI LTS 产物。

## 构建矩阵

| Android | 内核 | 产物 |
| --- | --- | --- |
| 12 | `5.10.272` | `5.10.272-android12-lts-SukiSU-Ultra-AnyKernel3.zip` |
| 13 | `5.10.272` | `5.10.272-android13-lts-SukiSU-Ultra-AnyKernel3.zip` |
| 13 | `5.15.220` | `5.15.220-android13-lts-SukiSU-Ultra-AnyKernel3.zip` |
| 14 | `5.15.220` | `5.15.220-android14-lts-SukiSU-Ultra-AnyKernel3.zip` |
| 14 | `6.1.177` | `6.1.177-android14-lts-SukiSU-Ultra-AnyKernel3.zip` |
| 15 | `6.6.144` | `6.6.144-android15-lts-SukiSU-Ultra-AnyKernel3.zip` |
| 16 | `6.12.96` | `6.12.96-android16-lts-SukiSU-Ultra-AnyKernel3.zip` |

GitHub Actions 构建记录：[run 40251632106](https://github.com/LOVECHEN/GKI_KernelSU_SUSFS/actions/runs/40251632106)。7 个内核 job 全部成功，构建摘要均记录 `v4.2.1-r2-a864d15a@HEAD`、版本号 `41079` 和 SUSFS `v2.3.0`。

## AndroMeld 边界

Release 中名称含 `2026-03` 的 `6.12.74-android16` 包是 AndroMeld 精确原版兼容产物，继续固定 SukiSU Ultra `41050`，并保持 SUSFS、NoMount、BBG、Networking、DroidSpaces、NTSync、Ptrace、Unicode、BPF 和 Performance 全部关闭。它们没有被本次通用 GKI 更新覆盖。

因此，Release 同时保留两个管理器 APK：

- `SukiSU_v4.2.1-r2_41079-release.apk`：配套本次通用 GKI LTS 产物。
- `SukiSU_v4.2.1-r1_41050-release.apk`：配套 AndroMeld 精确原版兼容产物。
