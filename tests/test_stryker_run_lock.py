"""S41 T038 (A4 · D212 item 7): two runs in one service never read each other's report.

A scoped run that crashes writes no report; a sweep started beside it removes the report directory and writes its own,
and the crashed run then passes on the sweep's report. The wrapper holds one lock per service for a run, recording its
holder's pid, so the second run waits for the first and a lock whose holder is gone is broken. The fake `npm` here
sleeps in a scoped run (`scoped_sleep`) and exits 1 writing nothing, and writes the plan's report in any other.
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import unittest

from test_stryker_verdict import REPORT, SCRIPT, SERVICE, VerdictCase, mutant, report

sys.dont_write_bytecode = True
TEST_SELECTION = {"reads": ["assets/languages/typescript/scripts/stryker-mutation.py",
                            "assets/toolkit/scripts/check-styles.py"]}
PLAN = {"scoped_sleep": 3, "report": report(src__health_ts=[mutant("Killed")])}


class RunLockTest(VerdictCase):
    def start(self, *arguments: str) -> subprocess.Popen[str]:
        self.plan.write_text(json.dumps(PLAN), encoding="utf-8")
        env = {**os.environ, "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}", "FAKE_LOG": str(self.log),
               "FAKE_PLAN": str(self.plan)}
        for marker in ("CI", "GITHUB_ACTIONS", "GITLAB_CI"):
            env.pop(marker, None)
        return subprocess.Popen([sys.executable, "-B", str(SCRIPT), SERVICE, *arguments], cwd=self.tree, env=env,
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    def started(self) -> None:
        """Wait until the first run has started Stryker, so it holds whatever it is going to hold."""
        deadline = time.time() + 20
        while not self.execs():
            self.assertLess(time.time(), deadline, "the first run never started Stryker")
            time.sleep(0.05)

    def test_e1_a_sweep_started_beside_a_scoped_run_waits_and_the_scoped_run_never_passes_on_its_report(self) -> None:
        first = self.start("--file", "src/health.ts")
        self.addCleanup(first.kill)
        self.started()
        code, lines = self.run_wrapper(PLAN)
        out, _ = first.communicate(timeout=60)
        self.assertEqual(first.returncode, 1, out)
        self.assertIn(f"mutation: Stryker exited 1 and left no readable report at {REPORT}; that is not a pass", out)
        self.assertEqual(code, 0, lines)
        self.assertTrue(any("another run of" in line and "waiting" in line for line in lines), lines)
        self.assertEqual(lines[-1], "mutation: 1 mutants: 1 killed, 0 ignored, 0 not covered (reported, never failed); "
                                    f"passed — report {REPORT}")

    def test_e2_a_lock_whose_holder_was_killed_does_not_hold_the_next_run(self) -> None:
        first = self.start("--file", "src/health.ts")
        self.addCleanup(first.kill)
        self.started()
        locks = list((self.tree / ".stryker-tmp").glob("run-*.lock"))
        self.assertEqual(len(locks), 1, "the run holds no lock where every shell finds it")
        self.assertEqual(locks[0].read_text(encoding="utf-8").split()[0], str(first.pid))
        os.kill(first.pid, signal.SIGKILL)
        first.communicate(timeout=30)
        begun = time.time()
        code, lines = self.run_wrapper(PLAN)
        self.assertEqual(code, 0, lines)
        self.assertLess(time.time() - begun, 20, lines)
        self.assertFalse(locks[0].exists(), "the finished run left its lock")


if __name__ == "__main__":
    unittest.main()
