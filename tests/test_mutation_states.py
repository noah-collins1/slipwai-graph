"""S08 T032 (G7, AC-S08-14, AC-S08-15): what the criteria say and no example held — the stamp and the adopted layout.

A stamp written for the tree stands after `make mutation` has run (the gate reuses it and starts no check), and the
scoped gate's choice from a scoped baseline is the choice it made before the run, not a wider one. `make mutation` is
the real target here, run with the machine's own tools; the changed file is a test, so no mutation tool starts.
"""
from __future__ import annotations

import subprocess

from scoped_fixture import ShapeCase
from stamp_fixture import git
from test_mutation_borders import clean_environment

TEST_FILE = "apps/service/health/zz_test.go"
DRY: dict[str, str | None] = {"STANDIN_DRY": "1"}


class StampStatesTest(ShapeCase):
    shape = "go-web"

    def make_mutation(self) -> None:
        done = subprocess.run(["make", "mutation"], cwd=self.repo, env=clean_environment(), text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
        self.assertEqual(done.returncode, 0, done.stdout[-2000:])
        self.assertIn("mutation: no mutant to run — only tests changed", done.stdout)

    def test_ac14_a_stamp_written_for_the_tree_is_reused_after_make_mutation(self) -> None:
        self.edit(TEST_FILE, "package health\n")
        written = self.plant_stamp()
        self.make_mutation()
        self.assertEqual(self.stamp_path().read_bytes(), written)  # type: ignore[union-attr]
        self.forget_log()
        run = self.run_gate()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue(self.reuse_lines(run), run.stdout)
        self.assertEqual(self.checks(), [], "a check started although a stamp stood")

    def test_ac14_the_scoped_gate_chooses_from_a_scoped_baseline_as_it_did_before_make_mutation(self) -> None:
        self.edit("apps/service/main.go", "\n// an edit\n")
        before = self.scoped(DRY)
        self.assertEqual(before.returncode, 0, before.stdout + before.stderr)
        self.assertNotIn("the full gate runs", before.stdout + before.stderr)
        self.reset()
        self.edit(TEST_FILE, "package health\n")  # only a test: `make mutation` starts no tool
        baseline, ignored = self.baseline_file().read_bytes(), git(self.repo, "status", "--porcelain", "--ignored")
        self.make_mutation()
        self.assertEqual(self.baseline_file().read_bytes(), baseline, "the scoped baseline moved")
        self.assertEqual(git(self.repo, "status", "--porcelain", "--ignored"), ignored, "a file appeared or went")
        self.reset()
        self.edit("apps/service/main.go", "\n// an edit\n")
        after = self.scoped(DRY)
        self.assertEqual(self.scoped_lines(after), self.scoped_lines(before), after.stdout + after.stderr)
