#!/usr/bin/env python3
"""Adapt SukiSU-Ultra sources to APIs exposed by the target kernel tree."""

from pathlib import Path
import sys


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return source.replace(old, new, 1)


kernel = Path(sys.argv[1])
sukisu = Path(sys.argv[2])

netlink_header = (kernel / "include/linux/netlink.h").read_text()
super_access_path = sukisu / "extension/kpm/super_access.c"
super_access = super_access_path.read_text()
if "cb_mutex;" not in netlink_header:
    super_access = replace_once(
        super_access,
        "DEFINE_MEMBER(netlink_kernel_cfg, cb_mutex)\n",
        "",
        "netlink_kernel_cfg.cb_mutex compatibility",
    )
    super_access_path.write_text(super_access)
    print("Removed unavailable netlink_kernel_cfg.cb_mutex descriptor")

lsm_header = (kernel / "include/linux/lsm_hooks.h").read_text()
lsm_hook_path = sukisu / "hook/lsm_hook.c"
lsm_hook = lsm_hook_path.read_text()
if "const struct lsm_id *lsmid" in lsm_header:
    lsm_hook = replace_once(
        lsm_hook,
        "static struct security_hook_list ksu_hooks[] = {\n",
        """static const struct lsm_id ksu_lsmid = {
    .name = "ksu",
    .id = LSM_ID_UNDEF,
};

static struct security_hook_list ksu_hooks[] = {
""",
        "KernelSU LSM identity declaration",
    )
    lsm_hook = replace_once(
        lsm_hook,
        'security_add_hooks(ksu_hooks, ARRAY_SIZE(ksu_hooks), "ksu");',
        "security_add_hooks(ksu_hooks, ARRAY_SIZE(ksu_hooks), &ksu_lsmid);",
        "security_add_hooks lsm_id argument",
    )
    lsm_hook_path.write_text(lsm_hook)
    print("Adapted security_add_hooks to the struct lsm_id API")
