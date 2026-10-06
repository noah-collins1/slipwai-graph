"""What a change is measured against: the trunk the scoped gate measures against, or the tree `SINCE` names.

The scoped gate's own scripts do the measuring, loaded where they ship and never changed (D156 point 1): they are
`assets/toolkit/scripts/check-slice-scope.py` and the package `verify_scoped` beside it. Where they cannot be loaded, or
git fails, every module runs (data-model rows 8-11).
"""
from __future__ import annotations

import functools
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
TREES = ("assets", "src", "tests")
# D119: the interpreter caches, named once — a directory and two suffixes
CACHE_DIRECTORY = "__pycache__"
CACHE_SUFFIXES = (".pyc", ".pyo")


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


@functools.cache
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


class ChangeSet(NamedTuple):
    """What changed since the base: every path (sorted), the ones the base's own diff names (the rest are the unpushed
    range's), the trunk's unpushed `Span` and the first line of the report (the base's, with D153's clause)."""

    paths: list[str]
    own: frozenset[str]
    span: Any
    line: str
    against: str = ""  # the base as the summary names it: `main` at 8072724


class Choice(NamedTuple):
    """The shape `verify_scoped.changes.unpushed_words` rewrites: whether a unit runs, and why."""

    runs: bool
    reason: str


def change_set(root: Path, base: Base) -> ChangeSet:
    """D117 rule 2 as D125 counts it, from `changes.changed`, plus D153's unpushed range for the trunk (rows 10, 11)."""
    scoped = load_scoped(root)
    span = scoped.changes.Span()
    try:
        if base.kind == "trunk":
            span = scoped.changes.unpushed(scoped.scope, base.commit)
        if span.failure:
            raise Full(full_line(printable(span.failure, 600, quote=False)))
        own = frozenset(scoped.changes.changed(scoped.scope, base.commit))
    except Full:
        raise
    except (Exception, SystemExit) as error:  # `CouldNotCompare` is git's own first line; the rest, the error's
        raise cannot_be_established(error) from error
    line = base.line + (f"; {printable(span.note, 600, quote=False)}" if span.note else "")
    return ChangeSet(sorted(own | set(span.paths)), own, span, line, f"`{base.name}` at {base.short}")


def changed_words(root: Path, found: ChangeSet, path: str) -> str:
    """How a changed path is worded: `<path>` changed, or D153's own words where only the unpushed range changed it."""
    plain = Choice(True, f"{printable(path)} changed")
    if found.span is None or path in found.own or path not in found.span.paths:
        return f"`{printable(path)}` changed"
    scoped = load_scoped(root)
    return str(scoped.changes.unpushed_words([plain], set(found.own), found.span, scoped.scope)[0].reason)


def is_cache(path: str) -> bool:
    """D119's interpreter caches, the only files git may ignore without the run saying so."""
    return CACHE_DIRECTORY in path.split("/") or path.endswith(CACHE_SUFFIXES)


def ignored_listing(root: Path) -> list[str]:
    """Every file git ignores under `assets/`, `src/` or `tests/`, caches included."""
    status, out = git_out(root, "ls-files", "-z", "--others", "--ignored", "--exclude-standard", "--", *TREES)
    if status:
        raise cannot_be_established(f"git could not list the ignored files: {printable(out)}")
    return sorted(path for path in out.split("\0") if path)


def ignored_files(root: Path) -> list[str]:
    """Every file git ignores under `assets/`, `src/` or `tests/` that is not an interpreter cache (research R-6)."""
    return [path for path in ignored_listing(root) if not is_cache(path)]


def cache_files(root: Path) -> list[str]:
    """The interpreter caches git ignores under `assets/`: never a reason to run everything and claimed by no
    configuration, but a file a module that reads the directory it sits in reads (T026, AC-S38-10)."""
    return [path for path in ignored_listing(root) if is_cache(path) and path.startswith("assets/")]


def replay_changes(root: Path, span: str) -> ChangeSet:
    """The change set of `<base>..<tip>`: the paths that differ between the two trees, both sides of a rename, taken
    from the commits and never the working tree (AC-S38-15). A span that cannot be read is row 11."""
    start, dots, tip = span.partition("..")
    if not dots or not start or not tip or tip.startswith(".") or start.startswith("-") or tip.startswith("-"):
        raise cannot_be_established(f"`{printable(span)}` is not a range of commits written <base>..<tip>")
    commits = []
    for name in (start, tip):
        status, out = git_out(root, "rev-parse", "--verify", "-q", f"{name}^{{commit}}")
        if status or not out.strip():
            raise cannot_be_established(f"`{printable(name)}` names no commit")
        commits.append(out.strip())
    status, out = git_out(root, "diff", "--no-renames", "--name-only", "-z", commits[0], commits[1])
    if status:
        raise cannot_be_established(f"git could not compare the range: {printable(out)}")
    paths = sorted(path for path in out.split("\0") if path)
    short = short_of(root, commits[0])
    line = f"compared with `{printable(start)}` at {short}, replaying `{printable(span)}`"
    return ChangeSet(paths, frozenset(paths), None, line, f"`{printable(start)}` at {short}")
