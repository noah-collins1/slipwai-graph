"""What counts as one `Scope:` statement, and which ids meet (D63, AC-S02-81 to -83; adversary C1, C2, C3, C7, C8).

The filter never drops what it cannot place. So ids meet on their head (the letters, case set aside, and the number,
read as a number) whatever the slug; and a `Scope:` the checker cannot read as `global` alone or a list of single
ASCII ids, or an entry that says its scope twice, is refused by the gate and carried as global by the
verb (a status said twice is only noted by the gate, D65, and carried the same), so no spelling can make a
decision that binds a slice vanish from it.
"""
from __future__ import annotations

import subprocess
import tempfile
import unittest

from test_decisions_scope import SLICE, entry, printed, run, scratch

TEST_SELECTION: dict[str, object] = {
    "reads": ["assets/toolkit/scripts/check-decisions.py", "assets/toolkit/scripts/check-styles.py"],
}

Pair = tuple["subprocess.CompletedProcess[str]", "subprocess.CompletedProcess[str]"]


def gate_and_verb(log: str, ident: str = SLICE) -> Pair:
    with tempfile.TemporaryDirectory() as directory:
        repo = scratch(directory, log)
        return run(repo), run(repo, "--scope", ident)


class IdsMeetOnTheirHeadTest(unittest.TestCase):
    def verb(self, log: str, ident: str = SLICE) -> Pair:
        return gate_and_verb(log, ident)

    def test_e81_a_shortened_slug_another_padding_or_another_case_meets_the_slice(self) -> None:
        for value in ("S02-runner", "S2", "S002", "s02-runner-bookkeeping", "s2", "S02-some-other-slug"):
            gate, verb = self.verb(entry(1, value) + "\n" + entry(2, "S11-render-once"))
            self.assertEqual(0, gate.returncode, (value, gate.stderr))
            self.assertEqual(["D1"], printed(verb), value)
            self.assertIn("1 in scope", verb.stdout.splitlines()[-1], value)

    def test_e81_the_wanted_side_meets_on_its_head_too(self) -> None:
        log = entry(1, SLICE) + "\n" + entry(2, "S12-model-sidecar")
        for wanted in ("S02", "S2", "S02-runner", "S0002-anything"):
            self.assertEqual(["D1"], printed(self.verb(log, wanted)[1]), wanted)

    def test_e81_s1_does_not_meet_s12_nor_s10_and_another_letter_does_not_meet(self) -> None:
        log = "\n".join([entry(1, "S12-model-sidecar"), entry(2, "S10"), entry(3, "T02-runner-bookkeeping"),
                         entry(4, "SS02")])
        self.assertEqual([], printed(self.verb(log, "S1")[1]))
        self.assertEqual([], printed(self.verb(log, SLICE)[1]))
        self.assertEqual(["D1"], printed(self.verb(log, "S12")[1]))

    def test_e81_a_number_too_long_to_read_as_an_integer_is_compared_as_a_number_all_the_same(self) -> None:
        log = entry(1, "S" + "0" * 5000 + "2-x") + "\n" + entry(2, "S" + "1" * 5000)
        gate, verb = self.verb(log)
        self.assertEqual(0, gate.returncode, gate.stderr)
        self.assertEqual(["D1"], printed(verb))


class ScopeThatIsNotOneStatementTest(unittest.TestCase):
    def refused_and_carried(self, value: str) -> None:
        log = entry(1, "S11-render-once") + "\n" + entry(2, value) + "\n" + entry(3, "S11-render-once")
        for ident in (SLICE, "S11-render-once", "S77-anything"):
            gate, verb = gate_and_verb(log, ident)
            self.assertEqual(1, gate.returncode, (value, gate.stdout))
            lines = [line for line in gate.stderr.splitlines() if "Scope" in line]
            self.assertEqual(1, len(lines), gate.stderr)
            self.assertIn("D2", lines[0])
            self.assertIn("`global` alone or slice ids", lines[0])
            self.assertEqual(0, verb.returncode, verb.stderr)
            self.assertIn("D2", printed(verb), (value, ident))

    def test_e82_a_range_is_refused_by_the_gate_and_carried_by_the_verb(self) -> None:
        self.refused_and_carried("S01-S03")

    def test_e82_two_ids_joined_by_a_full_stop_or_a_hyphen_are_refused_and_carried(self) -> None:
        self.refused_and_carried(f"S05-other.{SLICE}")
        self.refused_and_carried("s01-S03")

    def test_e82_a_digit_that_is_not_ascii_is_refused_and_carried(self) -> None:
        for value in ("S０２", "S٠٢", "S02, S１"):
            self.refused_and_carried(value)

    def test_e82_hold_a_slug_with_a_digit_in_it_is_one_id_and_passes(self) -> None:
        gate, verb = gate_and_verb(entry(1, "S10-oauth2-login, S14-v2") + "\n" + entry(2, "S14-other.v2"), "S14")
        self.assertEqual(0, gate.returncode, gate.stderr)
        self.assertEqual(["D1", "D2"], printed(verb))


