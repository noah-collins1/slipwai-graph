"""What the gate prints says what is true where it is printed (S22, D33 and D34; AC-S22-25, AC-S22-28).

Each test drives `check-slice-scope` through its command line in a temporary repository on `slice/S1`.
"""
from __future__ import annotations

import json
from pathlib import Path

from test_slice_scope_base import SliceScopeBaseTest
from test_slice_scope_no_base import out
from test_slice_scope_root import git

OWN = "specs/f/slices/S1/a.md"
CLAUSE = "`master` is here too and `project.json` records no trunk"
FIX = "set `ci.branch` to `master` in `project.json` on it, or delete the stale `main`"


class MasterBesideMainTest(SliceScopeBaseTest):
    """AC-S22-25: the words, never the base or the exit."""

    def master_ahead(self, own_only: bool = False, ci: dict[str, object] | None = None) -> Path:
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
        (repo / "project.json").write_text(json.dumps({"deployables": self.root(), "ci": {"branch": "a..b"}}))
        git(repo, "commit", "-q", "-am", "record")
        out = self.run_gate(repo).stderr  # `project.json` itself is refused, so the header carries the words
        self.assertIn("`ci.branch` names `a..b`, which is not a branch name; ", out)
        self.assertIn(CLAUSE, out)

    def said_with(self, value: object) -> str:
        """`master` ahead of a stale `main`, `ci.branch` recorded as `value`; everything the gate printed."""
        repo = self.master_ahead(own_only=True, ci={"branch": value})
        result = self.run_gate(repo)
        return result.stdout + result.stderr

    def test_a_usable_recorded_name_with_no_ref_keeps_its_own_sentence_and_no_clause(self) -> None:
        """D33 *where `ci.branch` records nothing usable*: `develop` is usable, so the clause is false there."""
        said = self.said_with("develop")
        self.assertIn("`ci.branch` names `develop`, which has no branch here", said)
        self.assertNotIn("records no trunk", said)

    def test_the_clause_stays_where_nothing_usable_is_recorded(self) -> None:
        for value in (None, 7, "slice/S9"):
            with self.subTest(value=value):
                self.assertIn("records no trunk", self.said_with(value))
        repo = self.master_ahead(own_only=True)  # absent
        self.assertIn("records no trunk", self.run_gate(repo).stdout)


class NoBaseReportTest(SliceScopeBaseTest):
    """AC-S22-28 (G5, G8): a no-base failure is a line of its own, and a forge's output carries no fetch."""

    HEADER = "reaches outside what one slice may touch"

    def no_trunk(self) -> Path:
        repo = self.repo(self.root())
        self.commit(repo, OWN)
        git(repo, "branch", "-D", "main")
        return repo

    def unrelated(self) -> Path:
        repo = self.repo(self.root())
        self.commit(repo, OWN)
        tree = out(repo, "hash-object", "-t", "tree", "/dev/null")
        git(repo, "update-ref", "refs/heads/main", out(repo, "commit-tree", tree, "-m", "x"))
        return repo

    def lose(self, repo: Path) -> None:
        (repo / "specs/f").mkdir(parents=True, exist_ok=True)
        (repo / "specs/f/plan.md").write_text("x\n")

    def test_a_developers_no_base_failure_is_one_line_of_its_own(self) -> None:
        for build, words in ((self.no_trunk, "has no `main` to compare with"), (self.unrelated, "shares no history")):
            with self.subTest(words=words):
                result = self.run_gate(build())
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stdout, "")
                lines = result.stderr.splitlines()
                self.assertEqual(len(lines), 1, result.stderr)
                self.assertTrue(lines[0].startswith(f"check-slice-scope: slice/S1 {words.split(' ')[0]}"), lines[0])
                self.assertIn(words, lines[0])
                self.assertNotIn(self.HEADER, result.stderr)

    def test_a_lost_record_keeps_the_header_and_the_no_base_line_follows_it(self) -> None:
        """Order: the findings under their header first, then the no-base line, forge or developer."""
        for env, words in (({}, "has no `main` to compare with"), ({"CI": "true"}, "was NOT checked")):
            with self.subTest(env=env):
                repo = self.no_trunk()
                self.lose(repo)
                result = self.run_gate(repo, env)
                self.assertEqual(result.returncode, 1)
                lines = result.stderr.splitlines()
                self.assertIn(self.HEADER, lines[0])
                self.assertIn("specs/f/plan.md", result.stderr)
                self.assertIn(words, lines[-1])
                self.assertEqual(sum(words in line for line in lines), 1)

    def test_a_forges_not_checked_output_carries_no_fetch_command(self) -> None:
        """G5: a recorded name with no branch here is passed over, and the note names no `git fetch`."""
        for lost in (False, True):
            with self.subTest(lost=lost):
                repo = self.repo(self.root(), ci={"branch": "develop"})
                git(repo, "branch", "-D", "main")
                if lost:
                    self.lose(repo)
                result = self.run_gate(repo, {"CI": "true"})
                self.assertIn("was NOT checked", result.stderr)
                self.assertIn("`ci.branch` names `develop`, which has no branch here", result.stderr)
                self.assertNotIn("git fetch", result.stdout + result.stderr)
                self.assertEqual(result.returncode, 1 if lost else 0)

    def test_a_lost_record_in_the_unrelated_trunk_state_fails_attached_and_under_a_marker(self) -> None:
        """D32/AC-S22-19: `HEAD` attached, a trunk sharing no history; the findings come first, whoever runs it."""
        for env, words in (({}, "shares no history with `main`"), ({"CI": "true"}, "was NOT checked")):
            with self.subTest(env=env):
                repo = self.unrelated()
                self.lose(repo)
                result = self.run_gate(repo, env)
                self.assertEqual(result.returncode, 1)
                lines = result.stderr.splitlines()
                self.assertIn(self.HEADER, lines[0])
                self.assertIn("specs/f/plan.md", result.stderr)
                self.assertIn(words, lines[-1])

    def test_a_marker_set_to_false_is_still_a_marker(self) -> None:
        """D32 *non-empty*: `CI=false` is how a person says no, and the check reads it as a run that is CI."""
        for marker in ("CI", "GITHUB_ACTIONS", "GITLAB_CI"):
            with self.subTest(marker=marker):
                result = self.run_gate(self.no_trunk(), {marker: "false"})
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertIn("was NOT checked", result.stderr)


