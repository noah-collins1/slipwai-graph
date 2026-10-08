"""S41 T004-T005 (rules 3 and 4 · AC-S41-4, -5): the verdict is the report's, and what installs and starts Stryker.

The wrapper runs as a subprocess in a temporary project with a fake `npm` first on `PATH`, written here: it records its
arguments and working directory, and writes the `mutation.json` (or the failure) an example's plan hands it. The
services
are hand-written fixtures, not the factory's; the factory's config is `test_stryker_generated`'s.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from typing import Any

from test_stryker_list import SCRIPT, project

sys.dont_write_bytecode = True
TEST_SELECTION = {"reads": ["assets/languages/typescript/scripts/stryker-mutation.py"]}
SERVICE = "apps/service"
REPORT = f"{SERVICE}/reports/mutation/mutation.json"
FAKE_NPM = f"""#!{sys.executable}
import json, os, shutil, sys
from pathlib import Path
args = sys.argv[1:]
plan = json.loads(Path(os.environ["FAKE_PLAN"]).read_text(encoding="utf-8")) if os.environ.get("FAKE_PLAN") else {{}}
with open(os.environ["FAKE_LOG"], "a", encoding="utf-8") as log:
    log.write(json.dumps({{"argv": args, "cwd": os.getcwd()}}) + "\\n")
cwd = Path.cwd()
if args[:1] == ["ci"]:
    if plan.get("ci_exit"):
        sys.exit(plan["ci_exit"])
    root = cwd / "node_modules"
    root.mkdir(exist_ok=True)
    (root / ".package-lock.json").write_text("{{}}", encoding="utf-8")
    for name in plan.get("installs", ["core", "vitest-runner"]):
        (root / "@stryker-mutator" / name).mkdir(parents=True, exist_ok=True)
        (root / "@stryker-mutator" / name / "package.json").write_text("{{}}", encoding="utf-8")
    sys.exit(0)
if args[:1] == ["exec"]:
    old = (cwd / "reports/mutation/mutation.json").exists() or (cwd / ".stryker-tmp").exists()
    if plan.get("expect_clean") and old:
        Path(os.environ["FAKE_LOG"] + ".dirty").write_text("dirty", encoding="utf-8")
    if "report" in plan:
        (cwd / "reports/mutation").mkdir(parents=True, exist_ok=True)
        (cwd / "reports/mutation/mutation.json").write_text(
            plan["report"] if isinstance(plan["report"], str) else json.dumps(plan["report"]), encoding="utf-8")
    if plan.get("sandbox"):
        (cwd / ".stryker-tmp/sandbox-x/node_modules").mkdir(parents=True, exist_ok=True)
    sys.exit(plan.get("exit", 0))
