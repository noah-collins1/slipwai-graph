"""R6 of S14-result-contract: what was handed back, per delegated stage.

`check-decisions.py --hand-backs <slice-dir>` lists each ended benchmark entry the transcript shows was delegated
against the record; `benchmark.py` carries the count per slice. Records are written by hand here: the harness's
transcripts are not under test, only what is read from `benchmark.json` and `hand-backs.md`.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any

from hand_backs_fixture import SCRIPTS, entry, run, scratch, valid

SLICE = "specs/f/slices/S1"
IMPLEMENT = "## 2026-10-05T17:01:02Z — drive-implement — implement"
BLOCK = {"delegate": "drive-implement", "status": "green"}


def stage(name: str, started: str, ended: str, delegated: bool = True, source: str | None = "claude") -> dict[str, Any]:
    return {"stage": name, "started": started, "ended": ended, "seconds": 600, "signals": {}, "delegated": delegated,
            "usage": {"source": source, "reason": None if source else "no transcript"}}


def project(directory: str, stages: list[dict[str, Any]], record: str | None = None) -> Path:
    repo = scratch(directory, record)
    (repo / "scripts/agents").mkdir()
    shutil.copy(SCRIPTS / "agents/benchmark.py", repo / "scripts/agents/benchmark.py")
    (repo / SLICE / "benchmark.json").write_text(
        json.dumps({"feature": "f", "slice": "S1", "stages": stages}), encoding="utf-8")
    return repo


def implement_block() -> str:
    return entry(valid() | BLOCK, IMPLEMENT)


def benchmark(repo: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["python3", "-B", "scripts/agents/benchmark.py"], cwd=repo, text=True, capture_output=True)


TWO = [stage("implement", "2026-10-05T17:00:00Z", "2026-10-05T17:10:00Z"),
       stage("converge", "2026-10-05T18:00:00Z", "2026-10-05T18:10:00Z")]


class CoverageVerbTest(unittest.TestCase):
    def verb(self, stages: list[dict[str, Any]], record: str | None = None) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory:
            return run(project(directory, stages, record), "--hand-backs", SLICE)

    def test_e1_two_delegated_entries_one_with_a_block_is_one_of_two(self) -> None:
        result = self.verb(TWO, "# Hand-backs — S1\n\n" + implement_block())
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual([
            "hand-backs: implement 2026-10-05T17:00:00Z drive-implement: block",
            "hand-backs: converge 2026-10-05T18:00:00Z: nothing recorded — a finding for converge",
            "hand-backs: with a result contract: 1 of 2"], result.stdout.splitlines())

    def test_e2_a_missing_entry_counts_in_the_total_and_not_the_count(self) -> None:
        record = "## 2026-10-05T18:05:00Z — drive-converge — converge\n\n- **Missing:** refused: out of budget\n\n"
        result = self.verb(TWO, implement_block() + record)
        lines = result.stdout.splitlines()
        self.assertIn("hand-backs: converge 2026-10-05T18:00:00Z: missing — refused: out of budget", lines)
        self.assertEqual("hand-backs: with a result contract: 1 of 2", lines[-1])

    def test_e3_an_entry_the_harness_could_not_attribute_is_neither_counted_nor_a_finding(self) -> None:
        stages = [stage("implement", "2026-10-05T17:00:00Z", "2026-10-05T17:10:00Z", source=None)]
        result = self.verb(stages)
        self.assertEqual([
            "hand-backs: implement 2026-10-05T17:00:00Z: the harness could not attribute its delegates — not counted",
            "hand-backs: with a result contract: 0 of 0"], result.stdout.splitlines())

    def test_e4_a_slice_with_no_record_is_nought_of_its_delegated_stages(self) -> None:
        result = self.verb(TWO)
        self.assertEqual("hand-backs: with a result contract: 0 of 2", result.stdout.splitlines()[-1])

    def test_e4_a_stage_run_in_this_context_or_still_open_is_not_listed(self) -> None:
        stages = [stage("gaps", "2026-10-05T16:00:00Z", "2026-10-05T16:10:00Z", delegated=False),
                  {"stage": "plan", "started": "2026-10-05T16:20:00Z"}]
        self.assertEqual(["hand-backs: with a result contract: 0 of 0"], self.verb(stages).stdout.splitlines())

    def test_e5_a_block_outside_every_window_or_for_another_stage_does_not_count(self) -> None:
        late = implement_block().replace("17:01:02", "17:30:00")
        other = entry(None, "## 2026-10-05T17:02:00Z — drive-gaps — gaps")
        result = self.verb(TWO[:1], late + other)
        self.assertEqual("hand-backs: implement 2026-10-05T17:00:00Z: nothing recorded — a finding for implement",
                         result.stdout.splitlines()[0])
        self.assertEqual("hand-backs: with a result contract: 0 of 1", result.stdout.splitlines()[-1])

    def test_e5_a_malformed_block_inside_the_window_does_not_count(self) -> None:
        bad = implement_block().replace('"status": "green"', '"status": "gaps"')
        result = self.verb(TWO[:1], bad)
        self.assertEqual("hand-backs: with a result contract: 0 of 1", result.stdout.splitlines()[-1])

    def test_a_folder_that_is_not_a_slice_is_usage_exit_two(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = project(directory, TWO)
            for folder in ("specs/f", "apps/x", "specs/f/slices/S9"):
                self.assertEqual(2, run(repo, "--hand-backs", folder).returncode, folder)
            self.assertEqual(2, run(repo, "--hand-backs").returncode)


class BenchmarkCountTest(unittest.TestCase):
    def aggregate(self, stages: list[dict[str, Any]], record: str | None = None) -> str:
        with tempfile.TemporaryDirectory() as directory:
            repo = project(directory, stages, record)
            result = benchmark(repo)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual([], list(repo.rglob("__pycache__")))
            return result.stdout

    def test_the_slice_prints_its_count_of_delegated_stages_that_handed_back_a_block(self) -> None:
        out = self.aggregate(TWO, implement_block())
        self.assertIn("S1: hand-backs with a result contract: 1 of 2", out)
        self.assertNotIn("could not attribute", out)

    def test_a_stage_the_harness_could_not_attribute_is_said_and_not_counted(self) -> None:
        stages = [*TWO, stage("tasks", "2026-10-05T15:00:00Z", "2026-10-05T15:10:00Z", source=None)]
        out = self.aggregate(stages, implement_block())
        self.assertIn("S1: hand-backs with a result contract: 1 of 2; 1 stage(s) the harness could not attribute"
                      " — not counted", out)

    def test_a_slice_with_no_delegated_or_unattributed_stage_prints_no_line(self) -> None:
        out = self.aggregate([stage("gaps", "2026-10-05T16:00:00Z", "2026-10-05T16:10:00Z", delegated=False)])
        self.assertNotIn("hand-backs", out)

    def test_a_block_naming_a_decision_the_feature_lacks_counts_in_neither_reading(self) -> None:
        ghost = entry(valid() | BLOCK | {"decisions": ["D9999"]}, IMPLEMENT)
        stages = TWO[:1]
        self.assertIn("S1: hand-backs with a result contract: 0 of 1", self.aggregate(stages, ghost))
        with tempfile.TemporaryDirectory() as directory:
            verb = run(project(directory, stages, ghost), "--hand-backs", SLICE)
        self.assertEqual("hand-backs: with a result contract: 0 of 1", verb.stdout.splitlines()[-1])

    def test_a_block_naming_a_decision_the_feature_has_counts_in_both(self) -> None:
        good = entry(valid() | BLOCK | {"decisions": ["D134"]}, IMPLEMENT)
        self.assertIn("S1: hand-backs with a result contract: 1 of 1", self.aggregate(TWO[:1], good))

    def test_a_project_without_the_module_prints_what_it_printed_before(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = project(directory, TWO, implement_block())
            (repo / "scripts/hand_backs.py").unlink()
            result = benchmark(repo)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNotIn("hand-backs", result.stdout)


if __name__ == "__main__":
    unittest.main()
