"""Stryker for a generated TypeScript service: its checked-in configuration, the wrapper's path and the recipe line.

The mutation tool of the TypeScript backend is Stryker, pinned exactly with its Vitest runner (ADR 0009), run through
`scripts/stryker-mutation.py`, which decides the verdict from the report Stryker writes and not from Stryker's exit
status. This module is the factory's half: what lands in a service's directory and the one line the Makefile runs.
The wrapper itself is an asset, `assets/languages/typescript/scripts/stryker-mutation.py`.
"""
from __future__ import annotations

import json

from ..assets import LANGUAGE_ROOT
from ..backends import APP
from ..selection import Selection
from ..services import App

# Where the wrapper lands in a project (once, however many TypeScript services there are) and the asset it is read from.
SCRIPT_PATH = "scripts/stryker-mutation.py"
SCRIPT_ASSET = LANGUAGE_ROOT / "typescript" / "scripts" / "stryker-mutation.py"
# The `mutation-full` line of a TypeScript service, with the service's path as the token every native command carries.
FULL_COMMAND = f"python3 {SCRIPT_PATH} {APP}"

CONFIG_NAME = "stryker.config.json"
# The report the JSON reporter writes under the service: the one place the wrapper reads a verdict from.
REPORT = "reports/mutation/mutation.json"
# The adapters only `tests/integration/` reaches, named by the feature that brings that suite (D213): its store's directory.
INTEGRATION_ADAPTERS = "!src/adapters/driven/event-store-{feature}/**"

VITEST_COMMENT = (
    "related is off so that a file holding no mutant reports zero mutants and exits 0, where Stryker's related mode "
    "exits 1 with no report; the first run of the suite then takes every test, and each mutant still runs only the "
    "tests that cover it."
)
MUTATE_COMMENT = (
    "The files Stryker mutates (D213): production code under src/, not the entry points (main.ts, openapi.ts) and, where "
    "Postgres is the store, not the adapter only tests/integration reaches. Add an exclusion the same way; "
    "scripts/stryker-mutation.py reads only literal segments, * within a segment and ** as a whole segment, and a "
    "pattern outside that makes `make mutation` sweep this service."
)
THRESHOLDS_COMMENT = (
    "Nothing here gates anything: the verdict is scripts/stryker-mutation.py's, read from the report (a survivor or a "
    "timeout fails, whatever the percentages say)."
)
TSCONFIG_COMMENT = (
    "Names a file that does not exist on purpose. Stryker rewrites a tsconfig's extends and references with TypeScript's "
    "JavaScript API, which TypeScript 7 does not have; this service's tsconfig.json has neither. If you add an extends or "
    "references that leaves this directory, the copy Stryker tests in will not resolve it and its first test run fails."
)


def mutate_list(integration: str | None) -> list[str]:
    """The `mutate` patterns of a service: the store adapters are excluded only where the store's feature brings a suite
    the Docker-free gate cannot run (`Selection.integration_feature`) — the trait, never the store's name."""
    adapters = [INTEGRATION_ADAPTERS.format(feature=integration)] if integration else []
    return ["src/**/*.ts", "!src/main.ts", "!src/openapi.ts", *adapters]


def pretty(value: object, column: int = 0, indent: int = 0) -> str:
    """JSON as the project's formatter writes it (`biome.jsonc`: two spaces, a hundred columns): an object one key a
    line, an array on one line where it fits after `column` and one item a line where it does not. `make lint` runs
    `biome check` over every file under `apps/`, and a config the formatter would rewrite is a red gate."""
    if isinstance(value, dict):
        pad = " " * (indent + 2)
        rows = [f"{pad}{json.dumps(key)}: {pretty(item, len(pad) + len(json.dumps(key)) + 2, indent + 2)}"
                for key, item in value.items()]
        return "{\n" + ",\n".join(rows) + "\n" + " " * indent + "}"
    if isinstance(value, list):
        inline = "[" + ", ".join(json.dumps(item) for item in value) + "]"
        if column + len(inline) + 1 <= 100:
            return inline
        pad = " " * (indent + 2)
        return "[\n" + ",\n".join(pad + json.dumps(item) for item in value) + "\n" + " " * indent + "]"
    return json.dumps(value)


