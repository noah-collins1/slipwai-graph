"""What the memory of `check-codegraph` can and cannot vouch for (S01-gate-walks, R8 to R10).

A narrowed run never reports *current* where the whole run would not (the constitution's MUST about a scoped gate).
So the paths it skips are the ones the memory vouches for, and every path it cannot vouch for is hashed: one that
was dirty when the memory was written and has since been reverted, a row rewritten, added or removed in the index,
a file git was told not to report, a database that is not the one that was compared. Helpers are those of
`test_codegraph_narrowed`.
"""
from __future__ import annotations

import copy
import json
import os
import shutil
import sqlite3
import tempfile
from pathlib import Path
from typing import Any

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


def whole_line(why: str) -> str:
    return (r"^check-codegraph: index current — \d+ file\(s\), indexed \d{4}-\d\d-\d\d \d\d:\d\d:\d\d "
            rf"\(compared everything: {why}\)\n$")


class AMemoryThatCannotBeUsedTest(FactoryTestCase):
    """R9: the whole run, said in one clause — never a failure for that alone, never a narrower pass."""

    def prepared(self, directory: str, name: str = "memory") -> Project:
        project = Project(self, directory, name)
        project.whole()
        self.assertTrue(project.memory.is_file(), "a passing whole comparison leaves its memory")
        project.slice()
        return project

    def test_no_memory_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.prepared(directory)
            project.memory.unlink()
            run = project.run()
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertRegex(run.stdout, whole_line("no earlier whole comparison is recorded"))

    def test_a_memory_that_is_not_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.prepared(directory)
            for broken in ("{", "[]", '{"commit": 1}'):
                project.memory.write_text(broken)
                run = project.run()
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertRegex(run.stdout, whole_line("the record of the last whole comparison could not be read"))

    def test_a_memory_of_the_right_shape_with_a_content_the_run_cannot_use(self) -> None:
        """AC-S01-18's class: any content of the memory file, to the depth the run uses it, is the whole run."""
        unusable: dict[str, list[Any]] = {
            "dirty": [[["a"]], [1], "a"],
            "whole": [1e300, float("inf"), float("nan"), True, "now", -1e300],
            "rows": [{"a": 1}, {"a": ["x"]}],
            "database": [["a"], [1.5, 2], [1]],
            "files": [{"a": "x"}, {"a": [1, 2]}, {"a": [1, 2, 3, 4, "x"]}, {"a": None}],
            "key": [None], "commit": [None, 1]}
        with tempfile.TemporaryDirectory() as directory:
            project = self.prepared(directory)
            record = json.loads(project.memory.read_text())
            for field, values in unusable.items():
                for value in values:
                    with self.subTest(field=field, value=repr(value)):
                        project.memory.write_text(json.dumps({**record, field: value}))
                        run = project.run()
                        self.assertEqual(run.returncode, 0, run.stderr)
                        self.assertRegex(run.stdout,
                                         whole_line("the record of the last whole comparison could not be read"))

    def test_a_commit_the_repository_no_longer_has(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.prepared(directory)
            record = json.loads(project.memory.read_text())
            project.memory.write_text(json.dumps({**record, "commit": "0" * 40}))
            run = project.run()
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertRegex(run.stdout, whole_line("the commit it was taken at is gone"))

    def test_a_gate_script_that_changed_since(self) -> None:
        for script in ("scripts/check-codegraph.py", "scripts/agents/code_index.py"):
            with self.subTest(script), tempfile.TemporaryDirectory() as directory:
                project = self.prepared(directory)
                with (project.repo / script).open("a") as handle:
                    handle.write("# one more byte\n")
                project.resync()
                run = project.run()
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertRegex(run.stdout, whole_line("the gate's scripts changed since"))

    def test_a_corrupt_database_is_rebuilt_or_failed_never_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.prepared(directory)
            project.database.write_bytes(b"garbage " * 1000)
            rebuilt = project.run()
            self.assertEqual(rebuilt.returncode, 0, rebuilt.stderr)
            self.assertRegex(rebuilt.stdout, r"^check-codegraph: rebuilt a corrupt database first \([\d.]+s\); "
                             r"index current — \d+ file\(s\), indexed .* \(compared everything: ")
            self.assertNotIn("hashed", rebuilt.stdout)
            project.database.write_bytes(b"garbage " * 1000)
            refused = project.run(**NO_SYNC)
            self.assertEqual(refused.returncode, 1)
            self.assertIn("fails SQLite's integrity check", refused.stderr)
            self.assertNotIn("skipped", refused.stdout + refused.stderr)


class TheMemoryIsWrittenOnlyByAPassTest(FactoryTestCase):
    """R10: no renewal after a failure; nothing in `git status`; it lives and dies with `.codegraph/`."""

    def test_hold_a_failing_run_leaves_the_memory_as_it_was(self) -> None:
        """Green at the tree where only a pass writes; seen failing with the write moved before the verdict."""
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.whole()
            before = project.remembered()
            project.slice()
            project.edit()
            self.assertEqual(project.run(**NO_SYNC).returncode, 1)
            self.assertEqual(project.remembered(), before)

    def test_a_narrowed_pass_that_synced_renews_the_memory_and_keeps_the_whole_moment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.whole()
            whole = json.loads(project.memory.read_text())["whole"]
            project.slice()
            project.edit()
            project.commit()
            project.settle()  # a file written within two seconds of the run is hashed by the next one too
            first = project.run()
            self.assertIn("synced 1 file(s) first; index current — hashed 1 of", first.stdout)
            second = project.run()
            self.assertIn("index current — hashed 0 of", second.stdout)
            self.assertEqual(json.loads(project.memory.read_text())["whole"], whole)
            self.assertEqual(first.stdout.split("(")[-2].split(")")[0], second.stdout.split("(")[-2].split(")")[0])

    def test_hold_git_never_sees_the_memory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.whole()
            project.slice()
            project.run()
            self.assertTrue(project.memory.is_file())
            self.assertEqual(project.git("status", "--porcelain"), "")

    def test_where_git_would_see_it_no_memory_is_written_and_every_run_is_whole(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            ignore = project.repo / ".gitignore"
            ignore.write_text("".join(line for line in ignore.read_text().splitlines(keepends=True)
                                      if line.strip() != ".codegraph/"))
            project.commit("stop ignoring the index")
            project.whole()
            self.assertFalse(project.memory.exists())
            project.slice()
            run = project.run()
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertRegex(run.stdout, whole_line("no earlier whole comparison is recorded"))
            self.assertFalse(project.memory.exists())

    def test_hold_a_memory_copied_into_a_clone_at_another_commit_is_not_trusted(self) -> None:
        """A copy of `.codegraph/` (another inode), and a hard link to it (the same inode and device): the commit
        and the rows say it is not this tree's, whichever way the database came."""
        for name, put in (("copy", shutil.copy2), ("link", os.link)):
            with self.subTest(name), tempfile.TemporaryDirectory() as directory:
                project = Project(self, directory, name)
                project.whole()
                edited = project.edit()
                project.commit("a later commit")
                clone = copy.copy(project)
                clone.repo = Path(directory) / f"{name}-clone"
                project.git("clone", "-q", str(project.repo), str(clone.repo))
                clone.memory = clone.repo / ".codegraph/gate-memory.json"
                clone.database = clone.repo / ".codegraph/codegraph.db"
                clone.memory.parent.mkdir()
                put(project.memory, clone.memory)
                put(project.database, clone.database)
                clone.git("checkout", "-q", "-b", "slice/S1")
                narrowed = clone.run(**NO_SYNC)
                clone.git("checkout", "-q", "main")
                whole = clone.run(**NO_SYNC)
                self.assertEqual((narrowed.returncode, narrowed.stderr), (whole.returncode, whole.stderr))
                self.assertEqual(whole.returncode, 1)
                self.assertIn(f"- {edited}", whole.stderr)
