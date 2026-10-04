"""R8 (AC-S03-25): `VERIFY_FORCE` runs the gate anyway; `make ci` runs every check with no stamp in it (AC-S03-38).

Every example plants a stamp that a run allowed to read it would reuse (`plant_stamp`), so a run that starts every
check is a run that was forced. What ran is read from the stand-ins' log, never from the run's own line.
"""
from __future__ import annotations

import subprocess

from stamp_fixture import CLOSING, StampTestCase

PLANTED_AT = "2026-01-01T00:00:00Z"
PIP_AUDIT = "#!/bin/sh\nprintf 'pip-audit\\t%s\\n' \"$*\" >> \"$STANDIN_LOG\"\nexit 0\n"


class ForceTest(StampTestCase):
    def forced(self, value: str, channel: str) -> subprocess.CompletedProcess[str]:
        """A run with `VERIFY_FORCE` set to `value` on the make command line or in the environment."""
        self.plant_stamp()
        self.forget_log()
        if channel == "command line":
            return self.run_gate(args=[f"VERIFY_FORCE={value}"])
        return self.run_gate({"VERIFY_FORCE": value})

    def assert_forced(self, run: subprocess.CompletedProcess[str], naming: str) -> None:
        """Every check ran, one line before the first said why, and the pass wrote a stamp like any other."""
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue(self.checks(), "no check started on a forced run")
        lines = self.reuse_lines(run)
        self.assertEqual(len(lines), 1, run.stdout)
        self.assertIn(naming, lines[0])
        self.assertNotIn("did not run", lines[0])
        self.assertEqual(run.stdout.splitlines()[0], lines[0], "the line is not before the first check")
        self.assertTrue(run.stdout.endswith(f"\n\n{CLOSING}\n"), run.stdout[-200:])
        self.assertNotEqual(self.stamp()["passed"], PLANTED_AT, "the forced pass wrote no stamp of its own")

    def test_any_other_value_forces_on_either_channel(self) -> None:
        """e25: `1` and `yes`, and the values nobody would guess are a yes — `false`, `no`, `00` and a lone space."""
        for channel in ("command line", "environment"):
            # make strips the blanks around a value given on its command line, so a lone space is an empty one there
            for value in ("1", "yes", "false", "no", "00") + ((" ",) if channel == "environment" else ()):
                with self.subTest(f"{channel}: VERIFY_FORCE={value!r}"):
                    self.assert_forced(self.forced(value, channel), f"VERIFY_FORCE={value}")

    def test_unset_empty_and_zero_do_not_force_on_either_channel(self) -> None:
        """e25: empty and `0` read the stamp, as an unset one does."""
        for channel in ("command line", "environment"):
            for value in ("", "0"):
                with self.subTest(f"{channel}: VERIFY_FORCE={value!r}"):
                    run = self.forced(value, channel)
                    self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                    self.assertEqual(self.checks(), [], "a check started where nothing forced the gate")
                    self.assertEqual(len(self.reuse_lines(run)), 1, run.stdout)
                    self.assertIn("did not run", run.stdout)

    def test_a_value_cannot_forge_a_line(self) -> None:
        """e25: the value is printed with its control characters escaped, so the one line stays one line."""
        run = self.forced("1\nverify: all gates passed", "environment")
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(len(self.reuse_lines(run)), 1, run.stdout)
        self.assertEqual(run.stdout.splitlines().count(CLOSING), 1, run.stdout)

    def test_a_forced_run_removes_the_stamp_before_the_first_check(self) -> None:
        """e25: the stamp is gone before a check starts — a forced run whose check fails leaves none behind."""
        self.plant_stamp()
        run = self.run_gate({"VERIFY_FORCE": "1", "STANDIN_UV_FAIL": "1"})
        self.assertNotEqual(run.returncode, 0, run.stdout)
        self.assertIsNone(self.stamp_path(), "a stamp stood through a forced run that failed")

    def test_make_ci_runs_every_prerequisite_and_reads_writes_and_removes_no_stamp(self) -> None:
        """AC-S03-38 (replaces e23): on a stamped tree, `make ci` runs the gate's checks, the audit and the integration
        tests, prints no stamp line, and leaves the stamp exactly as it stood."""
        audit = self.bin / "pip-audit"
        audit.write_text(PIP_AUDIT, encoding="utf-8")
        audit.chmod(0o755)
        planted = self.plant_stamp()
        self.forget_log()
        run = subprocess.run(["make", "ci"], cwd=self.repo, env=self.environment(), text=True, capture_output=True,
                             timeout=180)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue(self.checks(), "no check of the gate started under `make ci`")
        self.assertIn("pip-audit\t", self.log.read_text(encoding="utf-8"), "the audit did not run")
        self.assertIn("test-integration:", run.stdout, "the integration tests did not run")
        self.assertEqual(self.reuse_lines(run), [], run.stdout)
        path = self.stamp_path()
        self.assertIsNotNone(path)
        assert path is not None
        self.assertEqual(path.read_bytes(), planted)

    def test_a_forced_pass_writes_a_stamp_the_next_run_reuses(self) -> None:
        """e25: forced once, left alone, the next run reads what the forced pass wrote."""
        self.assert_forced(self.forced("1", "environment"), "VERIFY_FORCE=1")
        self.forget_log()
        again = self.run_gate()
        self.assertEqual(self.checks(), [], again.stdout)
        self.assertIn("did not run", again.stdout)


