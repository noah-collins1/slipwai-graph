"""The record `verify-scoped.py record` prints: what the gate's checks are, what each reads, what the project's
deployables are, and which contracts join them. ADR 0004 fixes its shape (schema 1).

It is derived on every call and written nowhere: the checks and their per-deployable units from the make database
(`make -npq`, which prints the rules and runs nothing), the deployables from `project.json`, the inputs from the
table in `table.py`, the packages from the tree, the model from the working tree and the base. A record that cannot
be built is a `RecordError`, whose words are one line.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any, NamedTuple

sys.dont_write_bytecode = True

from . import reach, rules  # noqa: E402
from .table import CHECKS, GATE_UNITS, NO_INPUTS, UNITS, Row  # noqa: E402

SCHEMA = 1
LIMIT = 80
RULES_FILE = "scripts/verify_scoped/rules.json"
MODEL = "docs/event-model/model.yaml"
DATABASE = ("-npq", ".DEFAULT")
FULL_GATE_GOAL = "verify-checks"  # what `verify`'s recipe hands its sub-make, which is a level deeper
RULE = re.compile(r"^([^\s#:=%][^:=]*?)::?(?!=)\s*(.*)$")
ASSIGNED = re.compile(r"^([^\s#:=%][^\s:=]*) ([:?!+]*=) (.*)$")
TARGET_VARIABLE = re.compile(r"^([^\s#:=%][^:=]*?):\s+(\S+) (:?=|\+=) (.*)$")
DEFINE = re.compile(r"^define (\S+)$")
ORIGIN = re.compile(r"^# (makefile(?: private)? \(from |'override' directive|environment|command line|default|automatic|makefile$)")
PATTERNS_END = re.compile(r"^# (\d+|No) pattern-specific variable values")
MAKE_STATE = ("MAKEFLAGS", "MFLAGS", "MAKELEVEL", "MAKEOVERRIDES")
SERVICE_KINDS = ("service", "web")
ALWAYS_TOOLS = ("make", "python3")


class RecordError(Exception):
    """The record cannot be built: the words say why, on one line."""


class FullGate(RecordError):
    """The database of a Makefile whose text matched differs from what the factory fingerprinted: the words say what;
    `built` is the record."""

    def __init__(self, words: str, built: dict[str, Any]) -> None:
        super().__init__(words)
        self.built = built


class Reach(FullGate):
    """A deployable reads outside its own path (D148): the words are the whole reason the full gate runs."""


def printable(value: object, limit: int = LIMIT, quote: bool = True) -> str:
    """The one printer for a word that is not the script's own — a path, a name from `project.json`, a branch from the
    baseline, an error's text: a character that is a control or a line separator dropped (a lone surrogate, which a path
    that is not UTF-8 decodes to, is one), a backtick made an apostrophe where `quote`, and cut to `limit`; so it can
    forge no line and end no span early, and it can be written to any stream."""
    kept = []
    for char in str(value):
        if unicodedata.category(char)[0] == "C" or unicodedata.category(char) in ("Zl", "Zp"):
            kept.append("" if quote else " ")
        else:
            kept.append("'" if char == "`" and quote else char)
    return "".join(kept)[:limit]


class ObligationError(RecordError):
    """`verification.obligations` in `project.json` is not what it must be: the words are the one line that says so."""


class Database(NamedTuple):
    needs: dict[str, list[str]]  # target -> prerequisites, in the order the rules gave them
    recipes: dict[str, list[str]]
    variables: dict[str, str]
    order_only: dict[str, list[str]] = {}  # target -> what it waits for without being rebuilt by it (`a: | b`)
    origins: dict[str, str] = {}  # variable -> `file` where the Makefile assigns it, else the kind make prints
    flavours: dict[str, str] = {}  # variable -> `:=` (simple) or `=` (recursive)
    target_vars: dict[str, list[tuple[str, str, str]]] = {}  # target -> (name, flavour, value) of `target: NAME := value`
    patterns: dict[str, list[str]] = {}  # pattern -> the variables a Makefile sets for it (origin `file` or `override`)


def database(make: str, makefile: str, goal: str = ".DEFAULT", level: str | None = None,
             flags: tuple[str, ...] = (), words: tuple[str, ...] = ()) -> Database:
    """The rules and variables of `makefile`, read with `make -npq -f <makefile> .DEFAULT`: it exits 2 for the goal it
    has no rule for, and nothing is run. The make state of the caller's own run is left out of the call. A `goal` other
    than `.DEFAULT` is handed to the Makefile as `MAKECMDGOALS` on the command line and not as a goal, because a goal's
    recipe lines that call `$(MAKE)` are run even under `-n`; a `level` is `MAKELEVEL`, `flags` are options of the call, and
    `words` goals and variables handed to it as they are (the factory's tests read its text under a real run's goals)."""
    environment = {key: value for key, value in os.environ.items() if key not in MAKE_STATE}
    environment.update({} if level is None else {"MAKELEVEL": level})
    given = [*([] if goal == ".DEFAULT" else [f"MAKECMDGOALS={goal}"]), *words]
    try:
        done = subprocess.run([make, *flags, "-f", makefile, *DATABASE, *given], capture_output=True, text=True,
                              check=False, env=environment, timeout=60, encoding="utf-8", errors="replace")
    except (OSError, subprocess.SubprocessError) as error:
        raise RecordError(f"the make database cannot be read: {error}") from error
    found = Database({}, {}, {}, {}, {}, {}, {}, {})
    current: list[str] = []
    origin = ""
    body: list[str] | None = None  # the lines of a `define` being read
    last = ""  # the variable the previous line assigned: a line that follows it with no note is the rest of its value
    section = False  # inside the pattern-specific variable values
    pattern = ""
    private = False
    files = False  # past the variables: a line there is a rule's, never an assignment
    for line in done.stdout.splitlines():
        if body is not None:
            body.append(line) if line != "endef" else None
            if line == "endef":
                found.variables[last] = "\n".join(body)
                body = None
            continue
        if line.startswith("\t"):
            for target in current:
                found.recipes.setdefault(target, []).append(line[1:])
            last = ""
            continue
        if line.startswith("#"):  # the database's own notes: the one that heads each recipe, and each variable's origin
            last = ""
            files = files or line == "# Files"
            section = section or line == "# Pattern-specific Variable Values"
            section = section and PATTERNS_END.match(line) is None
            if ORIGIN.match(line):
                private = " private " in line
                origin = ("file" if line.startswith("# makefile") and "(from" in line else
                          "override" if line.startswith("# 'override'") else line[2:])
            elif section and origin in ("file", "override") and (held := ASSIGNED.match(line[2:])):
                found.patterns.setdefault(pattern, []).append(held.group(1))
            continue
        if section:
            pattern = line.removesuffix(" :") if line.endswith(" :") else pattern
            continue
        assigned = None if files else ASSIGNED.match(line)
        defined = None if files else DEFINE.match(line)
        if assigned or defined:
            name = assigned.group(1) if assigned else str(defined and defined.group(1))
            found.variables[name] = assigned.group(3) if assigned else ""
            found.flavours[name] = ":=" if assigned and assigned.group(2).startswith(":") else "="
            found.origins[name] = origin
            last, current = name, []
            body = [] if defined else None
            continue
        if last:  # the lines after a multi-line value that is not a `define`
            found.variables[last] += "\n" + line if line else ""
            continue
        targeted = TARGET_VARIABLE.match(line)
        if targeted:
            flavour = {":=": "simple", "=": "recursive", "+=": "append"}[targeted.group(3)]
            kind = "override " if origin == "override" else "private " if private else ""
            for target in targeted.group(1).split():
                found.target_vars.setdefault(target, []).append((targeted.group(2), kind + flavour, targeted.group(4)))
            current = []
            continue
        rule = RULE.match(line)
        current = rule.group(1).split() if rule else []
        normal, _, ordered = (rule.group(2) if rule else "").partition("|")
        for target in current:
            known = found.needs.setdefault(target, [])
            known.extend(word for word in normal.split() if word not in known)
            later = found.order_only.setdefault(target, [])
            later.extend(word for word in ordered.split() if word not in later and word not in known)
    return found


def family_of(deployable: dict[str, Any]) -> str:
    return str(deployable.get("language", "")).split("-")[0]


def deployables_of(root: Path) -> dict[str, dict[str, Any]]:
    """The deployables `project.json` lists, each as the record holds it."""
    try:
        document = json.loads((root / "project.json").read_text(encoding="utf-8"))
        listed = document["deployables"]
    except (OSError, ValueError, KeyError, TypeError, RecursionError) as error:
        raise RecordError(f"project.json lists no deployables that can be read ({type(error).__name__})") from error
    found: dict[str, dict[str, Any]] = {}
    for name, item in listed.items():
        if isinstance(item, dict) and item.get("kind") in SERVICE_KINDS and isinstance(item.get("path"), str):
            entry = {"kind": item["kind"], "path": item["path"], "family": family_of(item)}
            if item["kind"] == "web" and isinstance(item.get("api"), str):
                entry["api"] = item["api"]
            found[str(name)] = entry
    return found


def names(path: str, text: str) -> bool:
    return re.search(rf"(?<![\w/.-]){re.escape(path)}(?![\w-])", text) is not None


class Context:
    """What a row's templates expand over: the deployables, the exporting services, the npm packages."""

    def __init__(self, deployables: dict[str, dict[str, Any]], data: Database, packages: list[str]) -> None:
        self.deployables = deployables
        openapi = "\n".join(data.recipes.get("check-openapi", []))
        self.exporting = [name for name, item in deployables.items()
                          if item["kind"] == "service" and names(item["path"], openapi)]
        self.packages = packages

    def paths(self, token: str) -> list[tuple[str | None, str]]:
        """What `{token}` stands for, as (component, directory) pairs."""
        every = self.deployables
        chosen = {"dep": list(every), "web": [n for n, d in every.items() if d["kind"] == "web"],
                  "svc": self.exporting}[token] if token != "npm" else []
        found: list[tuple[str | None, str]] = [(name, every[name]["path"] + "/") for name in chosen]
        return found + [(None, f"packages/{package}/") for package in self.packages] if token == "npm" else found


