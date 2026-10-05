"""T025 (R3, R4 · AC-S06-2, -4; data-model *How a unit is chosen*, last paragraph): the recipe-sum guard.

Where a gate's recipe is not exactly its units' lines and family targets' lines, and its prerequisites not exactly
theirs, the gate runs whole under its own name: a project owns its `Makefile`, and a line it added to `lint:` is one no
unit holds. Examples run the real `make` over a generated project on a slice branch, with a baseline, after the
`Makefile` the branch is cut from has been changed on the trunk (a `Makefile` change on the branch itself broadens).
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from scoped_fixture import FULL, MAKEFILE_WORDS, ShapeCase
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


def text_digest(makefile: Path) -> str:
    """The digest `rules.json` holds for a `Makefile`, computed here as the spec words it (sha256, CRLF read as LF)."""
    return hashlib.sha256(makefile.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


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

    def assert_text_is_the_reason(self, run: Any) -> None:
        """D140: a gate a project edited is no longer the factory's, so no sum is read and the full gate runs."""
        self.assertEqual(self.scoped_lines(run)[0], FULL + MAKEFILE_WORDS, run.stdout)
        self.assertEqual(self.lines(run), [], "a unit line was said beside the full gate")
        self.assertEqual(len(self.verify_calls()), 1, "`make verify` was not run exactly once")


class RecipeSumTest(SumCase):
    """A project's edit to a gate's recipe or prerequisites was once a gate that ran whole (T025); with the text held
    it is the full gate, and the sum is read only for the record (e4 and e1 below)."""

    def test_e1_a_line_the_project_added_to_lint_is_the_full_gate_and_the_run_fails(self) -> None:
        self.trunk_changes(self.add_to_lint)
        self.edit("apps/web/src/App.tsx", "\n// FORBIDDEN\n")
        run = self.scoped()
        self.assert_text_is_the_reason(run)
        self.assertNotEqual(run.returncode, 0, run.stdout)

    def test_e2_a_prerequisite_the_project_added_is_the_full_gate(self) -> None:
        self.trunk_changes(lambda text: text + "\nlint: lint-docs\nlint-docs:\n\t@echo not linted; false\n")
        self.edit("apps/service/src/main.ts", "\n// an edit\n")
        run = self.scoped()
        self.assert_text_is_the_reason(run)
        self.assertNotEqual(run.returncode, 0, run.stdout)

    def test_e3_a_line_a_unit_runs_that_the_gate_no_longer_has_is_the_full_gate(self) -> None:
        self.trunk_changes(lambda text: text.replace(OWN_LINE, "", 1))
        self.edit("apps/service/src/main.ts", "\n// an edit\n")
        self.assert_text_is_the_reason(self.scoped(env=DRY))


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
        git(self.repo, "commit", "-qam", "a project's own change to what the factory wrote", "--allow-empty")
        git(self.repo, "checkout", "-q", "-B", "slice/S1")
        self.write_baseline()

    def forbidden(self) -> None:
        self.edit("apps/web/src/App.tsx", "\n// FORBIDDEN\n")


class FullGateTest(RuleCase):
    """Every edit D127 once charged to one check, one gate or the full gate is the full gate through the `Makefile`
    reason now: named check, prerequisite of a check, order-only prerequisite of a gate, `verify`, `verify-checks`, a
    rule two members reach, a variable the recipe reads, the shell, a check removed."""

    EDITS = {
        "a line added to a named check's recipe": lambda text: text.replace(DRAWIO, DRAWIO + FORBIDDEN, 1),
        "a prerequisite given to a named check": lambda text: text + LINT_DOCS + "check-decisions: lint-docs\n",
        "an order-only prerequisite of a gate": lambda text: text + LINT_DOCS + "lint: | lint-docs\n",
        "a prerequisite of verify": lambda text: text + LINT_DOCS + "verify: lint-docs\n",
        "a line in verify-checks": lambda text: text.replace(CLOSING, FORBIDDEN + CLOSING, 1),
        "a rule two members reach": lambda text: text + LINT_DOCS + "check-python: lint-docs\n",
        "a variable the verify recipe reads": lambda text: text.replace("VERIFY_STAMP := ", "VERIFY_STAMP := -x ", 1),
        "the shell every recipe runs in": lambda text: text.replace("SHELL := /bin/bash", "SHELL := /bin/sh", 1),
        "a check the project removed": lambda text: text.replace(" check-decisions test", " test", 1),
        "a check the project added": lambda text: text + "\nverify-checks: own\nown:\n\t@echo ok\n",
    }

    def test_e4_each_is_the_full_gate_with_the_makefile_words_and_runs_make_verify_once(self) -> None:
        first = git(self.repo, "rev-parse", "main").strip()
        for what, edit in self.EDITS.items():
            with self.subTest(what):
                self.reset()
                git(self.repo, "checkout", "-q", "main")
                git(self.repo, "checkout", "-q", first, "--", "Makefile")  # each edit is to the factory's text
                self.trunk(edit)
                self.forbidden()
                run = self.scoped()
                self.assertEqual(self.scoped_lines(run)[0], FULL + MAKEFILE_WORDS, run.stdout)
                self.assertEqual(self.lines(run), [], "a unit line was said beside the full gate")
                self.assertEqual(len(self.verify_calls()), 1, "`make verify` was not run exactly once")
                self.forget_log()

    def test_e6_no_rules_file_is_the_full_gate_for_want_of_knowledge(self) -> None:
        self.trunk(change=lambda repo: (repo / RULES).unlink(missing_ok=True))
        self.forbidden()
        run = self.scoped()
        self.assertEqual(self.scoped_lines(run)[-1], INCOMPLETE, run.stdout)
        self.assertEqual(self.lines(run), [])

    def test_e6_a_rules_file_of_a_schema_it_does_not_know_is_the_same(self) -> None:
        def write(repo: Path) -> None:
            held = {"schema": 2, "rules": {}, "variables": {}, "makefile": text_digest(repo / "Makefile")}
            (repo / RULES).write_text(json.dumps(held), encoding="utf-8")

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
