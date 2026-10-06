"""T035 (D166): *stage time* is one figure wherever it is printed — a cut-off entry ends at its last transcript line —
and the recorded seconds stay in `--json`."""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from elapsed_fixture import (
    FEATURE,
    Session,
    bench,
    commit,
    graph,
    project,
    record,
    register,
    stamp,
    summaries,
    write,
)

sys.dont_write_bytecode = True

SPLIT = f"specs/{FEATURE}/story-split.md"
REGISTER = f"specs/{FEATURE}/slices/README.md"


class OneFigureTest(unittest.TestCase):
    def setUp(self) -> None:
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.repo = project(Path(self.scratch.name))

    def lay(self, cut_off: bool = True, transcript: bool = True) -> None:
        repo = self.repo
        write(repo, SPLIT, graph([("S2", [])]))
        commit(repo, stamp(1), "split", SPLIT)
        said = Session(repo)
        cursor = said.open(None, "implement", f"specs/{FEATURE}/slices/S2/benchmark.json")
        said.say(None, "r1", 100, stamp(1, "10:30:00"))
        item = said.entry("implement", stamp(1, "10:00:00"), stamp(1, "13:30:00"), cursor)
        if cut_off:
            item["cut_off"] = "iteration 3 ended with the entry open"
        path = record(repo, "S2", item)
        write(repo, REGISTER, register(["S2"]))
        commit(repo, stamp(2), "S2 done", REGISTER, path)
        if not transcript:
            shutil.rmtree(repo / ".home/.claude")

    def test_e1_the_column_the_stage_row_the_heading_and_the_feature_line_say_the_same(self) -> None:
        self.lay()
        out = bench(self.repo).stdout
        row = next(line for line in out.splitlines() if line.lstrip().startswith("S2 "))
        self.assertEqual(row.split()[2], "30m00s", row)
        self.assertIn("stage time 30m00s in all", out)
        bench(self.repo, "overview", FEATURE)
        page = (self.repo / f"specs/{FEATURE}/benchmark.md").read_text(encoding="utf-8")
        self.assertIn("### S2 — stage time 30m00s", page)
        stage = next(line for line in page.splitlines() if line.startswith("| implement"))
        self.assertIn("| 30m00s |", stage)
        self.assertIn("not at the recorded end", page)
        self.assertIn("recorded_seconds", page)

    def test_e2_json_keeps_the_recorded_seconds_beside_the_trimmed_ones(self) -> None:
        self.lay()
        found = summaries(self.repo)["S2"]["entries"][0]
        self.assertEqual((found["stage_seconds"], found["recorded_seconds"]), (1800, 12600))

    def test_e3_nothing_else_moves_where_there_is_no_cut_off_or_no_transcript(self) -> None:
        for kwargs in ({"cut_off": False}, {"transcript": False}):
            with self.subTest(**kwargs):
                self.setUp()
                self.lay(**kwargs)
                found = summaries(self.repo)["S2"]
                self.assertEqual(found["entries"][0]["stage_seconds"], 12600)
                self.assertEqual(found["entries"][0]["recorded_seconds"], 12600)
                row = next(line for line in bench(self.repo).stdout.splitlines() if line.lstrip().startswith("S2 "))
                self.assertEqual(row.split()[2], "3h30m", row)


if __name__ == "__main__":
    unittest.main()
