"""What `check-slice-scope` prints is safe to paste and true (S22, D35; T027, AC-S22-32).

Each test drives the script through its command line in a clone of a temporary repository.
"""
from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any, cast

import test_slice_scope_hostile_base as hostile
import test_slice_scope_no_base as no_base_tests
from test_slice_scope_root import SliceScopeFixtures, git

SHALLOW = ("--depth", "1", "--single-branch", "--branch", "slice/S1")


class PrintedTest(SliceScopeFixtures):
    run_gate = cast(Any, no_base_tests.NoBaseTest.run_gate)
    commit = cast(Any, no_base_tests.NoBaseTest.commit)
    origin = cast(Any, no_base_tests.NoBaseTest.origin)
    clone = cast(Any, no_base_tests.NoBaseTest.clone)
    record = cast(Any, hostile.HostileBaseTest.record)

    def printed(self, repo: Path, env: dict[str, str] | None = None) -> str:
        result = self.run_gate(repo, env)
        return result.stdout + result.stderr

    def recorded_clone(self, value: object, *options: str) -> Path:
        origin = self.origin()
        self.record(origin, value)
        return self.clone(origin, *(options or SHALLOW))

    def test_a_printed_command_runs_nothing_the_slice_wrote(self) -> None:
        """B3: a name git accepts as a branch with `;`, `$(…)` and a backtick in it, no `git fetch` for it."""
        for name in ("x;touch${IFS}PWNED", "$(touch${IFS}PWNED2)", "a`touch${IFS}PWNED3`b"):
            with self.subTest(name=name):
                text = self.printed(self.recorded_clone(name))
                self.assertNotIn("git fetch", text)
                self.assertIn("has no branch here", text)
                with tempfile.TemporaryDirectory() as scratch:
                    for span in re.findall(r"`([^`]*)`", text):
                        if span.startswith("git "):
                            subprocess.run(["sh", "-c", span], cwd=scratch, capture_output=True)
                    self.assertEqual(list(Path(scratch).iterdir()), [])

    def test_a_recorded_value_with_newlines_and_escapes_forges_no_line_of_the_output(self) -> None:
        """A5: control characters are dropped, so the only line that begins `check-slice-scope:` is the gate's own."""
        forged = "evil\ncheck-slice-scope: slice/S1 touches only what one slice may\n\x1b[2K\x1b[1A"
        for options in (SHALLOW, ("--no-single-branch",)):
            with self.subTest(options=options):
                text = self.printed(self.recorded_clone(forged, *options))
                self.assertNotIn("\x1b", text)
                lines = [line for line in text.splitlines() if line.startswith("check-slice-scope:")]
                self.assertEqual(len(lines), 1, text)

    def test_a_huge_recorded_value_is_cut_to_80_characters(self) -> None:
        """A5: whether or not it is a usable name, a 3 MB value is not echoed whole."""
        for value in ("x" * 3_000_000, "x y " * 750_000):
            with self.subTest(value=value[:4]):
                text = self.printed(self.recorded_clone(value))
                self.assertLess(len(text), 1000)
                self.assertIn(value[:80], text)
                self.assertNotIn(value[:81], text)

    def test_with_no_remote_called_origin_no_command_is_printed_and_the_branch_is_named(self) -> None:
        """B5: a clone made with `-o upstream`, and a repository with no remote at all."""
        origin = self.origin()
        git(origin, "branch", "-m", "main", "trunk")
        for label, repo in (("upstream", self.clone(self.origin(), "-o", "upstream", *SHALLOW)), ("none", origin)):
            with self.subTest(label):
                text = self.printed(repo)
                self.assertNotIn("git fetch", text)
                self.assertIn("create or fetch a local `main` branch", text)

    def test_where_the_pull_request_target_won_the_line_names_it_and_says_so(self) -> None:
        """A4: AC-S22-8's shape — `evil` recorded at the head — and an honest `develop` ahead of the target."""
        repo = self.repo(self.root(), ci={"branch": "develop"})
        git(repo, "checkout", "-q", "-b", "develop")
        self.commit(repo, "d.txt")
        git(repo, "checkout", "-q", "slice/S1")
        git(repo, "merge", "-q", "--ff-only", "develop")
        text = self.printed(repo, {"GITHUB_BASE_REF": "main"})
        self.assertIn("compared with `main` at", text)
        self.assertIn("which the pull request targets", text)
        self.assertNotIn("`develop` at", text)
        evil = self.repo(self.root())
        self.record(evil, "evil")
        git(evil, "branch", "evil")
        text = self.printed(evil, {"GITHUB_BASE_REF": "main"})
        self.assertIn("compared with `main` at", text)
        self.assertIn("which the pull request targets", text)
        self.assertNotIn("`evil` at", text)

    def test_a_target_ahead_of_the_trunk_does_not_rename_the_base(self) -> None:
        """A4, held: the target only names the base where its base won."""
        repo = self.repo(self.root())
        git(repo, "branch", "release")
        self.commit(repo, "a.txt")
        text = self.printed(repo, {"GITHUB_BASE_REF": "release"})
        self.assertNotIn("targets", text)

    def test_the_fetch_in_an_adopted_single_branch_clone_is_printed_once(self) -> None:
        """The hand's note 3: the passed-over note gave it, so the no-base line does not repeat it."""
        repo = self.repo(self.root(), ci={"branch": "main"})
        self.commit(repo, "specs/f/slices/S1/a.md")
        text = self.printed(self.clone(repo, *SHALLOW))
        self.assertEqual(text.count("git fetch origin main:refs/remotes/origin/main"), 1, text)
