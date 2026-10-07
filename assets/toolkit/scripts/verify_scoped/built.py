"""Directories the baseline exempts that a walking check reads (T030, D194).

`check-imports` and `check-migrations` read every directory but D45's four and a recorded Java root's `target` (D52):
the gate is never switched off by what a slice names a directory. The verify stamp's key leaves some directories out
(`dist/`, `coverage/`, `target/`, `.build/`, …), so a file in one is compared by nothing the scoped gate has. Where such
a directory exists in the working tree under a declared input of one of the two, and holds a file that check reads, the
check keeps no recorded inputs — it runs, claims nothing — and the reason names the directory.

Each list is the owner's, loaded and never copied: the stamp's `exempt_entry`, each check's own `skipped` (which
directories it never descends) and the constants by which it picks the files it opens. What the gate's own runs leave
there and neither check opens (a web build's `.js`, a coverage report) changes nothing.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from functools import cache
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

SCRIPTS = Path(__file__).resolve().parent.parent
EVERYTHING = "./"
WHY = ("`{directory}` exists under one of its inputs and holds a file it reads, and the baseline exempts `{pattern}`, "
       "so no change there can be compared")


@cache
def script(filename: str) -> Any:
    """A script beside the package, loaded under a name of its own and never copied; None where it is not there."""
    path = SCRIPTS / filename
    spec = importlib.util.spec_from_file_location("scoped_reads_" + filename.removesuffix(".py").replace("-", "_"), path)
    if spec is None or spec.loader is None or not path.is_file():
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def imports_reads(module: Any, path: Path) -> bool:
    return path.suffix in module.SOURCE_SUFFIXES  # every rule of `check-imports` opens only these


def migrations_reads(module: Any, path: Path) -> bool:  # `check-migrations.migrations()`'s own test of a file
    return (path.suffix in module.SUFFIXES and module.MIGRATION_NAME.match(path.name) is not None
            and path.parent.name in module.MIGRATION_DIRECTORIES)


READERS = {"check-imports": ("check-imports.py", imports_reads), "check-migrations": ("check-migrations.py", migrations_reads)}


def holds_read(module: Any, top: Path, reads: Any) -> bool:
    """Whether a file under `top`, in a directory the check descends, is one it opens."""
    for current, directories, files in os.walk(top):
        here = Path(current)
        directories[:] = [name for name in directories if not module.skipped(here, name)]
        if any(reads(module, here / name) for name in files):
            return True
    return False


def found_in(root: Path, entries: list[str], module: Any, reads: Any, stamp: Any) -> str | None:
    """The first exempt directory under the check's directory inputs that holds a file it opens, as words."""
    tops = [entry for entry in entries if entry.endswith("/") and entry != EVERYTHING]
    tops = [entry for entry in tops if not any(entry != other and entry.startswith(other) for other in tops)]
    for entry in sorted(tops):
        for current, directories, _ in os.walk(root / entry):
            here = Path(current)
            directories[:] = sorted(name for name in directories if not module.skipped(here, name))
            for name in list(directories):
                relative = (here / name).relative_to(root).as_posix() + "/"
                exempt = stamp.exempt_entry(relative)
                if exempt is not None and exempt[0].endswith("/") and holds_read(module, here / name, reads):
                    return WHY.format(directory=relative, pattern=exempt[0])
    return None


def with_built(checks: dict[str, Any], root: Path) -> None:
    """Each walking check with an exempt directory it reads under its inputs keeps no recorded inputs."""
    stamp = script("verify-stamp.py")
    if stamp is None:
        return
    for name, (filename, reads) in READERS.items():
        entry = checks.get(name)
        module = script(filename) if entry is not None and entry["inputs"] is not None else None
        if module is None:
            continue
        words = found_in(root, entry["inputs"]["files"], module, reads, stamp)
        if words is not None:
            entry.update(inputs=None, claims=False, always=words)
