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

throne_tracker_path = sukisu / "manager/throne_tracker.c"
throne_tracker = throne_tracker_path.read_text()
malformed_initializer = ".depth = pos->depth }\n"
if malformed_initializer in throne_tracker:
    throne_tracker = replace_once(
        throne_tracker,
        malformed_initializer,
        ".depth = pos->depth };\n",
        "throne tracker initializer terminator",
    )
    throne_tracker_path.write_text(throne_tracker)
    print("Restored missing throne tracker initializer semicolon")

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
    legacy_hooks = "static struct security_hook_list ksu_hooks[] = {\n"
    legacy_registration = (
        'security_add_hooks(ksu_hooks, ARRAY_SIZE(ksu_hooks), "ksu");'
    )
    if legacy_hooks in lsm_hook:
        lsm_hook = replace_once(
            lsm_hook,
            legacy_hooks,
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
            legacy_registration,
            "security_add_hooks(ksu_hooks, ARRAY_SIZE(ksu_hooks), &ksu_lsmid);",
            "security_add_hooks lsm_id argument",
        )
        lsm_hook_path.write_text(lsm_hook)
        print("Adapted security_add_hooks to the struct lsm_id API")
    elif "security_add_hooks(" not in lsm_hook:
        # Current SukiSU patches LSM slots at runtime and no longer registers a
        # static hook array, so the target kernel's registration API is unused.
        print("SukiSU uses runtime LSM slot patching; no lsm_id adaptation needed")
    else:
        raise RuntimeError(
            "Unknown SukiSU LSM registration layout for the struct lsm_id API"
        )
