"""mutmut for a generated Python service: the wrapper's path and the one recipe line.

The mutation tool of the Python backend is mutmut, pinned exactly in each service's dev group (ADR 0010), configured by
the `[tool.mutmut]` table of the service's `pyproject.toml` and run through `scripts/mutmut-mutation.py`, which decides
the verdict from the `.meta` files mutmut writes and not from mutmut's exit status. This module is the factory's half:
where the wrapper lands in a project and the one line the Makefile runs. The wrapper itself is an asset,
`assets/languages/python/scripts/mutmut-mutation.py`.
"""
from __future__ import annotations

from ..assets import LANGUAGE_ROOT
from ..backends import APP
from ..services import App

# Where the wrapper lands in a project (once, however many Python services there are) and the asset it is read from.
SCRIPT_PATH = "scripts/mutmut-mutation.py"
SCRIPT_ASSET = LANGUAGE_ROOT / "python" / "scripts" / "mutmut-mutation.py"
# The `mutation-full` line of a Python service, with the service's path as the token every native command carries.
FULL_COMMAND = f"python3 {SCRIPT_PATH} {APP}"
# Where a run leaves what it wrote, relative to the service: mutmut's copy of `src/` and one `.meta` file per mutated
# file. Spelled once: the note, the command text and the changelog fragment all point at it.
REPORT = "mutants/"
META_REPORT = f"{REPORT}<file>.meta"


def mutmut_files(services: list[App]) -> dict[str, str]:
    """What mutmut adds beside the services: the wrapper, once, at its path from the project root."""
    return {SCRIPT_PATH: SCRIPT_ASSET.read_text(encoding="utf-8")} if services else {}


# Emitted above the `mutation:` target of a project with a Python service, for the reason the other backends' notes are:
# the next person to read a mutation result needs to know what ran and where the verdict is decided. `__APP__/<file>` is
# rewritten to the project's own Python services by `mutation_notes`, for every name in `NAMED_FILES`.
PYTHON_MUTATION_NOTE = f"""\
# Wired up: mutmut 3.8.0, pinned in each service's `dev` group, configured by the `[tool.mutmut]` table of
# `{APP}/pyproject.toml` and run through `{SCRIPT_PATH}`, one wrapper for the project. The wrapper installs from the
# committed lock (`uv sync --locked`), has mutmut generate the mutants, reads which ones each file holds from the `.meta`
# files it writes under `{APP}/{REPORT}` (`{META_REPORT}`) and hands `mutmut run` exactly those names. It decides the
# verdict itself, from the `.meta` files and never from mutmut's exit status, which is 0 when mutants survive: a killed
# mutant passes, a mutant no test reaches is counted and reported, never failed, and anything else fails. The report is
# written whether the run passed or failed and is ignored by git: it is one run on one machine, and the next run
# replaces it.
#
# `make mutation` scopes itself on a `slice/<id>` branch, to the production files that differ from the trunk commit the
# branch was cut from, and `make mutation SINCE=<branch-or-commit>` does the same against that ref on any checkout, CI
# included. CI, the trunk and a checkout the script cannot read run the sweep, `make mutation-full`, which is also what an
# empty `SINCE` runs. Phase 4 on `main` runs `make mutation SINCE=<the commit before the merge>`, so the check is priced
# by the change that merged. A change to the `[tool.mutmut]` table, to the mutmut pin, to the `mutmut` or `libcst` entries
# of the lock or to `{SCRIPT_PATH}` sweeps the service, since no scope can be trusted across it; a change to the `mutation`
# or `mutation-full` rule, or a `mutation-full` recipe that is not the one the factory wrote, makes the whole run the
# sweep, and that recipe runs as written.
#
# An equivalent mutant is a bare `# pragma: no mutate` comment on its line, named in the commit that adds it; the
# survivors of the starter's own tests are weak tests to strengthen, not noise to suppress. Only that bare comment excuses
# a mutant: `# pragma: no mutate block`, `start` and `end`, and `do_not_mutate_patterns` in the table silence mutants
# nobody looked at, and the wrapper fails the run that holds them.
#
# The default Python starter's `make mutation-full` reports survivors the day it is generated, because its own starter
# tests leave them; a slice that edits one of those files meets that file's survivors in its scoped `make mutation`. The
# minimal starter (no HTTP framework, the memory store) is green.
#
# Two settings in the table look odd and are not. `tests/integration` is left out of the test selection, as it is of
# `make test`, because it needs a database. And `-p no:xdist` keeps pytest on one process, because mutmut records which
# tests reach which function from a single one.
"""
# Said in the command text beside the Go and TypeScript reports' sentences.
PYTHON_REPORT_TEXT = f"""The Python run leaves its report at `<service>/{REPORT}` (`{META_REPORT}`), and `{SCRIPT_PATH}` decides the verdict from it — read that, not the scrollback.
"""
