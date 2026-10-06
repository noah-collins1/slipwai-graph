"""T035 of S14-result-contract (adversary A6): damaged inputs end in the page's exits, never a traceback.

A `benchmark.json` or a record the verbs read, and a hand-back they are given, can be cut off, empty, of the wrong
shape, not UTF-8 or nested past what the parser reads; each is one line on stderr, exit 1, and nothing is written.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any

from hand_backs_fixture import RECORD, entry, fence, run, valid
from hand_backs_fixture import gate as checked
from test_hand_backs_coverage import SLICE, TWO, benchmark, project, stage

BENCH = f"{SLICE}/benchmark.json"
GOOD: dict[str, Any] = {
    "feature": "f", "slice": "S1", "stages": [stage("gaps", "2026-10-05T16:00:00Z", "2026-10-05T16:10:00Z")]}
DEEP = "[" * 100000 + "]" * 100000


def damaged_benchmarks() -> dict[str, bytes]:
    """Each damaged `benchmark.json`, by what is wrong with it."""
    good = json.dumps(GOOD)
    one = GOOD["stages"][0]
    with_usage = json.dumps({**GOOD, "stages": [{**one, "usage": "claude"}]}).encode()
    return {
        "cut off": good[:40].encode(), "empty": b"", "a BOM": b"\xef\xbb\xbf" + good.encode(), "a list": b"[]",
        "stages an object": b'{"stages": {}}', "usage a string": with_usage,
        "no stage name": json.dumps({"stages": [{"started": "2026-10-05T16:00:00Z", "ended": "x"}]}).encode(),
        "a stage that is a string": b'{"stages": ["gaps"]}', "not UTF-8": b'{"stages": [], "x": "\xff"}',
        "nested too deep": DEEP.encode(),
    }


class Damaged(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.repo = project(self.directory.name, TWO)
        self.record = self.repo / RECORD

    def one_line(self, result: subprocess.CompletedProcess[str], word: str, label: str) -> None:
        self.assertNotIn("Traceback", result.stderr, label)
        self.assertEqual(1, result.returncode, (label, result.stderr))
        self.assertEqual(1, len(result.stderr.splitlines()), (label, result.stderr))
        self.assertIn(word, result.stderr, label)


class DamagedBenchmarkTest(Damaged):
    def test_every_verb_that_reads_a_damaged_benchmark_json_says_so_in_one_line_naming_it(self) -> None:
        for label, content in damaged_benchmarks().items():
            (self.repo / BENCH).write_bytes(content)
            for args in (("--hand-backs", SLICE), ("--hand-back-missing", SLICE, "drive-gaps", "gaps", "why")):
                self.one_line(run(self.repo, *args), BENCH, f"{label}: {args[0]}")
            result = run(self.repo, "--hand-back", SLICE, "drive-gaps", "gaps", stdin=fence(valid()))
            self.one_line(result, BENCH, label)
            self.assertFalse(self.record.exists(), label)

    def test_make_benchmark_says_a_slice_it_cannot_count_is_not_counted_and_goes_on(self) -> None:
        nameless = {"feature": "f", "slice": "S1", "stages": [{**TWO[0], "stage": None}]}
        (self.repo / BENCH).write_text(json.dumps(nameless), encoding="utf-8")
        result = benchmark(self.repo)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("S1: hand-backs: ", result.stdout)
        self.assertIn("— not counted", result.stdout)
        self.record.write_bytes(b"\xe2\x80")
        (self.repo / BENCH).write_text(json.dumps({"feature": "f", "slice": "S1", "stages": TWO}), encoding="utf-8")
        result = benchmark(self.repo)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("S1: hand-backs: hand-backs.md is not UTF-8 — not counted", result.stdout)

    def test_a_stage_with_no_started_is_could_not_tell_and_never_a_window_from_the_start_of_time(self) -> None:
        odd = {key: value for key, value in TWO[0].items() if key != "started"}
        record = entry(valid() | {"delegate": "drive-implement", "status": "green"},
                       "## 2026-10-05T17:01:02Z — drive-implement — implement")
        (self.repo / BENCH).write_text(json.dumps({"feature": "f", "slice": "S1", "stages": [odd]}), encoding="utf-8")
        self.record.write_text(record, encoding="utf-8")
        result = run(self.repo, "--hand-backs", SLICE)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("hand-backs: implement ?: could not tell which entries answer it (no started instant) — "
                         "not counted", result.stdout.splitlines()[0])
        self.assertEqual("hand-backs: with a result contract: 0 of 0; 1 could not tell — not counted",
                         result.stdout.splitlines()[-1])


class DamagedRecordTest(Damaged):
    def test_a_record_ending_mid_utf8_is_one_line_naming_it_for_every_verb_and_the_gate(self) -> None:
        self.record.write_bytes("# Hand-backs — S1\n\n".encode() + "—".encode()[:2])
        for args in ((), ("--hand-backs", SLICE), ("--hand-back-missing", SLICE, "drive-gaps", "gaps", "why")):
            self.one_line(run(self.repo, *args), RECORD, str(args))
        appended = run(self.repo, "--hand-back", SLICE, "drive-gaps", "gaps", stdin=fence(valid()))
        self.one_line(appended, RECORD, "append")
        self.assertEqual("# Hand-backs — S1\n\n".encode() + "—".encode()[:2], self.record.read_bytes())


class DeepBodyTest(Damaged):
    def test_a_body_nested_past_what_the_parser_reads_is_refused_by_the_verb_and_a_finding_for_the_gate(self) -> None:
        deep = f"```result-contract\n{DEEP}\n```\n"
        result = run(self.repo, "--hand-back", SLICE, "drive-gaps", "gaps", stdin=deep)
        self.one_line(result, "nested", "verb")
        self.assertFalse(self.record.exists())
        gate = checked(f"## 2026-10-05T17:00:00Z — drive-gaps — gaps\n\n```result-contract\n{DEEP}\n```\n")
        self.assertNotIn("Traceback", gate.stderr)
        self.assertEqual(1, gate.returncode)
        self.assertIn("nested", gate.stderr)

    def test_a_value_nested_deep_inside_a_valid_object_is_a_fault_not_a_traceback(self) -> None:
        block = json.dumps(valid() | {"scope": "[" * 900 + "]" * 900}).replace('"[', "[").replace(']"', "]")
        result = run(self.repo, "--hand-back", SLICE, "drive-gaps", "gaps",
                     stdin=f"```result-contract\n{block}\n```\n")
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(1, result.returncode)
        self.assertFalse(Path(self.record).exists())


if __name__ == "__main__":
    unittest.main()
