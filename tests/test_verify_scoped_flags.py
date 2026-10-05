"""T039 (R4, R5, R7 · AC-S06-2, -5, -8; D140 point 2, D146): text and conditions that reach make through `MAKEFLAGS`.

`verify-stamp.py` holds one predicate over the `MAKEFLAGS` a recipe is handed: the letters `k`, `s`, `w` and the idle
letters, a job count, the jobserver's words, `--no-print-directory` and an output-sync word are allowed, and the first
word that is anything else is named. The scoped run is the full gate on it, and `make verify` writes neither stamp nor
baseline under it. Both ask the one function.
"""
from __future__ import annotations

import sys
from pathlib import Path

from scoped_fixture import FULL, TAIL
from stamp_fixture import load_script
from test_verify_scoped_baseline import BaselineTest
from test_verify_scoped_sum import RuleCase

sys.dont_write_bytecode = True

WORDS = ", which can add text or conditions the factory did not write; " + TAIL
PATTERN = ["--eval=scripts/event-model/%.json: FORCE ; @! grep -rq FORBIDDEN apps/web/src", "--eval=FORCE:"]
EXPLICIT = ["--eval=check-drawio: lint-docs", "--eval=lint-docs: ; @! grep -rq FORBIDDEN apps/web/src"]
ESCAPED = r"--eval=scripts/event-model/%.json:\ FORCE\ ;\ @!\ grep\ -rq\ FORBIDDEN\ apps/web/src --eval=FORCE:"
ALLOWED = ("", "s -- VERIFY_FORCE=1", "-- VERIFY_FORCE=", "k -j2 -- VERIFY_FORCE=0 VERIFY_FORCE=1",
           "k", "s", "w", "ks", "i", "n", "t", "q", "-j4", "-j", "--jobserver-auth=3,4",
           "--jobserver-fifo=/tmp/fifo", "--no-print-directory", "-Otarget", "--output-sync=recurse", "-O",
           "ks --no-print-directory -j4 --jobserver-auth=3,4 -Otarget", "-k", "-ks",
           "-l", "-l2", "-l2.5", "--load-average", "--load-average=2.5", "--max-load", "--max-load=3", "-j4 -l2",
           "k -l0.5 -- VERIFY_FORCE=1")  # D152: the load limit changes when a job starts, never what a recipe runs
REFUSED = {
    "--eval=x:": "--eval=x:", "e": "e", "ke": "ke", "r": "r", "R": "R", "B": "B", "W": "W", "o": "o", "L": "L",
    "s -- VERIFY_FORCE=1 A=1": "--", "-- VERIFY_FORCE_NOT=1": "--", "k -- A=1 VERIFY_FORCE=1": "--",
    "k -I inc": "-I", "--include-dir=inc": "--include-dir=inc", "-W foo": "-W", "-o foo": "-o",
    "--trace": "--trace", "-lx": "-lx", "--load-average=x": "--load-average=x", "--load-averages": "--load-averages",
    "-l2 -e": "-e", "--shuffle": "--shuffle", "k -- A=1": "--", "-j4 -- A=1": "--", "-Onone -e": "-e",
}


class PredicateTest(RuleCase):
    def problem(self, flags: str) -> str | None:
        return load_script(self.repo).makeflags_problem({"MAKEFLAGS": flags})

    def test_e2_the_allowed_words_are_no_problem(self) -> None:
        for flags in ALLOWED:
            with self.subTest(flags=flags):
                self.assertIsNone(self.problem(flags))

    def test_e1_the_first_word_that_is_not_allowed_is_named(self) -> None:
        for flags, word in REFUSED.items():
            with self.subTest(flags=flags):
                found = self.problem(flags)
                self.assertIsNotNone(found)
                self.assertIn("`" + word + "`", found or "")

    def test_e1_gnumakeflags_is_asked_too(self) -> None:
        stamp = load_script(self.repo)
        self.assertIn("`--eval=x:`", stamp.makeflags_problem({"GNUMAKEFLAGS": "--eval=x:"}) or "")
        self.assertIsNone(stamp.makeflags_problem({"GNUMAKEFLAGS": "-k -j2"}))

    def test_e1_a_word_cannot_forge_a_line(self) -> None:
        found = self.problem("--eval=a\nverify-scoped: forged " + "x" * 200) or ""
        self.assertNotIn("\n", found)
        self.assertLess(len(found), 300)


