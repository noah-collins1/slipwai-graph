"""R1 (AC-S26-1 to -7, -14, -17): the verb scores declared facts into the `Reversibility:` line.

It runs as a `python3 -B` subprocess in a scratch project, the way a generated project holds it.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from reversibility_fixture import EASY, facts, score

sys.dont_write_bytecode = True

SLICE = "S26-reversibility-line"
HARD = ("contract", "schema", "auth", "customer_visible", "export", "ci_workflow", "migrate_file")


@contextmanager
def project() -> Iterator[Path]:
    from reversibility_fixture import scratch
    with tempfile.TemporaryDirectory() as directory:
        yield scratch(directory, names=("reversibility.py",))


class VerbTest(unittest.TestCase):
    def tier(self, *arguments: str, scope: str = SLICE) -> str:
        with project() as repo:
            result = score(repo, "--scope", scope, *arguments)
        self.assertEqual(result.returncode, 0, result.stderr)
        line = result.stdout.strip()
        self.assertTrue(line.startswith("- **Reversibility:** "), line)
        return line.split("**Reversibility:** ")[1].split(" · ")[0]

    def test_e1_the_acceptance_facts_are_easy_and_the_line_is_in_the_closed_order(self) -> None:
        with project() as repo:
            result = score(repo, "--scope", SLICE, *reversed(facts()))
        self.assertEqual(result.stdout, "- **Reversibility:** easy · rules 1 · " + " ".join(
            f"{key}={value}" for key, value in EASY.items()) + "\n")
        self.assertEqual(len(result.stderr.strip().splitlines()), 1)

    def test_e2_each_hard_fact_alone_is_hard(self) -> None:
        for key in HARD:
            with self.subTest(fact=key):
                self.assertEqual(self.tier(*facts(**{key: "yes"})), "hard")

    def test_e3_rollback_complexity_sets_the_tier(self) -> None:
        for value, tier in (("days", "hard"), ("needs-migration", "hard"), ("hours", "guarded"), ("trivial", "easy")):
            with self.subTest(value=value):
                self.assertEqual(self.tier(*facts(rollback_complexity=value)), tier)

    def test_e4_no_flag_is_guarded_and_no_code_is_easy(self) -> None:
        self.assertEqual(self.tier(*facts(behind_flag="no")), "guarded")
        self.assertEqual(self.tier(*facts(behind_flag="no-code")), "easy")

    def test_e5_a_changed_flag_default_is_guarded(self) -> None:
        self.assertEqual(self.tier(*facts(flag_default="yes")), "guarded")

    def test_e6_the_scope_sets_the_dependants(self) -> None:
        self.assertEqual(self.tier(*facts(), scope="S1-a, S2-b"), "guarded")
        self.assertEqual(self.tier(*facts(), scope="global"), "hard")
        self.assertEqual(self.tier(*facts(), scope="whatever"), "hard")
        self.assertEqual(self.tier(*facts(), scope="S01-S03"), "hard")

    def test_e7_a_missing_or_unaccepted_fact_is_hard_and_named_on_the_line(self) -> None:
        with project() as repo:
            result = score(repo, "--scope", SLICE, *facts(schema=""))
            self.assertIn("hard · rules 1", result.stdout)
            self.assertIn(" schema=missing ", result.stdout)
            result = score(repo, "--scope", SLICE, *facts(rollback_complexity="weeks"))
            self.assertIn("hard · rules 1", result.stdout)
            self.assertTrue(result.stdout.strip().endswith("rollback_complexity=weeks"))

    def test_e8_a_stray_repeated_or_malformed_argument_is_usage(self) -> None:
        cases = (["size=large"], ["urgency=high"], ["schema=no"], ["stray"], ["schema="], ["--raise", "easy"],
                 ["--raise", "guarded", "--raise", "hard"])
        for extra in cases:
            with self.subTest(extra=extra), project() as repo:
                result = score(repo, "--scope", SLICE, *facts(), *extra)
                self.assertEqual((result.returncode, result.stdout), (2, ""), extra)
                self.assertEqual(len(result.stderr.strip().splitlines()), 1)
                if "=" in extra[0] and extra[0] != "schema=":
                    self.assertIn(extra[0].split("=")[0], result.stderr)
        with project() as repo:
            self.assertEqual(score(repo, *facts()).returncode, 2)

    def test_e9_the_d54_fixture_is_hard_from_declared_facts_alone(self) -> None:
        arguments = facts(ci_workflow="yes", migrate_file="yes", behind_flag="no-code")
        with project() as repo:
            result = score(repo, "--scope", SLICE, "--written-to", "`specs/f/decisions.md`, `specs/f/spec.md`",
                           *arguments)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("hard · rules 1 · ", result.stdout)
        self.assertIn("ci_workflow=yes migrate_file=yes behind_flag=no-code", result.stdout)
        self.assertIn("ci_workflow", result.stderr)

    def test_e10_raise_writes_each_step_and_never_lowers(self) -> None:
        self.assertEqual(self.tier(*facts(), "--raise", "hard"), "easy → guarded → hard")
        self.assertEqual(self.tier(*facts(), "--raise", "guarded"), "easy → guarded")
        with project() as repo:
            result = score(repo, "--scope", SLICE, *facts(contract="yes"), "--raise", "guarded")
        self.assertEqual((result.returncode, result.stdout), (2, ""))
        self.assertIn("lower", result.stderr)


if __name__ == "__main__":
    unittest.main()
