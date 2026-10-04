"""A pull request's target keeps the base from moving to a branch the slice chose (S24, D87 F1; AC-S24-14).

Each test drives `check-slice-scope` on the checkout a forge makes (`tests/forge_checkout.py`) and reads the line
it prints: the commit it says it compared with is never newer than the target's base.
"""
from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any, cast

import test_slice_scope_base as base_tests
from forge_checkout import pull_request_checkout, run
from test_slice_scope_forge import COMPARED, GITHUB, GITLAB
from test_slice_scope_root import SliceScopeFixtures


class SliceScopeForgeHostileTest(SliceScopeFixtures):
    def run_gate(self, repo: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
        return cast(Any, base_tests.SliceScopeBaseTest.run_gate)(self, repo, env)

    def commit(self, repo: Path, path: str) -> None:
        cast(Any, base_tests.SliceScopeBaseTest.commit)(self, repo, path)

    def record_evil(self, origin: Path, record: bool = True) -> None:
        """On `slice/S1`: record `ci.branch: evil` (unless `main` already does), and merge an orphan root carrying
        the slice's own tree, as branch `evil`."""
        if record:
            document = json.loads((origin / "project.json").read_text())
            (origin / "project.json").write_text(json.dumps({**document, "ci": {"branch": "evil"}}))
            run(origin, "commit", "-q", "-am", "record evil")
        run(origin, "checkout", "-q", "--orphan", "evil")
        run(origin, "commit", "-q", "-m", "orphan root with the slice's tree")
        run(origin, "checkout", "-q", "slice/S1")
        run(origin, "merge", "-q", "--no-ff", "--allow-unrelated-histories", "-m", "take evil", "evil")

    def evil_checkout(self, path: str) -> Path:
        origin = self.repo(self.root())
        self.commit(origin, path)
        self.record_evil(origin)
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        return pull_request_checkout(origin, "slice/S1", Path(directory.name))

    def test_an_unrelated_branch_the_slice_chose_does_not_stand_in_for_the_target(self) -> None:
        """e1: the slice's own `evil` shares no history with `main`; the pull request's target does."""
        clone = self.evil_checkout("Makefile")
        for env in (GITHUB, GITLAB):
            result = self.run_gate(clone, env)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("Makefile", result.stderr)
            self.assertIn("project.json", result.stderr)
            self.assertIn(COMPARED, result.stdout + result.stderr)
            self.assertNotIn("compared with `evil`", result.stdout + result.stderr)

    def test_the_same_refs_on_a_slice_inside_its_scope_pass(self) -> None:
        """e2: `main` records `evil`; the slice touches only its own files and merges the orphan root."""
        origin = self.repo(self.root(), ci={"branch": "evil"})
        self.commit(origin, "specs/f/slices/S1/a.md")
        self.record_evil(origin, record=False)
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        clone = pull_request_checkout(origin, "slice/S1", Path(directory.name))
        for env in (GITHUB, GITLAB):
            result = self.run_gate(clone, env)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("touches only what one slice may", result.stdout)
            self.assertIn(COMPARED, result.stdout)

    def test_the_commit_compared_with_is_never_newer_than_the_targets_base(self) -> None:
        """The class (AC-S24-14): wherever a pull request's target is usable and has a base, the commit the line
        names is that base or an ancestor of it — the recorded trunk older, the target older, both level, and the
        recorded name unrelated to the target."""
        for shape in ("trunk older", "target older", "level", "unrelated"):
            with self.subTest(shape=shape):
                clone, target = self.shaped(shape)
                result = self.run_gate(clone, {**GITHUB, "GITHUB_BASE_REF": target})
                said = re.search(r"compared with `[^`]+` at ([0-9a-f]+)", result.stdout + result.stderr)
                self.assertIsNotNone(said, result.stdout + result.stderr)
                assert said is not None
                target_base = run(clone, "merge-base", "HEAD", f"refs/remotes/origin/{target}")
                ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", said.group(1), target_base],
                                          cwd=clone)
                self.assertEqual(ancestor.returncode, 0, f"{said.group(1)} is newer than {target_base}")

    def shaped(self, shape: str) -> tuple[Path, str]:
        """A pull-request checkout of the shape, and the name of the pull request's target."""
        origin = self.repo(self.root(), ci={"branch": "trunk"} if shape == "trunk older" else {})
        run(origin, "checkout", "-q", "main")
        run(origin, "branch", "old")
        self.commit(origin, "later.md")
        run(origin, "branch", "-f", "release", "old" if shape == "target older" else "main")
        run(origin, "checkout", "-q", "-b", "slice/S2", "main")
        run(origin, "branch", "-D", "slice/S1")
        run(origin, "branch", "-m", "slice/S1")
        self.commit(origin, "Makefile")
        if shape == "trunk older":
            run(origin, "branch", "trunk", "old")
        if shape == "unrelated":
            (origin / "project.json").write_text('{"deployables": {"shop": {"kind": "service", "path": "."}}, '
                                                 '"ci": {"branch": "evil"}}')
            run(origin, "commit", "-q", "-am", "record evil")
            self.record_evil(origin, record=False)
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        target = "release" if shape == "target older" else "main"
        return pull_request_checkout(origin, "slice/S1", Path(directory.name), base=target), target
