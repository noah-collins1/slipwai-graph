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
import re
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
SELECTED = "SELECTED_TEST_MODULES"  # the modules a selected run starts, comma-separated: the audit narrows to them
KNOBS = ("SINCE", "FULL")  # what picks the selection: the tests it starts never read it (a project they build would)


# make writes a command-line assignment into `MAKEFLAGS` as it was given, a space in its value as `\ `, so a word is
# a run of non-space characters and backslash-escaped ones; the assignment forms are make's own (`=`, `:=`, `::=`,
# `:::=`, `+=`, `?=`, `!=`).
FLAG_WORD = re.compile(r"(?:\\.|\S)+")
KNOB_ASSIGNMENT = re.compile(r"(?:" + "|".join(KNOBS) + r")(?::{1,3}=|[+?!]?=)")


def without_knobs(env: dict[str, str]) -> None:
    """Drop `SINCE` and `FULL` from `env` and from make's own copy: `MAKEFLAGS` and `MFLAGS` carry a command-line
    `SINCE=<ref>` to every make a test starts, where a generated project's `make mutation` would read it as its own.
    Every assignment form goes, whole, and no other word is split (T051). `tests/support.py` does the same for the
    tests that start a generated project's commands, where the `Makefile` bypasses this selector."""
    for knob in KNOBS:
        env.pop(knob, None)
    for flags in ("MAKEFLAGS", "MFLAGS"):
        if flags in env:
            words = [word for word in FLAG_WORD.findall(env[flags]) if not KNOB_ASSIGNMENT.match(word)]
            if "--" in words and words[-1] == "--":
                words.pop()
            if words:
                env[flags] = " ".join(words)
            else:
                del env[flags]


FAILING = re.compile(r"^(?:FAIL|ERROR): (\S+) \((\S+?)\)")


def failed_module(line: str) -> str | None:
    """The module a unittest report line (`FAIL: test_it (module.Class.test_it)`) blames; a module that did not import
    is `ERROR: module (unittest.loader._FailedTest.module)`, named by its first word."""
    found = FAILING.match(line)
    if found is None:
        return None
    return found.group(1) if found.group(2).startswith("unittest.loader.") else found.group(2).split(".")[0]


def run_unittest(arguments: tuple[str, ...], pythonpath: str, backends: str | None = None, *,
                 keep: bool = False, selected: list[str] | None = None) -> tuple[int, list[str]]:
    """`PYTHONPATH=<pythonpath> python3 -m unittest <arguments>`, with `FACTORY_BACKENDS` set to `backends` or unset
    (kept as it is where `keep`: the person gave it). Returns its status and the modules that failed, each once, in
    the order reported (`SELECTED_TEST_MODULES` is `selected` joined, and is removed wherever nothing was selected:
    a value from outside must not narrow a full run's audit); its report is passed on as it is written. No timeout:
    the suite takes as long as it takes, and the person running it can stop it."""
    env = dict(os.environ, PYTHONPATH=pythonpath)
    if backends is not None:
        env[BACKENDS] = backends
    elif not keep:
        env.pop(BACKENDS, None)
    env.pop(SELECTED, None)
    if selected is not None:
        env[SELECTED] = ",".join(selected)
    without_knobs(env)
    failed: list[str] = []
    with subprocess.Popen((*UNITTEST, *arguments), cwd=ROOT, env=env, stderr=subprocess.PIPE, text=True,
                          errors="replace") as process:
        assert process.stderr is not None
        for line in process.stderr:
            sys.stderr.write(line)
            sys.stderr.flush()
            module = failed_module(line)
            if module is not None and module not in failed:
                failed.append(module)
        return process.wait(), failed


def run_full() -> int:
    """Today's full command: `PYTHONPATH=src python3 -m unittest discover -s tests -v`."""
    return run_unittest(FULL_ARGUMENTS, "src", keep=True)[0]


def run_modules(modules: list[str], backends: str | None = None,
                selected: list[str] | None = None) -> tuple[int, list[str]]:
    """`PYTHONPATH=src:tests python3 -m unittest -v <modules>`, which CI already trusts."""
    if not modules:
        return 0, []  # `unittest` with no names would discover from here: nothing selected is nothing run
    return run_unittest(("-v", *modules), "src:tests", backends, selected=selected)


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
    status, failed = run_modules([module for module in running if module not in narrowed], selected=running)
    narrowed_status, narrowed_failed = run_modules(narrowed, ",".join(selection.backends), running)  # both run
    print(summary, flush=True)
    if running:
        print(report.result_line(len(running), sorted({*failed, *narrowed_failed}), status or narrowed_status),
              flush=True)
    return status or narrowed_status  # either batch failing fails the run


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
