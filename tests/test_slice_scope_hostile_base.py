"""A name that cannot be compared with is not a base (S22, D35; T024) and the gate ends in a verdict (T025).

Each test drives `check-slice-scope` through its command line in a temporary repository or in a clone of one.
"""
from __future__ import annotations

import json
import os
import subprocess
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
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertNotIn("touches only what one slice may", result.stdout)
        self.assertIn("NOT checked", result.stderr)


class HostileInputTest(SliceScopeFixtures):
    """T025: whatever the gate is given, it ends in a verdict, within seconds, and never on a traceback."""

    def gate(self, repo: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
        quiet = dict.fromkeys(("GITHUB_HEAD_REF", "CI_COMMIT_REF_NAME", "GITHUB_BASE_REF",
                               "CI_MERGE_REQUEST_TARGET_BRANCH_NAME", "CI", "GITHUB_ACTIONS", "GITLAB_CI"), "")
        try:
            result = subprocess.run(["python3", self.script], cwd=repo, text=True, capture_output=True, timeout=30,
                                    stdin=subprocess.DEVNULL, env={**os.environ, **quiet, **(env or {})})
        except subprocess.TimeoutExpired:
            self.fail("the gate did not end: it was reading something that never ends")
        self.assertNotIn("Traceback", result.stderr)
        return result

    def verdict_against_main(self, repo: Path, env: dict[str, str] | None = None) -> None:
        result = self.gate(repo, env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("compared with `main`", result.stdout)

    def test_a_nul_or_a_lone_surrogate_in_the_recorded_name_is_a_verdict_against_main(self) -> None:
        """A2: the name reaches `git` as an argument, and Python refuses to hand it over."""
        for value in ("a\u0000b", "a\ud800b"):
            with self.subTest(value=ascii(value)):
                repo = self.repo(self.root(), ci={"branch": value})
                self.verdict_against_main(repo)

    def test_a_pipe_or_a_device_is_not_read_as_the_record_or_the_model(self) -> None:
        """A3: `project.json` and `model.yaml` as a symlink to `/dev/zero` and to a FIFO."""
        if not Path("/dev/zero").exists():
            self.skipTest("no /dev/zero here")
        for name in ("project.json", "delivery/docs/event-model/model.yaml"):
            for kind in ("device", "fifo"):
                with self.subTest(name=name, kind=kind):
                    repo = self.repo(self.root(), model=True)
                    (repo / name).unlink()
                    if kind == "device":
                        (repo / name).symlink_to("/dev/zero")
                    else:
                        os.mkfifo(repo / name)
                    self.assertIn(self.gate(repo).returncode, (0, 1))

    def test_a_file_over_the_cap_is_not_read(self) -> None:
        """A3: a `project.json` naming `develop`, padded past the cap, reads as nothing: `main` is the base."""
        repo = self.repo(self.root())
        git(repo, "branch", "develop", "main")
        (repo / "project.json").write_text(json.dumps({"ci": {"branch": "develop"}}) + " " * (8 * 1024 * 1024 + 1))
        result = self.gate(repo)
        self.assertIn("compared with `main`", result.stdout + result.stderr)

    def test_a_checkout_git_cannot_read_exits_0_and_says_so_without_a_word_about_history(self) -> None:
        """B4: `GIT_DIR` pointing nowhere, on any branch name, with and without a marker."""
        for env in ({}, {"CI": "true"}, {"CI_COMMIT_REF_NAME": "slice/S1"}, {"CI_COMMIT_REF_NAME": "feature/x"},
                    {"GITHUB_HEAD_REF": "slice/S1", "GITHUB_ACTIONS": "true"}):
            with self.subTest(env=env):
                repo = self.repo(self.root())
                result = self.gate(repo, {**env, "GIT_DIR": str(repo / "nowhere")})
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(len(result.stderr.splitlines()), 1, result.stderr)
                self.assertIn("git could not read this checkout", result.stderr)
                self.assertIn("fatal:", result.stderr)
                for word in ("branch", "history", "fetch-depth", "NOT checked"):
                    self.assertNotIn(word, result.stderr)


class CouldNotCompareTest(SliceScopeFixtures):
    run_gate = cast(Any, no_base_tests.NoBaseTest.run_gate)
    commit = cast(Any, no_base_tests.NoBaseTest.commit)
    origin = cast(Any, no_base_tests.NoBaseTest.origin)
    clone = cast(Any, no_base_tests.NoBaseTest.clone)
    """T026 (B2): where a base was found and git cannot produce the diff, the gate never says the slice passed."""

    def blind_clone(self) -> Path:
        """A treeless partial clone whose remote is gone: `merge-base` works on the commits it has, `git diff` needs
        the base's tree and cannot fetch it — B2's own reproduction, with a `file://` origin and no network."""
        origin = self.origin()
        git(origin, "config", "uploadpack.allowfilter", "true")
        clone = self.clone(origin, "--filter=tree:0", "--branch", "slice/S1")
        git(clone, "remote", "set-url", "origin", "file:///gone")
        return clone

    def test_a_diff_that_cannot_run_fails_a_developer_in_one_line_naming_the_base_and_gits_own_words(self) -> None:
        clone = self.blind_clone()
        short = out(clone, "rev-parse", "--short", "origin/main")
        result = self.run_gate(clone)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertNotIn("touches only what one slice may", result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(len(result.stderr.splitlines()), 1, result.stderr)
        for word in ("`main`", short, "fatal:", "/gone"):
            self.assertIn(word, result.stderr)

    def test_under_a_marker_the_slice_is_not_checked_and_the_reason_is_gits(self) -> None:
        for env in (MARKER, DETACHED):
            with self.subTest(env=env):
                result = self.run_gate(self.blind_clone(), env)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertNotIn("touches only what one slice may", result.stdout + result.stderr)
                self.assertIn("NOT checked", result.stderr)
                self.assertIn("fatal:", result.stderr)
