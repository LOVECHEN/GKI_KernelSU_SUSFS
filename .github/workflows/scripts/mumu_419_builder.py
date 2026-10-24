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
    nofault_calls = {
        "kernel/runtime/ksud_integration.c": 1,
        "kernel/sulog/event.c": 2,
        "kernel/feature/sucompat.c": 2,
    }
    for relative, expected in nofault_calls.items():
        path = checkout / relative
        content = path.read_text(encoding="utf-8")
        actual = content.count("strncpy_from_user_nofault")
        if actual != expected:
            raise RuntimeError(
                f"Linux 4.19 nofault user copy in {relative}: "
                f"expected {expected} matches, found {actual}"
            )
        path.write_text(
            content.replace("strncpy_from_user_nofault", "strncpy_from_unsafe_user"),
            encoding="utf-8",
        )
    ksud_integration = checkout / "kernel/runtime/ksud_integration.c"
    replace_once(
        ksud_integration,
        "copy_from_user_nofault(&size, st_size_ptr, sizeof(long))",
        "probe_user_read(&size, st_size_ptr, sizeof(long))",
        "Linux 4.19 nofault user read",
    )
    replace_once(
        ksud_integration,
        "copy_to_user_nofault(st_size_ptr, &new_size, sizeof(long))",
        "probe_user_write(st_size_ptr, &new_size, sizeof(long))",
        "Linux 4.19 nofault user write",
    )
    replace_once(
        checkout / "kernel/hook/arm64/patch_memory.c",
        "copy_to_kernel_nofault(map, src, len)",
        "probe_kernel_write(map, src, len)",
        "Linux 4.19 nofault kernel write",
    )
    file_wrapper = checkout / "kernel/infra/file_wrapper.c"
    replace_once(
        file_wrapper,
        '''#if LINUX_VERSION_CODE >= KERNEL_VERSION(6, 1, 0)
static int ksu_wrapper_iopoll(struct kiocb *kiocb, struct io_comp_batch *icb, unsigned int v)
{
    struct ksu_file_wrapper *data = kiocb->ki_filp->private_data;
    struct file *orig = data->orig;
    kiocb->ki_filp = orig;
    return orig->f_op->iopoll(kiocb, icb, v);
}
#else
static int ksu_wrapper_iopoll(struct kiocb *kiocb, bool spin)
{
    struct ksu_file_wrapper *data = kiocb->ki_filp->private_data;
    struct file *orig = data->orig;
    kiocb->ki_filp = orig;
    return orig->f_op->iopoll(kiocb, spin);
}
#endif

''',
        "",
        "Linux 4.19 file_operations.iopoll",
    )
    replace_once(
        file_wrapper,
        '''// no REMAP_FILE_DEDUP: use file_in
// https://cs.android.com/android/kernel/superproject/+/common-android-mainline:common/fs/read_write.c;l=1598-1599;drc=398da7defe218d3e51b0f3bdff75147e28125b60
// https://cs.android.com/android/kernel/superproject/+/common-android-mainline:common/fs/remap_range.c;l=403-404;drc=398da7defe218d3e51b0f3bdff75147e28125b60
// REMAP_FILE_DEDUP: use file_out
// https://cs.android.com/android/kernel/superproject/+/common-android-mainline:common/fs/remap_range.c;l=483-484;drc=398da7defe218d3e51b0f3bdff75147e28125b60
static loff_t ksu_wrapper_remap_file_range(struct file *file_in, loff_t pos_in, struct file *file_out, loff_t pos_out,
                                           loff_t len, unsigned int remap_flags)
{
    if (remap_flags & REMAP_FILE_DEDUP) {
        struct ksu_file_wrapper *data = file_out->private_data;
        struct file *orig = data->orig;
        return orig->f_op->remap_file_range(file_in, pos_in, orig, pos_out, len, remap_flags);
    } else {
        struct ksu_file_wrapper *data = file_in->private_data;
        struct file *orig = data->orig;
        return orig->f_op->remap_file_range(orig, pos_in, file_out, pos_out, len, remap_flags);
    }
}
''',
        '''static int ksu_wrapper_clone_file_range(struct file *file_in, loff_t pos_in, struct file *file_out,
                                                loff_t pos_out, u64 len)
{
    struct ksu_file_wrapper *data = file_in->private_data;
    struct file *orig = data->orig;
    return orig->f_op->clone_file_range(orig, pos_in, file_out, pos_out, len);
}

static int ksu_wrapper_dedupe_file_range(struct file *file_in, loff_t pos_in, struct file *file_out,
                                         loff_t pos_out, u64 len)
{
    struct ksu_file_wrapper *data = file_out->private_data;
    struct file *orig = data->orig;
    return orig->f_op->dedupe_file_range(file_in, pos_in, orig, pos_out, len);
}
''',
        "Linux 4.19 clone and dedupe file operations",
    )
    replace_once(
        file_wrapper,
        "    p->ops.iopoll = fp->f_op->iopoll ? ksu_wrapper_iopoll : NULL;\n",
        "",
        "Linux 4.19 iopoll assignment",
    )
    replace_once(
        file_wrapper,
        "    p->ops.remap_file_range = fp->f_op->remap_file_range ? ksu_wrapper_remap_file_range : NULL;\n",
        '''    p->ops.clone_file_range = fp->f_op->clone_file_range ? ksu_wrapper_clone_file_range : NULL;
    p->ops.dedupe_file_range = fp->f_op->dedupe_file_range ? ksu_wrapper_dedupe_file_range : NULL;
''',
        "Linux 4.19 clone and dedupe assignments",
    )
    replace_once(
        file_wrapper,
        '''    const struct qstr qname = QSTR_INIT(name, strlen(name));
    int error;

''',
        "",
        "Linux 4.19 anonymous inode security locals",
    )
    replace_once(
        file_wrapper,
        '''    error = security_inode_init_security_anon(inode, &qname, context_inode);
    if (error) {
        iput(inode);
        return ERR_PTR(error);
    }
''',
        "",
        "Linux 4.19 anonymous inode security hook",
    )
    replace_once(
        file_wrapper,
        "    struct inode_security_struct *wrapper_sec = selinux_inode(wrapper_inode);\n",
        "    struct inode_security_struct *wrapper_sec = wrapper_inode->i_security;\n",
        "Linux 4.19 inode security accessor",
    )
    replace_once(
        checkout / "kernel/infra/seccomp_cache.c",
        '#include <linux/seccomp.h>\n',
        '''#include <linux/seccomp.h>

#ifndef SECCOMP_ARCH_NATIVE_NR
#define SECCOMP_ARCH_NATIVE_NR NR_syscalls
#endif
''',
        "Linux 4.19 native seccomp syscall count",
    )
    replace_once(
        checkout / "kernel/policy/app_profile.c",
        "    atomic_set(&current->seccomp.filter_count, 0);\n",
        '''#if LINUX_VERSION_CODE >= KERNEL_VERSION(5, 9, 0)
    atomic_set(&current->seccomp.filter_count, 0);
#endif
''',
        "Linux 4.19 seccomp state layout",
    )
    cpu_spoof = checkout / "kernel/extension/cpu_spoof.c"
    replace_once(
        cpu_spoof,
        '''                {
                    struct clocksource **curr_cs_ptr =
                        (struct clocksource **)find_kernel_symbol_exact(
                            "curr_clocksource");
                    if (curr_cs_ptr && *curr_cs_ptr) {
                        (*curr_cs_ptr)->vdso_clock_mode =
                            VDSO_CLOCKMODE_ARCHTIMER;
                    } else {
                        pr_warn("ksu: set_spoof_cpu failed to resolve 'curr_clocksource'\\n");
                        ++missing;
                    }
                }
''',
        '''#if LINUX_VERSION_CODE >= KERNEL_VERSION(5, 7, 0)
                {
                    struct clocksource **curr_cs_ptr =
                        (struct clocksource **)find_kernel_symbol_exact(
                            "curr_clocksource");
                    if (curr_cs_ptr && *curr_cs_ptr) {
                        (*curr_cs_ptr)->vdso_clock_mode =
                            VDSO_CLOCKMODE_ARCHTIMER;
                    } else {
                        pr_warn("ksu: set_spoof_cpu failed to resolve 'curr_clocksource'\\n");
                        ++missing;
                    }
                }
#endif
''',
        "Linux 4.19 clocksource vDSO state",
    )
    sepolicy_h = checkout / "kernel/selinux/sepolicy.h"
    replace_once(
        sepolicy_h,
        '''#include <linux/types.h>

#include "ss/policydb.h"
''',
        '''#include <linux/types.h>
#include <linux/version.h>

#include "ss/policydb.h"

#if LINUX_VERSION_CODE < KERNEL_VERSION(5, 10, 0)
#include "ss/services.h"
struct selinux_policy {
    struct sidtab *sidtab;
    struct policydb policydb;
    struct selinux_map map;
    u32 latest_granting;
};
#endif
''',
        "Linux 4.19 SELinux policy wrapper",
    )
    rules = checkout / "kernel/selinux/rules.c"
    replace_once(
        rules,
        '''void apply_kernelsu_rules()
{
    struct selinux_policy *pol, *old_pol;
    struct policydb *db;
''',
        '''void apply_kernelsu_rules()
{
    struct selinux_policy *pol, *old_pol;
    struct policydb *db;
#if LINUX_VERSION_CODE < KERNEL_VERSION(5, 10, 0)
    struct selinux_policy old_view;
    struct policydb old_db;
#endif
''',
        "Linux 4.19 initial policy locals",
    )
    replace_once(
        rules,
        '''    mutex_lock(&selinux_state.policy_mutex);

    old_pol = rcu_dereference_protected(selinux_state.policy, lockdep_is_held(&selinux_state.policy_mutex));
    backup_sepolicy = ksu_dup_sepolicy(old_pol);
''',
        '''#if LINUX_VERSION_CODE >= KERNEL_VERSION(5, 10, 0)
    mutex_lock(&selinux_state.policy_mutex);
    old_pol = rcu_dereference_protected(selinux_state.policy, lockdep_is_held(&selinux_state.policy_mutex));
#else
    old_view.sidtab = selinux_state.ss->sidtab;
    old_view.policydb = selinux_state.ss->policydb;
    old_view.map = selinux_state.ss->map;
    old_view.latest_granting = selinux_state.ss->latest_granting;
    old_pol = &old_view;
#endif
    backup_sepolicy = ksu_dup_sepolicy(old_pol);
''',
        "Linux 4.19 initial policy snapshot",
    )
    replace_once(
        rules,
        '''    rcu_assign_pointer(selinux_state.policy, pol);
    synchronize_rcu();
    ksu_destroy_sepolicy(old_pol);

    reset_avc_cache();
out_unlock:
    mutex_unlock(&selinux_state.policy_mutex);
}
''',
        '''#if LINUX_VERSION_CODE >= KERNEL_VERSION(5, 10, 0)
    rcu_assign_pointer(selinux_state.policy, pol);
    synchronize_rcu();
    ksu_destroy_sepolicy(old_pol);
#else
    write_lock(&selinux_state.ss->policy_rwlock);
    old_db = selinux_state.ss->policydb;
    selinux_state.ss->policydb = pol->policydb;
    memset(&pol->policydb, 0, sizeof(pol->policydb));
    write_unlock(&selinux_state.ss->policy_rwlock);
    policydb_destroy(&old_db);
    kfree(pol);
#endif

    reset_avc_cache();
out_unlock:
#if LINUX_VERSION_CODE >= KERNEL_VERSION(5, 10, 0)
    mutex_unlock(&selinux_state.policy_mutex);
#endif
}
''',
        "Linux 4.19 initial policy commit",
    )
    replace_once(
        rules,
        '''    struct selinux_policy *pol, *old_pol;
    struct policydb *db;
    struct sepol_batch_cursor cursor;
''',
        '''    struct selinux_policy *pol, *old_pol;
    struct policydb *db;
#if LINUX_VERSION_CODE < KERNEL_VERSION(5, 10, 0)
    struct selinux_policy old_view;
    struct policydb old_db;
#endif
    struct sepol_batch_cursor cursor;
''',
        "Linux 4.19 dynamic policy locals",
    )
    replace_once(
        rules,
        '''    mutex_lock(&selinux_state.policy_mutex);

    old_pol = rcu_dereference_protected(selinux_state.policy, lockdep_is_held(&selinux_state.policy_mutex));
    pol = ksu_dup_sepolicy(old_pol);
''',
        '''#if LINUX_VERSION_CODE >= KERNEL_VERSION(5, 10, 0)
    mutex_lock(&selinux_state.policy_mutex);
    old_pol = rcu_dereference_protected(selinux_state.policy, lockdep_is_held(&selinux_state.policy_mutex));
#else
    old_view.sidtab = selinux_state.ss->sidtab;
    old_view.policydb = selinux_state.ss->policydb;
    old_view.map = selinux_state.ss->map;
    old_view.latest_granting = selinux_state.ss->latest_granting;
    old_pol = &old_view;
#endif
    pol = ksu_dup_sepolicy(old_pol);
''',
        "Linux 4.19 dynamic policy snapshot",
    )
    replace_once(
        rules,
        '''    rcu_assign_pointer(selinux_state.policy, pol);
    synchronize_rcu();
    ksu_destroy_sepolicy(old_pol);

    reset_avc_cache();
    ret = success_cmd_count;
    goto out_unlock;

out_drop_new_policy:
    ksu_destroy_sepolicy(pol);
out_unlock:
    mutex_unlock(&selinux_state.policy_mutex);
out_free:
''',
        '''#if LINUX_VERSION_CODE >= KERNEL_VERSION(5, 10, 0)
    rcu_assign_pointer(selinux_state.policy, pol);
    synchronize_rcu();
    ksu_destroy_sepolicy(old_pol);
#else
    write_lock(&selinux_state.ss->policy_rwlock);
    old_db = selinux_state.ss->policydb;
    selinux_state.ss->policydb = pol->policydb;
    memset(&pol->policydb, 0, sizeof(pol->policydb));
    write_unlock(&selinux_state.ss->policy_rwlock);
    policydb_destroy(&old_db);
    kfree(pol);
#endif

    reset_avc_cache();
    ret = success_cmd_count;
    goto out_unlock;

out_drop_new_policy:
    ksu_destroy_sepolicy(pol);
out_unlock:
#if LINUX_VERSION_CODE >= KERNEL_VERSION(5, 10, 0)
    mutex_unlock(&selinux_state.policy_mutex);
#endif
out_free:
''',
        "Linux 4.19 dynamic policy commit",
    )
    selinux_hide = checkout / "kernel/feature/selinux_hide.c"
    replace_once(
        selinux_hide,
        '''#include "hook/lsm_hook.h"

static DEFINE_MUTEX(selinux_hide_mutex);
''',
        '''#include "hook/lsm_hook.h"

#if LINUX_VERSION_CODE < KERNEL_VERSION(5, 10, 0)
#define ksu_status_lock (selinux_state.ss->status_lock)
#define ksu_status_page (selinux_state.ss->status_page)
#else
#define ksu_status_lock ((&selinux_state)->status_lock)
#define ksu_status_page ((&selinux_state)->status_page)
#endif

static DEFINE_MUTEX(selinux_hide_mutex);
''',
        "Linux 4.19 SELinux status storage",
    )
    hide_content = selinux_hide.read_text(encoding="utf-8")
    status_fields = {
        "selinux_state.status_lock": ("ksu_status_lock", 6),
        "selinux_state.status_page": ("ksu_status_page", 2),
    }
    for old, (new, expected) in status_fields.items():
        actual = hide_content.count(old)
        if actual != expected:
            raise RuntimeError(
                f"Linux 4.19 SELinux status field {old}: "
                f"expected {expected} matches, found {actual}"
            )
        hide_content = hide_content.replace(old, new)
    selinux_hide.write_text(hide_content, encoding="utf-8")
    replace_once(
        selinux_hide,
        '''    struct selinux_policy *orig_policy;
    struct policydb *policydb, *orig_policydb;
''',
        '''    struct selinux_policy *orig_policy;
#if LINUX_VERSION_CODE < KERNEL_VERSION(5, 10, 0)
    struct selinux_policy orig_view;
#endif
    struct policydb *policydb, *orig_policydb;
''',
        "Linux 4.19 SELinux hide policy locals",
    )
    replace_once(
        selinux_hide,
        '''    // removed: if (force)
    rcu_read_lock();
    orig_policy = rcu_dereference(selinux_state.policy);
    orig_policydb = &orig_policy->policydb;
''',
        '''    // removed: if (force)
#if LINUX_VERSION_CODE < KERNEL_VERSION(5, 10, 0)
    read_lock(&selinux_state.ss->policy_rwlock);
    orig_view.sidtab = selinux_state.ss->sidtab;
    orig_view.policydb = selinux_state.ss->policydb;
    orig_view.map = selinux_state.ss->map;
    orig_view.latest_granting = selinux_state.ss->latest_granting;
    orig_policy = &orig_view;
#else
    rcu_read_lock();
    orig_policy = rcu_dereference(selinux_state.policy);
#endif
    orig_policydb = &orig_policy->policydb;
''',
        "Linux 4.19 SELinux hide policy snapshot",
    )
    replace_once(
        selinux_hide,
        '''    rcu_read_unlock();
    if (orig_rc_p)
''',
        '''#if LINUX_VERSION_CODE < KERNEL_VERSION(5, 10, 0)
    read_unlock(&selinux_state.ss->policy_rwlock);
#else
    rcu_read_unlock();
#endif
    if (orig_rc_p)
''',
        "Linux 4.19 SELinux hide policy unlock",
    )
    cred_calls = {
        "kernel/selinux/selinux.c": 3,
        "kernel/feature/selinux_hide.c": 2,
    }
    for relative, expected in cred_calls.items():
        path = checkout / relative
        content = path.read_text(encoding="utf-8")
        actual = content.count("selinux_cred(")
        if actual != expected:
            raise RuntimeError(
                f"Linux 4.19 SELinux cred accessor in {relative}: "
                f"expected {expected} matches, found {actual}"
            )
        path.write_text(content.replace("selinux_cred(", "ksu_selinux_cred("), encoding="utf-8")
        replace_once(
            path,
            '#include "objsec.h"\n',
            '''#include "objsec.h"
#include <linux/version.h>

#if LINUX_VERSION_CODE < KERNEL_VERSION(5, 1, 0)
#define ksu_selinux_cred(cred) ((cred)->security)
#else
#define ksu_selinux_cred(cred) selinux_cred(cred)
#endif
''',
            f"Linux 4.19 SELinux cred accessor macro in {relative}",
        )
    sepolicy = checkout / "kernel/selinux/sepolicy.c"
    replace_once(
        sepolicy,
        "        for (n = db->te_avtab.htable[i]; n; prev = n, n = n->next) {\n",
        '''#if LINUX_VERSION_CODE >= KERNEL_VERSION(5, 1, 0)
        n = db->te_avtab.htable[i];
#else
        n = flex_array_get_ptr(db->te_avtab.htable, i);
#endif
        for (; n; prev = n, n = n->next) {
''',
        "Linux 4.19 avtab bucket lookup",
    )
    replace_once(
        sepolicy,
        "                db->te_avtab.htable[i] = n->next;\n",
        '''#if LINUX_VERSION_CODE >= KERNEL_VERSION(5, 1, 0)
                db->te_avtab.htable[i] = n->next;
#else
                flex_array_put_ptr(db->te_avtab.htable, i, n->next, GFP_ATOMIC | __GFP_ZERO);
#endif
''',
        "Linux 4.19 avtab bucket update",
    )
    replace_once(
        sepolicy,
        "            removed.htable[0] = n;\n",
        '''#if LINUX_VERSION_CODE >= KERNEL_VERSION(5, 1, 0)
            removed.htable[0] = n;
#else
            flex_array_put_ptr(removed.htable, 0, n, GFP_ATOMIC | __GFP_ZERO);
#endif
''',
        "Linux 4.19 removed avtab bucket",
    )
    replace_once(
        sepolicy,
        '''static bool add_filename_trans(struct policydb *db, const char *s, const char *t, const char *c, const char *d,
                               const char *o)
''',
        '''#if LINUX_VERSION_CODE >= KERNEL_VERSION(5, 7, 0)
static bool add_filename_trans(struct policydb *db, const char *s, const char *t, const char *c, const char *d,
                               const char *o)
''',
        "Linux 4.19 filename transition modern branch",
    )
    replace_once(
        sepolicy,
        '''out:
    return false;
}

static bool add_genfscon(struct policydb *db, const char *fs_name, const char *path, const char *context)
''',
        '''out:
    return false;
}
#else
static bool add_filename_trans(struct policydb *db, const char *s, const char *t, const char *c, const char *d,
                               const char *o)
{
    struct type_datum *src, *tgt, *def;
    struct class_datum *cls;
    struct filename_trans key;
    struct filename_trans_datum *trans;
    struct filename_trans *new_key = NULL;

    src = symtab_search(&db->p_types, s);
    tgt = symtab_search(&db->p_types, t);
    cls = symtab_search(&db->p_classes, c);
    def = symtab_search(&db->p_types, d);
    if (!src || !tgt || !cls || !def) {
        pr_warn("filename transition symbol missing: %s %s %s %s\\n", s, t, c, d);
        return false;
    }

    key.ttype = tgt->value;
    key.tclass = cls->value;
    key.name = (char *)o;
    trans = hashtab_search(db->filename_trans, &key);
    if (!trans) {
        trans = kzalloc(sizeof(*trans), GFP_KERNEL);
        new_key = kzalloc(sizeof(*new_key), GFP_KERNEL);
        if (!trans || !new_key)
            goto legacy_free;
        *new_key = key;
        new_key->name = kstrdup(key.name, GFP_KERNEL);
        if (!new_key->name)
            goto legacy_free;
        trans->otype = def->value;
        if (hashtab_insert(db->filename_trans, new_key, trans)) {
            kfree(new_key->name);
            goto legacy_free;
        }
    } else {
        trans->otype = def->value;
    }

    return ebitmap_set_bit(&db->filename_trans_ttypes, src->value - 1, 1) == 0;

legacy_free:
    kfree(new_key);
    kfree(trans);
    return false;
}
#endif

static bool add_genfscon(struct policydb *db, const char *fs_name, const char *path, const char *context)
''',
        "Linux 4.19 filename transition implementation",
    )
    replace_once(
        sepolicy,
        "static bool add_type(struct policydb *db, const char *type_name, bool attr)\n",
        '''#if LINUX_VERSION_CODE >= KERNEL_VERSION(5, 1, 0)
static bool add_type(struct policydb *db, const char *type_name, bool attr)
''',
        "Linux 4.19 type table modern branch",
    )
    replace_once(
        sepolicy,
        '''    return true;
}

static bool set_type_state(struct policydb *db, const char *type_name, bool permissive)
''',
        '''    return true;
}
#else
static bool add_type(struct policydb *db, const char *type_name, bool attr)
{
    struct type_datum *type = symtab_search(&db->p_types, type_name);
    struct flex_array *new_attr;
    struct flex_array *new_types;
    struct flex_array *new_names;
    struct flex_array *old;
    char *key;
    void *elem;
    u32 value;
    int i;

    if (type)
        return true;

    value = ++db->p_types.nprim;
    type = kzalloc(sizeof(*type), GFP_KERNEL);
    key = kstrdup(type_name, GFP_KERNEL);
    if (!type || !key)
        return false;
    type->primary = 1;
    type->value = value;
    type->attribute = attr;
    if (symtab_insert(&db->p_types, key, type))
        return false;

    new_attr = flex_array_alloc(sizeof(struct ebitmap), value, GFP_KERNEL | __GFP_ZERO);
    new_types = flex_array_alloc(sizeof(struct type_datum *), value, GFP_KERNEL | __GFP_ZERO);
    new_names = flex_array_alloc(sizeof(char *), value, GFP_KERNEL | __GFP_ZERO);
    if (!new_attr || !new_types || !new_names)
        return false;
    if (flex_array_prealloc(new_attr, 0, value, GFP_KERNEL | __GFP_ZERO) ||
        flex_array_prealloc(new_types, 0, value, GFP_KERNEL | __GFP_ZERO) ||
        flex_array_prealloc(new_names, 0, value, GFP_KERNEL | __GFP_ZERO))
        return false;

    for (i = 0; i < value - 1; i++) {
        elem = flex_array_get(db->type_attr_map_array, i);
        if (elem)
            flex_array_put(new_attr, i, elem, GFP_KERNEL | __GFP_ZERO);
        elem = flex_array_get_ptr(db->type_val_to_struct_array, i);
        if (elem)
            flex_array_put_ptr(new_types, i, elem, GFP_KERNEL | __GFP_ZERO);
        elem = flex_array_get_ptr(db->sym_val_to_name[SYM_TYPES], i);
        if (elem)
            flex_array_put_ptr(new_names, i, elem, GFP_KERNEL | __GFP_ZERO);
    }

    old = db->type_attr_map_array;
    db->type_attr_map_array = new_attr;
    flex_array_free(old);
    ebitmap_init(flex_array_get(db->type_attr_map_array, value - 1));
    ebitmap_set_bit(flex_array_get(db->type_attr_map_array, value - 1), value - 1, 1);

    old = db->type_val_to_struct_array;
    db->type_val_to_struct_array = new_types;
    flex_array_free(old);
    flex_array_put_ptr(db->type_val_to_struct_array, value - 1, type, GFP_KERNEL | __GFP_ZERO);

    old = db->sym_val_to_name[SYM_TYPES];
    db->sym_val_to_name[SYM_TYPES] = new_names;
    flex_array_free(old);
    flex_array_put_ptr(db->sym_val_to_name[SYM_TYPES], value - 1, key, GFP_KERNEL | __GFP_ZERO);

    for (i = 0; i < db->p_roles.nprim; i++)
        ebitmap_set_bit(&db->role_val_to_struct[i]->types, value - 1, 1);
    return true;
}
#endif

static bool set_type_state(struct policydb *db, const char *type_name, bool permissive)
''',
        "Linux 4.19 flex-array type table implementation",
    )
    replace_once(
        sepolicy,
        "    struct ebitmap *sattr = &db->type_attr_map_array[type->value - 1];\n",
        '''#if LINUX_VERSION_CODE >= KERNEL_VERSION(5, 1, 0)
    struct ebitmap *sattr = &db->type_attr_map_array[type->value - 1];
#else
    struct ebitmap *sattr = flex_array_get(db->type_attr_map_array, type->value - 1);
#endif
''',
        "Linux 4.19 type attribute map lookup",
    )
    replace_once(
        sepolicy,
        '''        if (old_pol->policydb.android_netlink_getneigh) {
            pr_info("adding POLICYDB_CONFIG_ANDROID_NETLINK_GETNEIGH\\n");
            *config_ptr |= POLICYDB_CONFIG_ANDROID_NETLINK_GETNEIGH;
        }
''',
        '''#if LINUX_VERSION_CODE >= KERNEL_VERSION(5, 10, 0)
        if (old_pol->policydb.android_netlink_getneigh) {
            pr_info("adding POLICYDB_CONFIG_ANDROID_NETLINK_GETNEIGH\\n");
            *config_ptr |= POLICYDB_CONFIG_ANDROID_NETLINK_GETNEIGH;
        }
#endif
''',
        "Linux 4.19 policy config fields",
    )
    replace_once(
        checkout / "kernel/sulog/event.c",
        "#include <linux/minmax.h>\n",
        "#include <linux/kernel.h>\n",
        "Linux 4.19 min/max definitions",
    )
    replace_once(
        checkout / "kernel/infra/su_mount_ns.c",
        "#include <uapi/linux/mount.h>\n",
        "",
        "Linux 4.19 mount flags header",
    )
    pkg_observer = checkout / "kernel/manager/pkg_observer.c"
    replace_once(
        pkg_observer,
        '''static int ksu_handle_inode_event(struct fsnotify_mark *mark, u32 mask, struct inode *inode, struct inode *dir,
                                  const struct qstr *file_name, u32 cookie)
{
    if (!file_name)
        return 0;
    if (mask & FS_ISDIR)
        return 0;
    if (file_name->len == 13 && !memcmp(file_name->name, "packages.list", 13)) {
        pr_info("packages.list detected: %d\\n", mask);
        ksu_defer_track_throne();
    }
    return 0;
}

static const struct fsnotify_ops ksu_ops = {
    .handle_inode_event = ksu_handle_inode_event,
};
''',
        '''static int ksu_handle_event(struct fsnotify_group *group, struct inode *inode, u32 mask, const void *data,
                            int data_type, const unsigned char *file_name, u32 cookie,
                            struct fsnotify_iter_info *iter_info)
{
    if (!file_name)
        return 0;
    if (mask & FS_ISDIR)
        return 0;
    if (strlen(file_name) == 13 && !memcmp(file_name, "packages.list", 13)) {
        pr_info("packages.list detected: %d\\n", mask);
        ksu_defer_track_throne();
    }
    return 0;
}

static const struct fsnotify_ops ksu_ops = {
    .handle_event = ksu_handle_event,
};
''',
        "Linux 4.19 fsnotify callback",
    )
    allowlist = checkout / "kernel/policy/allowlist.c"
    replace_once(
        allowlist,
        "#include <linux/task_work.h>\n",
        '''#include <linux/task_work.h>
#include <linux/sched/task.h>
''',
        "Linux 4.19 task reference helpers",
    )
    for relative in ["kernel/policy/allowlist.c", "kernel/supercall/supercall.c"]:
        path = checkout / relative
        replace_once(
            path,
            "#include <linux/version.h>\n",
            '''#include <linux/version.h>

#if LINUX_VERSION_CODE < KERNEL_VERSION(5, 8, 0) && !defined(TWA_RESUME)
#define TWA_RESUME true
#endif
''',
            f"Linux 4.19 task-work notification in {relative}",
        )
    replace_once(
        allowlist,
        "        fallthrough;\n",
        "        /* fall through */\n",
        "Linux 4.19 fallthrough annotation",
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
