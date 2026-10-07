"""The gate's own record is trustworthy (S01-gate-walks, T032 and T033: the adversary's F1, F2 and F3).

T032: one comparison judges, and the record keeps, one read of the index's rows. A `git` wrapper first on `PATH`
rewrites a row's hash at the moment the gate asks `git diff`, which is between the two reads a narrowed run used to
make. T033: the record is written through a file the gate creates for itself, never through a path already there.
"""
from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from support import FactoryTestCase
from test_codegraph_narrowed import Project

# Generates nothing itself: the projects come from `Project`, imported from the module above.
TEST_SELECTION: dict[str, object] = {}

FAKE = "0" * 64
WRAPPER = """#!{python}
import os, sqlite3, sys
args = sys.argv[1:]
here = os.path.dirname(os.path.abspath(__file__))
marker = os.path.join(here, "rewritten")
log = os.environ["FAKE_CODEGRAPH_LOG"]
after_sync = os.path.exists(log) and "sync" in open(log).read()
if args[:1] == ["diff"] and not os.path.exists(marker) and (after_sync or not {when_synced}):
    open(marker, "w").close()
    with sqlite3.connect(".codegraph/codegraph.db") as connection:
        connection.execute("UPDATE files SET content_hash = ? WHERE path = ?", ({fake!r}, {path!r}))
os.execv({git!r}, [{git!r}, *args])
"""


def rewriting(project: Project, directory: str, path: str, when_synced: bool = False) -> dict[str, str]:
    """A `git` first on the PATH that rewrites `path`'s row in the index the first time the gate runs `git diff`
    (the first one after a sync, where `when_synced`)."""
    wrapper = Path(directory) / "wrapper"
    wrapper.mkdir()
    (wrapper / "git").write_text(WRAPPER.format(python=sys.executable, git=shutil.which("git"), fake=FAKE,
                                                path=path, when_synced=when_synced))
    (wrapper / "git").chmod(0o755)
    return {"PATH": f"{wrapper}:{project.tools['PATH']}"}


def sources(project: Project) -> list[str]:
    return [path for path in project.rows() if not path.startswith("scripts/")]


class OneReadOfTheRowsTest(FactoryTestCase):
    """T032 (F1): a row that changes while a narrowed run reads is judged as the whole run judges it."""

    def test_a_row_rewritten_between_the_reads_fails_and_is_not_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.whole()
            project.slice()
            moved = sources(project)[0]
            env = rewriting(project, directory, moved)
            failed = project.run(CODEGRAPH_GATE_NO_SYNC="1", **env)
            self.assertEqual(failed.returncode, 1, f"narrowed passed where the whole run fails: {failed.stdout}")
            self.assertIn(f"- {moved}", failed.stderr)
            kept = project.remembered()
            self.assertTrue(kept is None or FAKE not in kept.decode(), "the record holds a hash nobody verified")
            again = project.run(CODEGRAPH_GATE_NO_SYNC="1")
            self.assertEqual(again.returncode, 1, "a later run passes on the rewritten row")

    def test_a_row_rewritten_after_a_sync_is_judged_by_the_comparison_after_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.in_place()
            project.whole()
            project.slice()
            first, second = sources(project)[:2]
            project.edit(first)
            env = rewriting(project, directory, second, when_synced=True)
            failed = project.run(**env)
            self.assertEqual(failed.returncode, 1, f"the comparison after the sync passed: {failed.stdout}")
            self.assertIn(f"- {second}", failed.stderr)
            kept = project.remembered()
            self.assertTrue(kept is None or FAKE not in kept.decode())


def settled_pass(project: Project) -> None:
    project.whole()
    project.slice()
    project.settle()


def record_of(project: Project) -> dict:
    return json.loads(project.memory.read_text())


