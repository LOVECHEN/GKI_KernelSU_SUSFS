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

## Build Latest SukiSU Ultra

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
| SUSFS | `true` |
| NoMount | `true` |

The remaining optional feature toggles can stay disabled for the first AndroMeld build. `allow_version_mismatch` is enabled because the runtime ships external modules built for its stock release string.

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
  -f use_susfs=true \
  -f use_nomount=true \
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

Keep these outputs from the completed run:

- `*-AnyKernel3`: flashable package contents. Zip the files at archive root before installation.
- `*-BuildInfo`: exact source revisions and checksums.
- SukiSU Ultra manager APK artifact.
- Raw kernel `Image`, when present in the kernel artifact.
