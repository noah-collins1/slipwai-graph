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
from test_adopt import repository, slipwai

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
    def repo(self, deployables: dict, model: bool = False, written: str | None = None, **project: object) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        repo = Path(directory.name)
        git(repo, "init", "-q", "-b", "main")
        (repo / "project.json").write_text(json.dumps({"deployables": deployables, **project}))
        (repo / "delivery/scripts/event-model").mkdir(parents=True)
        shutil.copy(SCRIPTS / "check-slice-scope.py", repo / "delivery/scripts")
        shutil.copy(SCRIPTS / "event-model/check.py", repo / "delivery/scripts/event-model")
        if written is not None:
            (repo / "delivery/.written").write_text(written)
        if model:
            (repo / "delivery/docs/event-model").mkdir(parents=True)
            (repo / "delivery/docs/event-model/model.yaml").write_text(MODEL)
        commit_all(repo, "base")
        git(repo, "checkout", "-q", "-b", "slice/S1")
        return repo

    def verdict(self, repo: Path, path: str) -> subprocess.CompletedProcess:
        target = repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        before = target.read_bytes() if target.exists() else None
        target.write_text("x\n")
        try:
            return subprocess.run(
                ["python3", "delivery/scripts/check-slice-scope.py"], cwd=repo, text=True, capture_output=True,
                env={**os.environ, "GITHUB_HEAD_REF": "", "CI_COMMIT_REF_NAME": ""},
            )
        finally:
            if before is None:
                target.unlink()
            else:
                target.write_bytes(before)

    def green(self, repo: Path, *paths: str) -> None:
        for path in paths:
            result = self.verdict(repo, path)
            self.assertEqual(result.returncode, 0, f"{path}: {result.stderr}")
            self.assertIn("touches only what one slice may", result.stdout, path)

    def refused(self, repo: Path, *paths: str) -> None:
        for path in paths:
            result = self.verdict(repo, path)
            self.assertNotEqual(result.returncode, 0, f"{path} was let through")
            self.assertIn(OUTSIDE, result.stderr, path)
            self.assertIn("the host's", result.stderr, path)

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

    def test_the_host_surface_at_the_root_is_refused(self) -> None:
        """R2 e1: the root Makefile, the manifest, the run's settings, CI and the harness guidance are the host's."""
        self.refused(self.repo(self.root()), "Makefile", "project.json", ".specify/x.json",
                     ".github/workflows/x.yml", "AGENTS.md", ".claude/settings.json")

    def test_the_delivery_directory_is_refused(self) -> None:
        """R2 e2: the gate, the skills, the commands and the baseline sit in the delivery directory."""
        self.refused(self.repo(self.root()), "delivery/scripts/x.py", "delivery/skills/x/SKILL.md",
                     "delivery/commands/x.md", "delivery/Makefile", "delivery/baseline.json")

    def test_the_docs_keep_their_own_answer(self) -> None:
        """R2 e3, held: the docs are refused as they were, by the docs clause."""
        result = self.verdict(self.repo(self.root()), "delivery/docs/x.md")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("the docs are the host's", result.stderr)

    def test_the_slice_writes_two_survey_pages_and_no_other(self) -> None:
        """R2 e4: `pinned.md` and `running.md` are the ladder's to write; `survey.md` stays the host's."""
        repo = self.repo(self.root())
        self.green(repo, "delivery/survey/pinned.md", "delivery/survey/running.md")
        self.refused(repo, "delivery/survey/survey.md")

    def test_a_path_the_factory_wrote_is_refused(self) -> None:
        """R2 e5: a line of `.written` is the host's, though no fixed name says so."""
        repo = self.repo(self.root(), written="lib/generated.py\n")
        self.refused(repo, "lib/generated.py")
        self.green(repo, "lib/own.py")

    def test_taking_a_file_over_does_not_open_the_gate_workflow(self) -> None:
        """R2 e6: `.written` with the gate's line deleted still refuses the gate workflow."""
        repo = self.repo(self.root(), written="lib/generated.py\n")
        self.refused(repo, ".github/workflows/verify-delivery.yml")

    def test_no_written_file_leaves_the_fixed_list(self) -> None:
        """R2 e7, held: with no `.written` the fixed list refuses and the rest is the slice's."""
        repo = self.repo(self.root())
        self.assertFalse((repo / "delivery/.written").exists())
        self.refused(repo, "Makefile")
        self.green(repo, "lib/own.py")

    def test_the_recorded_gate_is_the_hosts_wherever_it_sits(self) -> None:
        """R2 e8: `ci.gate` naming a file outside the fixed CI names is refused."""
        repo = self.repo(self.root(), ci={"gate": "ci/gate.yml"})
        self.refused(repo, "ci/gate.yml")
        self.green(repo, "ci/other.yml")

    def test_a_real_adoption_at_the_root(self) -> None:
        """AC-S20-1, -2 on a tree `slipwai adopt` made: tests are the slice's, the Makefile and a written path not."""
        with tempfile.TemporaryDirectory() as directory:
            repo = repository(Path(directory), "shop", {
                "package.json": json.dumps({"name": "shop", "scripts": {"lint": "x", "test": "y"}}),
                "src/index.js": "1\n", "test/a.test.js": "2\n", "Makefile": "all:\n\t@true\n",
            })
            self.assertEqual(slipwai(repo, "adopt", "--yes").returncode, 0)
            self.assertEqual(json.loads((repo / "project.json").read_text())["deployables"]["shop"]["path"], ".")
            written = [line for line in (repo / "delivery/.written").read_text().splitlines() if line]
            self.assertEqual(subprocess.run(["git", "status", "--porcelain"], cwd=repo, text=True,
                                            capture_output=True).stdout, "")  # adopt committed it, on main
            git(repo, "checkout", "-q", "-b", "slice/S1")
            self.green(repo, "tests/test_x.py", "test/a.test.js", "src/index.js")
            self.refused(repo, "Makefile", written[0], written[-1], ".github/workflows/verify-delivery.yml")


if __name__ == "__main__":
    unittest.main()
