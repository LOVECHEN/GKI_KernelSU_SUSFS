#!/usr/bin/env python3
"""Build MuMuPlayer 1.9.9 Linux 4.19.195 SukiSU artifacts."""

import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess


ANDROID_COMMON_COMMIT = "60080b53629d749f14cf6981b1602de6c19dd46e"
MUMU_SOURCE_COMMIT = "19380722db94c5b7d0a1a27304d12e69ad5629f3"
SUKISU_COMMIT = "d6b36700f3bd0a4c1585549b470dd30bb8774534"
MUMU_CONFIG_SHA256 = "8de88d19fdb81fe11d39646e8580f109fb24120855c26e2f5ac00e34a8aed620"
MUMU_SCHED_SHA256 = "ef182ca24187619d36a5be1d0d9b9deaf538d1f79d922db89f84d717a93b5519"


def run(command, cwd=None, capture=False):
    print("+", " ".join(str(part) for part in command), flush=True)
    return subprocess.run(
        [str(part) for part in command],
        cwd=cwd,
        check=True,
        text=True,
        capture_output=capture,
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_file(path: Path, expected: str, label: str):
    actual = sha256(path)
    if actual != expected:
        raise RuntimeError(f"{label} SHA256 mismatch: expected {expected}, got {actual}")


def append_once(path: Path, marker: str, block: str):
    content = path.read_text(encoding="utf-8")
    if marker not in content:
        path.write_text(content.rstrip() + "\n\n" + block.strip() + "\n", encoding="utf-8")


def replace_once(path: Path, old: str, new: str, label: str):
    content = path.read_text(encoding="utf-8")
    count = content.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    path.write_text(content.replace(old, new, 1), encoding="utf-8")


def set_config(path: Path, options: dict):
    lines = path.read_text(encoding="utf-8").splitlines()
    for key, value in options.items():
        replacement = f"{key}={value}"
        pattern = re.compile(rf"^(?:{re.escape(key)}=.*|# {re.escape(key)} is not set)$")
        replaced = False
        updated = []
        for line in lines:
            if pattern.match(line):
                if not replaced:
                    updated.append(replacement)
                    replaced = True
                continue
            updated.append(line)
        if not replaced:
            updated.append(replacement)
        lines = updated
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def prepare_kernel(kernel: Path):
    if kernel.exists():
        shutil.rmtree(kernel)
    run(["git", "clone", "--filter=blob:none", "--no-checkout",
         "https://android.googlesource.com/kernel/common", kernel])
    run(["git", "fetch", "--depth=1", "origin", ANDROID_COMMON_COMMIT], cwd=kernel)
    run(["git", "checkout", "--detach", "FETCH_HEAD"], cwd=kernel)
    actual = run(["git", "rev-parse", "HEAD"], cwd=kernel, capture=True).stdout.strip()
    if actual != ANDROID_COMMON_COMMIT:
        raise RuntimeError(f"Android common commit mismatch: {actual}")


def overlay_mumu(kernel: Path, source_root: Path):
    base = source_root / "reimpl/1.9.9/netease-1to1/kernel"
    patches = base / "kernel-patches"
    anti = patches / "nemu-anti-detect"
    config = base / "image-build/linux-4.19.195.nemu.config"
    sched = anti / "core-patches/include/linux/sched.h"
    verify_file(config, MUMU_CONFIG_SHA256, "MuMu config")
    verify_file(sched, MUMU_SCHED_SHA256, "MuMu sched.h")

    shutil.copytree(anti / "core-patches", kernel, dirs_exist_ok=True)
    shutil.copyfile(anti / "nemuctl.h", kernel / "include/linux/nemuctl.h")
    for name in ["nemuctl.c", "nemu_file_rule.c", "virtual_module.c"]:
        shutil.copyfile(anti / name, kernel / "drivers/misc" / name)
    shutil.copyfile(patches / "nemu-freq-qemu-arm.c",
                    kernel / "drivers/cpufreq/nemu-freq-qemu-arm.c")
    shutil.copyfile(patches / "mumu_power.c",
                    kernel / "drivers/power/supply/mumu_power.c")
    shutil.copyfile(patches / "pagecache_limit.c", kernel / "mm/pagecache_limit.c")
    shutil.copyfile(patches / "crypto-sha256-direct/sha256_generic.c",
                    kernel / "crypto/sha256_generic.c")

    qtaguid = anti / "xt_qtaguid-4.19-port"
    for name in ["xt_qtaguid.c", "xt_qtaguid_internal.h", "xt_qtaguid_print.c", "xt_qtaguid_print.h"]:
        shutil.copyfile(qtaguid / name, kernel / "net/netfilter" / name)
    shutil.copyfile(qtaguid / "xt_qtaguid_uapi.h",
                    kernel / "include/uapi/linux/netfilter/xt_qtaguid.h")

    append_once(
        kernel / "drivers/misc/Makefile",
        "CONFIG_NEMU_ANTI_DETECT",
        "obj-$(CONFIG_NEMU_ANTI_DETECT) += nemuctl.o nemu_file_rule.o virtual_module.o",
    )
    append_once(
        kernel / "drivers/misc/Kconfig",
        "config NEMU_ANTI_DETECT",
        """
config NEMU_ANTI_DETECT
    bool "NetEase MuMu anti-detect engine"
    default y
""",
    )
    append_once(
        kernel / "drivers/cpufreq/Makefile",
        "CONFIG_CPUFREQ_NEMU_QEMU_ARM",
        "obj-$(CONFIG_CPUFREQ_NEMU_QEMU_ARM) += nemu-freq-qemu-arm.o",
    )
    append_once(
        kernel / "drivers/cpufreq/Kconfig",
        "config CPUFREQ_NEMU_QEMU_ARM",
        """
config CPUFREQ_NEMU_QEMU_ARM
    bool "MuMu QEMU ARM CPU frequency driver"
    depends on ARM64 && CPU_FREQ
    default y
""",
    )
    append_once(
        kernel / "drivers/power/supply/Makefile",
        "CONFIG_MUMU_POWER",
        "obj-$(CONFIG_MUMU_POWER) += mumu_power.o",
    )
    append_once(
        kernel / "drivers/power/supply/Kconfig",
        "config MUMU_POWER",
        """
config MUMU_POWER
    bool "MuMu virtual battery"
    depends on POWER_SUPPLY
    default y
""",
    )
    append_once(kernel / "mm/Makefile", "CONFIG_PAGECACHE_LIMIT",
                "obj-$(CONFIG_PAGECACHE_LIMIT) += pagecache_limit.o")
    append_once(
        kernel / "mm/Kconfig",
        "config PAGECACHE_LIMIT",
        """
config PAGECACHE_LIMIT
    bool "MuMu page-cache limit service"
    default y
""",
    )
    append_once(
        kernel / "net/netfilter/Makefile",
        "CONFIG_NETFILTER_XT_MATCH_QTAGUID",
        "obj-$(CONFIG_NETFILTER_XT_MATCH_QTAGUID) += xt_qtaguid.o xt_qtaguid_print.o",
    )
    append_once(
        kernel / "net/netfilter/Kconfig",
        "config NETFILTER_XT_MATCH_QTAGUID",
        """
config NETFILTER_XT_MATCH_QTAGUID
    tristate "QTAGUID socket owner accounting"
    depends on NETFILTER_XT_MATCH_SOCKET && NETFILTER_XTABLES
    default y
""",
    )
    append_once(
        kernel / "crypto/Kconfig",
        "config CRYPTO_SHA256_DIRECT",
        """
config CRYPTO_SHA256_DIRECT
    bool "MuMu direct SHA-256 helpers"
    depends on CRYPTO_SHA256
    default y
""",
    )
    run(["git", "apply", patches / "eth-alloc-etherdev-wlan0.patch"], cwd=kernel)
    return config


def integrate_sukisu(kernel: Path):
    checkout = kernel / "KernelSU"
    run(["git", "clone", "--filter=blob:none", "--no-checkout",
         "https://github.com/SukiSU-Ultra/SukiSU-Ultra.git", checkout])
    run(["git", "fetch", "--depth=1", "origin", SUKISU_COMMIT], cwd=checkout)
    run(["git", "checkout", "--detach", "FETCH_HEAD"], cwd=checkout)
    actual = run(["git", "rev-parse", "HEAD"], cwd=checkout, capture=True).stdout.strip()
    if actual != SUKISU_COMMIT:
        raise RuntimeError(f"SukiSU commit mismatch: {actual}")

    init = checkout / "kernel/core/init.c"
    replace_once(
        init,
        '#include <linux/moduleparam.h>\n',
        '''#include <linux/moduleparam.h>

#ifndef MODULE_IMPORT_NS
#define MODULE_IMPORT_NS(namespace)
#endif
''',
        "Linux 4.19 module namespace compatibility",
    )
    replace_once(
        init,
        '''__attribute__((naked)) int __init kernelsu_init_early(void)
{
    asm("mov x19, x30;\\n"
        "bl ksu_setup_stack_chk_guard;\\n"
        "mov x30, x19;\\n"
        "b kernelsu_init;\\n");
}
''',
        '''int __init kernelsu_init(void);

__attribute__((no_stack_protector)) int __init kernelsu_init_early(void)
{
    ksu_setup_stack_chk_guard();
    return kernelsu_init();
}
''',
        "GCC arm64 stack protector bootstrap",
    )
    replace_once(
        checkout / "kernel/feature/sucompat.c",
        "#include <linux/pgtable.h>\n",
        "",
        "Linux 4.19 unused pgtable header",
    )

    drivers = kernel / "drivers"
    (drivers / "kernelsu").symlink_to(Path("../KernelSU/kernel"))
    append_once(drivers / "Makefile", "CONFIG_KSU", "obj-$(CONFIG_KSU) += kernelsu/")
    kconfig = drivers / "Kconfig"
    content = kconfig.read_text(encoding="utf-8")
    marker = 'source "drivers/kernelsu/Kconfig"'
    if marker not in content:
        insertion = content.rfind("endmenu")
        if insertion < 0:
            raise RuntimeError("drivers/Kconfig has no endmenu insertion point")
        kconfig.write_text(content[:insertion] + marker + "\n\n" + content[insertion:], encoding="utf-8")


def build_variant(kernel: Path, base_config: Path, output_dir: Path, variant: str, jobs: int):
    output_dir.mkdir(parents=True, exist_ok=True)
    config = output_dir / ".config"
    shutil.copyfile(base_config, config)
    common = {
        "CONFIG_LOCALVERSION_AUTO": "n",
        "CONFIG_NEMU_ANTI_DETECT": "y",
        "CONFIG_CPUFREQ_NEMU_QEMU_ARM": "y",
        "CONFIG_MUMU_POWER": "y",
        "CONFIG_PAGECACHE_LIMIT": "y",
        "CONFIG_NETFILTER_XT_MATCH_QTAGUID": "y",
        "CONFIG_CRYPTO_SHA256_DIRECT": "y",
    }
    if variant == "lkm":
        common.update({"CONFIG_KSU": "m", "CONFIG_KPM": "n"})
    else:
        common.update({"CONFIG_KSU": "y", "CONFIG_KPM": "y"})
    set_config(config, common)

    make = ["make", f"O={output_dir}", "ARCH=arm64",
            "CROSS_COMPILE=aarch64-linux-gnu-"]
    if shutil.which("ccache"):
        make.append("CC=ccache aarch64-linux-gnu-gcc")
    run(make + ["olddefconfig"], cwd=kernel)
    run(make + [f"-j{jobs}", "Image", "modules"], cwd=kernel)


def collect_artifacts(kernel: Path, workspace: Path, artifacts: Path, target: str):
    artifacts.mkdir(parents=True, exist_ok=True)
    if target in ("lkm", "all"):
        candidates = list((workspace / "out-lkm").rglob("kernelsu.ko"))
        if len(candidates) != 1:
            raise RuntimeError(f"expected one kernelsu.ko, found {len(candidates)}")
        shutil.copyfile(candidates[0], artifacts / "kernelsu-mumu-1.9.9-4.19.195-r2.ko")
    if target in ("image", "all"):
        image = workspace / "out-image/arch/arm64/boot/Image"
        if not image.is_file():
            raise RuntimeError("built-in KPM Image was not produced")
        shutil.copyfile(image, artifacts / "Image-mumu-1.9.9-4.19.195-sukisu-r2-kpm")

    manifest = []
    for artifact in sorted(artifacts.iterdir()):
        if artifact.is_file() and artifact.name != "SHA256SUMS.txt":
            manifest.append(f"{sha256(artifact)}  {artifact.name}")
    (artifacts / "SHA256SUMS.txt").write_text("\n".join(manifest) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--artifacts", required=True, type=Path)
    parser.add_argument("--target", choices=["lkm", "image", "all"], default="all")
    parser.add_argument("--jobs", type=int, default=max(1, os.cpu_count() or 1))
    args = parser.parse_args()

    kernel = args.workspace / "kernel"
    prepare_kernel(kernel)
    base_config = overlay_mumu(kernel, args.source_root.resolve())
    integrate_sukisu(kernel)
    if args.target in ("lkm", "all"):
        build_variant(kernel, base_config, args.workspace / "out-lkm", "lkm", args.jobs)
    if args.target in ("image", "all"):
        build_variant(kernel, base_config, args.workspace / "out-image", "image", args.jobs)
    collect_artifacts(kernel, args.workspace, args.artifacts.resolve(), args.target)


if __name__ == "__main__":
    main()
