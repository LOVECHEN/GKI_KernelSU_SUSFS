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

- KPM
- SUSFS
- NoMount
- Baseband Guard
- Networking
- DroidSpaces
- NTSync
- Ptrace Leak Fix
- Unicode Fix
- BPF

Performance 补丁保持关闭。该 Full 功能集同样用于 AndroMeld `6.12.74-android16-2026-03` 的 SukiSU Ultra 精确 stock-config 产物。

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

GitHub Actions 最终构建记录：[run 40293417133](https://github.com/LOVECHEN/GKI_KernelSU_SUSFS/actions/runs/40293417133)。7 个内核 job 全部成功，构建摘要均记录固定 SukiSU 提交 `a864d15ab8984c15bf585fb9e4dfbc6ccc8aaee1`、版本号 `41079`、UAPI `6` 和 SUSFS `v2.3.0`；workflow 同时对最终 `.config` 的 `CONFIG_KPM=y` 做失败即终止校验。

每个通用 GKI 目标同时提供同一份已验证 `Image` 的四种安装格式：

- `*-AnyKernel3.zip`：通过 Kernel Flasher、Recovery 或已有 Root 环境刷入。
- `*-boot.img`：未压缩 `Image` 封装的 Android boot image。
- `*-boot-gz.img`：gzip `Image` 封装的 Android boot image。
- `*-boot-lz4.img`：legacy LZ4 `Image` 封装的 Android boot image。

三种 boot image 都使用 boot header v4，并写入 64 MiB boot 分区约束与 AVB hash footer。Android 12 / 5.10 额外复用 Google certified GKI boot 的 ramdisk；其他版本沿用 GKI v4 的独立 `vendor_boot` 布局。正式仓库使用 GitHub Secret 中固定的 AVB RSA-2048 密钥，fork 未配置该 Secret 时会生成仅限该次构建的临时密钥，因此仍能完成构建。

7 个 LTS AnyKernel 与 21 个 boot image 均由最终 [GitHub Actions run 40293417133](https://github.com/LOVECHEN/GKI_KernelSU_SUSFS/actions/runs/40293417133) 重新生成并替换旧资产；Release 的 `SHA256SUMS` 已重新生成，覆盖除校验表自身外的全部资产。

## MuMu 1.9.9 专用 Linux 4.19.195

MuMu 产物使用同一 SukiSU Ultra `r2 41079` 与 UAPI `6`，但属于针对 MuMu 私有内核 ABI 构建的非 GKI 产物，不能刷入普通 GKI 设备。统一 Release 中以 `mumu` 或 `MuMu` 文件名明确隔离：

| 文件 | 用途 |
| --- | --- |
| `Image-mumu-1.9.9-4.19.195-sukisu-kpm-susfs-full` | 最终 Full Image，内置 SukiSU 41079、KPM 与 SUSFS v2.3.0 |
| `MuMu-1.9.9-4.19.195-SukiSU-Full-HostInstaller.zip` | macOS MuMu 宿主安装与恢复包，内含最终 Full Image |
| `SukiSU_v4.2.1-r2_41079-release-mumu.apk` | MuMu 配套的同源 UAPI 6 管理器，应用名与包名仍保持上游原值 |
| `Image-mumu-1.9.9-4.19.195-sukisu-r2-kpm` | 历史基础 KPM Image |
| `kernelsu-mumu-1.9.9-4.19.195-r2.ko` | 历史 SukiSU LKM |

最终 Full Image 来自 [run 40229027977](https://github.com/LOVECHEN/GKI_KernelSU_SUSFS/actions/runs/40229027977)，管理器来自 [run 40224422243](https://github.com/LOVECHEN/GKI_KernelSU_SUSFS/actions/runs/40224422243)，宿主安装包来自 [run 40231284954](https://github.com/LOVECHEN/GKI_KernelSU_SUSFS/actions/runs/40231284954)。运行验收已确认 SukiSU Built-in、KPM 3337、SUSFS v2.3.0、Zygisk Next 1.5.2 和 LSPosed 2.2.1 工作。

## AndroMeld 精确原版配置

Release 中名称含 `2026-03` 的 `6.12.74-android16` 包是 AndroMeld 精确原版配置产物。SukiSU Ultra 版本现在同样固定为 `v4.2.1-r2 (41079)` / UAPI `6`，并与通用 Full 功能集对齐：启用 KPM、SUSFS、NoMount、BBG、Networking、DroidSpaces、NTSync、Ptrace、Unicode 和 BPF。Performance 仍关闭，因为它在通用 Full 配置中也是显式 opt-in，并非 AndroMeld 特例。

最终产物来自 [workflow run 40295417701](https://github.com/LOVECHEN/GKI_KernelSU_SUSFS/actions/runs/40295417701)，其完整内核编译与最终配置校验成功；发布的 `6.12.74-android16-2026-03-SukiSU-Ultra-AnyKernel3.zip` SHA-256 为 `8f38a6daad2cb9273f6fbe8eb9e943a2e15eb52741a12a88bca93abaec180043`。

之前的 `41050 + 全部可选功能关闭` 是为定位显示唤醒问题制作的最小诊断 profile，不是 stock config 或外置模块 ABI 强制的限制。正式 Release 不再保留这个错误边界。

AndroMeld 精确原版与 MuMu 4.19.195 都由宿主直接加载 raw `Image`，不属于标准 Android 设备的通用 boot 分区布局，因此不会生成名称看似可刷、实际不适用的 `boot*.img`。

因此，Release 保留两个 SukiSU 管理器 APK：

- `SukiSU_v4.2.1-r2_41079-release.apk`：配套通用 GKI LTS 与 AndroMeld `6.12.74` 精确 stock-config 产物。
- `SukiSU_v4.2.1-r2_41079-release-mumu.apk`：配套 MuMu 1.9.9 Linux 4.19.195 专用产物。
