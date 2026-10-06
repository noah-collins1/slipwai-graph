"""R4: rework is what a demo that was not accepted cost; the record's cost is the sum of what its entries cost."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from elapsed_fixture import (
    Session,
    bench,
    commit,
    costed,
    entry,
    feature_record,
    git,
    project,
    record,
    stamp,
    summaries,
)

sys.dont_write_bytecode = True


class ReworkTest(unittest.TestCase):
    def setUp(self) -> None:
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.repo = project(Path(self.scratch.name))

    def test_e1_rework_is_the_entries_between_a_refused_demo_and_the_next_demo(self) -> None:
        """S08's shape: the last implement, after the accepted demo, is not rework."""
        def demo(start: str, end: str, outcome: str) -> dict:
            return costed(entry("demo", stamp(1, start), stamp(1, end), outcome=outcome), 100_000)

        record(self.repo, "S8",
               demo("09:00:00", "09:10:00", "implementation"),
               costed(entry("implement", stamp(1, "09:10:00"), stamp(1, "10:10:00")), 3_000_000),
               demo("10:10:00", "10:20:00", "implementation"),
               costed(entry("implement", stamp(1, "10:20:00"), stamp(1, "11:00:00")), 1_500_000),
               demo("11:00:00", "11:10:00", "accepted"),
               costed(entry("implement", stamp(1, "11:10:00"), stamp(1, "11:30:00")), 700_000))
        found = summaries(self.repo)["S8"]
        self.assertEqual(found["rework"], {"seconds": 3600 + 2400, "tokens": 4_500_000})
        self.assertEqual(found["cost"]["tokens"], 5_500_000)
        self.assertEqual([item["tokens"] for item in found["entries"]],
                         [100_000, 3_000_000, 100_000, 1_500_000, 100_000, 700_000])
        self.assertEqual(found["entries"][1]["stage_seconds"], 3600)
        out = bench(self.repo).stdout
        header = next(line for line in out.splitlines() if line.lstrip().startswith("slice  elapsed"))
        self.assertEqual(header.split()[-2:], ["rework", "cost"], header)
        row = next(line for line in out.splitlines() if line.lstrip().startswith("S8 ") and "1h40m" in line)
        self.assertTrue(row.split()[-1] == "5.5M" and "4.5M" in row, row)

    def test_e2_a_slice_with_no_demo_has_no_rework(self) -> None:
        record(self.repo, "S8", costed(entry("implement", stamp(1, "09:00:00"), stamp(1, "10:00:00")), 10))
        self.assertEqual(summaries(self.repo)["S8"]["rework"], {"seconds": 0, "tokens": 0})

    def test_e3_the_entries_after_a_refused_demo_with_no_next_demo_are_rework(self) -> None:
        record(self.repo, "S8",
               entry("demo", stamp(1, "09:00:00"), stamp(1, "09:10:00"), outcome="behaviour"),
               costed(entry("implement", stamp(1, "09:10:00"), stamp(1, "09:40:00")), 800),
               costed(entry("converge", stamp(1, "09:40:00"), stamp(1, "09:50:00")), 200))
        self.assertEqual(summaries(self.repo)["S8"]["rework"], {"seconds": 2400, "tokens": 1000})


P1, P2 = "specs/f/slices/S1/benchmark.json", "specs/f/slices/S2/benchmark.json"


def everything(repo: Path) -> list[dict]:
    return json.loads(bench(repo, "--json").stdout)


