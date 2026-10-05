"""R6 (AC-S06-6): the checks that always run claim nothing.

`check-slice-scope` compares the whole branch with its base and `check-codegraph` reads every tracked file, so each runs
on every scoped run and neither claims a file; `check-python` runs because every check waits on it; a `verify-checks`
prerequisite with no recorded inputs runs, named so. None of them broadens what else runs.
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest

from scoped_fixture import ShapeCase
from stamp_fixture import commit_all, git

sys.dont_write_bytecode = True

ALWAYS = {
    "check-python": "every check waits on it",
    "check-slice-scope": "it compares the whole branch with its base",
    "check-codegraph": "it reads every tracked file",
}
NO_INPUTS = ("check-agents", "check-speckit", "check-extensions", "check-constitution")
SERVICE = {"lint-service", "typecheck-service", "test-service", "check-openapi"}


class AlwaysTest(ShapeCase):
    def test_e1_a_web_only_change_names_the_seven_and_skips_the_services_units(self) -> None:
        self.edit("apps/web/src/App.tsx")
        run = self.scoped()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        ran, skipped = self.decided(run)
        for unit, reason in ALWAYS.items():
            self.assertEqual(ran[unit], reason, unit)
        for unit in NO_INPUTS:
            self.assertEqual(ran[unit], "no recorded inputs", unit)
        self.assertTrue(set(skipped) >= SERVICE, sorted(SERVICE - set(skipped)))
        (goals,) = self.called()
        self.assertTrue(set(goals) >= set(ALWAYS) | set(NO_INPUTS), goals)
        self.assertFalse(set(goals) & SERVICE, "an always-run check broadened what else runs")

    def test_e1_an_always_run_check_says_its_own_reason_never_a_path(self) -> None:
        self.edit("apps/web/src/App.tsx")
        ran, _ = self.decided(self.scoped())
        self.assertEqual(ran["check-slice-scope"], ALWAYS["check-slice-scope"])
        self.assertEqual(ran["check-codegraph"], ALWAYS["check-codegraph"])

    def test_e1_with_nothing_changed_they_still_run_and_nothing_else_does(self) -> None:
        run = self.scoped()
        ran, skipped = self.decided(run)
        self.assertEqual(set(ran), set(ALWAYS) | set(NO_INPUTS))
        self.assertTrue(skipped, "nothing was skipped")

    def test_e2_a_check_the_project_added_runs_as_having_no_recorded_inputs_and_broadens_nothing(self) -> None:
        git(self.repo, "checkout", "-q", "main")
        makefile = self.repo / "Makefile"
        makefile.write_text(makefile.read_text(encoding="utf-8")
                            + "\nverify-checks: check-licences\ncheck-licences:\n\t@echo licences checked\n",
                            encoding="utf-8")
        commit_all(self.repo, "a check of the project's own")
        git(self.repo, "checkout", "-q", "-B", "slice/S1", "main")
        self.edit("apps/web/src/App.tsx")
        run = self.scoped()
        ran, skipped = self.decided(run)
        self.assertEqual(ran["check-licences"], "no recorded inputs")
        self.assertIn("licences checked", run.stdout)
        self.assertTrue(set(skipped) >= SERVICE, sorted(SERVICE - set(skipped)))

    def test_e3_the_two_that_read_everything_claim_nothing(self) -> None:
        done = subprocess.run(["python3", "-B", "scripts/verify-scoped.py", "record"], cwd=self.repo,
                              env=self.environment(), text=True, capture_output=True, timeout=120)
        checks = json.loads(done.stdout)["checks"]
        for unit in ("check-slice-scope", "check-codegraph"):
            self.assertFalse(checks[unit]["claims"], unit)
            self.assertEqual(checks[unit]["always"], ALWAYS[unit], unit)


if __name__ == "__main__":
    unittest.main()
