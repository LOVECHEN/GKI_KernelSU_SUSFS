# MuMuPlayer 1.9.9 / Linux 4.19.195 SukiSU 构建记录（WIP）

本文记录 MuMuPlayer 1.9.9 私有 `4.19.195` 内核接入 SukiSU Ultra、LKM 与 KPM 的当前状态。MuMu 是修改过私有 ABI 的非 GKI 内核，不能伪装成 Android 12 / 5.10 的通用 GKI 矩阵项。

## 构建原则

- 所有实际内核编译均由 GitHub Actions 执行，本机不编译内核。
- 本机只允许编辑构建脚本、做静态检查、读取 Actions 日志和核对提交/SHA256。
- 专用入口为 `.github/workflows/mumu-1.9.9-4.19.yml`，在 GitHub Actions 中手动运行 `MuMu 1.9.9 Linux 4.19.195`。
- `target=all` 默认依次构建 LKM 与内置 KPM Image；也可用 `lkm` 或 `image` 单独构建。
- 私有 MuMu 源码通过只读 deploy key `MUMU_SOURCE_SSH_KEY` clone，不依赖 GitHub fork 关系，也不会被上游仓库删除操作同步移除。
- 每个外部输入固定到完整 commit，MuMu config 与重建的 `sched.h` 还会执行 SHA256 校验，避免上游移动导致不可复现。

## 固定版本

| 项目 | 固定版本 |
| --- | --- |
| Guest | MuMuPlayer 1.9.9 arm64 |
| 内核 | `4.19.195-android-arm64-gedae1315d023` |
| Android common 公共基线 | `60080b53629d749f14cf6981b1602de6c19dd46e` |
| MuMu 私有源码 | `LOVECHEN/mumu-neutralize@19380722db94c5b7d0a1a27304d12e69ad5629f3` |
| SukiSU Ultra | `v4.2.1-r2@d6b36700f3bd0a4c1585549b470dd30bb8774534`，管理器版本码 `41068` |
| KernelPatch 参考 | `SukiSU-Ultra/SukiSU_KernelPatch_patch@e60c6cfd5cea87cccf9adb7e4d4ba583702d443c` |
| KPM 模板参考 | `liankong233/KPM-Build-Anywhere@e26d77c8d6d38abcf7340a16a9b809660b9e78f4` |

Android common 的 `f931d3c324845b1be4337d27b565351fb581f206` 是合入 Linux 4.19.195 的 merge commit，但该点把 `ctx->rotate_necessary` 引用带回了 `kernel/events/core.c`，却没有恢复对应结构字段，直接编译会失败。其唯一直接后继 `60080b53` 的提交说明明确指出用于修复该 build breakage，因此构建固定在 `60080b53`，内核版本仍为 4.19.195。

## 上游与参考仓库

