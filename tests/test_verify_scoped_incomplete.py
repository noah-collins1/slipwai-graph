"""R5 (AC-S06-5): what cannot be established runs the full gate.

A changed `project.json`, `Makefile` or gate script, a changed path no deployable, contract or claiming check reads,
and a record the script cannot build each print one line, `dependency knowledge was incomplete ...`, and then the
one full gate, `make verify`, with its status. What ran is read from the stand-ins' log: the full gate is a `make`
call whose goal is `verify`, and no unit lines are said.
"""
from __future__ import annotations

import importlib
import sys
import unittest
from typing import Any

from scoped_fixture import EVENTS, FULL, LINE, ScopedCase, ShapeCase
from stamp_fixture import commit_all, git

from slipwai.assets import ROOT

sys.dont_write_bytecode = True

INCOMPLETE = LINE + "dependency knowledge was incomplete"
BROADENED = FULL + "dependency knowledge was incomplete"
UNCLAIMED = "no deployable, contract or check claims it"
DRY: dict[str, str | None] = {"STANDIN_DRY": "1"}


class IncompleteTest(ScopedCase):
    def assert_broadened(self, run: Any, said: list[str]) -> None:
        self.assertEqual(self.scoped_lines(run), [*said, BROADENED], run.stdout + run.stderr)
        self.assertEqual(len(self.verify_calls()), 1, "`make verify` was not run exactly once")
        self.assertEqual(self.lines(run), [], "a unit line was said beside the full gate")

    def lines(self, run: Any) -> list[str]:
        return [line for line in self.scoped_lines(run) if line[len(LINE):].startswith(("run ", "skip"))]

    def test_e1_an_unclaimed_path_is_named_and_the_full_gate_runs(self) -> None:
        (self.repo / "README.md").write_text("changed\n", encoding="utf-8")
        run = self.scoped()
        self.assert_broadened(run, [f"{INCOMPLETE} for README.md — {UNCLAIMED}"])
        self.forget_log()
        self.assertEqual(run.returncode, self.run_gate().returncode, "the status is not `make verify`'s")

    def test_e2_project_json_and_a_gate_script_say_what_they_are(self) -> None:
        with (self.repo / "project.json").open("a", encoding="utf-8") as handle:
            handle.write("\n")
        with (self.repo / "scripts" / "check-imports.py").open("a", encoding="utf-8") as handle:
            handle.write("\n# edited\n")
        self.assert_broadened(self.scoped(), [
            f"{INCOMPLETE} for project.json — it is project.json",
            f"{INCOMPLETE} for scripts/check-imports.py — it is a gate script under scripts/",
        ])

    def test_e2_the_makefile_and_this_scripts_own_modules_count(self) -> None:
        with (self.repo / "Makefile").open("a", encoding="utf-8") as handle:
            handle.write("\n# edited\n")
        (self.repo / "scripts" / "verify_scoped" / "extra.py").write_text("x = 1\n", encoding="utf-8")
        with (self.repo / "scripts" / "verify-scoped.py").open("a", encoding="utf-8") as handle:
            handle.write("\n# edited\n")
        self.assert_broadened(self.scoped(), [
            f"{INCOMPLETE} for Makefile — it is the Makefile",
            f"{INCOMPLETE} for scripts/verify-scoped.py — it is a gate script under scripts/",
            f"{INCOMPLETE} for scripts/verify_scoped/extra.py — it is a gate script under scripts/",
        ])

    def test_e5_every_unclaimed_path_has_its_own_line_and_the_gate_runs_once_with_its_status(self) -> None:
        (self.repo / "README.md").write_text("changed\n", encoding="utf-8")
        (self.repo / "LICENSE").write_text("changed\n", encoding="utf-8")
        (self.repo / "NOTICE").write_text("new\n", encoding="utf-8")
        run = self.scoped({"STANDIN_UV_FAIL": "1"})
        self.assertEqual(self.scoped_lines(run), [f"{INCOMPLETE} for {name} — {UNCLAIMED}"
                                                   for name in ("LICENSE", "NOTICE", "README.md")] + [BROADENED])
        self.assertEqual(len(self.verify_calls()), 1)
        self.forget_log()
        direct = self.run_gate({"STANDIN_UV_FAIL": "1"})
        self.assertNotEqual(direct.returncode, 0, direct.stdout)
        self.assertEqual(run.returncode, direct.returncode)


