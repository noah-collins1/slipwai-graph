"""R3 to R6 (AC-S27-7 to -10): the gate holds the `Status` forms, `Revert:`, the FR-033 facts and the rehearsal lines.

Each case writes a log into a scratch project that holds the three scripts and runs the gate as a `python3 -B`
subprocess.
"""
from __future__ import annotations

import sys
import unittest

from provisional_fixture import EASY_LINE, entry, gate

sys.dont_write_bytecode = True

PROVISIONAL = "provisional · ratify by 2026-10-14"


def provisional(number: int = 1, **keywords: str | None) -> str:
    """A provisional entry over the easy facts: its own `Revert:` line, unless `revert` says otherwise."""
    fields: dict[str, str | None] = {"status_line": PROVISIONAL, "revert": "own", "reversibility": EASY_LINE,
                                     **keywords}
    return entry(number, **fields)  # type: ignore[arg-type]


class GateCase(unittest.TestCase):
    def passes(self, *entries: str) -> None:
        result = gate("\n".join(entries))
        self.assertEqual((0, ""), (result.returncode, result.stderr), result.stdout)

    def refused(self, *entries: str, words: tuple[str, ...]) -> None:
        result = gate("\n".join(entries))
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        findings = [row for row in result.stderr.splitlines() if row.startswith("  ")]
        self.assertEqual(1, len(findings), result.stderr)
        for word in words:
            self.assertIn(word, findings[0])


class StatusFormsAndRevertTest(GateCase):
    def test_r3_e1_a_provisional_entry_with_its_own_revert_line_passes(self) -> None:
        self.passes(provisional())

    def test_r3_e2_ratified_and_reverted_pass_with_or_without_a_revert_line(self) -> None:
        for status in ("ratified 2026-10-09", "reverted 2026-10-09"):
            self.passes(entry(1, status, reversibility=EASY_LINE))
            self.passes(entry(1, status, revert="own", reversibility=EASY_LINE))

    def test_r3_e3_a_malformed_date_or_form_is_refused_naming_the_entry_and_the_form(self) -> None:
        for status in ("provisional · ratify by 2026-13-01", "ratified tomorrow", "provisional",
                       "reverted 2026-02-30"):
            self.refused(provisional(status_line=status), words=("D1", "`Status`", "ratify by"))

    def test_r3_e4_a_provisional_entry_without_revert_is_refused_naming_it(self) -> None:
        self.refused(provisional(revert=None), words=("D1", "`Revert`"))

    def test_r3_e5_two_revert_lines_are_refused(self) -> None:
        twice = provisional() + "- **Revert:** commits carrying Decision: D1\n"
        self.refused(twice, words=("D1", "`Revert`", "more than one"))

    def test_r3_e6_a_revert_naming_another_entry_is_refused_naming_it(self) -> None:
        self.refused(provisional(1), provisional(2, revert="commits carrying Decision: D1"),
                     words=("D2", "`Revert`", "D1"))

    def test_r3_e7_a_revert_on_a_standing_entry_is_refused(self) -> None:
        self.refused(entry(1, "standing", revert="own"), words=("D1", "`Revert`", "standing"))

    def test_r3_e8_a_revert_that_is_not_commits_carrying_the_decision_is_refused(self) -> None:
        self.refused(provisional(revert="the last three commits"), words=("D1", "`Revert`"))


if __name__ == "__main__":
    unittest.main()
