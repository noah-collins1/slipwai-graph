"""The base a slice branch is compared with is the trunk's own, by full ref name (S22, D30; R1).

Each test drives `check-slice-scope` through its command line in a temporary repository on `slice/S1`.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from test_slice_scope_root import SliceScopeFixtures, git


class SliceScopeBaseTest(SliceScopeFixtures):
    def run_gate(self, repo: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
        quiet = dict.fromkeys(("GITHUB_HEAD_REF", "CI_COMMIT_REF_NAME", "GITHUB_BASE_REF",
                               "CI_MERGE_REQUEST_TARGET_BRANCH_NAME", "CI", "GITHUB_ACTIONS", "GITLAB_CI"), "")
        return subprocess.run(["python3", self.script], cwd=repo, text=True, capture_output=True,
                              env={**os.environ, **quiet, **(env or {})})

    def commit(self, repo: Path, path: str) -> None:
        (repo / path).parent.mkdir(parents=True, exist_ok=True)
        (repo / path).write_text("x\n")
        git(repo, "add", "--", path)
        git(repo, "commit", "-q", "-m", path)

    def rejects(self, repo: Path, path: str, env: dict[str, str] | None = None) -> None:
        result = self.run_gate(repo, env)
        self.assertNotEqual(result.returncode, 0, f"{path} was let through")
        self.assertIn(path, result.stderr)

    def passes(self, repo: Path) -> None:
        result = self.run_gate(repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("touches only what one slice may", result.stdout)

    def host_change_at_head(self) -> Path:
        repo = self.repo(self.root())
        self.commit(repo, "Makefile")
        return repo

    def test_a_master_branch_at_head_does_not_empty_the_diff(self) -> None:
        """e1: no recorded trunk, a `master` minted at HEAD."""
        repo = self.host_change_at_head()
        git(repo, "branch", "master")
        self.rejects(repo, "Makefile")

    def test_a_remote_master_at_head_does_not_empty_the_diff(self) -> None:
        """e2: the same with `refs/remotes/origin/master`."""
        repo = self.host_change_at_head()
        git(repo, "update-ref", "refs/remotes/origin/master", "HEAD")
        self.rejects(repo, "Makefile")

    def test_a_tag_named_main_is_not_a_base(self) -> None:
        """e3: the same with a tag `main` at HEAD beside the `main` branch, which a short name loses to."""
        repo = self.host_change_at_head()
        git(repo, "tag", "main", "HEAD")
        self.rejects(repo, "Makefile")

    def test_a_recorded_trunk_is_the_base_and_nothing_minted_replaces_it(self) -> None:
        """e4: `ci.branch: trunk` — own file green; a `main` or `master` minted at HEAD changes nothing."""
        repo = self.repo(self.root(), ci={"branch": "trunk"})
        git(repo, "branch", "trunk")
        self.commit(repo, "specs/f/slices/S1/a.md")
        self.passes(repo)
        self.commit(repo, "Makefile")
        for name in ("main", "master"):
            git(repo, "branch", "-f", name, "HEAD")
            self.rejects(repo, "Makefile")

    def test_a_main_minted_in_a_master_repository_does_not_empty_the_diff(self) -> None:
        """e5: `ci.branch: master`, trunk `master`, a `main` minted at HEAD."""
        repo = self.repo(self.root(), ci={"branch": "master"})
        git(repo, "branch", "master")
        self.commit(repo, "Makefile")
        git(repo, "branch", "-f", "main", "HEAD")
        self.rejects(repo, "Makefile")

    def test_an_older_master_left_behind_does_not_change_the_answer(self) -> None:
        """e6, held: `main` and an older `master`, nothing minted."""
        repo = self.repo(self.root())
        git(repo, "branch", "master")
        self.commit(repo, "specs/f/slices/S1/a.md")
        self.passes(repo)
        self.commit(repo, "Makefile")
        self.rejects(repo, "Makefile")


class RecordedNameTest(SliceScopeBaseTest):
    """R2: the record's name is read tolerantly and is never a slice's."""

    def record(self, repo: Path, value: object, commit: bool = True) -> None:
        (repo / "project.json").write_text(json.dumps({"deployables": self.root(), "ci": {"branch": value}}))
        if commit:
            git(repo, "commit", "-q", "-am", "record")

    def test_a_slice_name_is_never_the_base(self) -> None:
        """e1 committed, e2 uncommitted, e3 with a `slice/S9` branch at HEAD: `project.json` is refused."""
        for committed, minted in ((True, False), (False, False), (True, True)):
            with self.subTest(committed=committed, minted=minted):
                repo = self.repo(self.root())
                self.record(repo, "slice/S9" if minted else "slice/S1", commit=committed)
                if minted:
                    git(repo, "branch", "slice/S9", "HEAD")
                self.rejects(repo, "project.json")

    def test_a_slice_name_in_another_case_is_never_the_base(self) -> None:
        """A case-insensitive filesystem makes `Slice/S1` the slice's own ref; a distinct ref at HEAD stands in."""
        for name in ("Slice/S1", "SLICE/s1"):
            with self.subTest(name=name):
                repo = self.repo(self.root())
                self.record(repo, name)
                git(repo, "branch", name, "HEAD")
                self.rejects(repo, "project.json")

    def test_a_name_with_no_ref_is_passed_over_and_said_so(self) -> None:
        """e4: `nowhere` has no branch; `main` answers and the output says `nowhere` was passed over."""
        repo = self.repo(self.root())
        self.record(repo, "nowhere")
        result = self.run_gate(repo)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("project.json", result.stderr)
        self.assertIn("`ci.branch` names `nowhere`, which has no branch here", result.stderr)
        self.assertIn("git fetch origin nowhere", result.stderr)

    def test_the_bases_own_record_naming_an_absent_trunk_is_said_on_the_pass_line(self) -> None:
        """e7: the base records `develop`, which has no ref here; the slice's own file is green against `main`."""
        repo = self.repo(self.root(), ci={"branch": "develop"})
        self.commit(repo, "specs/f/slices/S1/a.md")
        result = self.run_gate(repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("touches only what one slice may", result.stdout)
        self.assertIn("`ci.branch` names `develop`, which has no branch here", result.stdout)
        self.assertIn("`git fetch origin develop`", result.stdout)

    def test_a_full_ref_name_reads_as_the_branch(self) -> None:
        """e6: `refs/heads/trunk` is `trunk`; a `main` minted at HEAD does not replace it."""
        repo = self.repo(self.root(), ci={"branch": "refs/heads/trunk"})
        git(repo, "branch", "trunk")
        self.passes(repo)
        self.commit(repo, "Makefile")
        git(repo, "branch", "-f", "main", "HEAD")
        self.rejects(repo, "Makefile")

    def test_an_unusable_name_gets_a_verdict_against_main_not_a_traceback(self) -> None:
        """e5, held: a value of any shape, `main` answers; a string says it is not a branch name."""
        for value in (7, ["main"], "", "  ", "-x", "refs/tags/main"):
            with self.subTest(value=value):
                repo = self.host_change_at_head()
                self.record(repo, value)
                result = self.run_gate(repo)
                self.assertNotIn("Traceback", result.stderr)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Makefile", result.stderr)
        repo = self.repo(self.root())
        self.record(repo, "-x")
        self.assertIn("`ci.branch` names `-x`, which is not a branch name", self.run_gate(repo).stderr)


class ForgeTargetTest(SliceScopeBaseTest):
    """R3: the forge's target is a second candidate, and across two names the older base wins."""

    TARGETS = ("GITHUB_BASE_REF", "CI_MERGE_REQUEST_TARGET_BRANCH_NAME")

    def test_the_target_outranks_a_recorded_name_minted_at_head(self) -> None:
        """e1, e2: `ci.branch: evil` with `evil` at HEAD; the target is `main`, so `project.json` is refused."""
        for variable in self.TARGETS:
            with self.subTest(variable=variable):
                repo = self.repo(self.root())
                (repo / "project.json").write_text(json.dumps({"deployables": self.root(), "ci": {"branch": "evil"}}))
                git(repo, "commit", "-q", "-am", "record")
                git(repo, "update-ref", "refs/remotes/origin/evil", "HEAD")
                self.rejects(repo, "project.json", {variable: "main"})

    def test_the_target_outranks_a_main_minted_beside_a_master_trunk(self) -> None:
        """e3: `master` is the trunk, `GITHUB_BASE_REF=master`, `refs/remotes/origin/main` minted at HEAD."""
        repo = self.repo(self.root())
        git(repo, "branch", "master")
        git(repo, "branch", "-D", "main")
        self.commit(repo, "Makefile")
        git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
        self.rejects(repo, "Makefile", {"GITHUB_BASE_REF": "master"})

    def test_a_target_ahead_of_main_moves_the_base_back_to_main(self) -> None:
        """e4: `feature` is cut from `main` and ahead of it; the slice is cut from `feature`."""
        repo = self.repo(self.root())
        git(repo, "checkout", "-q", "-b", "feature")
        self.commit(repo, "Makefile")
        git(repo, "checkout", "-q", "slice/S1")
        git(repo, "reset", "-q", "--hard", "feature")
        self.rejects(repo, "Makefile", {"GITHUB_BASE_REF": "feature"})

    def test_a_target_with_no_ref_or_no_name_is_ignored(self) -> None:
        """e5, held: the recorded trunk answers; `nowhere` has no ref, `-x` is no name."""
        for target in ("nowhere", "-x", "slice/S1", "refs/tags/main"):
            with self.subTest(target=target):
                repo = self.repo(self.root())
                self.commit(repo, "specs/f/slices/S1/a.md")
                self.passes(repo)
                self.commit(repo, "Makefile")
                self.rejects(repo, "Makefile", {"GITHUB_BASE_REF": target})

    def test_a_target_naming_a_slice_in_another_case_is_ignored(self) -> None:
        """Both variables, `Slice/S1` at HEAD and no trunk branch at all: the target alone would be the base."""
        for variable in self.TARGETS:
            with self.subTest(variable=variable):
                repo = self.repo(self.root())
                self.commit(repo, "Makefile")
                git(repo, "branch", "Slice/S1", "HEAD")
                git(repo, "branch", "-D", "main")
                result = self.run_gate(repo, {variable: "Slice/S1"})
                self.assertNotEqual(result.returncode, 0, "the slice's own ref was taken as the base")
                self.assertIn("has no `main` to compare with", result.stderr)


class ReportTest(SliceScopeBaseTest):
    """R4: the line says which trunk and which commit were compared."""

    def short(self, repo: Path, ref: str) -> str:
        return subprocess.run(["git", "rev-parse", "--short", ref], cwd=repo, text=True, capture_output=True,
                              check=True).stdout.strip()

    def test_the_pass_line_names_the_trunk_and_the_base_commit(self) -> None:
        """e1: the words before the bracket are unchanged."""
        repo = self.repo(self.root())
        self.commit(repo, "specs/f/slices/S1/a.md")
        line = self.run_gate(repo).stdout.strip()
        self.assertEqual(line, "check-slice-scope: slice/S1 touches only what one slice may "
                               f"(compared with `main` at {self.short(repo, 'main')})")
        self.assertRegex(line, r"at [0-9a-f]{7,}\)$")

    def test_the_refusal_header_ends_with_what_was_compared(self) -> None:
        """e2: the header names the trunk and the short commit."""
        repo = self.repo(self.root())
        self.commit(repo, "Makefile")
        header = self.run_gate(repo).stderr.splitlines()[0]
        self.assertTrue(header.startswith("check-slice-scope: a slice branch reaches outside what one slice may touch"))
        self.assertTrue(header.endswith(f" — compared with `main` at {self.short(repo, 'main')}"), header)
