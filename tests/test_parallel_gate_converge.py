"""Converge pass 1 of S04 (T014 to T017): the findings that held in the first run, each read over its whole class.

The Makefiles are built in-process from `project_files`, never run: every example reads what the generator wrote.
"""
from __future__ import annotations

import re
import sys
import unittest

from parallel_gate import ParallelGateTestCase, sync_lines, synced_projects
from test_parallel_gate_sync_ways import apps_of
from test_verify_stamp_scan import makefile_rules

from slipwai.assets import ROOT
from slipwai.catalog import axis_default
from slipwai.scaffold import project_files
from slipwai.selection import resolve_selection
from slipwai.services import App, add_service

sys.dont_write_bytecode = True

# A call of the Python family's script with a mode, whichever way the project spells the script's path.
PYTHON_CALL = re.compile(r"\./scripts/verify(?:-python)? --(?!install-only\b)[a-z]+(?:-[a-z]+)*")
NON_SYNCING = re.compile(r"--synced|--no-sync")


def shapes() -> dict[str, list[App]]:
    """One project of each shape the rule must hold in: one Python service, two, Python beside another family."""
    answers = resolve_selection({"http": axis_default("http", "python", "none")}, "event-modelling", "python", "none")
    return {
        "python": apps_of("python", "none", False, 1),
        "python-api-web": apps_of("python", axis_default("http", "python", "none"), True, 1),
        "two-python": apps_of("python", "none", False, 2),
        "python-go": add_service(apps_of("python", "none", False, 1), "more", "go", answers),
        "python-java": add_service(apps_of("python", "none", True, 1), "more", "java-quarkus", answers),
    }


class EveryPythonModeNamesSyncTest(unittest.TestCase):
    def test_t014_each_target_that_names_sync_passes_synced_and_only_those_do(self) -> None:
        """Both directions over every shape: a target naming `sync` has `--synced` on each call of the script, and a
        recipe line saying `--synced` or `--no-sync` belongs to a target that names it."""
        for name, apps in shapes().items():
            with self.subTest(shape=name):
                rules = makefile_rules(project_files("sweep", "event-modelling", "none", apps)["Makefile"])
                self.assertIn("format", rules)
                for target, (needs, recipe) in rules.items():
                    if target == "sync":
                        continue
                    for line in recipe:
                        if "sync" in needs:
                            for call in PYTHON_CALL.finditer(line):
                                self.assertIn("--synced", re.split(r"&&|;", line[call.start():])[0], (target, line))
                        elif NON_SYNCING.search(line):
                            self.fail(f"{target} does not name sync but runs {line!r}")


FRAGMENT = (ROOT / "changelog.d/parallel-gate.md").read_text(encoding="utf-8")


class OrderSentencesAreTrueOfAParallelRunTest(unittest.TestCase):
    def test_t015_a_failed_sync_is_said_for_what_it_stops_not_for_the_whole_run(self) -> None:
        """AC-S04-38 holds no run line after a failed sync; under `-j` the checks that do not run a Python service's
        code have started, so the words claim only the first."""
        text = " ".join(FRAGMENT.split())
        self.assertNotIn("stops the run before any check starts", text)
        self.assertIn("A failed sync starts no check that runs a Python service's code, and says so once.", text)


class FormatSyncsOnceTest(ParallelGateTestCase):
    SHAPE = "plain"

    def test_t014_format_alone_and_beside_lint_syncs_once(self) -> None:
        """`make format` and `make -j format lint` leave one sync line for the one service."""
        for goals in (("format",), ("-j", "format", "lint")):
            with self.subTest(goals=goals):
                self.forget_log()
                self.assert_passed(self.make(*goals))
                self.assertEqual(synced_projects(self.log), ["apps/service"], sync_lines(self.log))


if __name__ == "__main__":
    unittest.main()
