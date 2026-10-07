"""R3 (AC-S26-8), the paths and the streams: a `Written to` path is matched against the committed list as a path.

`./x`, a directory and a backslash path match as the exact one does, in the verb and in the gate, which share one
normaliser (`on_list`). The verb's output survives a console that cannot write its arrows and dots.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest

from reversibility_fixture import EASY, entry, facts, gate, score, scratch

sys.dont_write_bytecode = True

TEST_SELECTION: dict[str, object] = {
    "reads": [
        "assets/toolkit/scripts/check-decisions.py",
        "assets/toolkit/scripts/check-styles.py",
        "assets/toolkit/scripts/reversibility.py",
    ],
}

LISTED = ("scripts/check-decisions.py", ".slipwai/propagated.md")
LINE = "- **Reversibility:** easy · rules 1 · " + " ".join(f"{key}={value}" for key, value in EASY.items())
SPELLINGS = ("scripts/check-decisions.py", "./scripts/check-decisions.py", "scripts/", "scripts", "./scripts/",
             "scripts\\check-decisions.py", ".\\scripts\\", "scripts//check-decisions.py")


class WrittenToPathsTest(unittest.TestCase):
    def test_e1_the_verb_scores_every_spelling_of_a_listed_path_as_migrate_file_yes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = scratch(directory, names=("reversibility.py",), listed=LISTED)
            for spelling in SPELLINGS:
                with self.subTest(spelling=spelling):
                    result = score(repo, "--scope", "S1", "--written-to", spelling, *facts())
                    self.assertEqual(0, result.returncode, result.stderr)
                    self.assertIn("migrate_file=yes", result.stdout)
                    self.assertIn("H7 migrate_file=yes", result.stderr)

    def test_e2_the_verb_leaves_a_path_that_is_not_listed_at_no(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = scratch(directory, names=("reversibility.py",), listed=LISTED)
            for other in ("README.md", "./README.md", "script", "scripts-extra/", " ", ".\\docs\\"):
                with self.subTest(other=other):
                    result = score(repo, "--scope", "S1", "--written-to", other, *facts())
                    self.assertIn("migrate_file=no", result.stdout)

    def test_e3_the_gate_refuses_migrate_file_no_over_every_spelling_of_a_listed_path(self) -> None:
        for spelling in SPELLINGS:
            with self.subTest(spelling=spelling), tempfile.TemporaryDirectory() as directory:
                repo = scratch(directory, entry(1, LINE, written=f"`{spelling}`"), listed=LISTED)
                result = gate(repo)
                self.assertEqual(1, result.returncode, result.stdout + result.stderr)
                self.assertIn("a `Written to` path is on the committed list", result.stderr)

    def test_e4_the_gate_passes_a_path_that_is_not_listed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = scratch(directory, entry(1, LINE, written="`./README.md`"), listed=LISTED)
            result = gate(repo)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)


class VerbStreamsTest(unittest.TestCase):
    def test_e5_the_verb_writes_utf_8_whatever_the_console_encoding_is(self) -> None:
        """M3: cp1252 is what a pipe gets on Windows; the arrow and the dot are not in it, and neither are in ascii."""
        with tempfile.TemporaryDirectory() as directory:
            repo = scratch(directory, names=("reversibility.py",), listed=LISTED)
            for encoding in ("cp1252", "ascii"):
                for extra in (("--raise", "hard"), ()):
                    with self.subTest(encoding=encoding, extra=extra):
                        result = subprocess.run(
                            ["python3", "-B", "scripts/reversibility.py", "--scope", "S1", *extra, *facts()],
                            cwd=repo, capture_output=True, env={**os.environ, "PYTHONIOENCODING": encoding})
                        self.assertEqual(0, result.returncode, result.stderr.decode("utf-8", "replace"))
                        text = result.stdout.decode("utf-8")
                        self.assertIn(" · rules 1 · ", text)
                        self.assertEqual(bool(extra), " → " in text)


if __name__ == "__main__":
    unittest.main()
