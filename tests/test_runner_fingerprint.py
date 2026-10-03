"""The fingerprint is path and content, and each file under `specs/` is read once while its record stands (D57;
AC-S02-12 to -21).

`fingerprint()` is what the stuck detector compares and what a parked run polls. The probe of
`test_runner_controls` loads the runner's script in a child under the audit hook and counts what a call opened,
with the record's clock put ten seconds on so that files written a moment ago are older than its margin; nothing
here is timed. A hold is shown to have teeth by making the record rest on size and modification time alone.
"""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from support import FactoryTestCase
from test_cruise_runner import cruise, enable, fake_harness, logged
from test_runner_controls import probe

from slipwai.project.cruise import LOG

FILES = {"specs/001/spec.md": "one\n", "specs/001/plan.md": "two\n", "specs/notes/a.txt": "three\n",
         "specs/notes/b.txt": "four\n", "specs/top.md": "five\n"}
EXCLUDED = {"specs/cruise-log.jsonl": "{}\n", "specs/cruise-checkpoint.md": "# checkpoint\n"}


def populate(repo: Path) -> list[str]:
    """Files under `specs/`, and the two the fingerprint leaves out; returns the ones it covers, sorted."""
    for name, text in {**FILES, **EXCLUDED}.items():
        (repo / name).parent.mkdir(parents=True, exist_ok=True)
        (repo / name).write_text(text)
    return sorted(FILES)


class RunnerFingerprintTest(FactoryTestCase):
    def test_a_later_call_over_a_tree_written_long_ago_opens_no_file_under_specs_and_returns_the_same(self) -> None:
        """AC-S02-12, -13 and -21: the first call opens each file under `specs/` but the log and the checkpoint
        exactly once; the second opens none and agrees, and so does the fiftieth — a count that does not depend on
        the call's number."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "reads", "standard", "python")
            covered = populate(repo)
            seen = probe(repo, """
cruise.SPECS_RECORD.clock = later()
first = cruise.fingerprint(); first_reads = opened("specs")
second = cruise.fingerprint(); second_reads = opened("specs")
calls = [cruise.fingerprint() for _ in range(48)]
result = {"first_reads": first_reads, "second_reads": second_reads, "fiftieth_reads": opened("specs"),
          "same": all(each == first for each in [second, *calls]), "shape": len(first)}""")
        self.assertEqual(seen["first_reads"], covered)
        self.assertEqual(seen["second_reads"], [])
        self.assertEqual(seen["fiftieth_reads"], [])
        self.assertTrue(seen["same"])
        self.assertEqual(seen["shape"], 16, "the field keeps its 16 hex characters")

    def test_a_touched_or_rewritten_file_is_read_alone_once_and_the_value_does_not_move(self) -> None:
        """AC-S02-14: touching a file, or writing the bytes it has, is not progress."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "touch", "standard", "python")
            populate(repo)
            seen = probe(repo, """
cruise.SPECS_RECORD.clock = later()
first = cruise.fingerprint(); opened()
os.utime("specs/top.md")
touched = cruise.fingerprint(); touched_reads = opened("specs")
settled = cruise.fingerprint(); settled_reads = opened("specs")
same = open("specs/notes/a.txt", "rb").read()
with open("specs/notes/a.txt", "wb") as handle: handle.write(same)
opened()
rewritten = cruise.fingerprint(); rewritten_reads = opened("specs")
settled_again = cruise.fingerprint(); settled_again_reads = opened("specs")
result = {"touched": touched_reads, "settled": settled_reads, "rewritten": rewritten_reads,
          "settled_again": settled_again_reads, "same": first == touched == settled == rewritten == settled_again}""")
        self.assertEqual(seen["touched"], ["specs/top.md"])
        self.assertEqual(seen["settled"], [])
        self.assertEqual(seen["rewritten"], ["specs/notes/a.txt"])
        self.assertEqual(seen["settled_again"], [])
        self.assertTrue(seen["same"])

    def test_a_file_written_within_the_margin_of_its_read_is_read_again_and_the_value_is_the_same(self) -> None:
        """AC-S02-17: with the record taken as of ten seconds on, a file whose modification time is one second short
        of that moment is not vouched for; it is opened at every call until it is older, and the value holds."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "window", "standard", "python")
            populate(repo)
            seen = probe(repo, """
