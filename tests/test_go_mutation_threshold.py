"""S08 T040 (class · AC-S08-2, adversary B3, D155): a threshold below "no survivor" is a share of the whole module.

A scoped run under such a threshold that meets a survivor (or a Gremlins failure) runs the service's whole module and
takes its verdict; a scope-invariant threshold (a number of at least 99.99, no `mutant-coverage`) judges the scoped run
alone, as T033 and T034 left it. A fake `go` plays a script of runs: per run the report it writes, what it prints and
its exit, as Gremlins does (10 under a built binary; `go run` turns it into 1 and says "exit status 10").
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

sys.dont_write_bytecode = True
FAKE_GO = """#!/usr/bin/env python3
import json, os, sys
if sys.argv[1:2] != ["run"]:
    sys.exit(0)
with open(os.environ["FAKE_LOG"], "a", encoding="utf-8") as log:
    log.write(json.dumps(["go", *sys.argv[1:]]) + "\\n")
with open(os.environ["FAKE_LOG"], encoding="utf-8") as log:
    index = sum(1 for line in log if '"run"' in line) - 1
step = json.loads(os.environ["FAKE_PLAN"])[index]
if step["report"] is not None:
    with open(sys.argv[sys.argv.index("--output") + 1], "w", encoding="utf-8") as report:
        report.write(step["report"])
print(step.get("say", "Test efficacy: 50.00%"))
code = step["exit"]
if code and os.environ["FAKE_STYLE"] == "run":
    sys.stderr.write("exit status %d\\n" % code)
    sys.exit(1)
