"""The base a slice branch is compared with is the trunk's own, by full ref name (S22, D30; R1).

Each test drives `check-slice-scope` through its command line in a temporary repository on `slice/S1`.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from test_slice_scope_root import SliceScopeFixtures, git


class SliceScopeBaseTest(SliceScopeFixtures):
    def run_gate(self, repo: Path) -> subprocess.CompletedProcess:
        quiet = dict.fromkeys(("GITHUB_HEAD_REF", "CI_COMMIT_REF_NAME", "GITHUB_BASE_REF",
                               "CI_MERGE_REQUEST_TARGET_BRANCH_NAME"), "")
        return subprocess.run(["python3", self.script], cwd=repo, text=True, capture_output=True,
                              env={**os.environ, **quiet})

    def commit(self, repo: Path, path: str) -> None:
        (repo / path).parent.mkdir(parents=True, exist_ok=True)
        (repo / path).write_text("x\n")
        git(repo, "add", "--", path)
        git(repo, "commit", "-q", "-m", path)

    def rejects(self, repo: Path, path: str) -> None:
        result = self.run_gate(repo)
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
