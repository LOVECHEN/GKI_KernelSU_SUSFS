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
`WildKernels/GKI_KernelSU_SUSFS`. The current ShirkNeko repository has since
been rewritten around `.github/workflows/scripts/*.py` and
`config/matrix.json`, while this fork retains and extends the older reusable
workflow plus composite-action architecture. Do not merge the rewritten tree
wholesale. Add MuMu as an isolated 4.19 workflow after the prototype builds.

## Cancelled experiment

Workflow run `40093890646` built a generic Android 12 / 5.10 image before the
4.19 baseline was corrected. It was cancelled and none of its temporary 5.10
device-profile changes were committed.
