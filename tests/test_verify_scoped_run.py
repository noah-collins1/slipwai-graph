"""R9 (AC-S06-12): every unit named once, in one make call that keeps the jobserver.

The chosen units run as one `make <units> VERIFY_ORDER=1` launched with the jobserver's descriptors still open, so
`make -j verify-scoped` runs them at once as `make -j verify` does. The last line counts what ran and what was skipped
and says passed, or that the gate did not pass and where each failure is named; the status is the sub-make's. What ran
is read from the stand-ins' log and marker files, never from a clock: two checks that each wait, bounded, for the
other's marker file show that both started before either ended.
"""
from __future__ import annotations

import subprocess
import sys
import unittest

from scoped_fixture import LINE, ShapeCase
from stamp_fixture import git

sys.dont_write_bytecode = True

NOT_PASSED = "; the scoped gate did not pass — each failed check is named above on a line carrying ***"


class RunTest(ShapeCase):
    def named(self, run: subprocess.CompletedProcess[str]) -> tuple[list[str], list[str]]:
        """The units a run named `run` and `skip`, in the order it said them."""
        said = [line.removeprefix(LINE).split() for line in self.lines(run)]
        return [words[1] for words in said if words[0] == "run"], [words[1] for words in said if words[0] == "skip"]

    def rendezvous(self) -> dict[str, str | None]:
        directory = self.repo.parent / "rendezvous"
        directory.mkdir()
        return {"STANDIN_RENDEZVOUS": str(directory)}

    def assert_together(self, args: list[str], env: dict[str, str | None]) -> None:
        self.write_baseline({"STANDIN_NODE_VERSION": "v20.11.0"})  # a node that moved chooses every npm unit, no edit
        run = self.scoped({"STANDIN_NODE_VERSION": "v22.1.0", **env}, args)
        left = sorted(path.name for path in (self.repo.parent / "rendezvous").iterdir())
        self.assertEqual(left, ["service", "web"], "both lints did not start before either ended: " + run.stdout)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertNotIn("jobserver unavailable", run.stderr)

    def test_e1_two_checks_that_wait_for_each_other_both_start_before_either_ends(self) -> None:
        self.assert_together(["-j2"], self.rendezvous())

    def test_e1_the_pipe_jobserver_of_an_older_make_is_kept_too(self) -> None:
        """Where the jobserver is a pair of descriptors (make before 4.4's default), a sub-make started with them
        closed says `jobserver unavailable: using -j1` and the stand-ins' wait times out (teeth: `close_fds=True`)."""
        self.assert_together(["-j2", "--jobserver-style=pipe"], self.rendezvous())

    def test_e1_without_a_job_count_the_checks_run_one_at_a_time_and_say_nothing_of_a_jobserver(self) -> None:
        self.write_baseline({"STANDIN_NODE_VERSION": "v20.11.0"})
        run = self.scoped({"STANDIN_NODE_VERSION": "v22.1.0"})
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertNotIn("jobserver", run.stderr)

    def test_e2_a_failing_check_is_named_by_makes_own_line_and_the_run_says_so_last(self) -> None:
        self.edit("apps/web/src/App.tsx")
        run = self.scoped({"STANDIN_NPM_FAIL": "--workspace apps/web test"})
        self.assertNotEqual(run.returncode, 0, run.stdout)
        failed = [line for line in run.stderr.splitlines() if "***" in line]
        self.assertTrue(any("test-web" in line for line in failed), run.stderr)
        last = run.stdout.rstrip("\n").splitlines()[-1]
        self.assertEqual(last, self.scoped_lines(run)[-1])
        self.assertTrue(last.startswith(LINE) and last.endswith(NOT_PASSED), last)
        ran, skipped = self.named(run)
        self.assertIn(f"{len(ran)} run, {len(skipped)} skipped, compared with `main` at ", last)

    def test_e2_the_status_is_the_sub_makes(self) -> None:
        self.edit("apps/web/src/App.tsx")
        run = self.scoped({"STANDIN_NPM_FAIL": "--workspace apps/web test"})
        direct = subprocess.run(
            ["make", "test-web", "--no-print-directory", "-f", "Makefile", "VERIFY_ORDER=1"], cwd=self.repo,
            env=self.environment({"STANDIN_NPM_FAIL": "--workspace apps/web test"}), text=True,
            capture_output=True, timeout=120, check=False)
        self.assertNotEqual(direct.returncode, 0)
        self.assertEqual(run.returncode, direct.returncode)

    def test_e3_a_passing_run_counts_what_it_named_and_says_passed(self) -> None:
        self.edit("apps/web/src/App.tsx")
        run = self.scoped()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        ran, skipped = self.named(run)
        base = git(self.repo, "merge-base", "HEAD", "main").strip()
        short = git(self.repo, "rev-parse", "--short", base).strip()
        expected = f"{len(ran)} run, {len(skipped)} skipped, compared with `main` at {short}; passed"
        self.assertEqual(self.scoped_lines(run)[-1], LINE + expected)
        self.assertEqual(run.stdout.rstrip("\n").splitlines()[-1], LINE + expected)
        self.assertEqual((len(ran), len(skipped)), (len(set(ran)), len(set(skipped))))

    def test_e3_the_counts_are_the_lines_for_a_change_that_chose_nothing_but_the_checks_that_always_run(self) -> None:
        run = self.scoped()
        ran, skipped = self.named(run)
        closing = self.scoped_lines(run)[-1]
        self.assertTrue(closing.startswith(f"{LINE}{len(ran)} run, {len(skipped)} skipped, compared with `main` at "))
        self.assertTrue(closing.endswith("; passed"), closing)

    def test_e4_every_unit_is_named_exactly_once_in_the_lines_and_in_the_call(self) -> None:
        """HOLD over T007's selection (teeth: hand the call every target twice)."""
        self.edit("apps/web/src/App.tsx")
        run = self.scoped(self.environment_dry())
        ran, skipped = self.named(run)
        self.assertEqual(sorted(ran + skipped), sorted(set(ran + skipped)))
        (goals,) = self.called()
        self.assertEqual(sorted(goals), sorted(ran))

    def test_e4_the_call_carries_the_gates_own_output_grouping(self) -> None:
        self.edit("apps/web/src/App.tsx")
        self.scoped(self.environment_dry())
        (line,) = [line for line in self.log.read_text(encoding="utf-8").splitlines()
                   if "VERIFY_ORDER=1" in line and "verify-checks" not in line]
        self.assertIn("--output-sync=target", line.split())

    def environment_dry(self) -> dict[str, str | None]:
        return {"STANDIN_DRY": "1"}


if __name__ == "__main__":
    unittest.main()
