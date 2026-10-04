"""One sync per `make` run, at its edges (R1, AC-S04-38, -41, -44): a sync that fails, what a run prints, two goals.

A **hold** is true today and must stay true; each says so in its docstring and was seen to have teeth.
"""
from __future__ import annotations

import sys
import unittest

from parallel_gate import ParallelGateTestCase, run_lines, sync_lines, synced_projects

sys.dont_write_bytecode = True


class SyncEdgesTest(ParallelGateTestCase):
    SHAPE = "plain"

    def test_e11_a_sync_that_fails_stops_the_gate_with_no_check_started(self) -> None:
        """HOLD (AC-S04-38): with a `uv` whose `sync` exits non-zero, `make verify` and `make -j verify` exit non-zero
        and the log holds no run line."""
        for goals in (("verify",), ("-j", "verify")):
            with self.subTest(goals=goals):
                self.forget_log()
                done = self.make(*goals, env={"STANDIN_SYNC_FAIL": "1"})
                self.assertNotEqual(done.returncode, 0, done.stdout + done.stderr)
                self.assertEqual(run_lines(self.log), [], run_lines(self.log))

    def test_e14_a_run_prints_make_echo_of_the_sync_once_and_nothing_else_about_it(self) -> None:
        """AC-S04-41: the script's own `--install-only` run prints nothing, and `make verify`'s output holds exactly
        one line carrying `scripts/verify --install-only`: make's echo of the sync target's recipe."""
        done = self.make("verify")
        self.assert_passed(done)
        echoed = [line for line in done.stdout.splitlines() if "scripts/verify --install-only" in line]
        self.assertEqual(len(echoed), 1, done.stdout)
        self.assertEqual(done.stderr, "")
        quiet = self.run_in("./scripts/verify", "--install-only")
        self.assert_passed(quiet)
        self.assertEqual((quiet.stdout, quiet.stderr), ("", ""))

    def test_e15_two_goals_that_each_reach_the_gate_sync_at_most_twice_and_at_least_once(self) -> None:
        """AC-S04-44: `make verify lint` is two make processes (the gate's sub-make and the outer goal)."""
        self.assert_passed(self.make("verify", "lint"))
        count = len(synced_projects(self.log))
        self.assertTrue(0 < count <= 2, sync_lines(self.log))


if __name__ == "__main__":
    unittest.main()
