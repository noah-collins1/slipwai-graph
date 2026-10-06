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
