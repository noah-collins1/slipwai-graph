"""Which units a change runs, and the reason printed for each: the selection `verify-scoped.py` makes from the record.

A check that always runs (the record's `always`: why it runs on every scoped run, or `no recorded inputs`) is chosen with
that reason whatever changed, and claims nothing. Any other unit runs when, in this order, a changed path is one of its
file inputs (`<path> changed`), a contract it consumes changed (`consumes <contract> (<path>)`), an obligation a person
declared names it (`obligation <name> (<path>)`), or a unit it shares a recipe or a build directory with runs
(`shares one recipe with <unit>`, `shares a build directory with <unit>`). Changed paths are taken in sorted order, so the reason a unit names is the first path that chose it; every unit is named once,
the first reason that holds winning. After the paths come the machine's: a tool the baseline saw answer differently
(`<tool> answers differently from the baseline`) or a variable whose digest differs (`<NAME> differs from the baseline`),
for the units whose recorded inputs name it; a unit that shares a recipe with one of those runs with it.
"""
from __future__ import annotations

import json
import re
import sys
from collections.abc import Callable, Mapping
from typing import Any, NamedTuple

sys.dont_write_bytecode = True

from .record import Database  # noqa: E402
from .table import GATE_UNITS  # noqa: E402

CONSUMING = ("typecheck", "test")  # what a contract's consumer re-proves when the contract changes
BUILD_DIRECTORY_FAMILIES = ("go", "java")  # whose three units build in one directory
UNCHANGED = "none of its inputs changed"
MAKEFILES = ("Makefile", "GNUmakefile", "makefile")
PROJECT_JSON = "project.json"
WALKS = ("apps/", "packages/")  # directories a check walks whole: a changed path there chooses it, and is not known by it


class Choice(NamedTuple):
    unit: str
    runs: bool
    reason: str


class Drift(NamedTuple):
    """What differs between the machine and the baseline: the tools that answer differently, the variables that differ."""
    tools: frozenset[str]
    variables: frozenset[str]


def baseline_of(text: str | None, branch: str, exists: bool) -> tuple[dict[str, Any] | None, str]:
    """The baseline a file holds as a dict, or None with why it cannot be used: none yet on this branch (no file at
    all), another branch's, or one that is no file, does not parse or has not the shape `verify-stamp.py` writes."""
    if text is None:
        return None, "it cannot be read" if exists else "none yet on this branch"
    try:
        found = json.loads(text)
    except ValueError:
        return None, "it cannot be read"
    if not (isinstance(found, dict) and isinstance(found.get("branch"), str)
            and all(isinstance(found.get(key), dict) and all(isinstance(item, str) for item in found[key].values())
                    for key in ("tools", "variables"))):
        return None, "it cannot be read"
    return (found, "") if found["branch"] == branch else (None, f"it was taken on {found['branch']}")


def drift(baseline: Mapping[str, Any], tools: Mapping[str, str], variables: Mapping[str, str]) -> Drift:
    """The tools the machine answers for otherwise than the baseline recorded, and the variables whose digests differ;
    a name only one side has differs."""
    moved = {name for name in baseline["tools"].keys() | tools.keys() if baseline["tools"].get(name) != tools.get(name)}
    return Drift(frozenset(moved), frozenset(name for name in baseline["variables"].keys() | variables.keys()
                                             if baseline["variables"].get(name) != variables.get(name)))


def is_input(path: str, entry: str) -> bool:
    """Whether a changed path is the file an input names, or is under the directory it names (a directory ending `/`,
    a deleted file of that name included)."""
    return entry == "./" or path == entry.rstrip("/") or (entry.endswith("/") and path.startswith(entry))


def read_by(check: dict[str, Any], paths: list[str]) -> str | None:
    """The first changed path that is one of the check's file inputs; None where it has none or none changed."""
    files = (check["inputs"] or {}).get("files", [])
    return next((path for path in paths if any(is_input(path, entry) for entry in files)), None)


def consumed(check: dict[str, Any], contracts: list[dict[str, Any]], paths: list[str]) -> str | None:
    """`consumes <contract> (<path>)` for the first contract the check's deployable consumes that a changed path is in."""
    if check["gate"] not in CONSUMING:
        return None
    for contract in contracts:
        if not set(check["components"]) & set(contract["consumers"]):
            continue
        path = next((path for path in paths if any(is_input(path, entry) for entry in contract["paths"])), None)
        if path is not None:
            return f"consumes {contract['id']} ({path})"
    return None


