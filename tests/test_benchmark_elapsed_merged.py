"""T032 (F3): *merged* is the slice's own merge into the integration branch, never a catch-up merge into the slice."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from elapsed_fixture import (
    FEATURE,
    bench,
    commit,
    entry,
    git,
    graph,
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


class MergedTest(unittest.TestCase):
    def setUp(self) -> None:
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.repo = repo = project(Path(self.scratch.name))
        write(repo, SPLIT, graph([("S2", [])]))
        commit(repo, stamp(1), "split", SPLIT)
        self.path = record(repo, "S2", entry("implement", stamp(3, "09:00:00"), stamp(3, "10:00:00")),
                           entry("demo", stamp(3, "12:00:00"), stamp(3, "12:30:00"), outcome="accepted",
                                 driver="human"))
        commit(repo, stamp(3, "10:30:00"), "records", self.path)

    def merge(self, branch: str, into: str, subject: str, when: str) -> None:
        git(self.repo, "checkout", "-q", into)
        git(self.repo, "merge", "-q", "--no-ff", "-m", subject, branch, when=when)

    def lay(self, real: bool = True) -> None:
        repo = self.repo
        git(repo, "checkout", "-q", "-b", "slice/S2")
        write(repo, "work.txt", "w")
        commit(repo, stamp(3, "10:40:00"), "work on S2", "work.txt")
        git(repo, "checkout", "-q", "main")
        commit(repo, stamp(3, "10:50:00"), "main moves")
        self.merge("main", "slice/S2", "Merge branch 'main' into slice/S2", stamp(3, "11:00:00"))
        if real:
            self.merge("slice/S2", "main", "Merge branch 'slice/S2' into main", stamp(3, "18:00:00"))
            write(repo, REGISTER, register(["S2"]))
            commit(repo, stamp(3, "18:10:00"), "S2 done", REGISTER)

    def test_e1_a_catch_up_merge_into_the_slice_is_not_the_slices_merge(self) -> None:
        self.lay()
        found = summaries(self.repo)["S2"]
        self.assertEqual(found["moments"]["merged"], stamp(3, "18:00:00"))
        self.assertIn("merged 2026-10-03T18:00:00Z", self.overview())

    def test_e2_with_only_the_catch_up_merge_the_slice_has_not_merged(self) -> None:
        self.lay(real=False)
        git(self.repo, "checkout", "-q", "main")
        write(self.repo, REGISTER, register(["S2"]))
        commit(self.repo, stamp(3, "18:10:00"), "S2 done", REGISTER)
        self.assertNotIn("merged", summaries(self.repo)["S2"]["moments"])

    def test_e3_read_from_the_slices_own_branch_the_catch_up_merge_is_still_not_a_merge(self) -> None:
        self.lay(real=False)
        git(self.repo, "checkout", "-q", "slice/S2")
        self.assertNotIn("merged", summaries(self.repo)["S2"]["moments"])

    def land(self, branch: str, subject: str, when: str) -> None:
        """A branch with one commit, merged into `main` with this subject."""
        git(self.repo, "checkout", "-q", "-b", branch)
        write(self.repo, f"{branch.replace('/', '-')}-{when}.txt", branch)
        git(self.repo, "add", "-A", "--", ".")
        git(self.repo, "commit", "-q", "-m", f"work {branch}", when=when)
        self.merge(branch, "main", subject, when)

    def merged_of(self, ident: str) -> object:
        return summaries(self.repo)[ident]["moments"].get("merged")

    def accept(self, ident: str, when: str) -> None:
        git(self.repo, "checkout", "-q", "main")
        write(self.repo, REGISTER, register([ident]))
        commit(self.repo, when, f"{ident} done", REGISTER)

    def test_e4_a_merge_subject_naming_the_slice_in_prose_is_not_its_merge(self) -> None:
        """A1: `Merge slice/S2-b … ahead of slice/S1-a` is S2-b's merge, not S1-a's."""
        repo = self.repo
        write(repo, SPLIT, graph([("S1-a", []), ("S2-b", [])]))
        commit(repo, stamp(2), "split", SPLIT)
        for ident in ("S1-a", "S2-b"):
            record(repo, ident, entry("implement", stamp(3, "09:00:00"), stamp(3, "10:00:00")))
        commit(repo, stamp(3, "10:30:00"), "records", f"specs/{FEATURE}/slices/S1-a/benchmark.json",
               f"specs/{FEATURE}/slices/S2-b/benchmark.json")
        self.land("slice/S2-b", "Merge slice/S2-b into main — merged ahead of slice/S1-a, which waits",
                  stamp(3, "14:00:00"))
        self.accept("S1-a", stamp(5))
        self.assertIsNone(self.merged_of("S1-a"))
        self.assertEqual(self.merged_of("S2-b"), stamp(3, "14:00:00"))

    def test_e5_a_longer_branch_name_is_not_the_slices_branch(self) -> None:
        self.land("slice/S2-v2", "Merge branch 'slice/S2-v2' into main", stamp(3, "14:00:00"))
        self.accept("S2", stamp(5))
        self.assertIsNone(self.merged_of("S2"))

    def test_e6_the_plain_merge_subject_is_the_slices_merge(self) -> None:
        self.land("slice/S2", "Merge slice/S2 into main — prose", stamp(3, "14:00:00"))
        self.accept("S2", stamp(5))
        self.assertEqual(self.merged_of("S2"), stamp(3, "14:00:00"))

    def test_e7_a_merge_later_merged_again_is_the_last_one_not_after_accepted(self) -> None:
        self.land("slice/S2", "Merge branch 'slice/S2' into main", stamp(3, "14:00:00"))
        git(self.repo, "checkout", "-q", "slice/S2")
        write(self.repo, "more.txt", "m")
        commit(self.repo, stamp(4, "13:00:00"), "more work", "more.txt")
        self.merge("slice/S2", "main", "Merge branch 'slice/S2' into main (again)", stamp(4, "14:00:00"))
        self.accept("S2", stamp(4, "20:00:00"))
        self.assertEqual(self.merged_of("S2"), stamp(4, "14:00:00"))

    def overview(self) -> str:
        bench(self.repo, "overview", FEATURE)
        return (self.repo / f"specs/{FEATURE}/benchmark.md").read_text(encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
