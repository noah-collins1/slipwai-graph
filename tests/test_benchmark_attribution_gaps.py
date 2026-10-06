"""The after-converge gaps of AC-S39-3, -5: a request is counted where a record says it belongs, and where no record
does it is shared, in a figure that says so — never a number from a record that does not say it."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from elapsed_fixture import Session, bench, commit, costed, feature_record, git, project, record, stamp, summaries

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


class PartlyMissingTest(Base):
    """T034 (F5): a session with a transcript file gone is not costed as whole."""

    def lay(self, recorded: bool) -> Path:
        said = self.session
        cursor = said.open(None, "implement", P1)
        said.say(None, "h1", 10, stamp(1, "09:01:00"))
        delegate = said.agent("a1", "Implement T1", "drive-implement")
        said.say(delegate, "a1", 5000, stamp(1, "09:02:00"), "drive-implement")
        item = said.entry("implement", stamp(1, "09:00:00"), stamp(1, "09:30:00"), cursor)
        if recorded:
            item["usage"]["host"] = {"m": {"input": 10, "output": 0, "cache_read": 0, "cache_creation": 0}}
            item["usage"]["subagents"] = {"m": {"input": 5000, "output": 0, "cache_read": 0, "cache_creation": 0}}
        record(self.repo, "S1", item)
        feature_record(self.repo)
        return delegate

    def test_e1_a_missing_sub_agent_file_makes_the_cost_unknown_naming_it(self) -> None:
        self.lay(recorded=False).unlink()
        found = summaries(self.repo)["S1"]
        for figure in (found["cost"]["tokens"], found["entries"][0]["tokens"]):
            self.assertIsInstance(figure, dict, found)
            self.assertIn("agent-a1.jsonl", figure["unknown"])
        self.assertNotIn("transcripts, by", found["read_from"]["cost"])

    def test_e2_with_a_recorded_usage_the_cost_is_that_and_says_so(self) -> None:
        self.lay(recorded=True).unlink()
        found = summaries(self.repo)["S1"]
        self.assertEqual(found["cost"]["tokens"], 5010)
        self.assertEqual(found["read_from"]["cost"], "the entries' recorded usage")
        self.assertIn("agent-a1.jsonl", bench(self.repo).stdout)

    def test_e3_with_every_file_present_the_transcripts_are_read(self) -> None:
        self.lay(recorded=False)
        found = summaries(self.repo)["S1"]
        self.assertEqual(found["cost"]["tokens"], 5010)
        self.assertIn("the transcripts", found["read_from"]["cost"])


class TwoFeaturesTest(Base):
    """T037 (F8): a session two features ran in has its shared bucket split between them, never counted by both."""

    def lay(self) -> None:
        said = self.session
        first = said.open(None, "converge", P1)
        said.say(None, "h0", 7, stamp(1, "09:01:00"))
        second = said.open(None, "implement", P2)
        said.say(None, "h1", 50, stamp(1, "09:02:00"))  # two of f's brackets cover it: shared, and f's
        record(self.repo, "S1", said.entry("converge", stamp(1, "09:00:00"), stamp(1, "09:10:00"), first))
        record(self.repo, "S2", said.entry("implement", stamp(1, "09:01:30"), stamp(1, "09:10:00"), second))
        third = said.open(None, "implement", "specs/g/slices/S3/benchmark.json")
        said.say(None, "g1", 9, stamp(1, "11:01:00"))
        record(self.repo, "S3", said.entry("implement", stamp(1, "11:00:00"), stamp(1, "11:10:00"), third),
               feature="g")
        said.say(None, "late", 3, stamp(1, "12:00:00"))  # after every bracket: nobody's
        feature_record(self.repo)
        feature_record(self.repo, feature="g")

    def test_e1_the_shared_bucket_is_split_by_the_brackets_that_cover_each_request(self) -> None:
        self.lay()
        found = json.loads(bench(self.repo, "--json").stdout)
        mine = [item["session_totals"]["sess"] for item in found if item.get("session_totals")]
        self.assertEqual(len(mine), 2)
        by_attributed = {part["attributed"]: part for part in mine}
        self.assertEqual(by_attributed[7]["shared"], 50)
        self.assertEqual(by_attributed[9]["shared"], 0)
        for part in mine:
            self.assertEqual(part["total"], 69)
            self.assertEqual(part["total"], part["attributed"] + part["shared"] + part["elsewhere"], part)
        self.assertEqual(sum(part["shared"] for part in mine), 50)  # not 53 twice
        shared = sorted(item["cost"]["shared"] for item in found if item["slice"] is None)
        self.assertEqual(shared, [0, 50])

    def test_e2_the_feature_says_which_other_feature_ran_in_the_session(self) -> None:
        self.lay()
        self.assertIn("also ran in feature g", bench(self.repo).stdout)


class ConservedAcrossFeaturesTest(Base):
    """B4: a session is split among every feature that brackets in it or is charged there by the chain."""

    def lay(self, other: str = "S7") -> None:
        said = self.session
        cursor = said.open(None, "implement", P1)
        said.say(None, "h1", 100, stamp(1, "09:01:00"))
        owner = said.agent("ds", f"drive-slice {other}", "drive-slice")
        child = said.agent("ci", "Implement T1", "drive-implement", parent="ds")
        said.say(owner, "ra", 10, stamp(1, "09:02:00"), "drive-slice")
        said.say(child, "rb", 5000, stamp(1, "09:03:00"), "drive-implement")
        record(self.repo, "S1", said.entry("implement", stamp(1, "09:00:00"), stamp(1, "09:10:00"), cursor))
        feature_record(self.repo)

    def test_e1_a_feature_charged_only_by_the_chain_is_a_feature_of_the_session(self) -> None:
        self.lay()
        record(self.repo, "S7", entryless(), feature="g")
        feature_record(self.repo, feature="g")
        found = {(item["feature"], item["slice"]): item for item in json.loads(bench(self.repo, "--json").stdout)}
        mine = found[("f", None)]["session_totals"]["sess"]
        self.assertEqual((mine["attributed"], mine["shared"], mine["elsewhere"]), (100, 0, 5010))
        other = found[("g", "S7")]["cost"]
        self.assertEqual((other["sessions"], other["shared"]), ({"sess": 5010}, 0))
        self.assertEqual(found[("g", None)]["session_totals"]["sess"]["attributed"], 5010)

    def test_e2_a_slice_id_found_in_two_features_is_shared_with_a_note(self) -> None:
        self.lay("S1")
        record(self.repo, "S1", entryless(), feature="g")
        feature_record(self.repo, feature="g")
        found = {(item["feature"], item["slice"]): item for item in json.loads(bench(self.repo, "--json").stdout)}
        self.assertEqual(found[("f", "S1")]["cost"]["tokens"], 100)
        self.assertEqual(found[("f", None)]["session_totals"]["sess"]["shared"], 5010)
        self.assertIn("more than one feature", bench(self.repo).stdout)


def entryless() -> dict:
    """A stage that ran in no session this machine knows."""
    return {"stage": "implement", "started": stamp(1, "09:00:00"), "ended": stamp(1, "09:10:00"), "seconds": 600,
            "signals": {}, "usage": {"source": None, "reason": "fixture"}}


class FallbackClaimsTest(Base):
    """B5: an entry costed from its recorded usage claims the live requests of its window, so none counts twice."""

    def test_e1_a_sub_agent_file_gone_leaves_the_host_line_with_the_entry_not_the_shared_bucket(self) -> None:
        said = self.session
        cursor = said.open(None, "implement", P1)
        said.say(None, "h1", 100, stamp(1, "09:01:00"))
        delegate = said.agent("a1", "Implement T1", "drive-implement")
        said.say(delegate, "a1", 5000, stamp(1, "09:02:00"), "drive-implement")
        item = costed(said.entry("implement", stamp(1, "09:00:00"), stamp(1, "09:10:00"), cursor), 5107, "sess")
        record(self.repo, "S1", item)
        feature_record(self.repo)
        delegate.unlink()
        found = summaries(self.repo)
        self.assertEqual(self.figures(found["S1"]), (5107, 0))
        self.assertEqual(found["S1"]["cost"]["sessions"], {"sess": 100})
        self.assertEqual(found["(feature)"]["session_totals"]["sess"], {"total": 100, "attributed": 100, "shared": 0})

    def test_e2_a_main_transcript_gone_leaves_the_chains_requests_with_the_entry_not_counted_again(self) -> None:
        said = self.session
        owner = said.agent("ds", "drive-slice S1", "drive-slice")
        child = said.agent("ci", "Implement T1", "drive-implement", parent="ds")
        cursor = said.open(owner, "implement", P1)
        said.say(owner, "ra", 10, stamp(1, "09:01:00"), "drive-slice")
        said.say(child, "rb", 5000, stamp(1, "09:02:00"), "drive-implement")
        said.say(None, "h1", 100, stamp(1, "09:03:00"))
        item = costed(said.entry("implement", stamp(1, "09:00:00"), stamp(1, "09:10:00"), cursor), 5110, "sess")
        record(self.repo, "S1", item)
        feature_record(self.repo)
        said.main.unlink()
        found = summaries(self.repo)
        self.assertEqual(self.figures(found["S1"]), (5110, 0))
        self.assertEqual(found["S1"]["cost"]["sessions"], {"sess": 5010})


if __name__ == "__main__":
    unittest.main()