- [SukiSU KernelPatch / KPM 层](https://github.com/SukiSU-Ultra/SukiSU_KernelPatch_patch)
- [KPM-Build-Anywhere](https://github.com/liankong233/KPM-Build-Anywhere)
- [SukiSU Ultra](https://github.com/SukiSU-Ultra/SukiSU-Ultra)
- [ShirkNeko/GKI_KernelSU_SUSFS](https://github.com/ShirkNeko/GKI_KernelSU_SUSFS)
- [WildKernels/GKI_KernelSU_SUSFS](https://github.com/WildKernels/GKI_KernelSU_SUSFS)

## 目标产物

1. `kernelsu-mumu-1.9.9-4.19.195-r2.ko`：使用 MuMu 精确 config、私有 `task_struct` ABI 和完整 overlay 构建的 SukiSU LKM，配置为 `CONFIG_KSU=m`、`CONFIG_KPM=n`。
2. `Image-mumu-1.9.9-4.19.195-sukisu-r2-kpm`：内置 SukiSU 与 KPM 的 MuMu 4.19.195 Image，配置为 `CONFIG_KSU=y`、`CONFIG_KPM=y`。
3. `SHA256SUMS.txt`：同一次 Actions 构建生成的产物校验值。

`KPM-Build-Anywhere` 用于构建 KPM payload，不负责把 SukiSU 接入内核；KernelPatch/KPM 工具链仍作为独立的镜像补丁和模块开发路线保留。

## MuMu 专用输入

工作流从私有 MuMu 仓库覆盖以下内容，而不是只拿一个通用 4.19 config 编译：

- `linux-4.19.195.nemu.config`；
- 重建的 `include/linux/sched.h`，其中包含 MuMu 私有 `task_struct` 字段；
- `nemuctl`、`nemu_file_rule`、`virtual_module` 反检测实现；
- `nemu-freq`、`mumu_power`、`pagecache_limit`；
- MuMu 直接 SHA-256 实现；
- 4.19 版 `xt_qtaguid`；
- `alloc_etherdev` 的 `wlan0` 补丁。

MuMu 已启用 `CONFIG_KALLSYMS=y`、`CONFIG_KALLSYMS_ALL=y`、`CONFIG_KPROBES=y`、`CONFIG_KRETPROBES=y`、`CONFIG_HAVE_SYSCALL_TRACEPOINTS=y`、`CONFIG_EXT4_FS=y` 和 `CONFIG_MODULES=y`，并且未强制模块签名、未启用 modversions。非 GKI KPM 所需的 kallsyms 条件已经满足。

## GitHub Actions 使用方式

1. 打开仓库的 Actions 页面。
2. 选择 `MuMu 1.9.9 Linux 4.19.195`。
3. 点击 `Run workflow`。
4. `target` 选择 `all`，同时生成 LKM 与 KPM Image。
5. 构建成功后下载 `mumu-1.9.9-linux-4.19.195-sukisu-r2-all` artifact。

对应工作流：`.github/workflows/mumu-1.9.9-4.19.yml`。

构建脚本：`.github/workflows/scripts/mumu_419_builder.py`。

## 已确认约束

- MuMu 1.9.9 的基线和虚拟设备私有 ABI 是 Linux 4.19.195，不能替换成 Android 12 / 5.10 GKI。
- SukiSU 支持手动接入非 GKI 与旧内核；其 Kconfig 允许 `CONFIG_KSU=m`，因此 4.19 可以生成 `kernelsu.ko`。官方 release 未提供 4.19 LKM，不代表不能构建。
- 完整 KPM 支持使用独立的内置 Image 目标，不能把 `CONFIG_KPM=y` 塞进纯 LKM 目标冒充支持。
- MuMu 修改了 `task_struct`。即使 vermagic 一致，使用 vanilla 4.19 头文件构建的模块仍可能产生错误字段偏移，所以必须使用 MuMu 重建的 `sched.h` 和精确 config。
- SukiSU r2 在 4.19 上若出现新内核 API 调用，只能在完整 Actions 日志确认后做最小兼容层，不能凭旧版本错误列表盲改。

## Actions 实测记录

### 首轮：`40097079789`

- 私有 MuMu 源码 checkout、依赖安装、overlay、SukiSU r2 clone 与配置阶段均成功。
- 实际编译运行约 10 分钟后在 Android common 基线失败。
- 首个错误是 `kernel/events/core.c` 引用不存在的 `perf_event_context.rotate_necessary`，还没有进入 SukiSU r2 的 4.19 API 兼容错误。
- 根因是固定到了未带紧随其后的 build-fix 的 `f931d3c3` merge commit。
- 处理：Android common 固定点更新为直接修复提交 `60080b53`，继续由 GitHub Actions 重跑验证。

### 第二轮：`40098156407`

- 固定到 `60080b53` 后运行约 18 分钟，首轮的 `rotate_necessary` 错误不再出现，公共基线修复有效。
- 编译已进入 SukiSU r2 的 `drivers/kernelsu/core/init.c`。
- Linux 4.19 尚未提供 `MODULE_IMPORT_NS`；该 namespace 在 4.19 也不存在，因此兼容层对旧内核将该声明置空。
- SukiSU 为 A12/5.10 LKM 准备的 arm64 `naked` canary bootstrap 由 Clang 语义实现，但 MuMu 原版 config/工具链是 GCC 12；GCC 忽略 arm64 `naked` 并把无返回路径视为错误。
- 处理：使用 `no_stack_protector` 普通 C 包装先初始化 `__stack_chk_guard`，再调用并返回 `kernelsu_init()`；语义仍是进入带 stack protector 的主体前完成 canary 初始化。
- Actions 增加持久化 `ccache`，实际编译仍只在 GitHub 执行，后续兼容迭代复用已编对象。

### 第三轮：`40099568023`

- 第二轮的两个 `core/init.c` 错误均已越过，证明 namespace 与 GCC canary bootstrap 兼容转换有效。
- 编译进入 `drivers/kernelsu/feature/sucompat.c` 后，唯一错误为 4.19 不存在 `linux/pgtable.h`。
- `sucompat.c` 没有调用任何页表 API；`untagged_addr` 已由其现有的 `linux/mm.h` 提供，因此删除多余 include，不引入替代实现。
- 本轮生成 3904 个可缓存对象、约 0.4 GB ccache。原 `actions/cache` 在失败 job 中不保存 post cache，工作流已改为显式 `restore`/`save`，在传播编译失败前保存缓存。

### 第四轮：`40100971711`

- 已越过 `linux/pgtable.h`，唯一新错误为 4.19 不存在 `strncpy_from_user_nofault`。
- 4.19 提供语义相同的旧名称 `strncpy_from_unsafe_user`；对 r2 源码中 3 个文件的 5 处调用统一做严格计数替换。
- 显式 cache 流程验证成功：在 job 标记失败前保存了约 408.7 MB、3904 个可缓存对象，后续 Actions run 可直接复用。

### 第五轮：`40102688899`

- compiler cache 恢复成功，3923/4161 个可缓存调用命中，命中率 `94.28%`，运行时间从 22 分钟降至约 8 分钟。
- 5 处 nofault user-copy 名称回退均已通过，唯一新错误是 arm64 `patch_memory.c` 使用 4.19 不存在的 `copy_to_kernel_nofault`。
- MuMu 4.19 提供并以 GPL 导出了语义相同的旧接口 `probe_kernel_write`，因此只对 arm64 目标做严格单点替换。

### 第六轮：`40103379602`

- `probe_kernel_write` 回退已通过；compiler cache 命中 4160/4184，命中率 `99.43%`。
- 错误集中到 `infra/file_wrapper.c` 的新版 VFS/SELinux API。
- 4.19 的 `file_operations` 没有 `iopoll`，所以旧目标不注册该回调。
- 4.19 尚未合并统一的 `remap_file_range`，但有 `clone_file_range` 和 `dedupe_file_range`；兼容层分别转发 source-wrapper 与 destination-wrapper，保留克隆和去重功能。
- 4.19 的 inode 分配路径已经调用 `security_inode_alloc` 并建立 `i_security`，但没有 `security_inode_init_security_anon` 与 `selinux_inode()`；兼容层跳过不存在的 anon hook，随后直接通过 `wrapper_inode->i_security` 设置 `ksu_file_sid`。

### 第七轮：`40104099042`

- `file_wrapper.c` 的 4.19 VFS/SELinux 映射全部通过。
- 唯一新错误为 `infra/seccomp_cache.c` 缺少 `SECCOMP_ARCH_NATIVE_NR`。
- 新版 arm64 seccomp 头将该宏定义为 `NR_syscalls`；4.19 已提供 `NR_syscalls`，所以补同义宏即可。
- 4.19 arm64 未定义 `SECCOMP_ARCH_COMPAT`，r2 的 compat bitmap 分支不会编入，无需虚构 compat syscall 数量。

### 第八轮：`40104703325`

- seccomp syscall 数量兼容宏已通过，cache 命中率 `99.34%`。
- 唯一新错误为 `infra/su_mount_ns.c` 包含 4.19 不存在的 `uapi/linux/mount.h`。
- 该文件使用的 `CLONE_NEWNS`、`MS_PRIVATE`、`MS_REC` 已由现有 4.19 头链提供；删除多余的新版 mount UAPI include，不复制头文件常量。

### 第九轮：`40105281921`

- mount flags 头修复通过，compiler cache 命中 4242/4246，命中率 `99.91%`。
- 唯一新错误为 `manager/pkg_observer.c` 使用新版 `.handle_inode_event` fsnotify 回调。
- 4.19 仍使用 `.handle_event`，文件名参数为 NUL 结尾的 `unsigned char *`；兼容层按 4.19 的完整签名接收事件，保持原有 `packages.list` 长度和内容判定以及 task-work 延迟处理逻辑。

### 第十轮：`40106012949`

- GitHub runner 的 apt mirror 本轮波动约 12 分钟；实际缓存编译约 2.5 分钟后给出结果，不是源码卡死。
- fsnotify 兼容回调已经通过。
- `policy/allowlist.c` 的错误为 4.19 尚无 `TWA_RESUME` 枚举、缺少声明 `put_task_struct` 的 `linux/sched/task.h`，以及尚无 `fallthrough` 标识符。
- 4.19 的 `task_work_add` 第三参数是 `bool`，因此 `TWA_RESUME` 回退为 `true`；同样使用该枚举的 `supercall.c` 一并适配。唯一 switch 贯穿改用 GCC 支持的 `/* fall through */` 注释。

### 第十一轮：`40107834312`

- task-work 的三个 4.19 兼容点均已通过，增量编译继续进入 `policy/app_profile.c`。
- 唯一新错误为 `struct seccomp` 没有 `filter_count`。Linux 上游标签确认该字段从 5.9 才出现，4.19 的结构只有 `mode` 与 `filter`。
- 兼容层仅在 `>= 5.9` 清零 `filter_count`；4.19 仍按原逻辑清除 `TIF_SECCOMP`、置空 `filter` 并调用 `seccomp_filter_release()`，不改变旧内核释放路径。

### 第十二轮：`40108530403`

- seccomp 结构兼容已通过，唯一新错误进入 `extension/cpu_spoof.c`：4.19 的 `struct clocksource` 没有 `vdso_clock_mode`。
- Linux 上游标签确认该字段从 5.7 才加入。MuMu 4.19 已能编译同一函数中针对 `vdso_data` 和 `vdso_default` 的写入路径。
- 兼容层仅对 `>= 5.7` 编译 `curr_clocksource->vdso_clock_mode` 写入；4.19 保留其余 vDSO 数据更新、CPU capability 清理和 CPU ID 伪装逻辑。

### 第十三轮：`40109099277`

- clocksource 字段边界修复已通过，唯一新错误为 `runtime/ksud_integration.c` 使用较新的 `copy_from_user_nofault` 和 `copy_to_user_nofault` 名称。
- MuMu 固定的 Android common 4.19 源码已提供旧名称 `probe_user_read` 与 `probe_user_write`，参数顺序、长度参数及成功返回 `0` 的约定均一致。
- 两处调用回退到 4.19 名称，保留 fstat 后调整注入 rc 长度的完整逻辑。

### 第十四轮：`40109765398`

- nofault user accessor 回退已通过，编译进入 `selinux/rules.c` 后暴露 SELinux 内部布局边界。
- Linux 4.19 的 `selinux_state` 持有 `struct selinux_ss *ss`，策略位于 `ss->policydb` 并由 `policy_rwlock` 保护；5.10+ 才使用 `selinux_state.policy`、`policy_mutex` 与独立 `struct selinux_policy`。
- 兼容层没有退回旧版 SukiSU：为 4.19 定义与 5.10 布局相容的策略快照包装，继续使用 r2 的策略序列化副本、完整规则集和批量命令解析。修改完成后在 `policy_rwlock` 写锁内原子移入新的 `policydb`，再销毁旧策略；初始备份仍交给 r2 的 `selinux_hide` 使用。

### 第十五轮：`40110727389`

- r2 的策略快照、初始规则、动态批量规则以及 `selinux_hide` 状态/策略访问均已通过编译，说明 4.19 SELinux 布局桥接生效。
- 唯一新错误为 `selinux/selinux.c` 找不到 `selinux_cred()`。Linux 上游标签确认该 helper 从 5.1 才加入；4.19 的等价数据仍由 `cred->security` 持有。
- 兼容层统一包装 `selinux.c` 与 `selinux_hide.c` 的 5 处凭据安全字段访问：4.19 读取 `cred->security`，5.1+ 保持调用 `selinux_cred()`。

### 第十六轮：`40111430275`

- `selinux_cred` 兼容已通过，错误全部集中到 `selinux/sepolicy.c` 的 4.19 容器布局。
- 4.19 的 avtab 桶、type attribute map、type-to-struct 与 type name 表仍由 `flex_array` 保存；5.1 起才切换为普通指针数组。兼容分支恢复 SukiSU 删除 non-GKI 支持前的 flex-array 扩容方式，同时保留 r2 的规则语义。
- 4.19 的 filename transition 使用 `struct filename_trans` 与旧 `hashtab` API；5.7+ 才有 `filename_trans_key`、源类型 bitmap 与链式 datum。两个版本分别维护，且 r2 的新版路径不变。
- `remove_avtab_node` 同样按 `<5.1` 使用 `flex_array_get_ptr`/`flex_array_put_ptr`；4.19 不存在的 Android netlink getneigh policy config 位不写入。

### 第十七轮：`40112310673`

- 4.19 SELinux policy 容器兼容已全部通过编译，构建继续推进到 `sulog/event.c`。
- 新版 SukiSU 直接包含 `linux/minmax.h`，而 Linux 4.19 尚未拆出该头文件；改用各版本均存在的 `linux/kernel.h` 提供同一组 `min`/`max` 定义。

### 第十八轮：`40113072256`

- `linux/kernel.h` 兼容已通过，编译继续推进到 `supercall/dispatch.c`。
- `do_set_init_pgrp()` 使用的 `tasklist_lock`/`init_task` 在 4.19 由 `linux/sched/task.h` 声明，`task_pgrp()`/`task_session()` 由 `linux/sched/signal.h` 声明；显式包含这两个头文件，不改原进程组与会话判定逻辑。

### 第十九轮：`40114098565`

- 进程组声明兼容已通过，错误推进到 r2 新增的 `feature/selinux_hide.c`。
- 4.19 用 `hashtab_search(symtab->table, name)` 查符号，并由 `sidtab_search()` 直接返回 `struct context *`；旧分支直接复用 context-to-string 转换，新分支仍保留 `sidtab_entry` 的字符串缓存。
- type bounds 和 access-vector 计算的 type/attribute 索引在 4.19 继续使用 `flex_array_get_ptr()`/`flex_array_get()`，5.1+ 路径保持普通数组访问。

## 仓库结构与来源关系

本仓库过去在 GitHub 上登记为 `ShirkNeko/GKI_KernelSU_SUSFS` 的 fork，迁移前的代码则已经演化成 WildKernels 风格的模块化 Actions 树。迁移前的精确版本保存在 `backup/wildkernels-2026-10-24`，因此切换主目录结构不会丢失旧实现。

当前 GitHub 仓库已经解除 fork 关系。`upstream` 和 `wild` 仅作为普通只读 Git remote；更新通过明确的 fetch、merge 或 cherry-pick 完成，不使用 GitHub fork sync，也不会因为上游删除仓库或分支而自动删除本仓库内容。

提交 `eb74629a` 将主构建结构切换为 ShirkNeko 的紧凑 Python 方案。私有矩阵功能按当前 Python 架构逐项迁回，而不是恢复庞大的 composite-action 目录。

### ShirkNeko 与 WildKernels 的区别

| 仓库 | 记录的参考提交 | 跟踪文件数 | 构建架构 | 主要范围 |
| --- | --- | ---: | --- | --- |
| [WildKernels/GKI_KernelSU_SUSFS](https://github.com/WildKernels/GKI_KernelSU_SUSFS) | `222173a6397e27bcc6461d4600c3ecb5d8ac61da`（2026-10-23） | 108 | 可复用 workflow、大量 composite action、按内核族拆分 JSON | 更广的 GKI 矩阵、多种 root 实现、功能模块、校验与 release |
| [ShirkNeko/GKI_KernelSU_SUSFS](https://github.com/ShirkNeko/GKI_KernelSU_SUSFS) | `814c5c22afbaa707c50a7573ec4edc338e80004a`（2026-08-27） | 14 | 两个 workflow、紧凑 Python builder、单一 `matrix.json` | SukiSU Ultra/SUSFS 与选定的 Android 12-15 GKI 目标 |

两者共同祖先为 `a834afe0383fe1a5b32a89bb175bbf340be6c8c6`。在记录的 head 上，WildKernels 相对共同祖先领先 2322 个提交，ShirkNeko 领先 200 个提交；两者是共同历史后的不同实现，不是简单的“新版目录”和“旧版目录”。

## Matrix 与私有目标

当前 Python builder 从 `.github/workflows/config/matrix.json` 读取全部 30 个通用目标，覆盖 Android 12 / 5.10 到 Android 17 / 6.18，并保留额外的 Android 13 / 5.10、Android 14 / 5.15 与 AndroMeld Android 16 / 6.12.74 支持。

MuMu 1.9.9 / 4.19.195 不进入该通用 matrix。它是非 GKI 内核并修改了私有 task ABI，必须使用独立源码、config、header overlay、workflow 和独立 LKM/Image 产物；只增加一行 `matrix.json` 无法正确支持。

## 已取消的错误实验

Actions run `40093890646` 曾在确认真实基线前构建通用 Android 12 / 5.10 镜像。该任务已经取消，其临时 5.10 设备配置没有进入提交，也不属于 MuMu 4.19 方案。
