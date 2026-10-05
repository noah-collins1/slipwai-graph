"""T034 (R4, R5 · AC-S06-2, -5; D127 item 2): the rules are read under the goal the full gate gives them.

`make verify` hands its sub-make the goal `verify-checks` one level deeper, with `--no-print-directory`. A conditional
on `MAKECMDGOALS`, `MAKELEVEL` or `MAKEFLAGS` can add a prerequisite or a line that the full gate runs and a read under
the scoped run's own goal never sees. Where the two reads differ the run is the full gate, with its reason; where they
agree, which is every shape the factory generates, nothing is said.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

from scoped_fixture import EVENTS, FULL, events_project
from test_scoped_targets import SHAPES
from test_verify_scoped_record import RecordCase
from test_verify_scoped_sum import FORBIDDEN, LINT_DOCS, RuleCase

from slipwai.assets import ROOT

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "assets" / "toolkit" / "scripts"))

CONDITIONALS = {
    "MAKECMDGOALS": "ifneq ($(filter verify-checks,$(MAKECMDGOALS)),)",
    "MAKELEVEL": "ifeq ($(MAKELEVEL),1)",
    "MAKEFLAGS": "ifneq ($(findstring no-print-directory,$(MAKEFLAGS)),)",
}
READ = "reads differently under the goal `verify-checks` and level 1 that `make verify` gives its sub-make"


class GoalConditionalTest(RuleCase):
    def conditional(self, condition: str, body: str = "check-drawio: lint-docs\n") -> str:
        return f"\n{condition}\n{body}endif\n" + LINT_DOCS

    def test_e1_a_rule_that_exists_only_under_the_full_gates_goal_makes_the_run_the_full_gate(self) -> None:
        self.trunk(lambda text: text + self.conditional(CONDITIONALS["MAKECMDGOALS"]))
        self.forbidden()
        run = self.scoped()
        ran, skipped = self.decided(run)
        self.assertNotIn("check-drawio", skipped, run.stdout)
        self.assertEqual(self.scoped_lines(run)[0], FULL + f"the Makefile's `check-drawio` rule {READ}", run.stdout)
        self.assertEqual(len(self.verify_calls()), 1)
        self.assertNotEqual(run.returncode, 0, run.stdout)

    def runs_full_gate(self, condition: str, body: str, what: str) -> None:
        self.trunk(lambda text: text + self.conditional(condition, body))
        self.forbidden()
        run = self.scoped()
        self.assertEqual(self.scoped_lines(run)[0], FULL + f"the Makefile's {what} {READ}", run.stdout)
        self.assertEqual(len(self.verify_calls()), 1)

    def test_e1_sweep_makecmdgoals(self) -> None:
        self.runs_full_gate(CONDITIONALS["MAKECMDGOALS"], "check-drawio: lint-docs\n", "`check-drawio` rule")

    def test_e1_sweep_makelevel(self) -> None:
        self.runs_full_gate(CONDITIONALS["MAKELEVEL"], "check-drawio: lint-docs\n", "`check-drawio` rule")

    def test_e1_sweep_makeflags(self) -> None:
        self.runs_full_gate(CONDITIONALS["MAKEFLAGS"], "check-drawio: lint-docs\n", "`check-drawio` rule")

    def test_e1_a_recipe_line_that_only_the_full_gate_has_is_named(self) -> None:
        self.runs_full_gate(CONDITIONALS["MAKELEVEL"], "check-drawio:\n" + FORBIDDEN, "`check-drawio` rule")

    def test_e1_a_variable_that_only_the_full_gate_has_is_named(self) -> None:
        self.runs_full_gate(CONDITIONALS["MAKELEVEL"], "QUIET := x\n", "variable `QUIET`")

    def test_e1_a_conditional_that_does_not_change_the_rules_leaves_the_scoped_run_scoped(self) -> None:
        self.trunk(lambda text: text + "\nifneq ($(filter verify-checks,$(MAKECMDGOALS)),)\nendif\n")
        self.forbidden()
        run = self.scoped()
        self.assertNotIn(FULL, run.stdout)
        self.assertEqual(self.verify_calls(), [])


class EveryShapeTest(RecordCase):
    def test_e2_hold_the_two_reads_agree_in_every_shape(self) -> None:
        record = importlib.import_module("verify_scoped.record")
        shapes: dict[str, Path] = {name: self.project(name) for name in SHAPES}
        self.projects.setdefault(EVENTS, events_project(self.parent))
        shapes[EVENTS] = self.projects[EVENTS]
        for shape, project in shapes.items():
            with self.subTest(shape=shape):
                makefile = str(project / "Makefile")
                data = record.database("make", makefile)
                self.assertIsNone(record.under_the_full_gate("make", makefile, data))
                there = record.database("make", makefile, record.FULL_GATE_GOAL, "1", ("--no-print-directory",))
                self.assertEqual((there.needs, there.order_only, there.recipes),
                                 (data.needs, data.order_only, data.recipes))

    def test_e2_the_read_under_the_full_gates_goal_runs_no_recipe(self) -> None:
        """A recipe line that calls `$(MAKE)` runs under `-n` and `-q`, so the goal is handed over as `MAKECMDGOALS`."""
        record = importlib.import_module("verify_scoped.record")
        folder = self.parent / "marker"
        folder.mkdir(exist_ok=True)
        text = "verify-checks:\n\t+$(MAKE) --version >/dev/null; touch ran\n"
        (folder / "Makefile").write_text(text, encoding="utf-8")
        record.database("make", str(folder / "Makefile"), record.FULL_GATE_GOAL, "1", ("--no-print-directory",))
        self.assertFalse((folder / "ran").exists())
