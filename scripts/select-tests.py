#!/usr/bin/env python3
"""Run the factory's tests: the modules a change on a slice branch can reach, or every module wherever it cannot be
established what a change reaches (the root `Makefile`'s `test` recipe calls this unless `TESTS` or `SKIP` names the
modules).

The full run is exactly today's `PYTHONPATH=src python3 -m unittest discover -s tests -v`; a selected run is
`PYTHONPATH=src:tests python3 -m unittest -v <modules>`. Every doubt means every module, and one line says why.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # before the package loads: nothing may be written beside the selector or under assets/

from select_tests import base, choose, declarations, full_rows, report, rules  # noqa: E402
from select_tests.report import Full, full_line, printable  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FULL_COMMAND = ("python3", "-m", "unittest", "discover", "-s", "tests", "-v")
NAMED_COMMAND = ("python3", "-m", "unittest", "-v")


def run_full() -> int:
    """Today's full command. No timeout: the suite takes as long as it takes, and the person running it can stop it."""
    env = dict(os.environ, PYTHONPATH="src")
    return subprocess.Popen(FULL_COMMAND, cwd=ROOT, env=env).wait()


def run_modules(modules: list[str]) -> int:
    """`PYTHONPATH=src:tests python3 -m unittest -v <modules>`, which CI already trusts."""
    if not modules:
        return 0  # `unittest` with no names would discover from here: nothing selected is nothing run
    env = dict(os.environ, PYTHONPATH="src:tests")
    return subprocess.Popen((*NAMED_COMMAND, *modules), cwd=ROOT, env=env).wait()


def plan() -> tuple[base.ChangeSet, list[choose.Verdict]]:
    """The base, what changed since, and which modules that reaches. Raises the line wherever the run is whole."""
    found = base.change_set(ROOT, base.establish(ROOT, os.environ))
    try:
        catalog = rules.load_catalog(ROOT)
    except Full:
        if "catalog.json" not in found.paths:
            raise
        catalog = {}  # a catalog that was changed and no longer reads is itself the first full row's path
    for path in found.paths:  # the first that broadens, in the order the change set is sorted
        why = rules.broadening(path, catalog)
        if why is not None:
            raise Full(full_line(f"{base.changed_words(ROOT, found, path)} — {why}"))
    for path in base.ignored_files(ROOT):
        raise Full(full_line(f"`{printable(path)}` is a file git ignores — what it changes cannot be established"))
    try:
        tree = declarations.scan(ROOT, catalog)
    except (OSError, ValueError, RecursionError) as error:
        raise base.cannot_be_established(f"the test tree could not be read: {error}") from error
    return found, choose.choose(tree, found.paths, catalog)


def main() -> int:
    try:
        refusal = full_rows(os.environ, ROOT)
        if refusal is not None:
            raise refusal
        found, verdicts = plan()
    except Full as full:
        print(full.line, flush=True)
        return run_full()
    print(found.line, flush=True)
    for verdict in verdicts:
        if not verdict.runs:
            print(report.skipped_line(verdict.module, verdict.skip), flush=True)
    return run_modules([verdict.module for verdict in verdicts if verdict.runs])


if __name__ == "__main__":
    sys.exit(main())
