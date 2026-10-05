"""R5 of S14-result-contract: the dispatching session appends, validated, to the slice's record.

`check-decisions.py --hand-back <dir> <type> <stage>` takes the hand-back on stdin; `--hand-back-missing` takes a
reason. Each runs in a scratch project as a subprocess, and the gate is then run over what it wrote.
"""
from __future__ import annotations

import json
import re
import subprocess
import tempfile
import unittest

from hand_backs_fixture import RECORD, fence, run, scratch, valid

SLICE = "specs/f/slices/S1"
PRETTY = "```result-contract\n" + json.dumps(valid(), indent=1) + "\n```\n"
HEAD = re.compile(r"^## \d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ — drive-gaps — gaps\n\n", re.M)


class Scratch(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.repo = scratch(self.directory.name)
        self.record = self.repo / RECORD

    def append(self, stdin: str, folder: str = SLICE, htype: str = "drive-gaps",
               stage: str = "gaps") -> subprocess.CompletedProcess[str]:
        return run(self.repo, "--hand-back", folder, htype, stage, stdin=stdin)


class AppendTest(Scratch):
    def test_e1_prose_and_a_valid_block_append_the_heading_and_the_fence_byte_for_byte(self) -> None:
        result = self.append(f"I read the diff; two gaps.\n\n{PRETTY}\nThat is all.\n")
        self.assertEqual(0, result.returncode, result.stderr)
        text = self.record.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# Hand-backs — S1\n\n"), text)
        self.assertRegex(text, HEAD)
        self.assertTrue(text.endswith("\n\n" + PRETTY + "\n"), text)
        self.assertNotIn("I read the diff", text)
        gate = run(self.repo)
        self.assertEqual(0, gate.returncode, gate.stderr)
        self.assertIn("1 hand-back(s) in 1 record(s)", gate.stdout)

    def test_e1_a_feature_level_record_is_created_under_the_feature_with_its_name_as_title(self) -> None:
        result = self.append(PRETTY, "specs/f")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue((self.repo / "specs/f/hand-backs.md").read_text(encoding="utf-8").startswith(
            "# Hand-backs — f\n\n"))
        self.assertFalse(self.record.exists())

    def test_e2_a_malformed_block_prints_the_field_line_exits_one_and_writes_nothing(self) -> None:
        bad = fence(valid() | {"status": "green"})
        result = self.append(bad)
        self.assertEqual(1, result.returncode)
        self.assertIn("status: 'green' is not one of gaps, none", result.stderr)
        self.assertFalse(self.record.exists())

    def test_e2_a_malformed_block_leaves_an_existing_record_unchanged(self) -> None:
        self.assertEqual(0, self.append(PRETTY).returncode)
        before = self.record.read_bytes()
        self.assertEqual(1, self.append(fence(valid() | {"decisions": ["D9999"]})).returncode)
        self.assertEqual(before, self.record.read_bytes())

    def test_e2_a_delegate_that_is_not_the_type_dispatched_is_refused(self) -> None:
        result = self.append(PRETTY, htype="drive-hand", stage="demo")
        self.assertEqual(1, result.returncode)
        self.assertIn("delegate", result.stderr)
        self.assertFalse(self.record.exists())

    def test_e3_a_hand_back_without_a_block_says_so_and_writes_nothing(self) -> None:
        for text in ("", "all done, no block\n", "```json\n{}\n```\n"):
            result = self.append(text)
            self.assertEqual(1, result.returncode)
            self.assertIn("no result-contract block", result.stderr)
        self.assertFalse(self.record.exists())

    def test_e3_an_unclosed_fence_is_refused(self) -> None:
        result = self.append("```result-contract\n{}\n")
        self.assertEqual(1, result.returncode)
        self.assertIn("not closed", result.stderr)
        self.assertFalse(self.record.exists())

    def test_e4_two_blocks_are_refused(self) -> None:
        result = self.append(PRETTY + "\n" + PRETTY)
        self.assertEqual(1, result.returncode)
        self.assertIn("two result-contract blocks", result.stderr)
        self.assertFalse(self.record.exists())

    def test_e5_a_missing_entry_is_appended_with_its_reason_and_the_gate_passes_it(self) -> None:
        result = run(self.repo, "--hand-back-missing", SLICE, "drive-gaps", "gaps", "malformed:", "status")
        self.assertEqual(0, result.returncode, result.stderr)
        text = self.record.read_text(encoding="utf-8")
        self.assertIsNotNone(re.search(HEAD.pattern + r"- \*\*Missing:\*\* malformed: status\n", text, re.M))
        gate = run(self.repo)
        self.assertEqual(0, gate.returncode, gate.stderr)
        self.assertIn("0 hand-back(s) in 1 record(s)", gate.stdout)

    def test_e6_a_folder_that_is_not_a_feature_or_a_slice_is_usage_exit_two(self) -> None:
        (self.repo / "apps/x").mkdir(parents=True)
        for folder in ("apps/x", "/tmp", "specs", "specs/f/slices", "specs/../apps", "specs/nope",
                       "specs/f/slices/S1/x"):
            for args in (("--hand-back", folder, "drive-gaps", "gaps"),
                         ("--hand-back-missing", folder, "drive-gaps", "gaps", "why")):
                result = run(self.repo, *args, stdin=PRETTY)
                self.assertEqual(2, result.returncode, (args, result.stderr))
                self.assertIn("usage", result.stderr)
        self.assertFalse(list(self.repo.rglob("hand-backs.md")))

    def test_e6_a_type_a_stage_or_a_reason_that_is_not_one_is_usage_exit_two(self) -> None:
        for args in (("--hand-back", SLICE, "drive-poet", "gaps"), ("--hand-back", SLICE, "drive-gaps", "Gaps"),
                     ("--hand-back", SLICE, "drive-gaps"), ("--hand-back", SLICE, "drive-gaps", "gaps", "extra"),
                     ("--hand-back-missing", SLICE, "drive-gaps", "gaps"), ("--hand-back-missing", SLICE)):
            self.assertEqual(2, run(self.repo, *args, stdin=PRETTY).returncode, args)
        self.assertFalse(self.record.exists())

    def test_e7_a_second_append_keeps_the_first_entrys_bytes(self) -> None:
        self.assertEqual(0, self.append(PRETTY).returncode)
        first = self.record.read_bytes()
        self.assertEqual(0, run(self.repo, "--hand-back-missing", SLICE, "drive-tasks", "tasks", "no continuation"
                                ).returncode)
        self.assertEqual(0, self.append(PRETTY, stage="converge").returncode)
        after = self.record.read_bytes()
        self.assertTrue(after.startswith(first))
        self.assertEqual(3, after.decode("utf-8").count("\n## "))
        gate = run(self.repo)
        self.assertEqual(0, gate.returncode, gate.stderr)
        self.assertIn("2 hand-back(s) in 1 record(s)", gate.stdout)

    def test_e7_an_entry_is_appended_after_a_file_that_ends_without_a_newline(self) -> None:
        self.record.write_text("# Hand-backs — S1", encoding="utf-8")
        self.assertEqual(0, self.append(PRETTY).returncode)
        self.assertEqual(0, run(self.repo).returncode)


class RetryTest(Scratch):
    """Constitution II: a retry cannot duplicate the side effect of either write verb."""

    def missing(self, reason: str, stage: str = "gaps") -> subprocess.CompletedProcess[str]:
        return run(self.repo, "--hand-back-missing", SLICE, "drive-gaps", stage, reason)

    def test_e8_the_same_block_again_is_a_noop_with_a_note_and_exit_zero(self) -> None:
        self.assertEqual(0, self.append(PRETTY).returncode)
        before = self.record.read_bytes()
        result = self.append(f"retried\n\n{PRETTY}")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("already", result.stderr)
        self.assertEqual(before, self.record.read_bytes())

    def test_e8_a_different_block_is_still_appended_and_then_the_first_again_is_too(self) -> None:
        self.assertEqual(0, self.append(PRETTY).returncode)
        other = fence(valid() | {"scope": "a correction"})
        self.assertEqual(0, self.append(other).returncode)
        self.assertEqual(0, self.append(PRETTY).returncode)  # not the last entry for the type and stage any more
        self.assertEqual(3, self.record.read_text(encoding="utf-8").count("\n## "))

    def test_e8_the_same_block_under_another_stage_or_type_is_appended(self) -> None:
        self.assertEqual(0, self.append(PRETTY).returncode)
        self.assertEqual(0, self.append(PRETTY, stage="converge").returncode)
        self.assertEqual(2, self.record.read_text(encoding="utf-8").count("\n## "))

    def test_e9_the_same_missing_reason_again_is_a_noop_with_a_note(self) -> None:
        self.assertEqual(0, self.missing("refused: out of budget").returncode)
        before = self.record.read_bytes()
        result = self.missing("refused: out of budget")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("already", result.stderr)
        self.assertEqual(before, self.record.read_bytes())

    def test_e9_a_different_reason_or_a_block_after_it_is_appended(self) -> None:
        self.assertEqual(0, self.missing("refused").returncode)
        self.assertEqual(0, self.missing("refused again").returncode)
        self.assertEqual(0, self.append(PRETTY).returncode)
        self.assertEqual(0, self.missing("refused again").returncode)
        self.assertEqual(4, self.record.read_text(encoding="utf-8").count("\n## "))


if __name__ == "__main__":
    unittest.main()
