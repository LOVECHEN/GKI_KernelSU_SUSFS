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

## Build the Device-Compatible Minimal SukiSU Ultra Kernel

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

Keep every remaining optional feature toggle disabled for the first AndroMeld build. `allow_version_mismatch` is enabled because the runtime ships external modules built for its stock release string.

The `2026-03` target is device-specific. Its matrix row selects
`config/andromeld-6.12.74-stock.config`, extracted from the original AndroMeld
kernel (`sha256:4c065ae7247d878dc34438e61230fb4c3e4a9ce286cd585bf49db03dd7e69726`).
The workflow installs this file as the real `gki_defconfig` before adding the
SukiSU configuration. It also embeds the untouched copy for `/proc/config.gz`.
Do not replace it with the latest generic `kernel-6.12-gz` config: that config
belongs to a different GKI rollup and changes hundreds of scheduler, power,
display, and Android options.

The stock config references `protected_module_names_list`, an input supplied by
Google's production build environment but absent from the public source commit.
The workflow creates an empty source-tree placeholder for this file. This keeps
the stock config and module ABI intact; the AndroMeld build does not compile or
ship external kernel modules from this list.

Device-compatible targets use the repository's deterministic directory cleanup
instead of the third-party apt-based free-space action. The latter can stall on
runner-image package changes before the kernel source is even downloaded.

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

The earlier run `39840787113` produced `6.12.74-android16-6-AndroMeld` with
SukiSU Ultra `41050-6`, but it used the generic `6.12.18` build config. Root
worked while the Android display wake path did not: launching an app left the
runtime asleep. That artifact is retained only as a diagnosis record and must
not be installed. A valid result must satisfy all of these checks:

- SukiSU reports `Built-in / Working`.
- ADB reports `uid=0(root)` and SELinux context `u:r:ksu:s0`.
- `/proc/modules` contains no `kernelsu` entry.
- An installed Android app opens visibly after the runtime has gone idle.

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
