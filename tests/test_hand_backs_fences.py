"""T024 and T023 of S14-result-contract (adversary A7, B4): fences are paired the CommonMark way.

A fence closes only on a run of the same character at least as long as the one that opened it, tildes included, and only
a top-level `result-contract` fence is a block; one quoted inside another fence is the delegate's example, not its
hand-back. The same reading holds for the verb's stdin and for a record on disk, where a heading hidden inside a foreign
fence, or a foreign fence never closed, is a finding naming the lines.
"""
from __future__ import annotations

import json
import tempfile
import unittest

from hand_backs_fixture import HEADING, RECORD, fence, findings, gate, run, scratch, valid

SLICE = "specs/f/slices/S1"
REAL = fence(valid())
EXAMPLE = "```result-contract\n" + json.dumps(valid() | {"scope": "the quoted example"}) + "\n```\n"


class StdinFencesTest(unittest.TestCase):
    def append(self, text: str) -> tuple[int, str, str]:
        with tempfile.TemporaryDirectory() as directory:
            repo = scratch(directory)
            result = run(repo, "--hand-back", SLICE, "drive-gaps", "gaps", stdin=text)
            record = repo / RECORD
            return result.returncode, result.stderr, record.read_text(encoding="utf-8") if record.exists() else ""

    def recorded(self, text: str, quoted: bool = True) -> None:
        code, err, record = self.append(text)
        self.assertEqual(0, code, err)
        self.assertEqual(1, record.count("```result-contract") + record.count("~~~result-contract"), record)
        self.assertEqual(not quoted, "the quoted example" in record, record)

    def refused(self, text: str, word: str = "no result-contract block") -> None:
        code, err, record = self.append(text)
        self.assertEqual(1, code, err)
        self.assertIn(word, err)
        self.assertEqual("", record)

    def test_a_four_backtick_wrapper_around_a_quoted_example_does_not_hide_the_real_block(self) -> None:
        self.recorded(f"prose\n\n````markdown\n{EXAMPLE}````\n\n{REAL}")

    def test_a_three_backtick_markdown_fence_quotes_the_example_it_holds(self) -> None:
        self.refused(f"```markdown\n{EXAMPLE}```\n")

    def test_a_four_backtick_run_closes_a_three_backtick_fence(self) -> None:
        self.recorded(f"```text\nsome output\n````\n\n{REAL}")

    def test_a_shorter_run_does_not_close_a_longer_fence(self) -> None:
        self.refused(f"````markdown\n{EXAMPLE}")  # the wrapper is never closed: all of it is the quoted text

    def test_tildes_quote_what_they_hold_and_are_not_closed_by_backticks(self) -> None:
        self.refused(f"~~~markdown\n{EXAMPLE}~~~\n")
        self.refused(f"~~~markdown\n{EXAMPLE}```\n\n{REAL}")
        self.recorded(f"~~~markdown\n{EXAMPLE}~~~\n\n{REAL}")

    def test_a_tilde_result_contract_fence_is_a_block(self) -> None:
        code, err, record = self.append("~~~result-contract\n" + json.dumps(valid()) + "\n~~~\n")
        self.assertEqual(0, code, err)
        self.assertIn("~~~result-contract", record)

    def test_a_closing_fence_carries_no_info_string_and_at_most_three_spaces_of_indent(self) -> None:
        self.refused("```text\n```result-contract\n{}\n```\n", "no result-contract block")
        self.recorded(f"```text\nx\n   ```\n\n{REAL}")
        self.refused(f"```text\nx\n    ```\n{REAL}")  # four spaces is code inside the fence, not its close

    def test_an_unclosed_result_contract_fence_is_still_refused_by_line(self) -> None:
        self.refused("```result-contract\n{\n", "not closed")

    def test_two_top_level_blocks_are_still_two_whatever_quoted_between_them(self) -> None:
        self.refused(f"{REAL}\n````markdown\n{EXAMPLE}````\n{REAL}", "two result-contract blocks")


class RecordFencesTest(unittest.TestCase):
    def test_a_quoted_example_in_a_wrapper_inside_an_entry_is_not_a_second_block(self) -> None:
        text = f"{HEADING}\n\n````markdown\n{EXAMPLE}````\n\n{REAL}"
        result = gate(text)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("1 hand-back(s) in 1 record(s)", result.stdout)

    def test_a_tilde_result_contract_fence_in_a_record_is_a_block(self) -> None:
        result = gate(f"{HEADING}\n\n~~~result-contract\n{json.dumps(valid())}\n~~~\n")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("1 hand-back(s) in 1 record(s)", result.stdout)

    def test_a_heading_inside_a_foreign_fence_is_a_finding_naming_both_lines(self) -> None:
        later = "## 2026-10-05T18:00:00Z — drive-gaps — gaps"
        text = f"{HEADING}\n\n```text\nleft open\n\n{later}\n\n{REAL}\n"
        found = findings(gate(text))
        hidden = [line for line in found if "hides" in line or "inside" in line]
        self.assertEqual(1, len(hidden), found)
        self.assertIn(f"{RECORD}:1:", hidden[0])
        self.assertIn("line 6", hidden[0])
        self.assertIn("line 3", hidden[0])

    def test_a_foreign_fence_never_closed_is_a_finding_naming_its_line(self) -> None:
        text = f"{HEADING}\n\n{REAL}\n```text\nleft open\n"
        found = findings(gate(text))
        self.assertEqual(1, len(found), found)
        self.assertIn("line 7", found[0])
        self.assertIn("not closed", found[0])

    def test_a_foreign_fence_closed_with_no_heading_inside_is_no_finding(self) -> None:
        text = f"{HEADING}\n\n```text\n## not a heading, a quote\n```\n\n{REAL}"
        self.assertEqual(0, gate(text).returncode)

    def test_the_repro_a_valid_entry_hidden_behind_an_unclosed_fence_is_no_longer_silent(self) -> None:
        text = f"{HEADING}\n\n{REAL}\n```text\n\n## 2026-10-05T18:00:00Z — drive-gaps — gaps\n\n{REAL}\n"
        result = gate(text)
        self.assertEqual(1, result.returncode, result.stdout)


if __name__ == "__main__":
    unittest.main()