class ShareTest(unittest.TestCase):
    """R5: each request is counted in one record, the shared bucket when no record can claim it."""

    def setUp(self) -> None:
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.repo = project(Path(self.scratch.name))
        self.session = Session(self.repo)

    def test_e3_a_host_line_covered_by_two_slices_host_opened_brackets_is_shared(self) -> None:
        said = self.session
        first = said.open(None, "converge", P1)
        said.say(None, "h0", 7, stamp(1, "09:01:00"))
        second = said.open(None, "implement", P2)
        said.say(None, "h1", 50, stamp(1, "09:02:00"))
        delegate = said.agent("d1", "Implement T1", "drive-implement")
        said.say(delegate, "d1", 900, stamp(1, "09:03:00"), "drive-implement")
        record(self.repo, "S1", said.entry("converge", stamp(1, "09:00:00"), stamp(1, "09:10:00"), first))
        record(self.repo, "S2", said.entry("implement", stamp(1, "09:01:30"), stamp(1, "09:10:00"), second))
        feature_record(self.repo)
        found = summaries(self.repo)
        self.assertEqual(found["S1"]["cost"], {"tokens": 7, "shared": 50})
        self.assertEqual(found["S2"]["cost"], {"tokens": 900, "shared": 50})
        self.assertEqual(found["(feature)"]["cost"]["shared"], 50)

    def test_e4_a_bracket_merged_from_two_branches_counts_its_requests_once(self) -> None:
        said = self.session
        cursor = said.open(None, "implement", P1)
        said.say(None, "h1", 40, stamp(1, "09:01:00"))
        once = said.entry("implement", stamp(1, "09:00:00"), stamp(1, "09:10:00"), cursor)
        record(self.repo, "S1", once, dict(once))
        record(self.repo, "S1", dict(once), feature="g")
        feature_record(self.repo)
        costs = sorted((item["path"], item["cost"]["tokens"]) for item in everything(self.repo) if item["slice"])
        self.assertEqual(sum(tokens for _, tokens in costs), 40)
        totals = summaries(self.repo)["(feature)"]["session_totals"]["sess"]
        self.assertEqual(totals, {"total": 40, "attributed": 40, "shared": 0})

    def test_e5_the_records_and_the_shared_bucket_add_up_to_the_sessions_distinct_requests(self) -> None:
        said = self.session
        cursor = said.open(None, "implement", P1)
        said.say(None, "h1", 40, stamp(1, "09:01:00"))
        record(self.repo, "S1", said.entry("implement", stamp(1, "09:00:00"), stamp(1, "09:10:00"), cursor))
        said.say(None, "late", 3, stamp(1, "11:00:00"))  # after every bracket: nobody's
        feature_record(self.repo)
        totals = summaries(self.repo)["(feature)"]["session_totals"]["sess"]
        self.assertEqual(totals, {"total": 43, "attributed": 40, "shared": 3})
        self.assertEqual(summaries(self.repo)["(feature)"]["cost"]["shared"], 3)

    def test_e7_no_transcripts_the_recorded_sum_stands_where_no_other_records_bracket_overlaps(self) -> None:
        def costing(start: str, end: str, tokens: int) -> dict:
            return costed(entry("implement", stamp(1, start), stamp(1, end)), tokens, session="gone")

        record(self.repo, "S1", costing("09:00:00", "10:00:00", 1000))
        record(self.repo, "S2", costing("09:30:00", "10:30:00", 2000))
        record(self.repo, "S3", costing("12:00:00", "13:00:00", 500))
        feature_record(self.repo)
        found = summaries(self.repo)
        reason = "brackets of {} overlap this one and the transcripts are not on this machine"
        self.assertEqual(found["S1"]["cost"]["tokens"], {"unknown": reason.format("S2")})
        self.assertEqual(found["S2"]["cost"]["tokens"], {"unknown": reason.format("S1")})
        self.assertEqual(found["S3"]["cost"], {"tokens": 500, "shared": {"unknown": "no transcript was read"}})
        self.assertEqual(found["(feature)"]["session_totals"]["gone"]["total"],
                         {"unknown": "the transcripts are not on this machine"})


