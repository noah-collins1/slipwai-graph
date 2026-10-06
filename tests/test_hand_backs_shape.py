"""R1 and R2 of S14-result-contract: a well-formed block passes, a malformed one names its field.

Each example runs `check-decisions.py` in a scratch project holding one `hand-backs.md`, as a project runs it.
"""
from __future__ import annotations

import tempfile
import unittest
from typing import Any

from hand_backs_fixture import HEADING, RECORD, entry, fence, run, scratch, valid


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


class WriteVerbContractTest(unittest.TestCase):
    """D162: the verb ships with contract 1 and vouches for no other; the gate's forward reading is for records."""

    def append(self, block: dict[str, Any]) -> tuple[Any, str]:
        with tempfile.TemporaryDirectory() as directory:
            repo = scratch(directory)
            result = run(repo, "--hand-back", "specs/f/slices/S1", "drive-gaps", "gaps", stdin=fence(block))
            record = repo / RECORD
            return result, record.read_text(encoding="utf-8") if record.exists() else ""

    def test_a_contract_other_than_one_is_refused_in_one_line_and_nothing_is_written(self) -> None:
        for block in ({"contract": 2}, valid() | {"contract": 2}, valid() | {"contract": 99},
                      valid() | {"contract": 0}):
            result, record = self.append(block)
            self.assertEqual(1, result.returncode, block)
            self.assertEqual([f"check-decisions: contract: {block['contract']} is not a contract this checker can "
                              "check (it checks 1); hand back a contract 1 block"], result.stderr.splitlines())
            self.assertEqual("", record)

    def test_a_contract_one_block_with_unknown_keys_is_still_appended(self) -> None:
        result, record = self.append(valid() | {"extra": "kept"})
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn('"extra": "kept"', record)

    def test_a_contract_that_is_not_an_integer_keeps_its_own_fault(self) -> None:
        for value in ("1", True, 1.5, None):
            result, record = self.append(valid() | {"contract": value})
            self.assertEqual(1, result.returncode, value)
            self.assertIn("is not the integer 1", result.stderr)
            self.assertEqual("", record)


class MalformedBlockTest(unittest.TestCase):
    def faults(self, block: dict[str, Any], heading: str = HEADING) -> list[str]:
        """The finding lines the gate printed for one block (exit 1 asserted), after the header."""
        with tempfile.TemporaryDirectory() as directory:
            result = run(scratch(directory, entry(block, heading)))
        self.assertEqual(1, result.returncode, result.stdout)
        return [line.strip() for line in result.stderr.splitlines() if line.startswith("  ")]

    def only(self, block: dict[str, Any], field: str, *words: str) -> str:
        found = self.faults(block)
        self.assertEqual(1, len(found), found)
        self.assertTrue(found[0].startswith(f"{RECORD}:1: {HEADING} — {field}: "), found[0])
        for word in words:
            self.assertIn(word, found[0])
        return found[0]

    def test_e1_a_block_without_files_changed_gets_one_line_naming_it(self) -> None:
        block = valid()
        del block["files_changed"]
        self.only(block, "files_changed", "absent")

    def test_e2_a_string_where_a_list_belongs_names_the_field(self) -> None:
        self.only(valid() | {"tests": "make test"}, "tests", "list")

    def test_e2_a_non_string_in_a_list_names_the_field(self) -> None:
        self.only(valid() | {"assumptions": ["fine", 3]}, "assumptions", "string")

    def test_e2_true_is_not_an_integer_for_contract_and_for_score(self) -> None:
        self.only(valid() | {"contract": True}, "contract", "integer")
        self.only(valid() | {"difficulty_observed": {"score": True, "reason": "x"}}, "difficulty_observed")

    def test_e2_a_contract_that_is_not_one_is_a_fault(self) -> None:
        for value in (0, "1", 1.0):
            self.only(valid() | {"contract": value}, "contract")

    def test_e2_an_empty_scope_or_change_summary_names_the_field(self) -> None:
        self.only(valid() | {"scope": ""}, "scope", "empty")
        self.only(valid() | {"change_summary": "  "}, "change_summary", "empty")

    def test_e3_a_status_outside_the_types_set_names_the_field_and_lists_the_set(self) -> None:
        heading = "## 2026-10-05T17:00:00Z — drive-hand — demo"
        block = valid() | {"delegate": "drive-hand", "status": "green"}
        found = self.faults(block, heading)
        self.assertEqual(1, len(found), found)
        self.assertIn(f"{heading} — status: ", found[0])
        self.assertIn("accepted, behaviour, implementation", found[0])

    def test_e3_a_delegate_that_is_not_one_of_the_ten_or_differs_from_the_heading_names_the_field(self) -> None:
        self.only(valid() | {"delegate": "drive-poet"}, "delegate", "drive-poet")
        self.only(valid() | {"delegate": "drive-hand", "status": "accepted"}, "delegate", "drive-gaps")

    def test_e4_an_absolute_path_or_one_with_a_dotdot_segment_names_files_changed(self) -> None:
        for path in ("/etc/passwd", "../x", "a/../b", "\\\\share\\x", "C:\\x", "C:/x"):
            self.only(valid() | {"files_changed": ["src/ok.py", path]}, "files_changed", repr(path))

    def test_e4_a_relative_path_and_an_empty_list_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = run(scratch(directory, entry(valid() | {"files_changed": ["src/a.py", "dir/..b/c"]})))
        self.assertEqual(0, result.returncode, result.stderr)

    def test_e5_a_decision_id_malformed_or_naming_no_entry_names_decisions(self) -> None:
        self.only(valid() | {"decisions": ["D9999"]}, "decisions", "D9999")
        self.only(valid() | {"decisions": ["d12"]}, "decisions", "d12")
        self.only(valid() | {"decisions": ["D134", "D12x"]}, "decisions", "D12x")

    def test_e5_a_feature_with_no_decisions_log_names_no_entry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = run(scratch(directory, entry(), decisions=0))
        self.assertEqual(1, result.returncode)
        self.assertIn("decisions: 'D134'", result.stderr)

    def test_e6_a_difficulty_that_is_not_exactly_score_and_reason_names_the_field(self) -> None:
        for bad in ({"score": 6, "reason": "x"}, {"score": 0, "reason": "x"}, {"score": 3}, "3 — hard",
                    {"score": 3, "reason": ""}, {"score": 3, "reason": "x", "extra": 1}, {"score": "3", "reason": "x"}):
            self.only(valid() | {"difficulty_observed": bad}, "difficulty_observed")

    def test_e7_two_faults_in_one_block_are_two_lines(self) -> None:
        found = self.faults(valid() | {"scope": "", "tests": "make test"})
        self.assertEqual(2, len(found), found)
        self.assertEqual({"scope", "tests"}, {line.split(" — ")[-1].split(":")[0] for line in found})

    def test_e7_the_line_number_is_the_entrys_heading_line(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = run(scratch(directory, "# Hand-backs — S1\n\n" + entry(valid() | {"scope": ""})))
        self.assertIn(f"  {RECORD}:3: {HEADING} — scope: ", result.stderr)


if __name__ == "__main__":
    unittest.main()
