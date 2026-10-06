"""R4: rework is what a demo that was not accepted cost; the record's cost is the sum of what its entries cost."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from elapsed_fixture import bench, costed, entry, project, record, stamp, summaries

sys.dont_write_bytecode = True


class ReworkTest(unittest.TestCase):
    def setUp(self) -> None:
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.repo = project(Path(self.scratch.name))

    def test_e1_rework_is_the_entries_between_a_refused_demo_and_the_next_demo(self) -> None:
        """S08's shape: the last implement, after the accepted demo, is not rework."""
        def demo(start: str, end: str, outcome: str) -> dict:
            return costed(entry("demo", stamp(1, start), stamp(1, end), outcome=outcome), 100_000)

        record(self.repo, "S8",
               demo("09:00:00", "09:10:00", "implementation"),
               costed(entry("implement", stamp(1, "09:10:00"), stamp(1, "10:10:00")), 3_000_000),
               demo("10:10:00", "10:20:00", "implementation"),
               costed(entry("implement", stamp(1, "10:20:00"), stamp(1, "11:00:00")), 1_500_000),
               demo("11:00:00", "11:10:00", "accepted"),
               costed(entry("implement", stamp(1, "11:10:00"), stamp(1, "11:30:00")), 700_000))
        found = summaries(self.repo)["S8"]
        self.assertEqual(found["rework"], {"seconds": 3600 + 2400, "tokens": 4_500_000})
        self.assertEqual(found["cost"]["tokens"], 5_500_000)
        self.assertEqual([item["tokens"] for item in found["entries"]],
                         [100_000, 3_000_000, 100_000, 1_500_000, 100_000, 700_000])
        self.assertEqual(found["entries"][1]["stage_seconds"], 3600)
        out = bench(self.repo).stdout
        header = next(line for line in out.splitlines() if line.lstrip().startswith("slice  elapsed"))
        self.assertEqual(header.split()[-2:], ["rework", "cost"], header)
        row = next(line for line in out.splitlines() if line.lstrip().startswith("S8 ") and "1h40m" in line)
        self.assertTrue(row.split()[-1] == "5.5M" and "4.5M" in row, row)

    def test_e2_a_slice_with_no_demo_has_no_rework(self) -> None:
        record(self.repo, "S8", costed(entry("implement", stamp(1, "09:00:00"), stamp(1, "10:00:00")), 10))
        self.assertEqual(summaries(self.repo)["S8"]["rework"], {"seconds": 0, "tokens": 0})

    def test_e3_the_entries_after_a_refused_demo_with_no_next_demo_are_rework(self) -> None:
        record(self.repo, "S8",
               entry("demo", stamp(1, "09:00:00"), stamp(1, "09:10:00"), outcome="behaviour"),
               costed(entry("implement", stamp(1, "09:10:00"), stamp(1, "09:40:00")), 800),
               costed(entry("converge", stamp(1, "09:40:00"), stamp(1, "09:50:00")), 200))
        self.assertEqual(summaries(self.repo)["S8"]["rework"], {"seconds": 2400, "tokens": 1000})


if __name__ == "__main__":
    unittest.main()
