"""R9 (AC-S03-10, -11, -26): a stamp is written only by a run in which everything ran and passed.

A run that fails, is killed, runs under make's `-i`, `-n`, `-t` or `-q`, finds the tree moved under it, or cannot
write where the stamp goes, leaves no stamp for a key it did not pass, and never changes the gate's exit code.
"""
from __future__ import annotations

import os
import signal
import subprocess
import threading
from pathlib import Path

from stamp_fixture import CLOSING, StampTestCase

NOT_RECORDED = "not recorded"


class RunsTest(StampTestCase):
    def move_tree(self) -> None:
        """A change to the tree, so the planted stamp is for a key it no longer has."""
        (self.repo / "moved.txt").write_text("moved\n", encoding="utf-8")

    def not_recorded(self, run: subprocess.CompletedProcess[str]) -> list[str]:
        return [line for line in run.stdout.splitlines() if NOT_RECORDED in line]

    def stamp_directory(self) -> Path:
        directory = self.repo / ".git" / "slipwai"
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def read_only(self, directory: Path) -> None:
        """`directory` that nothing can be created or removed in, restored when the test ends (the scratch removal,
        registered first, runs after)."""
        directory.chmod(0o555)
        self.addCleanup(directory.chmod, 0o755)
        try:
            (directory / "probe").write_text("", encoding="utf-8")
        except OSError:
            return
        (directory / "probe").unlink()
        self.skipTest("this account can write where a directory is read-only")

    def test_a_failing_check_leaves_no_stamp_though_one_stood_before(self) -> None:
        """e26: the stamp is removed before the first check, and a run that failed writes none."""
        self.plant_stamp()
        self.move_tree()
        run = self.run_gate({"STANDIN_UV_FAIL": "1"})
        self.assertNotEqual(run.returncode, 0, run.stdout)
        self.assertIsNone(self.stamp_path(), "a stamp stood through a run whose check failed")

    def test_a_run_killed_in_the_middle_of_the_gate_leaves_no_stamp(self) -> None:
        """e26: killed while a check runs, the stamp that stood is gone, and the next run is whole and writes one."""
        self.plant_stamp()
        self.move_tree()
        child = subprocess.Popen(
            ["make", "verify"], cwd=self.repo, env=self.environment({"STANDIN_UV_HANG": "1"}), text=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True,
        )
        stop = threading.Timer(120, os.killpg, (child.pid, signal.SIGKILL))  # a bound, not a wait
        stop.start()
        try:
            assert child.stdout is not None
            for line in child.stdout:
                if "waiting (stand-in)" in line:
                    break
            else:
                self.fail("the gate never reached its checks")
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()
        finally:
            stop.cancel()
            if child.stdout is not None:
                child.stdout.close()
        self.assertIsNone(self.stamp_path(), "a stamp stood through a run that was killed")
        again = self.run_gate()
        self.assertEqual(again.returncode, 0, again.stdout + again.stderr)
        self.assertNotEqual(self.stamp()["passed"], "2026-01-01T00:00:00Z")

    def test_make_dash_i_on_a_failing_tree_leaves_no_stamp(self) -> None:
        """e10: `-i` has the checks' failures ignored, the sub-make exits 0, and nothing here may take that for a pass;
        with `-k` as well, and with the two spelled as one."""
        for flags in (["-i"], ["-i", "-k"], ["-ik"], ["--ignore-errors"]):
            with self.subTest(" ".join(flags)):
                run = self.run_gate({"STANDIN_UV_FAIL": "1"}, flags)
                self.assertEqual(self.reuse_lines(run), [], run.stdout)
                self.assertIsNone(self.stamp_path(), "a pass was recorded under -i")

    def test_dry_run_touch_and_question_mode_neither_read_nor_write_a_stamp(self) -> None:
        """e10: on a stamped tree the stamp's bytes stand and there is no reuse line; on one whose key moved it is not
        removed either."""
        planted = self.plant_stamp()
        path = self.stamp_path()
        assert path is not None
        for moved in (False, True):
            if moved:
                self.move_tree()
            for flag in ("-n", "-t", "-q", "-nk"):
                with self.subTest(f"{flag}, key moved: {moved}"):
                    self.forget_log()
                    run = self.run_gate(args=[flag])
                    self.assertEqual(self.reuse_lines(run), [], run.stdout)
                    self.assertEqual(self.checks(), [], "a check started under a mode that runs none")
                    self.assertEqual(path.read_bytes(), planted)

    def test_a_key_that_moved_during_the_run_is_a_pass_not_recorded_and_one_line_says_so(self) -> None:
        """e11: a check that edits a tracked file; exit 0, the closing line, one line, no stamp."""
        run = self.run_gate({"STANDIN_EDIT": "README.md"})
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue(run.stdout.endswith(f"\n\n{CLOSING}\n") or run.stdout.splitlines()[-2:-1] == [CLOSING],
                        run.stdout[-300:])
        self.assertEqual(len(self.not_recorded(run)), 1, run.stdout)
        self.assertIsNone(self.stamp_path())

    def test_a_stamp_directory_nothing_can_be_written_in_is_a_pass_not_recorded(self) -> None:
        """e11: exit 0, the closing line, one line with the reason, and nothing written."""
        directory = self.stamp_directory()
        self.read_only(directory)
        run = self.run_gate()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn(CLOSING, run.stdout.splitlines())
        lines = self.not_recorded(run)
        self.assertEqual(len(lines), 1, run.stdout)
        self.assertRegex(lines[0], r"(?i)permission|denied|read-only|cannot write")
        self.assertEqual(sorted(directory.iterdir()), [])

    def test_a_stamp_that_cannot_be_removed_is_named_and_the_run_writes_none(self) -> None:
        """e26: one line names the file to delete, the gate runs, exit 0, and the stamp that stood is not replaced."""
        planted = self.plant_stamp()
        path = self.stamp_path()
        assert path is not None
        self.move_tree()
        self.read_only(path.parent)
        run = self.run_gate()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue(self.checks(), "the gate did not run")
        lines = [line for line in self.reuse_lines(run) if path.name in line]
        self.assertEqual(len(lines), 1, run.stdout)
        self.assertEqual(len(self.reuse_lines(run)), 1, run.stdout)
        self.assertEqual(path.read_bytes(), planted)

    def test_a_passing_run_removes_the_stamp_for_another_key_and_writes_its_own(self) -> None:
        """e26's border: a pass on a moved tree replaces the stamp, so no stamp ever stands for a key that was not
        passed last."""
        planted = self.plant_stamp()
        self.move_tree()
        run = self.run_gate()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertNotEqual(self.stamp_path().read_bytes(), planted)  # type: ignore[union-attr]
        self.assertEqual(self.not_recorded(run), [])
