"""T033 (F4): a park the cruise log leaves open ends at the first bracket any record began after it — or is unknown,
never *until accepted*."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from elapsed_fixture import FEATURE, commit, entry, graph, project, record, register, stamp, summaries, write

sys.dont_write_bytecode = True

SPLIT = f"specs/{FEATURE}/story-split.md"
REGISTER = f"specs/{FEATURE}/slices/README.md"


def row(number: int, started: str, ended: str, last: str) -> str:
    return json.dumps({"iteration": number, "started": stamp(1, started), "ended": stamp(1, ended),
                       "last_line": last}) + "\n"


class OpenParkTest(unittest.TestCase):
    def setUp(self) -> None:
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.repo = repo = project(Path(self.scratch.name))
        write(repo, SPLIT, graph([("S1", []), ("S2", [])]))
        commit(repo, stamp(1, "07:00:00"), "split", SPLIT)
        write(repo, "specs/cruise-log.jsonl", row(1, "08:00:00", "10:00:00", "cruise: continue")
              + row(2, "10:00:00", "11:00:00", "cruise: stopped: human"))

    def accept(self, mine: dict, other: dict | None = None) -> dict:
        paths = [record(self.repo, "S2", mine)]
        if other:
            paths.append(record(self.repo, "S1", other))
        write(self.repo, REGISTER, register(["S2"]))
        commit(self.repo, stamp(1, "18:00:00"), "S2 done", REGISTER, *paths)
        return summaries(self.repo)["S2"]

    def test_e1_the_park_ends_at_the_first_bracket_begun_after_it(self) -> None:
        found = self.accept(entry("implement", stamp(1, "13:00:00"), stamp(1, "14:00:00")))
        self.assertEqual(found["unattributed_person"], 2 * 3600)  # 11:00 -> 13:00, not -> 18:00
        self.assertIn("first bracket begun after it", found["read_from"]["unattributed_person"])
        self.assertIn(stamp(1, "13:00:00"), found["read_from"]["unattributed_person"])

    def test_e2_a_bracket_of_another_record_ends_it_too(self) -> None:
        found = self.accept(entry("implement", stamp(1, "15:00:00"), stamp(1, "16:00:00")),
                            entry("plan", stamp(1, "12:00:00"), stamp(1, "12:30:00")))
        self.assertEqual(found["unattributed_person"], 3600)

    def test_e3_with_no_bracket_after_it_the_wait_is_unknown_saying_why(self) -> None:
        found = self.accept(entry("implement", stamp(1, "09:00:00"), stamp(1, "10:30:00")))
        for figure in (*(found["waiting"][cause] for cause in ("review", "worker", "unattributed")),
                       found["unattributed_person"]):
            self.assertIn("no bracket of any record began after it", figure["unknown"])
        self.assertNotIn("until accepted", json.dumps(found["read_from"]))

    def test_e4_a_log_out_of_time_order_makes_review_worker_and_unattributed_unknown_naming_the_row(self) -> None:
        """A9: a park row that ended 11:00 followed by a row that started 09:30."""
        write(self.repo, "specs/cruise-log.jsonl", row(1, "08:00:00", "10:00:00", "cruise: continue")
              + row(2, "10:00:00", "11:00:00", "cruise: stopped: human")
              + row(3, "09:30:00", "12:00:00", "cruise: continue"))
        found = self.accept(entry("implement", stamp(1, "13:00:00"), stamp(1, "14:00:00")))
        for figure in (*(found["waiting"][cause] for cause in ("review", "worker", "unattributed")),
                       found["unattributed_person"]):
            self.assertIn("out of time order", figure["unknown"])
            self.assertIn("row 2", figure["unknown"])


if __name__ == "__main__":
    unittest.main()
