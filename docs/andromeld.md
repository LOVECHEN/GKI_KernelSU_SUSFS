# AndroMeld Kernel Build

This fork contains a pinned target for the current AndroMeld Android runtime:

| Field | Value |
| --- | --- |
| Kernel release | `6.12.74-android16-6-g3ec022196c4e-ab15076761-4k` |
| GKI family | `android16-6.12` |
| Linux sublevel | `74` |
| Patch level | `2026-03` |
| Page size | `4k` |
| Kernel common commit | `3ec022196c4e9d5c1434599cdda63f622dd6f586` |

The `source_commit` field in `.github/config/android16-6.12.json` is passed through the matrix and checked out after the Android manifest sync. The build therefore uses the exact `kernel/common` source commit instead of the moving monthly branch tip.

## Build the Validated Minimal SukiSU Ultra Kernel

Run the `Build Kernels` workflow with these inputs:

| Input | Value |
| --- | --- |
| Release Type | `CI` |
| Use cache | `false` |
| Force module version mismatch | `true` |
| Kernel Version | `6.12.x-android16` |
| OS patch level | `2026-03` |
| Page size | `4k` |
| Kernel Branding | `AndroMeld` |
| Keep KMI suffix | `true` |
| Commit mode | `latest` |
| Root Flavor | `SukiSU-Ultra` |
| SUSFS | `false` |
| NoMount | `false` |

Keep every remaining optional feature toggle disabled for the first AndroMeld build. This is the configuration that booted successfully in the AndroMeld runtime; add SUSFS, NoMount, and other patch sets only in separate follow-up builds. `allow_version_mismatch` is enabled because the runtime ships external modules built for its stock release string.

Equivalent GitHub CLI command:

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
  -f commit_mode=latest \
  -f root_flavor=SukiSU-Ultra \
  -f use_susfs=false \
  -f use_nomount=false \
  -f use_bbg=false \
  -f use_net=false \
  -f use_ds=false \
  -f use_ntsync=false \
  -f use_ptrace=false \
  -f use_unicode=false \
  -f use_bpf=false \
  -f use_perf=false \
  -f test_release_notes=false
```

The validated run produced `6.12.74-android16-6-AndroMeld` with SukiSU Ultra `41050-6`. The manager reports `Built-in / Working`, ADB runs as `uid=0(root)` with SELinux context `u:r:ksu:s0`, and `/proc/modules` contains no `kernelsu` entry. Those observations distinguish this kernel from both an LKM installation and the workflow's `No Root` flavor.

## Build One Current LTS Kernel for Every Family

Use `kernel_build_version=All` together with `os_patch_level=lts`. Every family config contains exactly one `lts` row, so this produces seven kernel jobs rather than every historical monthly row. Select `SukiSU-Ultra` explicitly; selecting `No Root` deliberately omits the root implementation, while the root-flavor `All` choice builds three different root implementations per target.

Use `Pre-Release` when the artifacts should remain available as a GitHub prerelease instead of only as expiring Actions artifacts:

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
  -f use_susfs=false \
  -f use_nomount=false \
  -f use_bbg=false \
  -f use_net=false \
  -f use_ds=false \
  -f use_ntsync=false \
  -f use_ptrace=false \
  -f use_unicode=false \
  -f use_bpf=false \
  -f use_perf=false \
  -f test_release_notes=false
```

The expected families are:

| Android common family | Linux series |
| --- | --- |
| `android12-5.10` | 5.10 |
| `android13-5.10` | 5.10 |
| `android13-5.15` | 5.15 |
| `android14-5.15` | 5.15 |
| `android14-6.1` | 6.1 |
| `android15-6.6` | 6.6 |
| `android16-6.12` | 6.12 |

The `lts` row follows the current LTS branch tip, so the resolved numeric sublevel is recorded by the completed run and may increase on a later dispatch.

Keep these outputs from the completed run:

- `*-AnyKernel3`: flashable package contents. Zip the files at archive root before installation.
- `*-BuildInfo`: exact source revisions and checksums.
- SukiSU Ultra manager APK artifact.
- Raw kernel `Image`, when present in the kernel artifact.