class TypescriptTest(ShapeCase):
    def test_e4_a_directory_under_packages_with_no_package_json_is_unclaimed(self) -> None:
        self.edit("packages/shared-go/x.go", "package shared\n")
        run = self.scoped(DRY)
        self.assertEqual(self.scoped_lines(run), [
            f"{INCOMPLETE} for packages/shared-go/x.go — {UNCLAIMED}", BROADENED], run.stdout + run.stderr)
        self.assertEqual(len(self.verify_calls()), 1)

    def test_e4_a_path_a_claiming_check_reads_is_claimed(self) -> None:
        self.edit("docs/event-model/README.md")
        run = self.scoped()
        self.assertNotIn(INCOMPLETE, "\n".join(self.scoped_lines(run)))
        self.assertEqual(self.verify_calls(), [])


class IntegrationTest(ShapeCase):
    shape = "integration"

    def test_e3_a_deployable_named_integration_has_no_units_and_the_gate_runs(self) -> None:
        self.edit("apps/service/src/service/extra.py", "x = 1\n")
        run = self.scoped(DRY)
        said = self.scoped_lines(run)
        self.assertEqual(len(said), 2, said)
        self.assertTrue(said[0].startswith(f"{INCOMPLETE} — "), said[0])
        self.assertIn("`integration`", said[0])
        self.assertIn("`lint-integration`", said[0])
        self.assertEqual(said[1], BROADENED)
        self.assertEqual(len(self.verify_calls()), 1)


class EventsTest(ShapeCase):
    shape = EVENTS

    def test_e4_a_model_it_cannot_read_where_an_event_edge_is_needed_names_why(self) -> None:
        git(self.repo, "checkout", "-q", "main")
        (self.repo / "docs" / "event-model" / "model.yaml").write_text("slices: [unclosed\n", encoding="utf-8")
        commit_all(self.repo, "a model that does not parse")
        git(self.repo, "checkout", "-q", "-B", "slice/S1", "main")
        self.edit("apps/billing/src/billing/extra.py", "x = 1\n")
        said = self.scoped_lines(self.scoped(DRY))
        self.assertEqual(len(said), 2, said)
        self.assertTrue(said[0].startswith(f"{INCOMPLETE} — the model cannot be read"), said[0])
        self.assertEqual(said[1], BROADENED)
        self.assertEqual(len(self.verify_calls()), 1)


class GateFilesTest(unittest.TestCase):
    """`unknown` is a pure function of the record and the changed paths: the names it cannot be run in a project."""

    def test_e2_every_spelling_of_the_makefile_counts(self) -> None:
        import sys as system
        system.path.insert(0, str(ROOT / "assets" / "toolkit" / "scripts"))
        module = importlib.import_module("verify_scoped.choose")
        record: dict[str, Any] = {"checks": {}, "contracts": []}
        found = module.unknown(record, ["GNUmakefile", "Makefile", "makefile", "scripts/a/b.py", "project.json"],
                               lambda path: path == "Makefile" or path.startswith("scripts/"))
        self.assertEqual(found, [
            ("GNUmakefile", "it is the Makefile"), ("Makefile", "it is the Makefile"),
            ("makefile", "it is the Makefile"), ("project.json", "it is project.json"),
            ("scripts/a/b.py", "it is a gate script under scripts/"),
        ])


if __name__ == "__main__":
    unittest.main()
