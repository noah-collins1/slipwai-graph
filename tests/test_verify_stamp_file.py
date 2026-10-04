"""R11 (AC-S03-27, -28): where the stamp lives and how long it lives.

One file per project per worktree under the git directory, never in the working tree, written by renaming a finished
file and never through a link; no expiry. A victim an example plants for a link to point at is inside the example's
own temporary directory, and what is read from the stand-ins' log is what ran.
"""
from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
from pathlib import Path

from stamp_fixture import CLOSING, StampTestCase, git

PLANTED_AT = "2026-01-01T00:00:00Z"


class FileTest(StampTestCase):
    def gate(
        self, cwd: Path | None = None, env: dict[str, str | None] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        """`make verify` in `cwd`, bounded well under the harness's: a gate that waits on a stamp is a failure."""
        child = subprocess.Popen(
            ["make", "verify"], cwd=cwd or self.repo, env=self.environment(env), text=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, start_new_session=True)
        try:
            out, err = child.communicate(timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)  # nothing is left waiting on a file
            child.communicate()
            raise
        return subprocess.CompletedProcess(child.args, child.returncode, out, err)

    def stamp_dir(self) -> Path:
        return self.repo / ".git" / "slipwai"

    def planted(self) -> tuple[bytes, Path]:
        """A stamp for the tree as it stands, and where it is."""
        bytes_ = self.plant_stamp()
        path = self.stamp_path()
        assert path is not None
        return bytes_, path

    def assert_replaced_as_itself(self, path: Path, run: subprocess.CompletedProcess[str]) -> None:
        """The gate ran in full and passed, and what stood at the stamp's path is now the stamp, a regular file."""
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue(self.checks(), "a stamp was read through something that is not a regular file")
        self.assertTrue(path.is_file() and not path.is_symlink(), f"{path} is not a regular file")
        self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["result"], "pass")
        self.assertTrue(run.stdout.endswith(f"\n\n{CLOSING}\n"), run.stdout[-200:])

    def test_nothing_of_the_stamp_shows_in_git_status_and_no_ignore_line_is_added(self) -> None:
        """e28: a passing run writes a stamp, and `git status --porcelain --ignored` names nothing of it."""
        ignore = (self.repo / ".gitignore").read_bytes()
        before = git(self.repo, "status", "--porcelain")
        run = self.gate()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIsNotNone(self.stamp_path(), "a passing run wrote no stamp")
        for flags in ((), ("--ignored",)):
            status = git(self.repo, "status", "--porcelain", *flags)
            self.assertNotIn("slipwai", status)
            self.assertNotIn("verify-stamp", status)
        self.assertEqual(git(self.repo, "status", "--porcelain"), before)
        self.assertEqual((self.repo / ".gitignore").read_bytes(), ignore)
        self.assertEqual(list(self.repo.rglob("verify-stamp-*")), list(self.stamp_dir().glob("verify-stamp-*")))

    def test_a_second_worktree_has_no_stamp_of_the_first_and_keeps_its_own(self) -> None:
        """e28: worktrees of one repository never share one stamp."""
        self.assertEqual(self.gate().returncode, 0)
        first, wanted = self.planted()
        other = self.repo.parent / "other-worktree"
        git(self.repo, "worktree", "add", "-q", "-b", "elsewhere", str(other))
        (other / "apps" / "service" / ".venv").mkdir(parents=True)
        shutil.copy(self.repo / "apps" / "service" / ".venv" / "pyvenv.cfg", other / "apps" / "service" / ".venv")
        theirs = Path(git(other, "rev-parse", "--absolute-git-dir").strip()) / "slipwai"
        self.assertNotEqual(theirs, self.stamp_dir())
        self.assertEqual(list(theirs.glob("verify-stamp-*.json")), [], "a new worktree starts with a stamp")
        self.forget_log()
        run = self.gate(other)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue(self.checks(), "the second worktree reused the first one's stamp")
        self.assertEqual(wanted.read_bytes(), first)
        self.assertEqual(self.gate(other).returncode, 0)
        self.assertEqual(len(list(theirs.glob("verify-stamp-*.json"))), 1)

    def test_two_projects_in_one_repository_have_two_files_and_reuse_their_own(self) -> None:
        """e28 (D36): a project beside the first, in a directory of the same repository."""
        second = self.repo / "second"
        shutil.copytree(self.repo, second, ignore=shutil.ignore_patterns(".git"), symlinks=True)
        for directory in (self.repo, second):
            self.assertEqual(self.gate(directory).returncode, 0)
        files = sorted(self.stamp_dir().glob("verify-stamp-*.json"))
        self.assertEqual(len(files), 2, files)
        contents = [path.read_bytes() for path in files]
        for directory in (self.repo, second):
            with self.subTest(directory.name):
                self.forget_log()
                run = self.gate(directory)
                self.assertEqual(self.checks(), [], run.stdout)
                self.assertIn("did not run", run.stdout)
        self.assertEqual([path.read_bytes() for path in files], contents)

    def test_a_link_at_the_stamp_path_is_not_read_and_is_replaced_as_itself(self) -> None:
        """e28: the link is removed, not what it points to, which stays what it was."""
        bytes_, path = self.planted()
        victim = self.repo.parent / "victim-stamp.json"
        victim.write_bytes(bytes_)
        path.unlink()
        path.symlink_to(victim)
        self.forget_log()
        self.assert_replaced_as_itself(path, self.gate())
        self.assertEqual(victim.read_bytes(), bytes_, "a link at the stamp's path was written through")

    def test_a_link_to_a_directory_at_the_stamp_path_is_replaced_and_the_directory_stays(self) -> None:
        """e28: removed as itself, never as what it points at."""
        _, path = self.planted()
        victim = self.repo.parent / "victim-directory"
        victim.mkdir()
        (victim / "keep.txt").write_text("keep\n", encoding="utf-8")
        path.unlink()
        path.symlink_to(victim, target_is_directory=True)
        self.forget_log()
        self.assert_replaced_as_itself(path, self.gate())
        self.assertEqual(sorted(p.name for p in victim.iterdir()), ["keep.txt"])

    def test_an_empty_directory_at_the_stamp_path_is_replaced(self) -> None:
        """e28: a directory is not a stamp; an empty one is removed as itself and the stamp takes its place."""
        _, path = self.planted()
        path.unlink()
        path.mkdir()
        self.forget_log()
        self.assert_replaced_as_itself(path, self.gate())

    def test_a_directory_with_something_in_it_at_the_stamp_path_is_refused_by_name(self) -> None:
        """e28: not deleted wholesale — one line names it, the gate runs, nothing is written into it."""
        _, path = self.planted()
        path.unlink()
        path.mkdir()
        (path / "keep.txt").write_text("keep\n", encoding="utf-8")
        self.forget_log()
        run = self.gate()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue(self.checks())
        self.assertEqual(len([line for line in self.reuse_lines(run) if path.name in line]), 1, run.stdout)
        self.assertEqual(sorted(p.name for p in path.iterdir()), ["keep.txt"])

    def test_a_fifo_at_the_stamp_path_is_not_opened(self) -> None:
        """e28: opening one for reading waits for a writer that never comes; it is removed as itself."""
        if not hasattr(os, "mkfifo"):
            self.skipTest("this platform makes no FIFO")
        _, path = self.planted()
        path.unlink()
        os.mkfifo(path)
        self.forget_log()
        self.assert_replaced_as_itself(path, self.gate())

    def test_a_link_where_the_stamp_directory_goes_is_not_written_through(self) -> None:
        """e28: the directory of the factory's own is a real one; a link in its place is replaced, and what it
        pointed to receives nothing."""
        victim = self.repo.parent / "victim-directory"
        victim.mkdir()
        self.stamp_dir().symlink_to(victim, target_is_directory=True)
        run = self.gate()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(list(victim.iterdir()), [], "the stamp directory was written through a link")
        self.assertTrue(self.stamp_dir().is_dir() and not self.stamp_dir().is_symlink())
        self.assertIsNotNone(self.stamp_path())

    def test_a_link_where_the_stamp_directory_goes_is_neither_read_nor_removed_through(self) -> None:
        """e28: a stamp that stands behind the link is not reused, not removed and not replaced."""
        bytes_, path = self.planted()
        victim = self.repo.parent / "victim-directory"
        shutil.move(str(self.stamp_dir()), victim)
        self.stamp_dir().symlink_to(victim, target_is_directory=True)
        self.forget_log()
        run = self.gate()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue(self.checks(), "a stamp behind a link was read")
        self.assertEqual((victim / path.name).read_bytes(), bytes_)
        self.assertEqual(sorted(p.name for p in victim.iterdir()), [path.name])

    def test_a_link_at_the_note_path_is_not_read_or_written_through(self) -> None:
        """e28: the note a run leaves for `record` is replaced as itself, and the pass is recorded."""
        self.assertEqual(self.gate().returncode, 0)
        note = self.stamp_dir() / self.stamp_path().name.replace(".json", ".pending")  # type: ignore[union-attr]
        victim = self.repo.parent / "victim-note"
        victim.write_text('{"key": "forged", "tools": {}}\n', encoding="utf-8")
        note.symlink_to(victim)
        (self.repo / "moved.txt").write_text("moved\n", encoding="utf-8")
        run = self.gate()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(victim.read_text(encoding="utf-8"), '{"key": "forged", "tools": {}}\n')
        self.assertFalse(note.exists() or note.is_symlink(), "the note was left behind")
        self.assertEqual(len([line for line in run.stdout.splitlines() if "not recorded" in line]), 0, run.stdout)

    def test_a_directory_with_something_in_it_at_the_note_path_is_named_and_the_run_records_nothing(self) -> None:
        """e28, brought to AC-S03-36 (an empty one is removed as itself, `test_verify_stamp_exact`): nothing can be
        renamed onto it and it is not emptied, so one line names the directory to delete and the gate's exit stands."""
        self.assertEqual(self.gate().returncode, 0)
        path = self.stamp_path()
        assert path is not None
        note = path.with_suffix(".pending")
        note.mkdir()
        (note / "keep").write_text("", encoding="utf-8")
        (self.repo / "moved.txt").write_text("moved\n", encoding="utf-8")
        run = self.gate()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        lines = [line for line in run.stdout.splitlines() if note.name in line]
        self.assertEqual(len(lines), 1, run.stdout)
        self.assertIn("delete that directory", lines[0])
        self.assertIsNone(self.stamp_path(), "a run that could not leave its note recorded a pass")

    def test_a_stamp_of_any_age_is_reused_and_its_instant_shown(self) -> None:
        """e27: ten years old, still reused: the instant is shown and never compared."""
        _, path = self.planted()
        stamp = json.loads(path.read_text(encoding="utf-8"))
        stamp["passed"] = "2016-01-01T00:00:00Z"
        path.write_text(json.dumps(stamp, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        self.forget_log()
        run = self.gate()
        self.assertEqual(self.checks(), [])
        self.assertIn("2016-01-01T00:00:00Z", run.stdout)

    def test_deleting_the_stamp_has_the_effect_of_forcing(self) -> None:
        """e27: with the file gone the gate runs in full, and writes one."""
        _, path = self.planted()
        path.unlink()
        self.forget_log()
        run = self.gate()
        self.assertTrue(self.checks(), run.stdout)
        self.assertNotEqual(self.stamp()["passed"], PLANTED_AT)
