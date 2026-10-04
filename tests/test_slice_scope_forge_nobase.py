"""In a forge's checkout, no base is a failure and not a pass (S24, R4 and R6; AC-S24-5, -6, -7, -9, -13; D31, D32).

Each test drives `check-slice-scope` through its command line in a checkout built with git itself — a depth-1
clone, a detached head, an unrelated trunk, a treeless clone whose remote is gone — with `CI`, `GITHUB_ACTIONS`,
`GITLAB_CI` and the branch variables removed unless the test sets that one, so the suite is the same on a runner
that sets `CI=true` and on a laptop.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, cast

import test_slice_scope_hostile_base as hostile
import test_slice_scope_no_base as no_base_tests
from test_slice_scope_root import SliceScopeFixtures, git

OTHER_CI = "on any other CI, a full clone with the trunk's branch fetched from a remote named `origin`"
LOST = "specs/f/plan.md"
ATTACHED = (("GITHUB_ACTIONS", {"GITHUB_ACTIONS": "true"}), ("GITLAB_CI", {"GITLAB_CI": "true"}),
            ("CI", {"CI": "true"}))
DETACHED = (("GITHUB_HEAD_REF", {"GITHUB_HEAD_REF": "slice/S1"}),
            ("CI_COMMIT_REF_NAME", {"CI_COMMIT_REF_NAME": "slice/S1"}))
TARGETS: tuple[dict[str, str], ...] = ({}, {"GITHUB_BASE_REF": "main"}, {"CI_MERGE_REQUEST_TARGET_BRANCH_NAME": "main"})


def git_refs(repo: Path) -> list[str]:
    return no_base_tests.out(repo, "for-each-ref", "--format=%(refname)").splitlines()


class ForgeNoBaseTest(SliceScopeFixtures):
    # Borrowed, so that none of those suites' own tests run a second time here.
    run_gate = cast(Any, no_base_tests.NoBaseTest.run_gate)
    commit = cast(Any, no_base_tests.NoBaseTest.commit)
    origin = cast(Any, no_base_tests.NoBaseTest.origin)
    clone = cast(Any, no_base_tests.NoBaseTest.clone)
    no_ancestor = cast(Any, no_base_tests.NoBaseTest.no_ancestor)
    unrelated_main = cast(Any, no_base_tests.NoBaseTest.unrelated_main)
    orphan_slice = cast(Any, hostile.HostileBaseTest.orphan_slice)
    blind_clone = cast(Any, hostile.CouldNotCompareTest.blind_clone)

    def depth_one(self) -> Path:
        return self.clone(self.origin(), "--depth", "1", "--branch", "slice/S1")

    def unrelated(self) -> Path:
        repo = self.origin()
        self.unrelated_main(repo)
        return repo

    def failed_unchecked(self, repo: Path, env: dict[str, str], trunk: str = "main") -> str:
        """The forge's answer where there is no base: exit 1, nothing on stdout, one stderr line that says what
        to change on either forge and on any other (AC-S24-5, AC-S24-6)."""
        result = self.run_gate(repo, env)
        self.assertEqual(result.returncode, 1, f"{env}: {result.stdout}{result.stderr}")
        self.assertEqual(result.stdout, "", env)
        self.assertEqual(len(result.stderr.splitlines()), 1, result.stderr)
        refs = (f"`refs/heads/{trunk}`", f"`refs/remotes/origin/{trunk}`")  # the two refs it looked for (AC-S24-15)
        for word in ("NOT checked", f"`{trunk}`", "fetch-depth: 0", 'GIT_DEPTH: "0"', OTHER_CI, *refs):
            self.assertIn(word, result.stderr)
        for word in ("git fetch", "nothing to hold"):
            self.assertNotIn(word, result.stderr)
        return result.stderr

    def test_a_full_clone_whose_only_remote_is_upstream_is_told_it_was_not_checked(self) -> None:
        """AC-S24-15: the history is all there, under `refs/remotes/upstream/`; only the two full names answer."""
        origin = self.origin()
        clone = self.clone(origin, "--origin", "upstream", "--no-single-branch", "--branch", "slice/S1")
        self.assertIn("refs/remotes/upstream/main", git_refs(clone))
        self.failed_unchecked(clone, {"CI": "true"})

    def test_a_depth_one_clone_of_the_slice_fails_under_each_marker(self) -> None:
        """e1: the three markers, each alone, `HEAD` attached."""
        for name, env in ATTACHED:
            with self.subTest(marker=name):
                self.failed_unchecked(self.depth_one(), env)

    def test_the_detached_pull_request_route_fails_at_depth_one(self) -> None:
        """e2: the branch name in a variable, no marker, `HEAD` detached."""
        for name, env in DETACHED:
            with self.subTest(variable=name):
                clone = self.depth_one()
                git(clone, "checkout", "-q", "--detach")
                self.failed_unchecked(clone, env)

    def test_a_trunk_with_no_common_ancestor_and_a_target_with_none_fail_under_a_marker(self) -> None:
        """e3: no common ancestor at this depth, an unrelated trunk, and a pull-request target with no history."""
        self.failed_unchecked(self.no_ancestor(), {"CI": "true"})
        self.failed_unchecked(self.unrelated(), {"GITLAB_CI": "true"})
        for target in TARGETS[1:]:
            stderr = self.failed_unchecked(self.orphan_slice(), {"GITHUB_ACTIONS": "true", **target})
            self.assertNotIn("touches only what one slice may", stderr)

    def test_a_passed_over_name_is_still_said_in_the_failure(self) -> None:
        """e3, the words of AC-S22-28 kept: a recorded name with no branch here is said beside the failure."""
        origin = self.repo(self.root(), ci={"branch": "develop"})
        git(origin, "branch", "develop", "main")
        self.commit(origin, "specs/f/slices/S1/a.md")
        clone = self.clone(origin, "--depth", "1", "--branch", "slice/S1")
        stderr = self.failed_unchecked(clone, {"GITHUB_ACTIONS": "true"}, trunk="develop")
        self.assertIn("`ci.branch` names `develop`", stderr)

    def test_every_no_base_state_on_every_route_under_every_marker_fails(self) -> None:
        """The class, closed: each state of no base, on each route, with each target variable, asserted alike."""
        states = {"depth one": self.depth_one, "no ancestor": self.no_ancestor, "unrelated trunk": self.unrelated,
                  "orphan slice": self.orphan_slice}
        routes = [(name, env, False) for name, env in ATTACHED] + [(name, env, True) for name, env in DETACHED]
        for state, build in states.items():
            for route, env, detach in routes:
                for target in TARGETS[1:] if state == "orphan slice" else TARGETS:
                    with self.subTest(state=state, route=route, target=target):
                        repo = build()
                        if detach:
                            git(repo, "checkout", "-q", "--detach")
                        self.failed_unchecked(repo, {**env, **target})

    def test_a_diff_that_cannot_run_fails_under_a_marker(self) -> None:
        """e5: a base and a `git diff` that fails — made with git, a treeless clone whose remote is gone."""
        for _name, env in ATTACHED:
            result = self.run_gate(self.blind_clone(), env)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertIn("NOT checked — git could not compare", result.stderr)
            self.assertIn("fatal:", result.stderr)

    def test_a_lost_record_fails_under_a_marker_with_no_base(self) -> None:
        """e4 (holds): the record and the line, exit 1."""
        repo = self.depth_one()
        (repo / LOST).parent.mkdir(parents=True, exist_ok=True)
        (repo / LOST).write_text("x\n")
        result = self.run_gate(repo, {"CI": "true"})
        self.assertEqual(result.returncode, 1)
        self.assertIn(LOST, result.stderr)
        self.assertIn("NOT checked", result.stderr)

    def test_a_checkout_git_cannot_read_still_exits_0_under_a_marker(self) -> None:
        """e6 (holds): the *could not read* line, exit 0."""
        repo = self.repo(self.root())
        result = self.run_gate(repo, {"CI": "true", "GIT_DIR": str(repo / "nowhere")})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("git could not read this checkout", result.stderr)

    def test_another_branch_has_nothing_to_hold_under_a_marker_with_history_and_without(self) -> None:
        """e7 (holds): not `slice/<id>`, so *nothing to hold*, exit 0."""
        for clone in (self.depth_one(), self.clone(self.origin(), "--no-single-branch")):
            git(clone, "checkout", "-q", "-b", "feature/x")
            for _name, env in ATTACHED:
                result = self.run_gate(clone, env)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("nothing to hold", result.stdout)

    def test_a_usable_base_is_held_exactly_as_on_a_developers_machine(self) -> None:
        """AC-S24-7's last clause: with the marker set and without, a host change fails and a slice file passes."""
        for env in ({}, *(env for _name, env in ATTACHED)):
            with self.subTest(env=env):
                repo = self.origin()
                result = self.run_gate(repo, env)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("touches only what one slice may", result.stdout)
                self.commit(repo, "Makefile")
                result = self.run_gate(repo, env)
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn("Makefile", result.stderr)

    def test_a_developers_checkout_with_no_base_still_fails_with_a_fetch_command(self) -> None:
        """AC-S24-9: no marker and no detached variable route — today's answer, unchanged."""
        repo = self.depth_one()
        result = self.run_gate(repo)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("git fetch origin refs/heads/main:refs/remotes/origin/main", result.stderr)
        self.assertNotIn("NOT checked", result.stderr)
        json.loads((repo / "project.json").read_text(encoding="utf-8"))  # the checkout is untouched and readable
        self.assertEqual(subprocess.run(["git", "status", "--porcelain"], cwd=repo, text=True,
                                        capture_output=True).stdout, "")