def expand(row: Row, own: str | None, context: Context) -> tuple[list[str], list[str], list[str]]:
    """The row's files, tools and the deployables it concerns, with every template replaced."""
    files: set[str] = set()
    tools: set[str] = set(ALWAYS_TOOLS)
    components: list[str] = []
    here = context.deployables.get(own, {}) if own else {}
    for entry in row.files:
        if entry == "{own}":
            files.add(here["path"] + "/")
            components.append(str(own))
        elif entry.startswith("{") and entry.endswith("}"):
            for component, path in context.paths(entry[1:-1]):
                files.add(path)
                components.extend([component] if component else [])
        else:
            files.add(entry)
    for tool in row.tools:
        if tool == "{svc}":
            for name in context.exporting:
                tools.update(expand_tool(UNITS[context.deployables[name]["family"]], context.deployables[name]))
        else:
            tools.add(tool.replace("{own}", here.get("path", "") + "/") if "{own}" in tool else tool)
    return sorted(files), sorted(tools), sorted(dict.fromkeys(components))


def expand_tool(row: Row, deployable: dict[str, Any]) -> list[str]:
    return [tool.replace("{own}", deployable["path"] + "/") for tool in row.tools]


def check_entry(gate: str, row: Row | None, own: str | None, context: Context, targets: list[str]) -> dict[str, Any]:
    if row is None:
        return {"gate": gate, "components": [], "inputs": None, "claims": False, "always": NO_INPUTS,
                "targets": targets}
    files, tools, components = expand(row, own, context)
    return {"gate": gate, "components": components,
            "inputs": {"files": files, "tools": tools, "variables": sorted(row.variables)},
            "claims": row.claims, "always": row.always, "targets": targets}


