"""R1 and R3: when a slice was ready and accepted, read from git; what its stage time and worked time are."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from elapsed_fixture import (
    FEATURE,
    bench,
    commit,
    entry,
    graph,
    merge,
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
MODEL = "docs/event-model/model.yaml"


class ElapsedTest(unittest.TestCase):
    def setUp(self) -> None:
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.repo = project(Path(self.scratch.name))

    def standard(self, own_row: bool = True) -> dict[str, str]:
        """Split on day 1 naming S1 and S2 (S2 after S1), S1's row on day 2, S2's own row on day 4."""
        repo = self.repo
        write(repo, SPLIT, graph([("S1", []), ("S2", ["S1"])]))
        shas = {"split": commit(repo, stamp(1), "split", SPLIT)}
        write(repo, REGISTER, register(["S1"]))
        shas["dep"] = commit(repo, stamp(2), "S1 done", REGISTER)
        path = record(repo, "S2", entry("implement", stamp(3, "10:00:00"), stamp(3, "11:00:00")))
        if own_row:
            write(repo, REGISTER, register(["S1", "S2"]))
            shas["own"] = commit(repo, stamp(4), "S2 done", REGISTER, path)
        return shas

    def test_e1_elapsed_runs_from_the_dependencys_row_to_the_slices_own(self) -> None:
        shas = self.standard()
        found = summaries(self.repo)["S2"]
        self.assertEqual(found.get("elapsed"), 2 * 86400)
        self.assertEqual(found["moments"]["ready"], stamp(2))
        self.assertEqual(found["moments"]["accepted"], stamp(4))
        self.assertIn(shas["dep"], found["read_from"]["ready"])
        self.assertIn(shas["own"], found["read_from"]["accepted"])

    def test_e2_the_merge_and_the_accepted_demo_are_shown_inside_the_interval(self) -> None:
        self.standard(own_row=False)
        repo = self.repo
        demo = entry("demo", stamp(3, "12:00:00"), stamp(3, "12:30:00"), outcome="accepted", driver="human")
        path = record(repo, "S2", entry("implement", stamp(3, "10:00:00"), stamp(3, "11:00:00")), demo)
        commit(repo, stamp(3, "13:00:00"), "records", path)
        merge(repo, stamp(3, "14:00:00"), "S2")
        write(repo, REGISTER, register(["S1", "S2"]))
        commit(repo, stamp(4), "S2 done", REGISTER)
        moments = summaries(repo)["S2"]["moments"]
        self.assertEqual((moments["demo_accepted"], moments["merged"]), (stamp(3, "12:30:00"), stamp(3, "14:00:00")))
        self.assertLess(moments["ready"], moments["demo_accepted"])
        self.assertLess(moments["merged"], moments["accepted"])
        bench(repo, "overview", FEATURE)
        page = (repo / f"specs/{FEATURE}/benchmark.md").read_text(encoding="utf-8")
        self.assertIn(f"merged {stamp(3, '14:00:00')}", page)
        self.assertIn(f"demo accepted {stamp(3, '12:30:00')}", page)
        self.assertIn("48h00m", page)

    def test_e2b_a_merge_of_s10_is_not_a_merge_of_s1(self) -> None:
        self.standard()
        record(self.repo, "S1", entry("implement", stamp(1, "10:00:00"), stamp(1, "11:00:00")))
        merge(self.repo, stamp(3, "14:00:00"), "S10-other")
        self.assertNotIn("merged", summaries(self.repo)["S1"]["moments"])

    def test_e3_a_slice_with_no_row_is_open_since_its_ready_moment(self) -> None:
        self.standard(own_row=False)
        found = summaries(self.repo)["S2"]
        self.assertEqual(found.get("elapsed"), {"unknown": f"open since {stamp(2)}"})
        self.assertEqual(found["moments"]["accepted"], {"unknown": f"open since {stamp(2)}"})
        self.assertIn(f"open since {stamp(2)}", bench(self.repo, "overview", FEATURE).stdout + (
            self.repo / f"specs/{FEATURE}/benchmark.md").read_text(encoding="utf-8"))

    def test_e4_a_dependency_with_no_done_mark_means_not_ready(self) -> None:
        write(self.repo, SPLIT, graph([("S1", []), ("S2", ["S1"])]))
        commit(self.repo, stamp(1), "split", SPLIT)
        record(self.repo, "S2", entry("implement", stamp(3), stamp(3, "10:00:00")))
        self.assertEqual(summaries(self.repo)["S2"].get("elapsed"), {"unknown": "not ready: S1 is not done"})

    def test_e5_a_slice_in_no_split_and_no_model_is_unknown_and_says_where_it_looked(self) -> None:
        write(self.repo, SPLIT, graph([("S1", [])]))
        commit(self.repo, stamp(1), "split", SPLIT)
        record(self.repo, "S9", entry("implement", stamp(3), stamp(3, "10:00:00")))
        reason = summaries(self.repo)["S9"]["elapsed"]["unknown"]
        self.assertIn("story-split.md", reason)
        self.assertIn("model.yaml", reason)

    def test_e6_the_event_profile_reads_status_implemented_from_the_model(self) -> None:
        repo = self.repo
        planned = "slices:\n  - id: S1\n    status: planned\n  - id: S2\n    depends_on: [S1]\n    status: planned\n"
        write(repo, MODEL, planned)
        commit(repo, stamp(1), "model", MODEL)
        write(repo, MODEL, planned.replace("id: S1\n    status: planned", "id: S1\n    status: implemented"))
        dep = commit(repo, stamp(2), "S1 implemented", MODEL)
        path = record(repo, "S2", entry("implement", stamp(3), stamp(3, "10:00:00")))
        write(repo, MODEL, planned.replace("planned", "implemented"))
        own = commit(repo, stamp(4), "S2 implemented", MODEL, path)
        found = summaries(repo)["S2"]
        self.assertEqual(found.get("elapsed"), 2 * 86400)
        self.assertIn(dep, found["read_from"]["ready"])
        self.assertIn(own, found["read_from"]["accepted"])

    def test_outside_a_git_repository_the_moments_say_git_could_not_be_read(self) -> None:
        self.standard()
        (self.repo / ".git").rename(self.repo / ".git-gone")
        found = summaries(self.repo)["S2"]
        self.assertIn("git could not be read", found["elapsed"]["unknown"])
        self.assertTrue(json.dumps(found))


if __name__ == "__main__":
    unittest.main()
