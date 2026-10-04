"""One sync per `make` run (R1, AC-S04-28 to -33): the gate, `-j`, two services, two goals, and a mode on its own.

The Python project is a generated one with no transport, so its gate passes against stand-in tools; evidence is the
stand-in `uv`'s log (`tests/parallel_gate.py`), never a printed line. A **hold** is an example that is true today and
must stay true; each says so in its docstring and was seen to have teeth.
"""
from __future__ import annotations

import sys
import unittest

from parallel_gate import (
    ParallelGateTestCase,
    log_text,
    run_lines,
    sync_lines,
    synced_projects,
    syncs_precede_runs,
)

sys.dont_write_bytecode = True

MODES = ("--lint-only", "--typecheck-only", "--test-only", "")


class OneProjectTest(ParallelGateTestCase):
    SHAPE = "plain"

    def test_e1_make_verify_syncs_the_service_once(self) -> None:
        """AC-S04-28: `make verify` in full leaves one sync line for the service's `--project`."""
        self.assert_passed(self.make("verify"))
        self.assertEqual(synced_projects(self.log), ["apps/service"], sync_lines(self.log))
        self.assertTrue(run_lines(self.log), "the gate ran nothing")

    def test_e2_make_j_verify_syncs_once_and_before_any_run(self) -> None:
        """AC-S04-29: under `-j`, one sync per service, and every sync line precedes the first run line."""
        self.assert_passed(self.make("-j", "verify"))
        self.assertEqual(synced_projects(self.log), ["apps/service"], sync_lines(self.log))
        self.assertTrue(syncs_precede_runs(self.log), log_text(self.log))

    def test_e4_two_goals_in_one_command_sync_once(self) -> None:
        """AC-S04-31: `make lint test` is one make process, so one sync."""
        self.assert_passed(self.make("lint", "test"))
        self.assertEqual(synced_projects(self.log), ["apps/service"], sync_lines(self.log))

    def test_e5_each_mode_target_alone_syncs_once_before_it_runs_anything(self) -> None:
        """HOLD (AC-S04-32): `make lint`, `make typecheck` and `make test` alone each sync once, first."""
        for target in ("lint", "typecheck", "test"):
            with self.subTest(target=target):
                self.forget_log()
                self.assert_passed(self.make(target))
                self.assertEqual(synced_projects(self.log), ["apps/service"], sync_lines(self.log))
                self.assertTrue(syncs_precede_runs(self.log), log_text(self.log))

    def test_e6_a_mode_typed_directly_syncs_first(self) -> None:
        """HOLD (AC-S04-33): `./scripts/verify` with a mode, or none, syncs once before its first run."""
        for mode in MODES:
            with self.subTest(mode=mode or "none"):
                self.forget_log()
                self.assert_passed(self.run_in("./scripts/verify", *([mode] if mode else [])))
                self.assertEqual(synced_projects(self.log), ["apps/service"], sync_lines(self.log))
                if mode:
                    self.assertTrue(syncs_precede_runs(self.log), log_text(self.log))


class TwoServicesTest(ParallelGateTestCase):
    SHAPE = "two"

    def test_e3_two_services_sync_once_each(self) -> None:
        """AC-S04-30: `make verify` on two services leaves exactly two sync lines, one per `--project`."""
        self.assert_passed(self.make("verify"))
        self.assertEqual(sorted(synced_projects(self.log)), ["apps/second", "apps/service"], sync_lines(self.log))

    def test_e3_two_services_under_j_sync_once_each_and_before_any_run(self) -> None:
        """HOLD (AC-S04-29, G7): `make -j verify` on two services leaves one sync line per `--project`, all before the
        first run line. Teeth: drop `lint` and `typecheck` from the sync's dependents."""
        self.assert_passed(self.make("-j", "verify"))
        self.assertEqual(sorted(synced_projects(self.log)), ["apps/second", "apps/service"], sync_lines(self.log))
        self.assertTrue(syncs_precede_runs(self.log), log_text(self.log))


if __name__ == "__main__":
    unittest.main()
