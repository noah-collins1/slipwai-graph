"""The one place the factory's knowledge of what each gate check reads lives.

A row is data: the file inputs a change to which can alter the check's answer (a path, or a directory ending in `/`),
the tools it asks of the machine beyond `make` and `python3`, the variables of `verify-stamp.py`'s `VARIABLES` it reads,
whether its file inputs claim a changed path as known, and why it runs on every scoped run where it does. In a file
input `{own}` is the deployable's own directory, `{dep}` each deployable's, `{web}` each browser app's, `{svc}` each
service that exports an OpenAPI document and `{npm}` each npm package under `packages/`; in a tool `{own}` is likewise,
and `{svc}` is each exporting service's family's tools.

A row the scan of a check's scripts contradicts is corrected by widening it, never by narrowing below what the script
reads (`tests/test_verify_scoped_record.py` holds this table against the scripts). A check the table does not name has
no recorded inputs, and runs on every scoped run for it.
"""
from __future__ import annotations

import sys
from typing import NamedTuple

sys.dont_write_bytecode = True

EVERYTHING = "./"  # the project's own directory: every path


class Row(NamedTuple):
    files: tuple[str, ...] = ()
    tools: tuple[str, ...] = ()
    variables: tuple[str, ...] = ()
    claims: bool = True
    always: str | None = None


# A deployable's lint, typecheck and test units, by the family of its language.
UNITS: dict[str, Row] = {
    "typescript": Row(("{own}", "package.json", "package-lock.json", ".nvmrc", "biome.jsonc"), ("node", "npm")),
    "python": Row(("{own}",), ("uv", "interpreter {own}.venv")),
    "go": Row(("{own}", "go.work", "go.work.sum"), ("go",)),
    "java": Row(("{own}",), ("java",)),
}
GATE_UNITS = ("lint", "typecheck", "test")
EVERY_CHECK_WAITS = "every check waits on it"

CHECKS: dict[str, Row] = {
    "check-openapi": Row(("{svc}", "packages/api-client/", "package.json", "package-lock.json", ".nvmrc"),
                         ("node", "npm", "{svc}")),
    "check-imports": Row(("{dep}", "{npm}")),
    "check-migrations": Row(("{dep}",), ("git",)),
    "check-styles": Row(("{web}",)),
    "check-ux-gates": Row(
        ("{web}", ".slipwai/extensions.json", "AGENTS.md", "package-lock.json", ".github/workflows/verify.yml"),
        ("git", "node", "npm"),
        ("UX_GATES_REQUIRE", "UX_GATES_SINCE", "UX_GATES_SHARD", "SLIPWAI_NO_INSTALL"),
    ),
    "check-model": Row(("docs/event-model/", "{dep}")),
    "check-drawio": Row(("docs/event-model/model.yaml", "docs/event-model/model.drawio"), ("node", "npm")),
    "check-decisions": Row(("specs/", "docs/event-model/model.yaml")),
    "check-benchmark": Row(
        ("specs/", ".specify/", "docs/event-model/model.yaml", "AGENTS.md", "agents/", "commands/", "skills/"),
        ("git",),
    ),
    "check-flags": Row(("{dep}", "packages/", "infra/service/flags.auto.tfvars"), ("git",)),
    "check-deploy-role": Row(("infra/bootstrap/", "infra/service/")),
    "check-python": Row(claims=False, always=EVERY_CHECK_WAITS),
    "check-slice-scope": Row(
        (EVERYTHING,), ("git",),
        ("GITHUB_HEAD_REF", "CI_COMMIT_REF_NAME", "GITHUB_BASE_REF", "CI_MERGE_REQUEST_TARGET_BRANCH_NAME"),
        False, "it compares the whole branch with its base",
    ),
    "check-codegraph": Row((EVERYTHING,), ("git",), ("CODEGRAPH_GATE_NO_SYNC",), False, "it reads every tracked file"),
}
NO_INPUTS = "no recorded inputs"
