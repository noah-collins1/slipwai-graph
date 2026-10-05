"""T034 + T037 (R4, R5 · AC-S06-2, -5; D127 item 2, D140): a conditional on what a real run has is the full gate.

`make verify` hands its sub-make the goal `verify-checks` one level deeper, with `--no-print-directory` and
`VERIFY_ORDER=1`; the scoped run's call hands its units as goals. A conditional on `MAKECMDGOALS`, `MAKELEVEL`,
`MAKEFLAGS`, `MAKE_RESTARTS`, the clock or `VERIFY_ORDER` can add a prerequisite or a line that a real run takes and a
database read never sees. No read can model them all, so the text is held instead (D140): each of the shapes below is a
`Makefile` the factory did not write and is the full gate before make reads it. The factory's own text gives the same
database under the goal of the full gate's sub-make in every shape (e2).
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

from scoped_fixture import EVENTS, FULL, MAKEFILE_WORDS, events_project
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


class GoalConditionalTest(RuleCase):
    """T034's five conditionals and T037's (a) to (e) are one reproduction each: a `Makefile` the factory did not
    write is the full gate with the `Makefile` words, before make reads it (D140). Each was a false *passed* while
    the full gate failed: web lint fails on the `FORBIDDEN` edit and the scoped run passed."""

    def conditional(self, condition: str, body: str = "check-drawio: lint-docs\n") -> str:
        return f"\n{condition}\n{body}endif\n" + LINT_DOCS

    def assert_full(self, text: str, env: dict[str, str | None] | None = None, fails: bool = False) -> None:
        self.trunk(lambda old: old + text)
        self.forbidden()
        run = self.scoped(env=env)
        self.assertEqual(self.scoped_lines(run)[0], FULL + MAKEFILE_WORDS, run.stdout)
        self.assertEqual(self.lines(run), [], "a unit line was said beside the full gate")
        self.assertEqual(len(self.verify_calls()), 1)
        if fails:
            self.assertNotEqual(run.returncode, 0, run.stdout)

    def test_e1_a_rule_that_exists_only_under_the_full_gates_goal(self) -> None:
        self.assert_full(self.conditional(CONDITIONALS["MAKECMDGOALS"]), fails=True)

    def test_e1_sweep_makelevel(self) -> None:
        self.assert_full(self.conditional(CONDITIONALS["MAKELEVEL"]))

    def test_e1_sweep_makeflags(self) -> None:
        self.assert_full(self.conditional(CONDITIONALS["MAKEFLAGS"]))

    def test_e1_a_recipe_line_that_only_the_full_gate_has(self) -> None:
        self.assert_full(self.conditional(CONDITIONALS["MAKELEVEL"], "check-drawio:\n" + FORBIDDEN))

    def test_e1_a_variable_that_only_the_full_gate_has(self) -> None:
        self.assert_full(self.conditional(CONDITIONALS["MAKELEVEL"], "QUIET := x\n"))

    def test_e1_a_conditional_that_changes_nothing_is_the_full_gate_too(self) -> None:
        """Fails closed: the text is not the factory's, whatever the conditional does."""
        self.assert_full("\nifneq ($(filter verify-checks,$(MAKECMDGOALS)),)\nendif\n" + LINT_DOCS)

    def test_t037_a_the_factorys_own_verify_order_idiom(self) -> None:
        self.assert_full(self.conditional("ifeq ($(origin VERIFY_ORDER),command line)"), fails=True)

    def test_t037_b_the_dry_run_flags(self) -> None:
        condition = "ifeq (,$(findstring n,$(filter-out --%,$(firstword $(MAKEFLAGS)))))"
        self.assert_full(self.conditional(condition), fails=True)

    def test_t037_c_the_origin_of_the_goals(self) -> None:
        self.assert_full(self.conditional("ifneq ($(origin MAKECMDGOALS),command line)"), fails=True)

    def test_t037_a_prime_an_unconditional_use_of_verify_order(self) -> None:
        self.assert_full("\ncheck-drawio: $(if $(VERIFY_ORDER),lint-docs)\n" + LINT_DOCS, fails=True)

    def test_t037_d_the_scoped_calls_own_goals(self) -> None:
        condition = "ifneq ($(filter lint-web,$(MAKECMDGOALS)),)"
        self.assert_full(self.conditional(condition, "override SHELL := /bin/true\n"),
                         env={"STANDIN_NPM_FAIL": "run lint"}, fails=True)

    def test_t037_e_makeflags_with_e(self) -> None:
        self.assert_full("\nMAKEFLAGS += -e\n" + LINT_DOCS)

    def test_t037_make_restarts(self) -> None:
        self.assert_full("\nifeq ($(MAKE_RESTARTS),)\ncheck-drawio: lint-docs\nendif\n" + LINT_DOCS)

    def test_t037_the_clock(self) -> None:
        self.assert_full("\nifeq ($(shell date +%Y),1999)\ncheck-drawio: lint-docs\nendif\n" + LINT_DOCS)


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
