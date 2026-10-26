#!/usr/bin/env python3
"""Bridge pre-refactor SUSFS policy helpers to the SukiSU 41087 ABI."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def replace_exact(source: str, old: str, new: str, expected: int, label: str) -> str:
    count = source.count(old)
    if count != expected:
        raise SystemExit(f"{label}: expected {expected} matches, found {count}")
    return source.replace(old, new)


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(f"usage: {sys.argv[0]} <kernel-common> <sukisu-kernel>")

    common = Path(sys.argv[1])
    sukisu = Path(sys.argv[2])
    hide_path = sukisu / "feature/selinux_hide.c"
    hide = hide_path.read_text()

    # SUSFS calls these helpers from the core SELinux objects. SukiSU keeps
    # both declarations and definitions private because its own callers live
    # in this translation unit, so export the exact existing implementations.
    hide = replace_exact(
        hide,
        "static int security_context_to_sid_with_policy",
        "int security_context_to_sid_with_policy",
        2,
        "context-to-SID helper export",
    )
    hide = replace_exact(
        hide,
        "static int security_sid_to_context_with_policy",
        "int security_sid_to_context_with_policy",
        2,
        "SID-to-context helper export",
    )
    hide = replace_exact(
        hide,
        "static void security_compute_av_user_with_policy",
        "void security_compute_av_user_with_policy",
        1,
        "access-vector helper declaration export",
    )
    hide = replace_exact(
        hide,
        "static void __nocfi security_compute_av_user_with_policy",
        "void __nocfi security_compute_av_user_with_policy",
        1,
        "access-vector helper definition export",
    )
    hide_path.write_text(hide)

    # SUSFS v2.3.0 before the 6.12.92 rebase used the older seven-argument
    # context-to-SID declaration. SukiSU 41087 added two optional outputs for
    # synchronising the live SID table. Preserve that implementation and pass
    # NULL for the outputs instead of relying on uninitialised argument slots.
    declaration_re = re.compile(
        r"(extern int security_context_to_sid_with_policy\("
        r"struct selinux_policy \*policy, const char \*scontext, u32 scontext_len,\s*"
        r"u32 \*sid, u32 def_sid, gfp_t gfp_flags)\);"
    )
    call_re = re.compile(
        r"(security_context_to_sid_with_policy\("
        r"(?!struct selinux_policy)[^;]*?SECSID_NULL,\s*GFP_KERNEL)\);",
        re.DOTALL,
    )

    declaration_count = 0
    call_count = 0
    touched: list[str] = []
    for path in sorted((common / "security/selinux").rglob("*.c")):
        source = path.read_text()
        source, declarations = declaration_re.subn(
            r"\1, u32 *orig_sid_p, int *orig_rc_p);", source
        )
        source, calls = call_re.subn(r"\1, NULL, NULL);", source)
        if declarations or calls:
            path.write_text(source)
            declaration_count += declarations
            call_count += calls
            touched.append(str(path.relative_to(common)))

    if declaration_count != 2:
        raise SystemExit(
            "policy helper declarations: expected 2 matches, "
            f"found {declaration_count}"
        )
    if call_count != 4:
        raise SystemExit(
            f"policy helper calls: expected 4 matches, found {call_count}"
        )

    print("Exported SukiSU policy helpers and adapted SUSFS callers:")
    for path in touched:
        print(f"  {path}")


if __name__ == "__main__":
    main()