sys.exit(code)
"""
STYLES = ("run", "binary")
LOWERED = "unleash:\n  threshold:\n    efficacy: 98.9\n"
FACTORY = "unleash:\n  threshold:\n    efficacy: 99.99\n"


def report(*statuses: str) -> str:
    return json.dumps({"files": [{"file_name": "a.go", "mutations": [{"status": s} for s in statuses]}]})


def run(body: str | None, code: int = 0, say: str | None = None) -> dict[str, object]:
    return {"report": body, "exit": code, **({"say": say} if say else {})}


class ThresholdTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = Path(tempfile.mkdtemp(prefix="go-thr-", dir="/tmp"))
        self.addCleanup(shutil.rmtree, self.directory, ignore_errors=True)
        self.service = self.directory / "svc"
        self.service.mkdir()
        for name in ("a.go", "b.go"):
            (self.service / name).write_text("package x\n", encoding="utf-8")
        (self.service / "go.mod").write_text("module example.com/svc\n\ngo 1.22\n", encoding="utf-8")
        self.tools = FakeTools(self.directory, git=False)
        executable(self.tools.bin / "go", FAKE_GO)

    def main(self, yaml: str | None, plan: list[dict[str, object]], style: str = "binary") -> tuple[int, str, str]:
        config = self.service / ".gremlins.yaml"
        config.unlink(missing_ok=True)
        if yaml is not None:
            config.write_text(yaml, encoding="utf-8")
        self.tools.log.unlink(missing_ok=True)
        module = loaded()
        saved = dict(os.environ)
        os.environ.update(self.tools.environment(), FAKE_PLAN=json.dumps(plan), FAKE_STYLE=style)
        out, err = io.StringIO(), io.StringIO()
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                status = module.main(["go-mutation.py", str(self.service), "--file", "a.go"])
        finally:
            os.environ.clear()
            os.environ.update(saved)
        return status, out.getvalue(), err.getvalue()

    def runs(self) -> list[list[str]]:
        return self.tools.runs()

    def test_e1_a_lowered_threshold_and_a_lived_scoped_mutant_runs_the_whole_module_and_says_so(self) -> None:
        for style in STYLES:
            with self.subTest(style):
                plan = [run(report("KILLED", "LIVED"), 10), run(report("KILLED"))]
                status, out, err = self.main(LOWERED, plan, style)
                self.assertEqual(status, 0, out + err)
                first, second = self.runs()
                self.assertIn("--exclude-files", first)
                self.assertNotIn("--exclude-files", second)  # the unscoped path
                self.assertIn("mutation: svc — a scoped mutant lived and efficacy 98.9 is a share of the whole module, "
                              "not `no survivor`; the whole module is run and judges", out.splitlines())

    def test_e2_the_sweeps_verdict_and_report_are_the_runs(self) -> None:
        for style, expected in (("binary", 10), ("run", 1)):
            with self.subTest(style):
                plan = [run(report("LIVED"), 10), run(report("LIVED", "KILLED"), 10)]
                status, out, err = self.main(LOWERED, plan, style)
                self.assertEqual(status, expected, out + err)
                self.assertEqual(len(self.runs()), 2)
                self.assertIn("KILLED", (self.service / "gremlins.json").read_text(encoding="utf-8"))

    def test_e3_a_gremlins_failure_with_no_survivor_listed_is_the_sweeps_too(self) -> None:
        for style in STYLES:
            with self.subTest(style):
                plan = [run(report("KILLED", "NOT COVERED"), 10), run(report("KILLED"))]
                status, out, err = self.main(LOWERED, plan, style)
                self.assertEqual((status, len(self.runs())), (0, 2), out + err)
                self.assertIn("Gremlins failed the scoped run", out)

    def test_e4_a_scope_invariant_threshold_judges_the_scoped_run_alone(self) -> None:
        for style, expected in (("binary", 10), ("run", 1)):
            for yaml in (FACTORY, "unleash:\n  threshold:\n    efficacy: 100 # none\n"):
                with self.subTest(style=style, yaml=yaml):
                    status, out, err = self.main(yaml, [run(report("KILLED", "LIVED"), 10)], style)
                    self.assertEqual((status, len(self.runs())), (expected, 1), out + err)
                    self.assertNotIn("the whole module is run", out)

    def test_e5_all_killed_passes_under_any_threshold_without_a_sweep(self) -> None:
        for style in STYLES:
            for yaml, code in ((LOWERED, 0), (LOWERED, 10), (None, 0)):
                with self.subTest(style=style, yaml=yaml, code=code):
                    status, out, err = self.main(yaml, [run(report("KILLED", "KILLED"), code)], style)
                    self.assertEqual((status, len(self.runs())), (0, 1), out + err)

    def test_e6_not_covered_only_passes_unless_mutant_coverage_is_set(self) -> None:
        for style in STYLES:
            with self.subTest(style=style, set=False):
                status, out, err = self.main(LOWERED, [run(report("NOT COVERED"), 10)], style)
                self.assertEqual((status, len(self.runs())), (0, 1), out + err)
            with self.subTest(style=style, set=True):
                coverage = LOWERED + "  mutant-coverage: 60\n"
                status, out, err = self.main(coverage, [run(report("NOT COVERED"), 10), run(report("KILLED"))], style)
                self.assertEqual((status, len(self.runs())), (0, 2), out + err)
                self.assertIn("mutant-coverage", out)

    def test_e7_what_stays_red_stays_red_without_a_sweep(self) -> None:
        for style in STYLES:
            for plan in ([run(report("LIVED", "TIMED OUT"), 10)], [run(report("TIMED OUT"), 0)], [run(None, 10)],
                         [run("{not json", 10)]):
                with self.subTest(style=style, plan=plan):
                    status, out, err = self.main(LOWERED, plan, style)
                    self.assertNotEqual(status, 0, out + err)
                    self.assertEqual(len(self.runs()), 1)

    def test_e8_a_threshold_it_cannot_read_as_a_number_is_not_invariant(self) -> None:
        for yaml in (None, "unleash:\n  integration: true\n", "unleash:\n  threshold:\n    efficacy: high\n",
                     'unleash:\n  threshold:\n    efficacy: "99.99"\n', "unleash:\n  threshold:\n    efficacy: 99.98\n",
                     "unleash:\n  threshold:\n    efficacy: 99.99\n  mutant-coverage: 50\n"):
            with self.subTest(yaml=yaml):
                status, out, err = self.main(yaml, [run(report("LIVED"), 10), run(report("LIVED"), 10)])
                self.assertEqual((status, len(self.runs())), (10, 2), out + err)


if __name__ == "__main__":
    unittest.main()
