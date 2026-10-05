"""What the factory wrote for every rule `make verify` reaches, in one canonical form, and the two ways to read it.

`scripts/verify_scoped/rules.json` (schema 1) holds a digest for each rule reachable from `verify` (through normal and
order-only prerequisites, the recipe `verify` hands its sub-make being `verify-checks`) and from the scoped units, and a
digest for each variable the factory's `Makefile` assigns. The factory writes it from the `Makefile` text it writes
(`from_text`); `verify-scoped.py` reads the make database of the project's own `Makefile` (`from_database`) and compares.
One digest is over `{"needs", "order_only", "recipe", "vars"}` with the recipe lines as make stores them, unexpanded,
repeated rule lines for one target merged the way make merges them, and the rule's target-specific variables; a
variable's is over its flavour (`override` and `private` kept) and its value as written. Every variable of origin `file`
or `override` is held, dot-names and make's specials included (D133). `exports` is one digest over the lines of every
makefile that export, unexport, name `.EXPORT_ALL_VARIABLES` or call `$(eval`. No path of any machine is stored.

The module is stdlib only, so the factory loads it and a generated project runs it. A construct `from_text` cannot read
is a `ValueError` at generate time, which fails the factory's tests: it never reaches a project.
"""
from __future__ import annotations

import hashlib
import json
import os
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
TARGET_VAR = re.compile(r"^([^\s:=#][^:=]*?)\s*:\s+(?:(override|private)\s+)?([A-Za-z_.][\w.]*)\s*(::=|:=|=|\+=)\s*(.*?)\s*$")
EVAL = re.compile(r"\$[({]\s*eval\b")
COMPARED = ("file", "override")  # the origins of a variable a Makefile gives; the rest are the baseline's (D116) or make's own
OUTPUT_SYNC = "$(if $(filter output-sync,$(.FEATURES)),--output-sync=target)"
# the only reference-bearing simple assignment the factory writes (`gate.py`), by its written text: what it expands to
WRITTEN = {OUTPUT_SYNC: lambda features: "--output-sync=target" if "output-sync" in features else ""}
UNSET_BY_COMMAND = "ifeq ($(origin VERIFY_ORDER),command line)"  # false under `make -npq`, which gets no variable
REFERENCES = re.compile(r"\$(\$|[({]\s*([A-Za-z_][\w.-]*))")  # group 2 is the name; `$$` is a dollar sign


class Parsed(NamedTuple):
    """Rules and variables, as either reader finds them. `variables` holds (flavour, value)."""
    needs: dict[str, list[str]]
    order_only: dict[str, list[str]]
    recipes: dict[str, list[str]]
    variables: dict[str, tuple[str, str]]
    roots: list[str]
    target_vars: dict[str, list[tuple[str, str, str]]] = {}  # target -> (name, flavour, value) it sets for itself


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
    target_vars: dict[str, list[tuple[str, str, str]]] = {}
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
                variables.setdefault(line.split()[1], ("simple", ""))  # make defines what is exported and not yet set
                continue
            raise ValueError(f"{where}: `{line.split()[0]}` is a construct rules.py cannot read")
        assigned = ASSIGNMENT.match(line)
        if assigned:
            assign(variables, assigned, where)
            continue
        targeted = TARGET_VAR.match(line)
        if targeted:
            set_for_target(target_vars, targeted, where)
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
    return Parsed(needs, order_only, recipes, variables, phony_after_section(text), target_vars)


def phony_after_section(text: str) -> list[str]:
    """The names the `.PHONY` line right after the scoped section's header holds: its units and family targets."""
    head = text.find(SECTION)
    if head < 0:
        return []
    found = re.search(r"^\.PHONY:\s*([^\n]*)$", text[head:], re.M)
    return found.group(1).split() if found else []


