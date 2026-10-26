# SukiSU Ultra v4.2.1-r2 (41079)

本次统一 Release 使用 tag `v4.2.1-r2-41079`，收录通用 GKI LTS 与 MuMu 1.9.9 Linux 4.19.195 专用产物。两组产物均固定使用 SukiSU Ultra `v4.2.1-r2 (41079)`，不是旧版 `41050`，也不跟随上游未来提交自动漂移。

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

## MuMu 1.9.9 专用 Linux 4.19.195

MuMu 产物使用同一 SukiSU Ultra `r2 41079` 与 UAPI `6`，但属于针对 MuMu 私有内核 ABI 构建的非 GKI 产物，不能刷入普通 GKI 设备。统一 Release 中以 `mumu` 或 `MuMu` 文件名明确隔离：

| 文件 | 用途 |
| --- | --- |
| `Image-mumu-1.9.9-4.19.195-sukisu-kpm-susfs-full` | 最终 Full Image，内置 SukiSU 41079、KPM 与 SUSFS v2.3.0 |
| `MuMu-1.9.9-4.19.195-SukiSU-Full-HostInstaller.zip` | macOS MuMu 宿主安装与恢复包，内含最终 Full Image |
| `SukiSU_v4.2.1-r2_41079-release-mumu.apk` | MuMu 配套的同源 UAPI 6 管理器，应用名与包名仍保持上游原值 |
| `Zygisk-Next-MuMu-Compat-v1.0.0.zip` | MuMu kernel-domain PID 1 所需的 Zygisk Next 兼容层，不替代官方 Zygisk Next ZIP |
| `Image-mumu-1.9.9-4.19.195-sukisu-r2-kpm` | 历史基础 KPM Image |
| `kernelsu-mumu-1.9.9-4.19.195-r2.ko` | 历史 SukiSU LKM |

最终 Full Image 来自 [run 40229027977](https://github.com/LOVECHEN/GKI_KernelSU_SUSFS/actions/runs/40229027977)，管理器来自 [run 40224422243](https://github.com/LOVECHEN/GKI_KernelSU_SUSFS/actions/runs/40224422243)，宿主安装包来自 [run 40231284954](https://github.com/LOVECHEN/GKI_KernelSU_SUSFS/actions/runs/40231284954)。运行验收已确认 SukiSU Built-in、KPM 3337、SUSFS v2.3.0、Zygisk Next 1.5.2 和 LSPosed 2.2.1 工作。

## AndroMeld 边界

Release 中名称含 `2026-03` 的 `6.12.74-android16` 包是 AndroMeld 精确原版兼容产物，继续固定 SukiSU Ultra `41050`，并保持 SUSFS、NoMount、BBG、Networking、DroidSpaces、NTSync、Ptrace、Unicode、BPF 和 Performance 全部关闭。它们没有被本次通用 GKI 更新覆盖。

因此，Release 同时保留三个 SukiSU 管理器 APK：

- `SukiSU_v4.2.1-r2_41079-release.apk`：配套本次通用 GKI LTS 产物。
- `SukiSU_v4.2.1-r2_41079-release-mumu.apk`：配套 MuMu 1.9.9 Linux 4.19.195 专用产物。
- `SukiSU_v4.2.1-r1_41050-release.apk`：配套 AndroMeld 精确原版兼容产物。
