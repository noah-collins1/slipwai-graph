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

from select_tests import full_rows  # noqa: E402
from select_tests.report import Full  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FULL_COMMAND = ("python3", "-m", "unittest", "discover", "-s", "tests", "-v")


def run_full() -> int:
    """Today's full command. No timeout: the suite takes as long as it takes, and the person running it can stop it."""
    env = dict(os.environ, PYTHONPATH="src")
    return subprocess.Popen(FULL_COMMAND, cwd=ROOT, env=env).wait()


def main() -> int:
    refusal: Full | None = full_rows(os.environ, ROOT)
    if refusal is not None:
        print(refusal.line, flush=True)
    return run_full()


if __name__ == "__main__":
    sys.exit(main())
