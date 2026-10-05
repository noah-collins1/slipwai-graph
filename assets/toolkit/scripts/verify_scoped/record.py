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
from pathlib import Path
from typing import Any, NamedTuple

sys.dont_write_bytecode = True

from .table import CHECKS, GATE_UNITS, NO_INPUTS, UNITS, Row  # noqa: E402

SCHEMA = 1
MODEL = "docs/event-model/model.yaml"
DATABASE = ("-npq", ".DEFAULT")
RULE = re.compile(r"^([^\s#:=%][^:=]*?)::?(?!=)\s*(.*)$")
ASSIGNED = re.compile(r"^(\w+) :?= (.*)$")
MAKE_STATE = ("MAKEFLAGS", "MFLAGS", "MAKELEVEL", "MAKEOVERRIDES")
SERVICE_KINDS = ("service", "web")
ALWAYS_TOOLS = ("make", "python3")


class RecordError(Exception):
    """The record cannot be built: the words say why, on one line."""


class Database(NamedTuple):
    needs: dict[str, list[str]]  # target -> prerequisites, in the order the rules gave them
    recipes: dict[str, list[str]]
    variables: dict[str, str]


def database(make: str, makefile: str) -> Database:
    """The rules and variables of `makefile`, read with `make -npq -f <makefile> .DEFAULT`: it exits 2 for the goal it
    has no rule for, and nothing is run. The make state of the caller's own run is left out of the call."""
    environment = {key: value for key, value in os.environ.items() if key not in MAKE_STATE}
    try:
        done = subprocess.run([make, "-f", makefile, *DATABASE], capture_output=True, text=True, check=False,
                              env=environment, timeout=60, encoding="utf-8", errors="replace")
    except (OSError, subprocess.SubprocessError) as error:
        raise RecordError(f"the make database cannot be read: {error}") from error
    needs: dict[str, list[str]] = {}
    recipes: dict[str, list[str]] = {}
    variables: dict[str, str] = {}
    current: list[str] = []
    for line in done.stdout.splitlines():
        if line.startswith("\t"):
            for target in current:
                recipes.setdefault(target, []).append(line[1:])
            continue
        if line.startswith("#"):  # the database's own notes, among them the one that heads each recipe
            continue
        assigned = ASSIGNED.match(line)
        if assigned:
            variables[assigned.group(1)] = assigned.group(2)
            current = []
            continue
        rule = RULE.match(line)
        current = rule.group(1).split() if rule else []
        for target in current:
            known = needs.setdefault(target, [])
            known.extend(word for word in (rule.group(2).split("|")[0].split() if rule else []) if word not in known)
    return Database(needs, recipes, variables)


def family_of(deployable: dict[str, Any]) -> str:
    return str(deployable.get("language", "")).split("-")[0]


def deployables_of(root: Path) -> dict[str, dict[str, Any]]:
    """The deployables `project.json` lists, each as the record holds it."""
    try:
        document = json.loads((root / "project.json").read_text(encoding="utf-8"))
        listed = document["deployables"]
    except (OSError, ValueError, KeyError, TypeError) as error:
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
    return checks


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
    services = [name for name, item in deployables.items() if item["kind"] == "service"]
    models = models_of(root, scope, base) if len(services) > 1 else []
    return {"schema": SCHEMA, "deployables": deployables, "checks": checks,
            "contracts": contracts_of(deployables, context, models), "obligations": []}


def render(record: dict[str, Any]) -> str:
    return json.dumps(record, indent=2, sort_keys=True) + "\n"

