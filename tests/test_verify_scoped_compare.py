"""R7, the comparison (AC-S06-8, -9): a scoped run asks the machine what the baseline asked and compares.

A unit runs when one of its tools answers differently from the baseline, or one of its variables' digests differs;
`UX_GATES_JOBS` and the job count select nothing. Where there is no usable baseline (none, another branch's, one that
does not parse, a tool that does not answer) every check that reads a tool or a variable runs, which is every check, so
the run is `make verify`, which then writes the baseline. The baseline is taken here through `verify-stamp.py`'s own
functions under the answers the example gives (`ScopedCase.write_baseline`); a scoped run never writes one.
"""
from __future__ import annotations

import json
import sys
import unittest

from scoped_fixture import FULL, LINE, ScopedCase, ShapeCase

sys.dont_write_bytecode = True

DRY: dict[str, str | None] = {"STANDIN_DRY": "1"}
NODE_READERS = {f"{gate}-{name}" for gate in ("lint", "typecheck", "test") for name in ("service", "web")} | {
    "check-ux-gates", "check-drawio", "check-openapi"}
NO_BASELINE = LINE + "no usable baseline ({why}) — every check that reads a tool or a variable runs"
EVERY = FULL + "every check was chosen"


class ToolsTest(ShapeCase):
    def test_e1_a_node_that_answers_differently_runs_what_asks_it(self) -> None:
        self.write_baseline({"STANDIN_NODE_VERSION": "v20.11.0"})
        run = self.scoped({"STANDIN_NODE_VERSION": "v22.1.0", **DRY})
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        ran, skipped = self.decided(run)
        self.assertTrue(set(ran) >= NODE_READERS, sorted(NODE_READERS - set(ran)))
        self.assertEqual({ran[unit] for unit in NODE_READERS}, {"node answers differently from the baseline"})
        self.assertTrue({"check-styles", "check-imports", "check-model", "check-decisions"} <= set(skipped))
        (goals,) = self.called()
        self.assertTrue(set(goals) >= NODE_READERS and not {"check-styles", "check-model"} & set(goals), goals)

    def test_e1_a_node_that_answers_as_it_did_selects_nothing(self) -> None:
        self.write_baseline({"STANDIN_NODE_VERSION": "v20.11.0"})
        ran, skipped = self.decided(self.scoped({"STANDIN_NODE_VERSION": "v20.11.0", **DRY}))
        self.assertEqual(set(ran) & NODE_READERS, set(), "a unit ran for a machine that answers as it did")
        self.assertTrue(set(skipped) >= NODE_READERS)

    def test_e1_the_tool_a_unit_names_is_the_first_of_its_tools_that_moved(self) -> None:
        self.write_baseline({"STANDIN_NODE_VERSION": "v20.11.0", "STANDIN_NPM_VERSION": "10.0.0"})
        ran, _ = self.decided(self.scoped({"STANDIN_NODE_VERSION": "v20.11.0", "STANDIN_NPM_VERSION": "11.0.0", **DRY}))
        self.assertEqual(ran["test-service"], "npm answers differently from the baseline")

    def test_e1_a_path_that_changed_is_named_before_a_tool_that_moved(self) -> None:
        self.write_baseline({"STANDIN_NODE_VERSION": "v20.11.0"})
        self.edit("apps/web/src/App.tsx")
        ran, _ = self.decided(self.scoped({"STANDIN_NODE_VERSION": "v22.1.0", **DRY}))
        self.assertEqual(ran["lint-web"], "apps/web/src/App.tsx changed")
        self.assertEqual(ran["lint-service"], "node answers differently from the baseline")


class VariablesTest(ShapeCase):
    def decide(self, then: str | None, was: str | None) -> tuple[dict[str, str], dict[str, str]]:
        self.write_baseline({"UX_GATES_SINCE": was})
        return self.decided(self.scoped({"UX_GATES_SINCE": then, **DRY}))

    def test_e2_set_where_it_was_unset_runs_the_check_that_reads_it(self) -> None:
        ran, skipped = self.decide("abc123", None)
        self.assertEqual(ran["check-ux-gates"], "UX_GATES_SINCE differs from the baseline")
        self.assertIn("lint-web", skipped)
        self.assertIn("check-model", skipped)

    def test_e2_unset_where_it_was_set_and_another_value_each_differ(self) -> None:
        for then, was in ((None, "abc123"), ("def456", "abc123")):
            with self.subTest(then=then, was=was):
                self.reset()
                ran, _ = self.decide(then, was)
                self.assertEqual(ran["check-ux-gates"], "UX_GATES_SINCE differs from the baseline")

    def test_e2_set_to_empty_differs_from_unset(self) -> None:
        for then, was in (("", None), (None, "")):
            with self.subTest(then=then, was=was):
                self.reset()
                ran, _ = self.decide(then, was)
                self.assertEqual(ran["check-ux-gates"], "UX_GATES_SINCE differs from the baseline")

    def test_e2_both_as_at_the_baseline_is_skipped(self) -> None:
        for value in (None, "", "abc123"):
            with self.subTest(value=value):
                self.reset()
                ran, skipped = self.decide(value, value)
                self.assertIn("check-ux-gates", skipped)
                self.assertNotIn("check-ux-gates", ran)

    def test_e3_hold_the_job_count_selects_nothing(self) -> None:
        """HOLD (teeth: add `UX_GATES_JOBS` to `VARIABLES` of the stamp or the table's row and this fails)."""
        self.write_baseline({"UX_GATES_JOBS": None})
        plain = self.decided(self.scoped(DRY))
        for env, args in (({"UX_GATES_JOBS": "8"}, None), ({}, ["-j4"])):
            with self.subTest(env=env, args=args):
                self.assertEqual(self.decided(self.scoped({**env, **DRY}, args)), plain)
        self.assertNotIn("check-ux-gates", plain[0])


