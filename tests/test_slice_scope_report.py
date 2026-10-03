"""What the gate prints says what is true where it is printed (S22, D33 and D34; AC-S22-25, AC-S22-28).

Each test drives `check-slice-scope` through its command line in a temporary repository on `slice/S1`.
"""
from __future__ import annotations

import json
from pathlib import Path

from test_slice_scope_base import SliceScopeBaseTest
from test_slice_scope_root import git

OWN = "specs/f/slices/S1/a.md"
CLAUSE = "`master` is here too and `project.json` records no trunk"
FIX = "set `ci.branch` to `master` in `project.json` on it, or delete the stale `main`"


class MasterBesideMainTest(SliceScopeBaseTest):
    """AC-S22-25: the words, never the base or the exit."""

    def master_ahead(self, own_only: bool = False, ci: dict[str, str] | None = None) -> Path:
        """`master` one commit past `main`, holding its own host file; the slice is cut from `master`."""
        repo = self.repo(self.root(), ci=ci) if ci else self.repo(self.root())
        self.commit(repo, OWN if own_only else "Makefile")
        git(repo, "branch", "master", "HEAD")
        self.commit(repo, OWN + ".more")
        return repo

    def test_a_master_trunk_ahead_of_a_stale_main_is_told_what_to_record(self) -> None:
        """Refusal: the header says `master` is here, no trunk is recorded, and the fix; the base stays `main`'s."""
        repo = self.master_ahead()
        result = self.run_gate(repo)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("Makefile", result.stderr)
        header = result.stderr.splitlines()[0]
        self.assertIn(f"compared with `main` at {self.short(repo, 'main')}", header)
        self.assertIn(CLAUSE, header)
        self.assertIn(FIX, header)

    def test_the_pass_line_carries_the_clause_too(self) -> None:
        repo = self.master_ahead(own_only=True)
        result = self.run_gate(repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"compared with `main` at {self.short(repo, 'main')}", result.stdout)
        self.assertIn(CLAUSE, result.stdout)
        self.assertIn(FIX, result.stdout)

    def test_recording_master_makes_the_slice_green_against_it_without_the_clause(self) -> None:
        repo = self.master_ahead(ci={"branch": "master"})
        result = self.run_gate(repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("compared with `master`", result.stdout)
        self.assertNotIn("is here too", result.stdout + result.stderr)

    def test_a_master_minted_at_the_head_leaves_the_refusal_and_the_base(self) -> None:
        """AC-S22-1's repository: the clause may appear; the base and the exit are as before."""
        repo = self.repo(self.root())
        self.commit(repo, "Makefile")
        git(repo, "branch", "master")
        result = self.run_gate(repo)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Makefile", result.stderr)
        self.assertIn(f"compared with `main` at {self.short(repo, 'main')}", result.stderr)

    def test_an_older_master_left_behind_has_no_clause(self) -> None:
        """AC-S22-12's repository: `main` moved on, `master` stayed at the first commit. Teeth: *strictly newer*."""
        repo = self.repo(self.root())
        git(repo, "branch", "master")
        git(repo, "checkout", "-q", "main")
        self.commit(repo, "specs/f/slices/S1/m.md")
        git(repo, "checkout", "-q", "slice/S1")
        git(repo, "merge", "-q", "--no-edit", "main")
        self.commit(repo, "Makefile")
        result = self.run_gate(repo)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("is here too", result.stderr)

    def test_a_master_with_the_same_base_has_no_clause(self) -> None:
        repo = self.repo(self.root())
        git(repo, "branch", "master")
        self.commit(repo, OWN)
        self.assertNotIn("is here too", self.run_gate(repo).stdout)

    def test_a_usable_recorded_trunk_with_a_ref_has_no_clause(self) -> None:
        repo = self.master_ahead(ci={"branch": "main"})
        self.assertNotIn("is here too", self.run_gate(repo).stderr)
        repo = self.master_ahead(ci={"branch": "other"})
        git(repo, "branch", "other", "main")
        self.assertNotIn("is here too", self.run_gate(repo).stderr)

    def test_the_clause_joins_the_passed_over_words(self) -> None:
        repo = self.master_ahead(own_only=True)
        (repo / "project.json").write_text(json.dumps({"deployables": self.root(), "ci": {"branch": "nowhere"}}))
        git(repo, "commit", "-q", "-am", "record")
        out = self.run_gate(repo).stderr  # `project.json` itself is refused, so the header carries the words
        self.assertIn("`ci.branch` names `nowhere`", out)
        self.assertIn(CLAUSE, out)
