"""What the method-file checks read that a table row cannot name: a manifest's paths, a preset's files and what an
installed integration's `registry.json` row gives. Derived at record time and added to the checks' file inputs,
as `record.with_named` does for `check-model`.

A source that cannot be read, that does not parse, or that names a path outside the project (absolute, `~`, a `..`
segment, a backslash, empty) leaves the check with no recorded inputs: it runs on every scoped run (D172 limit i). A
source that is simply absent adds nothing. Both the working tree and the base are read, so a path the branch removed
from a manifest is still an input for the change that removed it.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

sys.dont_write_bytecode = True

from .table import NO_INPUTS  # noqa: E402

# Copied from `check-speckit.py`'s `PRESET_FILE_ENTRY`: the `file:` values a `preset.yml` declares; a test holds both equal.
PRESET_FILE_ENTRY = re.compile(r"""^\s*(?:-\s+)?file:\s*["']?([^"'\s#]+)["']?\s*(?:#.*)?$""", re.MULTILINE)
INTEGRATIONS = ".specify/integrations"
PRESETS = ".specify/presets"
REGISTERED = PRESETS + "/.registry"
STATE = ".specify/integration.json"
REGISTRY = Path(__file__).resolve().parent.parent / "agents" / "registry.json"
MANIFEST = re.compile(r"^\.specify/integrations/[^/]+\.manifest\.json$")
PRESET = re.compile(r"^\.specify/presets/([^/]+)/preset\.yml$")


class Unreadable(Exception):
    """A source of derived inputs cannot be trusted: the check keeps no recorded inputs."""


def inside(path: object) -> bool:
    """A path the project holds: a non-empty string that is neither absolute nor `~`-relative, climbs nowhere and
    holds no backslash, so joined to any directory of the project it stays under the project."""
    if not isinstance(path, str) or not path or "\\" in path or "\0" in path or path.startswith("~"):
        return False
    posix = PurePosixPath(path)
    return not posix.is_absolute() and ".." not in posix.parts


def read(path: Path) -> str | None:
    """A file's text, None where it is absent, `Unreadable` where it exists and cannot be read."""
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except (OSError, UnicodeError) as error:
        raise Unreadable(str(error)) from error


def at_base(scope: Any, base: str | None, path: str) -> str | None:
    if base is None:
        return None
    try:
        return scope.git_show(base, "./" + path)  # type: ignore[no-any-return]
    except scope.CouldNotCompare as error:
        raise Unreadable(str(error)) from error


def texts(root: Path, scope: Any, base: str | None, directory: str, wanted: re.Pattern[str]) -> list[tuple[str, str]]:
    """Every file of `directory` the pattern names, as `(path, text)`, in the working tree and at the base."""
    found: dict[str, list[str]] = {}
    here = root / directory
    for path in sorted(here.glob("**/*") if here.is_dir() else []):
        relative = path.relative_to(root).as_posix()
        if wanted.match(relative):
            found.setdefault(relative, []).append(read(path) or "")
    if base is not None:
        listed = scope.git("ls-tree", "-r", "--name-only", base, "--", directory)
        if listed is None:
            raise Unreadable("the base's listing of " + directory + " cannot be read")
        for relative in listed.splitlines():
            if wanted.match(relative):
                shown = at_base(scope, base, relative)
                found.setdefault(relative, []).extend([shown] if shown is not None else [])
    return [(path, text) for path, each in sorted(found.items()) for text in each]


def parsed(text: str) -> dict[str, Any]:
    try:
        value = json.loads(text)
    except (ValueError, RecursionError) as error:
        raise Unreadable(str(error)) from error
    if not isinstance(value, dict):
        raise Unreadable("not an object")
    return value


def manifest_files(root: Path, scope: Any, base: str | None) -> set[str]:
    """Every `files` key of every integration manifest, which `check-speckit` opens."""
    found: set[str] = set()
    for _, text in texts(root, scope, base, INTEGRATIONS, MANIFEST):
        files = parsed(text).get("files")
        if not isinstance(files, dict) or not all(inside(key) for key in files):
            raise Unreadable("a manifest has no `files` map of project paths")
        found.update(PurePosixPath(key).as_posix() + ("/" if key.endswith("/") else "") for key in files)
    for path, text in texts(root, scope, base, PRESETS, PRESET):
        if not all(inside(declared) for declared in PRESET_FILE_ENTRY.findall(text)):
            raise Unreadable(f"{path} declares a file outside the project")
    for text in (read(root / REGISTERED), at_base(scope, base, REGISTERED)):
        if not all(inside(name) for name in registered(text)):
            raise Unreadable(f"{REGISTERED} names a preset outside {PRESETS}/")
    return found


def registered(text: str | None) -> list[object]:
    """The preset names `.registry` lists: `check-speckit` reads `<name>/preset.yml` under the presets for each. One it
    cannot parse lists none here: the file is a declared input, and `check-speckit` itself fails on it."""
    try:
        presets = json.loads(text).get("presets") if text is not None else None
    except (ValueError, RecursionError, AttributeError):
        return []
    return list(presets) if isinstance(presets, dict) else []


def installed(root: Path, scope: Any, base: str | None) -> set[str]:
    """The integrations `.specify/integration.json` selects in the working tree and at the base, as
    `agents/project.py`'s `selected_integrations` reads it."""
    sources = [read(root / STATE), at_base(scope, base, STATE)]
    chosen: set[str] = set()
    for text in (source for source in sources if source is not None):
        state = parsed(text)
        listed = state.get("installed_integrations")
        default = state.get("default_integration")
        if isinstance(listed, list) and any(isinstance(value, str) for value in listed):
            chosen.update(value for value in listed if isinstance(value, str))
        elif isinstance(default, str):
            chosen.add(default)
        else:
            raise Unreadable(STATE + " names no integration")
    return chosen


def rows(registry: Path) -> dict[str, dict[str, Any]]:
    try:
        harnesses = json.loads(registry.read_text(encoding="utf-8")).get("harnesses")
    except (OSError, UnicodeError, ValueError, RecursionError, AttributeError) as error:
        raise Unreadable(str(error)) from error
    if not isinstance(harnesses, list):
        raise Unreadable("the registry has no harnesses")
    return {row["key"]: row for row in harnesses if isinstance(row, dict) and isinstance(row.get("key"), str)}


def integration_files(root: Path, scope: Any, base: str | None, registry: Path) -> set[str]:
    """What each installed integration's registry row says the check reads: directories (ending in `/`) and files."""
    chosen = installed(root, scope, base)
    if not chosen:
        return set()
    table = rows(registry)
    found: set[str] = set()
    for key in sorted(chosen):
        row = table.get(key)
        if row is None:  # a key the registry does not know: `integration.json` itself is the input that fails
            continue
        agent = row.get("agentFile")
        hooks = row.get("hooks")
        projection = hooks.get("projection") if isinstance(hooks, dict) else None
        directories = [row.get("skillsDir"), row.get("commandsDir"), agent.get("dir") if isinstance(agent, dict) else None]
        files = [row.get("contextFile"), projection.get("where") if isinstance(projection, dict) else None]
        for value in (*directories, *files):
            if value is not None and not inside(value):
                raise Unreadable(f"the registry row of {key} names {value}")
        found.update(value.strip("/") + "/" for value in directories if value)
        found.update(value for value in files if value)
    return found


HOLLOW = "an ignored projection directory with no files, whose existence the baseline cannot see"


def bare(path: Path) -> bool:
    """A directory with nothing under it, at any depth: no file and no link, which is all the baseline's digest sees."""
    return not any(not found.is_dir() or found.is_symlink() for found in path.rglob("*"))


def hollow(root: Path, scope: Any, base: str | None, registry: Path = REGISTRY) -> list[str]:
    """The projection directories `check-agents` (an installed integration's) and `check-speckit` (every in-repo one the
    registry names) judge by whether they exist, that exist with no file under them: `unprojected` turns on it, and
    git ignores them, so the baseline's digest of files cannot see one appear."""
    try:
        table = rows(registry)
        chosen = installed(root, scope, base)
    except Unreadable:  # `add` leaves the check with no recorded inputs, which is the full gate
        return []
    found: set[str] = set()
    for key, row in table.items():
        agent = row.get("agentFile")
        listed = [row.get("skillsDir"), row.get("commandsDir")]
        if key in chosen and isinstance(agent, dict):
            listed.append(agent.get("dir"))
        found.update(value.strip("/") + "/" for value in listed if isinstance(value, str) and inside(value))
    return sorted(directory for directory in found if (root / directory).is_dir() and bare(root / directory))


def add(entry: dict[str, Any] | None, derive: Any) -> None:
    if entry is None or entry["inputs"] is None:
        return
    try:
        more = derive()
    except Unreadable:
        entry.update(inputs=None, claims=False, always=NO_INPUTS)
        return
    entry["inputs"]["files"] = sorted(set(entry["inputs"]["files"]) | more)


def with_derived(checks: dict[str, Any], root: Path, scope: Any, base: str | None, registry: Path = REGISTRY) -> None:
    """Add what manifests and presets name to `check-speckit`, and what the installed integrations' registry rows
    name to `check-agents`."""
    add(checks.get("check-speckit"), lambda: manifest_files(root, scope, base))
    add(checks.get("check-agents"), lambda: integration_files(root, scope, base, registry))
