"""What a change is measured against: the trunk the scoped gate measures against, or the tree `SINCE` names.

The scoped gate's own scripts do the measuring, loaded where they ship and never changed (D156 point 1): they are
`assets/toolkit/scripts/check-slice-scope.py` and the package `verify_scoped` beside it. Where they cannot be loaded, or
git fails, every module runs (data-model rows 8-11).
"""
from __future__ import annotations

import importlib
import importlib.util
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any, NamedTuple

from . import git_out
from .report import Full, full_line, printable

sys.dont_write_bytecode = True

SCRIPTS = "assets/toolkit/scripts"


class Scoped(NamedTuple):
    """The scoped gate's two loaded parts: `check-slice-scope.py` and `verify_scoped.changes`."""

    scope: Any
    changes: Any


class Base(NamedTuple):
    """What the change is compared with: the commit, the first line that says so, the ref's name and its short id."""

    commit: str
    line: str
    name: str
    short: str
    kind: str  # `trunk` or `since`


def cannot_be_established(why: object) -> Full:
    return Full(full_line(f"the change set cannot be established — {printable(why)}"))


def load_scoped(root: Path) -> Scoped:
    """Both scripts, by path, as they ship. Nothing is written beside them; a script that does not load is row 11."""
    scripts = root / SCRIPTS
    sys.dont_write_bytecode = True
    try:
        spec = importlib.util.spec_from_file_location("check_slice_scope", scripts / "check-slice-scope.py")
        package = importlib.util.spec_from_file_location(
            "verify_scoped", scripts / "verify_scoped" / "__init__.py",
            submodule_search_locations=[str(scripts / "verify_scoped")])
        if spec is None or spec.loader is None or package is None or package.loader is None:
            raise ImportError(f"{SCRIPTS} holds no scoped gate")
        scope = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scope)
        loaded = importlib.util.module_from_spec(package)
        sys.modules["verify_scoped"] = loaded
        package.loader.exec_module(loaded)
        changes = importlib.import_module("verify_scoped.changes")
    except (Exception, SystemExit) as error:
        raise cannot_be_established(f"the scoped gate's scripts could not be loaded: {error}") from error
    return Scoped(scope, changes)


def short_of(root: Path, commit: str) -> str:
    status, out = git_out(root, "rev-parse", "--short", commit)
    return out.strip() if status == 0 and out.strip() else commit[:7]


def since_base(root: Path, ref: str) -> Base:
    """`SINCE=<ref>`: the commit the ref names, which must share history with `HEAD` (row 8)."""

    def unresolved(why: str) -> Full:
        return Full(full_line(f"SINCE={printable(ref)} could not be resolved — {why}"))

    if ref.startswith("-"):
        raise unresolved("it names no commit")
    status, out = git_out(root, "rev-parse", "--verify", "-q", f"{ref}^{{commit}}")
    commit = out.strip()
    if status == 127:
        raise unresolved(printable(out))
    if status or not commit:
        raise unresolved("it names no commit")
    status, out = git_out(root, "merge-base", "HEAD", commit)
    if status == 1:
        raise unresolved("it shares no history with HEAD")
    if status:
        raise unresolved(f"git could not compare it with HEAD: {printable(out)}")
    short = short_of(root, commit)
    line = (f"compared with `{printable(ref)}` at {short}, named by SINCE — taken as passing on the word of whoever "
            "named it")
    return Base(commit, line, printable(ref), short, "since")


def trunk_base(root: Path, scoped: Scoped) -> Base:
    """The trunk, as `check-slice-scope.merge_base()` tells it (row 9)."""
    try:
        found = scoped.scope.merge_base()
    except (Exception, SystemExit) as error:
        raise cannot_be_established(f"the trunk could not be read: {error}") from error
    if found.commit is None:
        trunk = printable(found.named or found.trunk)
        why = found.bare or f"there is no `{trunk}` to compare with, or it shares no history with this branch"
        raise Full(full_line(f"the trunk cannot be told — {printable(why, 400, quote=False)}"))
    short = short_of(root, found.commit)
    name = printable(found.named or found.trunk)
    return Base(found.commit, f"compared with `{name}` at {short} (the trunk)", name, short, "trunk")


def establish(root: Path, env: Mapping[str, str]) -> Base:
    """The base this run compares with: `SINCE` where it is given, else the trunk. Raises the line where it cannot."""
    ref = env.get("SINCE", "")
    if ref:
        return since_base(root, ref)
    return trunk_base(root, load_scoped(root))
