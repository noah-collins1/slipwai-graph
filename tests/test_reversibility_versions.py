"""R9 (AC-S26-13): S39's reader reads the verb's lines as computed. Guards: they pass when written.

`measures.py` is loaded by path with bytecode off and is not changed; the verb runs as a subprocess.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from collections.abc import Sequence
from typing import Any

from reversibility_fixture import ROOT, SCRIPTS, entry, facts, score, scratch

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


if __name__ == "__main__":
    unittest.main()
