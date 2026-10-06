"""T031 of S14-result-contract (D161, B2): a stage that ended before the result contract reached the project owes
nothing, and `--hand-backs` and `make benchmark` say so instead of counting it.

The arrival is the author time of the earliest commit that added `hand_backs.py`, read from git by the script itself;
where git cannot tell, the stage is *could not tell*: said, not counted, never a finding. Each project here is a
temporary git repository whose scripts were committed at a chosen instant.
"""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any

from hand_backs_fixture import SCRIPTS, commit, git, run, scratch
from test_hand_backs_coverage import SLICE, benchmark, implement_block, project, stage, toolkit

ARRIVED = "2026-10-05T12:00:00Z"
BEFORE = stage("implement", "2026-10-05T10:00:00Z", "2026-10-05T11:59:59Z")
AFTER = stage("converge", "2026-10-05T13:00:00Z", "2026-10-05T13:10:00Z")


class ArrivalTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)

    def verb(self, stages: list[dict[str, Any]], record: str | None = None, arrived: str | None = ARRIVED,
             **options: str) -> list[str]:
        repo = project(self.directory.name, stages, record, arrived)
        if options.get("committer"):
            git(repo, "commit", "-q", "--amend", "--no-edit", committer=options["committer"])
        result = run(repo, "--hand-backs", SLICE)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        return result.stdout.splitlines()

    def test_a_stage_that_ended_before_the_arrival_owes_nothing_and_says_so(self) -> None:
        lines = self.verb([BEFORE, AFTER])
        self.assertRegex(lines[0], r"^hand-backs: implement 2026-10-05T10:00:00Z: predates the result contract "
                                   r"\([0-9a-f]{7,}, 2026-10-05\) — owes nothing$")
        self.assertIn("converge 2026-10-05T13:00:00Z drive-converge: nothing recorded", lines[1])
        self.assertEqual("hand-backs: with a result contract: 0 of 1; 1 predate the contract", lines[-1])

    def test_a_stage_that_ended_at_the_arrival_or_straddles_it_still_owes(self) -> None:
        at = stage("implement", "2026-10-05T11:00:00Z", ARRIVED)
        across = stage("converge", "2026-10-05T11:30:00Z", "2026-10-05T12:30:00Z")
        lines = self.verb([at, across])
        self.assertEqual("hand-backs: with a result contract: 0 of 2", lines[-1])
        self.assertFalse(any("predates" in line for line in lines), lines)

    def test_a_stage_after_the_arrival_with_a_block_is_held_as_before(self) -> None:
        lines = self.verb([stage("implement", "2026-10-05T17:00:00Z", "2026-10-05T17:10:00Z")], implement_block())
        self.assertEqual("hand-backs: with a result contract: 1 of 1", lines[-1])

    def test_the_cut_off_is_the_author_time_not_the_committer_time(self) -> None:
        # A rebase moves the committer time later; a stage between the two must still owe.
        lines = self.verb([AFTER], committer="2026-10-06T00:00:00Z")
        self.assertEqual("hand-backs: with a result contract: 0 of 1", lines[-1])

    def test_the_earliest_adding_commit_is_the_arrival(self) -> None:
        repo = project(self.directory.name, [BEFORE], arrived=ARRIVED)
        (repo / "scripts/hand_backs.py").unlink()
        git(repo, "commit", "-q", "-am", "drop", author="2026-10-05T14:00:00Z")
        shutil.copy(SCRIPTS / "hand_backs.py", repo / "scripts/hand_backs.py")
        commit(repo, "2026-10-05T15:00:00Z")
        self.assertIn("predates", run(repo, "--hand-backs", SLICE).stdout.splitlines()[0])

    def test_a_project_that_is_not_a_repository_could_not_tell_and_counts_nothing(self) -> None:
        lines = self.verb([BEFORE, AFTER], arrived=None)
        self.assertRegex(lines[0], r"^hand-backs: implement 2026-10-05T10:00:00Z: could not tell whether it predates "
                                   r"the result contract \(.*git.*\) — not counted$")
        self.assertEqual("hand-backs: with a result contract: 0 of 0; 2 could not tell — not counted", lines[-1])

    def test_a_module_no_commit_has_added_yet_says_what_to_commit(self) -> None:
        repo = project(self.directory.name, [AFTER], arrived=None)
        git(repo, "init", "-q")
        out = run(repo, "--hand-backs", SLICE).stdout.splitlines()
        self.assertIn("commit what slipwai migrate wrote, and this can tell", out[0])
        self.assertEqual("hand-backs: with a result contract: 0 of 0; 1 could not tell — not counted", out[-1])

    def test_a_shallow_clone_could_not_tell(self) -> None:
        origin = project(self.directory.name, [AFTER], arrived=ARRIVED)
        (origin / "README.md").write_text("two\n", encoding="utf-8")
        git(origin, "add", "-A")
        git(origin, "commit", "-q", "-m", "later", author="2026-10-06T00:00:00Z")
        clone = Path(self.directory.name + "-clone")
        self.addCleanup(shutil.rmtree, clone, True)
        git(origin, "clone", "-q", "--depth", "1", "file://" + str(origin), str(clone))
        out = run(clone, "--hand-backs", SLICE).stdout.splitlines()
        self.assertIn("shallow", out[0])
        self.assertEqual("hand-backs: with a result contract: 0 of 0; 1 could not tell — not counted", out[-1])

    def test_an_ended_that_does_not_parse_could_not_tell(self) -> None:
        odd = stage("implement", "2026-10-05T10:00:00Z", "yesterday")
        lines = self.verb([odd])
        self.assertIn("could not tell", lines[0])
        self.assertIn("ended", lines[0])
        self.assertEqual("hand-backs: with a result contract: 0 of 0; 1 could not tell — not counted", lines[-1])

    def test_a_project_in_a_subdirectory_of_the_repository_reads_its_own_module(self) -> None:
        sub = Path(self.directory.name) / "sub"
        sub.mkdir()
        project_ = scratch(str(sub))
        (project_ / "scripts/agents").mkdir()
        (project_ / SLICE / "benchmark.json").write_text(
            '{"feature": "f", "slice": "S1", "stages": [' + json.dumps(BEFORE) + "]}", encoding="utf-8")
        commit(project_, ARRIVED, root=Path(self.directory.name))
        self.assertIn("predates", run(project_, "--hand-backs", SLICE).stdout.splitlines()[0])

    def test_the_arrival_is_read_by_a_function_that_coverage_is_given_not_by_coverage(self) -> None:
        module = toolkit("hand_backs")
        stages = [BEFORE]
        self.assertEqual(0, module.coverage(stages, "", set(), None).predates)


