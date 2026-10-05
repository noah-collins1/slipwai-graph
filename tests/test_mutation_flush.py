"""S08 T033 (LOW note): the Go scoped line precedes Gremlins output in a pipe."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_go_mutation_file import FakeTools, executable
from test_mutation_uncovered import FAKE_GO

from slipwai.assets import LANGUAGE_ROOT

sys.dont_write_bytecode = True
SCRIPT = LANGUAGE_ROOT / "go" / "scripts/go-mutation.py"


class FlushTest(unittest.TestCase):
    def test_e2_the_scoped_line_comes_before_gremlins_output_through_a_pipe(self) -> None:
        directory = Path(tempfile.mkdtemp(prefix="go-flush-", dir="/tmp"))
        self.addCleanup(shutil.rmtree, directory, ignore_errors=True)
        service = directory / "svc"
        service.mkdir()
        (service / "a.go").write_text("package x\n", encoding="utf-8")
        (service / "go.mod").write_text("module example.com/svc\n\ngo 1.22\n", encoding="utf-8")
        tools = FakeTools(directory, git=False)
        executable(tools.bin / "go", FAKE_GO)
        env = {**os.environ, **tools.environment(), "FAKE_REPORT": '{"files": []}', "FAKE_EXIT": "0"}
        done = subprocess.run([sys.executable, "-B", str(SCRIPT), str(service), "--file", "a.go"], env=env,
                              text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
        lines = done.stdout.splitlines()
        scoped = next(i for i, line in enumerate(lines) if line.startswith("mutation: scoped to"))
        self.assertLess(scoped, lines.index("Test efficacy: 0.00%"), done.stdout)


if __name__ == "__main__":
    unittest.main()
