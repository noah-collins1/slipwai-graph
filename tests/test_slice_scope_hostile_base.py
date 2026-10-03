"""A name that cannot be compared with is not a base (S22, D35; T024) and the gate ends in a verdict (T025).

Each test drives `check-slice-scope` through its command line in a temporary repository or in a clone of one.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import test_slice_scope_no_base as no_base_tests
from test_slice_scope_no_base import out
from test_slice_scope_root import SliceScopeFixtures, git

MARKER = {"CI": "true"}
DETACHED = {"CI_COMMIT_REF_NAME": "slice/S1", "GITLAB_CI": "true"}


class HostileBaseTest(SliceScopeFixtures):
    # The helpers, borrowed so that none of `NoBaseTest`'s own tests run a second time here.
    run_gate = cast(Any, no_base_tests.NoBaseTest.run_gate)
    commit = cast(Any, no_base_tests.NoBaseTest.commit)
    origin = cast(Any, no_base_tests.NoBaseTest.origin)
    clone = cast(Any, no_base_tests.NoBaseTest.clone)
    fails_with = cast(Any, no_base_tests.NoBaseTest.fails_with)

    def record(self, repo: Path, value: object) -> None:
        (repo / "project.json").write_text(json.dumps({"deployables": self.root(), "ci": {"branch": value}}))
        git(repo, "commit", "-q", "-am", "record")

    def unrelated_root(self, repo: Path) -> str:
        return out(repo, "commit-tree", out(repo, "hash-object", "-t", "tree", "/dev/null"), "-m", "unrelated")

    def zz_clone(self) -> Path:
        """B1: a full clone with `origin/main`, an unrelated `origin/zz`, and a slice that records `zz`."""
        repo = self.origin()
        git(repo, "update-ref", "refs/heads/zz", self.unrelated_root(repo))
        self.record(repo, "zz")
        self.commit(repo, "Makefile")
        return self.clone(repo, "--no-single-branch")

    def test_a_recorded_name_with_no_common_history_is_passed_over_for_main(self) -> None:
        """B1: attached with no variables, under a marker, and detached with a branch variable."""
        for label, env in (("attached", None), ("marker", MARKER), ("detached", DETACHED)):
            with self.subTest(label):
                clone = self.zz_clone()
                out(clone, "rev-parse", "--verify", "refs/remotes/origin/zz^{commit}")
                if label == "detached":
                    git(clone, "checkout", "-q", "--detach")
                result = self.run_gate(clone, env)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("Makefile", result.stderr)
                self.assertIn("project.json", result.stderr)
                self.assertIn("compared with `main`", result.stderr)
                self.assertIn("`zz`", result.stderr)
                self.assertIn("shares no history", result.stderr)
                self.assertNotIn("NOT checked", result.stderr)

    def orphan_slice(self) -> Path:
        """A1: a slice with no history in common with `main` that records, and has a branch of, `evil`."""
        repo = self.repo(self.root())
        git(repo, "checkout", "-q", "main")
        git(repo, "branch", "-D", "slice/S1")
        git(repo, "checkout", "-q", "--orphan", "slice/S1")
        (repo / "project.json").write_text(json.dumps({"deployables": self.root(), "ci": {"branch": "evil"}}))
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "orphan")
        git(repo, "branch", "evil")
        return repo

    def test_a_target_with_no_common_history_is_no_base_whatever_the_record_names(self) -> None:
        """A1: a developer's checkout fails on the target; a forge's says NOT checked; never the pass line."""
        target = {"GITHUB_BASE_REF": "main"}
        repo = self.orphan_slice()
        self.fails_with(repo, "shares no history with `main`", env=target)
        result = self.run_gate(repo, {**target, **MARKER})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("touches only what one slice may", result.stdout)
        self.assertIn("NOT checked", result.stderr)
