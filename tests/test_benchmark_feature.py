"""R6: a feature's elapsed time is not its stage time — the three figures sit under three names."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from collections.abc import Sequence
from pathlib import Path

from elapsed_fixture import FEATURE, bench, commit, entry, graph, project, record, register, stamp, summaries, write

from slipwai.assets import ROOT

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


UNKNOWN = "unknown — no decision entry carries a Reversibility: line"


def log(entries: Sequence[tuple[str, str | None, str]]) -> str:
    """A decision log: each entry is (when, Reversibility value or None, Status)."""
    parts = ["# Decisions — f\n"]
    for number, (when, tier, status) in enumerate(entries, 1):
        lines = [f"## D{number} — a question", f"- **Stage:** plan · **When:** {when} · **Iteration:** 1"]
        lines += [f"- **Reversibility:** {tier}"] if tier else []
        parts.append("\n".join([*lines, f"- **Status:** {status}"]) + "\n")
    return "\n".join(parts)


class DecisionHealthTest(unittest.TestCase):
    def setUp(self) -> None:
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.repo = project(Path(self.scratch.name))

    def health(self, text: str, *skippers: dict) -> tuple[list[str], dict]:
        """The three printed lines under the feature heading, and `decision_health` of the feature record."""
        write(self.repo, f"specs/{FEATURE}/decisions.md", text)
        record(self.repo, "S1", entry("implement", stamp(1, "10:00:00"), stamp(1, "11:00:00")), *skippers)
        out = bench(self.repo).stdout.splitlines()
        lines = [line.strip() for line in out if line.strip().startswith(("escalation share", "misclassification rate",
                                                                          "median wait"))]
        write(self.repo, f"specs/{FEATURE}/benchmark.json",
              json.dumps({"feature": FEATURE, "slice": None, "stages": []}))
        return lines, summaries(self.repo)["(feature)"].get("decision_health", {})

    def test_e1_this_repositorys_log_reads_three_unknowns_and_prints_no_percent(self) -> None:
        shutil.copy2(ROOT / "specs/001-faster-slipwai/decisions.md", self.repo / "d.md")
        lines, found = self.health((self.repo / "d.md").read_text(encoding="utf-8"))
        self.assertEqual(3, len(lines), lines)
        for line in lines:
            self.assertIn(UNKNOWN, line)
            self.assertNotIn("%", line)
            self.assertFalse(any(ch.isdigit() for ch in line.split("—")[0]), line)
        self.assertEqual({key: {"unknown": UNKNOWN[len("unknown — "):]} for key in
                          ("escalation_share", "misclassification_rate", "median_wait")}, found)

    def test_e2_twenty_tiered_entries_four_escalated_is_twenty_percent_and_flagged(self) -> None:
        when = stamp(1, "10:30:00")
        entries = [(when, "easy", "ratified")] * 16 + [(when, "guarded → hard", "ratified")] * 4
        lines, found = self.health(log(entries))
        self.assertIn("escalation share: 20% (4 of 20 entries scored easy or guarded) — outside the healthy band 5–15%",
                      lines[0])
        self.assertEqual((20, True), (found["escalation_share"]["percent"], found["escalation_share"]["flagged"]))
        self.assertEqual(0, bench(self.repo, "overview", FEATURE).returncode)
        page = (self.repo / f"specs/{FEATURE}/benchmark.md").read_text(encoding="utf-8")
        self.assertIn("## Decision health\n\n- escalation share: 20% (4 of 20", page)
        arrow = log([(when, "easy -> hard", "standing")] + [(when, "guarded", "standing")] * 9)
        self.assertIn("10% (1 of 10", self.health(arrow)[0][0])

    def test_e3_one_reverted_of_ten_is_flagged_none_of_ten_is_not(self) -> None:
        when = stamp(1, "10:30:00")
        one = [(when, "easy", "reverted")] + [(when, "easy", "ratified")] * 9
        lines, found = self.health(log(one))
        self.assertIn("misclassification rate: 10% (1 of 10 reviewed) — over 5%", lines[1])
        self.assertTrue(found["misclassification_rate"]["flagged"])
        lines, found = self.health(log([(when, "easy", "ratified")] * 10))
        self.assertIn("misclassification rate: 0% (0 of 10 reviewed)", lines[1])
        self.assertNotIn("over 5%", lines[1])
        self.assertFalse(found["misclassification_rate"]["flagged"])

    def test_e4_tiers_but_no_review_the_rate_is_unknown_naming_that(self) -> None:
        lines, found = self.health(log([(stamp(1, "10:30:00"), "easy", "standing")] * 3))
        self.assertIn("misclassification rate: unknown — no tiered entry was ratified or reverted", lines[1])
        self.assertEqual({"unknown": "no tiered entry was ratified or reverted"}, found["misclassification_rate"])

    def test_e5_median_wait_is_the_median_of_the_skipper_brackets_holding_each_when(self) -> None:
        a = entry("skipper", stamp(1, "10:00:00"), stamp(1, "10:02:00"))
        b = entry("skipper", stamp(1, "11:00:00"), stamp(1, "11:05:00"))
        entries = [(stamp(1, "10:01:00"), "easy", "ratified"), (stamp(1, "11:04:00"), "easy", "ratified"),
                   (stamp(1, "12:00:00"), "guarded", "ratified")]
        lines, found = self.health(log(entries), a, b)
        self.assertIn("median wait: easy 3m30s", lines[2])
        self.assertIn("guarded unknown (no skipper bracket holds a guarded entry's When: moment)", lines[2])
        self.assertEqual(210, found["median_wait"]["easy"])
        self.assertEqual("no hard entry", found["median_wait"]["hard"]["unknown"])


if __name__ == "__main__":
    unittest.main()
