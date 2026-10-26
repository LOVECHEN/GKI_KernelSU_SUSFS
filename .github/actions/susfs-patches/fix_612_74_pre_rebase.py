#!/usr/bin/env python3
"""Apply the two known pre-6.12.92 SUSFS hunks to Android 16 6.12.74."""

from pathlib import Path
import sys


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    source = path.read_text()
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    path.write_text(source.replace(old, new, 1))


root = Path(sys.argv[1])

replace_once(
    root / "fs/exec.c",
    """#include <linux/dma-buf.h>

#include <linux/uaccess.h>
""",
    """#include <linux/dma-buf.h>
#ifdef CONFIG_KSU_SUSFS
#include <linux/susfs_def.h>
#endif

#include <linux/uaccess.h>
""",
    "exec SUSFS include",
)

replace_once(
    root / "fs/proc/task_mmu.c",
    """\tstruct vm_area_struct *vma = v;
\tstruct mem_size_stats mss = {};

\tif (!vma_data_pages(vma))
""",
    """\tstruct vm_area_struct *vma = v;
\tstruct mem_size_stats mss = {};

#ifdef CONFIG_KSU_SUSFS_SUS_MAP
\tif (vma->vm_file) {
\t\tif (SUSFS_IS_INODE_SUS_MAP(file_inode(vma->vm_file)))
\t\t\treturn 0;
\t}
#endif // #ifdef CONFIG_KSU_SUSFS_SUS_MAP

\tif (!vma_data_pages(vma))
""",
    "show_smap SUS map filter",
)