"""


def mutant(status: str, line: int = 3, column: int = 5, name: str = "StringLiteral", replacement: str = '""') -> dict:
    return {"id": "0", "mutatorName": name, "replacement": replacement, "status": status,
            "location": {"start": {"line": line, "column": column}, "end": {"line": line, "column": column + 1}}}


def report(**files: list[dict]) -> dict:
    return {"schemaVersion": "1.0", "thresholds": {"high": 80, "low": 60},
            "files": {name.replace("__", "/").replace("_ts", ".ts"): {"mutants": mutants} for name, mutants in
                      files.items()}}


class VerdictCase(unittest.TestCase):
    installed = True

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="stryker-verdict-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        (self.bin / "npm").write_text(FAKE_NPM, encoding="utf-8")
        (self.bin / "npm").chmod(0o755)
        self.log = self.root / "npm.log"
        self.plan = self.root / "plan.json"
        self.tree = self.root / "tree"
        project(self.tree)
        for manifest in ("package.json", "package-lock.json", f"{SERVICE}/package.json"):
            (self.tree / manifest).write_text("{}", encoding="utf-8")
        if self.installed:
            self.install(("core", "vitest-runner"))

    def install(self, names: tuple[str, ...]) -> None:
        """What `npm ci` leaves, newer than every manifest: the marker, and the named Stryker packages."""
        modules = self.tree / "node_modules"
        for name in names:
            (modules / "@stryker-mutator" / name).mkdir(parents=True, exist_ok=True)
            (modules / "@stryker-mutator" / name / "package.json").write_text("{}", encoding="utf-8")
        marker = modules / ".package-lock.json"
        marker.parent.mkdir(exist_ok=True)
        marker.write_text("{}", encoding="utf-8")
        later = time.time() + 100
        os.utime(marker, (later, later))

    def run_wrapper(self, plan: dict[str, Any], *arguments: str, path: str | None = None) -> tuple[int, list[str]]:
        self.plan.write_text(json.dumps(plan), encoding="utf-8")
        env = {**os.environ, "PATH": path if path is not None else f"{self.bin}{os.pathsep}{os.environ['PATH']}",
               "FAKE_LOG": str(self.log), "FAKE_PLAN": str(self.plan)}
        for marker in ("CI", "GITHUB_ACTIONS", "GITLAB_CI"):
            env.pop(marker, None)
        done = subprocess.run([sys.executable, "-B", str(SCRIPT), SERVICE, *arguments], cwd=self.tree, env=env,
                              text=True, capture_output=True, timeout=120)
        return done.returncode, done.stdout.splitlines()

    def calls(self) -> list[dict[str, Any]]:
        lines = self.log.read_text(encoding="utf-8").splitlines() if self.log.exists() else []
        return [json.loads(line) for line in lines]

    def execs(self) -> list[dict[str, Any]]:
        return [call for call in self.calls() if call["argv"][:1] == ["exec"]]


class VerdictTest(VerdictCase):
    def test_e1_a_scoped_run_that_kills_everything_passes_and_is_started_from_the_service(self) -> None:
        status, lines = self.run_wrapper({"report": report(src__health_ts=[mutant("Killed"), mutant("Killed")])},
                                         "--file", "src/health.ts")
        self.assertEqual(status, 0, lines)
        self.assertEqual(lines[0], "mutation: scoped to 1 given file(s): src/health.ts")
        self.assertEqual(self.execs(), [{"argv": ["exec", "--no", "--", "stryker", "run", "--mutate", "src/health.ts"],
                                         "cwd": str((self.tree / SERVICE).resolve())}])
        self.assertEqual(lines[-1], "mutation: 2 mutants: 2 killed, 0 ignored, 0 not covered (reported, never failed); "
                                    f"passed — report {REPORT}")

    def test_e2_every_status_but_killed_ignored_and_no_coverage_fails_and_is_named(self) -> None:
        for status in ("Survived", "Timeout", "RuntimeError", "CompileError", "Pending", "Bogus"):
            with self.subTest(status=status):
                code, lines = self.run_wrapper({"report": report(src__a_ts=[mutant("Killed"), mutant(status, 7, 9)])},
                                               "--file", "src/a.ts")
                self.assertEqual(code, 1, lines)
                self.assertIn(f'mutation: {status} {SERVICE}/src/a.ts:7:9 StringLiteral → "" (report {REPORT})', lines)
                self.assertTrue(lines[-1].endswith(f"failed — report {REPORT}"), lines[-1])
        (self.tree / SERVICE / "src/a.ts").write_text(  # the Ignored mutant is at line 3: T028's one escape
            '\n// Stryker disable next-line StringLiteral: a label\nexport const a = "x";\n', encoding="utf-8")
        code, lines = self.run_wrapper({"report": report(src__a_ts=[mutant("Killed"), mutant("Ignored"),
                                                                    mutant("NoCoverage")])}, "--file", "src/a.ts")
        self.assertEqual(code, 0, lines)
        self.assertEqual(lines[-1], "mutation: 3 mutants: 1 killed, 1 ignored, 1 not covered (reported, never failed); "
                                    f"passed — report {REPORT}")

    def test_e2_two_failing_mutants_give_two_lines_and_the_last_line_counts_both_statuses(self) -> None:
        code, lines = self.run_wrapper({"report": report(src__a_ts=[mutant("Survived", 1, 1), mutant("Timeout", 2, 2),
                                                                    mutant("Killed")])}, "--file", "src/a.ts")
        self.assertEqual(code, 1)
        self.assertEqual([line for line in lines if " StringLiteral " in line], [
            f'mutation: Survived {SERVICE}/src/a.ts:1:1 StringLiteral → "" (report {REPORT})',
            f'mutation: Timeout {SERVICE}/src/a.ts:2:2 StringLiteral → "" (report {REPORT})'])
        self.assertIn("1 survived, 1 timed out; failed", lines[-1])

    def test_e3_stryker_s_exit_code_is_printed_and_never_decides(self) -> None:
        survivor = report(src__a_ts=[mutant("Survived")])
        code, lines = self.run_wrapper({"report": survivor, "exit": 0}, "--file", "src/a.ts")
        self.assertEqual(code, 1)
        self.assertIn("mutation: Stryker exited 0", " ".join(lines))
        killed = report(src__a_ts=[mutant("Killed")])
        code, lines = self.run_wrapper({"report": killed, "exit": 1}, "--file", "src/a.ts")
        self.assertEqual(code, 0, lines)
        self.assertIn("mutation: Stryker exited 1", " ".join(lines))
        schemaless = {"report": {"schemaVersion": "1.0"}}
        for plan in ({"exit": 0}, {"exit": 1}, {"exit": 2}, {"report": "not json"}, schemaless):
            with self.subTest(plan=plan):
                code, lines = self.run_wrapper(plan, "--file", "src/a.ts")
                self.assertEqual(code, 1, lines)
                code_said = plan.get("exit", 0)
                self.assertEqual(lines[-1], f"mutation: Stryker exited {code_said} and left no readable report "
                                            f"at {REPORT}; that is not a pass")

    def test_e4_zero_mutants_is_no_mutant_to_run_when_scoped_and_a_failure_when_swept(self) -> None:
        """T026: the zero is `files: {}` over a given file the wrapper's own reader says holds nothing to plant."""
        (self.tree / SERVICE / "src/a.ts").write_text("export interface A { b: string }\n", encoding="utf-8")
        code, lines = self.run_wrapper({"report": {"files": {}}}, "--file", "src/a.ts")
        self.assertEqual(code, 0, lines)
        self.assertEqual(lines[-1], "mutation: no mutant to run — src/a.ts: Stryker found no mutant in them "
                                    "(types or comments only)")
        code, lines = self.run_wrapper({"report": {"files": {}}})
        self.assertEqual(code, 1)
        self.assertEqual(lines[-1], f"mutation: Stryker found nothing to mutate in {SERVICE}; a pass on nothing is not "
                                    "a pass")

    def test_e5_scoped_means_scoped_and_a_sweep_judges_every_file(self) -> None:
        code, lines = self.run_wrapper({"report": report(src__a_ts=[mutant("Killed")])}, "--file", "src/a.ts")
        self.assertEqual(code, 0, lines)
        both = report(src__a_ts=[mutant("Killed")], src__b_ts=[mutant("Survived")])
        code, lines = self.run_wrapper({"report": both})
        self.assertEqual(code, 1)
        self.assertEqual(self.execs()[-1]["argv"], ["exec", "--no", "--", "stryker", "run"])
        self.assertIn(f'mutation: Survived {SERVICE}/src/b.ts:3:5 StringLiteral → "" (report {REPORT})', lines)

    def test_e5_a_dot_slash_file_is_judged_against_the_report_keyed_without_it(self) -> None:
        """T024: `matched` accepts `./src/x.ts`; the report is keyed `src/x.ts`, so a survivor there must still fail."""
        code, lines = self.run_wrapper({"report": report(src__x_ts=[mutant("Survived", 4, 2)])}, "--file", "./src/x.ts")
        self.assertEqual(code, 1, lines)
        self.assertIn(f'mutation: Survived {SERVICE}/src/x.ts:4:2 StringLiteral → "" (report {REPORT})', lines)

    def test_e6_every_run_starts_from_a_clean_slate_and_leaves_no_sandbox(self) -> None:
        """Teeth: skip the delete and the no-report example below passes wrongly."""
        old = self.tree / SERVICE / "reports/mutation"
        old.mkdir(parents=True)
        (old / "mutation.json").write_text(json.dumps(report(src__a_ts=[mutant("Killed")])), encoding="utf-8")
        (self.tree / SERVICE / ".stryker-tmp/sandbox-x").mkdir(parents=True)
        code, lines = self.run_wrapper({"expect_clean": True, "sandbox": True}, "--file", "src/a.ts")
        self.assertFalse(Path(str(self.log) + ".dirty").exists(), "the fake found the earlier run's output")
        self.assertEqual(code, 1, "a previous green report made a run that wrote none pass: " + str(lines))
        self.assertFalse((self.tree / SERVICE / ".stryker-tmp").exists())

    def test_e7_hold_nothing_but_the_report_and_the_sandbox_is_written_and_no_flag_loosens_the_run(self) -> None:
        """HOLD (teeth: pass `--incremental` and see it fail)."""
        def digest() -> dict[str, str]:
            return {str(p.relative_to(self.tree / SERVICE)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in sorted((self.tree / SERVICE).rglob("*")) if p.is_file()}
        before = digest()
        self.run_wrapper({"report": report(src__a_ts=[mutant("Killed")]), "sandbox": True}, "--file", "src/a.ts")
        self.run_wrapper({"report": report(src__a_ts=[mutant("Killed")])})
        after = digest()
        self.assertEqual({k: v for k, v in after.items() if not k.startswith("reports/")}, before)
        self.assertEqual([k for k in after if k.startswith("reports/")], ["reports/mutation/mutation.json"])
        for call in self.execs():
            self.assertFalse([a for a in call["argv"] if "incremental" in a or "thresholds" in a], call)


class InstallTest(VerdictCase):
    """Rule 4: install from the committed lock, never fetch; a missing tool is one setup line (T005)."""

    installed = False
    OK = {"report": report(src__a_ts=[mutant("Killed")])}

    def argvs(self) -> list[list[str]]:
        return [call["argv"] for call in self.calls()]

    def test_e1_a_fresh_clone_installs_from_the_lock_at_the_root_and_then_starts_stryker(self) -> None:
        code, lines = self.run_wrapper(self.OK, "--file", "src/a.ts")
        self.assertEqual(code, 0, lines)
        self.assertEqual(self.argvs()[0], ["ci"])
        self.assertEqual(self.calls()[0]["cwd"], str(self.tree.resolve()))
        self.assertTrue((self.tree / "node_modules/.package-lock.json").is_file())
        self.assertEqual(self.argvs()[1][:3], ["exec", "--no", "--"])
        self.assertEqual(lines.count("mutation: installing from the committed lock (npm ci)"), 1, lines)

    def test_e2_a_fresh_marker_skips_the_install_and_a_newer_manifest_or_root_lock_brings_it_back(self) -> None:
        self.install(("core", "vitest-runner"))
        self.run_wrapper(self.OK, "--file", "src/a.ts")
        self.assertEqual([a[0] for a in self.argvs()], ["exec"])
        later = time.time() + 500
        for touched in (f"{SERVICE}/package.json", "package.json", "package-lock.json"):
            with self.subTest(touched=touched):
                self.install(("core", "vitest-runner"))
                before = len(self.argvs())
                os.utime(self.tree / touched, (later, later))
                self.run_wrapper(self.OK, "--file", "src/a.ts")
                self.assertEqual(self.argvs()[before][0], "ci")
                later += 500

    def test_e3_a_failing_install_is_one_setup_line_and_stryker_is_never_started(self) -> None:
        code, lines = self.run_wrapper({**self.OK, "ci_exit": 1}, "--file", "src/a.ts")
        self.assertEqual(code, 2)
        self.assertEqual(lines[-1], "mutation: npm ci failed (exit 1); fix the install, then run this again")
        self.assertEqual(self.execs(), [])

    def test_e4_no_npm_is_one_line_and_nothing_is_created(self) -> None:
        (self.tree / ".nvmrc").write_text("24\n", encoding="utf-8")
        empty = self.root / "empty"
        empty.mkdir()
        code, lines = self.run_wrapper(self.OK, "--file", "src/a.ts", path=str(empty))
        self.assertEqual(code, 2)
        self.assertEqual(lines, ["mutation: npm is not on PATH; install Node 24 to run Stryker"])
        self.assertEqual(self.calls(), [])
        self.assertFalse((self.tree / SERVICE / "reports").exists())
        self.assertFalse((self.tree / "node_modules").exists())

    def test_e5_stryker_missing_after_the_install_is_one_line_naming_both_packages(self) -> None:
        for installs in (["core"], ["vitest-runner"], []):
            with self.subTest(installs=installs):
                shutil.rmtree(self.tree / "node_modules", ignore_errors=True)
                code, lines = self.run_wrapper({**self.OK, "installs": installs}, "--file", "src/a.ts")
                self.assertEqual(code, 2, lines)
                self.assertEqual(lines[-1], "mutation: Stryker is not installed in this project: add "
                                            "@stryker-mutator/core and @stryker-mutator/vitest-runner 10.0.0 to "
                                            f"{SERVICE}/package.json's devDependencies and run npm install")
                self.assertEqual(self.execs(), [])
                self.log.unlink()

    def test_e6_hold_nothing_is_fetched_stryker_only_starts_through_exec_no(self) -> None:
        """HOLD (teeth: drop `--no` from the command and see it fail)."""
        for files in ((), ("--file", "src/a.ts")):
            shutil.rmtree(self.tree / "node_modules", ignore_errors=True)
            self.run_wrapper(self.OK, *files)
        for argv in self.argvs():
            self.assertIn(argv[0], ("ci", "exec"), argv)
            self.assertNotIn("install", argv)
            self.assertTrue(argv[0] != "exec" or argv[1] == "--no", argv)

    def test_e7_a_swept_run_and_a_scoped_run_install_alike(self) -> None:
        for files in ((), ("--file", "src/a.ts")):
            with self.subTest(files=files):
                shutil.rmtree(self.tree / "node_modules", ignore_errors=True)
                self.log.unlink(missing_ok=True)
                code, lines = self.run_wrapper(self.OK, *files)
                self.assertEqual(self.argvs()[0], ["ci"])
                self.assertIn("mutation: installing from the committed lock (npm ci)", lines)


if __name__ == "__main__":
    unittest.main()
