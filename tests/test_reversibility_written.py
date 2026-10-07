"""T021 (A2; AC-S26-8): every path a `Written to` value names is looked up on the committed list.

Backticked and bare paths alike, separated by `,`, `;` or ` and `, and a glob that matches a listed path: a listed
file written any of these ways is `migrate_file=yes`, in the verb and in the gate. The lookup only ever raises a
tier, so it reads every candidate the value could name, and every path the gate's own `paths_of` reads is among them.
"""
from __future__ import annotations

import sys
import tempfile
import unittest

from reversibility_fixture import EASY, SCRIPTS, entry, facts, gate, score, scratch
from test_reversibility_gate import loaded

sys.dont_write_bytecode = True
LISTED = ("scripts/check-decisions.py", "Makefile")
LINE = "- **Reversibility:** easy · rules 1 · " + " ".join(f"{key}={value}" for key, value in EASY.items())
NAMED = ("`README.md`, scripts/check-decisions.py", "README.md, `docs/x.md`; scripts/check-decisions.py",
         "README.md; scripts/check-decisions.py", "README.md and scripts/check-decisions.py",
         "`README.md` and Makefile", "README.md;Makefile", "scripts/*.py", "`scripts/check-*.py`",
         "scripts/check-decisions.p?", "SCRIPTS/*", "Make[f]ile", "`README.md`, `scripts/[cd]*`")
NOT_NAMED = ("README.md", "docs/*.md", "README.md; docs/x and docs/y", "`scripts-old/*`", "brand and design")


class WrittenToEveryPathTest(unittest.TestCase):
    def test_e1_the_verb_finds_a_listed_path_however_the_value_names_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = scratch(directory, names=("reversibility.py",), listed=LISTED)
            for value in NAMED:
                with self.subTest(value=value):
                    result = score(repo, "--scope", "S1", "--written-to", value, *facts())
                    self.assertEqual(0, result.returncode, result.stderr)
                    self.assertIn("migrate_file=yes", result.stdout)

    def test_e2_the_verb_leaves_a_value_naming_no_listed_path_at_no(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = scratch(directory, names=("reversibility.py",), listed=LISTED)
            for value in NOT_NAMED:
                with self.subTest(value=value):
                    result = score(repo, "--scope", "S1", "--written-to", value, *facts())
                    self.assertIn("migrate_file=no ", result.stdout)

    def test_e3_the_gate_refuses_migrate_file_no_however_the_value_names_a_listed_path(self) -> None:
        for value in NAMED:
            with self.subTest(value=value), tempfile.TemporaryDirectory() as directory:
                result = gate(scratch(directory, entry(1, LINE, written=value), listed=LISTED))
                self.assertEqual(1, result.returncode, result.stdout + result.stderr)
                self.assertIn("a `Written to` path is on the committed list", result.stderr)

    def test_e4_every_path_the_gate_reads_is_one_the_list_lookup_reads(self) -> None:
        held, verb = (loaded(SCRIPTS / name) for name in ("check-decisions.py", "reversibility.py"))
        for value in (*NAMED, *NOT_NAMED, "a, b", "a and b", "", "``", " a ;; b ", "`a, b`"):
            with self.subTest(value=value):
                self.assertLessEqual(set(held.paths_of(value)), set(verb.written_paths(value)))


if __name__ == "__main__":
    unittest.main()
