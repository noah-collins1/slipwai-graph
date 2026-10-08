"""The gate and the `Scope:` line (D60, AC-S02-57 to -63): absence is never a failure, a malformed value is.

The line is new, so the gate can refuse only what the line introduces: an empty value, or a value that is neither
`global` alone nor slice ids separated by commas. An entry without the line after one that has it is noted and
still passes. Examples that must be unchanged by the new rule (the holds) are checked against the checker as
released before this change, taken from git into a scratch file.
"""
from __future__ import annotations

import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_decisions_scope import entry, run, scratch

from slipwai.assets import ROOT

RELEASED = "596740f"  # the last commit before the Scope: line was read by the checker
FIXTURE = ROOT / "specs/001-faster-slipwai/decisions.md"
# Lines only a later release defines, which the released checker never read. From D195 on this repository's own log
# carries them, and D65's carve-out lets a log holding one get a different answer (S26's R5 e2), so the holds read the
# log without them: the question they ask is whether everything else in it still gets the released answer.
LATER_LINES = re.compile(r"^- \*\*(?:Reversibility|Proposed rule|Revert|Provisional \((?:shadow|advisory)\)):\*\*.*\n",
                         re.M)


def own_log() -> str:
    """This repository's own decisions log, less the lines only a later release defines (`LATER_LINES`)."""
    return LATER_LINES.sub("", FIXTURE.read_text(encoding="utf-8"))


def released_checker(directory: str) -> Path:
    path = Path(directory) / "released-check-decisions.py"
    text = subprocess.run(["git", "show", f"{RELEASED}:assets/toolkit/scripts/check-decisions.py"], cwd=ROOT,
                          text=True, capture_output=True, check=True, encoding="utf-8").stdout
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


class DecisionsScopeGateTest(unittest.TestCase):
    def gate(self, log: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory:
            return run(scratch(directory, log))

    def test_e57_hold_this_repositorys_own_log_gets_the_verdict_the_released_checker_gave(self) -> None:
        log = own_log()
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as other:
            repo = scratch(directory, "", script=released_checker(other))
            (repo / "specs/f/decisions.md").write_text(log, encoding="utf-8", newline="\n")
            before = run(repo)
        with tempfile.TemporaryDirectory() as directory:
            repo = scratch(directory, "")
            (repo / "specs/f/decisions.md").write_text(log, encoding="utf-8", newline="\n")
            after = run(repo)
        self.assertEqual((before.returncode, before.stdout, before.stderr),
                         (after.returncode, after.stdout, after.stderr))

    def test_e58_hold_global_and_bare_or_backticked_ids_after_the_stage_line_pass(self) -> None:
        log = "\n".join([entry(1, "global"), entry(2, "S02-runner-bookkeeping, S14-result-contract"),
                         entry(3, "`S02-runner-bookkeeping`, `S3`"), entry(4, "S02")])
        result = self.gate(log)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNotIn("note:", result.stdout)

    def test_e59_an_empty_scope_exits_one_with_a_line_naming_the_entry(self) -> None:
        result = self.gate(entry(1) + "\n" + entry(2, ""))
        self.assertEqual(1, result.returncode)
        lines = [line for line in result.stderr.splitlines() if "Scope" in line]
        self.assertEqual(1, len(lines), result.stderr)
        self.assertIn("D2", lines[0])
        self.assertIn("`global` alone or slice ids", lines[0])

    def test_e60_a_mixed_or_prose_scope_exits_one_with_the_same_kind_of_line(self) -> None:
        for value in ("global, S02-runner-bookkeeping", "the runner"):
            result = self.gate(entry(1, value))
            self.assertEqual(1, result.returncode, value)
            lines = [line for line in result.stderr.splitlines() if "Scope" in line]
            self.assertEqual(1, len(lines), result.stderr)
            self.assertIn("D1", lines[0])
            self.assertIn("`global` alone or slice ids", lines[0])

    def test_e61_hold_an_id_no_slice_has_passes(self) -> None:
        result = self.gate(entry(1, "S99-no-such-slice"))
        self.assertEqual(0, result.returncode, result.stderr)

    def test_e62_an_entry_without_the_line_after_one_with_it_passes_with_one_note_naming_it(self) -> None:
        result = self.gate(entry(1, "global") + "\n" + entry(2))
        self.assertEqual(0, result.returncode, result.stderr)
        notes = [line for line in result.stdout.splitlines() if "note:" in line]
        self.assertEqual(1, len(notes), result.stdout)
        self.assertIn("D2", notes[0])
        self.assertIn("carried as global", notes[0])
        self.assertEqual(0, len([line for line in self.gate(entry(1) + "\n" + entry(2)).stdout.splitlines()
                                 if "note:" in line]))

    def test_e63_hold_the_checker_as_released_passes_a_log_carrying_well_formed_scope_lines(self) -> None:
        log = "\n".join([entry(1, "global"), entry(2, "S02-runner-bookkeeping, S14-result-contract"), entry(3)])
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as other:
            result = run(scratch(directory, log, script=released_checker(other)))
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
