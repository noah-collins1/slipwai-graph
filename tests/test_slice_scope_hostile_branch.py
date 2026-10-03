"""What a slice branch can plant or name must not move the gate (adversary A1, A2, A4, A5; D23).

Each test drives `check-slice-scope` through its command line in a temporary repository laid out as an adoption
leaves one, on a `slice/S1` branch, with the fixtures of `test_slice_scope_root`.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from test_slice_scope_root import SliceScopeFixtures, git

HOST_PATHS = ("project.json", ".github/x.yml", "delivery/x.py", "Makefile", ".claude/x.json", "AGENTS.md")


class HostileBranchTest(SliceScopeFixtures):
    def run_gate(self, repo: Path) -> subprocess.CompletedProcess:
        return subprocess.run(["python3", self.script], cwd=repo, text=True, capture_output=True,
                              env={**os.environ, "GITHUB_HEAD_REF": "", "CI_COMMIT_REF_NAME": ""})

    def write(self, repo: Path, path: str, text: str = "x\n", commit: bool = False) -> None:
        (repo / path).parent.mkdir(parents=True, exist_ok=True)
        (repo / path).write_text(text)
        if commit:
            git(repo, "add", "--", path)
            git(repo, "commit", "-q", "-m", "slice", "--", path)

    def refuses(self, repo: Path, path: str) -> None:
        result = self.run_gate(repo)
        self.assertNotEqual(result.returncode, 0, f"{path} was let through")
        self.assertIn(path, result.stderr)

    # T016 (A1)
    QUOTED = ("déploy.yml", "delivery/scripts/é.py", ".specify/é.sh", ".claude/a\tb.json", ".claude/q\"x.json",
              "specs/f/slices/S2/é.md")

    def test_a_path_git_quotes_is_held_like_any_other(self) -> None:
        """T016: non-ASCII, tab and quote names under host paths are refused, committed or not."""
        for commit in (False, True):
            for path in (".github/workflows/déploy.yml", *self.QUOTED[1:]):
                repo = self.repo(self.root())
                self.write(repo, path, commit=commit)
                self.refuses(repo, path)

    def test_an_existing_migration_with_a_non_ascii_name_is_not_editable(self) -> None:
        """T016: the edit of a shipped `0002_añadir.py` is refused."""
        path = "db/migrations/0002_añadir.py"
        repo = self.repo(self.root(), existing={path: "a\n"})
        self.write(repo, path, "b\n")
        self.refuses(repo, path)

    def test_ascii_answers_as_before_and_a_service_file_under_apps_is_the_slices(self) -> None:
        """T016, held: an ASCII path is as it was; a non-ASCII file in the slice's own service is green."""
        repo = self.repo({"shop": {"kind": "service", "path": "apps/shop"}}, model=True)
        self.write(repo, "apps/shop/é.py")
        self.write(repo, "apps/shop/a.py")
        result = self.run_gate(repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.write(repo, "Makefile")
        self.refuses(repo, "Makefile")

    # T017 (A2)
    def test_ownership_is_read_from_the_base_record(self) -> None:
        """T017: planted deployables over the host's paths own nothing; every path is refused."""
        repo = self.repo(self.root())
        planted = {f"p{index}": {"kind": "service", "path": path}
                   for index, path in enumerate(("project.json", ".github", "delivery", "Makefile", ".claude",
                                                 "AGENTS.md"))}
        planted["shop"] = {"kind": "service", "path": "."}
        self.write(repo, "project.json", json.dumps({"deployables": planted}))
        for path in HOST_PATHS[1:]:
            self.write(repo, path)
        result = self.run_gate(repo)
        self.assertNotEqual(result.returncode, 0)
        for path in HOST_PATHS:
            self.assertIn(path, result.stderr)

    def test_a_planted_ci_gate_is_not_the_bases(self) -> None:
        """T017: `ci.gate` read from the branch's record would name a path; the base's does not."""
        repo = self.repo(self.root(), ci={"gate": "ci/gate.yml"})
        self.write(repo, "project.json", json.dumps({"deployables": self.root(), "ci": {"gate": "other.yml"}}))
        self.write(repo, "ci/gate.yml")
        self.refuses(repo, "ci/gate.yml")

    def test_a_base_with_no_record_owns_nothing(self) -> None:
        """T017: no `project.json` on the base, one planted on the branch: nothing is owned."""
        repo = self.repo(self.root())
        git(repo, "checkout", "-q", "main")
        git(repo, "rm", "-q", "project.json")
        git(repo, "commit", "-q", "-m", "drop")
        git(repo, "checkout", "-q", "slice/S1")
        git(repo, "merge", "-q", "main")
        self.write(repo, "project.json", json.dumps({"deployables": self.root()}))
        self.write(repo, "lib/own.py")
        self.refuses(repo, "lib/own.py")

    def test_an_unchanged_record_answers_as_before(self) -> None:
        """T017, held: with `project.json` as on the base the root deployable owns what it did."""
        self.green(self.repo(self.root()), "tests/test_x.py")

