"""T025 (R3, R4 · AC-S06-2, -4; data-model *How a unit is chosen*, last paragraph): the recipe-sum guard.

Where a gate's recipe is not exactly its units' lines and family targets' lines, and its prerequisites not exactly
theirs, the gate runs whole under its own name: a project owns its `Makefile`, and a line it added to `lint:` is one no
unit holds. Examples run the real `make` over a generated project on a slice branch, with a baseline, after the
`Makefile` the branch is cut from has been changed on the trunk (a `Makefile` change on the branch itself broadens).
"""
from __future__ import annotations

import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from scoped_fixture import FULL, ShapeCase
from stamp_fixture import git
from test_scoped_targets import SHAPES
from test_verify_scoped_record import RecordCase, loaded, record

sys.dont_write_bytecode = True

WHOLE = "its recipe is not the sum of its per-deployable targets"
OWN_LINE = "\tnpm --workspace apps/service run lint\n"
FORBIDDEN = "\t@! grep -rq FORBIDDEN apps/web/src\n"
GATE = "lint: ## Run the native formatting and static-analysis gate\n"
DRY: dict[str, str | None] = {"STANDIN_DRY": "1"}
RULES = "scripts/verify_scoped/rules.json"
WHY = "its rule is not the one the factory wrote (scripts/verify_scoped/rules.json)"
INCOMPLETE = FULL + "dependency knowledge was incomplete"
LINT_DOCS = "\n.PHONY: lint-docs\nlint-docs:\n" + FORBIDDEN
DRAWIO = "\tnode scripts/event-model/node_modules/tsx/dist/cli.mjs scripts/event-model/render-drawio.ts --check\n"
CLOSING = "\t@echo 'verify: all gates passed'\n"


def full(target: str) -> str:
    return FULL + f"the Makefile's `{target}` rule is not the one the factory wrote"


class SumCase(ShapeCase):
    shape = "model-typescript-web"

    def trunk_changes(self, edit: Callable[[str], str]) -> None:
        """The project's own `Makefile`, as the trunk has it: edited, committed, and the branch cut from it again."""
        git(self.repo, "checkout", "-q", "main")
        makefile = self.repo / "Makefile"
        makefile.write_text(edit(makefile.read_text(encoding="utf-8")), encoding="utf-8")
        git(self.repo, "commit", "-qam", "a project's own gate line")
        git(self.repo, "checkout", "-q", "-B", "slice/S1")
        self.write_baseline()

    def add_to_lint(self, text: str) -> str:
        head, tail = text.split(GATE, 1)
        first, rest = tail.split("\n", 1)
        return head + GATE + first + "\n" + FORBIDDEN + rest

    def whole(self, run_units: dict[str, str]) -> None:
        """Every `lint` unit runs, for the one reason, however little of it changed."""
        self.assertEqual({unit: reason for unit, reason in run_units.items() if unit.startswith("lint-")},
                         {"lint-service": WHOLE, "lint-web": WHOLE})


class RecipeSumTest(SumCase):
    def test_e1_a_line_the_project_added_to_lint_runs_lint_whole_and_the_run_fails(self) -> None:
        self.trunk_changes(self.add_to_lint)
        self.edit("apps/web/src/App.tsx", "\n// FORBIDDEN\n")
        run = self.scoped()
        ran, _ = self.decided(run)
        self.whole(ran)
        self.assertNotEqual(run.returncode, 0, run.stdout)
        self.assertTrue(self.scoped_lines(run)[-1].endswith("each failed check is named above on a line carrying ***"))

    def test_e1_the_make_call_names_the_gate_in_place_of_its_units(self) -> None:
        self.trunk_changes(self.add_to_lint)
        self.edit("apps/web/src/App.tsx", "\n// FORBIDDEN\n")
        self.scoped(env=DRY)
        (goals,) = self.called()
        self.assertIn("lint", goals)
        self.assertEqual([goal for goal in goals if goal.startswith("lint-")], [])

    def test_e2_a_prerequisite_the_project_added_is_part_of_the_sum(self) -> None:
        self.trunk_changes(lambda text: text + "\nlint: lint-docs\nlint-docs:\n\t@echo not linted; false\n")
        self.edit("apps/service/src/main.ts", "\n// an edit\n")
        run = self.scoped()
        ran, _ = self.decided(run)
        self.assertEqual(ran["lint-service"], WHOLE)
        self.assertEqual(ran["lint-web"], WHOLE)
        self.assertNotEqual(run.returncode, 0, run.stdout)

    def test_e3_a_line_a_unit_runs_that_the_gate_no_longer_has(self) -> None:
        self.trunk_changes(lambda text: text.replace(OWN_LINE, "", 1))
        self.edit("apps/service/src/main.ts", "\n// an edit\n")
        ran, _ = self.decided(self.scoped(env=DRY))
        self.whole(ran)


