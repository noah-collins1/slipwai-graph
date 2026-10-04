"""Each check's output stays together where the make can (R4, AC-S04-10 to -12, -16).

GNU Make 4.0 and later list `output-sync` among their features; an example that needs the feature skips, saying so,
on a make that does not. A check's lines are written by a stand-in `uv` (`tests/parallel_gate.py`) that prints three
lines with a barrier between each, so without grouping two checks' lines alternate; evidence is the output read back.
"""
from __future__ import annotations

import os
import re
import signal
import subprocess
import sys
import tempfile
import threading
import unittest

from parallel_gate import ParallelGateTestCase, barrier_events, has_output_sync, line_events, log_text
from support import FactoryTestCase
from test_parallel_gate_run import FAILED, gate_line

from slipwai.catalog import CATALOG

sys.dont_write_bytecode = True

GUARDED = "$(if $(filter output-sync,$(.FEATURES)),--output-sync=target)"
FORCE: dict[str, str | None] = {"VERIFY_FORCE": "1"}


def tagged(lines: list[str]) -> list[str]:
    """The check each `<tool> line <n>` line belongs to, consecutive repeats folded into one."""
    tags: list[str] = []
    for line in lines:
        match = re.fullmatch(r"(\w+) line \d+", line)
        if match and (not tags or tags[-1] != match.group(1)):
            tags.append(match.group(1))
    return tags


class GroupedOutputTest(ParallelGateTestCase):
    SHAPE = "plain"

    def setUp(self) -> None:
        if not has_output_sync():
            self.skipTest("this make does not list output-sync among its features")
        super().setUp()

    def test_e1_each_checks_lines_are_contiguous_under_j(self) -> None:
        """AC-S04-10: two checks, three lines each with a barrier between, stay contiguous."""
        code, lines = self.make_merged("-j", "verify", env={**FORCE, "STANDIN_LINES": "3", "STANDIN_BARRIER": "1"})
        self.assertEqual(code, 0, "\n".join(lines))
        met = barrier_events(self.log).count("met")
        self.assertEqual(met, 8, "the checks did not run together\n" + log_text(self.log))
        for tool in ("ruff", "mypy"):
            self.assertEqual(sum(1 for line in lines if re.fullmatch(rf"{tool} line \d", line)), 3)
        self.assertEqual(sorted(tagged(lines)), ["mypy", "ruff"], "the checks' lines interleave:\n" + "\n".join(lines))

    def test_e3_a_serial_run_shows_a_checks_first_line_before_its_last_is_written(self) -> None:
        """HOLD (AC-S04-12): the stand-in prints line one, then waits, bounded, for this test to have read it from the
        pipe. Teeth: `--output-sync=target` on the sub-make is not held at one job by GNU Make 4.4.1, so it cannot
        falsify this; `MAKEFLAGS += --output-sync=recurse` at the top of the Makefile holds the line and fails it."""
        child = subprocess.Popen(
            ["make", "verify"], cwd=self.repo,
            env=self.environment({**FORCE, "STANDIN_WAIT_FILE": str(self.log) + ".go"}),
            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True,
        )
        stop = threading.Timer(120, os.killpg, (child.pid, signal.SIGKILL))  # a bound, not a wait
        stop.start()
        try:
            assert child.stdout is not None
            for line in child.stdout:
                if line.strip() == "ruff line 1":
                    open(str(self.log) + ".go", "w", encoding="utf-8").close()
                    break
            else:
                self.fail("the first line never reached the reader")
            rest = child.stdout.read()
            self.assertEqual(child.wait(), 0, rest)
        finally:
            stop.cancel()
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGKILL)
        self.assertEqual(line_events(self.log), ["seen"], log_text(self.log))


# The two ways the variable reaches a make that did not write it: its command line, and the environment with `-e`.
WAYS: dict[str, tuple[tuple[str, ...], dict[str, str | None]]] = {
    "command line": (("-j", "verify", "VERIFY_GROUP=-i"), {}),
    "environment with -e": (("-e", "-j", "verify"), {"VERIFY_GROUP": "-i"}),
}


