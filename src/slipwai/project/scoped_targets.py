"""The scoped gate's targets: a deployable is a component with `lint-`, `typecheck-` and `test-` of its own.

`make verify` is one gate over the whole project, and a branch that touched one deployable does not need every
other deployable's lint, type check and tests to learn what it already knew. The generated `Makefile` therefore ends
with a section that splits each of the gate's three recipes by deployable, as targets nothing in the gate names: the
`verify`, `verify-checks` and `ci` rules and everything before this section are byte for byte what they were, so the
merge root and CI still run exactly the gate they ran.

A unit's recipe is that deployable's own lines of today's merged recipe, read from the same tables the gate is built
from (`native_commands.commands_of`, `web_recipes`), never spelled a second time. A line that names no deployable's
path — the Python family's `./scripts/verify --lint-only`, Go's `gofmt` over every module and its coverage warm-up —
belongs to the family, and is a *family target*, `<check>_<family>`, that each unit of the family names as a
prerequisite: a make that runs two Python units runs the shared line once. A unit takes what the gate's checks take
before they run, `check-python` first and `sync` (Python) or `build-packages` (npm) after, and under `VERIFY_ORDER`
the order the gate gives a Java or Go service (`parallel_gate.gate_order`).

A deployable named `integration`, or beginning `integration-`, gets no units: `test-integration` and
`test-integration-<service>` are existing targets, and a second recipe under either name would replace theirs. The
script that selects units (`scripts/verify-scoped.py`) finds that a deployable it needs is missing and runs the full
gate, so a name is never a way to skip a check.
"""
from __future__ import annotations

import re

from ..layout import Layout
from ..services import App, services_of, web_apps
from .gate import stamped
from .native_commands import commands_of, steps, web_recipes
from .parallel_gate import FIRST, SYNC, in_recipe

CHECKS = ("lint", "typecheck", "test")
NPM_PACKAGES = "build-packages"
ORDER = "ifeq ($(origin VERIFY_ORDER),command line)"
HEADER = """
# Scoped gate: each deployable's lint, typecheck and test as targets of their own, and the family targets that hold
# a line shared by several. Nothing above this line names them, so `make verify` and `make ci` are what they were.
"""


def unit_of(check: str, app: App) -> str:
    return f"{check}-{app.name}"


def has_units(app: App) -> bool:
    """Whether a deployable's `test-<name>` is free: `test-integration` and `test-integration-<service>` are not."""
    return app.name != "integration" and not app.name.startswith("integration-")


def own_lines(apps: list[App]) -> list[tuple[App, dict[str, list[str]]]]:
    """Every deployable with, per check, the lines of its recipe in the gate's own spelling, in the gate's order."""
    services = services_of(apps)
    web = web_apps(apps)
    recipes = [*zip(services, commands_of(services, apps), strict=True), *zip(web, web_recipes(web), strict=True)]
    return [(app, {check: steps(in_recipe(recipe[check], apps)) for check in CHECKS}) for app, recipe in recipes]


def names_a_path(line: str, paths: list[str]) -> bool:
    return any(re.search(rf"(?<![\w/.-]){re.escape(path)}(?![\w-])", line) for path in paths)


def prerequisites(app: App) -> list[str]:
    """What every one of the deployable's targets waits for, as the gate's checks do: the Python check first, then
    the environment (Python) or the packages (npm)."""
    return [FIRST, *([SYNC] if app.language == "python" else [NPM_PACKAGES] if app.language == "typescript" else [])]


def rule(target: str, needs: list[str], lines: list[str]) -> str:
    return f"{target}: {' '.join(needs)}\n" + "".join(f"\t{line}\n" for line in lines)


def order_rules(apps: list[App]) -> str:
    """What `gate_order` gives the gate, per service: Java's three in a chain, and Go's typecheck and test after
    its lint. Under the gate's own `VERIFY_ORDER` only, so a unit typed alone is what it was."""
    rules = ""
    for service in services_of(apps):
        if not has_units(service):
            continue
        if service.language == "java":
            rules += f"{unit_of('typecheck', service)}: {unit_of('lint', service)}\n"
            rules += f"{unit_of('test', service)}: {unit_of('typecheck', service)}\n"
        elif service.language == "go":
            rules += f"{unit_of('typecheck', service)} {unit_of('test', service)}: {unit_of('lint', service)}\n"
    return f"{ORDER}\n{rules}endif\n" if rules else ""


def verify_scoped_rule() -> str:
    """The one target a person types: `scripts/verify-scoped.py run`, handed the make and the makefile that are running,
    as `verify` hands them to its own sub-make. It is the gate (`make verify`) wherever it cannot read the branch."""
    return """
.PHONY: verify-scoped
verify-scoped: ## The checks whose inputs changed on a slice branch; the full gate wherever it cannot tell
\t@python3 scripts/verify-scoped.py run --make "$(MAKE)" --makefile "$(firstword $(MAKEFILE_LIST))"
"""


def scoped_section(apps: list[App], layout: Layout) -> str:
    """The section a stamped gate's `Makefile` ends with; nothing for an adopted repository's, which keeps its own."""
    if not stamped(apps, layout):
        return ""
    everything = own_lines(apps)
    paths = [app.path for app, _ in everything]
    units = [(app, lines) for app, lines in everything if has_units(app)]
    if not units:
        return ""
    names: list[str] = []
    text = ""
    for check in CHECKS:
        families: dict[str, list[str]] = {}
        rules = ""
        for app, lines in units:
            own = [line for line in lines[check] if names_a_path(line, paths)]
            shared = [line for line in lines[check] if not names_a_path(line, paths)]
            needs = prerequisites(app)
            if shared:
                family = f"{check}_{app.language}"
                known = families.setdefault(family, [])
                known.extend(line for line in shared if line not in known)
                needs.append(family)
            rules += rule(unit_of(check, app), needs, own)
            names.append(unit_of(check, app))
        for family, shared_lines in families.items():
            language = family.split("_", 1)[1]
            names.append(family)
            text += rule(family, [FIRST, *([SYNC] if language == "python" else [])], shared_lines)
        text += rules
    return f"{HEADER}.PHONY: {' '.join(names)}\n{text}{order_rules(apps)}{verify_scoped_rule()}"
