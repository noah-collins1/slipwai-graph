"""The stamped `verify` rule: a tree that already passed the gate is not judged again.

`verify` keeps its name and loses its prerequisites; the checks move to `verify-checks`, which carries them, the
blank line and the closing line exactly as `verify` did. The recipe asks `scripts/verify-stamp.py reuse` first: it
exits 0 only after printing the one line that says this tree already passed, and any other answer sends the run on
to the checks, after which `record` writes the stamp. Nothing the script meets can fail the gate (`reuse` exits
non-zero for any other reason, `record` always exits 0), and a run that did not pass never reaches `record`.

Chosen only for the projects whose gate the stamp is held to so far — one Python service, no transport, no
frontend, nothing wrapped; every other project keeps `adopted_targets.GATE` as it was.
"""
from __future__ import annotations

from ..services import App, services_of, transports_of, web_apps, wrapped_of

STAMP_SCRIPT = "scripts/verify-stamp.py"

STAMPED = """VERIFY_STAMP :=
verify: ## Full deterministic pre-commit gate (a tree that already passed is not judged again; VERIFY_FORCE=1 runs it anyway)
\t@python3 {script} reuse --goals "$(MAKECMDGOALS)" --make "$(MAKE)" $(VERIFY_STAMP) || {{ $(MAKE) --no-print-directory verify-checks && python3 {script} record --make "$(MAKE)" $(VERIFY_STAMP); }}
.PHONY: verify-checks
verify-checks: {dependencies}
\t@echo
\t@echo 'verify: all gates passed'"""


def stamped(apps: list[App]) -> bool:
    """Whether this project's gate is the stamped one."""
    services = services_of(apps)
    return (
        not wrapped_of(apps) and not web_apps(apps) and not transports_of(apps)
        and len(services) == 1 and services[0].backend == "python"
    )


def stamped_gate(dependencies: str) -> str:
    """The `verify` rule and the `verify-checks` rule that carries the gate's prerequisites."""
    return STAMPED.format(script=STAMP_SCRIPT, dependencies=dependencies)
