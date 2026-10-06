"""T039 (F10): no note beside the renamed column says *wall* — stage time has one name."""
from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path

from elapsed_fixture import bench, entry, project, record, stamp

sys.dont_write_bytecode = True


class StageTimeNameTest(unittest.TestCase):
    def test_e1_the_notes_name_stage_time_never_wall(self) -> None:
        with tempfile.TemporaryDirectory() as scratch:
            repo = project(Path(scratch))
            record(repo, "S1",
                   entry("implement", stamp(1, "09:00:00"), stamp(1, "10:00:00"), delegate="drive-implement",
                         cycle="rule"),
                   entry("implement", stamp(1, "10:00:00"), stamp(1, "11:00:00"), delegate="host", cycle="example"),
                   entry("gaps", stamp(1, "11:00:00"), stamp(1, "11:00:00")))
            out = bench(repo).stdout
        self.assertIn("compares with neither", out)
        self.assertIn("not bracketed around its work", out)
        self.assertIsNone(re.search(r"\bwall\b", out, re.I), out)


if __name__ == "__main__":
    unittest.main()
