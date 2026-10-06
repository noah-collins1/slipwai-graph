"""T040-T042: the page and the plain report say what the waiting table's columns mean, which token figure is the
cost, and why every `unknown` cell is unknown."""
from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path

from elapsed_fixture import FEATURE, bench, commit, entry, graph, project, record, register, stamp, write

sys.dont_write_bytecode = True

SPLIT = f"specs/{FEATURE}/story-split.md"
REGISTER = f"specs/{FEATURE}/slices/README.md"


class PageTest(unittest.TestCase):
    def setUp(self) -> None:
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.repo = repo = project(Path(self.scratch.name))
        write(repo, SPLIT, graph([("S1", []), ("S2", [])]))
        commit(repo, stamp(1), "split", SPLIT)
        done = record(repo, "S1", entry("implement", stamp(2, "09:00:00"), stamp(2, "10:00:00")))
        opened = entry("implement", stamp(2, "09:00:00"), stamp(2, "10:00:00"))
        del opened["ended"], opened["seconds"]
        record(repo, "S2", opened)
        write(repo, REGISTER, register(["S1"]))
        commit(repo, stamp(3), "S1 done", REGISTER, done)
        write(repo, "specs/cruise-log.jsonl", "not json\n")

    def page(self) -> str:
        bench(self.repo, "overview", FEATURE)
        return (self.repo / f"specs/{FEATURE}/benchmark.md").read_text(encoding="utf-8")

    def test_e1_the_waiting_table_carries_its_key_in_the_report_and_the_page(self) -> None:
        for text in (bench(self.repo).stdout, self.page()):
            key = next(line for line in text.splitlines() if "`--json` names where each was read from" in line)
            for word in ("worker", "dependency", "review", "integration", "unattributed", "cost"):
                self.assertIn(f"{word} = ", key)
            self.assertLess(text.index("integration"), text.index(key))

    def test_e2_the_page_says_which_token_figure_is_the_cost(self) -> None:
        for text in (bench(self.repo).stdout, self.page()):
            self.assertIn("cache creation tokens as recorded", text)
            self.assertIn("cost is attributed by spawn chain", text)

    def test_e3_every_unknown_cell_carries_its_reason_or_points_at_the_note_that_does(self) -> None:
        text = bench(self.repo).stdout
        self.assertIn("S1: review, worker and unattributed unknown", text)
        self.assertIn("line 1", text)
        self.assertIn("S2: cost unknown — no bracket ended", text)
        for line in text.splitlines():
            if re.match(r"^\s+S[12]\s{2,}", line) and "unknown" in line:
                self.assertNotRegex(line, r"unknown(?! \(see notes\))")


if __name__ == "__main__":
    unittest.main()
