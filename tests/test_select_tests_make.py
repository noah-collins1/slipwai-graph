"""The patched root `Makefile`, driven as a person drives it (S38 R9, AC-S38-6, -13, -14).

The real `Makefile` is copied into the fixture repository with declared stand-in modules. On a slice branch with one go
path changed `make test` selects and `make verify` does not; a given `TESTS` or `SKIP` turns selection off and says so;
a change to the `Makefile` itself runs every module. What ran is read from the stand-ins' log. On the unpatched tree
each
test fails with the line that names the patch.
"""
from __future__ import annotations

import shutil
import sys
import unittest

from select_fixture_declare import GO, DeclarationCase
from test_select_tests_makefile import MAKEFILE, UNPATCHED

sys.dont_write_bytecode = True

PYTHON = '{"configurations": {"backend": ["python"]}}'
GO_DECLARED = '{"configurations": {"backend": ["go"]}}'
EVERY = ["test_a", "test_b", "test_c"]
CHECKS = ["verify --lint-only", "verify --typecheck-only", "check-structure"]


class MakeCase(DeclarationCase):
    """A slice branch cut from the trunk with one go path changed: `test_b` reads python, so a selection skips it."""

    def setUp(self) -> None:
        super().setUp()
        if "select-tests.py" not in MAKEFILE.read_text(encoding="utf-8"):
            self.fail(UNPATCHED)
        self.declare(test_a=GO_DECLARED, test_b=PYTHON, test_c="")
        self.slice_changing(GO)

    def stamps(self) -> dict[str, tuple[bytes, int]]:
        directory = self.repo / ".git" / "slipwai"
        files = directory.glob("*") if directory.is_dir() else ()
        return {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in files}

    def ok(self, *args: str, **env: str) -> str:
        done = self.make(*args, **env)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        return done.stdout


class TestMakeTestSelectsOnASliceBranch(MakeCase):
    def test_it_runs_the_modules_the_change_reaches_through_the_selector(self) -> None:
        self.ok("test")
        self.assertEqual(self.modules_run(), ["test_a", "test_c"])

    def test_full_runs_every_module(self) -> None:
        self.ok("test", "FULL=1")
        self.assertEqual(self.modules_run(), EVERY)

    def test_a_change_to_the_root_makefile_runs_every_module(self) -> None:  # AC-S38-14
        with (self.repo / "Makefile").open("a", encoding="utf-8") as handle:
            handle.write("# edited\n")
        self.ok("test")
        self.assertEqual(self.modules_run(), EVERY)


class TestAGivenTestsOrSkipTurnsSelectionOff(MakeCase):
    def test_skip_runs_every_module_but_it_and_says_so(self) -> None:  # e4
        out = self.ok("test", "SKIP=test_b")
        self.assertIn("selection off: SKIP given", out)
        self.assertNotIn("selection off: TESTS given", out)
        lines = self.ran()
        self.assertEqual(sorted(line.split("\t")[1] for line in lines), ["test_a", "test_c"])
        self.assertEqual({line.split("\t")[2] for line in lines}, {"PYTHONPATH=src:tests"})

    def test_skip_of_a_module_the_selection_would_run_still_runs_the_rest(self) -> None:
        out = self.ok("test", "SKIP=test_a")
        self.assertIn("selection off: SKIP given", out)
        self.assertEqual(self.modules_run(), ["test_b", "test_c"])

    def test_tests_runs_exactly_those_modules_and_says_so(self) -> None:  # e4
        out = self.ok("test", "TESTS=test_b test_c")
        self.assertIn("selection off: TESTS given", out)
        self.assertNotIn("selection off: SKIP given", out)
        lines = self.ran()
        self.assertEqual(sorted(line.split("\t")[1] for line in lines), ["test_b", "test_c"])
        self.assertEqual({line.split("\t")[2] for line in lines}, {"PYTHONPATH=src:tests"})


class TestAnEmptyTestsIsNotGiven(MakeCase):
    def test_skip_beside_an_empty_tests_runs_every_other_module_and_says_skip(self) -> None:  # T034, R-9
        for how, args, env in (("on the command line", ("TESTS=", "SKIP=test_b"), {}),
                               ("exported empty", ("SKIP=test_b",), {"TESTS": ""})):
            with self.subTest(how):
                out = self.ok("test", *args, **env)
                self.assertIn("selection off: SKIP given", out)
                self.assertNotIn("selection off: TESTS given", out)
                self.assertNotIn("no module runs", out)
                self.assertEqual(self.modules_run(), ["test_a", "test_c"])

    def test_an_empty_tests_alone_is_unset_and_the_selector_runs(self) -> None:  # T034, R-9
        out = self.ok("test", "TESTS=")
        self.assertNotIn("selection off", out)
        self.assertEqual(self.modules_run(), ["test_a", "test_c"])

    def test_the_gate_with_an_empty_tests_and_skip_runs_the_rest(self) -> None:  # T034
        self.ok("verify-checks", "TESTS=", "SKIP=test_b")
        self.assertEqual(self.modules_run(), ["test_a", "test_c"])


