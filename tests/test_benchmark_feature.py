"""R6: a feature's elapsed time is not its stage time — the three figures sit under three names."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from elapsed_fixture import FEATURE, bench, commit, entry, graph, project, record, register, stamp, summaries, write

sys.dont_write_bytecode = True

SPLIT = f"specs/{FEATURE}/story-split.md"
REGISTER = f"specs/{FEATURE}/slices/README.md"


class FeatureFiguresTest(unittest.TestCase):
    def setUp(self) -> None:
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.repo = project(Path(self.scratch.name))

    def overlapping(self, done: int) -> None:
        """S1-S3 ready together on day 1, each bracketing the same 34 hours of implement; `done` of them have a row
        (S1 at 21:00, S2 at 22:00, S3 at 23:00 on day 2). The feature's own record holds one hour of `split`."""
        repo = self.repo
        write(repo, SPLIT, graph([("S1", []), ("S2", []), ("S3", [])]))
        paths = [SPLIT]
        for ident in ("S1", "S2", "S3"):
            paths.append(record(repo, ident, entry("implement", stamp(1, "10:00:00"), stamp(2, "20:00:00"))))
        paths.append(f"specs/{FEATURE}/benchmark.json")
        stages = [entry("split", stamp(1, "09:00:00"), stamp(1, "10:00:00"))]
        write(repo, paths[-1], json.dumps({"feature": FEATURE, "slice": None, "stages": stages}))
        commit(repo, stamp(1), "split", *paths)
        for index, ident in enumerate(("S1", "S2", "S3")[:done]):
            write(repo, REGISTER, register(["S1", "S2", "S3"][:index + 1]))
            commit(repo, stamp(2, f"{21 + index}:00:00"), f"{ident} done", REGISTER)

    def test_e1_three_overlapping_slices_elapsed_is_less_than_their_stage_time(self) -> None:
        self.overlapping(3)
        out = bench(self.repo).stdout
        self.assertIn("f — 3 slice(s) recorded, stage time 103h00m in all; elapsed 38h00m; "
                      "time with any slice in flight 34h00m", out)
        figures = summaries(self.repo)["(feature)"]["feature_figures"]
        self.assertEqual(figures, {"elapsed": 38 * 3600, "stage_seconds": 103 * 3600,
                                   "in_flight_seconds": 34 * 3600})
        self.assertLess(figures["elapsed"], figures["stage_seconds"])
        self.assertEqual(bench(self.repo, "overview", FEATURE).returncode, 0)
        page = (self.repo / f"specs/{FEATURE}/benchmark.md").read_text(encoding="utf-8")
        self.assertIn("3 slice(s) recorded, stage time 103h00m in all; elapsed 38h00m; "
                      "time with any slice in flight 34h00m.", page)

    def test_e2_with_one_slice_open_elapsed_is_open_and_the_other_two_figures_stand(self) -> None:
        self.overlapping(2)
        out = bench(self.repo).stdout
        self.assertIn(f"stage time 103h00m in all; elapsed open since {stamp(1)}; "
                      "time with any slice in flight 34h00m", out)
        figures = summaries(self.repo)["(feature)"]["feature_figures"]
        self.assertEqual(figures["elapsed"], {"unknown": f"open since {stamp(1)}"})
        self.assertEqual((figures["stage_seconds"], figures["in_flight_seconds"]), (103 * 3600, 34 * 3600))


if __name__ == "__main__":
    unittest.main()
