"""R6 of S14-result-contract: what was handed back, per delegated stage.

`check-decisions.py --hand-backs <slice-dir>` lists each ended benchmark entry the transcript shows was delegated
against the record; `benchmark.py` carries the count per slice. Records are written by hand here: the harness's
transcripts are not under test, only what is read from `benchmark.json` and `hand-backs.md`.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

from hand_backs_fixture import SCRIPTS, commit, entry, run, scratch, valid

SLICE = "specs/f/slices/S1"
IMPLEMENT = "## 2026-10-05T17:01:02Z — drive-implement — implement — 2026-10-05T17:00:00Z"
BLOCK = {"delegate": "drive-implement", "status": "green"}


TYPED = {"implement": "drive-implement", "converge": "drive-converge", "gaps": "drive-gaps", "tasks": "drive-tasks"}


def stage(name: str, started: str, ended: str, delegated: bool = True, source: str | None = "claude",
          agents: list[str] | None | str = "typed") -> dict[str, Any]:
    """An ended benchmark entry; `agents` is the types the benchmark recorded as run (`typed`: the stage's own)."""
    kept = [TYPED[name]] if agents == "typed" else agents
    return {"stage": name, "started": started, "ended": ended, "seconds": 600, "signals": {}, "delegated": delegated,
            "agents": kept, "usage": {"source": source, "reason": None if source else "no transcript"}}


def project(directory: str, stages: list[dict[str, Any]], record: str | None = None,
            arrived: str | None = "2000-01-01T00:00:00Z") -> Path:
    """A scratch project; its scripts are committed at `arrived` (D161), or it is no repository at all."""
    repo = scratch(directory, record)
    (repo / "scripts/agents").mkdir()
    # The toolkit ships `scripts/agents/` whole: benchmark.py loads measures.py and attribution.py from beside it.
    for name in ("benchmark.py", "measures.py", "attribution.py"):
        shutil.copy(SCRIPTS / "agents" / name, repo / "scripts/agents" / name)
    (repo / SLICE / "benchmark.json").write_text(
        json.dumps({"feature": "f", "slice": "S1", "stages": stages}), encoding="utf-8")
    if arrived:
        commit(repo, arrived)
    return repo


def implement_block() -> str:
    return entry(valid() | BLOCK, IMPLEMENT)


def benchmark(repo: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["python3", "-B", "scripts/agents/benchmark.py"], cwd=repo, text=True, capture_output=True)


TWO = [stage("implement", "2026-10-05T17:00:00Z", "2026-10-05T17:10:00Z"),
       stage("converge", "2026-10-05T18:00:00Z", "2026-10-05T18:10:00Z")]


def toolkit(name: str) -> Any:
    """A toolkit script loaded by path, with bytecode off."""
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + ".py") if name != "benchmark"
                                                  else SCRIPTS / "agents/benchmark.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OwnersTest(unittest.TestCase):
    def test_the_types_that_owe_a_stage_a_block_are_the_benchmarks_own_owners(self) -> None:
        self.assertEqual(toolkit("benchmark").OWNERS, toolkit("hand_backs").OWNERS)


