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

import importlib.util
import json
import re
import sys
from functools import cache
from typing import Any

from ..assets import TOOLKIT_ROOT
from ..catalog import family_of
from ..layout import Layout
from ..services import App, services_of, web_apps
from .gate import stamped
from .native_commands import commands_of, steps, web_recipes
from .parallel_gate import FIRST, SYNC, in_recipe

CHECKS = ("lint", "typecheck", "test")
NPM_PACKAGES = "build-packages"
RULES_PATH = "scripts/verify_scoped/rules.json"
NO_RECORD = "this layout has no verification-dependency record yet — the full gate runs"
ORDER = "ifeq ($(origin VERIFY_ORDER),command line)"
HEADER = """
# Scoped gate: each deployable's lint, typecheck and test as targets of their own, and the family targets that hold
# a line shared by several. Nothing above this line names them, so `make verify` and `make ci` are what they were.
"""

SCOPED_PAGE = """`make verify-scoped` runs only the checks whose inputs changed, and prints a line for each check, run or skipped, with
the reason. It compares two things. Files, committed or not, are compared with the trunk commit the branch is built on,
the one its last line names (`compared with `main` at <short>`); that commit moves when the branch is rebased onto the
trunk or merges it. The base is the newer of local `main` and `origin/main`. Where local `main` has commits `origin/main` does not, every
file those commits changed counts as changed too, so a check is skipped only on the word of a commit the forge's trunk
carries. With a remote but no `origin/main` it is the full gate. With no remote at all, local `main` is the word, and only
the merge root's `make verify` stands behind it. Tools,
variables and the files git ignores are compared with the baseline the branch's last green full run left. It scopes on a `slice/<id>` branch with a usable base, outside CI:
every deployable's `lint-`, `typecheck-` and `test-` is a check, and each is chosen when a changed file is one it reads,
when a contract it consumes changed, when an obligation names it, or when the machine differs from the baseline,
and everywhere else it is the full gate, `make verify`, and says why on its first line, so it is never wrong where it cannot
tell: on the trunk, on a branch that is no `slice/<id>`, with no usable base, in CI, under `VERIFY_FORCE`, and wherever
the checkout cannot be read. Dependency knowledge it does not have broadens it to the full gate as well: a changed
`Makefile`, `project.json` or gate script under `scripts/`, a changed path no check or contract claims, and a record
that cannot be built. It scopes only the `Makefile` the factory wrote. If your `Makefile` differs from the factory's in any
way, or make would also read a `GNUmakefile`, a `makefile` or a file named in `MAKEFILES`, every scoped run is the full
gate and says so on its first line, until the file is the factory's text again; put targets of your own in a file `make
verify` does not read and run them with `make -f deploy.mk <target>`. Every scoped run is also the full gate if make is
run with an option that adds text or conditions, `--eval`, `-I`, `-e`, a variable on the command line other than
`VERIFY_FORCE`, and a `make verify` run that way writes no stamp and no baseline. And it is the full gate when one
deployable reaches into another deployable's path or names its package, because no check can tell what that edge
carries: share through `packages/` or a published contract, and scoping returns. The baseline beside the stamp is a record under the git directory, never in the working tree: the
tools the machine answered for and the variables' digests, written by a green full run on a `slice/<id>` branch and
removed by any full run, so a full run that fails leaves none. A tool or variable that differs from the baseline chooses
every check that reads it, and with no baseline, or another branch's, every check that reads a tool or a variable runs.
`verification.obligations` in `project.json` declares an integration obligation: a name, two or more components, and the
checks (`lint`, `typecheck`, `test`, or a unit's name) that run when either component changes. The default is none, and
the factory never writes it; it is read as `project.json` stands at the branch's base. Declare one when two components
agree on something no file of either shows and no contract path covers, such as two services that agree on a
queue's message. `make -j verify-scoped` runs the chosen checks at the same time, as `make -j verify` does.

"""