class NoUsableBaselineTest(ShapeCase):
    def assert_full(self, run: object, why: str) -> None:
        said = self.scoped_lines(run)  # type: ignore[arg-type]
        self.assertEqual(said, [NO_BASELINE.format(why=why), EVERY], getattr(run, "stdout", ""))
        self.assertEqual(len(self.verify_calls()), 1, "`make verify` was not run exactly once")
        self.assertEqual(self.called(), [["verify-checks"]], "a selection was made as well as the full gate")

    def test_e4_none_yet_on_this_branch(self) -> None:
        self.baseline_file().unlink()
        self.assert_full(self.scoped(DRY), "none yet on this branch")

    def test_e4_one_taken_on_another_branch(self) -> None:
        path = self.baseline_file()
        path.write_text(json.dumps({**json.loads(path.read_text(encoding="utf-8")), "branch": "slice/b"}),
                        encoding="utf-8")
        self.assert_full(self.scoped(DRY), "it was taken on slice/b")

    def test_e4_one_that_does_not_parse_or_has_not_the_shape(self) -> None:
        path = self.baseline_file()
        wrong = '{"branch": "slice/S1", "tools": [], "variables": {}}'
        for text in ("{not json", "[]", '{"branch": "slice/S1"}', wrong):
            with self.subTest(text=text):
                for left in path.parent.iterdir():  # the full gate of the run before left a stamp and a baseline
                    left.unlink()
                path.write_text(text, encoding="utf-8")
                self.forget_log()
                self.assert_full(self.scoped(DRY), "it cannot be read")

    def test_e4_a_baseline_that_is_a_directory_cannot_be_read(self) -> None:
        path = self.baseline_file()
        path.unlink()
        path.mkdir()
        self.assert_full(self.scoped(DRY), "it cannot be read")

    def test_e4_a_tool_that_does_not_answer(self) -> None:
        run = self.scoped({"STANDIN_NODE_FAIL": "1", **DRY})
        said = self.scoped_lines(run)
        self.assertEqual(len(said), 2, said)
        self.assertRegex(said[0], rf"^{LINE}no usable baseline \(node exited 1 when asked its version\) — every check ")
        self.assertEqual(said[1], EVERY)
        self.assertEqual(len(self.verify_calls()), 1)

    def test_e4_the_line_is_said_once_and_no_unit_line_follows_it(self) -> None:
        self.baseline_file().unlink()
        run = self.scoped(DRY)
        self.assertEqual(sum("no usable baseline" in line for line in self.scoped_lines(run)), 1)
        self.assertEqual(self.lines(run), [])

    def test_e4_an_unclaimed_path_is_named_first_and_the_baseline_is_not_asked_for(self) -> None:
        self.baseline_file().unlink()
        self.edit("README.md")
        said = self.scoped_lines(self.scoped(DRY))
        self.assertEqual(len(said), 2, said)
        self.assertTrue(said[0].startswith(LINE + "dependency knowledge was incomplete for README.md"), said[0])


class WrittenByTheFullGateTest(ScopedCase):
    def test_e4_the_full_gate_a_missing_baseline_runs_writes_one(self) -> None:
        self.assertEqual(sorted((self.repo / ".git").glob("slipwai/verify-baseline-*")), [])
        run = self.scoped()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        said = self.scoped_lines(run)
        self.assertEqual(said, [NO_BASELINE.format(why="none yet on this branch"), EVERY], run.stdout)
        self.assertEqual(self.baseline_file().parent.name, "slipwai")

    def test_e5_hold_a_scoped_run_that_selects_leaves_the_baseline_as_it_was(self) -> None:
        """HOLD (teeth: make `run` call the stamp's `write_baseline` and the modification time moves)."""
        self.write_baseline()
        (self.repo / "apps" / "service" / "extra.txt").write_text("an edit\n", encoding="utf-8")
        path = self.baseline_file()
        was, before = path.read_bytes(), path.stat().st_mtime_ns
        run = self.scoped()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue(any(line.startswith(LINE + "run ") for line in self.scoped_lines(run)), run.stdout)
        self.assertEqual((path.read_bytes(), path.stat().st_mtime_ns), (was, before))
        self.assertEqual(self.verify_calls(), [])


if __name__ == "__main__":
    unittest.main()