def assign(variables: dict[str, tuple[str, str]], found: re.Match[str], where: str) -> None:
    """One assignment, as make keeps it. An `override` is held with its own flavour, so `override SHELL := /bin/bash` is
    not the `SHELL := /bin/bash` the factory writes; its value may call a function only where `WRITTEN` knows the text."""
    override, name, operator, value = found.groups()
    if "#" in value:
        raise ValueError(f"{where}: a comment on the line of `{name}` is a construct rules.py cannot read")
    prefix = "override " if override else ""
    if operator in ("::=", ":=") and "$" in value and not (override and value in WRITTEN):
        raise ValueError(f"{where}: `{name}` is simply expanded from a reference, which rules.py cannot read")
    if operator == "?=" and name in variables:
        return
    if operator == "+=" and name in variables:
        flavour, held = variables[name]
        variables[name] = (flavour if flavour.startswith(prefix) else prefix + flavour,
                           f"{held} {value}" if held and value else held or value)
        return
    variables[name] = (prefix + ("simple" if operator in ("::=", ":=") else "recursive"), value)


def set_for_target(target_vars: dict[str, list[tuple[str, str, str]]], found: re.Match[str], where: str) -> None:
    """`target: NAME := value`, which make keeps as the rule's own (and `%` makes a pattern-specific one: not written)."""
    targets, modifier, name, operator, value = found.groups()
    if "%" in targets or "#" in value or "$" in value:
        raise ValueError(f"{where}: a pattern-specific variable, or one with a reference, is not a construct rules.py reads")
    flavour = {"::=": "simple", ":=": "simple", "=": "recursive", "+=": "append"}[operator]
    for target in targets.split():
        target_vars.setdefault(target, []).append((name, f"{modifier} {flavour}" if modifier else flavour, value))


MAKE_OWN = ("MAKEFILE_LIST",)  # assigned by make for the file it reads
EMPTY_OWN = ("GNUMAKEFLAGS",)  # make's own `override` variable, empty until a person gives it a value


def own_flags(value: str) -> bool:
    """Whether a `MAKEFLAGS` is the one the database call itself gives make: its letters, the options handed to it and
    the command-line variables after `--`. make prints its own flags under the same note as `CURDIR`."""
    words = value.split(" -- ")[0].split()
    kept = [word for word in words if word != "--no-print-directory" and not word.startswith(("--output-sync=", "-O"))]
    return re.fullmatch(r"-*[npq]*", " ".join(kept).replace(" ", "")) is not None


def compared_variables(data: Any) -> dict[str, tuple[str, str]]:
    """Every variable the project's `Makefile` gives (origin `file` or `override`, `define` blocks included), as it is held."""
    features = data.variables.get(".FEATURES", "").split()
    own: dict[str, tuple[str, str]] = {}
    for name, value in data.variables.items():
        origin = data.origins.get(name)
        if name in MAKE_OWN or (name in EMPTY_OWN and not value):
            continue
        if name == "MAKEFLAGS" and origin == "makefile" and not own_flags(value):
            origin = "file"  # a bare `# makefile` is `CURDIR`, and make's own flags; a flag the Makefile adds shows in the value
        if origin not in COMPARED:
            continue
        simple = data.flavours.get(name) == ":="
        if origin == "override" and simple:
            value = next((text for text, answer in WRITTEN.items() if value == answer(features)), value)
        own[name] = (("override " if origin == "override" else "") + ("simple" if simple else "recursive"), value)
    return own


def from_database_parsed(data: Any, units: list[str]) -> Parsed:
    """The rules and variables of `record.database`'s output: the variables the project's own `Makefile` gives."""
    return Parsed(data.needs, data.order_only, data.recipes, compared_variables(data), units, data.target_vars)


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
    """Whether the target has a rule that says anything: a prerequisite, a recipe line or a variable of its own."""
    return bool(parsed.needs.get(target) or parsed.order_only.get(target) or parsed.recipes.get(target)
                or parsed.target_vars.get(target))


def rule_digest(parsed: Parsed, target: str) -> str:
    return digest({"needs": parsed.needs.get(target, []), "order_only": parsed.order_only.get(target, []),
                   "recipe": parsed.recipes.get(target, []), "vars": sorted(parsed.target_vars.get(target, []))})


def variable_digest(variable: tuple[str, str]) -> str:
    return digest({"flavour": variable[0], "value": variable[1]})


