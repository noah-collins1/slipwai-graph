"""T036 (D167): review and dependency are read only from a record that says a person; a park nobody gave a cause is
*a person, cause unrecorded*, inside unattributed and named beside `waiting`."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from elapsed_fixture import FEATURE, bench, commit, entry, graph, project, record, register, stamp, summaries, write

sys.dont_write_bytecode = True

SPLIT = f"specs/{FEATURE}/story-split.md"
REGISTER = f"specs/{FEATURE}/slices/README.md"
KEYS = ("dependency", "worker", "review", "integration", "unattributed")


def row(number: int, started: str, ended: str, last: str) -> str:
    return json.dumps({"iteration": number, "started": stamp(1, started), "ended": stamp(1, ended),
                       "last_line": last}) + "\n"


class PersonTest(unittest.TestCase):
    def setUp(self) -> None:
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.repo = repo = project(Path(self.scratch.name))
        write(repo, SPLIT, graph([("S2", [])]))
        commit(repo, stamp(1, "07:00:00"), "split", SPLIT)

    def accept(self, *stages: dict, log: str | None = None) -> dict:
        path = record(self.repo, "S2", *stages)
        if log is not None:
            write(self.repo, "specs/cruise-log.jsonl", log)
        write(self.repo, REGISTER, register(["S2"]))
        commit(self.repo, stamp(1, "20:00:00"), "S2 done", REGISTER, path)
        found = summaries(self.repo)["S2"]
        if all(isinstance(figure, int) for figure in (found["elapsed"], *found["waiting"].values())):  # the invariant
            parts = found["worked_seconds"] + sum(found["waiting"][key] for key in KEYS)
            self.assertEqual(parts, found["elapsed"], found)
        self.assertEqual(set(found["waiting"]), set(KEYS))
        return found

    def test_e1_a_cut_off_demo_is_stage_time_not_review(self) -> None:
        cut = entry("demo", stamp(1, "11:00:00"), stamp(1, "12:00:00"))
        cut["signals"] = {}
        cut["cut_off"] = "iteration 3 ended with the entry open"
        found = self.accept(cut)
        self.assertEqual(found["waiting"]["review"], 0)
        self.assertEqual(found["worked_seconds"], 3600)
        self.assertIn("S2 demo: stage time ends at its recorded end", bench(self.repo).stdout)

    def test_e2_a_drive_demo_closed_with_an_outcome_and_no_driver_is_review(self) -> None:
        found = self.accept(entry("demo", stamp(1, "11:00:00"), stamp(1, "12:00:00"), outcome="behaviour"))
        self.assertEqual(found["waiting"]["review"], 3600)
        self.assertEqual(found["read_from"]["review"], "a person's demo: outcome recorded, no driver")

    def test_e3_a_park_is_a_person_inside_unattributed_not_review_or_dependency_or_worker(self) -> None:
        found = self.accept(entry("implement", stamp(1, "09:00:00"), stamp(1, "09:30:00")),
                            log=row(1, "08:00:00", "10:00:00", "cruise: stopped: human")
                            + row(2, "12:00:00", "13:00:00", "cruise: continue"))
        self.assertEqual((found["waiting"]["review"], found["waiting"]["dependency"]), (0, 0))
        self.assertEqual(found["unattributed_person"], 7200)
        self.assertGreaterEqual(found["waiting"]["unattributed"], 7200)
        self.assertIn("none present: no record names a park's cause", found["read_from"]["review"])
        self.assertIn("a person held the run, cause unrecorded", bench(self.repo).stdout)
        # worker holds the rest of the log's span, not the park
        self.assertEqual(found["waiting"]["worker"], 20 * 3600 - 8 * 3600 - 1800 - 7200)

    def test_e4_a_parked_row_is_claimed_the_same_way(self) -> None:
        found = self.accept(entry("implement", stamp(1, "09:00:00"), stamp(1, "09:30:00")),
                            log=row(1, "08:00:00", "10:00:00", "cruise: parked: a person's approval")
                            + row(2, "12:00:00", "13:00:00", "cruise: continue"))
        self.assertEqual(found["unattributed_person"], 7200)

    def test_e5_a_torn_log_line_makes_the_person_figure_unknown_with_review_worker_and_unattributed(self) -> None:
        whole = row(1, "08:00:00", "10:00:00", "cruise: stopped: human")
        found = self.accept(entry("implement", stamp(1, "09:00:00"), stamp(1, "09:30:00")),
                            log=whole[:50] + "\n" + row(2, "12:00:00", "13:00:00", "cruise: continue"))
        for figure in (found["unattributed_person"], found["waiting"]["unattributed"]):
            self.assertIn("line 1", figure["unknown"])

    def test_e6_with_no_log_the_person_figure_is_zero_and_says_none_present(self) -> None:
        found = self.accept(entry("implement", stamp(1, "09:00:00"), stamp(1, "09:30:00")))
        self.assertEqual(found["unattributed_person"], 0)
        self.assertIn("none present", found["read_from"]["unattributed_person"])


if __name__ == "__main__":
    unittest.main()
