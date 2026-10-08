"""S27 Phase 4, the gate and the audit read one log (D210, AC-S27-25) and the gate trusts only a mode that was in force
(D209, AC-S27-24): the adversary's A1, A2, A7, A8 and B3, B4 reproductions, each copied here from its case file.

Each case writes a log into a scratch project holding the three toolkit scripts and runs the gate and the audit as
`python3 -B` subprocesses, the way a generated project holds them.
"""
from __future__ import annotations

import sys
import unittest

from provisional_fixture import EASY_LINE, HARD_LINE, audit, entry, gate

sys.dont_write_bytecode = True

PROVISIONAL = "provisional · ratify by 2026-10-14"
RATIFIED = "ratified 2026-10-08"


def provisional(number: int = 1, **keywords: str | None) -> str:
    fields: dict[str, str | None] = {"status_line": PROVISIONAL, "revert": "own", "reversibility": EASY_LINE,
                                     **keywords}
    return entry(number, **fields)  # type: ignore[arg-type]


def fenced(text: str, line: str) -> str:
    """`text` with `line` (a whole line, without its newline) wrapped in a code fence."""
    return text.replace(line + "\n", f"```\n{line}\n```\n")


class OneReading(unittest.TestCase):
    def refused(self, log: str, *words: str) -> list[str]:
        result = gate(log)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        found = [row for row in result.stderr.splitlines() if row.startswith("  ")]
        for word in words:
            self.assertIn(word, "\n".join(found))
        return found


class FencesAndNearMissLabelsTest(OneReading):
    """T038 (A1, A2, A7): a fenced line or a near-miss label is no `Status:` line, to the gate or to the audit."""

    def test_t038_a1_a_ratified_status_inside_a_fence_with_hard_facts_does_not_pass_the_gate(self) -> None:
        log = fenced(entry(1, RATIFIED, reversibility=HARD_LINE), f"- **Status:** {RATIFIED}")
        self.refused(log, "D1", "`Status`")

    def test_t038_a2_a_near_miss_status_label_beside_a_fenced_example_does_not_pass_the_gate(self) -> None:
        example = f"A ratified entry's last line reads:\n\n```\n- **Status:** {RATIFIED}\n```\n\n"
        log = example + entry(1, RATIFIED, reversibility=HARD_LINE).replace("**Status:**", "**Status :**")
        self.refused(log, "D1", "Status")

    def test_t038_a2b_a_near_miss_status_on_an_entry_of_a_held_log_is_refused_naming_the_label(self) -> None:
        log = provisional(1) + entry(2, RATIFIED, reversibility=HARD_LINE).replace("**Status:**", "**Status :**")
        found = self.refused(log, "D2", "`- **Status :**`", "- **Status:**")
        self.assertEqual(2, len(found), found)  # the label, and the entry that is left without a `Status`

    def test_t038_a2c_other_cases_and_bullets_of_the_label_are_near_misses_too(self) -> None:
        for label in ("- **status:**", "* **Status:**", "- **Status :**", "- Status:"):
            line = entry(2, RATIFIED, reversibility=HARD_LINE).replace("- **Status:**", label)
            self.refused(provisional(1) + line, "D2", f"`{label}`")

    def test_t038_a7_a_fenced_standing_status_before_the_real_provisional_one_is_provisional_to_both(self) -> None:
        log = provisional(1).replace("- **Status:** " + PROVISIONAL + "\n",
                                     f"```\n- **Status:** standing\n```\n- **Status:** {PROVISIONAL}\n")
        result = gate(log)
        self.assertEqual((0, ""), (result.returncode, result.stderr), result.stdout)
        parked = audit(log)
        self.assertEqual(3, parked.returncode, parked.stdout + parked.stderr)
        self.assertIn("ratify D1", parked.stdout)

    def test_t038_a7b_a_fenced_provisional_status_is_no_unratified_entry_to_the_audit(self) -> None:
        log = entry(1, "standing").replace(
            "- **Status:** standing\n", f"- **Status:** standing\n```\n- **Status:** {PROVISIONAL}\n```\n")
        parked = audit(log)
        self.assertEqual((0, ""), (parked.returncode, parked.stderr), parked.stdout)

    def test_t038_a7c_a_near_miss_status_is_no_unratified_entry_to_the_audit(self) -> None:
        log = provisional(1).replace("**Status:**", "**Status :**")
        parked = audit(log)
        self.assertEqual(0, parked.returncode, parked.stdout + parked.stderr)


class AsciiDigitsTest(OneReading):
    """T038 (A8): a heading's number is ASCII, in a held log, for the gate and for the audit."""

    def test_t038_a8_a_fullwidth_digit_in_a_heading_of_a_held_log_is_refused(self) -> None:
        log = provisional(1).replace("## D1 —", "## D１ —")
        found = self.refused(log, "heading", "0-9")
        self.assertEqual(1, len(found), found)

    def test_t038_a8b_the_audit_skips_what_the_gate_refuses(self) -> None:
        log = provisional(1).replace("## D1 —", "## D１ —")
        self.assertEqual(0, audit(log).returncode)

    def test_t038_a8c_a_log_with_none_of_the_new_forms_still_reads_a_fullwidth_heading_as_before(self) -> None:
        log = entry(1, "standing").replace("## D1 —", "## D１ —")
        result = gate(log)
        self.assertEqual((0, ""), (result.returncode, result.stderr), result.stdout)


class TheGateAndTheAuditAgreeTest(OneReading):
    def test_t038_agree_on_every_reproduction_a_log_the_gate_passes_parks_the_audit_exactly_when_it_is_provisional(
            self) -> None:
        cases = {
            "plain": (provisional(1), 3), "ratified": (entry(1, RATIFIED, reversibility=EASY_LINE), 0),
            "fenced": (fenced(provisional(1), f"- **Status:** {PROVISIONAL}"), 0),
            "second": (provisional(1) + entry(2, "standing"), 3),
        }
        for name, (log, parked) in cases.items():
            with self.subTest(name):
                self.assertEqual(parked, audit(log).returncode)
                if name != "fenced":
                    self.assertEqual(0, gate(log).returncode, gate(log).stderr)


if __name__ == "__main__":
    unittest.main()
