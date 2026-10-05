"""R1 and R2 of S14-result-contract: a well-formed block passes, a malformed one names its field.

Each example runs `check-decisions.py` in a scratch project holding one `hand-backs.md`, as a project runs it.
"""
from __future__ import annotations

import tempfile
import unittest
from typing import Any

from hand_backs_fixture import HEADING, RECORD, entry, run, scratch, valid


class WellFormedBlockTest(unittest.TestCase):
    def gate(self, block: dict[str, Any]) -> Any:
        with tempfile.TemporaryDirectory() as directory:
            return run(scratch(directory, "# Hand-backs — S1\n\n" + entry(block)))

    def test_e1_the_pages_example_block_passes_and_the_summary_counts_it(self) -> None:
        result = self.gate(valid())
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("1 hand-back(s) in 1 record(s)", result.stdout)
        self.assertNotIn("note:", result.stdout)

    def test_e2_every_list_field_empty_passes(self) -> None:
        block = valid() | {key: [] for key in ("contracts_changed", "invariants_checked", "tests", "decisions",
                                               "assumptions", "unresolved", "files_changed")}
        result = self.gate(block)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("1 hand-back(s) in 1 record(s)", result.stdout)

    def test_e3_a_key_outside_the_thirteen_passes_with_no_note(self) -> None:
        result = self.gate(valid() | {"elapsed": 4})
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("1 hand-back(s) in 1 record(s)", result.stdout)
        self.assertNotIn("note:", result.stdout)

    def test_e4_a_later_contract_passes_with_one_note_naming_the_heading_and_holds_no_field(self) -> None:
        result = self.gate({"contract": 2})
        self.assertEqual(0, result.returncode, result.stderr)
        notes = [line for line in result.stdout.splitlines() if "check-decisions: note:" in line]
        self.assertEqual(1, len(notes), result.stdout)
        self.assertIn(HEADING, notes[0])
        self.assertIn(RECORD, notes[0])
        self.assertEqual("", result.stderr)


if __name__ == "__main__":
    unittest.main()
