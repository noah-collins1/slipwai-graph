"""The gate refuses nothing a log written before the `Scope:` line can contain (D65, AC-S02-57, -83, -85).

A log with no `Scope:` line is run through the gate (no argument) as released at `596740f` and as it stands, in a
scratch project each, over the shapes a log can have gone wrong in. The exit code and the findings on stderr are the
same; stdout is the same but for `note:` lines, which the gate may gain (D65: a second `Status:` line is noted, never
refused). The one stated exception is a log that is not UTF-8: a traceback then, one line now, exit 1 both.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_decisions_scope import SCRIPT, entry, run, scratch
from test_decisions_scope_gate import own_log, released_checker

from slipwai.assets import ROOT

BOM = "﻿"
TITLE = "# Decisions\n\n"


def second(label: str, first: str, again: str) -> str:
    text = entry(1)
    marker = f"- **{label}:** standing\n"
    return text.replace(marker, f"- **{label}:** {first}\n- **{label}:** {again}\n")


def inside(text: str, separator: str, rest: str = "- **Status:** overridden by D1") -> str:
    return text.replace("- **Why:** because", f"- **Why:** before{separator}{rest}")


def proposing(number: int, cited: str) -> str:
    """An entry with a `Proposed rule:` line, which a log written before S26 could hold (B1, D65)."""
    return entry(number).replace("- **Written to:**", f"- **Proposed rule:** ask first (same shape as {cited})\n"
                                 "- **Written to:**")


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
        "a `Proposed rule:` line citing one entry, no `Reversibility:`": TITLE + entry(1) + "\n" + proposing(2, "D1"),
        "a `Proposed rule:` line citing no entry, no `Reversibility:` line": TITLE + proposing(1, "D7, D9"),
    }
    for name, separator in (("U+2028", " "), ("form feed", "\x0c"), ("U+0085", "\u0085")):
        cases[f"{name} before a status label inside a field"] = TITLE + inside(entry(1), separator)
        cases[f"{name} before a heading inside a field"] = TITLE + inside(entry(1), separator, "## D9 — x") + entry(2)
    found = {name: text.encode("utf-8") for name, text in cases.items()}
    found["CRLF line endings"] = (TITLE + two).replace("\n", "\r\n").encode("utf-8")
    found["CRLF line endings, a second status"] = (
        TITLE + second("Status", "standing", "overridden by D1")).replace("\n", "\r\n").encode("utf-8")
    found["this repository's own decisions.md"] = own_log().encode("utf-8")
    return found


def gate_of(script: Path, log: bytes, beside: bool = False) -> subprocess.CompletedProcess[str]:
    """The gate over `log`; `beside` puts `reversibility.py` in the scratch project's scripts as a project holds it."""
    with tempfile.TemporaryDirectory() as directory:
        repo = scratch(directory, "", script=script)
        if beside:
            shutil.copy(SCRIPT.with_name("reversibility.py"), repo / "scripts/reversibility.py")
        (repo / "specs/f/decisions.md").write_bytes(log)
        return run(repo)


def checker_at(ref: str, directory: str) -> Path:
    """`check-decisions.py` as committed at `ref`, written beside nothing."""
    path = Path(directory) / f"check-decisions-{ref}.py"
    text = subprocess.run(["git", "show", f"{ref}:assets/toolkit/scripts/check-decisions.py"], cwd=ROOT, text=True,
                          capture_output=True, check=True, encoding="utf-8").stdout
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def gate_with(script: Path, log: bytes, scripts: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
    """The gate over `log` in a scratch project holding `scripts` (names under `assets/toolkit/scripts/`) beside it."""
    with tempfile.TemporaryDirectory() as directory:
        repo = scratch(directory, "", script=script)
        for name in scripts:
            shutil.copy(SCRIPT.with_name(name), repo / "scripts" / name)
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

    def test_s26_r5_e1_the_same_cases_beside_reversibility_py_get_the_released_checkers_answer(self) -> None:
        """A guard over the loader (AC-S26-10): no case carries a `Reversibility:` or `Proposed rule:` line, so the
        module present beside the gate changes nothing."""
        with tempfile.TemporaryDirectory() as other:
            released = released_checker(other)
            for name, log in logs().items():
                before, after = gate_of(released, log), gate_of(SCRIPT, log, beside=True)
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


BEFORE_S27 = "5f4fc00"  # the checker as S26 left it, the last one that knows nothing of `provisional.py`


class GateHoldsTheEarlierAnswerBesideProvisionalPyTest(unittest.TestCase):
    """S27 R6 (AC-S27-7): a log with no provisional, ratified, reverted or rehearsal line gets the earlier answer."""

    def test_r6_e1_every_case_and_this_repositorys_log_with_all_three_scripts_beside_get_both_earlier_answers(
            self) -> None:
        with tempfile.TemporaryDirectory() as other:
            released, before = released_checker(other), checker_at(BEFORE_S27, other)
            for name, log in logs().items():
                after = gate_with(SCRIPT, log, ("reversibility.py", "provisional.py"))
                for earlier in (gate_of(released, log), gate_of(before, log, beside=True)):
                    self.assertEqual((earlier.returncode, earlier.stderr), (after.returncode, after.stderr), name)
                    self.assertEqual(without_notes(earlier.stdout), without_notes(after.stdout), name)

    def test_r6_e2_a_revert_line_on_a_standing_entry_passed_before_and_is_refused_now(self) -> None:
        """D65's carve-out (P4): `Revert:` is a label only this release defines, so a log that carried one passed an
        earlier checker and is refused by this one, naming the entry and the field."""
        log = (TITLE + entry(1).replace("- **Status:** standing\n", "- **Status:** standing\n"
                                        "- **Revert:** commits carrying Decision: D1\n")).encode("utf-8")
        with tempfile.TemporaryDirectory() as other:
            before = gate_with(checker_at(BEFORE_S27, other), log, ("reversibility.py",))
        after = gate_with(SCRIPT, log, ("reversibility.py", "provisional.py"))
        self.assertEqual(0, before.returncode, before.stderr)
        self.assertEqual(1, after.returncode, after.stdout)
        self.assertIn("D1", after.stderr)
        self.assertIn("`Revert`", after.stderr)

    def test_r6_e3_without_provisional_py_beside_it_a_log_with_no_new_form_gets_the_same_answer(self) -> None:
        for name, log in logs().items():
            without = gate_with(SCRIPT, log, ("reversibility.py",))
            beside = gate_with(SCRIPT, log, ("reversibility.py", "provisional.py"))
            self.assertEqual((without.returncode, without.stdout, without.stderr),
                             (beside.returncode, beside.stdout, beside.stderr), name)


if __name__ == "__main__":
    unittest.main()
