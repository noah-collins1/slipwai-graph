"""Every page that owns a stop with delegates says when each block is appended, and what a skipper's block names."""
from __future__ import annotations

from support import FactoryTestCase
from test_result_contract_briefs import ADOPTED, brief, command

from slipwai.layout import AT_ROOT


def flat(text: str) -> str:
    return " ".join(text.split())


class SkipperAnswerTest(FactoryTestCase):
    def test_the_cruise_text_puts_the_skippers_own_number_in_change_summary_never_in_decisions(self) -> None:
        for layout in (AT_ROOT, ADOPTED):
            text = flat(command("cruise", layout))
            with self.subTest(layout=layout.delivery):
                self.assertNotIn("the entry's `D<n>` in `decisions`", text)
                self.assertIn("own `D<n>` goes in the block's `change_summary` and never in `decisions`", text)
                self.assertIn("which lists only the standing entries the work relied on", text)

    def test_an_unavailable_answer_is_an_entry_in_the_protocol_and_in_the_skipper_brief(self) -> None:
        for layout in (AT_ROOT, ADOPTED):
            cruise = flat(command("cruise", layout))
            skipper = flat(brief("drive-skipper", layout))
            with self.subTest(layout=layout.delivery):
                self.assertIn("An `unavailable` answer is an entry too, appended at `Status: standing`", cruise)
                self.assertIn("a person overrides it as they override any entry", cruise)
                self.assertIn("An `unavailable` answer is still the entry", skipper)
                self.assertIn("Your own `D<n>` goes in `change_summary` and never in `decisions`", skipper)
                self.assertNotIn("`unavailable: <what a person must provide>`", skipper)


def section(text: str, heading: str) -> str:
    return text.split(heading, 1)[1].split("\n## ", 1)[0]


class StopsTest(FactoryTestCase):
    def test_the_adversary_page_appends_each_block_before_it_ends_the_benchmark_entry(self) -> None:
        for event in (False, True):
            for layout in (AT_ROOT, ADOPTED):
                where = f"{layout.delivery}/" if layout.moved else ""
                text = flat(command("adversary", layout, event))
                with self.subTest(event=event, layout=layout.delivery):
                    verb = f"python3 {where}scripts/check-decisions.py --hand-back specs/<feature>/slices/<id> "
                    self.assertIn(verb + "drive-adversary adversary", text)
                    self.assertIn(f"({where}docs/result-contract.md)", text)
                    self.assertLess(text.index(verb), text.rindex("end the `adversary` benchmark entry"))
                    self.assertIn("one continuation", text)

    def test_the_completion_audit_is_the_backstop_for_every_slices_record(self) -> None:
        for layout in (AT_ROOT, ADOPTED):
            where = f"{layout.delivery}/" if layout.moved else ""
            text = flat(section(command("cruise", layout), "## When the ready set is empty: the completion audit"))
            with self.subTest(layout=layout.delivery):
                self.assertIn("each audit `drive-gaps` delegate also runs "
                              f"`python3 {where}scripts/check-decisions.py --hand-backs` over every slice", text)
                self.assertIn("a delegated stage with neither a passing block nor a `Missing:` line is an audit "
                              "finding", text)
                self.assertIn(f"python3 {where}scripts/check-decisions.py --hand-back specs/<feature> drive-gaps audit",
                              text)
                self.assertLess(text.index("--hand-back specs/<feature> drive-gaps audit"),
                                text.index("Only an audit with nothing left to build ends with `cruise: done`"))

    def test_every_page_that_owns_a_stop_with_delegates_appends_before_it_closes_the_stage(self) -> None:
        for layout in (AT_ROOT, ADOPTED):
            pages = {
                "drive": section(command("drive", layout), "## What every delegate hands back"),
                "cruise": command("cruise", layout),
                "adversary": command("adversary", layout),
                "audit": section(command("cruise", layout), "## When the ready set is empty: the completion audit"),
            }
            for name, text in pages.items():
                with self.subTest(layout=layout.delivery, page=name):
                    self.assertIn("--hand-back ", text)
                    self.assertRegex(flat(text), r"before (it|you) (close|end)s? the|before the stage's benchmark "
                                                 r"entry closes|before ending the|before you end the|before the audit")

    def test_a_continuation_after_the_entry_closed_is_recorded_with_started(self) -> None:
        for layout in (AT_ROOT, ADOPTED):
            text = flat(section(command("drive", layout), "## What every delegate hands back"))
            with self.subTest(layout=layout.delivery):
                self.assertIn("A continuation recorded after the stage's benchmark entry has closed passes "
                              "`--started <instant>` to either verb, the instant the `--hand-backs` line names", text)
                self.assertIn("on time, the verb finds the open entry itself", text)
