"""R6: a feature's elapsed time is not its stage time — the three figures sit under three names."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from collections.abc import Sequence
from pathlib import Path

from elapsed_fixture import (
    FEATURE,
    bench,
    commit,
    entry,
    feature_record,
    graph,
    project,
    record,
    register,
    stamp,
    summaries,
    write,
)

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

    def test_e3_a_slice_with_no_ready_moment_makes_the_feature_elapsed_unknown_naming_it(self) -> None:
        repo = self.repo
        write(repo, SPLIT, graph([("S1", [])]))  # S2 is in no graph and no model: its ready moment is unread
        paths = [SPLIT] + [record(repo, ident, entry("implement", stamp(1, "10:00:00"), stamp(1, "11:00:00")))
                           for ident in ("S1", "S2")]
        own = f"specs/{FEATURE}/benchmark.json"
        stages = [entry("split", stamp(1, "09:00:00"), stamp(1, "10:00:00"))]
        write(repo, own, json.dumps({"feature": FEATURE, "slice": None, "stages": stages}))
        paths.append(own)
        commit(repo, stamp(1), "records", *paths)
        write(repo, REGISTER, register(["S1", "S2"]))
        commit(repo, stamp(2, "21:00:00"), "done", REGISTER)
        done = bench(self.repo)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertNotIn("Traceback", done.stderr)
        elapsed = summaries(self.repo)["(feature)"]["feature_figures"]["elapsed"]
        self.assertEqual(set(elapsed), {"unknown"})
        self.assertTrue(elapsed["unknown"].startswith("S2: "), elapsed)
        self.assertIn("elapsed unknown (S2: ", done.stdout)


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
        self.assertIn("guarded unknown (no skipper bracket holds the When: moment of any guarded entry)", lines[2])
        self.assertEqual(210, found["median_wait"]["easy"])
        self.assertEqual("no hard entry", found["median_wait"]["hard"]["unknown"])


WAITING = ("dependency", "worker", "review", "integration", "unattributed")
FIGURES = ("elapsed", "stage_seconds", "worked_seconds", "cost", "rework")
READ = ("elapsed", "stage_seconds", "worked_seconds", *WAITING[:4], "unattributed", "rework", "cost")
SOURCES = ("commit", "specs/cruise-log.jsonl", "decisions.md", "transcript", "bracket", "none present")


def is_figure(value: object) -> bool:
    return (isinstance(value, int) and not isinstance(value, bool)) or (
        isinstance(value, dict) and set(value) == {"unknown"} and isinstance(value["unknown"], str))


class JsonKeysTest(unittest.TestCase):
    """R9: `--json` carries every figure S37 reads, on every record, and says where each was read."""

    def setUp(self) -> None:
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.repo = project(Path(self.scratch.name))
        repo = self.repo
        write(repo, SPLIT, graph([("S1", []), ("S2", [])]))
        paths = [SPLIT, record(repo, "S1", entry("implement", stamp(1, "10:00:00"), stamp(1, "12:00:00"))),
                 record(repo, "S2", entry("implement", stamp(1, "10:00:00"), stamp(1, "12:00:00"))),
                 feature_record(repo, entry("split", stamp(1, "09:00:00"), stamp(1, "10:00:00")))]
        commit(repo, stamp(1), "split", *paths)
        write(repo, REGISTER, register(["S1"]))
        commit(repo, stamp(1, "15:00:00"), "S1 done", REGISTER)  # S2 stays open

    def test_e1_every_key_is_on_every_record_each_a_number_or_an_unknown_object(self) -> None:
        found = summaries(self.repo)
        self.assertEqual({"S1", "S2", "(feature)"}, set(found))
        for name, item in found.items():
            with self.subTest(record=name):
                self.assertTrue(all(is_figure(item[key]) for key in ("elapsed", "stage_seconds", "worked_seconds")))
                self.assertEqual(set(WAITING), set(item["waiting"]))
                self.assertTrue(all(is_figure(value) for value in item["waiting"].values()))
                self.assertEqual({"seconds", "tokens"}, set(item["rework"]))
                self.assertEqual({"tokens", "shared"}, set(item["cost"]))
                self.assertTrue(all(is_figure(value) for value in (*item["rework"].values(), *item["cost"].values())))
                self.assertTrue(all(isinstance(value, str) or is_figure(value) for value in item["moments"].values()))
                self.assertIsInstance(item["entries"], list)
                self.assertIsInstance(item["reentered"], list)
        self.assertEqual(7200 + 0, found["S1"]["stage_seconds"])
        self.assertTrue(isinstance(found["S1"]["elapsed"], int) and "unknown" in found["S2"]["elapsed"])

    def test_e2_read_from_names_a_source_for_each_figure_known_or_not(self) -> None:
        for name, item in summaries(self.repo).items():
            with self.subTest(record=name):
                for key in READ:
                    self.assertIn(key, item["read_from"])
                    said = item["read_from"][key]
                    self.assertTrue(any(word in said for word in SOURCES), (key, said))
        read = summaries(self.repo)["S1"]["read_from"]
        self.assertRegex(read["elapsed"], r"[0-9a-f]{7}")
        self.assertIn("bracket", read["worked_seconds"])
        self.assertTrue(read["worker"].startswith("none present"))

    def test_e3_the_reading_paragraph_says_how_elapsed_differs_from_stage_time(self) -> None:
        self.assertEqual(0, bench(self.repo, "overview", FEATURE).returncode)
        page = (self.repo / f"specs/{FEATURE}/benchmark.md").read_text(encoding="utf-8")
        sentence = ("Elapsed runs from a slice's ready commit to its accepted one; stage time adds up its brackets, "
                    "which overlap across slices, so the two are never the same figure under one name.")
        self.assertEqual(1, page.count(sentence))
        self.assertIn(sentence, page.split("## Reading these numbers")[1])


if __name__ == "__main__":
    unittest.main()
