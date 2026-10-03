"""`check-codegraph` on a `slice/<id>` branch hashes what changed (S01-gate-walks, R6 and R7).

The project is the indexed one of `test_code_index_health` — a generated Python project whose index was built by the
fake `codegraph` CLI, which keeps a real SQLite database. *A whole comparison* is one run of the gate on `main` that
passed; `NARROW` is checked out on `slice/S1` with none of the CI markers set. R6 is a set of holds: off a slice
branch, and in CI, the run is today's, to the byte. R7 is the change: on `NARROW` the gate hashes only what changed
and says so.
"""
from __future__ import annotations

import hashlib
import os
import re
import sqlite3
import subprocess
import tempfile
import time
from pathlib import Path

from gate_audit import Audited
from support import FactoryTestCase, commit_all
from test_code_index_health import indexed

GATE = "scripts/check-codegraph.py"
CI_MARKERS = ("CI", "GITHUB_ACTIONS", "GITLAB_CI")
# The gate's own two scripts are opened by any run (it is one of them, and it loads the other); everything else the
# index holds is a file the run either needed to hash or did not.
OWN = {"scripts/check-codegraph.py", "scripts/agents/code_index.py"}
CURRENT = re.compile(r"^check-codegraph: index current — (\d+) file\(s\), indexed \d{4}-\d\d-\d\d \d\d:\d\d:\d\d\n$")
HASHED = (r"^check-codegraph: {synced}index current — hashed {hashed} of (\d+) file\(s\), only what changed since the "
          r"last whole comparison \(\d{{4}}-\d\d-\d\d \d\d:\d\d:\d\d\); the integrity check was not run here and runs "
          r"in the full gate\n$")


# The fake CLI of `test_code_index_health` replaces the database file on `sync`. CodeGraph's own writes are SQLite's,
# in place, to the same file: this stand-in rewrites the rows and leaves the inode, and can be made to fail.
IN_PLACE = """#!/usr/bin/env python3
import hashlib, os, sqlite3, subprocess, sys
from pathlib import Path
with open(os.environ["FAKE_CODEGRAPH_LOG"], "a") as log:
    log.write(" ".join(sys.argv[1:]) + "\\n")
if sys.argv[1] == "sync":
    if os.environ.get("FAKE_SYNC_FAILS"):
        sys.exit("Error: the watcher could not start")
    connection = sqlite3.connect(".codegraph/codegraph.db")
    connection.execute("DELETE FROM files")
    for path in subprocess.run(["git", "ls-files"], capture_output=True, text=True).stdout.split():
        if path.endswith(".py") and Path(path).is_file():
            digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
            connection.execute("INSERT INTO files VALUES (?, ?, 2.0)", (path, digest))
    connection.commit()
    connection.close()
    print("Done")
"""


def narrowed_line(hashed: int, synced: str = "") -> str:
    return HASHED.format(synced=re.escape(synced), hashed=hashed)