def sharing(unit: str, check: dict[str, Any], record: dict[str, Any], data: Database, chosen: list[str]) -> str | None:
    """A unit that a chosen unit takes along: one it shares its only recipe line with, or its deployable's build."""
    own = data.recipes.get(unit, [])
    family = [need for need in data.needs.get(unit, []) if re.fullmatch(rf"{check['gate']}_\w+", need)]
    if not own and family:
        peer = next((other for other in chosen if family[0] in data.needs.get(other, [])), None)
        if peer is not None:
            return f"shares one recipe with {peer}"
    deployable = record["deployables"].get(check["components"][0]) if check["components"] else None
    if deployable is not None and deployable["family"] in BUILD_DIRECTORY_FAMILIES:
        peer = next((other for other in chosen if record["checks"][other]["components"] == check["components"]), None)
        if peer is not None:
            return f"shares a build directory with {peer}"
    return None


def bound(unit: str, record: dict[str, Any], paths: list[str]) -> str | None:
    """`obligation <name> (<path>)` for the first declared obligation that names the unit and whose component a changed
    path is in: the first path, in sorted order, under any of the obligation's components."""
    for obligation in record["obligations"]:
        if unit not in obligation["checks"]:
            continue
        under = [record["deployables"][name]["path"] + "/" for name in obligation["components"]]
        path = next((path for path in paths if any(is_input(path, entry) for entry in under)), None)
        if path is not None:
            return f"obligation {obligation['name']} ({path})"
    return None


def first_reason(unit: str, check: dict[str, Any], record: dict[str, Any], paths: list[str]) -> str | None:
    """Why a changed path chooses the check, by the order of the reasons: it reads the path, it consumes it through a
    contract, then an obligation a person declared names it."""
    path = read_by(check, paths)
    if path is not None:
        return f"{path} changed"
    return consumed(check, record["contracts"], paths) or bound(unit, record, paths)


def moved(check: dict[str, Any], drifted: Drift | None) -> str | None:
    """Why the machine chooses the check: the first of its tools that answers differently, else the first of its
    variables that differs; None for a check with no recorded inputs, or where nothing moved."""
    if drifted is None or check["inputs"] is None:
        return None
    tool = next((name for name in check["inputs"]["tools"] if name in drifted.tools), None)
    if tool is not None:
        return f"{tool} answers differently from the baseline"
    name = next((name for name in check["inputs"]["variables"] if name in drifted.variables), None)
    return None if name is None else f"{name} differs from the baseline"


def choose(record: dict[str, Any], data: Database, changed: list[str], drifted: Drift | None = None) -> list[Choice]:
    """Every unit of the record, in its order, with whether it runs and why: a path, a contract, then what the machine
    says, each pass followed by the units that share a recipe or a build with a unit chosen so far."""
    paths = sorted(changed)
    checks: dict[str, dict[str, Any]] = record["checks"]
    reasons: dict[str, str] = {}

    def take(why: Callable[[str, dict[str, Any]], str | None]) -> None:
        for unit, check in checks.items():
            found = None if unit in reasons else why(unit, check)
            if found is not None:
                reasons[unit] = found

    def along(unit: str, check: dict[str, Any]) -> str | None:
        return sharing(unit, check, record, data, list(reasons)) if check["gate"] in GATE_UNITS else None

    take(lambda unit, check: check["always"] or first_reason(unit, check, record, paths))
    take(along)
    take(lambda unit, check: moved(check, drifted))
    take(along)
    return [Choice(unit, unit in reasons, reasons.get(unit, UNCHANGED)) for unit in checks]


def claimed(path: str, record: dict[str, Any]) -> bool:
    """Whether a deployable, a contract or a claiming check's file inputs hold the path: a check that always runs and
    one with no recorded inputs claim nothing, however much they read; a directory a check walks whole (`apps/`,
    `packages/`) is read by it and known by none, since a package nobody builds is a path this script cannot reason about."""
    if any(is_input(path, entry) for contract in record["contracts"] for entry in contract["paths"]):
        return True
    return any(check["claims"] and any(is_input(path, entry) for entry in (check["inputs"] or {}).get("files", [])
                                       if entry not in WALKS) for check in record["checks"].values())


def unknown(record: dict[str, Any], changed: list[str], is_gate_script: Callable[[str], bool]) -> list[tuple[str, str]]:
    """The changed paths this script cannot reason about, in sorted order, each with what makes it so: the project's
    record, a makefile or a gate script (the gate itself changed), or a path nothing claims."""
    found = []
    for path in sorted(changed):
        if path == PROJECT_JSON:
            found.append((path, "it is project.json"))
        elif path in MAKEFILES:
            found.append((path, "it is the Makefile"))
        elif is_gate_script(path):
            found.append((path, "it is a gate script under scripts/"))
        elif not claimed(path, record):
            found.append((path, "no deployable, contract or check claims it"))
    return found
