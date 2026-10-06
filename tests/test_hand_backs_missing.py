"""T029 of S14-result-contract (adversary A1): what a verb writes outside the delegate's verbatim block is one line.

`--hand-back-missing` writes a reason, and every verb writes a type and a stage; a value holding a line break, a
control character or the start of a fence or an entry would forge or hide an entry in an append-only record, so each is
refused with usage (exit 2) before anything is written.
"""
from __future__ import annotations

import tempfile
import unittest

from hand_backs_fixture import HEADING, RECORD, entry, fence, gate, run, scratch, valid

SLICE = "specs/f/slices/S1"
FORGED = "refused\n## 2026-10-05T17:00:00Z — drive-gaps — gaps\n\n" + fence(valid())


class OneLineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.repo = scratch(self.directory.name)
        self.record = self.repo / RECORD

    def missing(self, *reason: str) -> int:
        result = run(self.repo, "--hand-back-missing", SLICE, "drive-gaps", "gaps", *reason)
        self.assertNotIn("Traceback", result.stderr)
        return result.returncode

    def test_a_reason_with_a_line_break_or_a_control_character_is_refused_and_nothing_is_written(self) -> None:
        for reason in ("a\nb", "a\rb", "a\r\nb", "a b", "a b", "a\x85b", "a\x0bb", "a\x0cb",
                       "a\x1bb", "a\tb", "line\n", "\nline"):
            self.assertEqual(2, self.missing(reason), repr(reason))
            self.assertFalse(self.record.exists(), repr(reason))

    def test_a_multi_line_reason_that_opens_a_fence_or_an_entry_never_reaches_the_record(self) -> None:
        for reason in (FORGED, "refused\n```text\n", "refused\n~~~\n", "refused\n" + HEADING):
            self.assertEqual(2, self.missing(reason), repr(reason))
        self.assertFalse(self.record.exists())

    def test_the_forged_block_repro_neither_passes_the_gate_nor_covers_a_stage(self) -> None:
        self.assertEqual(2, self.missing(FORGED))
        gate = run(self.repo)
        self.assertEqual(0, gate.returncode, gate.stderr)
        self.assertNotIn("hand-back(s) in", gate.stdout)  # no record was made

    def test_a_break_in_any_word_of_a_reason_given_as_several_arguments_is_refused(self) -> None:
        self.assertEqual(2, self.missing("refused:", "no\nbudget"))
        self.assertFalse(self.record.exists())

    def test_the_refusal_names_the_reason_and_says_one_line(self) -> None:
        result = run(self.repo, "--hand-back-missing", SLICE, "drive-gaps", "gaps", "a\nb")
        self.assertIn("reason", result.stderr.splitlines()[0])
        self.assertIn("one line", result.stderr.splitlines()[0])

    def test_a_one_line_reason_with_text_a_person_writes_is_still_appended(self) -> None:
        for reason in ("refused: café — out of budget", "refused: ``` is not a fence here", "## not a heading"):
            self.assertEqual(0, self.missing(reason), reason)
        self.assertEqual(0, run(self.repo).returncode)

    def test_a_type_or_a_stage_with_a_line_break_is_refused_by_both_write_verbs(self) -> None:
        for args in (("--hand-back-missing", SLICE, "drive-gaps\n", "gaps", "why"),
                     ("--hand-back-missing", SLICE, "drive-gaps", "gaps\n## x", "why"),
                     ("--hand-back", SLICE, "drive-gaps", "gaps\n"), ("--hand-back", SLICE, "drive-gaps\n", "gaps")):
            self.assertEqual(2, run(self.repo, *args, stdin=entry()).returncode, args)
        self.assertFalse(self.record.exists())


class SummaryCountsMissingTest(unittest.TestCase):
    """T028 item 2: the gate's summary counts `Missing:` entries beside the blocks."""

    def test_the_summary_says_how_many_hand_backs_and_how_many_are_missing(self) -> None:
        missing = "## 2026-10-05T18:00:00Z — drive-tasks — tasks\n\n- **Missing:** no continuation\n\n"
        two = entry() + missing + missing.replace("tasks", "gaps")
        for record, words in ((two, "1 hand-back(s) in 1 record(s), 2 missing"),
                              (entry(), "1 hand-back(s) in 1 record(s), 0 missing"),
                              (missing, "0 hand-back(s) in 1 record(s), 1 missing")):
            result = gate(record)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn(words + ",", result.stdout)

    def test_a_malformed_entry_is_a_finding_and_not_counted_as_missing(self) -> None:
        result = gate("## 2026-10-05T18:00:00Z — drive-tasks — tasks\n\nprose only\n")
        self.assertEqual(1, result.returncode)


if __name__ == "__main__":
    unittest.main()
