"""R7 and R8 (AC-S27-14, -15): `--scope` reads the new statuses, and the completion audit refuses an unratified one."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest

from provisional_fixture import EASY_LINE, entry, run, scratch
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


if __name__ == "__main__":
    unittest.main()