class CostProvenanceTest(unittest.TestCase):
    """AC-S39-9: `read_from.cost`, and each entry's, names what the cost was read from — never a transcript that was
    not read."""

    def setUp(self) -> None:
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.repo = project(Path(self.scratch.name))

    def test_e1_no_transcript_on_the_machine_the_cost_is_the_recorded_usage_and_says_so(self) -> None:
        record(self.repo, "S1", costed(entry("implement", stamp(1, "09:00:00"), stamp(1, "10:00:00")), 10, "gone"),
               costed(entry("converge", stamp(1, "10:00:00"), stamp(1, "10:30:00")), 5, "gone"))
        found = summaries(self.repo)["S1"]
        self.assertEqual(found["cost"]["tokens"], 15)
        self.assertEqual(found["read_from"]["cost"], "the entries' recorded usage")
        self.assertNotIn("transcript", found["read_from"]["cost"])
        for item in found["entries"]:
            self.assertEqual(item["read_from"], "the entries' recorded usage")

    def test_e2_one_session_present_and_one_absent_both_are_named_with_their_entries(self) -> None:
        said = Session(self.repo)
        cursor = said.open(None, "implement", P1)
        said.say(None, "h1", 40, stamp(1, "09:01:00"))
        record(self.repo, "S1", said.entry("implement", stamp(1, "09:00:00"), stamp(1, "10:00:00"), cursor),
               costed(entry("converge", stamp(1, "10:00:00"), stamp(1, "10:30:00")), 5, "gone"))
        found = summaries(self.repo)["S1"]
        self.assertEqual(found["cost"]["tokens"], 45)
        self.assertEqual(found["read_from"]["cost"], "the transcripts, by delegate and bracket (1 entry) and "
                         "the entries' recorded usage (1 entry)")
        self.assertEqual([item["read_from"] for item in found["entries"]],
                         ["the transcripts, by delegate and bracket", "the entries' recorded usage"])


class UnreadEntriesTest(unittest.TestCase):
    """AC-S39-8: an unbracketed or open entry has no tokens and no stage time to read — unknown, never a bare `0`,
    with the transcripts on the machine and without them."""

    def setUp(self) -> None:
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.repo = project(Path(self.scratch.name))

    def lay(self) -> None:
        said = Session(self.repo)
        cursor = said.open(None, "implement", P1)
        said.say(None, "h1", 40, stamp(1, "09:30:00"))
        bracketed = said.entry("implement", stamp(1, "09:00:00"), stamp(1, "10:00:00"), cursor)
        bracketed["usage"]["host"] = {"m": {"input": 40, "output": 0, "cache_read": 0, "cache_creation": 0}}
        unbracketed = said.entry("gaps", stamp(1, "10:00:00"), stamp(1, "10:00:00"), said.open(None, "gaps", P1))
        left_open = said.entry("converge", stamp(1, "10:05:00"), stamp(1, "10:05:00"), said.open(None, "converge", P1))
        del left_open["ended"], left_open["seconds"]
        record(self.repo, "S1", bracketed, unbracketed, left_open)

    def test_e1_per_entry_figures_and_the_records_cost_are_the_same_with_and_without_transcripts(self) -> None:
        self.lay()
        runs = [summaries(self.repo)["S1"]]
        shutil.rmtree(self.repo / ".home/.claude")
        runs.append(summaries(self.repo)["S1"])
        for found in runs:
            for item in found["entries"][1:]:
                with self.subTest(stage=item["stage"]):
                    self.assertIsInstance(item["tokens"], dict, item)
                    self.assertIsInstance(item["stage_seconds"], dict, item)
            self.assertIn("not bracketed", found["entries"][1]["tokens"]["unknown"])
            self.assertIn("still open", found["entries"][2]["stage_seconds"]["unknown"])
            self.assertEqual(found["entries"][0]["stage_seconds"], 3600)
            self.assertEqual((found["stage_seconds"], found["seconds"]), (3600, 3600))  # the pin: today's sum stands
        self.assertEqual(runs[0]["cost"]["tokens"], runs[1]["cost"]["tokens"])
        self.assertIsInstance(runs[0]["cost"]["tokens"], dict)