def export_lines(text: str) -> list[str]:
    """The lines of one makefile that can change what reaches a recipe through the environment, or write a line nobody
    can read here: `export` and `unexport` (an `override` before them too), `.EXPORT_ALL_VARIABLES`, `$(eval`. Recipes
    and comments are left out, a backslash continuation is joined and whitespace collapsed, and a line inside an
    `ifdef` counts whether or not make takes the branch, so the rule fails closed."""
    joined = re.sub(r"\\\n[ \t]*", " ", text)
    found = []
    for line in joined.splitlines():
        if line.startswith("\t") or not line.strip() or line.lstrip().startswith("#"):
            continue
        words = line.split()
        first = words[1] if words[0] == "override" and len(words) > 1 else words[0]
        if first in ("export", "unexport") or ".EXPORT_ALL_VARIABLES" in line or EVAL.search(line):
            found.append(" ".join(words))
    return sorted(found)


def exported_names(lines: list[str]) -> set[str]:
    """The variables the `export` lines in `lines` name: the words after `export` up to an assignment."""
    names: set[str] = set()
    for line in lines:
        words = [word for word in line.split() if word != "override"]
        if words[0] != "export":
            continue
        for word in words[1:]:
            if word in (":=", "::=", "=", "?=", "+=", "!="):
                break
            names.add(re.split(r"[:?+!]?=", word)[0])
            if "=" in word:
                break
    return names


def project_exports(data: Any, root: str) -> list[str] | None:
    """`export_lines` of every file in the database's `MAKEFILE_LIST`, read from the project root; None where one cannot be."""
    lines: list[str] = []
    for name in dict.fromkeys(data.variables.get("MAKEFILE_LIST", "").split()):
        try:
            with open(os.path.join(root, name), encoding="utf-8") as handle:
                lines += export_lines(handle.read())
        except (OSError, ValueError):
            return None
    return sorted(lines)


def fingerprint(parsed: Parsed) -> dict[str, Any]:
    """The file's content: a digest for each rule reachable from `verify` and from the units, and for each variable."""
    rules = {target: rule_digest(parsed, target) for target in reach(parsed, [*ROOTS, *parsed.roots])
             if ruled(parsed, target)}
    return {"schema": SCHEMA, "rules": rules,
            "variables": {name: variable_digest(held) for name, held in parsed.variables.items()}}


def from_text(text: str) -> dict[str, Any]:
    """What the factory writes into `rules.json` for the `Makefile` text it writes."""
    return {**fingerprint(from_text_parsed(text)), "exports": digest(export_lines(text))}


def from_database(data: Any, units: list[str], root: str = ".") -> dict[str, Any]:
    """The same form read from the make database of a project's own `Makefile`; `units` are the scoped units, and `root`
    where the files of `MAKEFILE_LIST` are (a path make printed absolute is read as it is), for `exports`, which is left
    out where a file cannot be read."""
    found = fingerprint(from_database_parsed(data, units))
    lines = project_exports(data, root)
    return found if lines is None else {**found, "exports": digest(lines)}


class Unreadable(ValueError):
    """`rules.json` is missing, is not JSON, or is a schema this script does not know: what the factory wrote is not known."""


class Judgement(NamedTuple):
    """What the comparison charges: the first cause that makes the run the full gate (its words, whole), the named checks that always run, and the gates with units that run whole."""
    full: str | None
    checks: frozenset[str]
    gates: frozenset[str]


def load(path: str) -> dict[str, Any]:
    """The file's content; `Unreadable` where it is not a schema-1 file. Fields it does not know are ignored."""
    try:
        with open(path, encoding="utf-8") as handle:
            found = json.load(handle)
    except (OSError, ValueError) as error:
        raise Unreadable(f"{path} cannot be read ({type(error).__name__})") from error
    if not (isinstance(found, dict) and found.get("schema") == SCHEMA and isinstance(found.get("rules"), dict)
            and isinstance(found.get("variables"), dict) and isinstance(found.get("exports"), str)):
        raise Unreadable(f"{path} is not a schema {SCHEMA} rules file")
    return found


def used(parsed: Parsed, target: str, variables: dict[str, str]) -> set[str]:
    """The variables a target's recipe lines name, directly and through the values of the variables they name."""
    names = {name for line in parsed.recipes.get(target, []) for found in REFERENCES.finditer(line)
             if (name := found.group(2)) is not None}
    pending = list(names)
    while pending:
        for found in REFERENCES.finditer(variables.get(pending.pop(), "")):
            if found.group(2) is not None and found.group(2) not in names:
                names.add(found.group(2))
                pending.append(found.group(2))
    return names


