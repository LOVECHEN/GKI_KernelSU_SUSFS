# MuMuPlayer 1.9.9 / Linux 4.19.195 SukiSU WIP

This document records the local prototype state before the build is promoted to
GitHub Actions. It is intentionally not part of the generic 5.10+ GKI matrix.

## Target

- Guest: MuMuPlayer 1.9.9 arm64.
- Kernel: `4.19.195-android-arm64-gedae1315d023`.
- Android common base: merge commit `f931d3c324845b1be4337d27b565351fb581f206`
  (`Merge 4.19.195 into android-4.19-stable`).
- MuMu source snapshot: `LOVECHEN/mumu-neutralize` commit
  `19380722db94c5b7d0a1a27304d12e69ad5629f3`.
- SukiSU prototype: `SukiSU-Ultra/SukiSU-Ultra` commit
  `22561329c04479b7985391764125a3a362170df0`.
- KernelPatch reference: `SukiSU-Ultra/SukiSU_KernelPatch_patch` commit
  `e60c6cfd5cea87cccf9adb7e4d4ba583702d443c`.
- KPM template reference: `liankong233/KPM-Build-Anywhere` commit
  `e26d77c8d6d38abcf7340a16a9b809660b9e78f4`.

## Confirmed constraints

- Do not replace the MuMu kernel with Android 12 / 5.10 GKI. The 1.9.9 guest
  baseline and private virtual-device ABI are Linux 4.19.195.
- SukiSU documents manual builds for non-GKI and older kernels starting at
  4.14. Its `main` Kconfig makes `CONFIG_KSU` tristate, so 4.19 can produce a
  `kernelsu.ko`; official releases simply do not publish a 4.19 LKM.
- Full KPM support is a separate built-in image target using
  `CONFIG_KSU=y` and `CONFIG_KPM=y`.
- MuMu already enables `CONFIG_KALLSYMS=y`, `CONFIG_KALLSYMS_ALL=y`,
  `CONFIG_KPROBES=y`, `CONFIG_KRETPROBES=y`,
  `CONFIG_HAVE_SYSCALL_TRACEPOINTS=y`, `CONFIG_EXT4_FS=y`, and
  `CONFIG_MODULES=y`. It does not force module signatures or use modversions.
- MuMu changes `task_struct`. A module built against a vanilla 4.19 header can
  have incorrect field offsets even when its vermagic matches. The build must
  consume MuMu's reconstructed `include/linux/sched.h` and exact config.

## Intended artifacts

1. `kernelsu.ko`: SukiSU LKM built against the exact MuMu 4.19 task ABI.
2. `Image-sukisu-kpm`: MuMu's bootable 4.19.195 source image with
   `CONFIG_KSU=y` and `CONFIG_KPM=y`.
3. KernelPatch/KPM tooling: kept as an independent image-patching and KPM
   development path. `KPM-Build-Anywhere` builds KPM payloads; it does not
   integrate SukiSU by itself.

## Local prototype

The disposable build state is in Docker volume `mumu-sukisu-lkm-199`. The
toolchain image is `mumu-kbuild:bookworm-gcc12`. Both were created on
2026-10-24 and remain subject to the seven-day scratch TTL.

The prototype checked out Android common at `f931d3c3`, copied MuMu's exact
config and reconstructed `sched.h`, integrated SukiSU as
`drivers/kernelsu`, and selected:

```text
CONFIG_NEMU_ANTI_DETECT=y
CONFIG_KSU=m
# CONFIG_KPM is not set
```

Kconfig and `modules_prepare` complete. Compiling current SukiSU `main`
against 4.19 reaches the module objects but exposes upstream 4.19 compatibility
regressions:

- `MODULE_IMPORT_NS` is unavailable.
- `copy_to_kernel_nofault` is unavailable on 4.19.
- `linux/pgtable.h` and `uapi/linux/mount.h` are unavailable under those names.
- `fsnotify_ops.handle_inode_event` uses a newer fsnotify API.
- `SECCOMP_ARCH_NATIVE_NR` is unavailable.
- SELinux generated headers must be produced before the external module build.

