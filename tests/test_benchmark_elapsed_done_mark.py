"""AC-S39-1: a done mark is found by what the register holds at each commit, not by how often an id appears."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from elapsed_fixture import FEATURE, commit, entry, graph, project, record, register, stamp, summaries, write

sys.dont_write_bytecode = True

SPLIT = f"specs/{FEATURE}/story-split.md"
REGISTER = f"specs/{FEATURE}/slices/README.md"
NOTE = "\nNext up: S1-a.\n"


class NetZeroCommitTest(unittest.TestCase):
    """The row is added and a prose mention of the same id is removed in one commit: the id's count is unchanged."""

    def setUp(self) -> None:
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.repo = project(Path(self.scratch.name))
        write(self.repo, SPLIT, graph([("S1-a", [])]))
        commit(self.repo, stamp(1), "split", SPLIT)
        write(self.repo, REGISTER, register([]) + NOTE)
        commit(self.repo, stamp(2), "register: next up", REGISTER)
        write(self.repo, REGISTER, register(["S1-a"]))
        self.accepted = commit(self.repo, stamp(3), "S1-a done", REGISTER)
        record(self.repo, "S1-a", entry("implement", stamp(1, "10:00:00"), stamp(1, "11:00:00")))

    def test_e1_a_later_note_naming_the_id_is_not_the_done_mark(self) -> None:
        write(self.repo, REGISTER, register(["S1-a"]) + "\nS1-a merged clean.\n")
        commit(self.repo, stamp(5), "a note", REGISTER)
        found = summaries(self.repo)["S1-a"]
        self.assertEqual(found["moments"]["accepted"], stamp(3))
        self.assertEqual(found["read_from"]["accepted"], f"{self.accepted} (slices/README.md: S1-a)")
        self.assertEqual(found["elapsed"], 2 * 86400)

    def test_e2_with_no_later_commit_the_slice_reads_accepted_not_open(self) -> None:
        found = summaries(self.repo)["S1-a"]
        self.assertEqual((found["moments"]["accepted"], found["elapsed"]), (stamp(3), 2 * 86400))


if __name__ == "__main__":
    unittest.main()
