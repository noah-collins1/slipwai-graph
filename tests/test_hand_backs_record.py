"""R3 and R4 of S14-result-contract: a record's structure, and nothing recorded means nothing changes."""
from __future__ import annotations

import json
import unittest

from hand_backs_fixture import HEADING, RECORD, entry, fence, findings, gate, valid


class RecordStructureTest(unittest.TestCase):
    def one(self, record: str, *words: str) -> str:
        result = gate(record)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        found = findings(result)
        self.assertEqual(1, len(found), found)
        for word in words:
            self.assertIn(word, found[0])
        return found[0]

    def test_e1_an_unterminated_fence_is_one_finding_naming_the_entry(self) -> None:
        text = f"{HEADING}\n\n```result-contract\n{json.dumps(valid())}\n"
        self.one(text, f"{RECORD}:1: {HEADING}", "not closed")

    def test_e1_a_fence_not_closed_before_the_next_heading_is_unterminated(self) -> None:
        text = f"{HEADING}\n```result-contract\n{json.dumps(valid())}\n" + entry()
        found = findings(gate(text))
        self.assertEqual(1, len(found), found)
        self.assertIn("not closed", found[0])

    def test_e2_two_blocks_under_one_heading_are_one_finding(self) -> None:
        text = f"{HEADING}\n\n{fence(valid())}\n{fence(valid())}"
        self.one(text, f"{RECORD}:1: {HEADING}", "2 result-contract blocks")

    def test_e3_a_heading_not_in_the_shape_is_one_finding_naming_it(self) -> None:
        bad = "## yesterday — drive-gaps — gaps"
        self.one(entry(heading=bad), f"{RECORD}:1: {bad}", "<UTC time>")

    def test_e3_a_heading_with_no_stage_or_a_foreign_type_is_one_finding(self) -> None:
        self.one(entry(heading="## 2026-10-05T17:00:00Z — drive-gaps"), "<UTC time>")
        self.one(entry(heading="## 2026-10-05T17:00:00Z — gaps — gaps"), "<UTC time>")

    def test_e4_a_heading_followed_only_by_prose_is_one_finding(self) -> None:
        self.one(f"{HEADING}\n\nI did it, honest.\n", f"{RECORD}:1: {HEADING}", "neither")

    def test_e4_a_block_and_a_missing_line_together_are_one_finding(self) -> None:
        self.one(f"{HEADING}\n\n{fence(valid())}\n- **Missing:** refused: no\n", "both")

    def test_e4_a_missing_line_with_no_reason_is_not_a_missing_line(self) -> None:
        self.one(f"{HEADING}\n\n- **Missing:**\n", "neither")

    def test_e5_a_body_that_does_not_parse_or_is_not_an_object_is_one_finding(self) -> None:
        self.one(entry('{"contract": 1,'), f"{RECORD}:1: {HEADING}", "block", "JSON")
        self.one(entry("[1, 2]"), f"{RECORD}:1: {HEADING}", "block", "object")

    def test_e5_each_bad_entry_of_several_is_its_own_finding(self) -> None:
        text = entry() + entry("[1]", "## 2026-10-05T17:01:00Z — drive-gaps — gaps") + entry(
            "{", "## 2026-10-05T17:02:00Z — drive-gaps — gaps")
        found = findings(gate(text))
        self.assertEqual(2, len(found), found)

    def test_e6_a_missing_entry_with_any_reason_passes_stopped_included(self) -> None:
        for reason in ("stopped: the run was stopped mid-pass", "refused: out of budget", "no continuation"):
            result = gate(f"{HEADING}\n\n- **Missing:** {reason}\n")
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("0 hand-back(s) in 1 record(s)", result.stdout)

    def test_e7_text_before_the_first_heading_is_the_files_own(self) -> None:
        result = gate("# Hand-backs — S1\n\nThis file is append-only.\n\n" + entry())
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("1 hand-back(s) in 1 record(s)", result.stdout)

    def test_e7_a_fence_with_another_info_string_is_skipped_whole(self) -> None:
        text = f"{HEADING}\n\n```text\n## not a heading\n{{\n```\n\n{fence(valid())}"
        result = gate(text)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("1 hand-back(s) in 1 record(s)", result.stdout)


if __name__ == "__main__":
    unittest.main()
