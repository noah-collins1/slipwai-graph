"""The runner reads its log whole once per process and not again while the log is what it left (D58; AC-S02-22, -23).

Each entry the runner appends carries `bookkeeping.log_bytes`: the bytes it read from the log since its previous
append, or since the process started. That is how a test reads off what the runner read — a count, never a timing —
by running the runner as a subprocess against a fake harness and reading the log back, as `test_cruise_runner` does.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from support import FactoryTestCase
from test_cruise_runner import cruise, enable, fake_harness, logged

from slipwai.project.cruise import LOG

IDLE = 'mkdir -p specs && touch "specs/progress-$n"\necho "cruise: continue"'


def seed(repo: Path, count: int) -> int:
    """A log of `count` entries as an earlier run would have left it; returns its size in bytes."""
    (repo / LOG).parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps({"iteration": n, "started": "2026-10-03T10:00:00Z", "ended": "2026-10-03T10:00:30Z",
                         "harness": "claude", "last_line": "cruise: continue", "fingerprint": f"{n:016x}"})
             for n in range(1, count + 1)]
    (repo / LOG).write_text("".join(line + "\n" for line in lines), encoding="utf-8")
    return (repo / LOG).stat().st_size


class RunnerLogTest(FactoryTestCase):
    def run_two_iterations(self, name: str, seeded: int) -> tuple[list[dict], int]:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, name, "standard", "python")
            enable(repo, max_iterations="2")
            size = seed(repo, seeded)
            ended = cruise(repo, "run", "--no-park", env=fake_harness(Path(directory), IDLE))
            self.assertEqual(ended.returncode, 0, ended.stdout + ended.stderr)
            return logged(repo)[seeded:], size

    def test_the_seeded_log_is_read_once_and_the_next_iteration_reads_no_byte_of_it(self) -> None:
        """AC-S02-22: over a log of 50 entries, one process runs two iterations; they are numbered 51 and 52, the
        first entry's `log_bytes` is the seeded log's size counted once, the second's is 0."""
        entries, size = self.run_two_iterations("fifty", 50)
        self.assertEqual([entry["iteration"] for entry in entries], [51, 52])
        self.assertEqual([entry.get("bookkeeping", {}).get("log_bytes") for entry in entries], [size, 0])

    def test_the_second_iteration_reads_nothing_whatever_the_history_was(self) -> None:
        """AC-S02-23: over a log of one entry the second entry's `log_bytes` is 0, as over fifty."""
        entries, size = self.run_two_iterations("one", 1)
        self.assertEqual([entry["iteration"] for entry in entries], [2, 3])
        self.assertEqual([entry.get("bookkeeping", {}).get("log_bytes") for entry in entries], [size, 0])

    def test_a_run_over_no_log_reads_no_byte_and_every_later_iteration_reads_none(self) -> None:
        """No log at all: nothing to read at the start, and nothing at any iteration after."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "none", "standard", "python")
            enable(repo, max_iterations="3")
            cruise(repo, "run", "--no-park", env=fake_harness(Path(directory), IDLE))
            self.assertEqual([entry.get("bookkeeping", {}).get("log_bytes") for entry in logged(repo)], [0, 0, 0])
