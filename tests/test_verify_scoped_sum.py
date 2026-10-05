"""T025 (R3, R4 · AC-S06-2, -4; data-model *How a unit is chosen*, last paragraph): the recipe-sum guard.

Where a gate's recipe is not exactly its units' lines and family targets' lines, and its prerequisites not exactly
theirs, the gate runs whole under its own name: a project owns its `Makefile`, and a line it added to `lint:` is one no
unit holds. Examples run the real `make` over a generated project on a slice branch, with a baseline, after the
`Makefile` the branch is cut from has been changed on the trunk (a `Makefile` change on the branch itself broadens).
"""
from __future__ import annotations

import sys
from collections.abc import Callable

from scoped_fixture import ShapeCase
from stamp_fixture import git
from test_scoped_targets import SHAPES
from test_verify_scoped_record import RecordCase, loaded, record

sys.dont_write_bytecode = True

WHOLE = "its recipe is not the sum of its per-deployable targets"
OWN_LINE = "\tnpm --workspace apps/service run lint\n"
FORBIDDEN = "\t@! grep -rq FORBIDDEN apps/web/src\n"
GATE = "lint: ## Run the native formatting and static-analysis gate\n"
DRY: dict[str, str | None] = {"STANDIN_DRY": "1"}


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
