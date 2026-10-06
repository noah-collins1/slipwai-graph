"""R1 and R3: when a slice was ready and accepted, read from git; what its stage time and worked time are."""
from __future__ import annotations

import json
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


class BareIdTest(unittest.TestCase):
    """A slice id is read the same way in every table the ladder writes: backticked or bare (AC-S39-1, -2)."""

    def setUp(self) -> None:
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.repo = project(Path(self.scratch.name))

    def chain(self, style: str, bare_register: bool = False) -> None:
        """S1-a, S2-b after it: split on day 1, S1-a's row on day 3, S2-b's on day 5."""
        repo = self.repo
        write(repo, SPLIT, graph([("S1-a", []), ("S2-b", ["S1-a"])], style))
        commit(repo, stamp(1), "split", SPLIT)
        write(repo, REGISTER, register(["S1-a"], bare_register))
        commit(repo, stamp(3), "S1-a done", REGISTER)
        record(repo, "S2-b", entry("implement", stamp(4), stamp(4, "10:00:00")))
        write(repo, REGISTER, register(["S1-a", "S2-b"], bare_register))
        commit(repo, stamp(5), "S2-b done", REGISTER, f"specs/{FEATURE}/slices/S2-b/benchmark.json")

    def test_e1_a_bare_depends_on_is_a_dependency(self) -> None:
        self.chain("mixed")
        found = summaries(self.repo)["S2-b"]
        self.assertEqual((found["elapsed"], found["moments"]["ready"]), (2 * 86400, stamp(3)))

    def test_e2_a_bare_register_row_is_an_accepted_slice(self) -> None:
        self.chain("ticks", bare_register=True)
        record(self.repo, "S1-a", entry("implement", stamp(1, "10:00:00"), stamp(1, "11:00:00")))
        found = summaries(self.repo)
        self.assertEqual(found["S1-a"]["moments"]["accepted"], stamp(3))
        self.assertEqual(found["S2-b"]["elapsed"], 2 * 86400)

    def test_e3_a_split_naming_the_slice_bare_makes_it_ready(self) -> None:
        self.chain("bare")
        found = summaries(self.repo)["S2-b"]
        self.assertEqual((found["elapsed"], found["moments"]["ready"]), (2 * 86400, stamp(3)))

    def test_e4_bare_s1_beside_s10_each_reads_its_own_moments(self) -> None:
        repo = self.repo
        write(repo, SPLIT, graph([("S10", [])], "bare"))
        commit(repo, stamp(1), "S10 split", SPLIT)
        write(repo, SPLIT, graph([("S10", []), ("S1", [])], "bare"))
        commit(repo, stamp(2), "S1 split", SPLIT)
        write(repo, REGISTER, register(["S10"], True))
        commit(repo, stamp(3), "S10 done", REGISTER)
        write(repo, REGISTER, register(["S10", "S1"], True))
        commit(repo, stamp(5), "S1 done", REGISTER)
        record(repo, "S1", entry("implement", stamp(2), stamp(2, "10:00:00")))
        record(repo, "S10", entry("implement", stamp(1), stamp(1, "10:00:00")))
        found = summaries(repo)
        self.assertEqual((found["S1"]["moments"]["ready"], found["S1"]["moments"]["accepted"]), (stamp(2), stamp(5)))
        self.assertEqual((found["S10"]["moments"]["ready"], found["S10"]["moments"]["accepted"]),
                         (stamp(1), stamp(3)))


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


