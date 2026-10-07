"""R4 (AC-S26-9, -10, -14): the gate holds a decision entry's `Reversibility:` line to its grammar and to its rules.

Each case writes a log into a scratch project that holds both scripts and runs the gate as a `python3 -B` subprocess.
"""
from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

from reversibility_fixture import EASY, SCRIPTS, entry, gate, scratch
from test_decisions_scope_gate import released_checker

sys.dont_write_bytecode = True


def loaded(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(f"held_{path.stem.replace('-', '_')}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def line(tiers: str = "easy", rules: str = "1", **changes: str) -> str:
    """A `Reversibility:` line over the easy facts with `changes` applied; `""` drops a key."""
    merged = {**EASY, **changes}
    written = " ".join(f"{key}={value}" for key, value in merged.items() if value != "")
    return f"- **Reversibility:** {tiers} · rules {rules} · {written}"


class GateHoldsTheLineTest(unittest.TestCase):
    def run_gate(self, *entries: str, listed: tuple[str, ...] | None = ("scripts/check-decisions.py",),
                 ) -> tuple[int, str, str]:
        with tempfile.TemporaryDirectory() as directory:
            repo = scratch(directory, "\n".join(entries), listed=listed)
            result = gate(repo)
        return result.returncode, result.stdout, result.stderr

    def refused(self, found: tuple[int, str, str], *words: str) -> None:
        code, out, err = found
        self.assertEqual(1, code, out + err)
        findings = [row for row in err.splitlines() if row.startswith("  ")]
        self.assertEqual(1, len(findings), err)
        for word in words:
            self.assertIn(word, findings[0])

    def test_e1_a_well_formed_easy_line_passes(self) -> None:
        code, out, err = self.run_gate(entry(1, line()))
        self.assertEqual((0, ""), (code, err), out)

    def test_e2_a_tier_word_that_is_not_a_tier_is_refused_naming_the_entry_and_the_field(self) -> None:
        self.refused(self.run_gate(entry(1, line("medium"))), "decisions.md:", ": D1 ", "`Reversibility`", "medium")

    def test_e3_a_skipped_step_and_a_lowering_step_are_refused(self) -> None:
        self.refused(self.run_gate(entry(1, line("easy → hard"))), "D1", "`Reversibility`", "skips")
        self.refused(self.run_gate(entry(1, line("hard → guarded", ci_workflow="yes"))), "D1", "lowers")
        self.refused(self.run_gate(entry(1, line("easy → easy"))), "D1", "repeats")

    def test_e4_an_unknown_rules_version_is_refused(self) -> None:
        self.refused(self.run_gate(entry(1, line(rules="9"))), "D1", "`Reversibility`", "rules 9")

    def test_e5_a_key_that_is_not_a_fact_is_refused_naming_the_key(self) -> None:
        self.refused(self.run_gate(entry(1, line() + " size=large")), "D1", "`size`")
        self.refused(self.run_gate(entry(1, line() + " export=no")), "D1", "`export`", "twice")
        self.refused(self.run_gate(entry(1, line() + " loose")), "D1", "'loose'", "key=value")

    def test_e6_a_second_line_is_refused(self) -> None:
        self.refused(self.run_gate(entry(1, line() + "\n" + line())), "D1", "more than one `Reversibility:`")

    def test_e7_an_easy_line_the_facts_do_not_support_is_refused_naming_the_fact(self) -> None:
        self.refused(self.run_gate(entry(1, line(ci_workflow="yes"))), "D1", "`Reversibility`", "ci_workflow=yes")

    def test_e8_a_hard_line_with_an_unaccepted_fact_is_accepted(self) -> None:
        code, out, err = self.run_gate(entry(1, line("hard", schema="maybe")))
        self.assertEqual((0, ""), (code, err), out)
        self.refused(self.run_gate(entry(1, line("easy", schema="maybe"))), "schema=maybe")

    def test_e9_migrate_file_no_is_refused_while_a_written_path_is_on_the_list_or_no_list_exists(self) -> None:
        listed = entry(1, line(), written="`scripts/check-decisions.py`")
        self.refused(self.run_gate(listed), "D1", "migrate_file")
        self.refused(self.run_gate(entry(1, line()), listed=None), "D1", "migrate_file", "no committed list")
        self.assertEqual(0, self.run_gate(entry(1, line()), listed=("somewhere/else",))[0])

    def test_e10_an_escalation_whose_first_tier_is_right_is_accepted(self) -> None:
        code, out, err = self.run_gate(entry(1, line("easy → guarded → hard")))
        self.assertEqual((0, ""), (code, err), out)

    def test_a_log_with_no_line_is_not_refused_and_the_findings_name_each_entry_once(self) -> None:
        code, out, err = self.run_gate(entry(1), entry(2, line()), entry(3, line("medium")))
        self.assertEqual(1, code, out)
        self.assertEqual(1, len([row for row in err.splitlines() if row.startswith("  ")]), err)
        self.assertIn(": D3 ", err)

    def test_the_gate_reads_scope_with_its_own_scope_tokens(self) -> None:
        severals = entry(1, line("guarded"), scope="S1, S2")
        self.assertEqual(0, self.run_gate(severals)[0])
        self.refused(self.run_gate(entry(1, line("easy"), scope="S1, S2")), "D1", "guarded")
        code, _, err = self.run_gate(entry(1, line("easy"), scope="S01-S03"))  # unreadable: the scope finding too
        self.assertEqual(1, code)
        self.assertIn("rules 1 derive hard", err)

    def test_a_list_that_is_not_utf8_is_no_list_said_in_one_finding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = scratch(directory, entry(1, line()), listed=())
            (repo / ".slipwai/propagated").write_bytes(b"scripts/\xff\n")
            result = gate(repo)
        self.refused((result.returncode, result.stdout, result.stderr), "D1", "migrate_file", "no committed list")

    def test_the_verb_reads_scope_and_written_to_as_the_gate_does(self) -> None:
        """`reversibility.py` carries copies of the gate's readers so that it runs alone: they must give its answers."""
        held, verb = (loaded(SCRIPTS / name) for name in ("check-decisions.py", "reversibility.py"))
        for value in ("S1", "S1, S2", "`S26-reversibility-line`", "global", "global, S1", "", " ", "S01-S03",
                      "oauth2", "S5-oauth2", "s1", "S1,", "S1 S2", "S05-x.S02-y", "S1.2", "ÿ1", "S١"):
            self.assertEqual(held.scope_tokens(value), verb.scope_tokens(value), value)
        for value in ("`a`, `b`", "a, b", "", "`a` and b", "a,,b", " a ", "``"):  # the list reads more (T021)
            self.assertLessEqual(set(held.paths_of(value)), set(verb.written_paths(value)), value)

    def test_a_log_with_a_line_and_no_sibling_module_is_noted_not_refused(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = scratch(directory, entry(1, line("whatever")), names=("check-decisions.py",))
            result = gate(repo)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("reversibility.py is not beside this script", result.stdout)


def proposed(*cited: str) -> str:
    return "- **Proposed rule:** a sentence for the owner brief (same shape as " + ", ".join(cited) + ")"


class ProposedRuleTest(unittest.TestCase):
    """R7 (AC-S26-15, D185): a `Proposed rule:` cites two entries of the log; a cited entry's `Status` is not read."""

    def run_gate(self, *entries: str) -> tuple[int, str, str]:
        with tempfile.TemporaryDirectory() as directory:
            result = gate(scratch(directory, "\n".join(entries)))
        return result.returncode, result.stdout, result.stderr

    def refused(self, found: tuple[int, str, str], *words: str) -> None:
        code, out, err = found
        self.assertEqual(1, code, out + err)
        findings = [row for row in err.splitlines() if row.startswith("  ")]
        self.assertEqual(1, len(findings), err)
        for word in ("decisions.md:", "Proposed rule", *words):
            self.assertIn(word, findings[0])

    def test_e1_two_standing_entries_cited_pass(self) -> None:
        code, out, err = self.run_gate(entry(1), entry(2), entry(3, proposed("D1", "D2")))
        self.assertEqual((0, ""), (code, err), out)

    def test_e2_one_entry_cited_is_refused(self) -> None:
        self.refused(self.run_gate(entry(1), entry(2), entry(3, proposed("D1"))), ": D3 ")

    def test_e3_an_id_that_is_no_entry_is_refused_naming_it(self) -> None:
        self.refused(self.run_gate(entry(1), entry(2), entry(3, proposed("D1", "D9"))), ": D3 ", "D9")

    def test_e4_a_cited_entry_overridden_since_passes(self) -> None:
        overridden = entry(2).replace("**Status:** standing", "**Status:** overridden by D3")
        code, out, err = self.run_gate(entry(1), overridden, entry(3, proposed("D1", "D2")))
        self.assertEqual((0, ""), (code, err), out)

    def test_e5_the_entrys_own_id_is_refused_naming_it(self) -> None:
        self.refused(self.run_gate(entry(1), entry(2), entry(3, proposed("D3", "D1"))), ": D3 ", "D3", "earlier")

    def test_e5a_a_later_entry_is_refused_naming_it(self) -> None:
        """L2 (AC-S26-15 'earlier'): D2 and D3 exist, but they are not before D1."""
        found = self.run_gate(entry(1, proposed("D2", "D3")), entry(2), entry(3))
        self.refused(found, ": D1 ", "D2, D3", "not earlier")
        code, out, err = self.run_gate(entry(1), entry(2), entry(3), entry(4, proposed("D2", "D3")))
        self.assertEqual((0, ""), (code, err), out)
        self.refused(self.run_gate(entry(1), entry(2), entry(3, proposed("D1", "D4")), entry(4)), ": D3 ", "D4")

    def test_e5b_a_period_after_the_citation_still_reads_it(self) -> None:
        code, out, err = self.run_gate(entry(1), entry(2), entry(3, proposed("D1", "D2") + "."))
        self.assertEqual((0, ""), (code, err), out)

    def test_e5c_text_after_the_citation_is_allowed_and_a_d_number_outside_it_is_not_a_citation(self) -> None:
        for tail in (" — host to adopt", ". Host to adopt (see D9).", " (a note, D7) and more"):
            with self.subTest(tail=tail):
                code, out, err = self.run_gate(entry(1), entry(2), entry(3, proposed("D1", "D2") + tail))
                self.assertEqual((0, ""), (code, err), out)
        self.refused(self.run_gate(entry(1), entry(2), entry(3, proposed("D1") + " — as D2 did")), ": D3 ", "fewer")

    def test_e6_an_entry_without_the_line_is_never_refused(self) -> None:
        code, out, err = self.run_gate(entry(1), entry(2), entry(3, proposed("D1", "D2")), entry(4))
        self.assertEqual((0, ""), (code, err), out)


QUOTE = "- **Reversibility:** <tier> · rules <n> · <facts>"


class FencedQuoteTest(unittest.TestCase):
    """R5 (AC-S26-10, D65; M4): a label inside a code fence is a quotation, not the line, so a log whose only
    labels are quoted gets the answer the released checker gave, and a quote beside the real line is not a second."""

    def run_gate(self, text: str, released: bool = False) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as other:
            repo = scratch(directory, text, listed=("scripts/check-decisions.py",))
            if released:
                shutil.copy(released_checker(other), repo / "scripts/check-decisions.py")
            return gate(repo)

    def quoted(self, fence: str, label: str = QUOTE) -> str:
        return entry(1).replace("- **Written to:**", f"{fence}\n{label}\n{fence}\n- **Written to:**")

    def test_e1_a_fenced_quote_and_no_real_line_passes_as_the_released_checker_passed_it(self) -> None:
        for fence in ("```", "~~~", "````", "  ```"):
            for label in (QUOTE, "- **Proposed rule:** x (same shape as D8)"):
                with self.subTest(fence=fence, label=label):
                    text = self.quoted(fence, label)
                    before, after = self.run_gate(text, released=True), self.run_gate(text)
                    self.assertEqual(0, before.returncode, before.stderr)
                    self.assertEqual((before.returncode, before.stdout, before.stderr),
                                     (after.returncode, after.stdout, after.stderr))

    def test_e2_a_fenced_quote_beside_one_real_line_is_not_more_than_one(self) -> None:
        text = self.quoted("```").replace("- **Written to:**", line() + "\n- **Written to:**", 1)
        result = self.run_gate(text)
        self.assertEqual((0, ""), (result.returncode, result.stderr), result.stdout)

    def test_e3_a_line_after_the_fence_closes_is_real(self) -> None:
        text = self.quoted("```").replace("- **Written to:**", "- **Reversibility:** whatever\n- **Written to:**", 1)
        self.assertEqual(1, self.run_gate(text).returncode)

    def test_e4_a_fence_left_open_hides_the_rest_of_the_log(self) -> None:
        text = entry(1).replace("- **Written to:**", f"```\n{QUOTE}\n- **Written to:**", 1)
        self.assertEqual(self.run_gate(text, released=True).returncode, self.run_gate(text).returncode)


if __name__ == "__main__":
    unittest.main()
