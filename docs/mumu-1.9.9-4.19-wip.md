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
- SukiSU stable build: `v4.2.1-r2`, commit
  `d6b36700f3bd0a4c1585549b470dd30bb8774534`.
- KernelPatch reference: `SukiSU-Ultra/SukiSU_KernelPatch_patch` commit
  `e60c6cfd5cea87cccf9adb7e4d4ba583702d443c`.
- KPM template reference: `liankong233/KPM-Build-Anywhere` commit
  `e26d77c8d6d38abcf7340a16a9b809660b9e78f4`.

## Upstream references

- SukiSU KernelPatch/KPM layer:
  <https://github.com/SukiSU-Ultra/SukiSU_KernelPatch_patch>
- KPM standalone build template:
  <https://github.com/liankong233/KPM-Build-Anywhere>
- SukiSU Ultra root framework and kernel integration:
  <https://github.com/SukiSU-Ultra/SukiSU-Ultra>
- ShirkNeko GKI build-system reference and original fork parent:
  <https://github.com/ShirkNeko/GKI_KernelSU_SUSFS>
- WildKernels source repository and pre-migration modular workflow reference:
  <https://github.com/WildKernels/GKI_KernelSU_SUSFS>

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

The dedicated GitHub Actions entry is
`.github/workflows/mumu-1.9.9-4.19.yml`. It checks out the private MuMu source
at the pinned commit through the read-only `MUMU_SOURCE_SSH_KEY` deploy key,
verifies the config and reconstructed `sched.h` SHA256 values, and builds both
artifacts by default.

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

The GitHub repository was originally registered as a fork of
`ShirkNeko/GKI_KernelSU_SUSFS`, while its pre-migration code had evolved into a
WildKernels-style modular Actions tree. The exact pre-migration head is retained
on `backup/wildkernels-2026-10-24`, so changing the primary layout cannot lose
that implementation.

Commit `eb74629a` replaced the primary build-system files with ShirkNeko's
compact Python layout. Subsequent commits port the private matrix features back
into that model instead of restoring the large composite-action tree. Upstream
repositories are tracked as ordinary read-only Git remotes (`upstream` and
`wild`); updates are explicit fetch/merge/cherry-pick operations rather than
GitHub's fork-sync mechanism.

This structure change does not make MuMu 4.19 a GKI target. MuMu still needs an
isolated backend with its exact source, config and reconstructed header inputs;
it must not be added as a fake Android 12 / 5.10 matrix row.

### WildKernels versus ShirkNeko

The two repositories share history but are no longer the same implementation:

| Repository | Current reference | Tracked files | Build architecture | Scope |
| --- | --- | ---: | --- | --- |
| [WildKernels/GKI_KernelSU_SUSFS](https://github.com/WildKernels/GKI_KernelSU_SUSFS) | `222173a6397e27bcc6461d4600c3ecb5d8ac61da` (2026-10-23) | 108 | Reusable workflows plus many composite actions and per-family JSON files | Broad GKI matrix, multiple root implementations, feature modules, validation and releases |
| [ShirkNeko/GKI_KernelSU_SUSFS](https://github.com/ShirkNeko/GKI_KernelSU_SUSFS) | `814c5c22afbaa707c50a7573ec4edc338e80004a` (2026-08-27) | 14 | Two workflows backed by a compact Python builder and one `matrix.json` | SukiSU Ultra/SUSFS, selected Android 12-15 GKI targets |

Their merge base is `a834afe0383fe1a5b32a89bb175bbf340be6c8c6`.
At the recorded heads WildKernels is 2,322 commits ahead of that base and
ShirkNeko is 200 commits ahead, so neither current head is the other's latest
revision. "Latest" must identify which implementation is intended.

This repository now uses ShirkNeko's Python layout as the primary build-system
shape because it is smaller and easier to extend for private targets. The
pre-migration WildKernels implementation remains preserved on
`backup/wildkernels-2026-10-24`; exact source commits, stock configs and newer
kernel-family support are ported into the Python model rather than restoring
the full composite-action tree.

### Matrix and private-target compatibility

The migrated builder now reads all 30 targets exclusively from
`.github/workflows/config/matrix.json`; the duplicate matrix formerly embedded
in `build.py` has been removed. The matrix covers Android 12 / 5.10 through
Android 17 / 6.18, including the additional 13/5.10 and 14/5.15 families.

Private targets fall into three different classes:

1. Another monthly sublevel on an already supported Google GKI branch can be
   added as a matrix row after verifying that the manifest branch exists.
2. Another GKI family or an exact device kernel, such as AndroMeld Android 16 /
   6.12.74, also needs version validation, exact source checkout, stock-config
   installation, build-system and packaging support. Those fields now flow
   through `BuildConfig` in the Python builder. The 6.12 row also selects
   Simonpunk's `gki-android16-6.12` SUSFS branch and the retained compatibility
   adapters.
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