class Project:
    """An indexed project and the ways a test moves it: branches, edits, an index that follows or does not."""

    def __init__(self, case: FactoryTestCase, directory: str, name: str = "narrowed") -> None:
        self.case = case
        self.repo, self.tools, self.log = indexed(case, directory, name)
        self.memory = self.repo / ".codegraph/gate-memory.json"
        self.database = self.repo / ".codegraph/codegraph.db"

    def env(self, **extra: str | None) -> dict[str, str]:
        base = {key: value for key, value in os.environ.items() if key not in CI_MARKERS}
        merged = {**base, **self.tools, **extra}
        return {key: value for key, value in merged.items() if value is not None}

    def run(self, **extra: str | None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["python3", GATE], cwd=self.repo, env=self.env(**extra), text=True,
                              capture_output=True)

    def audited(self, **extra: str | None) -> Audited:
        return Audited(self.repo, GATE, env=self.env(**extra))

    def git(self, *arguments: str) -> str:
        done = subprocess.run(["git", *arguments], cwd=self.repo, text=True, capture_output=True, check=True)
        return done.stdout

    def in_place(self) -> None:
        """The CLI on the PATH is the stand-in that writes the database in place."""
        cli = Path(self.tools["PATH"].split(":")[0]) / "codegraph"
        cli.write_text(IN_PLACE)
        cli.chmod(0o755)

    def settle(self) -> None:
        """Wait until every file in the tree is safely older (the gate's two seconds) than now, so that a run starting
        now can vouch for it; a file written a moment ago is, by the gate's own rule, hashed again."""
        newest = max(max(stat.st_mtime, stat.st_ctime) for stat in
                     (path.lstat() for path in self.repo.rglob("*") if ".git" not in path.parts))
        time.sleep(max(0.0, newest + 2.1 - time.time()))

    def whole(self, settled: bool = True) -> subprocess.CompletedProcess[str]:
        """A whole comparison: the gate on `main`, passing."""
        self.git("checkout", "-q", "main")
        if settled:
            self.settle()
        done = self.run()
        self.case.assertEqual(done.returncode, 0, done.stderr)
        return done

    def slice(self) -> None:
        self.git("checkout", "-q", "-B", "slice/S1")

    def source(self) -> str:
        return next(path for path in self.rows() if path not in OWN and not path.startswith("scripts/"))

    def rows(self) -> dict[str, str]:
        with sqlite3.connect(self.database) as connection:
            return dict(connection.execute("SELECT path, content_hash FROM files").fetchall())

    def edit(self, path: str | None = None) -> str:
        path = path or self.source()
        target = self.repo / path
        target.write_text(target.read_text() + f"\n# edited {len(target.read_text())}\n")
        return path

    def resync(self) -> None:
        """The index follows the tree, in place — the way CodeGraph's own watcher writes it, not a new file."""
        with sqlite3.connect(self.database) as connection:
            for path in self.rows():
                digest = hashlib.sha256((self.repo / path).read_bytes()).hexdigest()
                connection.execute("UPDATE files SET content_hash = ? WHERE path = ?", (digest, path))

    def commit(self, message: str = "change") -> None:
        commit_all(self.repo, message)

    def remembered(self) -> bytes | None:
        return self.memory.read_bytes() if self.memory.exists() else None


