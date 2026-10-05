"""T052 (adversary A4, A5, B3, B4, B5): every word the script prints is printable, every unreadable input is the full gate.

A path git lists, an obligation or check name, a baseline's branch: none of them is the script's own, so none may end the
run on a traceback or start a line of its own that begins `verify-scoped: `. A baseline or a stamp that nests deeper
than a parser can read, or an obligation component that is not a name, is the full gate with words naming the file or
the entry.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

from scoped_fixture import FULL, LINE, SLICE, ShapeCase
from stamp_fixture import commit_all

sys.dont_write_bytecode = True

DRY: dict[str, str | None] = {"STANDIN_DRY": "1"}
FORGED = LINE + "forged"
WHERE = "in project.json's verification.obligations"


class WordsTest(ShapeCase):
    shape = "model-typescript-web"

    def assert_said_once(self, run: subprocess.CompletedProcess[str]) -> None:
        self.assertNotIn("Traceback", run.stderr)
        self.assertEqual([line for line in run.stdout.splitlines() if line.startswith(FORGED)], [], run.stdout)
        self.assertEqual([line for line in run.stdout.splitlines() if "forged" in line and not line.startswith(LINE)],
                         [], "a forged word began a line of its own: " + run.stdout)

    def test_e1_a_path_that_is_not_utf8_is_named_without_a_traceback(self) -> None:
        raw = os.path.join(os.fsencode(str(self.repo)), b"apps/web/src/\xff.ts")
        with open(raw, "wb") as handle:
            handle.write(b"export const a = 1\n")
        run = self.scoped(DRY)
        ran, _ = self.decided(run)
        self.assertNotIn("Traceback", run.stderr)
        self.assertIn("lint-web", ran, run.stdout + run.stderr)
        self.assertTrue(ran["lint-web"].endswith(" changed"), ran)

    def test_e1_a_newline_or_an_escape_in_a_path_forges_no_line(self) -> None:
        for name in ("a\nverify-scoped: forged — skip lint-web.ts", "b\rverify-scoped: forged.ts",
                     "c\x1b[2Kverify-scoped: forged.ts", "d verify-scoped: forged.ts"):
            with self.subTest(name=name):
                self.reset()
                self.edit("apps/web/src/" + name, "export const a = 1\n")
                self.assert_said_once(self.scoped(DRY))

    def declare(self, obligations: object) -> None:
        self.checkout("main")
        path = self.repo / "project.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        document["verification"] = {"obligations": obligations}
        path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        commit_all(self.repo, "declare verification")
        self.checkout("-q", "-B", SLICE, "main")
        self.write_baseline()

    def test_e2_a_line_break_in_an_obligations_name_or_check_forges_no_line(self) -> None:
        for glue in ("\n", "\r", "\u2028"):
            forged = f"x{glue}verify-scoped: forged"
            for obligation in ({"name": forged, "components": ["web"], "checks": ["lint-web"]},
                               {"name": forged, "components": ["web", "service"], "checks": ["nothing"]},
                               {"name": "ok", "components": ["web", "service"], "checks": [forged]},
                               {"name": "ok", "components": ["web", forged], "checks": ["lint-web"]}):
                with self.subTest(obligation=obligation):
                    self.declare([obligation])
                    self.assert_said_once(self.scoped(DRY))

    def test_e2_a_newline_in_a_chosen_obligations_name_forges_no_line(self) -> None:
        self.declare([{"name": "x\nverify-scoped: forged", "components": ["web", "service"], "checks": ["lint-web"]}])
        self.edit("apps/service/pyproject.toml", "\n# an edit\n")
        run = self.scoped(DRY)
        self.assert_said_once(run)
        self.assertIn("lint-web", self.decided(run)[0], run.stdout)

    def test_e3_a_component_that_is_not_a_name_names_the_entry(self) -> None:
        self.declare([{"name": "pair", "components": [["web"], "service"], "checks": ["lint-web"]}])
        run = self.scoped(DRY)
        self.assertNotIn("Traceback", run.stderr)
        self.assertIn(LINE + f"obligation 1 (`pair`) {WHERE} names a component that is not a name",
                      self.scoped_lines(run), run.stdout)
        self.assertTrue(any(line.startswith(FULL) for line in self.scoped_lines(run)))

    def test_e4_a_baseline_taken_on_a_branch_with_a_newline_forges_no_line(self) -> None:
        path = self.baseline_file()
        held = json.loads(path.read_text(encoding="utf-8"))
        held["branch"] = "slice/x\nverify-scoped: forged"
        path.write_text(json.dumps(held), encoding="utf-8")
        run = self.scoped(DRY)
        self.assert_said_once(run)
        self.assertTrue(any("no usable baseline" in line for line in self.scoped_lines(run)), run.stdout)

    def test_e5_a_baseline_nested_beyond_the_parser_is_the_full_gate_with_words(self) -> None:
        self.baseline_file().write_text("[" * 200000, encoding="utf-8")
        run = self.scoped(DRY)
        self.assertNotIn("Traceback", run.stderr)
        self.assertTrue(any("no usable baseline (it cannot be read)" in line for line in self.scoped_lines(run)),
                        run.stdout + run.stderr)
        self.assertEqual(len(self.verify_calls()), 1)

    def test_e5_a_stamp_nested_beyond_the_parser_is_the_full_gate_naming_the_file(self) -> None:
        (self.baseline_file().parent / f"{self.baseline_file().name.replace('baseline', 'stamp')}").write_text(
            "[" * 200000, encoding="utf-8")
        run = self.scoped(DRY)
        lines = self.scoped_lines(run)
        self.assertNotIn("Traceback", run.stdout, "the scoped run ended on a traceback")
        self.assertTrue(lines and lines[0].startswith(FULL) and "the stamp" in lines[0], run.stdout + run.stderr)