class OtherBranchesTest(unittest.TestCase):
    """AC-S39-5: without transcripts the overlap check sees the brackets kept on other slice branches."""

    def setUp(self) -> None:
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.repo = project(Path(self.scratch.name))

    def concurrent(self, start: str, end: str) -> None:
        """S2's record, committed on `slice/S2` alone; the checkout is left on `slice/S1`."""
        repo = self.repo
        git(repo, "checkout", "-q", "-b", "slice/S2")
        path = record(repo, "S2", costed(entry("implement", stamp(1, start), stamp(1, end)), 2000, "gone"))
        commit(repo, stamp(1, "11:00:00"), "S2's brackets", path)
        git(repo, "checkout", "-q", "-b", "slice/S1", "main")
        self.assertFalse((repo / path).exists())
        record(repo, "S1", costed(entry("implement", stamp(1, "09:00:00"), stamp(1, "10:00:00")), 1000, "gone"))

    def test_e1_a_concurrent_slices_brackets_on_its_own_branch_make_the_recorded_sum_unknown(self) -> None:
        self.concurrent("09:30:00", "10:30:00")
        found = summaries(self.repo)["S1"]
        for figure in (found["cost"]["tokens"], found["entries"][0]["tokens"]):
            self.assertIsInstance(figure, dict)
            self.assertTrue(figure["unknown"].startswith("brackets of S2 "), figure)
            self.assertIn("overlap", figure["unknown"])

    def test_e2_no_branch_holds_an_overlapping_bracket_the_recorded_sum_stands(self) -> None:
        self.concurrent("12:00:00", "13:00:00")
        self.assertEqual(summaries(self.repo)["S1"]["cost"]["tokens"], 1000)

    def test_e3_where_git_cannot_list_the_branches_the_recorded_sum_is_unknown_saying_so(self) -> None:
        self.concurrent("12:00:00", "13:00:00")
        shutil.rmtree(self.repo / ".git")
        figure = summaries(self.repo)["S1"]["cost"]["tokens"]
        self.assertIsInstance(figure, dict)
        self.assertIn("git", figure["unknown"])

    def test_e4_an_integration_branch_with_any_name_is_read_like_the_others(self) -> None:
        """T025 e1: the branch is `adopt-method`, S2's record is committed only there."""
        repo = self.repo
        git(repo, "branch", "-m", "main", "adopt-method")
        path = record(repo, "S2", costed(entry("implement", stamp(1, "09:30:00"), stamp(1, "10:30:00")), 2000, "gone"))
        commit(repo, stamp(1, "11:00:00"), "S2 on the integration branch", path)
        git(repo, "checkout", "-q", "-b", "slice/S1", "HEAD~1")
        record(repo, "S1", costed(entry("implement", stamp(1, "09:00:00"), stamp(1, "10:00:00")), 1000, "gone"))
        found = summaries(repo)["S1"]
        for figure in (found["cost"]["tokens"], found["entries"][0]["tokens"]):
            self.assertIsInstance(figure, dict)
            self.assertIn("brackets of S2 on adopt-method overlap", figure["unknown"])

    def test_e5_a_newer_copy_of_a_record_this_tree_holds_is_compared_too(self) -> None:
        """T025 e2: the tree holds S2 with a `plan` that overlaps nothing; `main`'s copy adds an overlapping one."""
        repo = self.repo
        plan = costed(entry("plan", stamp(1, "07:00:00"), stamp(1, "08:00:00")), 50, "gone")
        path = record(repo, "S2", plan)
        commit(repo, stamp(1, "08:00:00"), "S2 plan", path)
        git(repo, "checkout", "-q", "-b", "slice/S1")
        git(repo, "checkout", "-q", "main")
        record(repo, "S2", plan, costed(entry("implement", stamp(1, "09:30:00"), stamp(1, "10:30:00")), 2000, "gone"))
        commit(repo, stamp(1, "11:00:00"), "S2 implement on main", path)
        git(repo, "checkout", "-q", "slice/S1")
        record(repo, "S1", costed(entry("implement", stamp(1, "09:00:00"), stamp(1, "10:00:00")), 1000, "gone"))
        found = summaries(repo)["S1"]
        self.assertIsInstance(found["cost"]["tokens"], dict, found["cost"])
        self.assertIn("brackets of S2 on main overlap", found["cost"]["tokens"]["unknown"])
        self.assertEqual(found["entries"][0]["tokens"], found["cost"]["tokens"])


if __name__ == "__main__":
    unittest.main()
