"""The stamped `verify` rule: a tree that already passed the gate is not judged again.

`verify` keeps its name and loses its prerequisites; the checks move to `verify-checks`, which carries them, the
blank line and the closing line exactly as `verify` did. The recipe asks `scripts/verify-stamp.py reuse` first: it
exits 0 only after printing the one line that says this tree already passed, and any other answer sends the run on
to the checks, after which `record` writes the stamp. A third group runs only when the checks failed (`reuse`'s exit 0
ends the recipe and `record` always exits 0): it says, last of the gate's own lines, that the gate did not pass and where
make names the failed checks, then exits with the sub-make's own status (a question-mode run, `make -q`, exits 1 for a
gate it did not judge and says nothing). Nothing the script meets can fail the gate (`reuse` exits non-zero for any other
reason, `record` always exits 0), and a run that did not pass never reaches `record`. The sub-make groups each check's
output by target where the running make lists `output-sync` among its features (`VERIFY_GROUP`: the one construct newer
than GNU Make 3.81 a generated Makefile names, and never handed to a make that lacks it). It is quoted, so a make whose
path holds a space runs it, and is given the makefile the gate ran from, so a project whose makefile is not named
`Makefile` runs it too. It is also given `VERIFY_ORDER=1`, which only the gate's checks read (`parallel_gate.gate_order`):
a Java or Go project's native checks wait for one another there, and are what they were when typed alone. `ci` hangs on `verify-checks`, not on `verify`: the extended gate never asks about a stamp, by
whatever route it is reached, and the recipe reads no goals.

Every generated project takes it, whatever its backends, transports and browser apps; the one exception is a
project of an adopted repository (a wrapped application, or the delivery material moved under a directory, where
the stamp is never called), which keeps `adopted_targets.GATE` as it was. The
transport's `check-openapi` line hangs on `verify-checks` inside its own markers, so `./init --http none` cuts it.
"""
from __future__ import annotations

from ..backends import machine_tools
from ..layout import Layout
from ..services import App, backends_of, services_of, web_apps, wrapped_of
from .model_targets import MODEL_GATES

STAMP_SCRIPT = "scripts/verify-stamp.py"

FAILED = "verify: the gate did not pass; each failed check is named above on a line carrying ***"
STAMPED = """VERIFY_STAMP := {arguments}
override VERIFY_GROUP := $(if $(filter output-sync,$(.FEATURES)),--output-sync=target)
verify: ## Full deterministic pre-commit gate (a tree that already passed is not judged again; VERIFY_FORCE=1 runs it anyway)
\t@run=$$(python3 {script} token); python3 {script} reuse --token "$$run" --make "$(MAKE)" $(VERIFY_STAMP) || {{ "$(MAKE)" $(VERIFY_GROUP) --no-print-directory -f "$(firstword $(MAKEFILE_LIST))" verify-checks VERIFY_ORDER=1 && python3 {script} record --token "$$run" --make "$(MAKE)" $(VERIFY_STAMP); }} || {{ rc=$$?; [ "$$rc" -eq 1 ] || echo '{failed}'; exit "$$rc"; }}
.PHONY: verify-checks
verify-checks: {dependencies}
\t@echo
\t@echo 'verify: all gates passed'"""


def ci_gate(apps: list[App], layout: Layout) -> str:
    """The target `ci` depends on for the checks: `verify-checks` where `verify` is stamped, `verify` where it is not."""
    return "verify-checks" if stamped(apps, layout) else "verify"


def stamped(apps: list[App], layout: Layout) -> bool:
    """Whether this project's gate is the stamped one: every generated project's is, an adopted repository's is not."""
    return not wrapped_of(apps) and not layout.moved


def stamp_arguments(apps: list[App], model: bool = False) -> str:
    """What `VERIFY_STAMP` hands the script: a `--tool` per tool the table asks the machine for (the model's `node` and `npm` where
    the gate has its checks), and an `--environment` per Python service, whose interpreter is read from where `uv sync` wrote it."""
    tools = machine_tools(backends_of(apps), bool(web_apps(apps)), model)
    environments = [f"{service.path}/.venv" for service in services_of(apps) if service.backend == "python"]
    return " ".join([f"--tool {tool}" for tool in tools] + [f"--environment {path}" for path in environments])


def has_model_checks(dependencies: str) -> bool:
    """Whether the gate's prerequisites carry the event profile's model checks (`model_targets.MODEL_GATES`)."""
    return set(MODEL_GATES.split()) <= set(dependencies.split())


def stamped_gate(apps: list[App], dependencies: str) -> str:
    """The `verify` rule and the `verify-checks` rule that carries the gate's prerequisites."""
    arguments = stamp_arguments(apps, has_model_checks(dependencies))
    return STAMPED.format(script=STAMP_SCRIPT, failed=FAILED, dependencies=dependencies, arguments=arguments)
