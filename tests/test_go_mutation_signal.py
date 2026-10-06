"""S08 T038 (class · AC-S08-2, adversary B1): a scoped Go run passes on nothing only on Gremlins' positive word.

Real Gremlins 0.6.0 stopped by SIGINT or SIGTERM prints "Shutting down gracefully..." and exits 0 with no report
(`cmd/unleash.go`: `if cancelled { return nil }`); finding nothing to mutate prints "No results to report." and
exits 0 with no report as well. The fake `go` here does each, as `go run` and as a built binary, which differ only
on a non-zero exit and so are the same here. Nothing is mutated.
"""
from __future__ import annotations

import contextlib
import io
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from test_go_mutation_file import FakeTools, executable, loaded

sys.dont_write_bytecode = True
FAKE_GO = """#!/usr/bin/env python3
import os, sys
if sys.argv[1:2] == ["run"]:
    if os.environ.get("FAKE_REPORT") is not None:
        with open(sys.argv[sys.argv.index("--output") + 1], "w", encoding="utf-8") as report:
            report.write(os.environ["FAKE_REPORT"])
    print(os.environ["FAKE_SAY"])
    sys.exit(int(os.environ.get("FAKE_EXIT", "0")))
"""
STOPPED = "Starting...\nGathering coverage... done in 1.7s\n\nShutting down gracefully...\n"
NOTHING = "Starting...\nGathering coverage... done in 1.7s\n\nNo results to report.\n"


class SignalTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = Path(tempfile.mkdtemp(prefix="go-sig-", dir="/tmp"))
        self.addCleanup(shutil.rmtree, self.directory, ignore_errors=True)
        self.service = self.directory / "svc"
        self.service.mkdir()
        for name in ("a.go", "b.go"):
            (self.service / name).write_text("package x\n", encoding="utf-8")
        (self.service / "go.mod").write_text("module example.com/svc\n\ngo 1.22\n", encoding="utf-8")
        self.tools = FakeTools(self.directory, git=False)
        executable(self.tools.bin / "go", FAKE_GO)

    def main(self, said: str, report: str | None, *arguments: str) -> tuple[int, str, str]:
        module = loaded()
        saved = dict(os.environ)
        os.environ.update(self.tools.environment(), FAKE_SAY=said)
        os.environ.pop("FAKE_REPORT", None)
        if report is not None:
            os.environ["FAKE_REPORT"] = report
        out, err = io.StringIO(), io.StringIO()
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                status = module.main(["go-mutation.py", str(self.service), *arguments])
        finally:
            os.environ.clear()
            os.environ.update(saved)
        return status, out.getvalue(), err.getvalue()

    def test_e1_a_signal_stopped_run_with_no_report_fails_with_words(self) -> None:
        status, out, err = self.main(STOPPED, None, "--file", "a.go")
        self.assertNotEqual(status, 0, out + err)
        self.assertNotIn("no mutant to run", out)
        self.assertIn("stopped by a signal", err)

    def test_e2_an_exit_zero_with_an_unreadable_report_fails(self) -> None:
        for body in ("{not json", "[]", '{"files": 3}'):
            with self.subTest(body):
                status, out, err = self.main(NOTHING, body, "--file", "a.go")
                self.assertNotEqual(status, 0, out + err)
                self.assertNotIn("no mutant to run", out)

    def test_e3_a_stop_that_also_said_nothing_to_report_still_fails(self) -> None:
        status, out, err = self.main(NOTHING + STOPPED, None, "--file", "a.go")
        self.assertNotEqual(status, 0, out + err)

    def test_e4_hold_a_real_nothing_to_mutate_passes_and_says_so(self) -> None:
        status, out, err = self.main(NOTHING, None, "--file", "a.go")
        self.assertEqual(status, 0, out + err)
        self.assertTrue(any("no mutant to run" in line for line in out.splitlines()), out)
        self.assertIn("No results to report.", out)  # Gremlins' own words still reach the log

    def test_e5_the_sweep_fails_the_same_cases(self) -> None:
        for said, body in ((STOPPED, None), (NOTHING, "{not json"), (NOTHING, None)):
            with self.subTest(said=said[-20:], report=body):
                status, out, err = self.main(said, body)
                self.assertNotEqual(status, 0, out + err)


if __name__ == "__main__":
    unittest.main()
