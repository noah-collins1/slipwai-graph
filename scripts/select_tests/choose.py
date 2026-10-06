"""Which test modules a change reaches, and the one reason each runs or is skipped.

A module runs when it is undeclared, or when something it declares is reached: its own file or a helper it imports
changed, a file it reads, or a configuration it generates. The reasons are listed in one order — *undeclared*, the
module's own file, `reads`, the configuration, the helper — and the first is the one printed.
A skipped module has one reason too, in the words of what it does not read.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, NamedTuple

from . import declarations, rules

UNDECLARED = "undeclared"


class Reason(NamedTuple):
    """Why a module runs. `narrowable` says it was reached by a backend's own configuration only."""

    text: str
    narrowable: bool = False


class Verdict(NamedTuple):
    """A module's answer: the reasons it runs (none: it is skipped) and, for a skipped one, why."""

    module: str
    reasons: tuple[Reason, ...]
    skip: str

    @property
    def runs(self) -> bool:
        return bool(self.reasons)


class Reach(NamedTuple):
    """What the changed paths reach: files, and configurations (`every`, or the `(axis, option)` pairs named)."""

    paths: tuple[str, ...]
    every: bool
    configs: tuple[tuple[str, str], ...]
    plain: bool  # some changed path carries no configuration at all
    narrowable: frozenset[tuple[str, str]]  # the pairs only a backend's own assets reached
    test_files: tuple[str, ...] = ()  # the names of the `tests/<name>.py` files that changed


def reach(paths: list[str], claims: Mapping[str, rules.Claim]) -> Reach:
    pairs: list[tuple[str, str]] = []
    for path in paths:
        pairs.extend(pair for pair in claims[path].configs if pair not in pairs)
    narrow = {pair for pair in pairs
              if all(pair in claims[path].narrowable for path in paths if pair in claims[path].configs)
              and not any(claims[path].every for path in paths)}
    return Reach(tuple(paths), any(claims[path].every for path in paths), tuple(pairs),
                 any(not claims[path].every and not claims[path].configs for path in paths), frozenset(narrow),
                 tuple(claims[path].test_file for path in paths if claims[path].test_file))


def reads_match(path: str, entry: str) -> bool:
    return path == entry or path.startswith(entry.rstrip("/") + "/")


def reasons_for(module: str, tree: declarations.Tree, declaration: declarations.Declaration,
                reached: Reach) -> list[Reason]:
    """Every reason a declared module is reached, in the one order they are told: its own file, the files it reads, the
    configurations it generates, the helpers it imports."""
    found: list[Reason] = []
    if module in reached.test_files:
        found.append(Reason(f"`tests/{module}.py` changed"))
    for entry in sorted(declaration.reads):
        if any(reads_match(path, entry) for path in reached.paths):
            found.append(Reason(f"reads `{entry}`"))
    if reached.every and declaration.generates:
        found.append(Reason("reads every configuration"))
    for axis, option in reached.configs:
        if declaration.admits(axis, option):
            found.append(Reason(f"reads the {option} configuration", narrowable=(axis, option) in reached.narrowable))
    for name in reached.test_files:
        if name != module and name in tree.imported[module]:
            found.append(Reason(f"imports `tests/{name}.py`"))
    return found


def skip_reason(reached: Reach) -> str:
    """What a module that was not reached does not read: the configurations that changed, the files, or both."""
    changed = reached.every or bool(reached.configs)
    if not changed:
        return "reads none of the changed files"
    options = "" if reached.every else " " + ", ".join(dict.fromkeys(option for _, option in reached.configs))
    said = f"reads no{options} configuration"
    return f"{said} and none of the changed files" if reached.plain else said


class Selection(NamedTuple):
    """Every module's verdict, and the backends the matrix narrows to: those only a backend's own assets reached, and
    the backends of the catalog that stay out of it."""

    verdicts: list[Verdict]
    backends: tuple[str, ...]
    left_out: tuple[str, ...]

    def narrows(self, verdict: Verdict) -> bool:
        """A module runs narrowed when every reason it runs is a backend's own assets (a module with one other reason,
        an undeclared one included, runs whole)."""
        return bool(self.backends) and verdict.runs and all(reason.narrowable for reason in verdict.reasons)

    def narrowed(self) -> list[Verdict]:
        return [verdict for verdict in self.verdicts if self.narrows(verdict)]


def select(tree: declarations.Tree, paths: list[str], catalog: Mapping[str, Any]) -> Selection:
    """Every test module, in name order, with whether it runs and why; and the backends it narrows to."""
    claims = {path: claim for path in paths if (claim := rules.claim(path, catalog)) is not None}
    reached = reach(paths, claims)
    verdicts: list[Verdict] = []
    for module in sorted(name for name in tree.sources if declarations.is_module(name)):
        declaration, _ = tree.effective(module)
        if declaration is None:
            verdicts.append(Verdict(module, (Reason(UNDECLARED),), ""))
            continue
        found = reasons_for(module, tree, declaration, reached)
        verdicts.append(Verdict(module, tuple(found), "" if found else skip_reason(reached)))
    named = sorted(option for axis, option in reached.narrowable if axis == "backend")
    left_out = sorted(rules.names(catalog, "backends") - set(named)) if named else []
    return Selection(verdicts, tuple(named), tuple(left_out))


def choose(tree: declarations.Tree, paths: list[str], catalog: Mapping[str, Any]) -> list[Verdict]:
    return select(tree, paths, catalog).verdicts
