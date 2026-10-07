"""R2 (AC-S03-2, -3, -4): the key is the working files, as they are.

Each example stamps the fixture, changes it one way, and holds that the next run starts the checks and leaves a new
stamp (which the run after that reuses). What started is read from the stand-ins' log.
"""
from __future__ import annotations

import os
import subprocess
from collections.abc import Callable
from pathlib import Path

from stamp_case import StampTestCase
from stamp_names import CLOSING, commit_all, git

# Generates nothing itself: the project comes from `stamp_case.StampTestCase`, whose declaration the join carries.
# "README.md" is the generated project's tracked file; named because the selector reads the string as the root file.
TEST_SELECTION: dict[str, object] = {"reads": ["README.md"]}

TRACKED = "README.md"


def can_link(directory: Path) -> bool:
    probe = directory / ".probe"
    try:
        probe.symlink_to("elsewhere")
    except (OSError, NotImplementedError):
        return False
    probe.unlink()
    return True


class WorkingFilesTest(StampTestCase):
    def changes_the_key(self, change: Callable[[], object]) -> None:
        """Stamp the tree, apply `change`, and hold: the full gate runs, a new stamp is written for the new tree."""
        self.assertEqual(self.run_gate().returncode, 0)
        before = self.stamp()["key"]
        self.forget_log()
        change()
        run = self.run_gate()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue(self.checks(), "no check started: the old stamp was reused")
        self.assertTrue(run.stdout.endswith(f"{CLOSING}\n"))
        self.assertNotEqual(self.stamp()["key"], before, "a passing run left the old stamp")
        self.forget_log()
        self.run_gate()
        self.assertEqual(self.checks(), [], "the new stamp was not written for the tree the run judged")

    def test_a_tracked_edit_not_committed_runs_the_gate(self) -> None:
        """e2: one character of a tracked file."""
        self.changes_the_key(lambda: (self.repo / TRACKED).write_bytes((self.repo / TRACKED).read_bytes() + b"x"))

    def test_the_same_edit_committed_runs_the_gate(self) -> None:
        """e2: the edit, committed (a hold of the bytes the key began with)."""
        def change() -> None:
            (self.repo / TRACKED).write_bytes((self.repo / TRACKED).read_bytes() + b"x")
            commit_all(self.repo, "edit")
        self.changes_the_key(change)

    def test_a_new_untracked_file_runs_the_gate(self) -> None:
        """e2: a file git does not ignore appears."""
        self.changes_the_key(lambda: (self.repo / "notes.txt").write_text("new\n", encoding="utf-8"))

    def test_a_deleted_file_runs_the_gate(self) -> None:
        """e2: a tracked file deleted from disk is a value, not a failure."""
        self.changes_the_key(lambda: (self.repo / TRACKED).unlink())

    def test_an_executable_bit_runs_the_gate(self) -> None:
        """e2: `chmod +x` and nothing else."""
        if os.name == "nt":
            self.skipTest("no executable bit on this platform")
        path = self.repo / TRACKED
        path.chmod(0o644)
        git(self.repo, "update-index", "--chmod=-x", TRACKED)
        self.changes_the_key(lambda: path.chmod(0o755))

    def test_a_link_retargeted_runs_the_gate(self) -> None:
        """e2: a link's target is the key's, and two targets of the same bytes are two targets."""
        if not can_link(self.repo):
            self.skipTest("this platform cannot make a symbolic link")
        (self.repo / "target-a.txt").write_text("same\n", encoding="utf-8")
        (self.repo / "target-b.txt").write_text("same\n", encoding="utf-8")
        (self.repo / "pointer").symlink_to("target-a.txt")
        commit_all(self.repo, "a link")

        def retarget() -> None:
            (self.repo / "pointer").unlink()
            (self.repo / "pointer").symlink_to("target-b.txt")
        self.changes_the_key(retarget)

    def test_a_link_to_nothing_is_a_target_and_not_a_failure(self) -> None:
        """e2: a dangling link is read by its target, never followed."""
        if not can_link(self.repo):
            self.skipTest("this platform cannot make a symbolic link")
        (self.repo / "pointer").symlink_to("not-here.txt")
        commit_all(self.repo, "a dangling link")

        def retarget() -> None:
            (self.repo / "pointer").unlink()
            (self.repo / "pointer").symlink_to("nor-here")
        self.changes_the_key(retarget)


