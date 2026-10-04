"""A slice is held on the checkout a forge makes for its pull request (S24, R3; AC-S24-4).

Every test here is a hold: the slice changes no line `check-slice-scope` reads for this, and the checkout the
`verify` job now makes (`tests/forge_checkout.py`: full history, `HEAD` detached on the merge commit, no local
branch) is one it already answers on. Each drives the script's command line.
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any, cast

import test_slice_scope_base as base_tests
from forge_checkout import pull_request_checkout, run
from test_slice_scope_root import SliceScopeFixtures

COMPARED = "compared with `main` at"
GITHUB = {"CI": "true", "GITHUB_ACTIONS": "true", "GITHUB_HEAD_REF": "slice/S1", "GITHUB_BASE_REF": "main"}
GITLAB = {"GITLAB_CI": "true", "CI_COMMIT_REF_NAME": "slice/S1", "CI_MERGE_REQUEST_TARGET_BRANCH_NAME": "main"}
# every way a pull request's checkout is told what it is: each forge's variables, with and without the target,
# and the route with no marker at all (the branch name alone, `HEAD` detached)
ROUTES = {
    "github": GITHUB,
    "github without the target": {k: v for k, v in GITHUB.items() if k != "GITHUB_BASE_REF"},
    "gitlab": GITLAB,
    "gitlab without the target": {k: v for k, v in GITLAB.items() if k != "CI_MERGE_REQUEST_TARGET_BRANCH_NAME"},
    "github head name alone": {"GITHUB_HEAD_REF": "slice/S1"},
    "gitlab ref name alone": {"CI_COMMIT_REF_NAME": "slice/S1"},
}


class SliceScopeForgeTest(SliceScopeFixtures):
    def run_gate(self, repo: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
        return cast(Any, base_tests.SliceScopeBaseTest.run_gate)(self, repo, env)

    def commit(self, repo: Path, path: str) -> None:
        cast(Any, base_tests.SliceScopeBaseTest.commit)(self, repo, path)

    def checkout(self, path: str, depth: int | None = None) -> Path:
        """The pull-request checkout of `slice/S1`, which adds `path` to `main`."""
        origin = self.repo(self.root())
        self.commit(origin, path)
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        return pull_request_checkout(origin, "slice/S1", Path(directory.name), depth=depth)

    def hold_refused(self, clone: Path, env: dict[str, str], path: str = "Makefile") -> None:
        result = self.run_gate(clone, env)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(path, result.stderr)
        self.assertIn(COMPARED, result.stdout + result.stderr)

    def hold_passes(self, clone: Path, env: dict[str, str]) -> None:
        result = self.run_gate(clone, env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("touches only what one slice may", result.stdout)
        self.assertIn(COMPARED, result.stdout)

    def test_hold_the_checkout_is_what_the_workflow_makes(self) -> None:
        """The helper's shape, once: only remote refs, `HEAD` detached on the merge commit, `main` there at full
        history and absent at depth 1."""
        full, shallow = self.checkout("Makefile"), self.checkout("Makefile", depth=1)
        for clone in (full, shallow):
            self.assertEqual(run(clone, "for-each-ref", "refs/heads"), "")
            refs = run(clone, "for-each-ref", "--format=%(refname)", "refs/").splitlines()
            self.assertTrue(all(r.startswith("refs/remotes/origin/") for r in refs), refs)
            detached = subprocess.run(["git", "symbolic-ref", "-q", "HEAD"], cwd=clone, capture_output=True)
            self.assertEqual(detached.returncode, 1, "HEAD is on a branch")
        self.assertEqual(len(run(full, "rev-parse", "HEAD^@").split()), 2, "HEAD is not a merge commit")
        self.assertIn("refs/remotes/origin/main", run(full, "for-each-ref", "--format=%(refname)").splitlines())
        self.assertEqual(run(shallow, "for-each-ref", "--format=%(refname)"), "")
        self.assertEqual(run(shallow, "rev-parse", "--is-shallow-repository"), "true")

    def test_hold_a_host_change_on_github_is_refused(self) -> None:
        """e1."""
        self.hold_refused(self.checkout("Makefile"), GITHUB)

    def test_hold_a_host_change_on_gitlab_is_refused(self) -> None:
        """e2."""
        self.hold_refused(self.checkout("Makefile"), GITLAB)

    def test_hold_a_slice_inside_its_scope_passes_on_both(self) -> None:
        """e3."""
        clone = self.checkout("specs/f/slices/S1/a.md")
        self.hold_passes(clone, GITHUB)
        self.hold_passes(clone, GITLAB)

    def test_hold_every_route_refuses_a_host_change_and_passes_a_slice(self) -> None:
        """The sweep that closes the class: e1 and e3 on each forge's variables, with and without the target,
        and on the route with no marker."""
        refused, inside = self.checkout("Makefile"), self.checkout("specs/f/slices/S1/a.md")
        for name, env in ROUTES.items():
            with self.subTest(route=name, answer="refused"):
                self.hold_refused(refused, env)
            with self.subTest(route=name, answer="passes"):
                self.hold_passes(inside, env)