class GroupingVariableIsTheMakefilesOwnTest(ParallelGateTestCase):
    SHAPE = "plain"

    def test_e5_a_red_tree_stays_red_whatever_the_variable_says(self) -> None:
        """AC-S04-82: `-i` handed to the sub-make through `VERIFY_GROUP` would make it ignore the failures; each way
        exits non-zero, ends on the failed-run line, writes no stamp, and the next plain run runs in full."""
        for way, (args, env) in WAYS.items():
            with self.subTest(way=way):
                self.forget_log()
                code, lines = self.make_merged(*args, env={**env, "STANDIN_FAIL_TOOLS": "ruff pytest"})
                self.assertNotEqual(code, 0, "\n".join(lines))
                self.assertRegex(gate_line(lines)[0], FAILED, "\n".join(lines))
                self.assertNotIn("verify: all gates passed", lines)
                self.assertEqual(self.stamps(), [])
                self.forget_log()
                self.assertNotEqual(self.make("verify", env={"STANDIN_FAIL_TOOLS": "ruff pytest"}).returncode, 0)

    def test_e6_a_green_tree_passes_both_ways_and_groups_as_without_the_variable(self) -> None:
        """AC-S04-82, green half (a hold; teeth: `override` taken off the variable, which the red test also sees)."""
        if not has_output_sync():
            self.skipTest("this make does not list output-sync among its features")
        for way, (args, env) in WAYS.items():
            with self.subTest(way=way):
                self.forget_log()
                code, lines = self.make_merged(
                    *args, env={**env, **FORCE, "STANDIN_LINES": "3", "STANDIN_BARRIER": "1"})
                self.assertEqual(code, 0, "\n".join(lines))
                self.assertEqual(sorted(tagged(lines)), ["mypy", "ruff"], "lines interleave:\n" + "\n".join(lines))


class MakefileTextTest(FactoryTestCase):
    def assert_nothing_newer(self, makefile: str) -> None:
        """No `.WAIT`, no `.NOTPARALLEL` with a prerequisite, grouping named only in the one guarded expression."""
        outside = makefile.replace(GUARDED, "")
        self.assertNotRegex(outside, r"output-sync|(?<![\w-])-O\b", "grouping named outside its guarded expression")
        self.assertNotIn(".WAIT", makefile)
        self.assertNotRegex(makefile, r"^\.NOTPARALLEL:[ \t]*\S", "a `.NOTPARALLEL` names a prerequisite")

    def test_e2_the_option_is_named_only_behind_a_test_of_the_makes_features(self) -> None:
        """AC-S04-11: the one guarded expression, read from the generated text (3.81 is read, not run)."""
        with tempfile.TemporaryDirectory() as directory:
            makefile = (self.generate(directory, "one", "standard", "python", http="none") / "Makefile").read_text()
        self.assertIn(f"override VERIFY_GROUP := {GUARDED}\n", makefile)
        recipe = re.search(r"^verify:.*\n((?:\t.*\n)+)", makefile, re.M)
        assert recipe is not None
        self.assertIn('"$(MAKE)" $(VERIFY_GROUP) --no-print-directory', recipe.group(1))
        self.assert_nothing_newer(makefile)

    def test_e4_every_starter_names_nothing_newer_than_the_guarded_grouping(self) -> None:
        """HOLD (AC-S04-16; teeth: `.WAIT` added to the generated text): every backend x http x frontend x profile."""
        with tempfile.TemporaryDirectory() as directory:
            for backend in CATALOG["backends"]:
                for http in (None, "none"):
                    for frontend in ("none", "react-vite"):
                        for profile in ("standard", "event-modelling"):
                            with self.subTest(backend=backend, http=http, frontend=frontend, profile=profile):
                                axes = {} if http is None else {"http": http}
                                name = f"{backend}-{http or 'with'}-{frontend}-{profile}"
                                repo = self.generate(directory, name, profile, backend, frontend, **axes)
                                self.assert_nothing_newer((repo / "Makefile").read_text())


if __name__ == "__main__":
    unittest.main()
