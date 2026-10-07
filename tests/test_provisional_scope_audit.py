"""R7 and R8 (AC-S27-14, -15): `--scope` reads the new statuses, and the completion audit refuses an unratified one."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest

from provisional_fixture import EASY_LINE, audit, entry, run, scratch
from test_decisions_gate_differential import checker_at

sys.dont_write_bytecode = True

PROVISIONAL = "provisional · ratify by 2026-10-14"


def scope(log: str, wanted: str = "S1", script: str = "check-decisions") -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as directory:
        repo = scratch(directory, log)
        if script != "check-decisions":
            (repo / "scripts/check-decisions.py").write_text(script, encoding="utf-8", newline="\n")
        return run(repo, "check-decisions", "--scope", wanted)


class ScopeReadsTheNewStatusesTest(unittest.TestCase):
    def test_r7_e1_provisional_and_ratified_are_printed_as_binding_and_reverted_is_left_out(self) -> None:
        log = "\n".join([entry(1, PROVISIONAL, revert="own", reversibility=EASY_LINE), entry(2, "ratified 2026-10-09"),
                         entry(3, "reverted 2026-10-09")])
        result = scope(log)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn(f"- **Status:** {PROVISIONAL}\n- **Revert:** commits carrying Decision: D1", result.stdout)
        self.assertIn("## D2 — Question 2", result.stdout)
        self.assertIn("- **Status:** ratified 2026-10-09", result.stdout)
        self.assertNotIn("## D3", result.stdout)
        summary = result.stdout.strip().splitlines()[-1]
        self.assertTrue(summary.startswith("check-decisions: carried 2 of 3 entries for S1: 2 in scope"), summary)
        self.assertTrue(summary.endswith("overridden and left out: D3 (reverted 2026-10-09); "
                                         "provisional and binding: D1"), summary)

    def test_r7_e2_a_log_of_standing_entries_is_printed_byte_for_byte_as_before(self) -> None:
        """A guard over the unchanged path: it passes when written."""
        log = "\n".join([entry(1), entry(2, "overridden by D3"), entry(3, scope="S2"), entry(4, scope="global")])
        with tempfile.TemporaryDirectory() as other:
            earlier = checker_at("5f4fc00", other).read_text(encoding="utf-8")
        before, after = scope(log, script=earlier), scope(log)
        self.assertEqual((before.returncode, before.stdout, before.stderr),
                         (after.returncode, after.stdout, after.stderr))
        self.assertNotIn("provisional and binding", after.stdout)


class CompletionAuditTest(unittest.TestCase):
    """R8 (AC-S27-14): the run does not say `done` while a provisional decision waits for a person."""

    def test_r8_e1_the_lowest_numbered_unratified_entry_is_named_and_the_audit_parks(self) -> None:
        log = "\n".join([entry(1), entry(2, PROVISIONAL, revert="own", reversibility=EASY_LINE), entry(3),
                         entry(4, PROVISIONAL, revert="own", reversibility=EASY_LINE)])
        result = audit(log)
        self.assertEqual((3, "cruise: parked: ratify D2\n"), (result.returncode, result.stdout), result.stderr)

    def test_r8_e2_ratified_reverted_and_overridden_by_a_person_no_longer_hold_the_run(self) -> None:
        log = "\n".join([entry(1), entry(2, "ratified 2026-10-09"), entry(3), entry(4, "reverted 2026-10-09"),
                         entry(5, "overridden by human 2026-10-09")])
        result = audit(log)
        self.assertEqual((0, "provisional: no unratified provisional decision in specs/f/decisions.md\n"),
                         (result.returncode, result.stdout), result.stderr)

    def test_r8_e3_no_log_is_nothing_unratified(self) -> None:
        result = audit(None)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("no decisions.md", result.stdout)

    def test_r8_e4_two_features_and_no_choice_is_exit_two_naming_both(self) -> None:
        logs = {"alpha": entry(1, PROVISIONAL, revert="own", reversibility=EASY_LINE), "beta": entry(1)}
        result = audit(logs)
        self.assertEqual((2, ""), (result.returncode, result.stdout))
        self.assertEqual(1, len(result.stderr.strip().splitlines()), result.stderr)
        self.assertTrue("alpha" in result.stderr and "beta" in result.stderr, result.stderr)
        chosen = audit(logs, "--feature", "beta")
        self.assertEqual((0, True), (chosen.returncode, "specs/beta/decisions.md" in chosen.stdout), chosen.stderr)
        parked = audit(logs, "--feature", "alpha")
        self.assertEqual((3, "cruise: parked: ratify D1\n"), (parked.returncode, parked.stdout))


if __name__ == "__main__":
    unittest.main()
