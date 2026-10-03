"""What the memory of `check-codegraph` can and cannot vouch for (S01-gate-walks, R8 to R10).

A narrowed run never reports *current* where the whole run would not (the constitution's MUST about a scoped gate).
So the paths it skips are the ones the memory vouches for, and every path it cannot vouch for is hashed: one that
was dirty when the memory was written and has since been reverted, a row rewritten, added or removed in the index,
a file git was told not to report, a database that is not the one that was compared. Helpers are those of
`test_codegraph_narrowed`.
"""
from __future__ import annotations

import os
import shutil
import sqlite3
import tempfile

from support import FactoryTestCase
from test_codegraph_narrowed import Project

NO_SYNC = {"CODEGRAPH_GATE_NO_SYNC": "1"}


class WhatTheMemoryCannotVouchForTest(FactoryTestCase):
    """R8: hashed, though git reports nothing."""

    def refused(self, project: Project, path: str) -> None:
        failed = project.run(**NO_SYNC)
        self.assertEqual(failed.returncode, 1, failed.stdout)
        self.assertIn(f"- {path}", failed.stderr)

    def test_a_file_dirty_at_the_memory_and_reverted_since_is_hashed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            edited = project.edit()
            project.resync()  # the index holds the dirty content, and the whole comparison passes on it
            project.whole()
            project.git("checkout", "--", edited)
            project.git("checkout", "-q", "-B", "slice/S1")
            self.refused(project, edited)
            project.git("checkout", "-q", "main")
            self.assertEqual(project.run(**NO_SYNC).returncode, 1, "the whole run says the same")

    def test_a_row_rewritten_in_the_index_is_hashed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.whole()
            project.slice()
            path = project.source()
            with sqlite3.connect(project.database) as connection:
                connection.execute("UPDATE files SET content_hash = ? WHERE path = ?", ("0" * 64, path))
            self.refused(project, path)

    def test_a_row_deleted_from_the_index_gives_the_whole_runs_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.whole()
            project.slice()
            path = project.source()
            with sqlite3.connect(project.database) as connection:
                connection.execute("DELETE FROM files WHERE path = ?", (path,))
            narrowed = project.run(**NO_SYNC)
            project.git("checkout", "-q", "main")
            whole = project.run(**NO_SYNC)
            self.assertEqual((narrowed.returncode, narrowed.stderr), (whole.returncode, whole.stderr))
            self.assertEqual(whole.returncode, 1)
            self.assertIn(f"- {path}", whole.stderr)

    def test_a_row_added_for_a_tracked_file_is_hashed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            extra = project.repo / "extra.py"
            extra.write_text("x = 1\n")
            project.commit("a file the index never saw")
            os.utime(extra, (0, 0))  # older than the index, so the whole run does not call it a hole
            project.whole()
            project.slice()
            with sqlite3.connect(project.database) as connection:
                connection.execute("INSERT INTO files VALUES ('extra.py', ?, 1.0)", ("0" * 64,))
            self.refused(project, "extra.py")

    def test_a_file_git_was_told_not_to_report_is_hashed(self) -> None:
        for flag in ("--assume-unchanged", "--skip-worktree"):
            with self.subTest(flag), tempfile.TemporaryDirectory() as directory:
                project = Project(self, directory)
                path = project.source()
                project.git("update-index", flag, path)
                project.whole()
                project.slice()
                project.edit(path)
                self.assertEqual(project.git("diff", "--name-only"), "", "git reports nothing")
                self.refused(project, path)

    def test_a_database_that_is_another_file_is_never_narrowed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.whole()
            project.slice()
            copy = project.database.with_name("copy.db")
            shutil.copy2(project.database, copy)
            before = project.database.stat().st_ino
            os.replace(copy, project.database)
            self.assertNotEqual(project.database.stat().st_ino, before)
            replaced = project.run()
            self.assertEqual(replaced.returncode, 0, replaced.stderr)
            self.assertRegex(replaced.stdout, r"^check-codegraph: index current — \d+ file\(s\), indexed ")
            self.assertNotIn("hashed", replaced.stdout)
