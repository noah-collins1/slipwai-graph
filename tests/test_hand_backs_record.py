"""R3 and R4 of S14-result-contract: a record's structure, and nothing recorded means nothing changes."""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from collections.abc import Callable
from pathlib import Path

from hand_backs_fixture import HEADING, RECORD, decision, entry, fence, findings, gate, run, scratch, valid
from test_decisions_scope import entry as scope_entry

from slipwai.assets import ROOT

RELEASED = "c3c760b"  # the checker as it stood before hand-backs.md was read


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

    def test_e8_each_content_before_the_first_heading_never_crashes_the_gate(self) -> None:
        after = f"{HEADING}\n- **Missing:** no continuation\n"
        cases = {
            "no fence": ("# T\n\nprose\n\n", 0),
            "a closed fence": (f"# T\n\n{fence(valid())}\n", 0),
            "an unclosed fence": ("# T\n```result-contract\n{\n", 1),
            "another info string, unclosed": ("# T\n```text\n{\n", 1),
        }
        for name, (preamble, code) in cases.items():
            with self.subTest(name):
                result = gate(preamble + after)
                self.assertNotIn("Traceback", result.stderr)
                self.assertEqual(code, result.returncode, result.stdout + result.stderr)
        found = findings(gate(cases["an unclosed fence"][0] + after))
        self.assertEqual(1, len(found), found)
        self.assertTrue(found[0].startswith(f"{RECORD}:2: "), found[0])
        self.assertIn("not closed", found[0])

    def test_e8_an_unclosed_fence_before_the_first_heading_at_the_end_of_the_file_is_a_finding(self) -> None:
        result = gate("# T\n\n```result-contract\n{\n")
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(1, result.returncode, result.stdout)
        self.assertIn(f"{RECORD}:3: ", findings(result)[0])


def released_checker(directory: str) -> Path:
    path = Path(directory) / "released-check-decisions.py"
    text = subprocess.run(["git", "show", f"{RELEASED}:assets/toolkit/scripts/check-decisions.py"], cwd=ROOT,
                          text=True, capture_output=True, check=True, encoding="utf-8").stdout
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def empty(repo: Path) -> None:
    """A project with nothing under specs/."""
    shutil.rmtree(repo / "specs")


def with_logs(repo: Path) -> None:
    """A project with decisions and a demo, and no record."""
    demo = ("## 2026-10-03T00:00:00Z — accepted · iteration 1 · drive-hand (sonnet)\n- **Started with:** a\n"
            "- **Driven through:** b\n- **Examples:** c\n- **Evidence:** none\n- **Feedback:** d\n")
    (repo / "specs/f/decisions.md").write_text("# Decisions\n\n" + scope_entry(1), encoding="utf-8")
    (repo / "specs/f/slices/S1/demo-log.md").write_text("# Demo\n\n" + demo, encoding="utf-8")


def with_own_specs(repo: Path) -> None:
    """This repository's own specs/, which holds no hand-backs.md."""
    shutil.rmtree(repo / "specs")
    shutil.copytree(ROOT / "specs", repo / "specs")


class NothingRecordedTest(unittest.TestCase):
    def triple(self, build: Callable[[Path], None], released: bool) -> tuple[int, str, str]:
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as other:
            repo = scratch(directory, decisions=0)
            if released:
                shutil.copy(released_checker(other), repo / "scripts/check-decisions.py")
            build(repo)
            result = run(repo)
        return result.returncode, result.stdout, result.stderr

    def test_e1_without_a_record_stdout_stderr_and_exit_equal_the_released_checkers(self) -> None:
        for build in (empty, with_logs, with_own_specs):
            with self.subTest(build.__name__):
                self.assertEqual(self.triple(build, True), self.triple(build, False))

    def test_e1_the_tree_with_logs_is_not_the_empty_answer(self) -> None:
        returncode, stdout, _ = self.triple(with_logs, False)
        self.assertEqual(0, returncode)
        self.assertIn("1 decision(s) in 1 file(s), 1 demo(s) in 1 log(s), every field", stdout)

    def test_e2_a_tree_whose_only_record_is_hand_backs_is_not_nothing_recorded_yet(self) -> None:
        result = gate(entry(valid() | {"decisions": []}), decisions=0)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNotIn("nothing recorded yet", result.stdout)
        self.assertIn("0 decision(s) in 0 file(s), 0 demo(s) in 0 log(s), 1 hand-back(s) in 1 record(s)", result.stdout)

    def test_e2_the_feature_level_record_is_read_too(self) -> None:
        result = gate(entry("[1]"), path="specs/f/hand-backs.md")
        self.assertEqual(1, result.returncode)
        self.assertIn("  specs/f/hand-backs.md:1: ", result.stderr)

    def test_e3_a_malformed_record_and_a_malformed_decision_report_under_one_header(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = scratch(directory, entry("[1]"), decisions=1)
            broken = decision(1).replace("- **Why:** because\n", "")
            (repo / "specs/f/decisions.md").write_text("# Decisions\n\n" + broken, encoding="utf-8")
            result = run(repo)
        self.assertEqual(1, result.returncode)
        self.assertEqual(1, result.stderr.count("the record is not in the shape"))
        self.assertEqual(2, len(findings(result)), result.stderr)
        self.assertTrue(findings(result)[0].startswith("specs/f/decisions.md"))
        self.assertTrue(findings(result)[1].startswith(RECORD))


if __name__ == "__main__":
    unittest.main()
