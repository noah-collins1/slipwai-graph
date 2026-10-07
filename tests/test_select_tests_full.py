"""Only a slice branch selects (S38 R1, AC-S38-1, -7, -13): every other case runs every module and says which.

The selector is run as the patched `make test` runs it, inside a temporary repository holding stand-in modules; what
ran is read from their log, and the line is read from the output.
"""
from __future__ import annotations

import sys

from select_fixture import SelectCase, git

sys.dont_write_bytecode = True

ALL = ["test_a", "test_b", "test_c"]
# Research R-7: what makes git describe another tree than the one the tests read.
LOCATING = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
            "GIT_COMMON_DIR", "GIT_NAMESPACE", "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT")


class FullCase(SelectCase):
    def assertFull(self, line: str, **env: str) -> None:
        done = self.selector(**env)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertEqual(self.modules_run(), ALL)
        self.assertEqual(done.stdout.splitlines()[0], line, done.stdout)
        self.assertEqual(sum(1 for text in done.stdout.splitlines() if text.startswith(("full:", "selection off:"))), 1)


class TestOnlyASliceBranchSelects(FullCase):
    def test_a_branch_that_is_not_a_slice_runs_every_module_and_names_the_case(self) -> None:
        for name in ("main", "adopt-method", "feature/x"):
            with self.subTest(branch=name):
                self.branch(name)
                self.assertFull(f"full: not a slice branch (`{name}`)")

    def test_a_detached_head_runs_every_module(self) -> None:
        git(self.repo, "checkout", "-q", "--detach")
        self.assertFull("full: HEAD is not on a branch")

    def test_a_slice_branch_with_no_commits_is_named_and_not_called_detached(self) -> None:
        git(self.repo, "checkout", "-q", "--orphan", "slice/x")
        self.assertFull("full: `slice/x` has no commits of its own — there is nothing beyond the base to compare")

    def test_an_unborn_branch_that_is_not_a_slice_is_not_a_slice_branch(self) -> None:
        git(self.repo, "checkout", "-q", "--orphan", "feature/x")
        self.assertFull("full: not a slice branch (`feature/x`)")

    def test_every_module_runs_through_discover_as_today(self) -> None:
        self.branch("feature/x")
        self.selector()
        self.assertEqual(self.pythonpaths(), {"PYTHONPATH=src"})

    def test_a_failing_module_fails_the_run(self) -> None:
        self.branch("feature/x")
        self.write("tests/test_b.py", "import unittest\n\n\nclass Case(unittest.TestCase):\n"
                   "    def test_it(self):\n        self.fail('b')\n")
        self.assertNotEqual(self.selector().returncode, 0)


class TestEveryEnvironmentThatMakesARunWhole(FullCase):
    def test_a_ci_marker_wins_on_a_slice_branch_with_or_without_since(self) -> None:
        self.branch("slice/x")
        for name in ("CI", "GITHUB_ACTIONS", "GITLAB_CI"):
            for extra in ({}, {"SINCE": "main"}):
                with self.subTest(marker=name, extra=extra):
                    self.assertFull(f"full: {name} is set — a CI run is the full gate", **{name: "1"}, **extra)

    def test_ratchet_tighten_runs_every_module(self) -> None:
        self.branch("slice/x")
        self.assertFull("full: RATCHET_TIGHTEN is set — a tightened baseline must not lose the findings of modules "
                        "that did not run", RATCHET_TIGHTEN="1")

    def test_full_runs_every_module(self) -> None:
        self.branch("slice/x")
        self.assertFull("full: FULL=1 given", FULL="1")

    def test_factory_backends_turns_selection_off_and_runs_as_asked(self) -> None:
        self.branch("slice/x")
        self.assertFull("selection off: FACTORY_BACKENDS given", FACTORY_BACKENDS="go")

    def test_a_factory_backends_value_reaches_the_modules(self) -> None:
        self.branch("slice/x")
        self.selector(FACTORY_BACKENDS="go")
        self.assertEqual({line.split("\t")[3] for line in self.ran() if line.startswith("module\t")},
                         {"FACTORY_BACKENDS=go"})

    def test_a_repository_locating_variable_runs_every_module_and_is_named(self) -> None:
        self.branch("slice/x")
        for name in LOCATING:
            with self.subTest(variable=name):
                self.assertFull(f"full: {name} is set — the change set would describe another tree", **{name: "x"})

    def test_the_rows_are_checked_in_order(self) -> None:
        self.branch("slice/x")
        self.assertFull("selection off: FACTORY_BACKENDS given", FACTORY_BACKENDS="go", FULL="1", CI="1",
                        RATCHET_TIGHTEN="1", GIT_DIR="x")
        self.assertFull("full: FULL=1 given", FULL="1", CI="1", RATCHET_TIGHTEN="1", GIT_DIR="x")
        self.assertFull("full: CI is set — a CI run is the full gate", CI="1", RATCHET_TIGHTEN="1", GIT_DIR="x")
        self.assertFull("full: RATCHET_TIGHTEN is set — a tightened baseline must not lose the findings of modules "
                        "that did not run", RATCHET_TIGHTEN="1", GIT_DIR="x")
