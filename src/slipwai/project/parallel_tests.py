"""What the gates page says about running tests across cores: the project's mark, and what each runner already does.

The mark is `parallelSafe` at the top of `project.json`. A Python service's `scripts/verify` reads it each time it
runs (`languages/python.py`), so the page says what the script does and not what a project once asked for. The other
backends' commands are unchanged by it, and the page records what their runners do by themselves — the sentence a
person reaches for when asking whether the gate is parallel — for the backends the project has and no others.
"""
from __future__ import annotations

from ..services import App, backends_of

# `-p xdist` names the plugin to pytest, so a run with `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` still starts its workers,
# and registers it under the name autoload would have, so a run without the variable does not register it twice.
FLAGS = "-p xdist -n auto --maxprocesses 4"

MARK = f"""**Tests across cores.** A Python service's gate runs its tests across cores where `project.json` says it may: `"parallelSafe": true`,
which every new project has, adds `{FLAGS}` (`pytest-xdist`, capped at four workers) to the gate's `pytest` in `make test`
and `make verify`, and never to the adversarial run or the integration run, whose tests share one database. **A missing mark is serial**,
and so is `false`, or a file the gate cannot read: a project made before the mark existed has none, and `slipwai migrate` never adds
one. Only the JSON `true` turns it on (a string `"true"` is serial), and a mark written twice is serial, because the gate cannot
tell which copy is meant: add the line `"parallelSafe": true,` once, with its comma, right after the `"target"` line, where `generate` writes it. The gate reads the mark each time it runs, so a change takes effect on the next run with nothing regenerated. Set it `false`
when the tests share a file, a port, a database or module-level state, which a second worker would trip over, or when a Python module at the project's root is named like a standard-library one (a `json.py`, say): it crashes every worker with *maximum crashed workers reached*, so rename it or set the mark `false`. On a small suite the workers cost a fraction of a second; they pay back once the suite takes several seconds. The mark needs `pytest-xdist`
in each Python service's development tools, which every service has; a service that removed it fails on an argument error until it is back, and so does one that sets `-p no:xdist` in `PYTEST_ADDOPTS`, which asks for no xdist while the mark asks for it: set the mark `false`. A parallel run can also hide a test that depends on another test's leftovers, because the two may run on different workers, so CI runs the suite serially to catch it: a test that passes locally but fails in CI is the first thing to look for.
"""

# A project with no Python service carries the key too, because `add-service` can bring one later.
NO_PYTHON = """Where `project.json` carries `"parallelSafe": true`, a Python service's tests run across cores; it changes nothing until a Python service is added.
"""

# What each family's runner does with the tests the gate hands it, whatever the mark says: no backend's command changes.
RUNNERS = {
    "typescript": "TypeScript: Vitest runs test files in parallel, by file.",
    "go": "Go: `go test` runs packages in parallel, by package.",
    "java-quarkus": "Java: Maven's Surefire runs tests one at a time, as configured here.",
    "java-spring": "Java: Maven's Surefire runs tests one at a time, as configured here.",
}


def parallel_tests_page(apps: list[App]) -> str:
    """The paragraphs for `docs/gates.md`: the mark where there is a Python service, one runner sentence for each
    backend that is not Python (once each, though two Java backends say the same), and nothing for a project that has
    none of them — an adopted repository's applications are not the factory's, so its page gains nothing."""
    backends = backends_of(apps)
    runners = list(dict.fromkeys(RUNNERS[backend] for backend in backends if backend in RUNNERS))
    python = "python" in backends
    lead = ("The other runners need no mark and run as they always have. " if python
            else "Each runner here needs no mark and runs as it always has. ")
    parts = ([MARK] if python else [NO_PYTHON] if runners else []) + (
        [lead + " ".join(runners) + "\n"] if runners else []
    )
    return "\n" + "\n".join(parts) if parts else ""
