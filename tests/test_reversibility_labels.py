"""T022 (B1, B4, B5; AC-S26-10, -15, D65): which lines the gate reads as the new labels, and when.

A `Proposed rule:` citation is held only in a log that carries a `Reversibility:` line; elsewhere the log gets one
`note:` and the released checker's answer. A label written nearly right — a space before the colon, another case,
underscores, a `*` bullet, the colon outside the bold — is never read, whatever else the log holds, and is a `note:`
naming the entry and the label as written. An entry says `Proposed rule:` once.
"""
from __future__ import annotations

import sys
import tempfile
import unittest

from reversibility_fixture import entry, gate, scratch
from test_reversibility_gate import line, proposed

sys.dont_write_bytecode = True
LISTED = ("scripts/check-decisions.py",)
BAD = "medium · rules 1 · contract=no"
NEAR = ("- **Reversibility :** ", "- **reversibility:** ", "- **REVERSIBILITY:** ", "- __Reversibility:__ ",
        "* **Reversibility:** ", "- **Reversibility**: ", "  - **Reversibility:** ", "- **Proposed Rule:** ",
        "- **Proposed rule**: ", "- __Proposed rule:__ ", "+ **Proposed  rule:** ")


def run(*entries: str) -> tuple[int, list[str], str]:
    """(exit code, the `note:` lines, stderr) of the gate over `entries`."""
    with tempfile.TemporaryDirectory() as directory:
        result = gate(scratch(directory, "\n".join(entries), listed=LISTED))
    notes = [row for row in result.stdout.splitlines() if row.startswith("check-decisions: note:")]
    return result.returncode, notes, result.stderr


class ProposedRuleAloneTest(unittest.TestCase):
    def test_e1_a_log_with_proposed_rule_lines_and_no_reversibility_line_passes_with_one_note(self) -> None:
        code, notes, err = run(entry(1), entry(2, proposed("D1")), entry(3, proposed("D9", "D8")))
        self.assertEqual((0, ""), (code, err), notes)
        said = [note for note in notes if "Proposed rule" in note]
        self.assertEqual(1, len(said), notes)
        self.assertIn("specs/f/decisions.md", said[0])
        self.assertIn("`Reversibility:`", said[0])

    def test_e2_the_same_citations_beside_a_reversibility_line_are_held(self) -> None:
        code, notes, err = run(entry(1, line()), entry(2, proposed("D1")))
        self.assertEqual(1, code, notes)
        self.assertIn(": D2 `Proposed rule` cites fewer than two", err)
        self.assertFalse([note for note in notes if "are not checked" in note], notes)


class NearMissLabelTest(unittest.TestCase):
    def test_e3_a_near_miss_is_a_note_naming_the_entry_and_the_label_and_is_never_read(self) -> None:
        for label in NEAR:
            for real in (False, True):
                with self.subTest(label=label, real=real):
                    first = entry(1, line()) if real else entry(1)
                    code, notes, err = run(first, entry(2, label + BAD))
                    self.assertEqual((0, ""), (code, err), notes)
                    said = [note for note in notes if label.strip() in note]
                    self.assertEqual(1, len(said), notes)
                    self.assertIn(": D2 ", said[0])

    def test_e4_the_exact_labels_and_fenced_quotes_are_no_near_miss(self) -> None:
        fenced = entry(2).replace("- **Written to:**", "```\n- **Reversibility :** x\n```\n- **Written to:**")
        code, notes, err = run(entry(1, line()), fenced, entry(3, line()), entry(4, proposed("D1", "D3")))
        self.assertEqual((0, ""), (code, err), notes)
        self.assertFalse([note for note in notes if "not read" in note], notes)


class SecondProposedRuleTest(unittest.TestCase):
    def test_e5_a_second_proposed_rule_line_in_an_entry_is_refused_naming_it(self) -> None:
        twice = entry(3, proposed("D1", "D2") + "\n" + proposed("D1", "D2"))
        code, notes, err = run(entry(1, line()), entry(2), twice)
        self.assertEqual(1, code, notes)
        findings = [row for row in err.splitlines() if row.startswith("  ")]
        self.assertEqual(1, len(findings), err)
        self.assertIn(": D3 ", findings[0])
        self.assertIn("more than one `Proposed rule:` line", findings[0])


if __name__ == "__main__":
    unittest.main()
