"""R1 and R2 (AC-S27-1 to -6, -10 verb half): `provisional.py status` prints a decision's Status from `decide`.

The verb reads no file; it runs as a `python3 -B` subprocess in a scratch project holding the scripts.
"""
from __future__ import annotations

import sys
import unittest

from provisional_fixture import EASY_LINE, FLAG_LINE, GUARDED_LINE, HARD_LINE, raw, status

sys.dont_write_bytecode = True

STANDING = "- **Status:** standing"
UNAVAILABLE = "unavailable: a person's approval"
REVERT = "- **Revert:** commits carrying Decision: D12"
MODES = ("recommended-first", "skipper-always", "provisional-shadow", "provisional-advisory")


class ProvisionalTableTest(unittest.TestCase):
    def lines(self, *arguments: str, **keywords: str) -> list[str]:
        result = status(*arguments, **keywords)
        self.assertEqual(0, result.returncode, result.stderr)
        return result.stdout.splitlines()

    def test_e1_a_guarded_item_under_provisional_is_provisional_for_seven_days_with_its_revert(self) -> None:
        self.assertEqual(["- **Status:** provisional · ratify by 2026-10-14", REVERT],
                         self.lines("provisional", line=GUARDED_LINE))

    def test_e2_an_easy_item_is_too(self) -> None:
        self.assertEqual(["- **Status:** provisional · ratify by 2026-10-14", REVERT],
                         self.lines("provisional", line=EASY_LINE))

    def test_e3_seven_days_are_counted_across_a_year_end_in_utc_dates(self) -> None:
        got = self.lines("provisional", line=EASY_LINE, when="2026-12-28T00:00Z")
        self.assertEqual(["- **Status:** provisional · ratify by 2027-01-04"], got[:1])

    def test_e4_the_d54_fixture_is_unavailable(self) -> None:
        self.assertEqual([UNAVAILABLE, STANDING], self.lines("provisional", line=HARD_LINE))

    def test_e5_flag_default_yes_is_unavailable_and_stderr_names_it(self) -> None:
        result = status("provisional", line=FLAG_LINE)
        self.assertEqual(([UNAVAILABLE, STANDING], 1), (result.stdout.splitlines(), len(result.stderr.splitlines())))
        self.assertIn("flag_default=yes", result.stderr)

    def test_e6_every_other_value_is_unavailable_for_every_tier(self) -> None:
        for decide in MODES:
            for name, line in (("easy", EASY_LINE), ("guarded", GUARDED_LINE), ("hard", HARD_LINE)):
                got = self.lines(decide, line=line)
                self.assertEqual(([UNAVAILABLE], [STANDING]), (got[:1], got[-1:]), (decide, name))

    def test_e7_no_reversibility_line_is_hard(self) -> None:
        result = status("provisional")
        self.assertEqual([UNAVAILABLE, STANDING], result.stdout.splitlines())
        self.assertIn("hard", result.stderr)

    def test_e8_the_last_step_of_the_line_governs(self) -> None:
        line = GUARDED_LINE.replace("guarded", "easy → guarded → hard", 1).replace(
            "rollback_complexity=hours", "rollback_complexity=days")
        self.assertEqual([UNAVAILABLE, STANDING], self.lines("provisional", line=line))

    def test_e9_no_approval_asked_is_standing_only_under_each_value(self) -> None:
        for decide in ("provisional", *MODES):
            self.assertEqual([STANDING], self.lines(decide, "no", line=EASY_LINE), decide)

    def test_e10_a_fact_a_must_and_a_release_are_unavailable_whatever_decide_says(self) -> None:
        for ask in ("fact", "must", "release"):
            got = self.lines("provisional", ask, line=EASY_LINE)
            self.assertEqual(2, len(got), ask)
            self.assertTrue(got[0].startswith("unavailable: "), got)
            self.assertNotEqual(UNAVAILABLE, got[0])
            self.assertEqual(STANDING, got[1])


class UsageTest(unittest.TestCase):
    def refused(self, option: str, *arguments: str) -> None:
        result = raw(*arguments)
        self.assertEqual((2, ""), (result.returncode, result.stdout), arguments)
        self.assertEqual(1, len(result.stderr.strip().splitlines()), result.stderr)
        self.assertIn(option, result.stderr.split(" - usage:")[0])

    def good(self, **changes: str) -> list[str]:
        merged = {"--decide": "provisional", "--ask": "approval", "--when": "2026-10-07T21:17:49Z", "--number": "D12",
                  **changes}
        return ["status", *[word for pair in merged.items() for word in pair]]

    def test_e11_a_bad_value_or_a_bad_line_or_a_repeated_option_is_exit_two_naming_the_option(self) -> None:
        self.refused("--decide", *self.good(**{"--decide": "sometimes"}))
        self.refused("--ask", *self.good(**{"--ask": "maybe"}))
        self.refused("--when", *self.good(**{"--when": "yesterday"}))
        self.refused("--number", *self.good(**{"--number": "12"}))
        self.refused("--reversibility", *self.good(), "--reversibility", EASY_LINE.replace("rules 1", "rules 9"))
        self.refused("--number", *self.good(), "--number", "D13")
        self.refused("--when", *self.good()[:-4], "--number", "D12")
        self.refused("--bogus", *self.good(), "--bogus", "x")


if __name__ == "__main__":
    unittest.main()
