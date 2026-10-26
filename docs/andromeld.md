# AndroMeld 内核构建

本仓库为当前 AndroMeld Android 运行时固定了以下目标：

| 字段 | 值 |
| --- | --- |
| 内核 release | `6.12.74-android16-6-g3ec022196c4e-ab15076761-4k` |
| GKI 系列 | `android16-6.12` |
| Linux 子版本 | `74` |
| 补丁级别 | `2026-03` |
| 页大小 | `4k` |
| kernel common commit | `3ec022196c4e9d5c1434599cdda63f622dd6f586` |

`.github/config/android16-6.12.json` 中的 `source_commit` 会进入构建矩阵，并在 Android manifest 同步后 checkout。构建因此使用精确的 `kernel/common` 提交，而不是随时间移动的月度分支顶端。

## 构建设备兼容的 Full SukiSU Ultra 内核

运行 `Build Kernels` workflow，使用以下输入：

| 输入 | 值 |
| --- | --- |
| Release Type | `CI` |
| Use cache | `false` |
| Force module version mismatch | `true` |
| Kernel Version | `6.12.x-android16` |
| OS patch level | `2026-03` |
| Page size | `4k` |
| Kernel Branding | `AndroMeld` |
| Keep KMI suffix | `true` |
| Commit mode | `verified` |
| Root Flavor | `SukiSU-Ultra` |
| SUSFS | `true` |
| NoMount | `true` |
| BBG / Networking / DroidSpaces | `true` |
| NTSync / Ptrace / Unicode / BPF | `true` |
| Performance | `false` |

`2026-03` 目标使用从 AndroMeld 原版内核提取的精确 stock config，但 stock config 只是设备配置基线，不代表必须关闭可选功能。正式 SukiSU 产物与通用 Full 配置对齐，启用 `SUSFS + NoMount + BBG + Networking + DroidSpaces + NTSync + Ptrace + Unicode + BPF`；`Performance` 与通用 Full 一样保持关闭，它从来不属于默认 Full 功能集。`allow_version_mismatch` 仍需启用，因为运行时包含按原版 release 字符串编译的外置模块。

早期为定位黑屏与显示唤醒问题，曾经人为关闭所有可选功能构建最小诊断版。那是排障手段，不是 AndroMeld 的技术限制，也不应继续作为正式 Release 配置。


`2026-03` 是设备专用目标。该 matrix 行选择从 AndroMeld 原版内核提取的 `config/andromeld-6.12.74-stock.config`（`sha256:4c065ae7247d878dc34438e61230fb4c3e4a9ce286cd585bf49db03dd7e69726`）。workflow 先把它安装为真正的 `gki_defconfig`，再叠加 SukiSU 与 Full 功能配置；同时嵌入未修改副本供 `/proc/config.gz` 使用。不要用最新通用 `kernel-6.12-gz` 配置替代，因为它属于另一个 GKI rollup，会改变数百项调度、电源、显示与 Android 配置。

原版配置引用 `protected_module_names_list`。该输入由 Google 生产构建环境提供，在公开源码提交中不存在。workflow 会在源码树中创建空占位文件，从而保留原版配置与模块 ABI；AndroMeld 构建不会编译或交付该列表中的外置内核模块。

设备兼容目标使用仓库自带的确定性目录清理，不使用依赖 apt 的第三方磁盘清理 action，避免 runner 镜像包变化导致在下载内核源码前卡住。

等价 GitHub CLI 命令：

```bash
gh workflow run main.yml \
  -R LOVECHEN/GKI_KernelSU_SUSFS \
  --ref main \
  -f release_type=CI \
  -f use_cache=false \
  -f allow_version_mismatch=true \
  -f kernel_build_version=6.12.x-android16 \
  -f os_patch_level=2026-03 \
  -f page_size=4k \
  -f brand_name=AndroMeld \
  -f keep_kmi=true \
  -f commit_mode=verified \
  -f root_flavor=SukiSU-Ultra \
  -f use_susfs=true \
  -f use_nomount=true \
  -f use_bbg=true \
  -f use_net=true \
  -f use_ds=true \
  -f use_ntsync=true \
  -f use_ptrace=true \
  -f use_unicode=true \
  -f use_bpf=true \
  -f use_perf=false \
  -f test_release_notes=false
```

早期 run `39840787113` 生成了带 SukiSU Ultra `41050-6` 的 `6.12.74-android16-6-AndroMeld`，但错误使用了通用 `6.12.18` 构建配置。Root 可以工作，Android 显示唤醒路径却失效，启动应用后运行时仍保持休眠。该 artifact 只保留为诊断记录，不得安装。run `39870151831` 用同一个固定源码与精确 AndroMeld stock config 重建，是首个完成运行时验证的 baseline。其 `Image` SHA-256 为 `7555dd3953da848e85ee6535206d64fd38060635eff96aaab5f8654b5cdd45b4`。有效结果必须满足：

