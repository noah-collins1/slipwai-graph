#!/usr/bin/env python3
"""`make mutation` and `make mutation-full` for a Python service: mutmut, held to what its own `.meta` files say.

    python3 scripts/mutmut-mutation.py <service> [--file <path within the service> ...]

Without `--file` the whole of the service's `[tool.mutmut]` `source_paths` is mutated; `--file`, repeatable, hands over
only those files. The verdict is read from the `mutants/<file>.meta` files mutmut writes, never from mutmut's exit status
(D212).

The configuration is read here, by the subset of `[tool.mutmut]` the factory writes (`targets`), so a `--file` is held
against what mutmut would mutate (`matched`) and a path mutmut would misread is refused (`refused`): `mutmut run` takes
mutant names as `fnmatch` patterns, so a `*`, `?` or `[` in a path is a pattern and not the file.

This is the skeleton past the configuration: it refuses to run, which can only fail, never pass.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

USAGE = "mutation: usage: mutmut-mutation.py <service> [--file <path within the service> ...]"
NOT_WIRED = "mutation: mutmut is not wired by this script yet; nothing was run"
# What `fnmatch` reads as syntax: the characters that make a path a pattern over mutant names, not a name.
OPENERS = "*?["
# The packages whose version decides which mutants exist: mutmut, and libcst with everything libcst resolves to (D222).
ROOT_PACKAGE = "mutmut"
PARSER_PACKAGE = "libcst"


class Unreadable(Exception):
    """A configuration this script cannot read; the message is what is wrong, without the file it is in."""


def parse(arguments: list[str]) -> tuple[str, list[str]] | None:
    """The service and the files handed over with `--file`, or None where the arguments are not that shape."""
    if not arguments or arguments[0].startswith("-"):
        return None
    files: list[str] = []
    rest = arguments[1:]
    while rest:
        if rest[0] != "--file" or len(rest) < 2:
            return None
        files.append(rest[1])
        rest = rest[2:]
    return arguments[0].rstrip("/") or "/", files


def read_toml(text: str) -> dict[str, Any]:
    """TOML text as data; `tomllib` is imported here so that loading the script on Python 3.10 never fails."""
    try:
        import tomllib
    except ImportError:
        raise Unreadable("no tomllib: Python 3.11 or newer reads [tool.mutmut]") from None
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise Unreadable(f"is not valid TOML ({error})") from None


def opener(path: str) -> str | None:
    """The first character of a path that `fnmatch` reads as syntax, if it holds one."""
    return next((char for char in path if char in OPENERS), None)


def check_paths(values: Any, name: str) -> list[str]:
    """`source_paths` as a non-empty list of relative POSIX paths with no `..` and no pattern syntax, else Unreadable."""
    if not isinstance(values, list) or not values:
        raise Unreadable(f"{name} must be a non-empty list of paths, not {values!r}")
    for value in values:
        if (not isinstance(value, str) or not value or value.startswith("/") or ".." in value.split("/")
                or opener(value)):
            raise Unreadable(f"{name} holds {value!r}, which is not a relative path of literal segments under the service")
    return values


def check_patterns(values: Any, name: str) -> list[str]:
    if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
        raise Unreadable(f"{name} must be a list of strings, not {values!r}")
    return values


def targets(service: str | Path) -> dict[str, Any]:
    """The service's `[tool.mutmut]` table, with `source_paths` (or, only where it is empty, the deprecated
    `paths_to_mutate`), `only_mutate` and `do_not_mutate` checked and defaulted."""
    path = Path(service) / "pyproject.toml"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise Unreadable(f"cannot be read ({error.strerror or error})") from None
    table = read_toml(text).get("tool", {}).get("mutmut")
    if not isinstance(table, dict):
        raise Unreadable("no [tool.mutmut] table")
    config = dict(table)
    config["source_paths"] = check_paths(table.get("source_paths") or table.get("paths_to_mutate"), "source_paths")
    for name in ("only_mutate", "do_not_mutate"):
        config[name] = check_patterns(table.get(name, []), name)
    return config


def matched(config: dict[str, Any], file: str) -> bool:
    """Whether mutmut 3.8.0 would mutate this file (a path within the service): a `.py` under `source_paths` that
    `should_mutate` takes, `fnmatch` applied to the path exactly as its `configuration.py` applies it."""
    from fnmatch import fnmatch

    if not file.endswith(".py") or not any(file.startswith(root.rstrip("/") + "/") for root in config["source_paths"]):
        return False
    included = not config["only_mutate"] or any(fnmatch(file, pattern) for pattern in config["only_mutate"])
    return included and not any(fnmatch(file, pattern) for pattern in config["do_not_mutate"])


def refused(service: str, file: str) -> str | None:
    """The words refusing a path `mutmut run` would read as a pattern over mutant names, or None."""
    char = opener(file)
    if char is None:
        return None
    return (f"`{service}/{file}` holds `{char}`, which mutmut reads as a pattern over mutant names; rename it, or run "
            "`make mutation-full`")


def requirement_name(requirement: str) -> str:
    found = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)", requirement)
    return re.sub(r"[-_.]+", "-", found.group(1)).lower() if found else ""


def manifest_versions(text: str) -> dict[str, Any]:
    document = read_toml(text)
    groups = [*document.get("dependency-groups", {}).values(), document.get("project", {}).get("dependencies", []),
              *document.get("project", {}).get("optional-dependencies", {}).values()]
    return {"tool.mutmut": document.get("tool", {}).get("mutmut"),
            "requirement": [item for group in groups for item in group
                            if isinstance(item, str) and requirement_name(item) == ROOT_PACKAGE]}


def closure(packages: list[dict[str, Any]], root: str) -> set[str]:
    """`root` and every package it resolves to, by the lock's own `dependencies`, whichever marker selects them."""
    wanted: dict[str, list[str]] = {}
    for package in packages:
        wanted.setdefault(package["name"], []).extend(item["name"] for item in package.get("dependencies", []))
    found, todo = set(), [root]
    while todo:
        name = todo.pop()
        if name not in found:
            found.add(name)
            todo.extend(wanted.get(name, []))
    return found


def lock_versions(text: str) -> dict[str, list[str]]:
    packages = read_toml(text).get("package")
    if not isinstance(packages, list):
        raise Unreadable("is not a uv lock: it has no [[package]] entries")
    names = {ROOT_PACKAGE} | closure(packages, PARSER_PACKAGE)
    found: dict[str, list[str]] = {}
    for package in packages:
        if package["name"] in names:
            found.setdefault(package["name"], []).append(package["version"])
    return found


def versions(pyproject_text: str | None = None, lock_text: str | None = None) -> dict[str, Any]:
    """What a change to the manifest or the lock sweeps on (R6): from the manifest its `[tool.mutmut]` table and every
    mutmut requirement as written, from the lock the versions of mutmut and of the closure of libcst, by name."""
    found: dict[str, Any] = {}
    if pyproject_text is not None:
        found.update(manifest_versions(pyproject_text))
    if lock_text is not None:
        found.update(lock_versions(lock_text))
    return found


def main(arguments: list[str]) -> int:
    parsed = parse(arguments)
    if parsed is None:
        print(USAGE)
        return 2
    service, files = parsed
    for file in files:
        refusal = refused(service, file)
        if refusal:
            print(f"mutation: {refusal}")
            return 2
    try:
        targets(service)
    except Unreadable as error:
        print(f"mutation: {service}/pyproject.toml: {error}")
        return 2
    print(NOT_WIRED)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
