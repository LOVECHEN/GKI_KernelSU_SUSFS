#!/usr/bin/env python3
"""Apply SUSFS map hiding to the legacy Android 16 6.12 smaps loop."""

from pathlib import Path
import sys


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return source.replace(old, new, 1)


path = Path(sys.argv[1])
source = path.read_text()

source = replace_once(
    source,
    """\tdo {
\t\tsmap_gather_stats(vma, &mss, 0);
\t\tlast_vma_end = vma->vm_end;
""",
    """\tdo {
#ifdef CONFIG_KSU_SUSFS_SUS_MAP
\t\tif (!(vma->vm_file &&
\t\t      SUSFS_IS_INODE_SUS_MAP(file_inode(vma->vm_file))))
#endif
\t\t\tsmap_gather_stats(vma, &mss, 0);
\t\tlast_vma_end = vma->vm_end;
""",
    "initial VMA gathering",
)

source = replace_once(
    source,
    """\t\t\tif (vma->vm_start >= last_vma_end) {
\t\t\t\tsmap_gather_stats(vma, &mss, 0);
\t\t\t\tlast_vma_end = vma->vm_end;
\t\t\t\tcontinue;
\t\t\t}
""",
    """\t\t\tif (vma->vm_start >= last_vma_end) {
#ifdef CONFIG_KSU_SUSFS_SUS_MAP
\t\t\t\tif (!(vma->vm_file &&
\t\t\t\t      SUSFS_IS_INODE_SUS_MAP(file_inode(vma->vm_file))))
#endif
\t\t\t\t\tsmap_gather_stats(vma, &mss, 0);
\t\t\t\tlast_vma_end = vma->vm_end;
\t\t\t\tcontinue;
\t\t\t}
""",
    "resumed whole-VMA gathering",
)

source = replace_once(
    source,
    """\t\t\tif (vma->vm_end > last_vma_end) {
\t\t\t\tsmap_gather_stats(vma, &mss, last_vma_end);
\t\t\t\tlast_vma_end = vma->vm_end;
\t\t\t}
""",
    """\t\t\tif (vma->vm_end > last_vma_end) {
#ifdef CONFIG_KSU_SUSFS_SUS_MAP
\t\t\t\tif (!(vma->vm_file &&
\t\t\t\t      SUSFS_IS_INODE_SUS_MAP(file_inode(vma->vm_file))))
#endif
\t\t\t\t\tsmap_gather_stats(vma, &mss, last_vma_end);
\t\t\t\tlast_vma_end = vma->vm_end;
\t\t\t}
""",
    "resumed partial-VMA gathering",
)

path.write_text(source)