- SukiSU 显示 `Built-in / Working`。
- 正常使用时 ADB 显示 `uid=2000(shell)` 与 SELinux 域 `u:r:shell:s0`。
- `/proc/modules` 中不存在 `kernelsu` 条目。
- 运行时休眠后，已安装 Android 应用仍能正常唤醒并显示。

日常使用 AndroMeld 时不要启用 SukiSU 的 `adb_root`。AndroMeld 的内部 helper 与 Fusion 窗口共用同一条 ADB transport；启用 `adb_root` 后 helper 会运行在 `u:r:ksu:s0`，唤醒请求会立即紧跟 `interactive_false`，Android 应用就会表现为空白、休眠或卡在“准备显示”。这与是否安装 Zygisk Next 和 LSPosed 无关。

如果维护期间启用了 `adb_root`，最终重启运行时前应关闭并持久化：

```bash
/data/adb/ksud feature set adb_root 0
/data/adb/ksud feature save
```

已验证的最终状态为 SukiSU `Built-in / Working`、Zygisk Next `1.5.2`、LSPosed `2.2.1 / Activated`，并使用普通 ADB shell。关闭该功能后，MT 管理器和独立 LSPosed 管理器都已通过 Fusion Host 成功打开。

同一份源码与 stock config 也在 [workflow run 39873307019](https://github.com/LOVECHEN/GKI_KernelSU_SUSFS/actions/runs/39873307019) 中成功构建 KernelSU-Next、KernelSU 和 BakaSU。这三个产物只完成构建验证，尚未在当前 AndroMeld VM 上做运行时验证。它们的 AnyKernel3 ZIP 与对应管理器 APK 与 SukiSU 产物一起发布在现有 [SukiSU Ultra v4.2.1-r2 (41079) release](https://github.com/LOVECHEN/GKI_KernelSU_SUSFS/releases/tag/v4.2.1-r2-41079) 中，不另建 release tag。当前 SukiSU 产物使用固定 `a864d15` 内核快照与 `41079` 管理器/UAPI 代际重建，旧 `41050` 管理器不再需要。

## 为每个系列构建一个当前 LTS 内核

使用 `kernel_build_version=All` 与 `os_patch_level=lts`。每个系列配置只包含一条 `lts` 记录，因此会生成 7 个内核 job，而不是构建所有历史月份。应显式选择 `SukiSU-Ultra`；`No Root` 会故意省略 Root 实现，`All (KernelSU-Next + KernelSU + BakaSU)` 则会为每个目标构建这三种 Root 实现。

如需将产物保留为 GitHub prerelease，而不是只作为会过期的 Actions artifact，请选择 `Pre-Release`：

```bash
gh workflow run main.yml \
  -R LOVECHEN/GKI_KernelSU_SUSFS \
  --ref main \
  -f release_type=Pre-Release \
  -f use_cache=true \
  -f allow_version_mismatch=true \
  -f kernel_build_version=All \
  -f os_patch_level=lts \
  -f page_size=4k \
  -f brand_name=AndroMeld \
  -f keep_kmi=true \
  -f commit_mode=latest \
  -f root_flavor=SukiSU-Ultra \
  -f use_susfs=true \
  -f use_nomount=true \
  -f use_bbg=true \
  -f use_net=true \
  -f use_ds=true \
  -f use_ntsync=true \
  -f use_ptrace=true \
  -f use_unicode=true \
  -f use_bpf=true \
  -f use_perf=false \
  -f test_release_notes=false
```

预期系列如下：

| Android common 系列 | Linux 系列 |
| --- | --- |
| `android12-5.10` | 5.10 |
| `android13-5.10` | 5.10 |
| `android13-5.15` | 5.15 |
| `android14-5.15` | 5.15 |
| `android14-6.1` | 6.1 |
| `android15-6.6` | 6.6 |
| `android16-6.12` | 6.12 |

`lts` 行跟随当前 LTS 分支顶端，因此实际解析到的数字子版本会记录在已完成 run 中，后续再次触发时可能提高。

已完成 run 中需保留：

- `*-AnyKernel3`：可刷写包内容，安装前将文件直接压到 ZIP 根目录。
- `*-BuildInfo`：精确源码 revision 与校验值。
- SukiSU Ultra 管理器 APK artifact。
- 内核 artifact 中的原始 `Image`（若存在）。
