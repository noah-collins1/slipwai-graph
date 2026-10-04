"""One sync per `make` run: the target every Python-running target names, and the recipes that run a mode without a second one.

`./scripts/verify <mode>` syncs every Python service's environment from its committed lock before it runs the mode, and
that is what a mode reached any other way — typed by a person, a CI step, an agent's hook — gets. A `make` run that reaches
several modes (`make verify` reaches three, `make -j verify` runs them at once on one `.venv`) would sync once per mode, so
the Makefile syncs once instead: `sync` is a phony target, every target whose recipe runs a mode names it as a
prerequisite, and the recipes pass the script a second argument, `--synced`, that says the environment is built. The
argument is the Makefile's own. It is never a default and never read from the environment, and nothing published outside
the Makefile — the CI workflow, `service_commands()`, the pages — spells it: a mode reached any other way syncs first.

Only Python has the target. TypeScript's `npm ci` is already the recipe of one file target, and Go and Java have no
install step in a gate mode to share.
"""
from __future__ import annotations

import re

from ..services import App, services_of
from ..tooling import verify_path
from .gate import FAILED
from .native_commands import STEP, steps
from .openapi import exporting

SYNC = "sync"
FIRST = "check-python"

# The paragraph the gates page of a stamped project carries beside the stamp's (`docs.documentation_files`). Wherever the
# gate is not the stamped one the page has neither: a moved layout's and an adopted repository's gate is serial, and the
# page says nothing of `-j` there, so every sentence below is read for a gate that is stamped. The adopted clause is
# said here, for a developer who works in both kinds of repository; the fragment's catch-up says it to the adopted one.
PAGE = f"""`make -j verify` runs the gate's checks at once, from GNU Make 3.81 on; use it when you wait on the gate locally,
and `make verify` where you want them one after another. Each check's output appears when that check finishes, so a long
test run shows no progress until then; on a make older than 4.0 lines may interleave, and the order of the lines is not
promised either way. A failed run ends on `{FAILED}`, then make's own last line. The claim is for `verify` as the only goal:
`make -j ci` is not promised. A passing run that installed dependencies as it went is not recorded, the next run on the
unchanged tree is, and `make install` beforehand makes the first one count. An adopted repository's gate runs serially
whatever `-j` says: a bare `.NOTPARALLEL:` holds its own targets, and a recorded command that itself calls `make` is the one
thing it cannot hold, that application's own.

"""


def python_services(apps: list[App]) -> list[App]:
    """The generated services written in Python: the ones whose environment the target builds."""
    return [service for service in services_of(apps) if service.language == "python"]


def script_of(apps: list[App]) -> str:
    """Where the Python family's verify script is, as a recipe spells it."""
    return f"./{verify_path('python', apps)}"


def needs(service: App) -> str:
    """The prerequisite a target of one service's own names, as it sits on a target line: ` sync` or nothing."""
    return f" {SYNC}" if service.language == "python" else ""


def in_recipe(recipe: str, apps: list[App]) -> str:
    """A recipe whose Python modes run on the environment `sync` built: each call of the script takes `--synced`
    after its mode, and a written-out `--install-only` line (the sync itself) goes. A project with no Python service
    has none of either, so the recipe is returned as it is."""
    if not python_services(apps):
        return recipe
    script = re.escape(script_of(apps))
    kept = [line for line in steps(recipe) if not re.fullmatch(rf"{script} --install-only", line)]
    return STEP.join(re.sub(rf"({script} --[a-z]+(?:-[a-z]+)*)(?! --synced)", r"\1 --synced", line) for line in kept)


def sync_rules(project_name: str, apps: list[App], suites: list[App], formatting: bool) -> str:
    """The `sync` target and the one line that makes it a prerequisite of every target that runs a Python mode.

    `lint`, `typecheck`, `test`, `adversarial` and `install` always; `format` where this project has one;
    `test-integration`, or the per-service targets, for a Python service's suite; `openapi` and `check-openapi`
    where a Python service exports its document. `migrate` and `dev` name it on their own target lines, inside the
    marked regions they live in (`makefile.install_step`, `makefile.dev_targets`), because a line outside would
    define a pruned target with no recipe. Nothing for a project with no Python service.
    """
    if not python_services(apps):
        return ""
    dependents = ["typecheck", "lint", *(["format"] if formatting else []), "test", "adversarial", "install"]
    python_suites = [s for s in suites if s.language == "python" and s.generated]
    if len(suites) == 1:
        dependents += ["test-integration"] if python_suites else []
    else:
        dependents += [f"test-integration-{s.name}" for s in python_suites]
    if any(s.language == "python" for s in exporting(project_name, apps)):
        dependents += ["openapi", "check-openapi"]
    return f"""
# Each Python service's environment, built from its committed lock once per `make` run: every target below names it
# rather than syncing inside its own recipe, so `make verify`, `make -j verify` and `make lint test` sync once. A mode
# run any other way (`{script_of(apps)[2:]} --lint-only` by hand) still syncs first.
.PHONY: {SYNC}
{SYNC}: {FIRST} ## Build each Python service's environment from its committed lock, once per make run
\t{script_of(apps)} --install-only
{' '.join(dependents)}: {SYNC}
"""


def python_first(stamped: bool, dependencies: str) -> str:
    """The one line that makes `check-python` first under `-j`: every prerequisite of the gate but itself names it.

    In a serial run nothing moves, because it leads the list already; under `-j` an older `python3` is named before the
    sync or any check starts. `check-openapi`, which is not in `dependencies` (it hangs on the gate inside its
    transport's markers), names it on its own target line (`openapi.openapi_targets`), and `sync` on its own. The
    root's `npm ci` file target and the model tooling's are not checks and do not: a file target that depended on a
    phony one would reinstall on every run. Nothing where the gate is not the stamped one — an adopted repository's runs
    serially whatever `-j` says (D88) and its rule is pinned byte for byte, `ci: verify` following it.
    """
    waiting = [word for word in dependencies.split() if word != FIRST]
    return f"{' '.join(waiting)}: {FIRST}\n" if stamped and waiting else ""


def gate_order(stamped: bool, apps: list[App]) -> str:
    """The order the gate's own sub-make gives the native checks, inside `ifdef VERIFY_ORDER` (3.80) so that a target typed
    alone is what it was: only the gate's recipe hands its sub-make the variable.

    Two of the families write where the others read. Maven's three checks write one service's `target/`, so with a Java
    service `typecheck` waits for `lint` and `test` for `typecheck`. Go's first `go` command resolves the workspace and
    writes `go.work.sum` on a fresh clone, and that is `typecheck`'s, so with a Go service `lint` and `test` wait for it
    (`typecheck` stays first, as it is in the serial run). A project with both takes the Java chain, which covers Go.
    Python and TypeScript need neither: after the sync and the root's install their checks write only their own caches.
    Nothing where the gate is not the stamped one, which is serial.
    """
    languages = {service.language for service in services_of(apps)}
    if not stamped:
        return ""
    if "java" in languages:
        rules = "typecheck: lint\ntest: typecheck\n"
    elif "go" in languages:
        rules = "lint test: typecheck\n"
    else:
        return ""
    return f"# Under the gate the checks that share a build directory run one after another.\nifdef VERIFY_ORDER\n{rules}endif\n"
