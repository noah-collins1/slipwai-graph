"""S41 T031 (D212 items 5 and 7): the wrapper's setup and output edges.

L1 a missing `stryker` binary is a setup line; L2 a report that could not be cleared is never this run's; L3 two
wrappers on one fresh clone run one install; L4 every line survives a cp1252 stdout. (L5, `check-imports`, is in
`test_stryker_after_run`.) The fixtures are `test_stryker_verdict`'s.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest

from test_stryker_list import SCRIPT, project
from test_stryker_verdict import REPORT, SERVICE, VerdictCase, mutant, report

sys.dont_write_bytecode = True
TEST_SELECTION = {"reads": ["assets/languages/typescript/scripts/stryker-mutation.py"]}
OK = {"report": report(src__a_ts=[mutant("Killed")])}


class EdgesTest(VerdictCase):
    def test_l1_a_missing_stryker_binary_is_the_setup_line_and_exit_2_never_1(self) -> None:
        (self.tree / "node_modules/.bin/stryker").unlink()
        code, lines = self.run_wrapper(OK, "--file", "src/a.ts")
        self.assertEqual(code, 2, lines)
        self.assertEqual(lines[-1], "mutation: Stryker is not installed in this project: add @stryker-mutator/core and "
                                    f"@stryker-mutator/vitest-runner 10.0.0 to {SERVICE}/package.json's "
                                    "devDependencies and run npm install")
        self.assertEqual(self.execs(), [])

    def test_l2_a_previous_report_that_could_not_be_removed_is_exit_2_and_stryker_is_not_started(self) -> None:
        if os.geteuid() == 0:
            self.skipTest("root can remove what a read-only directory holds")
        old = self.tree / SERVICE / "reports/mutation"
        old.mkdir(parents=True)
        (old / "mutation.json").write_text(json.dumps(report(src__a_ts=[mutant("Killed")])), encoding="utf-8")
        old.chmod(0o555)
        self.addCleanup(old.chmod, 0o755)
        code, lines = self.run_wrapper(OK, "--file", "src/a.ts")
        self.assertEqual(code, 2, lines)
        self.assertEqual(lines[-1], f"mutation: the previous report {REPORT} could not be removed; remove it, then run "
                                    "this again")
        self.assertEqual(self.execs(), [])

    def test_l4_every_line_survives_a_cp1252_stdout(self) -> None:
        self.plan.write_text(json.dumps({"report": report(src__a_ts=[mutant("Survived", replacement="→ ✓")])}),
                             encoding="utf-8")
        env = {**os.environ, "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}", "FAKE_LOG": str(self.log),
               "FAKE_PLAN": str(self.plan), "PYTHONIOENCODING": "cp1252"}
        for marker in ("CI", "GITHUB_ACTIONS", "GITLAB_CI"):
            env.pop(marker, None)
        done = subprocess.run([sys.executable, "-B", str(SCRIPT), SERVICE, "--file", "src/a.ts"], cwd=self.tree,
                              env=env, encoding="cp1252", capture_output=True, timeout=120)
        self.assertEqual((done.returncode, done.stderr), (1, ""))
        self.assertIn(f"mutation: Survived {SERVICE}/src/a.ts:3:5 StringLiteral ? ? ? (report {REPORT})",
                      done.stdout.splitlines())
        self.assertTrue(done.stdout.splitlines()[-1].endswith(f"failed — report {REPORT}"))


class LockTest(VerdictCase):
    installed = False

    def test_l3_two_wrappers_on_one_fresh_clone_run_one_install_between_them(self) -> None:
        project(self.tree, "apps/other")
        (self.tree / "apps/other/package.json").write_text("{}", encoding="utf-8")
        self.plan.write_text(json.dumps({**OK, "ci_sleep": 1.5}), encoding="utf-8")
        env = {**os.environ, "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}", "FAKE_LOG": str(self.log),
               "FAKE_PLAN": str(self.plan)}
        for marker in ("CI", "GITHUB_ACTIONS", "GITLAB_CI"):
            env.pop(marker, None)
        running = [subprocess.Popen([sys.executable, "-B", str(SCRIPT), service, "--file", "src/a.ts"], cwd=self.tree,
                                    env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                   for service in (SERVICE, "apps/other")]
        outputs = [one.communicate(timeout=120)[0] for one in running]
        self.assertEqual([one.returncode for one in running], [0, 0], outputs)
        installs = [call["argv"] for call in self.calls() if call["argv"][0] in ("ci", "ci-done")]
        self.assertEqual(installs, [["ci"], ["ci-done"]], "two installs ran on one node_modules")
        self.assertEqual(len(self.execs()), 2)


if __name__ == "__main__":
    unittest.main()
