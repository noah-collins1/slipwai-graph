"""What the factory wrote for every rule `make verify` reaches, in one canonical form, and the two ways to read it.

`scripts/verify_scoped/rules.json` (schema 1) holds a digest for each rule reachable from `verify` (through normal and
order-only prerequisites, the recipe `verify` hands its sub-make being `verify-checks`) and from the scoped units, and a
digest for each variable the factory's `Makefile` assigns. The factory writes it from the `Makefile` text it writes
(`from_text`); `verify-scoped.py` reads the make database of the project's own `Makefile` (`from_database`) and compares.
One digest is over `{"needs", "order_only", "recipe"}` with the recipe lines as make stores them, unexpanded, and
repeated rule lines for one target merged the way make merges them; a variable's is over its flavour and its value as
written. No path of any machine is stored.

The module is stdlib only, so the factory loads it and a generated project runs it. A construct `from_text` cannot read
is a `ValueError` at generate time, which fails the factory's tests: it never reaches a project.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from typing import Any, NamedTuple

sys.dont_write_bytecode = True

SCHEMA = 1
ROOTS = ("verify", "verify-checks")  # `verify`'s recipe runs `verify-checks` in a sub-make
SECTION = "# Scoped gate:"  # the comment that heads the section whose `.PHONY` line names the scoped units
ASSIGNMENT = re.compile(r"^(override\s+)?([A-Za-z_.][\w.]*)\s*(::=|:=|\?=|\+=|=)\s*(.*?)\s*$")
RULE_LINE = re.compile(r"^([^\s:=][^:=]*?)\s*:(?![:=])\s*(.*)$")
PHONY = re.compile(r"^\.PHONY:\s*(.*)$")
EXPORT = re.compile(r"^(un)?export\s+[\w.]+\s*$")
UNSET_BY_COMMAND = "ifeq ($(origin VERIFY_ORDER),command line)"  # false under `make -npq`, which gets no variable
REFERENCE = re.compile(r"\$[({]([A-Za-z_][\w.-]*)[)}]|\$([A-Za-z_])")


class Parsed(NamedTuple):
    """Rules and variables, as either reader finds them. `variables` holds (flavour, value)."""
    needs: dict[str, list[str]]
    order_only: dict[str, list[str]]
    recipes: dict[str, list[str]]
    variables: dict[str, tuple[str, str]]
    roots: list[str]


def merged(known: list[str], words: list[str], first: bool) -> None:
    """`words` added to what `known` has, each once: after it, or before it where the rule that gave them has a recipe."""
    fresh = list(dict.fromkeys(word for word in words if word not in known))
    known[:] = [*fresh, *known] if first else [*known, *fresh]


def from_text_parsed(text: str) -> Parsed:
    """The rules and variables of the `Makefile` text the factory writes, read as `make -npq` reads them."""
    needs: dict[str, list[str]] = {}
    order_only: dict[str, list[str]] = {}
    recipes: dict[str, list[str]] = {}
    variables: dict[str, tuple[str, str]] = {}
    lines: list[tuple[list[str], list[str], list[str], list[str]]] = []  # each rule line: targets, needs, order-only, recipe
    current: list[str] = []
    skipping = False
    sectioned = False
    for number, line in enumerate(text.splitlines(), 1):
        where = f"Makefile line {number}"
        if skipping:
            skipping = line != "endif"
            if line.startswith(("if", "else", "define")):
                raise ValueError(f"{where}: a conditional inside a conditional is a construct rules.py cannot read")
            continue
        if line.startswith("\t"):
            if not current:
                raise ValueError(f"{where}: a recipe line with no rule")
            lines[-1][3].append(line[1:])
            continue
        if not line.strip() or line.startswith("#"):
            sectioned = sectioned or line.startswith(SECTION)
            continue
        current = []
        if line == UNSET_BY_COMMAND:
            skipping = True
            continue
        if line.startswith(("if", "else", "endif", "define", "endef", "include", "-include", "sinclude", "vpath")) \
                or EXPORT.match(line):
            if EXPORT.match(line):
                continue
            raise ValueError(f"{where}: `{line.split()[0]}` is a construct rules.py cannot read")
        assigned = ASSIGNMENT.match(line)
        if assigned:
            assign(variables, assigned, where)
            continue
        body = line.split("#", 1)[0].rstrip()  # what follows a `#` is the help text, or a comment
        found = RULE_LINE.match(body)
        if found is None or "=" in body or ";" in body:
            raise ValueError(f"{where}: rules.py cannot read this line: {line[:60]}")
        if PHONY.match(line):
            continue
        normal, _, ordered = found.group(2).partition("|")
        current = found.group(1).split()
        lines.append((current, normal.split(), ordered.split(), []))
    for targets, normal, ordered, recipe in lines:
        for target in targets:
            known = needs.setdefault(target, [])
            later = order_only.setdefault(target, [])
            recipes.setdefault(target, []).extend(recipe)
            # a rule that has a recipe, even an empty one, puts its prerequisites first, so `$<` is its first
            merged(known, normal, recipe != [])
            merged(later, [word for word in ordered if word not in known], recipe != [])
    for target in list(order_only):
        order_only[target] = [word for word in order_only[target] if word not in needs[target]]
    return Parsed(needs, order_only, recipes, variables, phony_after_section(text))


def phony_after_section(text: str) -> list[str]:
    """The names the `.PHONY` line right after the scoped section's header holds: its units and family targets."""
    head = text.find(SECTION)
    if head < 0:
        return []
    found = re.search(r"^\.PHONY:\s*([^\n]*)$", text[head:], re.M)
    return found.group(1).split() if found else []