def sum_of(gate: str, units: list[str], data: Database) -> tuple[list[list[str]], set[str]]:
    """What a gate's recipe and prerequisites are when they are the sum of its units: the lines of each target that
    holds some (the units, and the family targets they wait for, each once), and everything those wait for but the
    targets themselves."""
    parts: list[list[str]] = []
    needs: set[str] = set()
    taken: set[str] = set()
    for unit in units:
        for target in (*[need for need in data.needs.get(unit, []) if re.fullmatch(rf"{gate}_\w+", need)], unit):
            if target not in taken:
                taken.add(target)
                parts.append(data.recipes.get(target, []))
                needs.update(data.needs.get(target, []))
                needs.update(data.order_only.get(target, []))  # make builds these too
    return parts, needs - taken


def whole_gates(gates: dict[str, list[str]], data: Database) -> set[str]:
    """The gates whose recipe lines or prerequisites are not exactly what their units and family targets hold: a line a
    project added to `lint:`, a prerequisite it gave it, a line a unit runs that the gate no longer does. The gate has
    the same lines, each target's own in the order it has them; which target's come first is the gate's choice."""
    found = set()
    for gate, units in gates.items():
        parts, needs = sum_of(gate, units, data)
        lines = data.recipes.get(gate, [])
        places = [[lines.index(line) if line in lines else -1 for line in part] for part in parts]
        waits = {*data.needs.get(gate, []), *data.order_only.get(gate, [])}
        if sorted(line for part in parts for line in part) != sorted(lines) or waits != needs \
                or any(place != sorted(place) for place in places):
            found.add(gate)
    return found


