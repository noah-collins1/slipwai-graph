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
POSTGRES_ADAPTER = "!src/adapters/driven/event-store-postgres/**"

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


def mutate_list(postgres: bool) -> list[str]:
    """The `mutate` patterns of a service: the Postgres adapter is excluded only where Postgres is the store."""
    return ["src/**/*.ts", "!src/main.ts", "!src/openapi.ts", *([POSTGRES_ADAPTER] if postgres else [])]


def stryker_config(selection: Selection) -> str:
    """The service's `stryker.config.json`: Stryker's options, each annotated by a `_comment` key it ignores."""
    config = {
        "testRunner": "vitest",
        "vitest": {"configFile": "vitest.config.ts", "related": False},
        "vitest_comment": VITEST_COMMENT,
        "mutate": mutate_list(selection.has("postgres")),
        "mutate_comment": MUTATE_COMMENT,
        "reporters": ["clear-text", "json", "html"],
        "incremental": False,
        "cleanTempDir": "always",
        "thresholds": {"high": 80, "low": 60, "break": None},
        "thresholds_comment": THRESHOLDS_COMMENT,
        "tsconfigFile": "stryker-does-not-rewrite-tsconfig.json",
        "tsconfigFile_comment": TSCONFIG_COMMENT,
    }
    return json.dumps(config, indent=2) + "\n"


def stryker_files(services: list[App]) -> dict[str, str]:
    """What Stryker adds beside the services: the wrapper, once, at its path from the project root."""
    return {SCRIPT_PATH: SCRIPT_ASSET.read_text(encoding="utf-8")} if services else {}
