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

    def test_the_line_for_a_file_a_check_wrote_says_which_part_moved_and_what_to_do(self) -> None:
        """e11 (T034, D81): the files; a check may have written one, `git status` shows it, the next run records."""
        run = self.run_gate({"STANDIN_EDIT": "README.md"})
        line = self.not_recorded(run)[0]
        self.assertIn("a file changed", line)
        self.assertIn("a check may have written one", line)
        self.assertIn("git status", line)
        self.assertIn("next run records", line)
        self.assertNotIn("README.md", line, "no list of files is kept between the two halves of a run")
        self.assertNotIn("README.md", "".join(p.read_text(encoding="utf-8") for p in self.stamp_directory().iterdir()))
        self.forget_log()
        again = self.run_gate()
        self.assertEqual(self.not_recorded(again), [])
        self.assertIsNotNone(self.stamp_path(), "the next run did not record")

    def test_the_line_for_a_gate_script_a_check_wrote_says_so(self) -> None:
        """e11 (T034): the part is named — the `Makefile` and `scripts/`, which are the gate."""
        line = self.not_recorded(self.run_gate({"STANDIN_EDIT": "Makefile"}))[0]
        self.assertIn("scripts", line)
        self.assertIn("a check may have written one", line)

    def test_the_line_for_the_index_does_not_say_a_file_was_written(self) -> None:
        """e11 (T034): where it is not the files, the files' advice is not given."""
        run = self.run_gate({"STANDIN_STAGE": "README.md"})
        lines = self.not_recorded(run)
        self.assertEqual(len(lines), 1, run.stdout)
        self.assertIn("index", lines[0])
        self.assertNotIn("a check may have written one", lines[0])

    def test_a_directory_at_the_stamps_path_is_called_a_directory(self) -> None:
        """e26 (T034): with something in it nothing is emptied; the line says to delete the directory."""
        self.plant_stamp()
        path = self.stamp_path()
        assert path is not None
        path.unlink()
        path.mkdir()
        (path / "keep").write_text("", encoding="utf-8")
        self.move_tree()
        run = self.run_gate()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        lines = [line for line in self.reuse_lines(run) if path.name in line]
        self.assertEqual(len(lines), 1, run.stdout)
        self.assertIn("directory", lines[0])
        self.assertNotIn("delete that file", lines[0])

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

    def test_a_stamp_that_stood_does_not_stand_through_a_run_that_ignores_errors_and_fails(self) -> None:
        """e26 (T019): a stamp for exactly this tree, then `make -i verify` with a check that fails: the checks run, the
        sub-make exits 0, and no stamp is left for the next plain run to reuse. A ratchet run is not among them (D80):
        it touches nothing, which `RatchetTest` holds."""
        for flags in (["-i"], ["-ik"], ["--ignore-errors"]):
            with self.subTest(" ".join(flags)):
                self.plant_stamp()
                self.forget_log()
                run = self.run_gate({"STANDIN_UV_FAIL": "1"}, flags)
                self.assertTrue(self.checks(), "the gate did not run: " + run.stdout)
                self.assertIsNone(self.stamp_path(), "a stamp stood through a run whose check failed")
                self.forget_log()
                again = self.run_gate()
                self.assertTrue(self.checks(), "the next plain run reused a stamp: " + again.stdout)

    def test_a_run_that_tightens_the_ratchet_and_ignores_errors_touches_nothing(self) -> None:
        """e26 hold (T029, D80, D81): the ratchet rule is asked first and wins, so `-i` removes nothing, writes nothing
        and leaves no note, whatever the checks do."""
        planted = self.plant_stamp()
        path = self.stamp_path()
        assert path is not None
        before = sorted(path.parent.iterdir())
        for fail in (None, "1"):
            with self.subTest(f"a check fails: {fail}"):
                self.forget_log()
                run = self.run_gate({"RATCHET_TIGHTEN": "1", "STANDIN_UV_FAIL": fail}, ["-i"])
                self.assertTrue(self.checks(), "the gate did not run: " + run.stdout)
                self.assertEqual(self.reuse_lines(run), [], run.stdout)
                self.assertEqual(path.read_bytes(), planted)
                self.assertEqual(sorted(path.parent.iterdir()), before)

    def test_a_stamp_that_cannot_be_removed_under_dash_i_is_named(self) -> None:
        """e26 (T019): the same run where the stamp cannot be removed says which file to delete, as a plain run does."""
        self.plant_stamp()
        path = self.stamp_path()
        assert path is not None
        self.read_only(path.parent)
        run = self.run_gate({"STANDIN_UV_FAIL": "1"}, ["-i"])
        self.assertTrue(self.checks(), "the gate did not run")
        self.assertEqual(len([line for line in self.reuse_lines(run) if path.name in line]), 1, run.stdout)

    def test_a_reuse_that_fails_in_a_way_nobody_foresaw_still_removes_the_stamp(self) -> None:
        """e26 (T019): `reuse` raising something other than the script's own refusal (here an unreadable `shallow`
        that is a directory, found while the key is built) runs every check, and the stamp that stood is gone."""
        self.plant_stamp()
        (self.repo / ".git" / "shallow").mkdir()
        self.forget_log()
        run = self.run_gate({"STANDIN_UV_FAIL": "1"})
        self.assertTrue(self.checks(), "the gate did not run: " + run.stdout)
        self.assertIsNone(self.stamp_path(), "a stamp stood through a run whose reuse failed")