def checks_of(data: Database, deployables: dict[str, dict[str, Any]], context: Context) -> dict[str, Any]:
    if "verify-checks" not in data.needs:
        raise RecordError("the make database has no `verify-checks`")
    checks: dict[str, Any] = {}
    for gate in data.needs["verify-checks"]:
        if gate not in GATE_UNITS:
            checks[gate] = check_entry(gate, CHECKS.get(gate), None, context, [gate])
            continue
        for name, item in deployables.items():
            unit = f"{gate}-{name}"
            if unit not in data.needs:
                raise RecordError(f"project.json lists the deployable `{name}`, and the make database has no `{unit}`")
            row = UNITS.get(item["family"])
            if row is None:
                raise RecordError(f"the deployable `{name}` is in a family this script does not know: {item['family']}")
            checks[unit] = check_entry(gate, row, name, context, [unit])
    units: dict[str, list[str]] = {}
    for unit, entry in checks.items():
        units.setdefault(entry["gate"], []).append(unit) if entry["gate"] in GATE_UNITS else None
    summed = whole_gates(units, data)
    for gate in summed:  # the gate runs whole, under its own name, wherever one of its units is chosen
        for unit in units[gate]:
            checks[unit].update(whole=True, targets=[gate])
    return checks


def asked_tools(data: Database) -> set[str] | None:
    """The tools the stamp asks of the machine, so the baseline holds their answers: a `--tool` each and an
    `--environment` for each interpreter, from the `VERIFY_STAMP` the project's `verify` recipe hands the stamp script.
    None where the gate names none."""
    words = data.variables.get("VERIFY_STAMP", "").split()
    if "VERIFY_STAMP" not in data.variables:
        return None
    return {words[i + 1] for i, word in enumerate(words[:-1]) if word == "--tool"} | {
        "interpreter " + words[i + 1] for i, word in enumerate(words[:-1]) if word == "--environment"}


def units_of(checks: dict[str, Any]) -> dict[str, list[str]]:
    """The units of each gate that has them, as the record's checks hold them."""
    units: dict[str, list[str]] = {}
    for unit, entry in checks.items():
        units.setdefault(entry["gate"], []).append(unit) if entry["gate"] in GATE_UNITS else None
    return units