class CoverageVerbTest(unittest.TestCase):
    def verb(self, stages: list[dict[str, Any]], record: str | None = None) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory:
            return run(project(directory, stages, record), "--hand-backs", SLICE)

    def test_e1_two_delegated_entries_one_with_a_block_is_one_of_two(self) -> None:
        result = self.verb(TWO, "# Hand-backs — S1\n\n" + implement_block())
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual([
            "hand-backs: implement 2026-10-05T17:00:00Z drive-implement: block",
            "hand-backs: converge 2026-10-05T18:00:00Z drive-converge: nothing recorded — a finding for converge",
            "hand-backs: with a result contract: 1 of 2"], result.stdout.splitlines())

    def test_e2_a_missing_entry_counts_in_the_total_and_not_the_count(self) -> None:
        record = ("## 2026-10-05T18:05:00Z — drive-converge — converge — 2026-10-05T18:00:00Z\n\n"
                  "- **Missing:** refused: out of budget\n\n")
        result = self.verb(TWO, implement_block() + record)
        lines = result.stdout.splitlines()
        self.assertIn("hand-backs: converge 2026-10-05T18:00:00Z drive-converge: missing — refused: out of budget",
                      lines)
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

    def test_e5_a_block_naming_another_start_or_none_or_another_stage_does_not_count(self) -> None:
        stale = implement_block().replace(" — 2026-10-05T17:00:00Z", " — 2026-10-04T17:00:00Z")
        bare = implement_block().replace(" — 2026-10-05T17:00:00Z", "")
        other = entry(None, "## 2026-10-05T17:02:00Z — drive-gaps — gaps — 2026-10-05T17:00:00Z")
        result = self.verb(TWO[:1], stale + bare + other)
        self.assertEqual("hand-backs: implement 2026-10-05T17:00:00Z drive-implement: nothing recorded — "
                         "a finding for converge",
                         result.stdout.splitlines()[0])
        self.assertEqual("hand-backs: with a result contract: 0 of 1", result.stdout.splitlines()[-1])

    def test_e5_a_continuation_written_after_the_stage_ended_answers_the_stage_it_names(self) -> None:
        late = implement_block().replace("17:01:02", "23:30:00")
        result = self.verb(TWO[:1], late)
        self.assertEqual("hand-backs: with a result contract: 1 of 1", result.stdout.splitlines()[-1])

    def test_e5_a_block_at_the_instant_two_stages_meet_covers_only_the_stage_it_names(self) -> None:
        stages = [stage("implement", "2026-10-05T17:00:00Z", "2026-10-05T17:10:00Z"),
                  stage("implement", "2026-10-05T17:10:00Z", "2026-10-05T17:20:00Z")]
        meet = implement_block().replace("17:01:02", "17:10:00")  # names the first pass's start
        lines = self.verb(stages, meet).stdout.splitlines()
        self.assertEqual("hand-backs: implement 2026-10-05T17:00:00Z drive-implement: block", lines[0])
        self.assertIn("implement 2026-10-05T17:10:00Z drive-implement: nothing recorded", lines[1])
        self.assertEqual("hand-backs: with a result contract: 1 of 2", lines[-1])

    def test_e5_a_malformed_block_inside_the_window_does_not_count(self) -> None:
        bad = implement_block().replace('"status": "green"', '"status": "gaps"')
        result = self.verb(TWO[:1], bad)
        self.assertEqual("hand-backs: with a result contract: 0 of 1", result.stdout.splitlines()[-1])

    def test_a_block_of_a_contract_this_factory_cannot_check_is_said_and_not_held(self) -> None:
        newer = entry({"contract": 2}, IMPLEMENT)
        result = self.verb(TWO, newer)
        self.assertEqual([
            "hand-backs: implement 2026-10-05T17:00:00Z drive-implement: block of contract 2 — this factory cannot "
            "check it; not counted as held",
            "hand-backs: converge 2026-10-05T18:00:00Z drive-converge: nothing recorded — a finding for converge",
            "hand-backs: with a result contract: 0 of 2"], result.stdout.splitlines())

    def test_a_passing_contract_one_block_holds_the_stage_beside_a_newer_one(self) -> None:
        result = self.verb(TWO[:1], entry({"contract": 2}, IMPLEMENT) + implement_block())
        self.assertEqual("hand-backs: implement 2026-10-05T17:00:00Z drive-implement: block",
                         result.stdout.splitlines()[0])
        self.assertEqual("hand-backs: with a result contract: 1 of 1", result.stdout.splitlines()[-1])

    def test_e6_a_stage_whose_only_helpers_are_untyped_owes_nothing_and_is_not_listed(self) -> None:
        stages = [stage("gaps", "2026-10-05T16:00:00Z", "2026-10-05T16:10:00Z", agents=["Explore"])]
        result = self.verb(stages)
        self.assertEqual(["hand-backs: with a result contract: 0 of 0"], result.stdout.splitlines())

    def test_e6_a_stage_run_by_drive_slice_in_its_own_context_owes_this_record_nothing(self) -> None:
        stages = [stage("plan", "2026-10-05T16:00:00Z", "2026-10-05T16:10:00Z", agents=["drive-slice"])]
        self.assertEqual(["hand-backs: with a result contract: 0 of 0"], self.verb(stages).stdout.splitlines())

    def test_e6_a_type_that_does_not_belong_to_the_stage_owes_nothing(self) -> None:
        stages = [stage("implement", "2026-10-05T17:00:00Z", "2026-10-05T17:10:00Z", agents=["drive-converge"])]
        self.assertEqual(["hand-backs: with a result contract: 0 of 0"], self.verb(stages).stdout.splitlines())

    def test_e6_a_typed_delegate_among_untyped_helpers_is_the_one_that_owes_the_block(self) -> None:
        stages = [stage("gaps", "2026-10-05T16:00:00Z", "2026-10-05T16:10:00Z", agents=["Explore", "drive-gaps"])]
        self.assertEqual([
            "hand-backs: gaps 2026-10-05T16:00:00Z drive-gaps: nothing recorded — a finding for converge",
            "hand-backs: with a result contract: 0 of 1"], self.verb(stages).stdout.splitlines())

    def test_e7_a_delegated_stage_with_no_agents_recorded_could_not_be_attributed_and_is_no_finding(self) -> None:
        nothing: tuple[list[str] | None, ...] = (None, [])
        for agents in nothing:
            stages = [stage("implement", "2026-10-05T17:00:00Z", "2026-10-05T17:10:00Z", agents=agents)]
            self.assertEqual([
                "hand-backs: implement 2026-10-05T17:00:00Z: the harness could not attribute its delegates — "
                "not counted", "hand-backs: with a result contract: 0 of 0"], self.verb(stages).stdout.splitlines())

    def test_a_harness_that_reads_no_subagents_names_a_typed_delegate_it_could_not_attribute(self) -> None:
        """A3: on Codex the reader returns no sub-agents, so `delegated` is false; a typed delegate named still owes."""
        named = stage("implement", "2026-10-05T17:00:00Z", "2026-10-05T17:10:00Z", delegated=False,
                      source="codex")
        signalled = stage("converge", "2026-10-05T18:00:00Z", "2026-10-05T18:10:00Z", delegated=False, source="codex",
                          agents=None) | {"signals": {"agent": "drive-converge"}}
        for one, word in ((named, "implement 2026-10-05T17:00:00Z"), (signalled, "converge 2026-10-05T18:00:00Z")):
            self.assertEqual([f"hand-backs: {word}: the harness could not attribute its delegates — not counted",
                              "hand-backs: with a result contract: 0 of 0"], self.verb([one]).stdout.splitlines())

    def test_a_codex_stage_that_names_no_typed_delegate_owes_nothing_and_says_nothing(self) -> None:
        plain = stage("implement", "2026-10-05T17:00:00Z", "2026-10-05T17:10:00Z", delegated=False, source="codex",
                      agents=None)
        helper = stage("gaps", "2026-10-05T16:00:00Z", "2026-10-05T16:10:00Z", delegated=False, source="codex",
                       agents=["Explore"])
        self.assertEqual(["hand-backs: with a result contract: 0 of 0"], self.verb([plain, helper]).stdout.splitlines())

    def test_e8_a_block_of_a_type_that_does_not_own_the_stage_does_not_count(self) -> None:
        wrong = entry(valid() | {"delegate": "drive-hand", "status": "accepted"},
                      "## 2026-10-05T17:02:00Z — drive-hand — implement")
        result = self.verb(TWO[:1], wrong)
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

    def test_a_codex_stage_with_a_typed_delegate_prints_the_hand_back_line_for_it(self) -> None:
        codex = stage("implement", "2026-10-05T17:00:00Z", "2026-10-05T17:10:00Z", delegated=False, source="codex")
        self.assertIn("S1: hand-backs with a result contract: 0 of 0; 1 stage(s) the harness could not attribute"
                      " — not counted", self.aggregate([codex]))

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

    def test_a_stage_with_only_untyped_helpers_or_drive_slice_owes_nothing_in_the_count(self) -> None:
        stages = [stage("gaps", "2026-10-05T16:00:00Z", "2026-10-05T16:10:00Z", agents=["Explore"]),
                  stage("plan", "2026-10-05T16:20:00Z", "2026-10-05T16:30:00Z", agents=["drive-slice"])]
        self.assertNotIn("hand-backs", self.aggregate(stages))

    def test_a_delegated_stage_with_no_agents_recorded_is_said_and_not_counted(self) -> None:
        stages = [*TWO[:1], stage("tasks", "2026-10-05T15:00:00Z", "2026-10-05T15:10:00Z", agents=None)]
        self.assertIn("S1: hand-backs with a result contract: 0 of 1; 1 stage(s) the harness could not attribute"
                      " — not counted", self.aggregate(stages))

    def test_a_project_without_the_module_prints_what_it_printed_before(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = project(directory, TWO, implement_block())
            (repo / "scripts/hand_backs.py").unlink()
            result = benchmark(repo)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNotIn("hand-backs", result.stdout)


if __name__ == "__main__":
    unittest.main()
