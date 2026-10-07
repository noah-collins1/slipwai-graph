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


def measures(path: Path = SCRIPTS / "agents/measures.py") -> Any:
    spec = importlib.util.spec_from_file_location(f"measures_under_guard_{path.parent.name}", path)
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

    def test_e3_measures_reads_the_line_as_it_did_at_the_plan(self) -> None:
        """`measures.py` may change (T023 skips fenced lines), but not its spelling of the line nor the tier and the
        escalation it reads from every line shape the verb writes: the reader at `063c187` and now agree."""
        text = subprocess.run(["git", "show", "063c187:assets/toolkit/scripts/agents/measures.py"], cwd=ROOT,
                              text=True, capture_output=True, check=True, encoding="utf-8").stdout
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "planned").mkdir()
            (Path(directory) / "planned/measures.py").write_text(text, encoding="utf-8")
            before, now = measures(Path(directory) / "planned/measures.py"), measures()
        self.assertEqual(before.SPELLING, now.SPELLING)
        kinds = [(facts(**change), extra) for change in ({}, {"behind_flag": "no"}, {"contract": "yes"})
                 for extra in ((), ("--raise", "guarded"), ("--raise", "hard")) if (change, extra) != (
                     {"contract": "yes"}, ("--raise", "guarded"))]  # that one would lower a tier: usage, not a line
        lines = [line for line in self.lines(kinds) if line]
        lines += [line.replace(" → ", arrow) for arrow in ("->", " -> ") for line in lines]
        log = "# Decisions\n\n" + "".join(entry(number, line) for number, line in enumerate(lines, 1))
        read = [[(item["tier"], item["escalated"]) for item in reader.decision_entries(log)]
                for reader in (before, now)]
        self.assertEqual(read[0], read[1])
        self.assertEqual(len(lines), len(read[1]))


V2 = '''
FACT_LISTS = {1: FACTS, 2: FACTS}


def rules_v2(facts, bound):
    tier, fired = rules_v1(facts, bound)
    if facts.get("behind_flag") == "no":
        return "hard", [*fired, "X1 behind_flag=no"]
    return tier, fired


RULES = {1: rules_v1, 2: rules_v2}
'''
MARKER = "RULES: dict[int, Callable[[dict[str, str], str], tuple[str, list[str]]]] = {1: rules_v1}\n"
LISTS = "FACT_LISTS: dict[int, dict[str, tuple[str, ...]]] = {1: FACTS}\n"
V2_FACTS = '''
FACT_LISTS = {1: FACTS, 2: {**FACTS, "pii": YES_NO}}


def rules_v2(facts, bound):
    tier, fired = rules_v1({k: v for k, v in facts.items() if k != "pii"}, bound)
    if facts.get("pii", "missing") != "no":
        return "hard", [*fired, f"X2 pii={facts.get('pii', 'missing')}"]
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
    def gate(self, text: str, fake: bool, v2: str = V2) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory:
            repo = scratch(directory, text, listed=("scripts/check-decisions.py",))
            if fake:
                source = (SCRIPTS / "reversibility.py").read_text(encoding="utf-8")
                assert MARKER in source and LISTS in source
                (repo / "scripts/reversibility.py").write_text(
                    source.replace(LISTS, "").replace(MARKER, v2), encoding="utf-8")
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

    def test_e3_a_fact_added_in_version_2_belongs_to_version_2_alone(self) -> None:
        """M1: each version has its own fact list; the parser and rule U1 read the list of the version a line names."""
        base = " ".join(f"{key}={value}" for key, value in EASY.items())
        old = f"- **Reversibility:** easy · rules 1 · {base}"
        new = f"- **Reversibility:** easy · rules 2 · {base} pii=no"
        bare = f"- **Reversibility:** easy · rules 2 · {base}"
        for text, code in ((old, 0), (new, 0), (f"{old} pii=no", 1), (bare, 1)):
            with self.subTest(text=text):
                result = self.gate(entry(1, text), True, V2_FACTS)
                self.assertEqual(code, result.returncode, result.stdout + result.stderr)
        refused = self.gate(entry(1, f"{old} pii=no"), True, V2_FACTS).stderr
        self.assertIn("pii", refused)
        self.assertIn("not a fact", refused)
        self.assertIn("pii=missing", self.gate(entry(1, bare), True, V2_FACTS).stderr)

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

    def test_e5_a_log_with_neither_label_never_loads_the_module(self) -> None:
        """A fake `reversibility.py` that fails on load: a log with neither label passes as before, and one with the
        label reaches it, so the guard is what kept it unloaded."""
        for text, code in ((entry(1) + "\n" + entry(2), 0), (entry(1, line("guarded", 1)), 1)):
            with self.subTest(code=code), tempfile.TemporaryDirectory() as directory:
                repo = scratch(directory, text, listed=("scripts/check-decisions.py",))
                (repo / "scripts/reversibility.py").write_text("raise SystemExit('loaded')\n", encoding="utf-8")
                result = gate(repo)
                self.assertEqual(code, result.returncode, result.stdout + result.stderr)
                self.assertEqual(code == 1, "loaded" in result.stderr, result.stderr)

    def test_e6_in_an_adopted_layout_the_note_names_the_verb_where_it_is(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = scratch(directory, entry(1, line("guarded", 1)) + "\n" + entry(2), origin="adopted",
                           delivery="delivery", listed=("delivery/.written",))  # an empty list is no list
            (repo / "delivery").mkdir(exist_ok=True)
            (repo / "scripts").rename(repo / "delivery/scripts")
            result = subprocess.run(["python3", "-B", "delivery/scripts/check-decisions.py"], cwd=repo, text=True,
                                    capture_output=True)
        self.assertEqual((0, ""), (result.returncode, result.stderr))
        self.assertIn("score it with python3 delivery/scripts/reversibility.py", result.stdout)


if __name__ == "__main__":
    unittest.main()
