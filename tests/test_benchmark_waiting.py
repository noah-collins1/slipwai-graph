"""R2: waiting by cause — what a slice's elapsed time was spent on besides work — adds up to elapsed, to the second."""
from __future__ import annotations

import json
import re
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
CAUSES = ("dependency", "worker", "review", "integration", "unattributed")


def park(iteration: int, started: str, ended: str, last: str) -> str:
    return json.dumps({"iteration": iteration, "started": started, "ended": ended, "last_line": last}) + "\n"


class WaitingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.repo = project(Path(self.scratch.name))

    def found(self, ident: str = "S2") -> dict:
        found = summaries(self.repo)[ident]
        if isinstance(found["elapsed"], int):
            parts = found["worked_seconds"] + sum(found["waiting"][cause] for cause in CAUSES)
            self.assertEqual(parts, found["elapsed"], f"worked and the causes do not add up: {found}")
        return found

    def accept(self, *stages: dict, row: str = stamp(2, "18:00:00")) -> None:
        """S2 after S1 in the split (ready day 1 09:00); its row at `row`."""
        write(self.repo, SPLIT, graph([("S1", []), ("S2", [])]))
        commit(self.repo, stamp(1), "split", SPLIT)
        path = record(self.repo, "S2", *stages)
        write(self.repo, REGISTER, register(["S2"]))
        commit(self.repo, row, "S2 done", REGISTER, path)

    def test_e1_a_sibling_merge_the_own_merge_and_a_gate_each_take_their_own_seconds(self) -> None:
        repo = self.repo
        write(repo, SPLIT, graph([("S1", []), ("S2", [])]))
        commit(repo, stamp(1), "split", SPLIT)
        path = record(
            repo,
            "S2",
            entry("implement", stamp(2, "10:00:00"), stamp(2, "11:00:00")),
            entry("demo", stamp(2, "12:00:00"), stamp(2, "12:30:00"), outcome="accepted", driver="human"),
            entry("gate", stamp(2, "16:10:00"), stamp(2, "16:40:00")),
            entry("adversary", stamp(2, "17:00:00"), stamp(2, "17:30:00")),
        )
        commit(repo, stamp(2, "13:00:00"), "records", path)
        sibling = merge(repo, stamp(2, "15:00:00"), "S1")
        own = merge(repo, stamp(2, "16:00:00"), "S2")
        write(repo, REGISTER, register(["S2"]))
        commit(repo, stamp(2, "18:00:00"), "S2 done", REGISTER)
        found = self.found()
        self.assertEqual(found["elapsed"], 33 * 3600)
        # worked: implement, demo and the adversary fix; the gate is integration's
        self.assertEqual(found["worked_seconds"], 3600 + 1800 + 1800)
        self.assertEqual(found["waiting"]["dependency"], 2.5 * 3600)  # demo accepted -> the sibling's merge
        self.assertEqual(found["waiting"]["integration"], 2 * 3600 - 1800)  # merge -> row, less the bracketed fix
        self.assertEqual((found["waiting"]["review"], found["waiting"]["worker"]), (0, 0))
        self.assertEqual(found["waiting"]["unattributed"], 33 * 3600 - 7200 - 9000 - 5400)
        self.assertIn(sibling, found["read_from"]["dependency"])
        self.assertIn(own, found["read_from"]["integration"])
        self.assertIn("gate", found["read_from"]["integration"])
        self.assertIn("none present", found["read_from"]["worker"])
        self.assertIn("none present", found["read_from"]["review"])

    def test_e2_a_park_is_review_and_the_cruise_log_spans_the_worker_wait(self) -> None:
        self.accept(entry("implement", stamp(1, "10:00:00"), stamp(1, "11:00:00")), row=stamp(1, "20:00:00"))
        write(
            self.repo,
            "specs/cruise-log.jsonl",
            park(1, stamp(1, "09:30:00"), stamp(1, "12:00:00"), "cruise: stopped: human")
            + park(2, stamp(1, "14:00:00"), stamp(1, "18:00:00"), "cruise: continue"),
        )
        found = self.found()
        self.assertEqual(found["elapsed"], 11 * 3600)
        self.assertEqual(found["waiting"]["review"], 2 * 3600)
        self.assertEqual(found["waiting"]["worker"], 8.5 * 3600 - 2 * 3600 - 3600)
        self.assertEqual(found["waiting"]["unattributed"], 1800 + 2 * 3600)
        self.assertIn("specs/cruise-log.jsonl", found["read_from"]["review"])
        self.assertIn("specs/cruise-log.jsonl", found["read_from"]["worker"])

    def test_e3_no_second_is_taken_twice_where_causes_overlap(self) -> None:
        """A park inside merge -> row, a skipper nested in an implement, a demo with no driver: each second once."""
        repo = self.repo
        write(repo, SPLIT, graph([("S2", [])]))
        commit(repo, stamp(1), "split", SPLIT)
        path = record(
            repo,
            "S2",
            entry("implement", stamp(1, "10:00:00"), stamp(1, "11:00:00")),
            entry("skipper", stamp(1, "10:10:00"), stamp(1, "10:20:00")),
            entry("demo", stamp(1, "12:00:00"), stamp(1, "13:00:00"), outcome="accepted"),
        )
        commit(repo, stamp(1, "13:30:00"), "records", path)
        merge(repo, stamp(1, "14:00:00"), "S2")
        write(repo, REGISTER, register(["S2"]))
        commit(repo, stamp(1, "18:00:00"), "S2 done", REGISTER)
        write(repo, "specs/cruise-log.jsonl", park(1, stamp(1, "09:00:00"), stamp(1, "15:00:00"), "stopped: human")
              + park(2, stamp(1, "16:00:00"), stamp(1, "19:00:00"), "cruise: continue"))
        found = self.found()
        self.assertEqual(found["worked_seconds"], 3600)  # the skipper counts once; the person's demo is review's
        self.assertEqual(found["waiting"]["integration"], 4 * 3600)  # 14:00 -> 18:00
        # the park (15:00-16:00) lies inside integration, which claims it first; the person's demo is review's
        self.assertEqual(found["waiting"]["review"], 3600)
        self.assertEqual((found["waiting"]["worker"], found["waiting"]["unattributed"]), (3 * 3600, 0))

    def test_e4_a_wait_for_a_patch_is_review_because_no_record_says_otherwise(self) -> None:
        self.accept(entry("implement", stamp(1, "10:00:00"), stamp(1, "11:00:00")), row=stamp(1, "20:00:00"))
        write(self.repo, "specs/cruise-log.jsonl", park(1, stamp(1, "09:00:00"), stamp(1, "13:00:00"), "stopped: human")
              + park(2, stamp(1, "15:00:00"), stamp(1, "16:00:00"), "cruise: continue"))
        found = self.found()
        self.assertEqual((found["waiting"]["dependency"], found["waiting"]["review"]), (0, 2 * 3600))

    def test_an_open_slice_has_no_worked_figure_and_no_waiting(self) -> None:
        write(self.repo, SPLIT, graph([("S2", [])]))
        commit(self.repo, stamp(1), "split", SPLIT)
        record(self.repo, "S2", entry("implement", stamp(1, "10:00:00"), stamp(1, "11:00:00")))
        found = summaries(self.repo)["S2"]
        reason = {"unknown": f"open since {stamp(1)}"}
        self.assertEqual(found.get("worked_seconds"), reason)
        self.assertEqual(found.get("waiting"), {cause: reason for cause in CAUSES})

    def test_the_waiting_table_follows_the_slice_table_and_says_each_unknown_once(self) -> None:
        self.accept(entry("implement", stamp(1, "10:00:00"), stamp(1, "11:00:00")), row=stamp(1, "20:00:00"))
        record(self.repo, "S3", entry("implement", stamp(1, "10:00:00"), stamp(1, "11:00:00")))
        out = bench(self.repo).stdout
        lines = out.splitlines()
        head = next(index for index, line in enumerate(lines) if "unattributed" in line)
        split = [re.split(r"\s{2,}", line.strip()) for line in lines[head:head + 4]]
        self.assertEqual(split[0], ["slice", "elapsed", "worked", "dependency", "worker", "review", "integration",
                                    "unattributed"])
        cells = {cells[0]: cells for cells in split[1:]}
        self.assertEqual(cells["S2"], ["S2", "11h00m", "1h00m", "0s", "0s", "0s", "0s", "10h00m"])
        self.assertEqual(cells["S3"][2:], ["unknown"] * 6)
        self.assertEqual(out.count("S3: elapsed unknown"), 1)
        self.assertIn("S3: elapsed unknown — S3 is in neither", out)
        self.assertLess(out.index("slice  delegate/cycle"), out.index("unattributed"))
        page = bench(self.repo, "overview", FEATURE)
        self.assertEqual(page.returncode, 0, page.stderr)
        self.assertIn("unattributed", (self.repo / f"specs/{FEATURE}/benchmark.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
