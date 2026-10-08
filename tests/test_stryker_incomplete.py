"""S41 T032 (D212, D217, AC-S41-4): a mutant under which the suite did not run to completion is never a survivor.

Stryker 10.0.0's Vitest runner marks a test skipped when a file-level `beforeAll` throws and reads a run with no failed
test as `Survived` (research R11). The report shows it only as `testsCompleted` below the dry run's test count, which a
static mutant (one every test runs under) must reach. The wrapper fails such a mutant under its own label, never the
tool's. The report here is the shape of the demo's `d217c-report-excerpt-tracing.json`.
"""
from __future__ import annotations

import json
import sys
import unittest

from test_stryker_verdict import REPORT, SERVICE, VerdictCase, mutant, report

sys.dont_write_bytecode = True
TEST_SELECTION = {"reads": ["assets/languages/typescript/scripts/stryker-mutation.py"]}


def tests(count: int) -> dict:
    """The report's `testFiles` as the json reporter writes it: the dry run's tests, `count` of them in two files."""
    return {f"tests/{name}.test.ts": {"tests": [{"id": str(n), "name": f"t{n}"} for n in range(first, first + size)]}
            for name, first, size in (("a", 0, count - 5), ("b", count - 5, 5))}


def survived(completed: int | None, static: bool = True, line: int = 81, replacement: str = "false",
             covered: tuple[str, ...] = ("39",)) -> dict:
    one = mutant("Survived", line=line, column=5, name="ConditionalExpression", replacement=replacement)
    one.update({"static": static, "coveredBy": list(covered), "killedBy": None})
    if completed is not None:
        one["testsCompleted"] = completed
    return one


class IncompleteTest(VerdictCase):
    def run_report(self, *mutants: dict, count: int | None = 86) -> tuple[int, list[str]]:
        the_report = report(src__tracing_ts=list(mutants))
        if count is not None:
            the_report["testFiles"] = tests(count)
        return self.run_wrapper({"report": the_report})

    def test_e1_a_static_survivor_that_ran_fewer_tests_than_the_dry_run_fails_as_incomplete_not_survived(self) -> None:
        code, lines = self.run_report(survived(81))
        self.assertEqual(code, 1, lines)
        self.assertEqual(lines[1], f"mutation: Incomplete {SERVICE}/src/tracing.ts:81:5 ConditionalExpression → false "
                                   "— Stryker says it survived, but the suite ran 81 of the dry run's 86 tests "
                                   "under it "
                                   "(a hook or a file failed, so that is not a survivor and not a pass; the tests that "
                                   "cover it are in tests/a.test.ts) — make the setup that failed fail inside a test "
                                   "(a hook inside a `describe`), and the mutant counts as killed "
                                   f"(report {REPORT})")
        self.assertEqual(lines[-1], "mutation: 1 mutants: 0 killed, 0 ignored, 0 not covered (reported, never failed), "
                                    f"1 survived with the suite incomplete; failed — report {REPORT}")
        self.assertNotIn(" 1 survived;", lines[-1])

    def test_e9_t035_the_line_names_no_file_the_report_does_not_place_and_says_the_remedy_either_way(self) -> None:
        the_report = report(src__tracing_ts=[survived(81, covered=("99",))])
        the_report["testFiles"] = tests(86)
        code, lines = self.run_wrapper({"report": the_report})
        self.assertEqual(code, 1, lines)
        self.assertNotIn("the tests that cover it are in", lines[1])
        self.assertIn("make the setup that failed fail inside a test (a hook inside a `describe`)", lines[1])
        the_report = report(src__tracing_ts=[survived(81, covered=("3", "83", "4"))])
        the_report["testFiles"] = tests(86)
        self.assertIn("the tests that cover it are in tests/a.test.ts, tests/b.test.ts",
                      self.run_wrapper({"report": the_report})[1][1])

    def test_e2_a_static_survivor_that_ran_every_test_stays_a_survivor(self) -> None:
        code, lines = self.run_report(survived(86, line=91, replacement="true"))
        self.assertEqual(code, 1, lines)
        self.assertTrue(lines[1].startswith(f"mutation: Survived {SERVICE}/src/tracing.ts:91:5"), lines)
        self.assertIn(", 1 survived;", lines[-1])

    def test_e3_a_survivor_that_is_not_static_is_never_compared_with_the_dry_run(self) -> None:
        code, lines = self.run_report(survived(2, static=False))
        self.assertEqual(code, 1, lines)
        self.assertTrue(lines[1].startswith("mutation: Survived "), lines)

    def test_e4_no_dry_run_count_in_the_report_leaves_the_tools_survived_as_it_is(self) -> None:
        code, lines = self.run_report(survived(81), count=None)
        self.assertEqual(code, 1, lines)
        self.assertTrue(lines[1].startswith("mutation: Survived "), lines)

    def test_e5_the_five_and_a_real_one_are_told_apart_in_one_report(self) -> None:
        five = [survived(81, line=81 + n) for n in range(5)]
        code, lines = self.run_report(*five, survived(86, line=91, replacement="true"))
        self.assertEqual(code, 1, lines)
        self.assertEqual(sum(line.startswith("mutation: Incomplete ") for line in lines), 5, lines)
        self.assertEqual(sum(line.startswith("mutation: Survived ") for line in lines), 1, lines)
        self.assertIn(", 5 survived with the suite incomplete, 1 survived; failed", lines[-1])

    def test_e6_a_killed_static_mutant_with_a_short_run_is_still_killed(self) -> None:
        one = mutant("Killed")
        one.update({"static": True, "testsCompleted": 27})
        code, lines = self.run_report(one)
        self.assertEqual((code, lines[-1].split(";")[0]),
                         (0, "mutation: 1 mutants: 1 killed, 0 ignored, 0 not covered (reported, never failed)"), lines)

    def test_e7_t041_with_ignore_static_a_static_survivor_ran_only_its_covering_tests(self) -> None:
        """A9: `ignoreStatic` runs a static mutant under the tests that cover it (here one), so one test completed is
        the whole of what it ran, and the suite's 86 is not the count to hold it to."""
        config = self.tree / SERVICE / "stryker.config.json"
        config.write_text(json.dumps({**json.loads(config.read_text(encoding="utf-8")), "ignoreStatic": True}),
                          encoding="utf-8")
        code, lines = self.run_report(survived(1), survived(1, line=91, covered=("1", "2", "3")))
        self.assertEqual(code, 1, lines)
        self.assertTrue(lines[1].startswith(f"mutation: Survived {SERVICE}/src/tracing.ts:81:5"), lines)
        self.assertTrue(lines[2].startswith(f"mutation: Incomplete {SERVICE}/src/tracing.ts:91:5"), lines)
        self.assertIn("the suite ran 1 of the 3 tests that cover it", lines[2])
        self.assertIn(", 1 survived with the suite incomplete, 1 survived; failed", lines[-1])

    def test_e8_t041_without_ignore_static_the_count_is_still_the_dry_runs(self) -> None:
        config = self.tree / SERVICE / "stryker.config.json"
        config.write_text(json.dumps({**json.loads(config.read_text(encoding="utf-8")), "ignoreStatic": False}),
                          encoding="utf-8")
        code, lines = self.run_report(survived(1))
        self.assertTrue(lines[1].startswith(f"mutation: Incomplete {SERVICE}/src/tracing.ts:81:5"), lines)


if __name__ == "__main__":
    unittest.main()
