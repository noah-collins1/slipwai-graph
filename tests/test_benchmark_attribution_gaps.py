"""The after-converge gaps of AC-S39-3, -5: a request is counted where a record says it belongs, and where no record
does it is shared, in a figure that says so — never a number from a record that does not say it."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from elapsed_fixture import Session, bench, commit, feature_record, git, project, record, stamp, summaries

sys.dont_write_bytecode = True

P1, P2 = "specs/f/slices/S1/benchmark.json", "specs/f/slices/S2/benchmark.json"


class Base(unittest.TestCase):
    def setUp(self) -> None:
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.repo = project(Path(self.scratch.name))
        self.session = Session(self.repo)

    @staticmethod
    def figures(item: dict) -> tuple:
        return item["cost"]["tokens"], item["cost"]["shared"]

    def conserved(self, found: dict, name: str = "sess") -> None:
        """Every token the session spent is in one record or the shared bucket."""
        total = found["(feature)"]["session_totals"][name]
        costs = sum(item["cost"]["tokens"] for item in found.values() if item["slice"])
        self.assertEqual(costs + total["shared"], total["total"], total)


class SiblingBranchTest(Base):
    """T030 (F1): brackets kept on another branch take part in who a request belongs to."""

    def lay(self, delegate_type: str = "drive-hand") -> None:
        said = self.session
        first = said.open(None, "implement", P1)
        second = said.open(None, "demo", P2)
        delegate = said.agent("d1", "S2 demo as the actor", delegate_type)
        said.say(delegate, "d1", 9000, stamp(1, "09:05:00"), delegate_type)
        said.say(None, "h1", 10, stamp(1, "09:06:00"))
        git(self.repo, "checkout", "-q", "-b", "slice/S2")
        commit(self.repo, stamp(1, "09:30:00"), "S2's demo",
               record(self.repo, "S2", said.entry("demo", stamp(1, "09:01:00"), stamp(1, "09:20:00"), second)))
        git(self.repo, "checkout", "-q", "main")
        record(self.repo, "S1", said.entry("implement", stamp(1, "09:00:00"), stamp(1, "09:30:00"), first))
        feature_record(self.repo)

    def test_e1_a_sibling_branchs_delegate_is_shared_not_this_slices_cost(self) -> None:
        self.lay()
        found = summaries(self.repo)
        self.assertEqual(found["S1"]["cost"]["tokens"], 0)
        self.assertEqual(found["S1"]["cost"]["shared"], 9010)
        self.assertEqual(found["S1"]["entries"][0]["delegates"], [])
        self.conserved(found)
        self.assertIn("slice/S2", bench(self.repo).stdout)

    def test_e2_a_delegate_type_no_covering_stage_runs_is_shared_with_a_note(self) -> None:
        said = self.session
        cursor = said.open(None, "implement", P1)
        delegate = said.agent("d1", "someone's demo", "drive-hand")
        said.say(delegate, "d1", 9000, stamp(1, "09:05:00"), "drive-hand")
        said.say(None, "h1", 10, stamp(1, "09:06:00"))
        record(self.repo, "S1", said.entry("implement", stamp(1, "09:00:00"), stamp(1, "09:30:00"), cursor))
        feature_record(self.repo)
        found = summaries(self.repo)
        self.assertEqual(self.figures(found["S1"]), (10, 9000))
        self.assertIn("a drive-hand delegate", bench(self.repo).stdout)
        self.conserved(found)

    def test_e3_a_delegate_the_covering_stage_runs_is_still_its_own(self) -> None:
        said = self.session
        cursor = said.open(None, "implement", P1)
        delegate = said.agent("d1", "Implement T1", "drive-implement")
        said.say(delegate, "d1", 900, stamp(1, "09:05:00"), "drive-implement")
        record(self.repo, "S1", said.entry("implement", stamp(1, "09:00:00"), stamp(1, "09:30:00"), cursor))
        feature_record(self.repo)
        found = summaries(self.repo)
        self.assertEqual(self.figures(found["S1"]), (900, 0))
        self.conserved(found)


class ConservationTest(Base):
    """T031 (F2): every token a session spent lands in one record or the shared bucket, and `--json` shows it."""

    def lay(self) -> None:
        said = self.session
        plan = said.open(None, "plan", P1)
        said.say(None, "h1", 1000, stamp(1, "09:01:00"))
        done = said.entry("plan", stamp(1, "09:00:00"), stamp(1, "09:10:00"), plan)
        gaps = said.open(None, "gaps", P1)
        said.say(None, "h2", 500, stamp(1, "09:10:00"))
        quick = said.entry("gaps", stamp(1, "09:10:00"), stamp(1, "09:10:00"), gaps)
        record(self.repo, "S1", done, quick)
        said.say(None, "late", 3, stamp(1, "11:00:00"))  # after every bracket: nobody's
        feature_record(self.repo)

    def test_e1_a_same_second_entry_keeps_its_tokens_and_its_stage_time_is_unknown(self) -> None:
        self.lay()
        found = summaries(self.repo)
        self.assertEqual(found["S1"]["cost"]["tokens"], 1500)
        self.assertEqual([item["tokens"] for item in found["S1"]["entries"]], [1000, 500])
        self.assertIsInstance(found["S1"]["entries"][1]["stage_seconds"], dict)
        self.assertEqual(found["S1"]["cost"]["sessions"], {"sess": 1500})

    def test_e2_the_records_and_the_shared_bucket_add_up_to_what_the_transcript_holds(self) -> None:
        self.lay()
        found = summaries(self.repo)
        self.assertEqual(found["(feature)"]["session_totals"]["sess"], {"total": 1503, "attributed": 1500, "shared": 3})
        self.conserved(found)
        self.assertEqual(sum(sum(item["cost"]["sessions"].values()) for item in found.values()), 1500)


if __name__ == "__main__":
    unittest.main()
