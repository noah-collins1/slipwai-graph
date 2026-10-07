"""T020 (A1, A3, A4, B7; AC-S26-8): the committed-list lookup reads a `Written to` path as a path in the project.

Every spelling of a listed path is found — absolute or `..` that land inside the project, another case, under a listed
directory — and one outside the project never is. A list that names nothing (empty, comments only) is no list, a
byte-order mark is not part of the first path, and a `layout.delivery` that names no directory in the project is one
line, never a traceback. Each case runs in the verb and in the gate, as `python3 -B` subprocesses.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from reversibility_fixture import EASY, entry, facts, gate, score, scratch

sys.dont_write_bytecode = True

TEST_SELECTION: dict[str, object] = {
    "reads": [
        "assets/toolkit/scripts/check-decisions.py",
        "assets/toolkit/scripts/check-styles.py",
        "assets/toolkit/scripts/reversibility.py",
    ],
}

LISTED = ("scripts/check-decisions.py",)
LINE = "- **Reversibility:** easy · rules 1 · " + " ".join(f"{key}={value}" for key, value in EASY.items())
HARD = LINE.replace("easy", "hard", 1).replace("migrate_file=no", "migrate_file=yes")


def project(directory: str, log: str = "", **options: object) -> Path:
    """A scratch project one level inside `directory`, so a path outside it can exist beside it."""
    (Path(directory) / "other/scripts").mkdir(parents=True)
    (Path(directory) / "other/scripts/check-decisions.py").write_text("", encoding="utf-8")
    (Path(directory) / "project").mkdir()
    return scratch(str(Path(directory) / "project"), log, **options).resolve()  # type: ignore[arg-type]


def inside(repo: Path) -> tuple[str, ...]:
    """Spellings of the listed file that land inside the project."""
    return (f"{repo}/scripts/check-decisions.py", f"{repo}/./scripts/../scripts/check-decisions.py",
            "scripts/../scripts/check-decisions.py", "README.md/../scripts/check-decisions.py",
            f"../{repo.name}/scripts/check-decisions.py", "SCRIPTS/Check-Decisions.PY", "Scripts\\check-decisions.py")


OUTSIDE = ("../other/scripts/check-decisions.py", "../scripts/check-decisions.py", "/scripts/check-decisions.py")


class VerbListTest(unittest.TestCase):
    def verb(self, repo: Path, written: str) -> tuple[int, str, str]:
        result = score(repo, "--scope", "S1", "--written-to", written, *facts())
        return result.returncode, result.stdout, result.stderr

    def test_e1_every_spelling_inside_the_project_of_a_listed_path_is_on_the_list(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = project(directory, names=("reversibility.py",), listed=LISTED)
            for spelling in inside(repo):
                with self.subTest(spelling=spelling):
                    code, out, err = self.verb(repo, spelling)
                    self.assertEqual(0, code, err)
                    self.assertIn("migrate_file=yes", out)

    def test_e2_a_path_outside_the_project_is_never_on_the_list(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = project(directory, names=("reversibility.py",), listed=LISTED)
            for spelling in (*OUTSIDE, f"{repo.parent}/other/scripts/check-decisions.py"):
                with self.subTest(spelling=spelling):
                    self.assertIn("migrate_file=no ", self.verb(repo, spelling)[1] + " ")

    def test_e3_a_listed_directory_covers_the_files_under_it_with_or_without_its_slash(self) -> None:
        for listed in (("scripts/",), ("scripts",), ("./Scripts//",)):
            with self.subTest(listed=listed), tempfile.TemporaryDirectory() as directory:
                repo = project(directory, names=("reversibility.py",), listed=listed)
                self.assertIn("migrate_file=yes", self.verb(repo, "scripts/check-decisions.py")[1])
                self.assertIn("migrate_file=no ", self.verb(repo, "scripts-old/x.py")[1] + " ")

    def test_e4_a_byte_order_mark_is_not_part_of_the_first_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = project(directory, names=("reversibility.py",), listed=())
            (repo / ".slipwai/propagated").write_text("﻿scripts/check-decisions.py\n", encoding="utf-8")
            self.assertIn("migrate_file=yes", self.verb(repo, "scripts/check-decisions.py")[1])

    def test_e5_an_empty_or_comment_only_list_is_no_list(self) -> None:
        for text in ("", "\n\n", "# the method's files\n", "﻿# nothing yet\n  \n"):
            with self.subTest(text=text), tempfile.TemporaryDirectory() as directory:
                repo = project(directory, names=("reversibility.py",), listed=())
                (repo / ".slipwai/propagated").write_text(text, encoding="utf-8")
                code, out, err = self.verb(repo, "README.md")
                self.assertEqual(0, code, err)
                self.assertIn("migrate_file=no-list", out)
                self.assertTrue(out.startswith("- **Reversibility:** hard ·"), out)

    def test_e6_an_unreadable_layout_delivery_is_one_line_and_no_list(self) -> None:
        for delivery in ("deli\u0000very", "../elsewhere", "/etc"):
            with self.subTest(delivery=delivery), tempfile.TemporaryDirectory() as directory:
                repo = project(directory, names=("reversibility.py",), origin="adopted", delivery=delivery)
                code, out, err = self.verb(repo, "README.md")
                self.assertEqual(0, code, err)
                self.assertNotIn("Traceback", err)
                self.assertIn("migrate_file=no-list", out)
                said = [row for row in err.splitlines() if "layout.delivery" in row]
                self.assertEqual(1, len(said), err)


class GateListTest(unittest.TestCase):
    def gate_over(self, written: str, listed: tuple[str, ...] = LISTED, line: str = LINE) -> tuple[int, str]:
        with tempfile.TemporaryDirectory() as directory:
            repo = project(directory, listed=listed)
            log = "# Decisions\n\n" + entry(1, line, written=written.replace("{repo}", str(repo)))
            (repo / "specs/f/decisions.md").write_text(log, encoding="utf-8")
            result = gate(repo)
        return result.returncode, result.stdout + result.stderr

    def test_e1_the_gate_refuses_migrate_file_no_over_every_spelling_inside_the_project(self) -> None:
        for spelling in ("{repo}/scripts/check-decisions.py", "scripts/../scripts/check-decisions.py",
                         "SCRIPTS/Check-Decisions.PY", "../project/scripts/check-decisions.py"):
            with self.subTest(spelling=spelling):
                code, said = self.gate_over(f"`{spelling}`")
                self.assertEqual(1, code, said)
                self.assertIn("a `Written to` path is on the committed list", said)

    def test_e2_the_gate_passes_a_path_outside_the_project(self) -> None:
        code, said = self.gate_over("`../other/scripts/check-decisions.py`")
        self.assertEqual(0, code, said)

    def test_e3_the_gate_reads_a_listed_directory_and_a_byte_order_mark(self) -> None:
        for listed in (("scripts",), ("scripts/",), ("﻿scripts/check-decisions.py",)):
            with self.subTest(listed=listed):
                code, said = self.gate_over("`scripts/check-decisions.py`", listed=listed)
                self.assertEqual(1, code, said)
                self.assertIn("a `Written to` path is on the committed list", said)

    def test_e4_the_gate_reads_an_empty_or_comment_only_list_as_no_list(self) -> None:
        for listed in ((), ("# nothing",)):
            with self.subTest(listed=listed):
                code, said = self.gate_over("`README.md`", listed=listed)
                self.assertEqual(1, code, said)
                self.assertIn("no committed list", said)

    def test_e5_an_unreadable_layout_delivery_is_one_finding_never_a_traceback(self) -> None:
        for delivery in ("deli\u0000very", "../elsewhere", "/etc"):
            with self.subTest(delivery=delivery), tempfile.TemporaryDirectory() as directory:
                repo = project(directory, entry(1, HARD), origin="adopted", delivery=delivery)
                result = gate(repo)
                self.assertEqual(1, result.returncode, result.stdout + result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                findings = [row for row in result.stderr.splitlines() if row.startswith("  ")]
                self.assertEqual(1, len(findings), result.stderr)
                self.assertIn("layout.delivery", findings[0])


if __name__ == "__main__":
    unittest.main()
