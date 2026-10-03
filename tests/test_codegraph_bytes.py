"""What a narrowed `check-codegraph` run cannot know from git alone (S01-gate-walks, T016 and T017).

The constitution's MUST: a narrowed run never reports *current* where the whole run would not. These examples are the
states git does not report faithfully: a path git was told not to report at the moment the memory vouched, and a file
whose bytes changed in a way git's comparison normalises away. Helpers are those of `test_codegraph_narrowed`.
"""
from __future__ import annotations

import tempfile

from support import FactoryTestCase
from test_codegraph_narrowed import Project

NO_SYNC = {"CODEGRAPH_GATE_NO_SYNC": "1"}
FLAGS = (("--assume-unchanged", "--no-assume-unchanged"), ("--skip-worktree", "--no-skip-worktree"))


class WhatGitWasNotReportingWhenTheMemoryVouchedTest(FactoryTestCase):
    """T017: a path flagged at the write is hashed afterwards, whichever run wrote the memory."""

    def reverted_after_the_flag_is_cleared(self, project: Project, path: str, clear: str) -> None:
        project.git("update-index", clear, path)
        project.git("checkout", "--", path)
        failed = project.run(**NO_SYNC)
        self.assertEqual(failed.returncode, 1, failed.stdout)
        self.assertIn(f"- {path}", failed.stderr)
        project.git("checkout", "-q", "main")
        self.assertEqual(project.run(**NO_SYNC).returncode, 1, "the whole run says the same")

    def test_flagged_and_edited_before_a_whole_pass_wrote_the_memory(self) -> None:
        for flag, clear in FLAGS:
            with self.subTest(flag), tempfile.TemporaryDirectory() as directory:
                project = Project(self, directory)
                path = project.source()
                project.git("update-index", flag, path)
                project.edit(path)
                project.resync()
                project.whole()
                project.slice()
                self.reverted_after_the_flag_is_cleared(project, path, clear)

    def test_flagged_and_edited_before_a_narrowed_pass_renewed_the_memory(self) -> None:
        for flag, clear in FLAGS:
            with self.subTest(flag), tempfile.TemporaryDirectory() as directory:
                project = Project(self, directory)
                project.whole()
                project.slice()
                path = project.source()
                project.git("update-index", flag, path)
                project.edit(path)
                project.resync()
                passed = project.run(**NO_SYNC)
                self.assertEqual(passed.returncode, 0, passed.stderr)
                self.assertIn("hashed 1 of", passed.stdout)
                self.reverted_after_the_flag_is_cleared(project, path, clear)
