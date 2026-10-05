"""R2 (AC-S06-10): a stamp is stronger than any scoped run.

On a slice branch, before reading any change, `verify-scoped` builds the key `verify-stamp.py` would build and compares
it with the stamp: equal prints verify-stamp's own reuse line and exits 0, and no check starts. The script never writes,
removes or refreshes a stamp; only `make verify`'s recipe does. What ran is read from the stand-ins' log and the stamp
file's own bytes, never from a line a run printed about itself.
"""
from __future__ import annotations

import subprocess
import sys
import unittest

from scoped_fixture import FULL, ScopedCase
from stamp_fixture import commit_all, load_script

sys.dont_write_bytecode = True

SCOPED = "verify-scoped.py"


class StampTest(ScopedCase):
    def green(self) -> bytes:
        """A green `make verify` on the slice branch, and the stamp it left."""
        run = self.run_gate()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        path = self.stamp_path()
        self.assertIsNotNone(path, "the green run left no stamp")
        assert path is not None
        self.forget_log()
        return path.read_bytes()

    def started(self) -> list[str]:
        """What the stand-ins saw that is a check starting, or the full gate asked for: not a version question, not
        the stamp's or this script's own launch."""
        found = []
        for line in self.log.read_text(encoding="utf-8").splitlines() if self.log.exists() else []:
            tool, _, arguments = line.partition("\t")
            asked = arguments == "--version" or SCOPED in arguments or "verify-stamp.py" in arguments
            if tool in ("uv", "python3") and not asked:
                found.append(line)
        return [*found, *self.verify_calls()]

    def reuse_line(self) -> str:
        stamp = self.stamp()
        return str(load_script(self.repo).REUSE_LINE).format(passed=stamp["passed"], abbreviated=str(stamp["key"])[:12])

    def assert_reused(self, run: subprocess.CompletedProcess[str], was: bytes) -> None:
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(self.reuse_lines(run), [self.reuse_line()])
        self.assertEqual(self.scoped_lines(run), [])
        self.assertEqual(self.started(), [], "a check or the full gate started")
        path = self.stamp_path()
        assert path is not None
        self.assertEqual(path.read_bytes(), was)

    def test_e1_a_stamp_that_stands_is_reused_with_the_stamps_line_and_no_check_starts(self) -> None:
        was = self.green()
        self.assert_reused(self.scoped(), was)

    def test_e2_an_edit_after_it_runs_a_selection_and_leaves_the_stamp_untouched(self) -> None:
        was = self.green()
        path = self.stamp_path()
        assert path is not None
        before = path.stat().st_mtime_ns
        (self.repo / "apps" / "service" / "extra.txt").write_text("an edit after the green run\n", encoding="utf-8")
        run = self.scoped()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(self.reuse_lines(run), [], "the stamp was reused for another tree")
        self.assertTrue(self.started(), "no check ran for an edited tree")
        self.assertEqual(path.read_bytes(), was)
        self.assertEqual(path.stat().st_mtime_ns, before)

    def test_e3_a_scoped_run_that_fails_leaves_no_stamp_written(self) -> None:
        (self.repo / "apps" / "service" / "extra.txt").write_text("an edit\n", encoding="utf-8")
        run = self.scoped({"STANDIN_UV_FAIL": "1"})
        self.assertNotEqual(run.returncode, 0, run.stdout)
        self.assertTrue(self.started(), "no check ran")
        self.assertIsNone(self.stamp_path(), "a failed scoped run wrote a stamp")

    def test_e3_a_scoped_pass_writes_no_stamp_either(self) -> None:
        (self.repo / "apps" / "service" / "extra.txt").write_text("an edit\n", encoding="utf-8")
        self.assertEqual(self.scoped().returncode, 0)
        self.assertIsNone(self.stamp_path(), "a scoped run wrote a stamp")

    def test_e4_hold_a_forced_run_is_the_full_gate_not_the_reuse_line(self) -> None:
        """HOLD (teeth: the forced border returning None lets the stamp answer first and this fails)."""
        self.green()
        run = self.scoped({"VERIFY_FORCE": "1"})
        self.assertEqual(self.scoped_lines(run), [FULL + "VERIFY_FORCE=1"], run.stdout)
        self.assertEqual(self.reuse_lines(run), ["verify: the full gate runs, forced by VERIFY_FORCE=1"])
        self.assertEqual(len(self.verify_calls()), 1)

    def test_e5_the_key_is_built_with_the_tools_the_stamp_would_ask(self) -> None:
        was = self.plant_stamp()
        self.forget_log()
        self.assert_reused(self.scoped(), was)
        self.forget_log()
        run = self.scoped({"STANDIN_UV_VERSION": "uv 0.99.0 (another)"})
        self.assertNotIn(self.reuse_line(), run.stdout, "a machine whose uv answers differently reused the stamp")

    def test_e5_one_example_per_environment_the_project_records(self) -> None:
        makefile = self.repo / "Makefile"
        text = makefile.read_text(encoding="utf-8")
        other = self.repo / "apps" / "other" / ".venv"
        other.mkdir(parents=True)
        config = other / "pyvenv.cfg"
        config.write_text("home = /usr/bin\nversion_info = 3.14.4\nuv = 0.12.20\n", encoding="utf-8")
        makefile.write_text(text.replace("--environment apps/service/.venv",
                                         "--environment apps/service/.venv --environment apps/other/.venv"),
                            encoding="utf-8")
        commit_all(self.repo, "a second environment")
        was = self.plant_stamp()
        self.forget_log()
        self.assert_reused(self.scoped(), was)
        config.write_text("home = /usr/bin\nversion_info = 3.13.9\nuv = 0.12.20\n", encoding="utf-8")
        self.forget_log()
        run = self.scoped()
        self.assertNotIn(self.reuse_line(), run.stdout, "the second environment was not part of the key")


if __name__ == "__main__":
    unittest.main()