class FiltersAndStatsTest(StampTestCase):
    def runs_in_full(self, change: Callable[[], object]) -> None:
        self.assertEqual(self.run_gate().returncode, 0)
        self.forget_log()
        change()
        run = self.run_gate()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue(self.checks(), "no check started: the stamp was reused")

    def test_a_crlf_rewrite_under_the_lf_attribute_runs_the_gate(self) -> None:
        """e3: `* text=auto eol=lf` makes git see the same file; the key reads the bytes."""
        self.assertIn("* text=auto eol=lf", (self.repo / ".gitattributes").read_text(encoding="utf-8"))
        path = self.repo / TRACKED
        self.runs_in_full(lambda: path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n")))

    def test_a_same_size_rewrite_with_the_time_restored_runs_the_gate(self) -> None:
        """e3: no stat shortcut — size and modification time are as they were, the bytes are not."""
        path = self.repo / TRACKED
        was = path.stat()

        def rewrite() -> None:
            data = bytearray(path.read_bytes())
            data[0] = ord("#") if data[0] != ord("#") else ord("%")
            path.write_bytes(bytes(data))
            os.utime(path, ns=(was.st_atime_ns, was.st_mtime_ns))
        self.runs_in_full(rewrite)
        self.assertEqual(path.stat().st_size, was.st_size)

    def test_a_run_never_writes_the_index(self) -> None:
        """e3: the index file's bytes are equal before and after a run that reuses and one that does not."""
        index = self.repo / ".git" / "index"
        self.assertEqual(self.run_gate().returncode, 0)
        git(self.repo, "update-index", "--refresh")
        for name in ("a full run", "a reuse"):
            with self.subTest(name):
                if name == "a full run":
                    (self.repo / "notes.txt").write_text("new\n", encoding="utf-8")
                    git(self.repo, "update-index", "--refresh")
                before = index.read_bytes()
                run = self.run_gate()
                self.assertEqual(run.returncode, 0)
                self.assertEqual(index.read_bytes(), before)


class IndexEntriesTest(StampTestCase):
    def test_staging_an_untracked_file_with_the_same_bytes_runs_the_gate(self) -> None:
        """e4: the same names, modes and bytes; the entry in the index is new."""
        (self.repo / "notes.txt").write_text("same\n", encoding="utf-8")
        self.assertEqual(self.run_gate().returncode, 0)
        self.forget_log()
        git(self.repo, "add", "notes.txt")
        run = self.run_gate()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue(self.checks(), "no check started: the entry in the index was not in the key")

    def runs_in_full(self, change: Callable[[], object]) -> None:
        self.assertEqual(self.run_gate().returncode, 0)
        self.forget_log()
        change()
        run = self.run_gate()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue(self.checks(), "no check started: the entry in the index was not in the key")

    def test_a_changed_mode_in_the_index_alone_runs_the_gate(self) -> None:
        """e4: an entry's mode, with the working file untouched."""
        if os.name == "nt":
            self.skipTest("no executable bit on this platform")
        (self.repo / TRACKED).chmod(0o644)
        git(self.repo, "update-index", "--chmod=-x", TRACKED)
        self.runs_in_full(lambda: git(self.repo, "update-index", "--chmod=+x", TRACKED))

    def test_a_blob_staged_that_the_working_file_no_longer_holds_runs_the_gate(self) -> None:
        """e4: an entry's blob id, with the working file's bytes as they were."""
        path = self.repo / TRACKED
        was = path.read_bytes()

        def stage_another() -> None:
            path.write_bytes(was + b"staged\n")
            git(self.repo, "add", TRACKED)
            path.write_bytes(was)
        self.runs_in_full(stage_another)

    def test_an_entry_at_another_stage_runs_the_gate(self) -> None:
        """e4: an entry's stage, as a merge conflict leaves it."""
        blob = git(self.repo, "rev-parse", f"HEAD:{TRACKED}").strip()
        zero = "0" * 40
        entries = f"0 {zero}\t{TRACKED}\n100644 {blob} 2\t{TRACKED}\n"
        self.runs_in_full(lambda: subprocess.run(
            ["git", "update-index", "--index-info"], cwd=self.repo, input=entries, text=True, check=True))
