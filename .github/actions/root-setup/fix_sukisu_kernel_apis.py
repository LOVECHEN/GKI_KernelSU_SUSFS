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
    cb_mutex_descriptor = "DEFINE_MEMBER(netlink_kernel_cfg, cb_mutex)\n"
    if cb_mutex_descriptor in super_access:
        super_access = replace_once(
            super_access,
            cb_mutex_descriptor,
            "",
            "netlink_kernel_cfg.cb_mutex compatibility",
        )
        super_access_path.write_text(super_access)
        print("Removed unavailable netlink_kernel_cfg.cb_mutex descriptor")
    else:
        print("netlink_kernel_cfg.cb_mutex descriptor already absent")

lsm_header = (kernel / "include/linux/lsm_hooks.h").read_text()
lsm_hook_path = sukisu / "hook/lsm_hook.c"
lsm_hook = lsm_hook_path.read_text()
if "const struct lsm_id *lsmid" in lsm_header:
    legacy_hooks = "static struct security_hook_list ksu_hooks[] = {\n"
    legacy_registration = (
        'security_add_hooks(ksu_hooks, ARRAY_SIZE(ksu_hooks), "ksu");'
    )
    if "static const struct lsm_id ksu_lsmid" in lsm_hook:
        print("SukiSU LSM identity already uses the struct lsm_id API")
    elif legacy_hooks in lsm_hook:
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

# The verified 41087 snapshot expects the post-6.12.92 SUSFS priority-filter
# ABI, while AndroMeld must stay on the pre-rebase 6.12.74 SUSFS baseline.
# Remove only the two optional call sites; all other SUSFS functionality stays
# enabled and is supplied by the pinned baseline later in the workflow.
pkg_observer_path = sukisu / "manager/pkg_observer.c"
pkg_observer = pkg_observer_path.read_text()
priority_refresh = """    // Renew the getpriority uid bitmap filter
    susfs_parse_priority_app_strings();

"""
if priority_refresh in pkg_observer:
    pkg_observer = replace_once(
        pkg_observer,
        priority_refresh,
        "",
        "SUSFS priority-filter refresh compatibility",
    )
    pkg_observer_path.write_text(pkg_observer)
    print("Removed unavailable SUSFS priority-filter refresh call")

dispatch_path = sukisu / "supercall/dispatch.c"
dispatch = dispatch_path.read_text()
priority_dispatch = """        case CMD_SUSFS_SET_PRIORITY_UID_FILTER:
            susfs_set_priority_uid_filter(arg);
            return 0;
"""
if priority_dispatch in dispatch:
    dispatch = replace_once(
        dispatch,
        priority_dispatch,
        "",
        "SUSFS priority-filter command compatibility",
    )
    dispatch_path.write_text(dispatch)
    print("Removed unavailable SUSFS priority-filter command")

# SukiSU 41087 declares user_arg_null_ptr() as returning a pointer but passes
# it to ksu_sulog_capture(), whose argv argument is a struct value.
sulog_event_path = sukisu / "sulog/event.c"
sulog_event = sulog_event_path.read_text()
bad_user_arg_null = "#define USER_ARG_NULL user_arg_null_ptr()"
if bad_user_arg_null in sulog_event:
    sulog_event = replace_once(
        sulog_event,
        bad_user_arg_null,
        "#define USER_ARG_NULL (*user_arg_null_ptr())",
        "SukiSU sulog null argv value",
    )
    sulog_event_path.write_text(sulog_event)
    print("Dereferenced the SukiSU sulog null argv value")
