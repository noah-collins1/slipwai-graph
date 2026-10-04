"""T022 of S05-xdist (D106): a CI run and the adversarial run are serial, whatever the mark says.

Built on the gate's stand-in harness in `test_xdist_gate`; the evidence is the stand-in's log of the `pytest` lines.
"""
from __future__ import annotations

import subprocess
import sys
import unittest
from collections.abc import Mapping

from parallel_gate import CI_MARKERS, gate_environment, run_lines
from test_xdist_gate import FLAGS, MarkReachesPytest

from slipwai.project.parallel_tests import MARK

sys.dont_write_bytecode = True


class CiAndAdversarialAreSerial(MarkReachesPytest):
    def lines(self, mode: str, env: Mapping[str, str | None] | None = None) -> list[str]:
        """The gate's pytest lines for `mode` ('all' is the bare gate), with `env` added to the gate environment."""
        self.log.write_text("", encoding="utf-8")
        run = subprocess.run(["./scripts/verify", *([] if mode == "all" else [mode])], cwd=self.repo,
                             env=gate_environment(self.bin, self.log, dict(env or {})), text=True, capture_output=True,
                             timeout=120)
        self.assertEqual(run.returncode, 0, run.stderr)
        found = [line for line in run_lines(self.log) if " pytest " in f" {line} "]
        self.assertTrue(found, f"no pytest ran in {mode}")
        return found

    def test_any_ci_marker_alone_makes_test_only_and_all_serial_even_set_to_false(self) -> None:
        self.project()
        self.mark(True)
        for marker in CI_MARKERS:
            for value in ("true", "false"):
                for mode in ("--test-only", "all"):
                    with self.subTest(marker=marker, value=value, mode=mode):
                        self.assertNotIn("-n ", " ".join(self.lines(mode, {marker: value})))

    def test_with_no_marker_set_the_flags_are_there(self) -> None:
        self.project()
        self.mark(True)
        for mode in ("--test-only", "all"):
            with self.subTest(mode=mode):
                for line in self.lines(mode):
                    self.assertIn(f"pytest {FLAGS} ", line)

    def test_an_empty_ci_marker_is_not_a_ci_run(self) -> None:
        self.project()
        self.mark(True)
        self.assertIn(FLAGS, " ".join(self.lines("--test-only", {"CI": ""})))

    def test_the_adversarial_run_is_serial_whatever_the_environment(self) -> None:
        self.project()
        self.mark(True)
        for env in ({}, {"CI": "true"}, {"GITHUB_ACTIONS": "false"}):
            with self.subTest(env=env):
                lines = self.lines("--adversarial-only", env)
                self.assertNotIn("-n ", " ".join(lines))
                self.assertIn("-k adversarial", lines[0])

    def test_the_marks_paragraph_says_a_parallel_run_can_hide_a_leak_and_ci_runs_serially(self) -> None:
        text = " ".join(MARK.split())
        self.assertIn("depends on another test's leftovers", text)
        self.assertIn("different workers", text)
        self.assertIn("CI runs the suite serially", text)
        self.assertIn("passes locally but fails in CI", text)
        self.assertNotIn("and the adversarial run", text)


def load_tests(loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str | None) -> unittest.TestSuite:
    """Only this module's own tests: the base class's are `test_xdist_gate`'s and run there."""
    suite = unittest.TestSuite()
    for name in ("test_any_ci_marker_alone_makes_test_only_and_all_serial_even_set_to_false",
                 "test_with_no_marker_set_the_flags_are_there", "test_an_empty_ci_marker_is_not_a_ci_run",
                 "test_the_adversarial_run_is_serial_whatever_the_environment",
                 "test_the_marks_paragraph_says_a_parallel_run_can_hide_a_leak_and_ci_runs_serially"):
        suite.addTest(CiAndAdversarialAreSerial(name))
    return suite