def under_the_full_gate(make: str, makefile: str, data: Database) -> str | None:
    """Words saying what the Makefile reads differently under the goal and level `make verify` hands its sub-make
    (`verify-checks`, `MAKELEVEL` 1, the options it passes) than under the scoped run's own, or None where nothing does.
    A rule, a variable a Makefile gives or one set for a pattern that differs is a conditional on `MAKECMDGOALS`,
    `MAKELEVEL` or `MAKEFLAGS`, and the full gate sees what this read does not."""
    group = data.variables.get("VERIFY_GROUP", "").split()
    there = database(make, makefile, FULL_GATE_GOAL, "1", ("--no-print-directory", *group))
    mine, theirs = rules.from_database_parsed(data, []), rules.from_database_parsed(there, [])
    parts = ((mine.needs, theirs.needs, "`{}` rule"), (mine.order_only, theirs.order_only, "`{}` rule"),
             (mine.recipes, theirs.recipes, "`{}` rule"), (mine.target_vars, theirs.target_vars, "`{}` rule"),
             (mine.variables, theirs.variables, "variable `{}`"), (data.patterns, there.patterns, "variable `{}`"))
    for here, full, words in parts:
        for name in sorted(set(here) | set(full)):
            if here.get(name) != full.get(name) and (here.get(name) or full.get(name)):
                return (f"the Makefile's {words.format(name)} reads differently under the goal `{FULL_GATE_GOAL}` and "
                        "level 1 that `make verify` gives its sub-make")
    return None


def compared(root: Path, data: Database, checks: dict[str, Any]) -> str | None:
    """What the database has that the factory did not write (`rules.json`), as words, or None. The text of the `Makefile`
    has matched already, or this would not be asked (D140), so a difference is the full gate and is charged to no one
    check. A file that cannot be read is a `RecordError`."""
    try:
        held = rules.load(str(root / RULES_FILE))
        return rules.difference(held, data, [unit for each in units_of(checks).values() for unit in each],
                                rules.project_exports(data, str(root)))
    except rules.Unreadable as error:
        raise RecordError(str(error)) from error


def packages_of(root: Path, scope: Any, base: str | None) -> list[str]:
    """The npm packages: a directory under `packages/` with a `package.json`, in the tree or at the base."""
    found = {path.parent.name for path in (root / "packages").glob("*/package.json")}
    if base is not None:
        listed = scope.git("ls-tree", "-r", "--name-only", base, "--", "packages") or ""
        found.update(match.group(1) for match in re.finditer(r"^packages/([^/]+)/package\.json$", listed, re.M))
    return sorted(found)


def events_of(model: object) -> tuple[dict[str, str], dict[str, set[str]]]:
    """Which service produces each event and which services read it, from a parsed model."""
    produced: dict[str, str] = {}
    read: dict[str, set[str]] = {}
    items = model.get("slices") if isinstance(model, dict) else None
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict) or not isinstance(item.get("service"), str):
            continue
        for frame in item.get("frames") or []:
            if isinstance(frame, dict) and frame.get("type") == "evt" and frame.get("external") is not True \
                    and isinstance(frame.get("name"), str):
                produced.setdefault(frame["name"], item["service"])
        for event in item.get("reads") or []:
            read.setdefault(str(event), set()).add(item["service"])
    return produced, read


def models_of(root: Path, scope: Any, base: str | None) -> list[object]:
    """The model as the working tree has it and as the base has it, each parsed with `check-model`'s own loader."""
    texts = []
    try:
        texts.append((root / MODEL).read_text(encoding="utf-8"))
    except OSError:
        pass
    if base is not None:
        try:
            shown = scope.git_show(base, "./" + MODEL)
        except scope.CouldNotCompare as error:
            raise RecordError(f"the model at the base cannot be read: {error}") from error
        texts.append(shown) if shown is not None else None
    try:
        return [scope.load_model(text) for text in texts]
    except Exception as error:
        raise RecordError("the model cannot be read: " + str(error).replace("\n", " ")[:100]) from error


