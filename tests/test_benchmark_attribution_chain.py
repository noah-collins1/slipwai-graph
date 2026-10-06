"""R5, by spawn chain: a request belongs to the slice whose `drive-slice` spawned it, read from `meta.json`."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from elapsed_fixture import Session, bench, feature_record, project, record, stamp, summaries

sys.dont_write_bytecode = True

P1, P2 = "specs/f/slices/S1/benchmark.json", "specs/f/slices/S2/benchmark.json"


class ChainTest(unittest.TestCase):
    def setUp(self) -> None:
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.repo = project(Path(self.scratch.name))
        self.session = Session(self.repo)

    def test_e1_two_slices_open_at_once_each_cost_only_their_own_delegates(self) -> None:
        said = self.session
        first = said.agent("a1", "drive-slice S1", "drive-slice")
        second = said.agent("b1", "S2 slice ladder to converge", "drive-slice")  # older: the first word names it
        impl_first = said.agent("a2", "Implement S1 T001", "drive-implement", parent="a1")
        impl_second = said.agent("b2", "Implement S2 T001", "drive-implement", parent="b1")
        c1 = said.open(first, "implement", P1)
        c2 = said.open(second, "implement", P2)
        said.say(first, "ra", 10, stamp(1, "09:01:00"), "drive-slice")
        said.say(impl_first, "ia", 100, stamp(1, "09:02:00"), "drive-implement")
        said.say(second, "rb", 20, stamp(1, "09:03:00"), "drive-slice")
        said.say(impl_second, "ib", 200, stamp(1, "09:04:00"), "drive-implement")
        said.say(None, "h1", 1, stamp(1, "09:05:00"))
        record(self.repo, "S1", said.entry("implement", stamp(1, "09:00:00"), stamp(1, "09:10:00"), c1))
        record(self.repo, "S2", said.entry("implement", stamp(1, "09:00:01"), stamp(1, "09:10:00"), c2))
        feature_record(self.repo)
        found = summaries(self.repo)
        self.assertEqual(found["S1"]["cost"]["tokens"], 110)
        self.assertEqual(found["S2"]["cost"]["tokens"], 220)
        self.assertEqual(found["S1"]["entries"][0]["delegates"], ["Implement S1 T001", "drive-slice S1"])
        self.assertEqual(found["S2"]["entries"][0]["tokens"], 220)
        self.assertEqual(found["(feature)"]["session_totals"]["sess"], {"total": 331, "attributed": 330, "shared": 1})

    def test_e2_a_host_spawned_delegate_inside_a_drive_slice_bracket_is_not_that_slices(self) -> None:
        said = self.session
        owner = said.agent("a1", "drive-slice S1", "drive-slice")
        stray = said.agent("h1", "Implement S6 T001", "drive-implement")  # spawned by the host: no parent
        cursor = said.open(owner, "implement", P1)
        said.say(owner, "ra", 10, stamp(1, "09:01:00"), "drive-slice")
        said.say(stray, "hs", 300, stamp(1, "09:02:00"), "drive-implement")
        record(self.repo, "S1", said.entry("implement", stamp(1, "09:00:00"), stamp(1, "09:10:00"), cursor))
        found = summaries(self.repo)["S1"]
        self.assertEqual((found["cost"]["tokens"], found["cost"]["shared"]), (10, 300))
        self.assertNotIn("Implement S6 T001", found["entries"][0]["delegates"])

    def test_e6_a_drive_slice_naming_no_record_leaves_its_requests_shared_and_says_so(self) -> None:
        said = self.session
        lost = said.agent("a1", "drive-slice S99-unknown", "drive-slice")
        cursor = said.open(None, "implement", P1)
        said.say(lost, "ra", 70, stamp(1, "09:01:00"), "drive-slice")
        said.say(None, "h1", 5, stamp(1, "09:02:00"))
        record(self.repo, "S1", said.entry("implement", stamp(1, "09:00:00"), stamp(1, "09:10:00"), cursor))
        cost = summaries(self.repo)["S1"]["cost"]
        self.assertEqual((cost["tokens"], cost["shared"]), (5, 70))
        self.assertIn('drive-slice "drive-slice S99-unknown" names no recorded slice — its requests are in the '
                      "shared bucket", bench(self.repo).stdout)

    def test_a_chain_climbs_to_the_drive_slice_through_a_parent(self) -> None:
        said = self.session
        said.agent("a1", "drive-slice S1", "drive-slice")
        said.agent("a2", "Fan-out", "drive-implement", parent="a1")
        deep = said.agent("a3", "Sub-delegate", "drive-implement", parent="a2")
        cursor = said.open(None, "implement", P1)
        said.say(deep, "d", 60, stamp(1, "09:01:00"), "drive-implement")
        record(self.repo, "S1", said.entry("implement", stamp(1, "09:00:00"), stamp(1, "09:10:00"), cursor))
        self.assertEqual(summaries(self.repo)["S1"]["cost"]["tokens"], 60)

    def test_rework_tokens_are_the_attributed_ones(self) -> None:
        said = self.session
        refused = said.open(None, "demo", P1)
        said.say(None, "r5", 5, stamp(1, "09:01:00"))
        demo = said.entry("demo", stamp(1, "09:00:00"), stamp(1, "09:10:00"), refused, outcome="implementation")
        again = said.agent("d1", "Implement T9", "drive-implement")
        cursor = said.open(None, "implement", P1)
        said.say(again, "r7", 700, stamp(1, "09:20:00"), "drive-implement")
        said.say(None, "r3", 3, stamp(1, "09:30:00"))
        record(self.repo, "S1", demo, said.entry("implement", stamp(1, "09:10:00"), stamp(1, "10:00:00"), cursor))
        found = summaries(self.repo)["S1"]
        self.assertEqual(found["rework"], {"seconds": 3000, "tokens": 703})
        self.assertEqual(found["cost"]["tokens"], 708)
        self.assertEqual(found["entries"][1]["delegates"], ["Implement T9"])


class BrokenChainTest(unittest.TestCase):
    """B3: a spawn chain that cannot be followed is not a host's: its requests are shared, and the note says why."""

    def setUp(self) -> None:
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.repo = project(Path(self.scratch.name))
        self.session = Session(self.repo)

    def run_it(self) -> dict:
        said = self.session
        owner = said.agent("ds", "drive-slice S1", "drive-slice")
        child = said.agent("ci", "Implement T1", "drive-implement", parent="ds")
        c2 = said.open(None, "implement", P2)
        c1 = said.open(owner, "implement", P1)
        said.say(owner, "ra", 10, stamp(1, "09:01:00"), "drive-slice")
        said.say(child, "ci", 5000, stamp(1, "09:02:00"), "drive-implement")
        said.say(None, "h1", 170, stamp(1, "09:03:00"))
        record(self.repo, "S1", said.entry("implement", stamp(1, "09:00:00"), stamp(1, "09:10:00"), c1))
        record(self.repo, "S2", said.entry("implement", stamp(1, "09:00:00"), stamp(1, "09:10:00"), c2))
        return {}

    def test_e1_with_the_metadata_present_the_chain_is_followed(self) -> None:
        self.run_it()
        found = summaries(self.repo)
        self.assertEqual((found["S1"]["cost"]["tokens"], found["S2"]["cost"]["tokens"]), (5010, 170))

    def test_e2_a_missing_drive_slice_meta_sends_its_tree_to_the_shared_bucket_with_a_note(self) -> None:
        self.run_it()
        (self.session.agents / "agent-ds.meta.json").unlink()
        found = summaries(self.repo)
        self.assertEqual((found["S1"]["cost"]["tokens"], found["S2"]["cost"]["tokens"]), (0, 170))
        self.assertEqual(found["S2"]["cost"]["shared"], 5010)
        self.assertIn("agent-ds.meta.json", bench(self.repo).stdout)

    def test_e3_a_corrupt_meta_is_the_same(self) -> None:
        self.run_it()
        (self.session.agents / "agent-ds.meta.json").write_text("{", encoding="utf-8")
        found = summaries(self.repo)
        self.assertEqual((found["S1"]["cost"]["tokens"], found["S2"]["cost"]["tokens"]), (0, 170))

    def test_e4_a_parent_that_resolves_nowhere_is_the_same_and_names_it(self) -> None:
        self.run_it()
        meta = self.session.agents / "agent-ci.meta.json"
        meta.write_text(meta.read_text(encoding="utf-8").replace('"ds"', '"ghost"'), encoding="utf-8")
        found = summaries(self.repo)
        self.assertEqual((found["S1"]["cost"]["tokens"], found["S2"]["cost"]["tokens"]), (10, 170))
        self.assertEqual(found["S2"]["cost"]["shared"], 5000)
        self.assertIn("ghost", bench(self.repo).stdout)


if __name__ == "__main__":
    unittest.main()
