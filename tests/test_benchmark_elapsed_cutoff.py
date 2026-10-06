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
    entry,
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

    def accepted(self, *stages: dict) -> None:
        repo = self.repo
        write(repo, SPLIT, graph([("S2", [])]))
        commit(repo, stamp(1), "split", SPLIT)
        path = record(repo, "S2", *stages)
        write(repo, REGISTER, register(["S2"]))
        commit(repo, stamp(2), "S2 done", REGISTER, path)

    def test_e4_a_bracket_that_ended_before_it_started_makes_stage_time_unknown_not_negative(self) -> None:
        """A7: an implement bracket 12:00 to 10:00 and a half-hour converge: no `-2h30m`."""
        self.accepted(entry("implement", stamp(1, "12:00:00"), stamp(1, "10:00:00")),
                      entry("converge", stamp(1, "13:00:00"), stamp(1, "13:30:00")))
        found = summaries(self.repo)["S2"]
        self.assertIn("implement", found["stage_seconds"]["unknown"])
        self.assertIn("before it started", found["stage_seconds"]["unknown"])
        self.assertIn("unknown", found["entries"][0]["stage_seconds"])
        self.assertEqual(found["entries"][1]["stage_seconds"], 1800)
        out = bench(self.repo).stdout
        self.assertIn("stage time unknown", out)
        self.assertNotIn("stage time -", out)
        self.assertEqual(0, bench(self.repo, "overview", FEATURE).returncode)

    def test_e5_an_accepted_demo_with_a_null_end_is_not_a_demo_moment_and_no_traceback(self) -> None:
        """A8: `"ended": null` on the accepted demo."""
        demo = entry("demo", stamp(1, "12:00:00"), stamp(1, "12:30:00"), outcome="accepted", driver="human")
        demo["ended"] = None
        self.accepted(entry("implement", stamp(1, "10:00:00"), stamp(1, "11:00:00")), demo)
        done = bench(self.repo, "--json")
        self.assertEqual((0, ""), (done.returncode, done.stderr))
        self.assertNotIn("demo_accepted", summaries(self.repo)["S2"]["moments"])


if __name__ == "__main__":
    unittest.main()