def named_by(models: list[object]) -> list[str] | None:
    """Every path a slice of the model names as evidence (`gwt`, `code`, a mockup's `at`), the working tree's and the
    base's, as `check-model` requires each to exist: a file as it is, a directory or a missing path with a `/` so a
    file under it is read too. None where a model was there and could not be read as a mapping."""
    found: set[str] = set()
    for model in models:
        if not isinstance(model, dict):
            return None
        items = model.get("slices")
        for item in items if isinstance(items, list) else []:
            if not isinstance(item, dict):
                continue
            for key in ("gwt", "code"):
                value = item.get(key)
                found.update(path for path in (value if isinstance(value, list) else [value]) if isinstance(path, str))
            for frame in item.get("frames") or []:
                for mockup in (frame.get("mockups") if isinstance(frame, dict) else None) or []:
                    at = mockup.get("at") if isinstance(mockup, dict) else None
                    found.update([at] if isinstance(at, str) and not at.startswith(("http://", "https://")) else [])
    return sorted(path.removeprefix("./") for path in found if path.removeprefix("./"))


def with_named(checks: dict[str, Any], root: Path, models: list[object]) -> None:
    """`check-model` reads what the model names, so each such path is one of its file inputs; where a model cannot be
    read as a mapping it is a check with no recorded inputs, which always runs."""
    entry = checks.get("check-model")
    if entry is None or entry["inputs"] is None:
        return
    named = named_by(models)
    if named is None:
        entry.update(inputs=None, claims=False, always=NO_INPUTS)
        return
    files = set(entry["inputs"]["files"])
    files.update(path if (root / path).is_file() else path.rstrip("/") + "/" for path in named)
    entry["inputs"]["files"] = sorted(files)


def contracts_of(deployables: dict[str, dict[str, Any]], context: Context, models: list[object]) -> list[dict[str, Any]]:
    contracts: list[dict[str, Any]] = []
    for name in deployables:
        item = deployables[name]
        consumers = [other for other, entry in deployables.items() if entry.get("api") == name]
        if item["kind"] == "service" and (consumers or name in context.exporting):
            contracts.append({"id": f"openapi:{name}", "kind": "openapi", "owner": name,
                              "paths": [item["path"] + "/"], "consumers": consumers})
    npm = [name for name, item in deployables.items() if item["family"] == "typescript"]
    contracts += [{"id": f"package:{package}", "kind": "package", "owner": None, "paths": [f"packages/{package}/"],
                   "consumers": npm} for package in context.packages]
    owners: dict[str, str] = {}
    readers: dict[str, set[str]] = {}
    for model in models:
        produced, read = events_of(model)
        owners.update({event: service for event, service in produced.items() if event not in owners})
        for event, services in read.items():
            readers.setdefault(event, set()).update(services)
    for event in sorted(owners):
        consumers = sorted(service for service in readers.get(event, set()) if service != owners[event]
                           and service in deployables)
        if consumers and owners[event] in deployables:
            contracts.append({"id": f"event:{event}", "kind": "event", "event": event, "owner": owners[event],
                              "paths": [deployables[owners[event]]["path"] + "/"], "consumers": consumers})
    return contracts


def declared(root: Path, scope: Any, base: str | None) -> object:
    """`verification` as `project.json` has it at the base, never the branch's own; the working tree's where there is no
    base to read (the record printed off a slice branch). None where there is no such key."""
    if base is not None:
        document: object = scope.project_document(base)
    else:
        try:
            document = json.loads((root / "project.json").read_text(encoding="utf-8"))
        except (OSError, ValueError, RecursionError):
            document = {}
    return document.get("verification") if isinstance(document, dict) else None


def shown(position: int, entry: object) -> str:
    name = entry.get("name") if isinstance(entry, dict) else None
    return f"obligation {position} ({'`' + printable(name) + '`' if isinstance(name, str) and name else 'unnamed'})"


