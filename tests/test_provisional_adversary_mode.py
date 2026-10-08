"""S27 Phase 4, T041 (B3, B4; D209, AC-S27-24): a provisional Status is only possible where the logs show a person
climbed to `provisional` first, a mode entry is dated when it was written, and the verb takes `decide` from the file.

Each case writes logs into a scratch project holding the three toolkit scripts and runs the gate or the verb as a
`python3 -B` subprocess, the way a generated project holds them.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from provisional_fixture import EASY_LINE, NAMES, WHEN, entry, run
from reversibility_fixture import scratch

sys.dont_write_bytecode = True

PROVISIONAL = "provisional · ratify by 2026-10-14"
BEFORE = "2026-10-01T09:00:00Z"  # before the entries' WHEN, 2026-10-07T21:17:49Z
AFTER = "2026-10-07T22:00:00Z"  # after it, and before now


def mode(number: int, to: str = "provisional", before: str = "provisional-advisory", when: str = BEFORE) -> str:
    """A mode entry as `cruise.py mode` writes it."""
    return (f"## D{number} — decide moved from {before} to {to}\n"
            f"- **Stage:** iteration start · **Slice:** none · **When:** {when} · **Iteration:** 1\n"
            "- **Scope:** global\n- **Question:** which `decide` mode does this run work under?\n"
            "- **Options:** a · b\n- **Decision:** to\n- **Why:** a person set it\n- **Decided by:** human\n"
            "- **Confidence:** high · **Would reverse if:** a person sets `decide` again\n"
            "- **Written to:** `.specify/cruise.json`\n- **Status:** standing\n")


def provisional(number: int = 1) -> str:
    return entry(number, PROVISIONAL, revert="own", reversibility=EASY_LINE)


def gate(logs: dict[str, str]) -> subprocess.CompletedProcess[str]:
    """The gate over `logs` (feature name to the entries of its log); `.specify/cruise.json` exists."""
    with tempfile.TemporaryDirectory() as directory:
        repo = scratch(directory, "", names=NAMES, listed=("scripts/check-decisions.py",))
        (repo / ".specify").mkdir()
        (repo / ".specify/cruise.json").write_text("{}\n", encoding="utf-8")
        for feature, log in logs.items():
            (repo / "specs" / feature).mkdir(exist_ok=True)
            (repo / "specs" / feature / "decisions.md").write_text("# Decisions\n\n" + log, encoding="utf-8")
        return run(repo, "check-decisions")


def findings(result: subprocess.CompletedProcess[str]) -> list[str]:
    return [row.strip() for row in result.stderr.splitlines() if row.startswith("  ")]


class ModeEntryTest(unittest.TestCase):
    def passes(self, logs: dict[str, str]) -> None:
        result = gate(logs)
        self.assertEqual((0, ""), (result.returncode, result.stderr), result.stdout)

    def refused(self, logs: dict[str, str], *words: str) -> list[str]:
        result = gate(logs)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        found = findings(result)
        self.assertEqual(1, len(found), found)
        for word in words:
            self.assertIn(word, found[0])
        return found


class TheModeWasInForceTest(ModeEntryTest):
    def test_t041_b3_a_mode_entry_dated_after_the_gate_runs_is_refused_naming_it(self) -> None:
        self.refused({"f": mode(1, when="2099-01-01T00:00:00Z")}, "specs/f/decisions.md", "D1", "2099-01-01", "after")

    def test_t041_b3b_a_future_mode_entry_is_no_basis_for_a_provisional_status(self) -> None:
        found = gate({"f": mode(1, when="2099-01-01T00:00:00Z") + provisional(2)})
        self.assertEqual(1, found.returncode)
        self.assertTrue(any("D2" in row and "no mode entry" in row for row in findings(found)), found.stderr)

    def test_t041_b3c_a_mode_entry_dated_in_the_past_passes_alone_and_with_an_offset(self) -> None:
        self.passes({"f": mode(1, when="2026-10-01T09:00:00+02:00")})
        self.passes({"f": mode(1, when="2026-10-01")})

    def test_t041_b3d_a_log_with_nothing_but_a_mode_entry_is_held_for_its_date(self) -> None:
        self.refused({"f": mode(1, to="skipper-always", before="recommended-first", when="2099-01-01T00:00:00Z")},
                     "D1", "after")

    def test_t041_d209_a_provisional_status_with_no_mode_entry_in_any_log_is_refused(self) -> None:
        self.refused({"f": provisional()}, "D1", "`Status`", "mode entry")

    def test_t041_d209b_a_mode_entry_to_provisional_before_it_in_the_same_log_is_the_basis(self) -> None:
        self.passes({"f": mode(1) + provisional(2)})

    def test_t041_d209c_a_mode_entry_in_another_features_log_is_the_basis_too(self) -> None:
        self.passes({"f": provisional(), "g": mode(1)})

    def test_t041_d209d_the_last_mode_entry_before_it_must_record_provisional(self) -> None:
        stepped_down = mode(1) + mode(2, to="provisional-advisory", before="provisional", when="2026-10-03T00:00:00Z")
        self.refused({"f": stepped_down + provisional(3)}, "D3", "provisional-advisory")

    def test_t041_d209e_a_mode_entry_dated_after_the_provisional_one_is_no_basis_for_it(self) -> None:
        self.refused({"f": provisional(1), "g": mode(1, when=AFTER)}, "D1", "mode entry")

    def test_t041_d209f_a_later_climb_back_restores_it_and_a_step_down_after_it_does_not_undo_it(self) -> None:
        down_up = (mode(1) + mode(2, to="provisional-advisory", before="provisional", when="2026-10-03T00:00:00Z")
                   + mode(3, to="provisional", before="provisional-advisory", when="2026-10-04T00:00:00Z"))
        self.passes({"f": down_up + provisional(4)})
        self.passes({"f": mode(1) + provisional(2) + mode(3, to="provisional-advisory", before="provisional",
                                                           when=AFTER)})

    def test_t041_d209g_a_ratified_or_standing_entry_needs_no_mode_entry(self) -> None:
        self.passes({"f": entry(1, "ratified 2026-10-08", reversibility=EASY_LINE) + entry(2, "standing")})

    def test_t041_d209h_a_fenced_mode_entry_is_no_mode_entry(self) -> None:
        self.refused({"f": "```\n" + mode(1) + "```\n\n" + provisional(1)}, "D1", "mode entry")


def verb(decide: str, file: str | None, *more: str) -> subprocess.CompletedProcess[str]:
    """`provisional.py status` in a scratch project whose `.specify/cruise.json` holds `file` (None: no file)."""
    with tempfile.TemporaryDirectory() as directory:
        repo = Path(scratch(directory, "", names=NAMES))
        if file is not None:
            (repo / ".specify").mkdir()
            (repo / ".specify/cruise.json").write_text(file, encoding="utf-8")
        return run(repo, "provisional", "status", "--decide", decide, "--ask", "approval", "--when", WHEN, "--number",
                   "D3", "--reversibility", EASY_LINE, *more)


class TheVerbReadsDecideTest(unittest.TestCase):
    def test_t041_b4_a_decide_that_differs_from_the_file_is_refused_in_one_line(self) -> None:
        for held, passed in (("recommended-first", "provisional"), ("provisional", "recommended-first"),
                             ("skipper-always", "provisional-advisory")):
            result = verb(passed, json.dumps({"decide": held}))
            self.assertEqual((2, ""), (result.returncode, result.stdout), result.stderr)
            self.assertIn(f"--decide '{passed}'", result.stderr)
            self.assertIn(f"'{held}'", result.stderr)
            self.assertIn("cruise.json", result.stderr)

    def test_t041_b4b_no_decide_key_is_the_bottom_rung_and_so_is_a_value_that_is_not_one_of_the_five(self) -> None:
        for file in ("{}", json.dumps({"decide": "anything"})):
            self.assertEqual(2, verb("provisional", file).returncode, file)
            self.assertEqual(0, verb("recommended-first", file).returncode, file)

    def test_t041_b4c_the_same_decide_gives_the_answer_it_always_gave(self) -> None:
        result = verb("provisional", json.dumps({"decide": "provisional"}))
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("- **Status:** provisional · ratify by 2026-10-14", result.stdout)

    def test_t041_b4d_a_file_that_cannot_be_read_is_refused_and_no_file_is_not_a_check(self) -> None:
        for file in ("{", "[]", '"x"'):
            self.assertEqual(2, verb("provisional", file).returncode, file)
        self.assertEqual(0, verb("provisional", None).returncode)


if __name__ == "__main__":
    unittest.main()