class TestSkipNamingEveryModuleStillTurnsSelectionOff(MakeCase):
    def test_it_says_so_runs_no_module_and_never_calls_the_selector(self) -> None:  # AC-S38-13, R-9
        out = self.ok("test", "SKIP=" + " ".join(EVERY))
        self.assertIn("selection off: SKIP given - no module runs", out)
        self.assertNotIn("selected", out)
        self.assertEqual(self.ran(), [])


class TestVerifyChecksRunDirectlyIsWhole(MakeCase):
    def test_every_module_runs_whatever_full_holds_wherever_it_is_set(self) -> None:  # AC-S38-6
        cases = {
            "plain": ((), {}),
            "FULL= on the command line": (("FULL=",), {}),
            "FULL=0 on the command line": (("FULL=0",), {}),
            "FULL=0 in the environment": ((), {"FULL": "0"}),
            "FULL= in the environment under make -e": (("-e",), {"FULL": ""}),
            "FULL=0 in the environment under make -e": (("-e",), {"FULL": "0"}),
            "FULL= in MAKEFLAGS": ((), {"MAKEFLAGS": "FULL="}),
        }
        for how, (args, env) in cases.items():
            with self.subTest(how):
                self.ok("verify-checks", *args, **env)
                self.assertEqual(self.modules_run(), EVERY)
                self.ran()


class TestVerifyChecksIsWholeWhateverTheOrderOfTheGoals(MakeCase):
    def test_all_gates_passed_is_said_only_after_every_module_ran(self) -> None:  # T035, AC-S38-6
        for goals in (["test", "verify-checks"], ["verify-checks", "test"], ["lint", "verify-checks"],
                      ["verify-checks"]):
            with self.subTest(" ".join(goals)):
                out = self.ok(*goals)
                self.assertIn("verify: all gates passed", out)
                self.assertIn("test_b", self.modules_run())


class TestMakeVerifyIsWhole(MakeCase):
    def test_every_check_and_every_module_run_and_the_stamp_is_recorded(self) -> None:  # e2
        self.ok("verify")
        lines = self.ran()
        self.assertEqual([line for line in lines if not line.startswith("module\t")], CHECKS)
        self.assertEqual(sorted(line.split("\t")[1] for line in lines if line.startswith("module\t")), EVERY)
        self.assertTrue(list((self.repo / ".git" / "slipwai").glob("*.json")), "no stamp was recorded")

    def test_since_does_not_narrow_it(self) -> None:  # e2
        for since in ("main", "HEAD~0"):
            with self.subTest(since=since, how="in the environment"):
                shutil.rmtree(self.repo / ".git" / "slipwai", ignore_errors=True)
                self.ok("verify", SINCE=since)
                self.assertEqual(self.modules_run(), EVERY)
                self.assertTrue(list((self.repo / ".git" / "slipwai").glob("*.json")))
            with self.subTest(since=since, how="on the command line"):  # the stamp records no pass made that way
                shutil.rmtree(self.repo / ".git" / "slipwai", ignore_errors=True)
                self.ok("verify", f"SINCE={since}")
                self.assertEqual(self.modules_run(), EVERY)

    def test_the_second_run_on_the_unchanged_tree_runs_nothing(self) -> None:
        self.ok("verify")
        self.ran()
        self.assertIn("already passed it at", self.ok("verify"))
        self.assertEqual(self.ran(), [])


class TestMakeVerifyOfASliceOfTheSuiteTouchesNoStamp(MakeCase):
    def test_tests_and_skip_leave_the_stamp_as_it_was(self) -> None:  # e3
        self.ok("verify")
        self.ran()
        before = self.stamps()
        self.assertTrue(before)
        for argument in ("TESTS=test_b", "SKIP=test_a"):
            with self.subTest(argument):
                self.ok("verify", argument)
                self.assertEqual(self.stamps(), before)
                self.assertEqual([line for line in self.ran() if not line.startswith("module\t")], CHECKS)

    def test_and_none_is_written_where_there_was_none(self) -> None:  # e3
        for argument in ("TESTS=test_b", "SKIP=test_a", "FACTORY_BACKENDS=go"):
            with self.subTest(argument):
                self.ok("verify", argument)
                self.assertEqual(self.stamps(), {})
                self.ran()


if __name__ == "__main__":
    unittest.main()
