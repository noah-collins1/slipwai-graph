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

from select_tests import base, full_rows, rules  # noqa: E402
from select_tests.report import Full, full_line, printable  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FULL_COMMAND = ("python3", "-m", "unittest", "discover", "-s", "tests", "-v")


def run_full() -> int:
    """Today's full command. No timeout: the suite takes as long as it takes, and the person running it can stop it."""
    env = dict(os.environ, PYTHONPATH="src")
    return subprocess.Popen(FULL_COMMAND, cwd=ROOT, env=env).wait()


def measure() -> Full | None:
    """The base, what changed since, and whether it can be told what that reaches; the line of the base is printed."""
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
            return Full(full_line(f"{base.changed_words(ROOT, found, path)} — {why}"))
    for path in base.ignored_files(ROOT):
        return Full(full_line(f"`{printable(path)}` is a file git ignores — what it changes cannot be established"))
    print(found.line, flush=True)
    return None


def main() -> int:
    refusal: Full | None = full_rows(os.environ, ROOT)
    if refusal is None:
        try:
            refusal = measure()
        except Full as full:
            refusal = full
    if refusal is not None:
        print(refusal.line, flush=True)
    return run_full()


if __name__ == "__main__":
    sys.exit(main())
