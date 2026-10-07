"""R9 (AC-S26-13): S39's reader reads the verb's lines as computed. Guards: they pass when written.

`measures.py` is loaded by path with bytecode off and is not changed; the verb runs as a subprocess.

R6 (AC-S26-11): a line is re-derived under the rules version it names. e1 runs the gate beside a fake written here, a
copy of `reversibility.py` with a version 2; e2 freezes version 1 as a digest (a guard: it passes when written).
"""
from __future__ import annotations

import hashlib
import importlib.util
import itertools
import shutil
import subprocess
import sys
import tempfile
import unittest
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from reversibility_fixture import EASY, ROOT, SCRIPTS, entry, facts, gate, score, scratch
from test_decisions_scope_gate import released_checker

sys.dont_write_bytecode = True


def measures() -> Any:
    spec = importlib.util.spec_from_file_location("measures_under_guard", SCRIPTS / "agents/measures.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReaderTest(unittest.TestCase):
    def lines(self, kinds: Sequence[tuple[list[str], tuple[str, ...]]]) -> list[str]:
        out = []
        with tempfile.TemporaryDirectory() as directory:
            repo = scratch(directory, names=("reversibility.py",), listed=("init",))
            for arguments, extra in kinds:
                result = score(repo, "--scope", "S1", *arguments, *extra)
                self.assertEqual(result.returncode, 0, result.stderr)
                out.append(result.stdout.strip())
        return out

    def test_e1_twenty_entries_give_tiers_and_the_share_as_computed(self) -> None:
        kinds = [(facts(), ())] * 12 + [(facts(), ("--raise", "hard"))] * 4 + [(facts(behind_flag="no"), ())] * 4
        lines = self.lines(kinds)
        text = "# Decisions\n\n" + "".join(entry(number, line) for number, line in enumerate(lines, 1))
        module = measures()
        found = module.decision_entries(text)
        self.assertEqual([item["tier"] for item in found], ["easy"] * 16 + ["guarded"] * 4)
        self.assertEqual(sum(item["escalated"] for item in found), 4)
        share = module.decision_health(text, [])["escalation_share"]
        self.assertEqual((share["numerator"], share["denominator"], share["percent"]), (4, 20, 20))

    def test_e2_easy_to_guarded_is_not_an_escalation_to_hard(self) -> None:
        (line,) = self.lines([(facts(), ("--raise", "guarded"))])
        found = measures().decision_entries(entry(1, line))
        self.assertEqual((found[0]["tier"], found[0]["escalated"]), ("easy", False))

    def test_e3_measures_is_unchanged_since_the_plan(self) -> None:
        result = subprocess.run(["git", "diff", "063c187", "--", "assets/toolkit/scripts/agents/measures.py"],
                                cwd=ROOT, text=True, capture_output=True)
        self.assertEqual((result.returncode, result.stdout), (0, ""))


V2 = '''
def rules_v2(facts, bound):
    tier, fired = rules_v1(facts, bound)
    if facts.get("behind_flag") == "no":
        return "hard", [*fired, "X1 behind_flag=no"]
    return tier, fired


RULES = {1: rules_v1, 2: rules_v2}
'''
VERSION_1_DIGEST = "e42e1582aeaf61cae82bccd83b7effef7b650c8228d31b4e28846ad061b27f84"


def loaded(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("reversibility_under_guard", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def line(tier: str, rules: int) -> str:
    written = " ".join(f"{key}={value}" for key, value in EASY.items() if key != "behind_flag")
    return f"- **Reversibility:** {tier} · rules {rules} · {written} behind_flag=no"


class OldLinesUnderNewerRulesTest(unittest.TestCase):
    def gate(self, text: str, fake: bool) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory:
            repo = scratch(directory, text, listed=("scripts/check-decisions.py",))
            if fake:
                source = (SCRIPTS / "reversibility.py").read_text(encoding="utf-8")
                marker = "RULES: dict[int, Callable[[dict[str, str], str], tuple[str, list[str]]]] = {1: rules_v1}\n"
                assert marker in source
                (repo / "scripts/reversibility.py").write_text(source.replace(marker, V2), encoding="utf-8")
            return gate(repo)

    def test_e1_a_version_1_line_passes_beside_a_version_2_and_a_version_2_line_is_held_to_it(self) -> None:
        old, new = entry(1, line("guarded", 1)), entry(1, line("guarded", 2))
        self.assertEqual(0, self.gate(old, fake=False).returncode)
        result = self.gate(old, fake=True)
        self.assertEqual((0, ""), (result.returncode, result.stderr))
        self.assertEqual(0, self.gate(entry(1, line("hard", 2)), fake=True).returncode)
        refused = self.gate(new, fake=True)
        self.assertEqual(1, refused.returncode, refused.stdout)
        self.assertIn("rules 2 derive hard", refused.stderr)
        self.assertIn("behind_flag=no", refused.stderr)
        self.assertIn("rules 2", self.gate(new, fake=False).stderr)  # the shipped gate does not know version 2

    def test_e2_version_1_is_frozen_as_a_digest_of_its_tier_over_every_fact_vector(self) -> None:
        """A guard: it passes when written. A shipped version is only ever added to, never edited."""
        module = loaded(SCRIPTS / "reversibility.py")
        digest = hashlib.sha256()
        for values in itertools.product(*module.FACTS.values()):
            for bound in ("one", "several", "global"):
                tier, _ = module.RULES[1](dict(zip(module.FACTS, values, strict=True)), bound)
                digest.update(f"{values} {bound} {tier}\n".encode())
        self.assertEqual(VERSION_1_DIGEST, digest.hexdigest())


NOTE = ("check-decisions: note: specs/f/decisions.md:{line}: D{number} has no `Reversibility:` line after an entry "
        "that has one; score it with python3 scripts/reversibility.py")


class MissingLineNoteTest(unittest.TestCase):
    """R5 (AC-S26-10; D176): an entry with no line after one that has it is noted, as `scope_notes` does; exit 0."""

    def gate(self, text: str, released: bool = False) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as other:
            repo = scratch(directory, text, listed=("scripts/check-decisions.py",))
            if released:
                shutil.copy(released_checker(other), repo / "scripts/check-decisions.py")
            return gate(repo)

    def test_e2_a_line_the_released_checker_passed_is_refused_now_the_one_log_shape_whose_answer_moves(self) -> None:
        """A guard. `- **Reversibility:** whatever` was passed by the released checker and is refused now: the label
        is new to this release, so D65's carve-out lets the gate refuse what only this release can produce."""
        log = entry(1, "- **Reversibility:** whatever")
        self.assertEqual(0, self.gate(log, released=True).returncode)
        self.assertEqual(1, self.gate(log).returncode)

    def test_e3_an_entry_without_the_line_after_one_with_it_is_noted_and_the_gate_passes(self) -> None:
        text = entry(1, line("guarded", 1)) + "\n" + entry(2)
        result = self.gate(text)
        self.assertEqual((0, ""), (result.returncode, result.stderr))
        notes = [row for row in result.stdout.splitlines() if "Reversibility" in row]
        heading = ("# Decisions\n\n" + text).splitlines().index("## D2 \u2014 Question 2") + 1
        self.assertEqual([NOTE.format(line=heading, number=2)], notes)

    def test_e4_an_entry_without_the_line_before_the_first_that_has_it_gets_no_note(self) -> None:
        result = self.gate(entry(1) + "\n" + entry(2, line("guarded", 1)))
        self.assertEqual((0, ""), (result.returncode, result.stderr))
        self.assertNotIn("has no `Reversibility:`", result.stdout)


if __name__ == "__main__":
    unittest.main()
