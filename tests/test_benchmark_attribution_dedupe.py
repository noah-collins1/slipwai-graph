"""B1, B2: one request is one charge — a copy another session holds counts nowhere, a streamed response counts its
last line's usage."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from elapsed_fixture import Session, feature_record, project, record, stamp, summaries

sys.dont_write_bytecode = True

P1, P2 = "specs/f/slices/S1/benchmark.json", "specs/f/slices/S2/benchmark.json"


def raw(path: Path, request: str, when: str, **usage: int) -> None:
    """One transcript line of a response, with exactly the usage given (a streamed response writes several)."""
    line = {"type": "assistant", "requestId": request, "timestamp": when.replace("Z", ".123Z"),
            "message": {"model": "m", "usage": usage}}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(line) + "\n")


class DedupeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.repo = project(Path(self.scratch.name))

    def test_b1_a_request_copied_into_another_session_is_counted_once_where_it_began(self) -> None:
        first, second = Session(self.repo, "sessA"), Session(self.repo, "sessB")
        c1 = first.open(None, "implement", P1)
        first.say(None, "r1", 5000, stamp(1, "09:01:00"))
        c2 = second.open(None, "implement", P2)
        second.say(None, "r9", 30, stamp(1, "09:03:00"))
        raw(second.main, "r1", stamp(1, "09:01:00"), input_tokens=5000)  # Claude Code's copy of an earlier request
        record(self.repo, "S1", first.entry("implement", stamp(1, "09:00:00"), stamp(1, "09:10:00"), c1))
        record(self.repo, "S2", second.entry("implement", stamp(1, "09:02:00"), stamp(1, "09:10:00"), c2))
        feature_record(self.repo)
        found = summaries(self.repo)
        self.assertEqual((found["S1"]["cost"]["tokens"], found["S2"]["cost"]["tokens"]), (5000, 30))
        totals = found["(feature)"]["session_totals"]
        self.assertEqual((totals["sessA"]["total"], totals["sessB"]["total"]), (5000, 30))

    def test_b2_a_streamed_response_counts_its_last_lines_usage(self) -> None:
        said = Session(self.repo)
        cursor = said.open(None, "implement", P1)
        raw(said.main, "r1", stamp(1, "09:01:00"), input_tokens=2, output_tokens=8)
        raw(said.main, "r1", stamp(1, "09:01:05"), input_tokens=2, output_tokens=176)
        record(self.repo, "S1", said.entry("implement", stamp(1, "09:00:00"), stamp(1, "09:10:00"), cursor))
        found = summaries(self.repo)["S1"]
        self.assertEqual(found["cost"]["tokens"], 178)


if __name__ == "__main__":
    unittest.main()