class StageTimeTest(unittest.TestCase):
    """R3: worked once, stage time renamed."""

    def setUp(self) -> None:
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.repo = project(Path(self.scratch.name))

    def accepted(self, *stages: dict) -> None:
        write(self.repo, SPLIT, graph([("S2", [])]))
        commit(self.repo, stamp(1), "split", SPLIT)
        path = record(self.repo, "S2", *stages)
        write(self.repo, REGISTER, register(["S2"]))
        commit(self.repo, stamp(2), "S2 done", REGISTER, path)

    def test_e1_a_skipper_nested_in_an_implement_adds_stage_time_but_not_worked_time(self) -> None:
        self.accepted(entry("implement", stamp(1, "10:00:00"), stamp(1, "11:00:00")),
                      entry("skipper", stamp(1, "10:10:00"), stamp(1, "10:20:00")))
        found = summaries(self.repo)["S2"]
        self.assertEqual((found.get("stage_seconds"), found["worked_seconds"]), (70 * 60, 60 * 60))

    def test_e3_a_cut_off_entry_with_no_transcript_keeps_its_recorded_end_and_says_why(self) -> None:
        cut = entry("implement", stamp(1, "10:00:00"), stamp(1, "14:00:00"))
        cut["cut_off"] = "iteration 3 ended with the entry open"
        self.accepted(cut)
        found = summaries(self.repo)["S2"]
        self.assertEqual((found.get("stage_seconds"), found["worked_seconds"]), (4 * 3600, 4 * 3600))
        notes = bench(self.repo).stdout
        self.assertIn(f"S2 implement: stage time ends at its recorded end {stamp(1, '14:00:00')} — its transcript's "
                      "last line could not be read", notes)

    def test_e2_a_cut_off_entry_ends_at_its_last_attributed_line_and_the_note_names_both_moments(self) -> None:
        session = Session(self.repo)
        cursor = session.open(None, "implement", f"specs/{FEATURE}/slices/S2/benchmark.json")
        session.say(None, "r1", 100, stamp(1, "10:30:00"))
        cut = session.entry("implement", stamp(1, "10:00:00"), stamp(1, "13:30:00"), cursor)
        cut["cut_off"] = "iteration 3 ended with the entry open"
        self.accepted(cut)
        found = summaries(self.repo)["S2"]
        self.assertEqual((found["stage_seconds"], found["worked_seconds"]), (1800, 1800))
        self.assertEqual(found["entries"][0]["tokens"], 100)
        self.assertIn(f"S2 implement: stage time ends at its last transcript line {stamp(1, '10:30:00')}, not at "
                      f"the recorded end {stamp(1, '13:30:00')}", bench(self.repo).stdout)

    def test_e4_stage_time_is_never_called_wall_and_no_heading_sums_it_as_elapsed(self) -> None:
        self.accepted(entry("implement", stamp(1, "10:00:00"), stamp(1, "11:00:00")),
                      entry("converge", stamp(1, "11:00:00"), stamp(1, "11:30:00")),
                      entry("example-map", stamp(1, "11:30:00"), stamp(1, "11:40:00")))
        record(self.repo, "S3", entry("implement", stamp(1, "10:00:00"), stamp(1, "10:05:00")))
        out = bench(self.repo).stdout
        header = next(line for line in out.splitlines() if line.lstrip().startswith("slice  delegate/cycle"))
        self.assertIn("stage time", header)
        self.assertIn("re-entered", header)
        self.assertNotRegex(header, r"\bwall\b|rework")
        self.assertIn("f — 2 slice(s) recorded, stage time 1h45m in all", out)
        self.assertEqual(bench(self.repo, "overview", FEATURE).returncode, 0)
        page = (self.repo / f"specs/{FEATURE}/benchmark.md").read_text(encoding="utf-8")
        self.assertIn("2 slice(s) recorded, stage time 1h45m in all", page)
        self.assertIn("### S2 — stage time 1h40m", page)
        self.assertIn("| stage | started (UTC) | stage time |", page)
        headings = [line for line in page.splitlines() if line.startswith("### ")]
        self.assertTrue(headings and all("stage time" in line for line in headings), headings)
        found = summaries(self.repo)["S2"]
        self.assertEqual(found["reentered"], ["example-map"])
        self.assertEqual(found["rework"], {"seconds": 0, "tokens": 0})  # R4's meaning: no demo, no rework


if __name__ == "__main__":
    unittest.main()
