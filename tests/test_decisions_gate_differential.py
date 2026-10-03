"""The gate refuses nothing a log written before the `Scope:` line can contain (D65, AC-S02-57, -83, -85).

A log with no `Scope:` line is run through the gate (no argument) as released at `596740f` and as it stands, in a
scratch project each, over the shapes a log can have gone wrong in. The exit code and the findings on stderr are the
same; stdout is the same but for `note:` lines, which the gate may gain (D65: a second `Status:` line is noted, never
refused). The one stated exception is a log that is not UTF-8: a traceback then, one line now, exit 1 both.
"""
from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from test_decisions_scope import SCRIPT, entry, run, scratch
from test_decisions_scope_gate import FIXTURE, released_checker

BOM = "﻿"
TITLE = "# Decisions\n\n"


def second(label: str, first: str, again: str) -> str:
    text = entry(1)
    marker = f"- **{label}:** standing\n"
    return text.replace(marker, f"- **{label}:** {first}\n- **{label}:** {again}\n")


def inside(text: str, separator: str, rest: str = "- **Status:** overridden by D1") -> str:
    return text.replace("- **Why:** because", f"- **Why:** before{separator}{rest}")


def logs() -> dict[str, bytes]:
    """Each log as the bytes of the whole file, title included where the case keeps one."""
    two = entry(1) + "\n" + entry(2)
    two2 = "\n" + entry(2)
    fields = entry(1).splitlines(keepends=True)
    swapped = "".join(fields[:2] + [fields[4], fields[3]] + fields[5:])
    cases: dict[str, str] = {
        "well-formed": TITLE + two,
        "status twice, standing then overridden": TITLE + second("Status", "standing", "overridden by D1") + two2,
        "status twice, overridden then standing": TITLE + second("Status", "overridden by D1", "standing") + two2,
        "status again inside a fence at column 0": TITLE + entry(1).replace(
            "- **Status:**", "```\n- **Status:** overridden by D9\n```\n- **Status:**"),
        "byte-order mark before the title": BOM + TITLE + two,
        "byte-order mark before D1, no title, one entry": BOM + entry(1),
        "byte-order mark before D1, no title, two entries": BOM + two,
        "fields out of order": TITLE + swapped,
        "a field missing": TITLE + entry(1).replace("- **Why:** because\n", ""),
        "a heading in the wrong shape": TITLE + entry(1).replace("## D1 — ", "## D1 - ") + "\n" + entry(2),
        "empty file": "",
    }
    for name, separator in (("U+2028", " "), ("form feed", "\x0c"), ("U+0085", "\u0085")):
        cases[f"{name} before a status label inside a field"] = TITLE + inside(entry(1), separator)
        cases[f"{name} before a heading inside a field"] = TITLE + inside(entry(1), separator, "## D9 — x") + entry(2)
    found = {name: text.encode("utf-8") for name, text in cases.items()}
    found["CRLF line endings"] = (TITLE + two).replace("\n", "\r\n").encode("utf-8")
    found["CRLF line endings, a second status"] = (
        TITLE + second("Status", "standing", "overridden by D1")).replace("\n", "\r\n").encode("utf-8")
    found["this repository's own decisions.md"] = FIXTURE.read_bytes()
    return found


def gate_of(script: Path, log: bytes) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as directory:
        repo = scratch(directory, "", script=script)
        (repo / "specs/f/decisions.md").write_bytes(log)
        return run(repo)


def without_notes(stdout: str) -> list[str]:
    return [line for line in stdout.splitlines() if not line.startswith("check-decisions: note:")]


class GateHoldsTheReleasedCheckersAnswerTest(unittest.TestCase):
    def test_e57_a_log_with_no_scope_line_gets_the_exit_code_and_findings_the_released_checker_gave(self) -> None:
        with tempfile.TemporaryDirectory() as other:
            released = released_checker(other)
            for name, log in logs().items():
                before, after = gate_of(released, log), gate_of(SCRIPT, log)
                self.assertEqual((before.returncode, before.stderr), (after.returncode, after.stderr), name)
                self.assertEqual(without_notes(before.stdout), without_notes(after.stdout), name)

    def test_e83_a_second_status_line_is_a_note_naming_the_entry_and_never_a_finding(self) -> None:
        for first, again in (("standing", "overridden by D1"), ("overridden by D1", "standing")):
            result = gate_of(SCRIPT, (TITLE + second("Status", first, again) + "\n" + entry(2)).encode("utf-8"))
            self.assertEqual((0, ""), (result.returncode, result.stderr), (first, result.stdout))
            notes = [line for line in result.stdout.splitlines() if line.startswith("check-decisions: note:")]
            self.assertEqual(1, len(notes), result.stdout)
            self.assertIn("D1", notes[0])
            self.assertIn("`Status:`", notes[0])

    def test_e83_a_second_scope_line_is_still_a_finding(self) -> None:
        text = entry(1, "global").replace("- **Scope:** global\n", "- **Scope:** global\n- **Scope:** S1\n")
        result = gate_of(SCRIPT, (TITLE + text).encode("utf-8"))
        self.assertEqual(1, result.returncode, result.stdout)
        self.assertIn("D1 has more than one `Scope:` line", result.stderr)

    def test_e85_a_byte_order_mark_before_the_first_entry_leaves_the_gate_as_the_released_one_was(self) -> None:
        broken = BOM + entry(1).replace("- **Why:** because\n", "")
        result = gate_of(SCRIPT, broken.encode("utf-8"))
        self.assertEqual((0, ""), (result.returncode, result.stderr), result.stdout)

    def test_e86_hold_a_log_that_is_not_utf_8_exits_one_both_ways_but_the_traceback_is_gone(self) -> None:
        with tempfile.TemporaryDirectory() as other:
            before, after = gate_of(released_checker(other), b"# D\n\xff\n"), gate_of(SCRIPT, b"# D\n\xff\n")
        self.assertEqual((1, 1), (before.returncode, after.returncode))
        self.assertIn("Traceback", before.stderr)
        self.assertEqual(1, len(after.stderr.strip().splitlines()))


if __name__ == "__main__":
    unittest.main()
