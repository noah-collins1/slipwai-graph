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
import os, sys
if sys.argv[1:2] == ["run"]:
    if os.environ["FAKE_REPORT"]:
        with open(sys.argv[sys.argv.index("--output") + 1], "w", encoding="utf-8") as report:
            report.write(os.environ["FAKE_REPORT"])
    code = int(os.environ["FAKE_EXIT"])
    print(os.environ.get("FAKE_SAY", "Test efficacy: 0.00%"))
    if code and os.environ["FAKE_STYLE"] == "run":  # `go run` reports the program's exit and exits 1 itself
        sys.stderr.write("exit status %d\\n" % code)
        sys.exit(1)
    sys.exit(code)
"""
STYLES = ("run", "binary")  # how Gremlins' exit reaches the script: through `go run` (1) or as a built binary
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

    def main(self, body: str, code: int, *arguments: str, style: str = "binary",
             say: str | None = None) -> tuple[int, str, str]:
        module = loaded()
        saved = dict(os.environ)
        os.environ.update(self.tools.environment(), FAKE_REPORT=body, FAKE_EXIT=str(code), FAKE_STYLE=style)
        if say is not None:
            os.environ["FAKE_SAY"] = say
        out, err = io.StringIO(), io.StringIO()
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                status = module.main(["go-mutation.py", str(self.service), *arguments])
        finally:
            os.environ.clear()
            os.environ.update(saved)
        return status, out.getvalue(), err.getvalue()

    def test_e1_file_run_with_every_mutant_not_covered_passes_and_counts_them(self) -> None:
        for style in STYLES:
            with self.subTest(style):
                status, out, err = self.main(report("NOT COVERED", "NOT COVERED"), 10, "--file", "a.go", style=style)
                self.assertEqual(status, 0, out + err)
                self.assertIn("mutation: 2 mutants not covered by any test, none killed or lived; not covered is "
                              "reported, never failed", out.splitlines())

    def test_e2_the_same_holds_under_since(self) -> None:
        (self.service / "c.go").write_text("package x\n", encoding="utf-8")
        git = self.tools.bin / "git"
        executable(git, "#!/bin/sh\ncase \"$*\" in *ls-files*) echo c.go;; esac\nexit 0\n")
        for style in STYLES:
            with self.subTest(style):
                status, out, err = self.main(report("NOT COVERED"), 10, "--since", "main", style=style)
                self.assertEqual(status, 0, out + err)
                self.assertIn("mutation: 1 mutants not covered", out)

    def test_e3_a_lived_mutant_still_fails(self) -> None:
        for style in STYLES:
            with self.subTest(style):
                status, out, _ = self.main(report("NOT COVERED", "LIVED"), 10, "--file", "a.go", style=style)
                self.assertNotEqual(status, 0, out)
                self.assertNotIn("not covered is reported", out)

    def test_e4_a_timed_out_mutant_still_fails(self) -> None:
        for style in STYLES:
            for code in (0, 10):
                with self.subTest(style=style, code=code):
                    status, _, err = self.main(report("NOT COVERED", "TIMED OUT"), code, "--file", "a.go", style=style)
                    self.assertNotEqual(status, 0, err)

    def test_e5_a_red_with_no_or_unreadable_report_stays_red(self) -> None:
        for style in STYLES:
            for body in ("", "{not json"):
                with self.subTest(style=style, report=body):
                    status, out, err = self.main(body, 10, "--file", "a.go", style=style)
                    self.assertNotEqual(status, 0, out + err)
                    self.assertNotIn("no mutant to run", out)

    def test_e5b_a_report_of_no_mutants_after_a_failed_run_stays_red(self) -> None:
        for style in STYLES:
            with self.subTest(style):
                self.assertNotEqual(self.main(report(), 10, "--file", "a.go", style=style)[0], 0)

    def test_e5c_a_scoped_run_with_nothing_to_mutate_is_said_and_passes(self) -> None:
        for style in STYLES:
            for body in ("", report()):
                with self.subTest(style=style, report=body):
                    status, out, err = self.main(body, 0, "--file", "a.go", style=style, say="\nNo results to report.")
                    self.assertEqual(status, 0, out + err)
                    self.assertTrue(any("no mutant to run" in line for line in out.splitlines()), out)

    def test_e6_hold_the_sweep_judges_as_it_did(self) -> None:
        for style, expected in (("binary", 10), ("run", 1)):
            with self.subTest(style):
                self.assertEqual(self.main(report("NOT COVERED"), 10, style=style)[0], expected)
        for body in ("", report()):
            with self.subTest(report=body):
                status, out, err = self.main(body, 0)
                self.assertEqual(status, 1, out + err)
                self.assertNotIn("no mutant to run", out)

    def test_e7_hold_pit_has_no_threshold_so_not_covered_only_passes(self) -> None:
        pom = POM.read_text(encoding="utf-8")
        for key in ("mutationThreshold", "coverageThreshold"):
            self.assertNotIn(key, pom)


if __name__ == "__main__":
    unittest.main()
