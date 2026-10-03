"""A deployable at `.` is the fallback owner of every path no other deployable claims.

An adopted repository records its one application at `.`, and `check-slice-scope` once read that as owning
nothing, so a slice's own tests were refused as *outside every deployable*. These tests run the gate in a real
temporary repository laid out as an adoption leaves one (the delivery material under `delivery/`), on a
`slice/S1` branch, with the deployables the manifest records.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from support import NO_MAINTENANCE, commit_all

from slipwai.assets import ROOT

SCRIPTS = ROOT / "assets/toolkit/scripts"
OUTSIDE = "outside every deployable"
MODEL = """\
schemaVersion: 1
slices:
  - id: S1
    name: Place an order
    pattern: state-change
    status: planned
    actor: Customer
    service: shop
    frames: []
"""


def git(repo: Path, *arguments: str) -> None:
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@local", *NO_MAINTENANCE, *arguments],
                   cwd=repo, capture_output=True, check=True)


class SliceScopeRootTest(unittest.TestCase):
    def repo(self, deployables: dict, model: bool = False) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        repo = Path(directory.name)
        git(repo, "init", "-q", "-b", "main")
        (repo / "project.json").write_text(json.dumps({"deployables": deployables}))
        (repo / "delivery/scripts/event-model").mkdir(parents=True)
        shutil.copy(SCRIPTS / "check-slice-scope.py", repo / "delivery/scripts")
        shutil.copy(SCRIPTS / "event-model/check.py", repo / "delivery/scripts/event-model")
        if model:
            (repo / "delivery/docs/event-model").mkdir(parents=True)
            (repo / "delivery/docs/event-model/model.yaml").write_text(MODEL)
        commit_all(repo, "base")
        git(repo, "checkout", "-q", "-b", "slice/S1")
        return repo

    def verdict(self, repo: Path, path: str) -> subprocess.CompletedProcess:
        target = repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("x\n")
        try:
            return subprocess.run(
                ["python3", "delivery/scripts/check-slice-scope.py"], cwd=repo, text=True, capture_output=True,
                env={**os.environ, "GITHUB_HEAD_REF": "", "CI_COMMIT_REF_NAME": ""},
            )
        finally:
            target.unlink()

    def green(self, repo: Path, *paths: str) -> None:
        for path in paths:
            result = self.verdict(repo, path)
            self.assertEqual(result.returncode, 0, f"{path}: {result.stderr}")
            self.assertIn("touches only what one slice may", result.stdout, path)

    def root(self, path: str = ".") -> dict:
        return {"shop": {"kind": "service", "path": path}}

    def test_the_root_deployable_owns_what_nobody_else_claims(self) -> None:
        """R1 e1-e3: the application's own tests, a sibling directory, root tooling and manifests are the slice's."""
        repo = self.repo(self.root())
        self.green(repo, "tests/test_x.py")
        self.green(repo, "worker/x.py", "scripts/x.py", "docs/x.md")
        self.green(repo, "requirements.txt", "pyproject.toml")

    def test_the_root_may_be_written_with_a_trailing_slash(self) -> None:
        """R1 e4: `./` answers as `.` does."""
        self.green(self.repo(self.root("./")), "tests/test_x.py", "worker/x.py")

    def test_an_empty_path_owns_nothing(self) -> None:
        """R1 e5: a deployable with `path: ""` is no fallback; its file stays outside every deployable."""
        result = self.verdict(self.repo(self.root("")), "tests/test_x.py")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(OUTSIDE, result.stderr)

    def test_a_subdirectory_service_still_owns_its_own_files(self) -> None:
        """R3 e1: the fallback does not outrank `apps/api`, and another service's code is not this slice's."""
        repo = self.repo({**self.root(), "api": {"kind": "service", "path": "apps/api"}}, model=True)
        result = self.verdict(repo, "apps/api/x.py")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("service `api` is not slice `S1`'s", result.stderr)

    def test_the_root_service_still_owns_the_rest_beside_a_subdirectory_one(self) -> None:
        """R3 e2: the same branch, a file the root service owns, is green."""
        repo = self.repo({**self.root(), "api": {"kind": "service", "path": "apps/api"}}, model=True)
        self.green(repo, "tests/test_x.py")


if __name__ == "__main__":
    unittest.main()
