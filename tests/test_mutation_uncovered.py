"""S08 T033 (rule · AC-S08-2): a scoped run judges as the sweep states: not covered is reported, a survivor fails.

A fake `go` stands in for Gremlins: it writes the report it is told to and exits the way Gremlins does, 10 when
the efficacy is below the threshold, which is what zero tested mutants score. Nothing is mutated.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from test_go_mutation_file import FakeTools, executable, loaded

from slipwai.assets import LANGUAGE_ROOT

sys.dont_write_bytecode = True
FAKE_GO = """#!/usr/bin/env python3
import json, os, sys
if sys.argv[1:2] == ["run"]:
    with open(sys.argv[sys.argv.index("--output") + 1], "w", encoding="utf-8") as report:
        report.write(os.environ["FAKE_REPORT"])
    print("Test efficacy: 0.00%")
    sys.exit(int(os.environ["FAKE_EXIT"]))
"""
POM = LANGUAGE_ROOT / "java-spring/app/pom.xml"


def report(*statuses: str) -> str:
    return json.dumps({"files": [{"file_name": "a.go", "mutations": [{"status": s} for s in statuses]}]})


class UncoveredTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = Path(tempfile.mkdtemp(prefix="go-unc-", dir="/tmp"))
        self.addCleanup(shutil.rmtree, self.directory, ignore_errors=True)
        self.service = self.directory / "svc"
        self.service.mkdir()
        for name in ("a.go", "b.go"):
            (self.service / name).write_text("package x\n", encoding="utf-8")
        (self.service / "go.mod").write_text("module example.com/svc\n\ngo 1.22\n", encoding="utf-8")
        self.tools = FakeTools(self.directory, git=False)
        executable(self.tools.bin / "go", FAKE_GO)

    def main(self, body: str, code: int, *arguments: str) -> tuple[int, str, str]:
        module = loaded()
        saved = dict(os.environ)
        os.environ.update(self.tools.environment(), FAKE_REPORT=body, FAKE_EXIT=str(code))
        out, err = io.StringIO(), io.StringIO()
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                status = module.main(["go-mutation.py", str(self.service), *arguments])
        finally:
            os.environ.clear()
            os.environ.update(saved)
        return status, out.getvalue(), err.getvalue()

    def test_e1_file_run_with_every_mutant_not_covered_passes_and_counts_them(self) -> None:
        status, out, err = self.main(report("NOT COVERED", "NOT COVERED"), 10, "--file", "a.go")
        self.assertEqual(status, 0, out + err)
        self.assertIn("mutation: 2 mutants not covered by any test, none killed or lived; not covered is "
                      "reported, never failed", out.splitlines())

    def test_e2_the_same_holds_under_since(self) -> None:
        (self.service / "c.go").write_text("package x\n", encoding="utf-8")
        git = self.tools.bin / "git"
        executable(git, "#!/bin/sh\ncase \"$*\" in *ls-files*) echo c.go;; esac\nexit 0\n")
        status, out, err = self.main(report("NOT COVERED"), 10, "--since", "main")
        self.assertEqual(status, 0, out + err)
        self.assertIn("mutation: 1 mutants not covered", out)

    def test_e3_a_lived_mutant_still_fails(self) -> None:
        status, out, _ = self.main(report("NOT COVERED", "LIVED"), 10, "--file", "a.go")
        self.assertEqual(status, 10, out)
        self.assertNotIn("not covered is reported", out)

    def test_e4_a_timed_out_mutant_still_fails(self) -> None:
        status, _, err = self.main(report("NOT COVERED", "TIMED OUT"), 10, "--file", "a.go")
        self.assertNotEqual(status, 0)

    def test_e5_a_red_with_no_report_stays_red(self) -> None:
        self.assertEqual(self.main("", 10, "--file", "a.go")[0], 10)

    def test_e6_hold_the_sweep_judges_as_it_did(self) -> None:
        status, out, _ = self.main(report("NOT COVERED"), 10)
        self.assertEqual(status, 10, out)

    def test_e7_hold_pit_has_no_threshold_so_not_covered_only_passes(self) -> None:
        pom = POM.read_text(encoding="utf-8")
        for key in ("mutationThreshold", "coverageThreshold"):
            self.assertNotIn(key, pom)


if __name__ == "__main__":
    unittest.main()