class EveryShapeTest(RecordCase):
    def test_e4_hold_no_generated_shape_has_a_gate_that_is_not_the_sum_of_its_units(self) -> None:
        held = 0
        for shape in SHAPES:
            project = self.project(shape)
            if record(project).returncode != 0:  # `integration` has no unit to sum
                continue
            held += 1
            data = loaded(project)
            self.assertEqual([unit for unit, check in data["checks"].items() if check.get("whole")], [], shape)
        self.assertGreaterEqual(held, 12)

    def test_e1_a_line_added_to_any_one_gate_of_any_family_makes_that_gate_whole(self) -> None:
        """The sweep: each of the three gates, in a shape of every family (npm, Python, Go, Java and a mix)."""
        for shape in ("model-typescript-web", "two-python", "go-web", "java-python-web"):
            for gate in ("lint", "typecheck", "test"):
                with self.subTest(shape=shape, gate=gate):
                    project = self.project(shape)
                    makefile = project / "Makefile"
                    text = makefile.read_text(encoding="utf-8")
                    heading = next(line for line in text.splitlines() if line.startswith(f"{gate}:"))
                    added = heading + "\n\t@echo a line the project added\n"
                    makefile.write_text(text.replace(heading + "\n", added, 1), encoding="utf-8")
                    units = loaded(project)["checks"]
                    wholes = {unit: check for unit, check in units.items() if check.get("whole")}
                    self.assertEqual({unit.split("-")[0] for unit in wholes}, {gate})
                    self.assertTrue(all(check["targets"] == [gate] for check in wholes.values()))

    def test_e3_the_lines_of_one_unit_in_another_order_are_not_the_sum(self) -> None:
        project = self.project("go-web")
        makefile = project / "Makefile"
        vet, staticcheck = "\tcd apps/service && go vet ./...\n", "\tcd apps/service && go tool staticcheck ./...\n"
        text = makefile.read_text(encoding="utf-8")
        self.assertIn(vet + staticcheck, text)
        makefile.write_text(text.replace(vet + staticcheck, staticcheck + vet, 1), encoding="utf-8")
        checks = loaded(project)["checks"]
        self.assertEqual({unit for unit, check in checks.items() if check.get("whole")}, {"lint-service", "lint-web"})


class RuleCase(ShapeCase):
    shape = "model-typescript-web"

    def trunk(self, edit: Callable[[str], str] | None = None, change: Callable[[Path], None] | None = None) -> None:
        """What the project's trunk holds, changed and committed, and the branch cut from it again with its baseline."""
        git(self.repo, "checkout", "-q", "main")
        if edit is not None:
            makefile = self.repo / "Makefile"
            makefile.write_text(edit(makefile.read_text(encoding="utf-8")), encoding="utf-8")
        if change is not None:
            change(self.repo)
        git(self.repo, "commit", "-qam", "a project's own change to what the factory wrote")
        git(self.repo, "checkout", "-q", "-B", "slice/S1")
        self.write_baseline()

    def forbidden(self) -> None:
        self.edit("apps/web/src/App.tsx", "\n// FORBIDDEN\n")


class NamedCheckTest(RuleCase):
    def test_e1_a_line_added_to_a_named_checks_recipe_runs_it_and_the_run_fails(self) -> None:
        self.trunk(lambda text: text.replace(DRAWIO, DRAWIO + FORBIDDEN, 1))
        self.forbidden()
        run = self.scoped()
        ran, skipped = self.decided(run)
        self.assertEqual(ran.get("check-drawio"), WHY, run.stdout)
        self.assertNotIn("check-drawio", skipped)
        self.assertNotEqual(run.returncode, 0, run.stdout)

    def test_e1_the_record_says_the_check_has_no_recorded_inputs_and_claims_nothing(self) -> None:
        self.trunk(lambda text: text.replace(DRAWIO, DRAWIO + FORBIDDEN, 1))
        entry = loaded(self.repo)["checks"]["check-drawio"]
        self.assertEqual((entry["inputs"], entry["claims"], entry["always"]), (None, False, WHY))

    def test_e2_a_prerequisite_a_project_gave_a_named_check_runs_it_and_the_run_fails(self) -> None:
        self.trunk(lambda text: text + LINT_DOCS + "check-decisions: lint-docs\n")
        self.forbidden()
        run = self.scoped()
        ran, skipped = self.decided(run)
        self.assertEqual(ran.get("check-decisions"), WHY, run.stdout)
        self.assertNotIn("check-decisions", skipped)
        self.assertNotEqual(run.returncode, 0, run.stdout)

    def test_e2_one_charged_check_does_not_make_the_others_run(self) -> None:
        self.trunk(lambda text: text + LINT_DOCS + "check-decisions: lint-docs\n")
        self.forbidden()
        _, skipped = self.decided(self.scoped())
        self.assertIn("check-drawio", skipped)
        self.assertIn("lint-service", skipped)

    def test_e3_an_order_only_prerequisite_of_a_gate_is_part_of_its_sum(self) -> None:
        self.trunk(lambda text: text + LINT_DOCS + "lint: | lint-docs\n")
        self.forbidden()
        run = self.scoped()
        ran, _ = self.decided(run)
        self.assertEqual({unit: why for unit, why in ran.items() if unit.startswith("lint-")},
                         {"lint-service": WHOLE, "lint-web": WHOLE}, run.stdout)
        self.assertNotEqual(run.returncode, 0, run.stdout)


