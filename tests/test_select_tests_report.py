"""Every skip is named, and a dry run shows it (S38 R8 first half, AC-S38-12): the lines of a run in the order the data
model gives them, the summary before the tests start and again last, and `--dry-run` printing the same and running
nothing.
"""
from __future__ import annotations

import sys

from select_fixture import git
from select_fixture_declare import GO, DeclarationCase

sys.dont_write_bytecode = True

MATRIX = '{"configurations": {"backend": ["typescript", "python", "go", "java-quarkus", "java-spring"]}}'
LEFT_OUT = "(java-quarkus, java-spring, python, typescript unaffected)"


class ReportCase(DeclarationCase):
    def trunk_commit(self) -> str:
        return git(self.repo, "rev-parse", "--short", "main").strip()

    def selection(self) -> None:
        """Five modules: one narrowed, one undeclared, one run for its configuration, two skipped."""
        self.declare(test_a='{"configurations": {"backend": ["go"], "frontend": ["none"]}}',
                     test_b='{"configurations": {"backend": ["python"]}}',
                     test_c="", test_d='{"reads": ["README.md"]}', test_matrix=MATRIX)
        self.write("README.md", "read\n")
        self.slice_changing(GO)


class TestARunNamesWhatItLeftOut(ReportCase):
    def test_the_lines_come_in_the_order_the_data_model_gives_before_and_after_the_tests(self) -> None:
        self.selection()
        done = self.selector_merged()
        self.assertEqual(done.returncode, 0, done.stdout)
        lines = done.stdout.splitlines()
        base = f"compared with `main` at {self.trunk_commit()} (the trunk)"
        summary = f"selected 3 of 5 modules against `main` at {self.trunk_commit()}"
        self.assertEqual(lines[:6], [base, "skipped test_b: reads no go configuration",
                                     "skipped test_d: reads no go configuration",
                                     f"narrowed test_a: backend go only {LEFT_OUT}",
                                     f"narrowed test_matrix: backend go only {LEFT_OUT}", summary])
        self.assertEqual(lines[-1], summary)
        first_test = next(number for number, line in enumerate(lines) if "(test_" in line and "..." in line)
        self.assertGreater(first_test, 5, "the summary and every skip come before the first test")
        self.assertEqual(sum(1 for line in lines if line == summary), 2)

    def test_each_skipped_module_is_named_once_with_one_reason(self) -> None:
        self.selection()
        done = self.selector_merged()
        skipped = [line for line in done.stdout.splitlines() if line.startswith("skipped ")]
        self.assertEqual([line.split(":")[0] for line in skipped], ["skipped test_b", "skipped test_d"])
        self.assertEqual(len({line.split(":")[0] for line in skipped}), len(skipped))

    def test_the_summary_is_last_even_when_a_module_fails(self) -> None:
        self.declare(test_a='{"configurations": {"backend": ["go"]}}')
        self.write("tests/test_a.py", "TEST_SELECTION = {'configurations': {'backend': ['go']}}\nimport unittest\n\n\n"
                   "class Case(unittest.TestCase):\n    def test_it(self):\n        self.fail('no')\n")
        self.slice_changing(GO)
        done = self.selector_merged()
        self.assertNotEqual(done.returncode, 0)
        self.assertTrue(done.stdout.splitlines()[-1].startswith("selected 1 of 1 modules against `main` at "))

    def test_nothing_selected_runs_nothing_and_says_so(self) -> None:
        self.declare(test_a='{"configurations": {"backend": ["python"]}}')
        self.slice_changing(GO)
        done = self.selector_merged()
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertEqual(self.modules_run(), [])
        self.assertEqual(done.stdout.splitlines()[-1],
                         f"selected 0 of 1 modules against `main` at {self.trunk_commit()}")


class TestADryRun(ReportCase):
    def test_prints_the_same_lines_up_to_the_summary_and_runs_nothing(self) -> None:
        self.selection()
        done = self.selector_merged("--dry-run")
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertEqual(self.ran(), [])
        base = f"compared with `main` at {self.trunk_commit()} (the trunk)"
        self.assertEqual(done.stdout.splitlines(), [
            base, "skipped test_b: reads no go configuration", "skipped test_d: reads no go configuration",
            f"narrowed test_a: backend go only {LEFT_OUT}", f"narrowed test_matrix: backend go only {LEFT_OUT}",
            f"selected 3 of 5 modules against `main` at {self.trunk_commit()}"])

    def test_agrees_with_the_run_it_stands_for(self) -> None:
        self.selection()
        dry = self.selector_merged("--dry-run").stdout.splitlines()
        wet = self.selector_merged().stdout.splitlines()
        self.assertEqual(wet[:len(dry)], dry)

    def test_a_full_run_is_a_line_and_nothing_runs(self) -> None:
        self.selection()
        done = self.selector_merged("--dry-run", FULL="1")
        self.assertEqual(done.returncode, 0)
        self.assertEqual(done.stdout.splitlines(), ["full: FULL=1 given"])
        self.assertEqual(self.ran(), [])

    def test_a_dry_run_where_the_base_cannot_be_established_prints_the_full_line_and_runs_nothing(self) -> None:
        self.selection()
        done = self.selector_merged("--dry-run", SINCE="nonexistent")
        self.assertEqual(done.returncode, 0)
        self.assertEqual(done.stdout.splitlines(),
                         ["full: SINCE=nonexistent could not be resolved — it names no commit"])
        self.assertEqual(self.ran(), [])

    def test_an_argument_it_does_not_know_is_refused(self) -> None:
        self.selection()
        done = self.selector_merged("--dry-runn")
        self.assertEqual(done.returncode, 2)
        self.assertEqual(self.ran(), [])