cruise.SPECS_RECORD.clock = later()
near = time.time_ns() + 9 * 10**9
os.utime("specs/top.md", ns=(near, near))
first = cruise.fingerprint(); opened()
second = cruise.fingerprint(); second_reads = opened("specs")
third = cruise.fingerprint(); third_reads = opened("specs")
result = {"second": second_reads, "third": third_reads, "same": first == second == third}""")
        self.assertEqual((seen["second"], seen["third"]), (["specs/top.md"], ["specs/top.md"]))
        self.assertTrue(seen["same"])

    def test_hold_a_same_size_rewrite_with_different_bytes_changes_the_value_even_with_its_time_restored(self) -> None:
        """AC-S02-15 (hold; today's value is of the bytes): the modification time put back leaves the change time
        to show it — skipped where the platform reports none."""
        if os.name == "nt":
            self.skipTest("Windows reports no change time, so a restored modification time is not seen there")
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "rewrite", "standard", "python")
            populate(repo)
            seen = probe(repo, """
cruise.SPECS_RECORD.clock = later()
first = cruise.fingerprint()
status = os.stat("specs/top.md")
with open("specs/top.md", "wb") as handle: handle.write(b"FIVE\\n")
moved = cruise.fingerprint()
os.utime("specs/top.md", ns=(status.st_atime_ns, status.st_mtime_ns))
with open("specs/notes/b.txt", "rb") as handle: data = handle.read()
status = os.stat("specs/notes/b.txt")
with open("specs/notes/b.txt", "wb") as handle: handle.write(b"FOUR\\n")
os.utime("specs/notes/b.txt", ns=(status.st_atime_ns, status.st_mtime_ns))
restored = cruise.fingerprint()
result = {"size": len(data) == len(b"FOUR\\n"), "moved": moved != first, "restored": restored != moved}""")
        self.assertTrue(seen["size"])
        self.assertTrue(seen["moved"], "different bytes of the same size change the value")
        self.assertTrue(seen["restored"], "and so do they with the modification time put back")

    def test_a_file_added_removed_or_renamed_changes_the_value_and_a_removed_files_record_is_dropped(self) -> None:
        """AC-S02-16: the path is in the digest; the record holds one entry per file under `specs/` and sheds a
        file that is gone."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "paths", "standard", "python")
            covered = populate(repo)
            seen = probe(repo, """
cruise.SPECS_RECORD.clock = later()
first = cruise.fingerprint(); held = len(cruise.SPECS_RECORD)
open("specs/added.md", "w").write("new\\n")
added = cruise.fingerprint(); held_added = len(cruise.SPECS_RECORD)
os.remove("specs/added.md")
removed = cruise.fingerprint(); held_removed = len(cruise.SPECS_RECORD)
os.rename("specs/top.md", "specs/renamed.md")
renamed = cruise.fingerprint(); held_renamed = len(cruise.SPECS_RECORD)
result = {"held": [held, held_added, held_removed, held_renamed],
          "values": [first != added, added != removed, removed == first, renamed != first]}""")
        self.assertEqual(seen["held"], [len(covered), len(covered) + 1, len(covered), len(covered)])
        self.assertEqual(seen["values"], [True, True, True, True])

    def test_hold_the_same_tree_gives_two_runner_processes_the_same_value(self) -> None:
        """AC-S02-18 (hold): the value is of the tree, never of the process. `test_cruise_runner`'s *no progress
        since iteration 2* across two runs is the other half and is run with no edit."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "twice", "standard", "python")
            populate(repo)
            values = [probe(repo, "result = cruise.fingerprint()") for _ in range(2)]
        self.assertEqual(values[0], values[1])

    def test_hold_a_commit_or_a_change_outside_specs_moves_the_value_and_opens_no_file_under_specs(self) -> None:
        """AC-S02-19 (hold for the value; the second call's reads are the count)."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "outside", "standard", "python")
            populate(repo)
            seen = probe(repo, """
cruise.SPECS_RECORD.clock = later()
first = cruise.fingerprint(); opened()
open("apps/stray.txt", "w").write("x\\n")
changed = cruise.fingerprint(); changed_reads = opened("specs")
import subprocess
subprocess.run(["git", "add", "-A"], check=True)
subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "x"], check=True)
committed = cruise.fingerprint(); committed_reads = opened("specs")
result = {"moved": [first != changed, changed != committed], "reads": [changed_reads, committed_reads]}""")
        self.assertEqual(seen["moved"], [True, True])
        self.assertEqual(seen["reads"], [[], []])

    def test_hold_a_log_that_carries_earlier_values_is_read_and_the_run_parks_on_values_of_its_own(self) -> None:
        """AC-S02-20 (hold): two entries carrying fingerprints the earlier code wrote do not make the next two
        iterations stuck; the run parks once `stuck_after` values of its own are equal — here after iteration 4,
        naming iteration 3 as the first of them."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "older", "standard", "python")
            enable(repo, stuck_after="2", unblock="park", max_iterations="5")
            (repo / LOG).parent.mkdir(exist_ok=True)
            (repo / LOG).write_text("".join(json.dumps({"iteration": n, "last_line": "cruise: continue",
                                                        "fingerprint": "0123456789abcdef"}) + "\n" for n in (1, 2)))
            env = fake_harness(Path(directory), 'echo "cruise: continue"')
            parked = cruise(repo, "run", "--no-park", env=env)
            self.assertEqual(parked.returncode, 3, parked.stdout + parked.stderr)
            self.assertIn("cruise: parked — no progress since iteration 3", parked.stdout)
            self.assertEqual([entry["iteration"] for entry in logged(repo)], [1, 2, 3, 4])


if __name__ == "__main__":
    unittest.main()