UNWRITTEN = ("the Makefile sets variable `{name}`{where}, which the factory did not write and make can hand to any check; "
             "set it on the rule that uses it (`<rule>: {name} := …`) to scope again")
READ_BY_ALL = ("SHELL", ".SHELLFLAGS")  # every recipe is run by them


def changed_variables(held: dict[str, Any], found: dict[str, Any], data: Any) -> list[str]:
    """The variables the factory fingerprinted that the project's `Makefile` gives a value that differs, or no longer gives.
    A variable the environment or the command line gives is the baseline's (D116), not compared here."""
    changed = [name for name, held_digest in found["variables"].items()
               if name in held["variables"] and held["variables"][name] != held_digest]
    changed += [name for name in held["variables"] if name not in found["variables"] and name not in data.origins]
    return sorted(changed)


def judge(held: dict[str, Any], data: Any, units: list[str], members: list[str], gates: dict[str, list[str]],
          exports: list[str] | None = None) -> Judgement:
    """Every difference between the factory's text and the project's, each charged to the one member of `verify-checks`
    that reaches it: a named check, or a gate with units; one that no member or two or more reach, and any in `verify` or
    `verify-checks`, is the full gate. A fingerprinted rule the project no longer has is a difference in `verify-checks`.
    A variable the factory did not write, a pattern-specific one, and an export line that differs are the full gate (D133);
    `exports` is `export_lines` of the project's files, None where one could not be read."""
    if exports is None:
        raise Unreadable("a file the Makefile reads cannot be read")
    parsed = from_database_parsed(data, units)
    found = fingerprint(parsed)
    reached = {member: set(reach(parsed, [member, *gates.get(member, [])])) for member in members}
    # a check of the project's own (`verify-checks: check-licences`, with a rule of its own) is a check the factory never
    # wrote and not a change to one: it is judged on its own rule below, and `verify-checks` as the factory wrote it
    own = [need for need in parsed.needs.get(ROOTS[1], []) if need not in held["rules"] and ruled(parsed, need)]
    if own and ROOTS[1] in found["rules"]:
        kept = {**parsed.needs, ROOTS[1]: [need for need in parsed.needs[ROOTS[1]] if need not in own]}
        found["rules"][ROOTS[1]] = rule_digest(parsed._replace(needs=kept), ROOTS[1])
    rules = [target for target, held_digest in found["rules"].items()
             if held["rules"].get(target) != held_digest and target not in own]
    rules += [ROOTS[1]] if any(target not in found["rules"] for target in held["rules"]) else []
    reading = {target: used(parsed, target, data.variables) | set(READ_BY_ALL) for target in found["rules"]}
    sent = exported_names(exports)  # the factory's own export lines, where the digest below says they are unchanged
    causes: list[str] = []
    charged: set[str] = set()

    def charge(owners: list[str], cause: str) -> None:
        causes.append(cause) if len(owners) != 1 else charged.add(owners[0])

    causes += [] if digest(exports) == held["exports"] else ["the Makefile's export lines are not the ones the factory wrote"]
    causes += [UNWRITTEN.format(name=name, where=f" for pattern `{pattern}`") for pattern, names in data.patterns.items()
               for name in names]
    for target in sorted(set(rules), key=lambda name: (name not in ROOTS, name)):
        charge([] if target in ROOTS else [member for member in members if target in reached[member]],
               f"the Makefile's `{target}` rule is not the one the factory wrote")
    for name in changed_variables(held, found, data):
        users = [target for target, names in reading.items() if name in names]
        charge([] if name in sent or any(target in ROOTS for target in users) else
               [member for member in members if any(target in reached[member] for target in users)],
               f"the Makefile's variable `{name}` is not the one the factory wrote")
    causes += [UNWRITTEN.format(name=name, where="") for name in found["variables"] if name not in held["variables"]]
    return Judgement(None if not causes else causes[0], frozenset(charged - set(gates)),
                     frozenset(charged & set(gates)))