These are real compile results, not assumptions. Before writing compatibility
patches, compare SukiSU tags and history to locate the newest release that still
contains the older-kernel shims.

## Repository lineage

`LOVECHEN/GKI_KernelSU_SUSFS` is a direct fork of
`ShirkNeko/GKI_KernelSU_SUSFS`; the network source is
`WildKernels/GKI_KernelSU_SUSFS`.

The merge base between `origin/main` and `shirk/main` is
`814c5c22afbaa707c50a7573ec4edc338e80004a` (2026-08-27). That commit is also
the current `shirk/main`; `origin/main` is 2,337 commits ahead and Shirk is zero
commits ahead. Therefore Shirk did not replace this fork with a newer layout.
This fork moved away from Shirk's compact Python builder after the fork point.

### Shirk layout at the fork point

- 14 tracked files and three top-level entries: `.github`, `README.md`, and
  `hmbird_patch.c`.
- Two composite actions, two primary workflows, one `config/matrix.json`, and
  seven Python scripts under `.github/workflows/scripts/`.
- A `BuildConfig`-driven Python build pipeline covering Android 12 through 15
  and kernel 5.10 through 6.6.
- The README explicitly excludes non-GKI kernels, so this layout is not a
  direct MuMu 4.19 build solution.

### Current fork layout

- 111 tracked files, including `config/`, `docs/`, licensing and provenance
  material in addition to `.github`.
- 48 composite actions for setup, pinning, cache, SUSFS, BTF, root-framework
  integration, device patches, build and packaging.
- Reusable preparation/build/manager/release/validation workflows and
  per-family JSON configuration from Android 12 / 5.10 through Android 17 /
  6.18.
- Compared with Shirk's current tree: 107 files added, 10 removed and three
  modified. The old Python builder, two monolithic workflows and single matrix
  file were removed in favor of the modular WildKernels-style pipeline.

Do not merge or restore the Shirk tree wholesale. Its simpler Python builder is
useful as a reference, but it is still a 5.10+ GKI builder. Add MuMu as an
isolated `mumu-1.9.9-4.19.yml` workflow with its exact source/config/header
inputs so the existing GKI matrix remains unchanged.

### Matrix and private-target compatibility

Shirk's batch workflow reads 19 public targets from
`.github/workflows/config/matrix.json`: Android 12 / 5.10, Android 13 / 5.15,
Android 14 / 6.1 and Android 15 / 6.6. The JSON is not its only source of
truth: `build.py` duplicates the matrix in `DEFAULT_BUILD_MATRIX` and currently
contains Android 13 / 5.15.189 while the JSON does not. Any reuse should remove
this duplication before adding targets.

Private targets fall into three different classes:

1. Another monthly sublevel on an already supported Google GKI branch can be
   added as a matrix row after verifying that the manifest branch exists.
2. Another GKI family or an exact device kernel, such as the existing
   AndroMeld Android 16 / 6.12.74 target, also needs version validation, source
   checkout, build-system and packaging support. This fork already passes an
   exact `source_commit`, `stock_config_path` and `build_from_stock_config`
   through its modular workflow.
3. MuMu 1.9.9 / 4.19.195 is non-GKI and changes the private task ABI. It needs a
   separate source/config/header backend and separate LKM/image artifacts; a
   `matrix.json` row alone cannot support it.

If any source or patch repository is private, repository URL/ref and checkout
credentials must be explicit workflow inputs or secrets rather than the public
URLs hard-coded by Shirk's `config.py`.

## Cancelled experiment

Workflow run `40093890646` built a generic Android 12 / 5.10 image before the
4.19 baseline was corrected. It was cancelled and none of its temporary 5.10
device-profile changes were committed.