class TheRecordIsWrittenThroughAFileOfItsOwnTest(FactoryTestCase):
    """T033 (F2, F3): a path that was already there is never written through, on a slice branch or on the trunk."""

    def trap(self, project: Project, make) -> Path:
        """Something the project committed (`git add -f`) or left at the old temporary name."""
        victim = project.repo.parent / "victim"
        victim.write_text("precious")
        tmp = project.repo / ".codegraph/gate-memory.json.tmp"
        make(tmp, victim)
        return victim

    def within_thirty_seconds(self, project: Project) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(["python3", "scripts/check-codegraph.py"], cwd=project.repo, env=project.env(),
                                  text=True, capture_output=True, timeout=30)
        except subprocess.TimeoutExpired:
            self.fail("the run did not return in thirty seconds")

    def link_at_the_old_temporary_name(self, branch: str) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.whole()
            if branch == "slice":
                project.slice()
            victim = self.trap(project, lambda tmp, target: tmp.symlink_to(target))
            project.git("add", "-f", ".codegraph/gate-memory.json.tmp")
            project.git("commit", "-q", "-m", "a link")
            project.settle()
            status = project.git("status", "--porcelain")
            done = project.run()
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertEqual(victim.read_text(), "precious", "written through the link")
            self.assertEqual(project.git("status", "--porcelain"), status)
            self.assertTrue(project.memory.is_file() and not project.memory.is_symlink())
            self.assertEqual(sorted(p.name for p in (project.repo / ".codegraph").iterdir() if ".tmp" in p.name),
                             ["gate-memory.json.tmp"], "a stray temporary file")

    def test_a_link_committed_at_the_temporary_name_is_not_written_through_on_a_slice_branch(self) -> None:
        self.link_at_the_old_temporary_name("slice")

    def test_a_link_committed_at_the_temporary_name_is_not_written_through_on_the_trunk(self) -> None:
        self.link_at_the_old_temporary_name("main")

    def test_a_fifo_at_the_temporary_name_does_not_hang_the_run(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.whole()
            os.mkfifo(project.repo / ".codegraph/gate-memory.json.tmp")
            done = self.within_thirty_seconds(project)
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertTrue(stat.S_ISFIFO((project.repo / ".codegraph/gate-memory.json.tmp").lstat().st_mode))

    def test_a_tracked_regular_file_at_the_temporary_name_is_left_as_it_is(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.whole()
            tmp = project.repo / ".codegraph/gate-memory.json.tmp"
            tmp.write_text("committed")
            project.git("add", "-f", ".codegraph/gate-memory.json.tmp")
            project.git("commit", "-q", "-m", "a file")
            project.settle()
            self.assertEqual(project.run().returncode, 0)
            self.assertTrue(tmp.is_file(), "the committed file was replaced")
            self.assertEqual(tmp.read_text(), "committed")
            self.assertEqual(project.git("status", "--porcelain"), "")

    def test_a_record_that_is_a_directory_a_link_or_a_fifo_is_never_fatal_and_writes_nothing_outside(self) -> None:
        for kind in ("directory", "link", "fifo"):
            with self.subTest(kind), tempfile.TemporaryDirectory() as directory:
                project = Project(self, directory)
                project.whole()
                project.memory.unlink()
                outside = Path(directory) / "outside"
                outside.write_text("precious")
                if kind == "directory":
                    project.memory.mkdir()
                elif kind == "link":
                    project.memory.symlink_to(outside)
                else:
                    os.mkfifo(project.memory)
                status = project.git("status", "--porcelain")
                project.slice()
                done = self.within_thirty_seconds(project)
                self.assertEqual(done.returncode, 0, done.stderr)
                self.assertIn("compared everything", done.stdout)
                self.assertEqual(outside.read_text(), "precious")
                self.assertEqual(project.git("status", "--porcelain"), status)
                self.assertFalse(project.memory.is_file() and not project.memory.is_symlink(), kind)
                self.assertEqual([p.name for p in (project.repo / ".codegraph").iterdir() if p.name.endswith(".tmp")],
                                 [])

    def test_twelve_runs_at_once_leave_one_valid_record_and_no_stray_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.whole()
            project.settle()
            running = [subprocess.Popen(["python3", "scripts/check-codegraph.py"], cwd=project.repo,
                                        env=project.env(), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                       for _ in range(12)]
            outcomes = [(run.wait(timeout=120), run.stderr.read() if run.stderr else "") for run in running]
            for run in running:
                for pipe in (run.stdout, run.stderr):
                    if pipe:
                        pipe.close()
            self.assertEqual([code for code, _ in outcomes], [0] * 12, outcomes)
            self.assertIn("rows", record_of(project))
            self.assertEqual([p.name for p in (project.repo / ".codegraph").iterdir() if p.name.endswith(".tmp")], [])

    def test_a_stale_temporary_file_of_the_gates_own_left_by_a_killed_run_is_swept(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.whole()
            left = project.repo / ".codegraph/.gate-memory-killed.tmp"
            left.write_text("{")
            old = time.time() - 3600
            os.utime(left, (old, old))
            project.settle()
            self.assertEqual(project.run().returncode, 0)
            self.assertFalse(left.exists())
