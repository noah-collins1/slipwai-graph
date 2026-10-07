"""The pin: what `make test` and `make verify` do today, through the real root `Makefile` (S38 T001).

Green before the selector exists and green after the patch: on every branch but a slice branch `make test` runs what
it ran before, and `make verify` is whole and stamped.
"""
from __future__ import annotations

import sys
import unittest

from select_fixture import BYPASS, SelectCase, bypass_list

from slipwai.assets import ROOT

sys.dont_write_bytecode = True

ALL = ["test_a", "test_b", "test_c"]


class TestMakeTestToday(SelectCase):
    def test_tests_runs_exactly_those_modules_with_src_and_tests_on_the_path(self) -> None:
        self.branch("topic")
        done = self.make("test", "TESTS=test_a test_c")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        lines = self.ran()
        self.assertEqual(sorted(line.split("\t")[1] for line in lines), ["test_a", "test_c"])
        self.assertEqual({line.split("\t")[2] for line in lines}, {"PYTHONPATH=src:tests"})

    def test_skip_runs_every_other_module(self) -> None:
        self.branch("topic")
        done = self.make("test", "SKIP=test_b")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertEqual(self.modules_run(), ["test_a", "test_c"])

    def test_trunk_and_adopt_method_run_every_module_through_discover(self) -> None:
        for name in ("main", "adopt-method"):
            with self.subTest(branch=name):
                self.branch(name)
                done = self.make("test")
                self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
                lines = self.ran()
                self.assertEqual(sorted(line.split("\t")[1] for line in lines), ALL)
                # `discover -s tests` is run with `PYTHONPATH=src`; the module list form adds `tests`
                self.assertEqual({line.split("\t")[2] for line in lines}, {"PYTHONPATH=src"})

class TestMakeVerifyToday(SelectCase):
    def test_verify_runs_every_check_and_every_module_and_records_the_stamp(self) -> None:
        self.branch("topic")
        done = self.make("verify")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        lines = self.ran()
        self.assertEqual([line for line in lines if not line.startswith("module\t")],
                         ["verify --lint-only", "verify --typecheck-only", "check-structure"])
        self.assertEqual(sorted(line.split("\t")[1] for line in lines if line.startswith("module\t")), ALL)
        recorded = list((self.repo / ".git" / "slipwai").glob("*.json"))
        self.assertTrue(recorded, "a full verify on a branch records a stamp (a `.pending` file is not one)")

    def test_a_second_verify_on_the_unchanged_tree_runs_nothing(self) -> None:
        self.branch("topic")
        self.assertEqual(self.make("verify").returncode, 0)
        self.ran()
        self.assertEqual(self.make("verify").returncode, 0)
        self.assertEqual(self.ran(), [])


class TestStampBypassList(unittest.TestCase):
    def test_the_variables_that_narrow_a_run_and_so_bypass_the_stamp_are_the_recorded_ones(self) -> None:
        # T017 compares the patched Makefile's list with this one: a narrowing variable never reads or writes a stamp.
        self.assertEqual(bypass_list(ROOT / "Makefile"), BYPASS)


if __name__ == "__main__":
    unittest.main()
