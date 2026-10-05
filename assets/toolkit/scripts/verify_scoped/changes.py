"""Which paths differ from the base: git's own answer, and every path whose raw bytes or mode differ besides.

`check-slice-scope.changed_files` asks `git diff`, which applies git's filters: `text=auto`, `eol`, `core.autocrlf`,
`filter=` clean and smudge, `ident`, `working-tree-encoding`, and `core.fileMode`. The stamp's key reads the bytes on
disk. So a difference those hide is one the stamp sees and `git diff` does not, and a check chosen only by git's answer
would be skipped on a tree `make verify` judges differently. A path is changed here when git says so, or when what is
on disk — the file's bytes, the target of a link, the executable bit — differs from the base's blob read raw: no filter,
attribute or configuration is asked, because none is read.
"""
from __future__ import annotations

import hashlib
import os
import stat
import subprocess
import sys
from typing import Any

sys.dont_write_bytecode = True

BLOB = "blob"
SYMLINK = "120000"
EXECUTABLE = "100755"
REGULAR = "100644"
CHUNK = 1 << 20
MAKEFILES = ("Makefile", "GNUmakefile", "makefile")  # at the root, which the text border reads (D140)


def digest(name: str, size: int, data: bytes | None, path: str) -> str:
    """The object id git gives a blob of these raw bytes (`name` is `sha1` or `sha256`, from the id's length)."""
    hasher = hashlib.new(name)
    hasher.update(f"blob {size}\0".encode())
    if data is not None:
        hasher.update(data)
        return hasher.hexdigest()
    with open(path, "rb") as handle:
        while block := handle.read(CHUNK):
            hasher.update(block)
    return hasher.hexdigest()


def written(scope: Any, base: str, path: str) -> bytes | None:
    """The bytes a checkout of the base would leave at `path`, its smudge side applied (`eol`, `ident`, `filter=`,
    `working-tree-encoding`): git's own `cat-file --filters`. None where git cannot say."""
    try:
        done = subprocess.run(["git", "cat-file", "--filters", f"{base}:{path}"], cwd=scope.ROOT, capture_output=True,
                              check=False)
    except (OSError, ValueError):
        return None
    return done.stdout if done.returncode == 0 else None


def raw_differs(scope: Any, base: str, entry: tuple[str, str, int], path: str, full: str) -> bool:
    """Whether the file at `full` is not what the base's blob `entry` is, read raw: its bytes as they lie on disk
    against the blob's, and where those differ, against what a checkout of the base would write there. A file git
    wrote as its attributes ask (CRLF under `eol=crlf`) is the base's; an edit a filter hides is not."""
    mode, blob, size = entry
    name = "sha1" if len(blob) == 40 else "sha256"
    try:
        found = os.lstat(full)
        if stat.S_ISLNK(found.st_mode):
            target = os.readlink(os.fsencode(full))
            return mode != SYMLINK or digest(name, len(target), target, full) != blob
        if not stat.S_ISREG(found.st_mode) or mode not in (REGULAR, EXECUTABLE):
            return True
        if (mode == EXECUTABLE) != bool(found.st_mode & stat.S_IXUSR):
            return True
        if found.st_size == size and digest(name, size, None, full) == blob:
            return False
        expected = written(scope, base, path)
        if expected is None:
            return True
        with open(full, "rb") as handle:
            return handle.read() != expected
    except OSError:
        return True


def tree(scope: Any, base: str) -> dict[str, tuple[str, str, int]]:
    """Every blob the base commit holds: path -> (mode, object id, size). A gitlink is not a file and is left out."""
    listed = scope.git_must("ls-tree", "-r", "-l", "-z", "--full-tree", base).split("\0")
    held: dict[str, tuple[str, str, int]] = {}
    for line in listed:
        head, _, path = line.partition("\t")
        fields = head.split()
        if len(fields) == 4 and fields[1] == BLOB and fields[3].isdigit():
            held[path] = (fields[0], fields[2], int(fields[3]))
    return held


def changed(scope: Any, base: str) -> list[str]:
    """Git's changed paths and the paths whose raw bytes or mode differ from the base's blob, sorted."""
    found = set(scope.changed_files(base))
    top = str(scope.git_must("rev-parse", "--show-toplevel")).removesuffix("\n")  # git's paths are the top's
    for path, entry in tree(scope, base).items():
        if path in found or path in MAKEFILES:  # the Makefile is judged by the border that reads its text (D140)
            continue
        if raw_differs(scope, base, entry, path, os.path.join(top, path)):
            found.add(path)
    return sorted(found)
