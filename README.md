# GKI SukiSU-Ultra + SUSFS 构建系统

本仓库使用 ShirkNeko 的紧凑 Python 构建结构，同时保留我们的私有目标、精确源码提交和设备 stock config 支持。仓库不依赖 GitHub fork 同步：上游作为只读 Git remote 跟踪，对方删库或改写历史不会删除本仓库已保存的 commit。

## 构建入口

- `Kernel Build`：手动选择单个 Android/Kernel 目标。
- `Build Kernels`：从 [matrix.json](.github/workflows/config/matrix.json) 生成并行构建矩阵。
- `.github/workflows/scripts/build.py`：本地或 CI 的统一 CLI 入口。

```bash
cd .github/workflows/scripts
python3 build.py --list-matrix
python3 build.py --android android16 --kernel 6.12 --sub-level 74 --os-patch 2026-03 --dry-run
python3 build.py --matrix android14-6.1
```

## 构建矩阵

`matrix.json` 是唯一事实源，当前共 30 个目标：

| Android | Kernel | Sub Levels | 说明 |
| --- | --- | --- | --- |
| 12 | 5.10 | 136, 198, 209, 236, X | Shirk 原始选定目标 |
| 13 | 5.10 | 209, 236, 243 | 我们扩展 |
| 13 | 5.15 | 74, 123, 148, 170, 178, 180, 189 | Shirk + 新月度版本 |
| 14 | 5.15 | 148, 180, 192 | 我们扩展 |
| 14 | 6.1 | 78, 90, 99, 124, 145 | Shirk 原始选定目标 |
| 15 | 6.6 | 50, 66, 102 | Shirk 原始选定目标 |
| 16 | 6.12 | 74 | AndroMeld：精确 source commit + stock config + 6.12 SUSFS |
| 17 | 6.18 | 20, 21, 32 | 当前无可用 SUSFS 6.18 分支，矩阵明确关闭 SUSFS |

私有/设备目标可在矩阵行中使用：

```json
{
  "sub_level": "74",
  "os_patch_level": "2026-03",
  "source_commit": "3ec022196c4e9d5c1434599cdda63f622dd6f586",
  "stock_config_path": "config/andromeld-6.12.74-stock.config",
  "build_from_stock_config": true,
  "susfs_repo_url": "https://gitlab.com/simonpunk/susfs4ksu.git",
  "susfs_branch": "gki-android16-6.12"
}
```

MuMuPlayer 1.9.9 的 `4.19.195` 是非 GKI 且修改过私有 `task_struct` ABI，不能伪装成 5.10 矩阵行。它的 SukiSU LKM 和内置 KPM Image 路线单独记录在 [MuMu 4.19 WIP](docs/mumu-1.9.9-4.19-wip.md)。

## 上游与参考

- [SukiSU-Ultra/SukiSU_KernelPatch_patch](https://github.com/SukiSU-Ultra/SukiSU_KernelPatch_patch)
- [liankong233/KPM-Build-Anywhere](https://github.com/liankong233/KPM-Build-Anywhere)
- [SukiSU-Ultra/SukiSU-Ultra](https://github.com/SukiSU-Ultra/SukiSU-Ultra)
- [ShirkNeko/GKI_KernelSU_SUSFS](https://github.com/ShirkNeko/GKI_KernelSU_SUSFS)
- [WildKernels/GKI_KernelSU_SUSFS](https://github.com/WildKernels/GKI_KernelSU_SUSFS)

ShirkNeko 当前是 14 个跟踪文件的紧凑 Python 构建器，主要覆盖 Android 12-15 / 5.10-6.6。WildKernels 当前是 108 个跟踪文件的模块化 Actions 系统，覆盖更广的内核家族、root 实现和功能模块。两者在共同历史后分叉，不是同一套结构的新旧版。精确 commit、分叉数据和迁移决策见 [MuMu 4.19 WIP](docs/mumu-1.9.9-4.19-wip.md#shirknekoversuswildkernels)。

## 上游更新

预期的 remote 布局：

```bash
git remote add upstream https://github.com/ShirkNeko/GKI_KernelSU_SUSFS.git
git remote add wild https://github.com/WildKernels/GKI_KernelSU_SUSFS.git
git fetch upstream
git fetch wild
```

更新时从对应 remote 选择性合并/cherry-pick，不用 fork 的「Sync fork」按钮。迁移前 WildKernels 式结构保存在 `backup/wildkernels-2026-10-24`。