def assign(variables: dict[str, tuple[str, str]], found: re.Match[str], where: str) -> None:
    """One assignment, as make keeps it. An `override` is the machine's (it may call a function of this make), and
    a name that begins with a dot is make's own, so neither is held."""
    override, name, operator, value = found.groups()
    if override or name.startswith("."):
        return
    if "#" in value:
        raise ValueError(f"{where}: a comment on the line of `{name}` is a construct rules.py cannot read")
    if operator in ("::=", ":=") and "$" in value:
        raise ValueError(f"{where}: `{name}` is simply expanded from a reference, which rules.py cannot read")
    if operator == "?=" and name in variables:
        return
    if operator == "+=" and name in variables:
        flavour, held = variables[name]
        variables[name] = (flavour, f"{held} {value}" if held and value else held or value)
        return
    variables[name] = ("simple" if operator in ("::=", ":=") else "recursive", value)


MAKE_OWN = ("MAKEFILE_LIST",)  # assigned by make for the file it reads


def from_database_parsed(data: Any, units: list[str]) -> Parsed:
    """The rules and variables of `record.database`'s output: the variables the project's own `Makefile` assigns."""
    own = {name: ("simple" if data.flavours.get(name) == ":=" else "recursive", value)
           for name, value in data.variables.items() if data.origins.get(name) == "file" and not name.startswith(".") and name not in MAKE_OWN}
    return Parsed(data.needs, data.order_only, data.recipes, own, units)


def digest(document: object) -> str:
    text = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(text.encode("ascii")).hexdigest()


def reach(parsed: Parsed, starts: list[str]) -> list[str]:
    """Every target `starts` waits for, themselves included, by normal and order-only prerequisites; first reached first."""
    seen: dict[str, None] = {}
    pending = list(starts)
    while pending:
        target = pending.pop(0)
        if target not in seen:
            seen[target] = None
            pending += [*parsed.needs.get(target, []), *parsed.order_only.get(target, [])]
    return list(seen)


def ruled(parsed: Parsed, target: str) -> bool:
    """Whether the target has a rule that says anything: a prerequisite or a recipe line."""
    return bool(parsed.needs.get(target) or parsed.order_only.get(target) or parsed.recipes.get(target))


def rule_digest(parsed: Parsed, target: str) -> str:
    return digest({"needs": parsed.needs.get(target, []), "order_only": parsed.order_only.get(target, []),
                   "recipe": parsed.recipes.get(target, [])})


def variable_digest(variable: tuple[str, str]) -> str:
    return digest({"flavour": variable[0], "value": variable[1]})


def fingerprint(parsed: Parsed) -> dict[str, Any]:
    """The file's content: a digest for each rule reachable from `verify` and from the units, and for each variable."""
    rules = {target: rule_digest(parsed, target) for target in reach(parsed, [*ROOTS, *parsed.roots])
             if ruled(parsed, target)}
    return {"schema": SCHEMA, "rules": rules,
            "variables": {name: variable_digest(held) for name, held in parsed.variables.items()}}


def from_text(text: str) -> dict[str, Any]:
    """What the factory writes into `rules.json` for the `Makefile` text it writes."""
    return fingerprint(from_text_parsed(text))


def from_database(data: Any, units: list[str]) -> dict[str, Any]:
    """The same form read from the make database of a project's own `Makefile`; `units` are the scoped units."""
    return fingerprint(from_database_parsed(data, units))
