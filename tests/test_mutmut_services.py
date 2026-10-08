"""S42 T031 (D223 item 2 · AC-S42-4 as amended): `mutmut-mutation.py` takes several services, runs each fully, and
fails at the end naming each failed one.

The harness is `test_mutmut_verdict`'s; its fake `uv` is read for the one change the examples need, that what it writes
under `mutants/` is looked up by the service's directory name (`FAKE_META` and `FAKE_RESULTS` map `a` to the files it
holds), since two services in one run cannot hold the same answer.
"""
from __future__ import annotations

import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

from test_mutmut_verdict import EXITED, FAKE_UV, KEY, Case, lines_of

sys.dont_write_bytecode = True
# `test_mutmut_verdict` imports `slipwai`, which reads this script on import (as `test_stryker_closure` does)
TEST_SELECTION = {"reads": ["assets/languages/python/scripts/mutmut-mutation.py",
                            "assets/toolkit/scripts/check-styles.py"]}
USAGE = "mutation: usage: mutmut-mutation.py <service> [<service> ...] [--file <path within the service> ...]"
BY_SERVICE = {'os.environ.get("FAKE_META", "{}"))': 'os.environ.get("FAKE_META", "{}")).get(os.path.basename('
                                                    'os.getcwd()), {})',
              'os.environ.get("FAKE_RESULTS", "{}"))': 'os.environ.get("FAKE_RESULTS", "{}")).get(os.path.basename('
                                                       'os.getcwd()), {})'}
SURVIVOR = {"src/pkg/a.py": {KEY: 0}}
KILLED = {"src/pkg/a.py": {KEY: 1}}


class ServicesCase(Case):
    def setUp(self) -> None:
        super().setUp()
        text = FAKE_UV
        for old, new in BY_SERVICE.items():
            self.assertIn(old, text, "test_mutmut_verdict's fake uv no longer reads its answers where this expects")
            text = text.replace(old, new)
        (self.bin / "uv").write_text(text, encoding="utf-8")
        (self.bin / "uv").chmod(0o755 | stat.S_IXUSR)
        self.a = self.make_service("apps/a")
        self.b = self.make_service("apps/b")

    def sweep(self, *services: str, answers: dict[str, dict[str, Any]]) -> subprocess.CompletedProcess[str]:
        return self.run_wrapper(*services, meta=answers, results=answers)

    def mutmut_runs(self) -> list[str]:
        return [Path(call["cwd"]).name for call in self.started_mutmut()]

    def generations(self) -> list[str]:
        return [Path(call["cwd"]).name for call in self.calls() if call["argv"][4:5] == ["python"]
                and "importlib.metadata" not in call["argv"][-1]]


class SeveralServicesTest(ServicesCase):
    def test_e1_both_services_are_generated_and_judged_one_result_line_each_then_the_summary_and_exit_one(self) -> None:
        done = self.sweep("apps/a", "apps/b", answers={"a": SURVIVOR, "b": KILLED})
        self.assertEqual(done.returncode, 1)
        self.assertEqual(self.generations(), ["a", "b"])
        self.assertEqual(self.mutmut_runs(), ["a", "b"])
        self.assertFalse(Path(str(self.log) + ".stale").exists(), "a service met a mutants/ left from an earlier one")
        lines = lines_of(done)
        results = [line for line in lines if " mutants: " in line]
        self.assertEqual(results, ["mutation: 1 mutants: 0 killed, 0 no tests (reported, never failed), 1 survived; "
                                   "failed — report apps/a/mutants/",
                                   "mutation: 1 mutants: 1 killed, 0 no tests (reported, never failed); passed "
                                   "— report apps/b/mutants/"])
        self.assertEqual(lines[-1], "mutation: 2 swept; failed: apps/a")

    def test_e2_both_green_is_the_passed_summary_and_exit_zero(self) -> None:
        done = self.sweep("apps/a", "apps/b", answers={"a": KILLED, "b": KILLED})
        self.assertEqual((done.returncode, lines_of(done)[-1]), (0, "mutation: 2 swept; passed"))

    def test_e3_both_failing_are_both_named_in_service_order(self) -> None:
        done = self.sweep("apps/b", "apps/a", answers={"a": SURVIVOR, "b": SURVIVOR})
        self.assertEqual((done.returncode, lines_of(done)[-1]), (1, "mutation: 2 swept; failed: apps/b, apps/a"))

    def test_e4_a_setup_exit_two_after_a_verdict_one_is_one_and_the_reverse_is_two(self) -> None:
        (self.b / "pyproject.toml").write_text("", encoding="utf-8")
        first = self.sweep("apps/a", "apps/b", answers={"a": SURVIVOR})
        self.assertEqual((first.returncode, lines_of(first)[-1]), (1, "mutation: 2 swept; failed: apps/a, apps/b"))
        self.assertIn("mutation: apps/b/pyproject.toml: no [tool.mutmut] table", lines_of(first))
        reverse = self.sweep("apps/b", "apps/a", answers={"a": SURVIVOR})
        self.assertEqual((reverse.returncode, lines_of(reverse)[-1]), (2, "mutation: 2 swept; failed: apps/b, apps/a"))
        self.assertEqual(self.mutmut_runs(), ["a", "a"], "a failed service does not stop the next")

    def test_e5_a_service_that_cannot_start_does_not_hold_the_lock_of_the_next(self) -> None:
        (self.b / "pyproject.toml").write_text("", encoding="utf-8")
        self.sweep("apps/b", "apps/a", answers={"a": KILLED})
        self.assertEqual(self.mutmut_runs(), ["a"])

    def test_e6_each_service_takes_its_own_lock_and_leaves_it_for_the_next_run(self) -> None:
        import fcntl
        self.sweep("apps/a", "apps/b", answers={"a": KILLED, "b": KILLED})
        for service in (self.a, self.b):
            with open(service / ".venv/mutmut-run.lock", "a", encoding="utf-8") as handle:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def test_e7_file_with_two_services_is_the_usage_line_exit_two_and_nothing_started(self) -> None:
        done = self.sweep("apps/a", "apps/b", "--file", "src/pkg/a.py", answers={"a": KILLED, "b": KILLED})
        self.assertEqual((done.returncode, done.stdout.strip()), (2, USAGE))
        self.assertEqual(self.calls(), [])

    def test_e8_hold_one_service_keeps_todays_output_with_no_summary_line(self) -> None:
        done = self.sweep("apps/a", answers={"a": KILLED})
        self.assertEqual(done.returncode, 0)
        self.assertEqual(lines_of(done), [
            f"mutation: mutmut exited 0 {EXITED}",
            "mutation: 1 mutants: 1 killed, 0 no tests (reported, never failed); passed — report apps/a/mutants/"])

    def test_e9_hold_no_service_or_an_option_first_is_the_usage_line(self) -> None:
        for arguments in ((), ("--file", "x.py"), ("apps/a", "--file")):
            with self.subTest(arguments=arguments):
                done = self.sweep(*arguments, answers={})
                self.assertEqual((done.returncode, done.stdout.strip()), (2, USAGE))


if __name__ == "__main__":
    import unittest
    unittest.main()
