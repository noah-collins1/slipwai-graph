"""A slice branch with no base to compare with is not let through as *nothing to hold* (S22, D31; R5).

Each test drives `check-slice-scope` through its command line in a temporary repository or in a clone of one;
`--depth` and single-branch need `file://` — a plain path clone ignores both.
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any, cast

import test_slice_scope_base as base_tests
from test_slice_scope_root import SliceScopeFixtures, git

FETCH_MAIN = "git fetch origin main"
LOST = "specs/f/plan.md"


def out(repo: Path, *arguments: str) -> str:
    return subprocess.run(["git", *arguments], cwd=repo, text=True, capture_output=True, check=True).stdout.strip()


class NoBaseTest(SliceScopeFixtures):
    def run_gate(self, repo: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
        return cast(Any, base_tests.SliceScopeBaseTest.run_gate)(self, repo, env)

    def commit(self, repo: Path, path: str) -> None:
        cast(Any, base_tests.SliceScopeBaseTest.commit)(self, repo, path)

    def origin(self) -> Path:
        """`main` at its first commit, and `slice/S1` one commit of its own ahead of it."""
        repo = self.repo(self.root())
        self.commit(repo, "specs/f/slices/S1/a.md")
        return repo

    def clone(self, origin: Path, *options: str) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        target = Path(directory.name) / "clone"
        url = f"file://{origin}"
        subprocess.run(["git", "clone", "-q", *options, url, str(target)], check=True, capture_output=True)
        return target

    def fails_with(self, repo: Path, *words: str, env: dict[str, str] | None = None) -> str:
        result = self.run_gate(repo, env)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertNotIn("nothing to hold", result.stdout + result.stderr)
        self.assertIn("reaches outside what one slice may touch", result.stderr)
        for word in words:
            self.assertIn(word, result.stderr)
        return result.stderr

    def test_a_single_branch_shallow_clone_is_told_which_ref_to_fetch(self) -> None:
        """e1: `--depth 1 --branch slice/S1` fetches no trunk ref at all."""
        clone = self.clone(self.origin(), "--depth", "1", "--branch", "slice/S1")
        self.assertEqual(out(clone, "rev-parse", "--is-shallow-repository"), "true")
        self.assertEqual(out(clone, "for-each-ref", "refs/remotes/origin/main", "refs/heads/main"), "")
        self.fails_with(clone, "`main`", FETCH_MAIN)

    def test_a_repository_whose_only_branch_is_the_slice_is_told_the_same(self) -> None:
        """e2: a full repository, `main` deleted."""
        repo = self.origin()
        git(repo, "branch", "-D", "main")
        self.fails_with(repo, "`main`", FETCH_MAIN)

    def test_a_shallow_clone_with_no_common_ancestor_is_told_to_unshallow(self) -> None:
        """e3: `origin/main` at depth 1 and the slice's own commit above it: no ancestor in depth."""
        clone = self.clone(self.origin(), "--depth", "1", "--no-single-branch", "--branch", "slice/S1")
        self.assertEqual(out(clone, "rev-parse", "--verify", "refs/remotes/origin/main^{commit}"),
                         out(self.origin_of(clone), "rev-parse", "main"))
        self.fails_with(clone, "shares no history with `main` at this depth", "git fetch --unshallow origin")

    def origin_of(self, clone: Path) -> Path:
        return Path(out(clone, "remote", "get-url", "origin").removeprefix("file://"))

    def test_an_unrelated_trunk_is_not_a_slice_branchs_trunk(self) -> None:
        """e4: a full repository whose `main` is an unrelated root."""
        repo = self.origin()
        root = out(repo, "commit-tree", out(repo, "hash-object", "-t", "tree", "/dev/null"), "-m", "unrelated")
        git(repo, "update-ref", "refs/heads/main", root)
        stderr = self.fails_with(repo, "a slice branch is cut from `main`")
        self.assertNotIn("git fetch", stderr)

    def test_a_variable_cannot_buy_the_pass_while_head_is_attached(self) -> None:
        """e5: `GITHUB_HEAD_REF` set, `HEAD` on the branch, no base: a developer's checkout."""
        repo = self.origin()
        git(repo, "branch", "-D", "main")
        self.fails_with(repo, FETCH_MAIN, env={"GITHUB_HEAD_REF": "slice/S1"})

    def test_a_lost_record_is_printed_with_the_missing_base(self) -> None:
        """e6: the untracked regular file at a canonical slot is reported beside the base line."""
        for build, words in ((self.no_trunk_ref, FETCH_MAIN), (self.no_ancestor, "shares no history")):
            repo = build()
            (repo / LOST).parent.mkdir(parents=True, exist_ok=True)
            (repo / LOST).write_text("x\n")
            self.fails_with(repo, LOST, "the record is about to be lost", words)

    def no_trunk_ref(self) -> Path:
        repo = self.origin()
        git(repo, "branch", "-D", "main")
        return repo

    def no_ancestor(self) -> Path:
        return self.clone(self.origin(), "--depth", "1", "--no-single-branch", "--branch", "slice/S1")

    def test_a_target_with_a_ref_is_the_base_where_the_trunk_has_none(self) -> None:
        """D30, *the forge's word*: no trunk ref, a usable target that has one — held against it, not failed."""
        repo = self.origin()
        git(repo, "branch", "develop", "main")
        git(repo, "branch", "-D", "main")
        result = self.run_gate(repo, {"GITHUB_BASE_REF": "develop"})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("compared with `develop`", result.stdout)
        self.commit(repo, "Makefile")
        self.base_rejects(repo, "Makefile", {"GITHUB_BASE_REF": "develop"})

    def base_rejects(self, repo: Path, path: str, env: dict[str, str]) -> None:
        result = self.run_gate(repo, env)
        self.assertEqual(result.returncode, 1)
        self.assertIn(path, result.stderr)

    def test_the_fetch_named_is_the_targets_then_the_recorded_trunk_then_main(self) -> None:
        """D30: the name the line tells a person to fetch."""
        repo = self.no_trunk_ref()
        self.fails_with(repo, "git fetch origin release", env={"GITHUB_BASE_REF": "release"})
        recorded = self.repo(self.root(), ci={"branch": "trunk"})
        git(recorded, "branch", "-D", "main")
        self.fails_with(recorded, "git fetch origin trunk")

    def test_a_forge_detached_checkout_keeps_answering_as_it_did(self) -> None:
        """Held until the forge's own line lands: detached `HEAD` and the variable, no base, exit 0."""
        repo = self.no_trunk_ref()
        git(repo, "checkout", "-q", "--detach")
        result = self.run_gate(repo, {"GITHUB_HEAD_REF": "slice/S1"})
        self.assertEqual(result.returncode, 0, result.stderr)