class AnEntryThatSaysAFieldTwiceTest(unittest.TestCase):
    def twice(self, label: str, first: str, second: str) -> str:
        text = entry(2, "global")
        marker = f"- **{label}:** {'global' if label == 'Scope' else 'standing'}\n"
        assert marker in text, marker
        return text.replace(marker, f"- **{label}:** {first}\n- **{label}:** {second}\n")

    def check(self, label: str, first: str, second: str, ident: str = SLICE) -> None:
        log = entry(1, "S11-render-once") + "\n" + self.twice(label, first, second)
        gate, verb = gate_and_verb(log, ident)
        self.assertEqual(1, gate.returncode, gate.stdout)
        lines = [line for line in gate.stderr.splitlines() if f"`{label}:`" in line]
        self.assertEqual(1, len(lines), gate.stderr)
        self.assertIn("D2", lines[0])
        self.assertIn(f"more than one `{label}:` line", lines[0])
        self.assertEqual(0, verb.returncode, verb.stderr)
        self.assertEqual(["D2"], printed(verb), (label, first, second))

    def test_e83_two_scope_lines_are_refused_and_carried_whichever_says_what(self) -> None:
        self.check("Scope", "S11-render-once", "global")
        self.check("Scope", "global", "S11-render-once")
        self.check("Scope", "S11-render-once", "S12-model-sidecar", "S12")

    def test_e83_two_status_lines_are_a_note_for_the_gate_and_carried_by_the_verb_either_way_round(self) -> None:
        for first, second in (("overridden by D1", "standing"), ("standing", "overridden by D1")):
            log = entry(1, "S11-render-once") + "\n" + self.twice("Status", first, second)
            gate, verb = gate_and_verb(log)
            self.assertEqual((0, ""), (gate.returncode, gate.stderr), (first, gate.stdout))
            notes = [line for line in gate.stdout.splitlines() if "note:" in line]
            self.assertEqual(1, len(notes), gate.stdout)
            self.assertIn("D2", notes[0])
            self.assertIn("`Status:`", notes[0])
            self.assertEqual(0, verb.returncode, verb.stderr)
            self.assertEqual(["D2"], printed(verb), (first, second))

    def test_e83_a_quoted_line_inside_a_fence_counts_as_a_second_line_at_the_start_of_a_line(self) -> None:
        text = entry(1, "global").replace("- **Status:**", "```\n- **Status:** overridden by D9\n```\n- **Status:**")
        gate, verb = gate_and_verb(text)
        self.assertEqual(0, gate.returncode, gate.stderr)
        self.assertIn("note:", gate.stdout)
        self.assertEqual(["D1"], printed(verb))

    def test_e83_hold_a_scope_or_status_label_said_mid_line_is_not_a_second_line(self) -> None:
        text = entry(1, "global").replace("- **Why:** because", "- **Why:** because - **Scope:** S11 - **Status:** x")
        gate, verb = gate_and_verb(text)
        self.assertEqual(0, gate.returncode, gate.stderr)
        self.assertEqual(["D1"], printed(verb))

    def test_e83_a_separator_other_than_a_line_feed_does_not_make_a_second_field(self) -> None:
        for separator in (" ", "\x0c", "\u0085", "\x1d"):
            text = entry(1, SLICE).replace("- **Why:** because", f"- **Why:** before{separator}- **Scope:** S11")
            gate, verb = gate_and_verb(text)
            self.assertEqual(0, gate.returncode, (separator, gate.stderr))
            self.assertEqual(["D1"], printed(verb), repr(separator))
            self.assertIn(f"before{separator}- **Scope:**", verb.stdout, repr(separator))


if __name__ == "__main__":
    unittest.main()