def stryker_config(selection: Selection) -> str:
    """The service's `stryker.config.json`: Stryker's options, each annotated by a `_comment` key it ignores."""
    config = {
        "testRunner": "vitest",
        "vitest": {"configFile": "vitest.config.ts", "related": False},
        "vitest_comment": VITEST_COMMENT,
        "mutate": mutate_list(selection.integration_feature),
        "mutate_comment": MUTATE_COMMENT,
        "reporters": ["clear-text", "json", "html"],
        "incremental": False,
        "cleanTempDir": "always",
        "thresholds": {"high": 80, "low": 60, "break": None},
        "thresholds_comment": THRESHOLDS_COMMENT,
        "tsconfigFile": "stryker-does-not-rewrite-tsconfig.json",
        "tsconfigFile_comment": TSCONFIG_COMMENT,
    }
    return pretty(config) + "\n"


def stryker_files(services: list[App]) -> dict[str, str]:
    """What Stryker adds beside the services: the wrapper, once, at its path from the project root."""
    return {SCRIPT_PATH: SCRIPT_ASSET.read_text(encoding="utf-8")} if services else {}


# Emitted above the `mutation:` target of a project with a TypeScript service, for the reason the other backends' notes
# are: the next person to read a mutation result needs to know what ran and where the verdict is decided. `__APP__/<file>`
# is rewritten to the project's own TypeScript services by `mutation_notes`, for every name in `NAMED_FILES`.
TYPESCRIPT_MUTATION_NOTE = f"""\
# Wired up: Stryker 10.0.0 with its Vitest runner, run through `{SCRIPT_PATH}`, one wrapper for the project, and
# configured by one `{APP}/{CONFIG_NAME}` per service. The wrapper installs from the committed lock (`npm ci`), starts
# Stryker as `npm exec --no` so that nothing is fetched, and decides the verdict itself: it reads
# `{APP}/{REPORT}` and fails on a survivor, a timeout or any status but killed and ignored, whatever Stryker's
# own exit status says. A mutant no test reaches is counted and reported, never failed. The report is written whether the
# run passed or failed and is ignored by git: it is one run on one machine, and the next run replaces it.
#
# `make mutation` scopes itself on a `slice/<id>` branch, to the production files that differ from the trunk commit the
# branch was cut from, and `make mutation SINCE=<branch-or-commit>` does the same against that ref on any checkout, CI
# included. CI, the trunk and a checkout the script cannot read run the sweep, `make mutation-full`, which is also what an
# empty `SINCE` runs. Phase 4 on `main` runs `make mutation SINCE=<the commit before the merge>`, so the check is priced
# by the change that merged. A scoped run is held against the `mutate` list in the config first: Stryker's `--mutate`
# replaces that list, so a file the list excludes (`main.ts`, `openapi.ts`, the Postgres adapter) is named and never
# started. A change to `{APP}/{CONFIG_NAME}`, to `{SCRIPT_PATH}` or to the Stryker versions sweeps the service, since no scope
# can be trusted across it; a change to the `mutation` or `mutation-full` rule, or a `mutation-full` recipe that is not the
# one the factory wrote, makes the whole run the sweep, and that recipe runs as written.
#
# An equivalent mutant is a `// Stryker disable next-line <mutator>: <reason>` comment on the line above it, named in the
# commit that adds it; the survivors of the starter's own tests are weak tests to strengthen, not noise to suppress.
# Only a `// Stryker disable next-line <mutator>: <reason>` comment excuses a mutant: `excludedMutations` in the config
# and block or file-wide disable comments do not, and the wrapper fails a mutant they ignore.
#
# The default TypeScript starter's `make mutation-full` fails the day it is generated, because its own starter tests leave
# survivors; a slice that edits one of those files meets that file's survivors in its scoped `make mutation`. The minimal
# starter is green. A fix is planned: a follow-on slice makes the starter's tests kill them.
#
# A mutant that Stryker reports `Survived` while the suite did not run to completion under it (a `beforeAll` threw, so the
# file's tests were skipped and no test failed) is not a survivor: the wrapper reads that from the report, `testsCompleted`
# below the dry run's test count on a mutant every test runs under, and fails it as `Incomplete`, never as `Survived`.
#
# Two settings in the config look odd and are not. `related` is off in `vitest`, so that a file holding no mutant
# reports zero mutants and the wrapper says so, where Stryker's related mode exits 1 with no report. And `tsconfigFile`
# names a file that does not exist: Stryker rewrites a tsconfig's `extends` and `references` with TypeScript's JavaScript
# API, which TypeScript 7 does not have, and this service's tsconfig has neither.
"""
# Said in the command text beside the Go report's sentence.
TYPESCRIPT_REPORT_TEXT = f"""The TypeScript run leaves its report at `<service>/{REPORT}`, and `{SCRIPT_PATH}` decides the verdict from it — read that, not the scrollback.
"""
