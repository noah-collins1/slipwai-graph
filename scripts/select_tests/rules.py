"""What a changed path can reach: the first row of data-model *The path rules* that claims it.

A row is data — the paths it names, the rule's words — in one table, so the order is one place. A path no row claims
is not an error, it is the answer: nothing says what it reaches, so every module runs.
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, NamedTuple

from .report import Full, full_line, printable

BROADENS = "its effect cannot be established"
UNCLAIMED = "no rule claims it"


class Claim(NamedTuple):
    """The row that claims a path: its words, whether it makes the run whole, and what it reaches — every
    configuration, or the `(axis, option)` pairs named; `backend_asset` says the path is a backend's own asset, which
    is what lets the matrix narrow to the backends it names."""

    rule: str
    full: bool
    every: bool = False
    configs: tuple[tuple[str, str], ...] = ()
    backend_asset: bool = False


class Row(NamedTuple):
    """One row of the table: the rule's words, the paths it names and the directories it holds."""

    rule: str
    paths: tuple[str, ...] = ()
    trees: tuple[str, ...] = ()
    full: bool = False

    def holds(self, path: str) -> bool:
        return path in self.paths or any(path.startswith(tree) for tree in self.trees)


# The first row of the data model: every path whose effect cannot be established. Each row's words beside it.
FULL_ROWS = (
    Row("the catalog", paths=("catalog.json",), full=True),
    Row("the pruner", paths=("assets/backing-services/prune.py",), full=True),
    Row("the generator", trees=("src/",), full=True),
    Row("the root Makefile", paths=("Makefile", "GNUmakefile", "makefile"), full=True),
    Row("the verify script", paths=("scripts/verify",), full=True),
    Row("the pinned development tooling", paths=("requirements-dev.txt",), full=True),
    Row("the package definition", paths=("pyproject.toml",), full=True),
    Row("the version", paths=("VERSION",), full=True),
    Row("the project record", paths=("project.json",), full=True),
    Row("the command's launcher", paths=("slipwai",), full=True),
    Row("the ignore rules", paths=(".gitignore",), full=True),
    Row("the attribute rules", paths=(".gitattributes",), full=True),
    Row("the selector", paths=("scripts/select-tests.py",), trees=("scripts/select_tests/",), full=True),
)
# `assets/backing-services/` holds files and directories no backend owns: every configuration reads them.
OTHER_BACKING_SERVICES = ("keycloak", "sql", "docker-compose.yml", "env.example")
# The rows after those: a change claimed here reaches the modules whose `reads` name it, and nothing else.
SELECTING = ("docs/", "specs/", "delivery/", ".github/", ".specify/", ".claude/", "changelog.d/", "coordination-lean/",
             "scripts/", "tests/")
SELECTING_FILES = ("README.md", "CHANGELOG.md", "AGENTS.md", "CLAUDE.md", "CONTRIBUTING.md", "SECURITY.md", "LICENSE",
                   "NOTICE")


def own_tests(path: str) -> bool:
    return path.startswith("tests/") and "/" not in path[len("tests/"):] and (
        path.startswith("tests/test_select_tests_") or path.startswith("tests/select_fixture"))


def load_catalog(root: Path) -> Mapping[str, Any]:
    """`catalog.json` as the working tree has it (a changed catalog is full anyway, but a path is claimed by it)."""
    try:
        found = json.loads((root / "catalog.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise Full(full_line(f"the change set cannot be established — catalog.json cannot be read: "
                             f"{printable(error)}")) from error
    if not isinstance(found, dict):
        raise Full(full_line("the change set cannot be established — catalog.json is not an object"))
    return found


def names(catalog: Mapping[str, Any], axis: str) -> frozenset[str]:
    value = catalog.get(axis)
    return frozenset(value) if isinstance(value, dict) else frozenset()


def backends_named(catalog: Mapping[str, Any], name: str) -> tuple[str, ...]:
    """The backends a directory name stands for: the backend of that name, and the backends of the family of it."""
    found = catalog.get("backends")
    if not isinstance(found, dict):
        return ()
    return tuple(backend for backend, record in found.items()
                 if backend == name or (isinstance(record, dict) and record.get("family") == name))


def asset_claim(path: str, catalog: Mapping[str, Any]) -> Claim | None:
    """The row below the first that claims a path under `assets/`, with what it reaches (data-model *The path rules*).
    A directory the catalog does not name is not claimed: nothing says what it reaches."""
    parts = path.split("/")
    if len(parts) < 3:
        return None
    tree, name = parts[1], parts[2]
    if tree in ("languages", "backing-services") and len(parts) > 3 and (backends := backends_named(catalog, name)):
        return Claim(f"the {name} assets", False, configs=tuple(("backend", b) for b in backends), backend_asset=True)
    if tree == "backing-services" and name in OTHER_BACKING_SERVICES:
        return Claim("the shared backing services", False, every=True)
    if tree == "toolkit":
        return Claim("the toolkit", False, every=True)
    if tree == "adoption":
        return Claim("the adoption assets", False, configs=(("command", "adopt"),))
    for directory, axis, axis_name in (("frontends", "frontend", "frontends"), ("profiles", "profile", "profiles"),
                                       ("targets", "target", "targets")):
        if tree == directory and len(parts) > 3 and name in names(catalog, axis_name):
            return Claim(f"the {name} assets", False, configs=((axis, name),))
    return None


def claim(path: str, catalog: Mapping[str, Any]) -> Claim | None:
    """The first row that claims `path`, or None where no row does."""
    for row in FULL_ROWS:
        if row.holds(path):
            return Claim(row.rule, True)
    if own_tests(path):
        return Claim("the selector's own tests", True)
    if path.startswith("assets/"):
        return asset_claim(path, catalog)
    if path in SELECTING_FILES or path.startswith(SELECTING):
        return Claim("the files its readers name", False)
    return None


def broadening(path: str, catalog: Mapping[str, Any]) -> str | None:
    """Why `path` makes the run whole — the rule's words — or None where it only selects."""
    found = claim(path, catalog)
    if found is None:
        return UNCLAIMED
    return f"{found.rule}: {BROADENS}" if found.full else None
