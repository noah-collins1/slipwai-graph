#!/usr/bin/env python3
"""Run the factory's tests: the modules a change on a slice branch can reach, or every module wherever it cannot be
established what a change reaches (the root `Makefile`'s `test` recipe calls this unless `TESTS` or `SKIP` names the
modules).

The full run is exactly today's `PYTHONPATH=src python3 -m unittest discover -s tests -v`; a selected run is
`PYTHONPATH=src:tests python3 -m unittest -v <modules>`. Every doubt means every module, and one line says why.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # before the package loads: nothing may be written beside the selector or under assets/

from select_tests import base, choose, declarations, full_rows, report, rules  # noqa: E402
from select_tests.report import Full, full_line, printable  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
UNITTEST = ("python3", "-m", "unittest")
FULL_ARGUMENTS = ("discover", "-s", "tests", "-v")
BACKENDS = "FACTORY_BACKENDS"


def run_unittest(arguments: tuple[str, ...], pythonpath: str, backends: str | None = None, *,
                 keep: bool = False) -> int:
    """`PYTHONPATH=<pythonpath> python3 -m unittest <arguments>`, with `FACTORY_BACKENDS` set to `backends` or unset
    (kept as it is where `keep`: the person gave it). No timeout: the suite takes as long as it takes, and the person
    running it can stop it."""
    env = dict(os.environ, PYTHONPATH=pythonpath)
    if backends is not None:
        env[BACKENDS] = backends
    elif not keep:
        env.pop(BACKENDS, None)
    return subprocess.Popen((*UNITTEST, *arguments), cwd=ROOT, env=env).wait()


def run_full() -> int:
    """Today's full command: `PYTHONPATH=src python3 -m unittest discover -s tests -v`."""
    return run_unittest(FULL_ARGUMENTS, "src", keep=True)


def run_modules(modules: list[str], backends: str | None = None) -> int:
    """`PYTHONPATH=src:tests python3 -m unittest -v <modules>`, which CI already trusts."""
    if not modules:
        return 0  # `unittest` with no names would discover from here: nothing selected is nothing run
    return run_unittest(("-v", *modules), "src:tests", backends)


def plan(replay: str | None = None) -> tuple[base.ChangeSet, choose.Selection]:
    """The base, what changed since, and which modules that reaches. Raises the line wherever the run is whole. A
    replay takes its change set from a range of commits, which leaves the working tree out of it."""
    found = base.replay_changes(ROOT, replay) if replay else base.change_set(ROOT, base.establish(ROOT, os.environ))
    try:
        return found, select(found, replay is not None)
    except Full as full:
        if replay:
            full.against = found.against  # a full replay says what it was measured against (AC-S38-15)
        raise


def select(found: base.ChangeSet, replay: bool) -> choose.Selection:
    """The modules the change set reaches, over the tree as it is; raises the line wherever the run is whole."""
    try:
        catalog = rules.load_catalog(ROOT)
    except Full:
        if "catalog.json" not in found.paths:
            raise
        catalog = {}  # a catalog that was changed and no longer reads is itself the first full row's path
    for path in found.paths:  # the first that broadens, in the order the change set is sorted
        why = rules.broadening(path, catalog, ROOT)
        if why is not None:
            raise Full(full_line(f"{base.changed_words(ROOT, found, path)} — {why}"))
    if not replay:  # git cannot say what a range of commits did to a file it ignores: the working tree is not in it
        for path in base.ignored_files(ROOT):
            raise Full(full_line(f"`{printable(path)}` is a file git ignores — what it changes cannot be established"))
    try:
        tree = declarations.scan(ROOT, catalog)
    except (OSError, ValueError, RecursionError) as error:
        raise base.cannot_be_established(f"the test tree could not be read: {error}") from error
    try:
        hidden = declarations.nameless(ROOT)
    except (OSError, ValueError, RecursionError) as error:
        raise base.cannot_be_established(f"the test tree could not be read: {error}") from error
    for path in hidden[:1]:  # `discover` imports it and the scan cannot name it: only the full run is the same answer
        raise Full(full_line(f"`{printable(path)}` is {rules.NAMELESS} — {rules.BROADENS}"))
    caches = [] if replay else base.cache_files(ROOT)  # they reach what reads their directory, and nothing else
    return choose.select(tree, found.paths, catalog, caches)


def arguments(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="select-tests.py", description=__doc__.split("\n\n")[0] if __doc__ else None)
    parser.add_argument("--dry-run", action="store_true", help="print what would run and why, and run nothing")
    parser.add_argument("--replay", metavar="BASE..TIP", help="with --dry-run: the change set of that range of commits")
    given = parser.parse_args(argv)
    if given.replay and not given.dry_run:
        parser.error("--replay only describes a selection: it needs --dry-run")
    return given


def main(argv: list[str]) -> int:
    given = arguments(argv)
    try:
        refusal = full_rows(os.environ, ROOT, branch=not given.replay)
        if refusal is not None:
            raise refusal
        found, selection = plan(given.replay)
    except Full as full:
        print(full.line, flush=True)
        if full.against:  # a replay that runs everything: all of them, against the base it was compared with
            total = len([path for path in (ROOT / "tests").glob("test*.py") if path.is_file()])
            print(report.summary_line(total, total, full.against), flush=True)
        return 0 if given.dry_run else run_full()
    print(found.line, flush=True)
    for verdict in selection.verdicts:
        if not verdict.runs:
            print(report.skipped_line(verdict.module, verdict.skip), flush=True)
    narrowed = [verdict.module for verdict in selection.narrowed()]
    for module in narrowed:
        print(report.narrowed_line(module, selection.backends, selection.left_out), flush=True)
    running = [verdict.module for verdict in selection.verdicts if verdict.runs]
    summary = report.summary_line(len(running), len(selection.verdicts), found.against)
    print(summary, flush=True)
    if given.dry_run:
        return 0
    status = run_modules([module for module in running if module not in narrowed])
    narrowed_status = run_modules(narrowed, ",".join(selection.backends))  # both run; either failing fails the run
    print(summary, flush=True)
    return status or narrowed_status


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