def adopted_scoped_sentence(layout: Layout) -> str:
    """The one sentence an unstamped page says of the target: it is the full gate, because nothing here records what a
    check reads."""
    return (f"`{layout.make} verify-scoped` is the full gate: {NO_RECORD.split(' — ')[0]}, so it says so and runs "
            f"`{layout.make} verify`.\n\n")


def scoped_page(apps: list[App], layout: Layout) -> str:
    return SCOPED_PAGE if stamped(apps, layout) else adopted_scoped_sentence(layout)


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
    its lint. Under the gate's own `VERIFY_ORDER` only, so a unit typed alone is what it was.

    Go's lint writes the workspace's `go.work.sum`, which every Go service shares, so with several the gate's whole order
    (D96) is every lint before any typecheck or test: each Go typecheck and test also waits for whichever Go lint is among
    the goals of this run, and for no other, so that a lint that was skipped is not run for its order."""
    rules = ""
    go = [service for service in services_of(apps) if service.language == "go" and has_units(service)]
    for service in services_of(apps):
        if not has_units(service):
            continue
        if service.language == "java":
            rules += f"{unit_of('typecheck', service)}: {unit_of('lint', service)}\n"
            rules += f"{unit_of('test', service)}: {unit_of('typecheck', service)}\n"
        elif service.language == "go":
            rules += f"{unit_of('typecheck', service)} {unit_of('test', service)}: {unit_of('lint', service)}\n"
    if len(go) > 1:
        later = " ".join(unit_of(check, service) for service in go for check in ("typecheck", "test"))
        lints = " ".join(unit_of("lint", service) for service in go)
        rules += f"{later}: $(filter {lints},$(MAKECMDGOALS))\n"
    return f"{ORDER}\n{rules}endif\n" if rules else ""


def verify_scoped_rule() -> str:
    """The one target a person types: `scripts/verify-scoped.py run`, handed the make and the makefile that are running,
    as `verify` hands them to its own sub-make. It is the gate (`make verify`) wherever it cannot read the branch."""
    return """
.PHONY: verify-scoped
verify-scoped: ## The checks whose inputs changed on a slice branch; the full gate wherever it cannot tell
\t@python3 scripts/verify-scoped.py run --make "$(MAKE)" --makefile "$(firstword $(MAKEFILE_LIST))"
"""


def adopted_rule(layout: Layout) -> str:
    """An adopted repository's `verify-scoped`: its gate has no stamp and no record of what each check reads, so the
    target says so and runs the full gate, as `ratchet-tighten` runs its own: through `$(MAKE)` with the layout's flag."""
    return f"""
.PHONY: verify-scoped
verify-scoped: ## The full gate: this layout has no verification-dependency record yet
\t@echo 'verify-scoped: {NO_RECORD}'; $(MAKE){layout.make_flag} --no-print-directory verify
"""


def scoped_section(apps: list[App], layout: Layout) -> str:
    """The section a stamped gate's `Makefile` ends with; for an adopted repository's, the one target that says it has
    no record and runs its own full gate."""
    if not stamped(apps, layout):
        return adopted_rule(layout)
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
            text += rule(family, [FIRST, *([SYNC] if family_of(language) == "python" else [])], shared_lines)
        text += rules
    return f"{HEADER}.PHONY: {' '.join(names)}\n{text}{order_rules(apps)}{verify_scoped_rule()}"


@cache
def rules_module() -> Any:
    """`scripts/verify_scoped/rules.py` as the toolkit ships it, loaded and never copied: the one canonical form of a rule
    and the reader of the factory's own text. No bytecode is written beside it, as `assets.py` does for its other loads."""
    source = TOOLKIT_ROOT / "scripts/verify_scoped/rules.py"
    spec = importlib.util.spec_from_file_location("slipwai_verify_scoped_rules", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load the rules reader from {source}")
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def rules_file(makefile_text: str) -> str:
    """The text of `scripts/verify_scoped/rules.json` for the `Makefile` text a stamped project is given: what the
    factory wrote, read by the same code the project's script reads make's database with. A construct that code cannot
    read raises here, so it fails the factory's tests and never reaches a project."""
    return json.dumps(rules_module().from_text(makefile_text), indent=2, sort_keys=True) + "\n"
