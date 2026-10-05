"""Which units a change runs, and the reason printed for each: the selection `verify-scoped.py` makes from the record.

A unit runs when, in this order, a changed path is one of its file inputs (`<path> changed`), a contract it consumes
changed (`consumes <contract> (<path>)`), or a unit it shares a recipe or a build directory with runs (`shares one recipe
with <unit>`, `shares a build directory with <unit>`). Changed paths are taken in sorted order, so the reason a unit
names is the first path that chose it; every unit is named once, the first reason that holds winning.
"""
from __future__ import annotations

import re
import sys
from typing import Any, NamedTuple

sys.dont_write_bytecode = True

from .record import Database  # noqa: E402
from .table import GATE_UNITS  # noqa: E402

CONSUMING = ("typecheck", "test")  # what a contract's consumer re-proves when the contract changes
BUILD_DIRECTORY_FAMILIES = ("go", "java")  # whose three units build in one directory
UNCHANGED = "none of its inputs changed"


class Choice(NamedTuple):
    unit: str
    runs: bool
    reason: str


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


def first_reason(check: dict[str, Any], contracts: list[dict[str, Any]], paths: list[str]) -> str | None:
    """Why a changed path chooses the check, by the order of the reasons: it reads the path, then it consumes it."""
    path = read_by(check, paths)
    return f"{path} changed" if path is not None else consumed(check, contracts, paths)


def choose(record: dict[str, Any], data: Database, changed: list[str]) -> list[Choice]:
    """Every unit of the record, in its order, with whether it runs and why."""
    paths = sorted(changed)
    checks: dict[str, dict[str, Any]] = record["checks"]
    reasons: dict[str, str] = {}
    for unit, check in checks.items():
        if check["always"] or check["inputs"] is None:
            continue
        found = first_reason(check, record["contracts"], paths)
        if found is not None:
            reasons[unit] = found
    chosen = list(reasons)
    for unit, check in checks.items():
        if unit in reasons or check["gate"] not in GATE_UNITS or check["inputs"] is None:
            continue
        found = sharing(unit, check, record, data, chosen)
        if found is not None:
            reasons[unit] = found
    return [Choice(unit, unit in reasons, reasons.get(unit, UNCHANGED)) for unit, check in checks.items()
            if not (check["always"] or check["inputs"] is None)]
