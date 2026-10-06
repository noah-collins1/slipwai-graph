"""R4: rework is what a demo that was not accepted cost; the record's cost is the sum of what its entries cost."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from elapsed_fixture import Session, bench, costed, entry, feature_record, project, record, stamp, summaries

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


if __name__ == "__main__":
    unittest.main()