class FullGateTest(RuleCase):
    def assert_full(self, target: str, run: Any) -> None:
        self.assertEqual(self.scoped_lines(run)[0], full(target), run.stdout)
        self.assertEqual(self.lines(run), [], "a unit line was said beside the full gate")
        self.assertEqual(len(self.verify_calls()), 1, "`make verify` was not run exactly once")

    def test_e4_a_prerequisite_of_verify_is_the_full_gate(self) -> None:
        self.trunk(lambda text: text + LINT_DOCS + "verify: lint-docs\n")
        self.forbidden()
        run = self.scoped()
        self.assert_full("verify", run)
        self.assertNotEqual(run.returncode, 0, run.stdout)

    def test_e4_a_line_in_verify_checks_is_the_full_gate(self) -> None:
        self.trunk(lambda text: text.replace(CLOSING, FORBIDDEN + CLOSING, 1))
        self.forbidden()
        self.assert_full("verify-checks", self.scoped())

    def test_e7_a_rule_two_members_reach_is_the_full_gate(self) -> None:
        self.trunk(lambda text: text + LINT_DOCS + "check-python: lint-docs\n")
        self.forbidden()
        self.assert_full("check-python", self.scoped())

    def assert_variable(self, name: str, run: Any) -> None:
        self.assertEqual(self.scoped_lines(run)[0], FULL + f"the Makefile's variable `{name}` is not the one the "
                         "factory wrote", run.stdout)

    def test_e8_a_variable_the_verify_recipe_reads_is_the_full_gate(self) -> None:
        self.trunk(lambda text: text.replace("VERIFY_STAMP := ", "VERIFY_STAMP := --tool git ", 1))
        self.forbidden()
        self.assert_variable("VERIFY_STAMP", self.scoped())

    def test_e8_the_shell_every_recipe_runs_in_is_the_full_gate(self) -> None:
        self.trunk(lambda text: text.replace("SHELL := /bin/bash", "SHELL := /bin/sh", 1))
        self.forbidden()
        self.assert_variable("SHELL", self.scoped())

    def test_e9_a_check_the_project_removed_is_a_difference_in_verify_checks(self) -> None:
        self.trunk(lambda text: text.replace(" check-decisions test", " test", 1))
        self.forbidden()
        self.assert_full("verify-checks", self.scoped())

    def test_e6_no_rules_file_is_the_full_gate_for_want_of_knowledge(self) -> None:
        self.trunk(change=lambda repo: (repo / RULES).unlink(missing_ok=True))
        self.forbidden()
        run = self.scoped()
        self.assertEqual(self.scoped_lines(run)[-1], INCOMPLETE, run.stdout)
        self.assertEqual(self.lines(run), [])

    def test_e6_a_rules_file_of_a_schema_it_does_not_know_is_the_same(self) -> None:
        def write(repo: Path) -> None:
            (repo / RULES).write_text(json.dumps({"schema": 2, "rules": {}, "variables": {}}), encoding="utf-8")

        self.trunk(change=write)
        self.forbidden()
        run = self.scoped()
        self.assertEqual(self.scoped_lines(run)[-1], INCOMPLETE, run.stdout)

    def test_e6_a_rules_file_that_is_not_json_is_the_same(self) -> None:
        def write(repo: Path) -> None:
            (repo / RULES).write_text("{not json", encoding="utf-8")

        self.trunk(change=write)
        self.forbidden()
        self.assertEqual(self.scoped_lines(self.scoped())[-1], INCOMPLETE)