class WholeRunIsTodaysTest(FactoryTestCase):
    """R6: every example is a hold — green before the narrowing exists, and it must stay green after."""

    def test_hold_the_trunk_prints_todays_line_and_opens_every_indexed_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            audited = project.audited()
            self.assertEqual(audited.result.returncode, 0, audited.result.stderr)
            self.assertRegex(audited.result.stdout, CURRENT)
            self.assertEqual(set(project.rows()) - set(audited.opened), set(), "every indexed file was hashed")

    def test_hold_in_ci_on_a_slice_branch_the_run_is_whole_and_leaves_the_memory_alone(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            today = project.whole().stdout
            project.slice()
            for marker in CI_MARKERS:
                before = project.remembered()
                audited = project.audited(**{marker: "true"})
                self.assertEqual(audited.result.stdout, today, marker)
                self.assertEqual(set(project.rows()) - set(audited.opened), set(), marker)
                self.assertEqual(project.remembered(), before, f"{marker}: the memory is neither read nor written")

    def test_hold_another_branch_and_a_detached_head_are_whole(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            today = project.whole().stdout
            project.git("checkout", "-q", "-b", "feature/x")
            self.assertEqual(project.run().stdout, today)
            project.git("checkout", "-q", "--detach")
            self.assertEqual(project.run().stdout, today)

    def test_hold_a_corrupt_database_is_rebuilt_or_failed_as_today_off_the_narrowed_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.whole()
            garbage = b"garbage " * 1000
            for where, extra in (("main", {}), ("slice/S1", {"CI": "true"})):
                project.git("checkout", "-q", *(["-B", where] if where != "main" else [where]))
                project.database.write_bytes(garbage)
                rebuilt = project.run(**extra)
                self.assertEqual(rebuilt.returncode, 0, rebuilt.stderr)
                self.assertRegex(rebuilt.stdout, r"^check-codegraph: rebuilt a corrupt database first \([\d.]+s\); "
                                 r"index current")
                project.database.write_bytes(garbage)
                refused = project.run(CODEGRAPH_GATE_NO_SYNC="1", **extra)
                self.assertEqual(refused.returncode, 1)
                self.assertIn("fails SQLite's integrity check", refused.stderr)


class NarrowedRunTest(FactoryTestCase):
    """R7: on a slice branch the gate hashes what changed, and the line says so."""

    def test_nothing_changed_hashes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.whole()
            project.slice()
            audited = project.audited()
            self.assertEqual(audited.result.returncode, 0, audited.result.stderr)
            self.assertRegex(audited.result.stdout, narrowed_line(0))
            self.assertEqual(set(project.rows()) & set(audited.opened) - OWN, set())

    def test_one_edited_file_is_the_one_file_hashed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.whole()
            project.slice()
            edited = project.edit()
            project.resync()
            audited = project.audited()
            self.assertEqual(audited.result.returncode, 0, audited.result.stderr)
            self.assertRegex(audited.result.stdout, narrowed_line(1))
            self.assertEqual(set(project.rows()) & set(audited.opened) - OWN, {edited})

    def test_a_committed_edit_is_still_one_and_the_pass_renews_the_next_run_to_none(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.whole()
            project.slice()
            project.edit()
            project.resync()
            project.commit()
            project.settle()  # a file written within two seconds of the run is hashed by the next one too
            self.assertRegex(project.run().stdout, narrowed_line(1))
            self.assertRegex(project.run().stdout, narrowed_line(0))

    def test_an_index_behind_the_tree_is_synced_first_and_the_edit_hashed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.whole()
            project.slice()
            project.edit()
            synced = project.run()
            self.assertEqual(synced.returncode, 0, synced.stderr)
            self.assertRegex(synced.stdout, narrowed_line(1, "synced 1 file(s) first; "))

    def test_hold_without_repairing_a_stale_file_fails_with_todays_report(self) -> None:
        """Green today as well — the whole run says this too — and it must say it on the narrowed path."""
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.whole()
            project.slice()
            edited = project.edit()
            failed = project.run(CODEGRAPH_GATE_NO_SYNC="1")
            self.assertEqual(failed.returncode, 1)
            self.assertIn("check-codegraph: the code index no longer describes this working tree", failed.stderr)
            self.assertIn("1 tracked file(s) changed since they were indexed:", failed.stderr)
            self.assertIn(f"- {edited}", failed.stderr)


class ASyncThatWritesInPlaceTest(FactoryTestCase):
    """The gate's own sync-then-compare-again, against a database written the way SQLite writes it: the same inode."""

    def test_a_sync_in_place_is_followed_by_the_second_comparison_and_renews_the_memory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.in_place()
            project.whole()
            project.slice()
            before = project.remembered()
            inode = project.database.stat().st_ino
            project.edit()
            project.commit()
            project.settle()
            synced = project.run()
            self.assertEqual(synced.returncode, 0, synced.stderr)
            self.assertRegex(synced.stdout, narrowed_line(1, "synced 1 file(s) first; "))
            self.assertEqual(project.database.stat().st_ino, inode, "written in place")
            self.assertNotEqual(project.remembered(), before, "the pass renewed the memory")
            self.assertRegex(project.run().stdout, narrowed_line(0))

    def test_a_sync_that_does_not_take_fails_and_leaves_the_memory_as_it_was(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.in_place()
            project.whole()
            project.slice()
            before = project.remembered()
            edited = project.edit()
            failed = project.run(FAKE_SYNC_FAILS="1")
            self.assertEqual(failed.returncode, 1)
            self.assertIn("`codegraph sync` did not take", failed.stderr)
            self.assertIn(f"- {edited}", failed.stderr)
            self.assertEqual(project.remembered(), before)