def obligations_of(verification: object, deployables: dict[str, dict[str, Any]],
                   checks: dict[str, Any]) -> list[dict[str, Any]]:
    """The obligations `verification` declares, each as the record holds it (a gate name replaced by its units, the
    checks sorted); an `ObligationError` whose words are one line where it is not the shape data-model.md fixes."""
    where = "in project.json's verification.obligations"
    if verification is None:
        return []
    if not isinstance(verification, dict):
        raise ObligationError("verification in project.json is not an object")
    if "obligations" not in verification:
        return []
    if not isinstance(verification["obligations"], list):
        raise ObligationError("verification.obligations in project.json is not a list")
    found: list[dict[str, Any]] = []
    for position, entry in enumerate(verification["obligations"], 1):
        who = f"{shown(position, entry)} {where}"
        if not isinstance(entry, dict):
            raise ObligationError(f"{who} is not an object")
        name = entry.get("name")
        if not isinstance(name, str) or not name:
            raise ObligationError(f"{who} has no name")
        if any(item["name"] == name for item in found):
            first = next(index for index, item in enumerate(found, 1) if item["name"] == name)
            raise ObligationError(f"{who} repeats the name of obligation {first}")
        components = entry.get("components")
        if isinstance(components, list) and not all(isinstance(item, str) for item in components):
            raise ObligationError(f"{who} names a component that is not a name")
        distinct = list(dict.fromkeys(components)) if isinstance(components, list) else []
        if len(distinct) < 2:
            raise ObligationError(f"{who} names fewer than two distinct components")
        unknown = next((item for item in distinct if item not in deployables), None)
        if unknown is not None:
            raise ObligationError(f"{who} names the component `{printable(unknown)}`, which is not among the deployables")
        wanted = entry.get("checks")
        if not isinstance(wanted, list) or not wanted:
            raise ObligationError(f"{who} names no checks")
        units: set[str] = set()
        for check in wanted:
            if not isinstance(check, str):
                raise ObligationError(f"{who} names a check that is not a name")
            held = [unit for unit, item in checks.items() if item["gate"] == check] if check in GATE_UNITS \
                else [check] if check in checks else []
            if not held:
                raise ObligationError(f"{who} names the check `{printable(check)}`, which the record does not hold")
            units.update(held)
        found.append({"name": name, "components": distinct, "checks": sorted(units)})
    return found


def base_of(scope: Any) -> str | None:
    """The commit the branch is compared with; None where there is none to be had."""
    try:
        return scope.merge_base().commit  # type: ignore[no-any-return]
    except Exception:
        return None


def build(make: str, makefile: str, scope: Any, data: Database | None = None, base: str | None = None) -> dict[str, Any]:
    """The record, or a `RecordError` saying why there is none. Where the caller has read the database or found the
    base already, it hands them over."""
    root = Path(scope.ROOT)
    deployables = deployables_of(root)
    data = data or database(make, makefile)
    base = base or base_of(scope)
    context = Context(deployables, data, packages_of(root, scope, base))
    checks = checks_of(data, deployables, context)
    asked = asked_tools(data)
    for entry in checks.values():  # a tool the baseline never asks cannot be told to have changed
        if asked is not None and entry["inputs"]:
            entry["inputs"]["tools"] = [tool for tool in entry["inputs"]["tools"] if tool in asked]
    full = compared(root, data, checks) or under_the_full_gate(make, makefile, data)
    reached = None if full is not None else reach.find(root, deployables, context.packages, base)
    services = [name for name, item in deployables.items() if item["kind"] == "service"]
    models = models_of(root, scope, base) if len(services) > 1 or "check-model" in checks else []
    with_named(checks, root, models)
    obligations = obligations_of(declared(root, scope, base), deployables, checks)
    built = {"schema": SCHEMA, "deployables": deployables, "checks": checks,
             "contracts": contracts_of(deployables, context, models), "obligations": obligations}
    if full is not None:
        raise FullGate(full, built)
    if reached is not None:
        raise Reach(reached, built)
    return built


def render(record: dict[str, Any]) -> str:
    return json.dumps(record, indent=2, sort_keys=True) + "\n"