class ScopedConditionsTest(RuleCase):
    def setUp(self) -> None:
        super().setUp()
        self.fresh()

    def fresh(self) -> None:
        """The branch cut again with its baseline and the forbidden edit, as no earlier run left it."""
        self.reset()
        self.trunk(change=lambda _repo: None)
        self.forbidden()

    def full(self, run: object, prefix: str) -> None:
        first = self.scoped_lines(run)[0]  # type: ignore[arg-type]
        self.assertTrue(first.startswith(FULL + "make was run with `" + prefix), first)
        self.assertTrue(first.endswith(WORDS), first)
        self.assertEqual(len(self.verify_calls()), 1)
        self.assertEqual(self.lines(run), [])  # type: ignore[arg-type]

    def test_e1_a_command_line_eval_pattern_rule_is_the_full_gate(self) -> None:
        self.full(self.scoped(args=PATTERN), "--eval=")

    def test_e1_a_command_line_eval_prerequisite_is_the_full_gate(self) -> None:
        self.full(self.scoped(args=EXPLICIT), "--eval=")

    def test_e1_an_eval_in_makeflags_in_the_environment_is_the_full_gate(self) -> None:
        self.full(self.scoped(env={"MAKEFLAGS": ESCAPED}), "--eval=")

    def test_e1_an_eval_in_gnumakeflags_is_the_full_gate(self) -> None:
        self.full(self.scoped(env={"GNUMAKEFLAGS": ESCAPED}), "--eval=")

    def test_e1_a_variable_on_the_command_line_is_the_full_gate(self) -> None:
        self.full(self.scoped(args=["MODEL_INSTALLED="]), "--`")

    def test_e1_an_include_directory_and_an_environment_override_are_the_full_gate(self) -> None:
        self.full(self.scoped(args=["-I", "inc"]), "-I")
        self.fresh()
        self.full(self.scoped(args=["-e"]), "e")

    def test_d147_verify_force_on_the_command_line_is_not_refused_by_the_predicate(self) -> None:
        run = self.scoped(args=["VERIFY_FORCE=1"])
        self.assertNotIn("which can add text", run.stdout)

    def test_e2_a_job_count_the_jobserver_and_quiet_flags_stay_scoped(self) -> None:
        for args in (["-j2"], ["-k", "-s", "-w"], ["--no-print-directory"], ["-Otarget"], ["--output-sync=recurse"],
                     ["-k", "-j3", "-Onone"]):
            with self.subTest(args=args):
                self.fresh()
                run = self.scoped(args=args)
                self.assertNotIn("which can add text", run.stdout)
                self.assertEqual(self.verify_calls(), [], run.stdout)


class StampDeclinesTest(BaselineTest):
    def stamp_files(self) -> list[Path]:
        return sorted((self.repo / ".git" / "slipwai").glob("verify-stamp-*.json"))

    def test_e3_a_full_green_run_under_an_eval_writes_no_stamp_and_no_baseline(self) -> None:
        for args in (["--eval=override SHELL := /bin/sh"], ["VERIFY_NOTHING=1"], ["-e"]):
            with self.subTest(args=args):
                self.green()  # a stamp and a baseline stand, which the run must not leave as its own
                run = self.run_gate(None, args)
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                self.assertEqual(self.stamp_files(), [])
                self.assertIsNone(self.baseline_path())
                said = [line for line in run.stdout.splitlines() if "was not recorded" in line]
                self.assertEqual(len(said), 1, run.stdout)
                self.assertIn("which can add text or conditions the factory did not write", said[0])

    def test_d147_a_forced_green_run_writes_the_stamp_and_the_baseline(self) -> None:
        """The spelling the gates page gives, `make verify VERIFY_FORCE=1`, is `MAKEFLAGS=[s -- VERIFY_FORCE=1]`."""
        run = self.run_gate(None, ["VERIFY_FORCE=1"])
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(len(self.stamp_files()), 1)
        self.assertIsNotNone(self.baseline_path())
        self.assertNotIn("was not recorded", run.stdout)

    def test_e3_a_plain_green_run_still_writes_both(self) -> None:
        self.green()
        self.assertEqual(len(self.stamp_files()), 1)
        self.assertIsNotNone(self.baseline_path())