class BenchmarkArrivalTest(unittest.TestCase):
    def test_every_slice_that_only_predates_is_one_line_and_no_per_slice_line(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = project(directory, [BEFORE], arrived=ARRIVED)
            second = repo / "specs/f/slices/S2"
            second.mkdir(parents=True)
            (second / "benchmark.json").write_text(
                '{"feature": "f", "slice": "S2", "stages": [' + json.dumps(BEFORE) + "]}", encoding="utf-8")
            out = benchmark(repo).stdout
        self.assertNotIn("S1: hand-backs", out)
        self.assertNotIn("S2: hand-backs", out)
        lines = [line for line in out.splitlines() if "ended before the result contract reached this project" in line]
        self.assertEqual(1, len(lines), out)
        self.assertRegex(lines[0], r"^\s*hand-backs: 2 stage\(s\) in 2 slice\(s\) ended before the result contract "
                                   r"reached this project \([0-9a-f]{7,}, 2026-10-05\) — not counted$")

    def test_a_slice_with_a_stage_after_the_arrival_keeps_its_own_line_and_its_count(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            out = benchmark(project(directory, [BEFORE, AFTER], arrived=ARRIVED)).stdout
        self.assertIn("S1: hand-backs with a result contract: 0 of 1", out)
        self.assertIn("hand-backs: 1 stage(s) in 1 slice(s) ended before", out)

    def test_where_git_cannot_tell_the_slice_line_says_so_and_there_is_no_cut_off_line(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            out = benchmark(project(directory, [BEFORE, AFTER], arrived=None)).stdout
        self.assertIn("S1: hand-backs with a result contract: 0 of 0; 2 could not tell — not counted", out)
        self.assertNotIn("ended before the result contract", out)


if __name__ == "__main__":
    unittest.main()
