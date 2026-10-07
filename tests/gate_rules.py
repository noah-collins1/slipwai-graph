"""Read a generated Makefile's gate: the target a full run's checks hang on, its prerequisites and its rule.

Not a test module. Its own file so a test that only reads a Makefile does not import `test_verify_stamp_pinned`,
whose imports reach every generating test; that module re-exports the three names for the tests that import them.
"""
from __future__ import annotations

import re

# Reads a Makefile text a caller passes; generates nothing and opens nothing of the repository.
TEST_SELECTION: dict[str, object] = {}


def gate_target_name(makefile: str) -> str:
    """The target a full run's checks hang on: `verify-checks` where the stamp's recipe has split them off."""
    return "verify-checks" if re.search(r"^verify-checks:", makefile, re.M) else "verify"


def gate_prerequisites(makefile: str) -> list[str]:
    """Every prerequisite the gate target is given, in the order its rules appear, `##` descriptions removed."""
    name = gate_target_name(makefile)
    found: list[str] = []
    for line in makefile.splitlines():
        match = re.match(rf"^{name}:(?!=)(.*)$", line)
        if match:
            found += match.group(1).split("##")[0].split()
    return found


def gate_rule(makefile: str) -> str:
    """The main rule of the gate target as written: its first line and the recipe lines under it."""
    lines = makefile.splitlines(keepends=True)
    head = f"{gate_target_name(makefile)}:"
    start = next(i for i, line in enumerate(lines) if line.startswith(head) and "check-openapi" not in line)
    end = start + 1
    while end < len(lines) and lines[end].startswith("\t"):
        end += 1
    return "".join(lines[start:end])