class RecordShapeTest(SliceScopeBaseTest):
    """AC-S22-28 (G6, G7): a record that was passed over is said so, in words that are true."""

    def said(self, value: object) -> str:
        repo = self.repo(self.root(), ci={"branch": value})
        self.commit(repo, OWN)
        result = self.run_gate(repo)
        return result.stdout + result.stderr

    def test_a_slice_shaped_name_is_a_slice_branch_never_the_trunk(self) -> None:
        for value in ("slice/S9", "Slice/S9", "refs/heads/slice/S9"):
            with self.subTest(value=value):
                stderr = self.said(value)
                self.assertIn("a slice branch, which is never the trunk", stderr)
                self.assertNotIn("not a branch name", stderr)

    def test_a_record_that_is_not_a_string_is_said_to_be_passed_over(self) -> None:
        for value in (7, 1.5, True, ["main"], {"name": "main"}):
            with self.subTest(value=value):
                stderr = self.said(value)
                self.assertIn("`ci.branch` is not a string, so it was passed over", stderr)
                self.assertNotIn("name", stderr.replace("`ci.branch` is not a string", ""))
                self.assertNotIn("1.5", stderr)

    def test_an_absent_null_or_blank_record_stays_silent(self) -> None:
        for value in (None, "", "  "):
            with self.subTest(value=value):
                self.assertNotIn("passed over", self.said(value))
        repo = self.repo(self.root(), ci={})
        self.commit(repo, OWN)
        self.assertNotIn("passed over", self.run_gate(repo).stdout)


class NamedTrunkTest(SliceScopeBaseTest):
    """AC-S22-1, -2, -11: what the line and the header say they compared with, and which of two refs of one name."""

    def test_an_origin_ahead_of_a_local_main_and_merged_is_the_base(self) -> None:
        """AC-S22-11, the inverse order: `origin/main` fetched past a `main` not pulled; `main`'s files are not ours."""
        repo = self.repo(self.root())
        git(repo, "checkout", "-q", "-b", "fetched", "main")
        self.commit(repo, "Makefile")
        git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
        git(repo, "checkout", "-q", "slice/S1")
        git(repo, "branch", "-q", "-D", "fetched")
        git(repo, "merge", "-q", "--no-edit", "refs/remotes/origin/main")
        self.commit(repo, OWN)
        result = self.run_gate(repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        newer = self.short(repo, "refs/remotes/origin/main")
        self.assertNotEqual(newer, self.short(repo, "refs/heads/main"))
        self.assertIn(f"compared with `main` at {newer}", result.stdout)

    def test_the_header_names_main_in_each_minted_ref_example(self) -> None:
        """AC-S22-1: a `master` branch, an `origin/master`, a tag `main` at the head; the refusal says `main`."""
        minted = (("branch", "-q", "master"), ("update-ref", "refs/remotes/origin/master", "HEAD"),
                  ("tag", "main", "HEAD"))
        for mint in minted:
            with self.subTest(mint=mint):
                repo = self.repo(self.root())
                self.commit(repo, "Makefile")
                git(repo, *mint)
                result = self.run_gate(repo)
                self.assertEqual(result.returncode, 1)
                self.assertIn("compared with `main` at", result.stderr.splitlines()[0])
                self.assertNotIn("compared with `master`", result.stderr)

    def test_the_pass_line_names_the_recorded_trunk_where_it_differs_from_main(self) -> None:
        """AC-S22-2: `trunk` one commit past `main`; the line names `trunk` and the commit it is at, not `main`'s."""
        repo = self.repo(self.root(), ci={"branch": "trunk"})
        self.commit(repo, "Makefile")
        git(repo, "branch", "trunk", "HEAD")
        self.commit(repo, OWN)
        result = self.run_gate(repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotEqual(self.short(repo, "trunk"), self.short(repo, "main"))
        self.assertIn(f"compared with `trunk` at {self.short(repo, 'trunk')}", result.stdout)
