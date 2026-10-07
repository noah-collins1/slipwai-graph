"""A literal `./slipwai generate` argv is read as the axes it generates (S43 T001, D187 rules 1-3, AC-S43-12/14).

The stamp-style argv names its backend, profile and frontend as literals, so a declaration that names them holds and a
change to another backend's assets skips the module; an argv the rule cannot read stays every option of every axis
(`test_select_tests_argv_forms`). Stand-in modules in a temporary repository, and the real tree read by the selector's
own scan for the last case.
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest

from select_fixture import CATALOG
from test_select_tests_generation import GenerationCase

from slipwai.assets import ROOT

sys.dont_write_bytecode = True

PYTHON = "assets/languages/python/main.py"
GO = "assets/languages/go/main.go"
STAMP = ('[str(ROOT / "slipwai"), "generate", "fixture", "--profile", "standard", "--backend", "python", '
         '"--frontend", "none", "--http", "none", "--output", str(parent), "--skip-checks"]')


def declaring(**axes: list[str]) -> str:
    return json.dumps({"configurations": axes})


STAMPED = declaring(backend=["python"], profile=["standard"], frontend=["none"])


class ArgvCase(GenerationCase):
    def setUp(self) -> None:
        super().setUp()
        axes: dict[str, dict[str, str]] = {key: {} for key in ("event-store", "http", "auth", "users")}
        self.write("catalog.json", json.dumps({**CATALOG, "axes": axes}))

    def argv(self, selection: str, argv: str) -> None:
        self.module(selection, f"argv = lambda: {argv}")  # never run: the selector reads it

    def skipped_on(self, path: str) -> bool:
        self.slice_changing(path)
        return "skipped test_a" in self.selector().stdout

    def runs_on(self, path: str) -> bool:
        self.slice_changing(path)
        return "skipped test_a" not in (output := self.selector().stdout) and "selected 1 of 1 modules" in output


class TestAStampStyleArgv(ArgvCase):
    def test_it_is_the_axes_it_names_so_a_declaration_of_them_holds_and_skips_another_backend(self) -> None:
        self.argv(STAMPED, STAMP)
        self.assertEqual(self.held(), [])
        self.assertTrue(self.skipped_on(GO))

    def test_it_is_selected_by_its_own_backend(self) -> None:
        self.argv(STAMPED, STAMP)
        self.assertTrue(self.runs_on(PYTHON))

    def test_the_bare_launcher_chain_reads_the_same(self) -> None:
        self.argv(STAMPED, STAMP.replace('str(ROOT / "slipwai")', 'ROOT / "slipwai"', 1))
        self.assertEqual(self.held(), [])
        self.assertTrue(self.skipped_on(GO))

    def test_a_computed_name_and_a_computed_output_value_still_read(self) -> None:
        self.argv(STAMPED, '[ROOT / "slipwai", "generate", pick(), "--profile", "standard", "--backend", "python", '
                           '"--frontend", "none", "--output", base / name]')
        self.assertEqual(self.held(), [])
        self.assertTrue(self.skipped_on(GO))


class TestWhatAnArgvLeavesOut(ArgvCase):
    def test_an_omitted_backend_is_every_backend_so_a_narrow_declaration_is_void_and_runs(self) -> None:
        self.argv(STAMPED, '[ROOT / "slipwai", "generate", "n", "--profile", "standard", "--frontend", "none"]')
        self.assertIn("computed backend", self.voided())
        self.assertTrue(self.runs_on(GO))

    def test_a_literal_the_declaration_lacks_voids_it(self) -> None:
        self.argv(declaring(backend=["typescript"], profile=["standard"], frontend=["none"]), STAMP)
        self.assertIn("generates the backend python", self.voided())
        self.assertTrue(self.runs_on(GO))

    def test_a_target_is_the_target_axis(self) -> None:
        both = '[ROOT / "slipwai", "generate", "n", "--backend", "python", "--profile", "standard", ' \
               '"--frontend", "none", "--target", "aws"]'
        self.argv(declaring(backend=["python"], profile=["standard"], frontend=["none"], target=["aws"]), both)
        self.assertEqual(self.held(), [])
        self.argv(declaring(backend=["python"], profile=["standard"], frontend=["none"], target=["azure"]), both)
        self.assertIn("generates the target aws", self.voided())

    def test_the_catalogs_axis_flags_answer_no_declared_axis(self) -> None:
        flags = '"--event-store", "x", "--http", "y", "--auth", "z", "--users", "u"'
        self.argv(STAMPED, f'[ROOT / "slipwai", "generate", "n", "--backend", "python", "--profile", "standard", '
                           f'"--frontend", "none", {flags}]')
        self.assertEqual(self.held(), [])
        self.assertTrue(self.skipped_on(GO))


PROBE = """
import json, sys
sys.dont_write_bytecode = True
sys.path.insert(0, 'scripts')
from pathlib import Path
from select_tests import choose, declarations
root = Path('.').resolve()
catalog = json.loads((root / 'catalog.json').read_text(encoding='utf-8'))
tree = declarations.scan(root, catalog)
def generates(member):
    return any('python' in (call.axes.get('backend') or ()) for call in tree.sources[member].facts.calls)
modules = sorted(n for n in tree.sources if declarations.is_module(n))
out = {"expected": [n for n in modules if any(generates(m) for m in (n, *tree.closures[n]))],
       "ran": sorted(v.module for v in choose.select(tree, [sys.argv[1]], catalog).verdicts if v.runs)}
print(json.dumps(out))
"""


class TestTheRealTree(unittest.TestCase):
    def test_a_python_path_selects_every_module_whose_closure_generates_python(self) -> None:
        """The expected set is read from `generation.facts` over the real tests, never typed; it may be empty where no
        real fixture generates a literal python configuration, and the property is then the empty one."""
        done = subprocess.run(["python3", "-B", "-c", PROBE, PYTHON], cwd=ROOT, text=True, capture_output=True,
                              timeout=180, check=False)
        self.assertEqual(done.returncode, 0, done.stderr)
        found: dict[str, list[str]] = json.loads(done.stdout)
        self.assertEqual([name for name in found["expected"] if name not in found["ran"]], [])


if __name__ == "__main__":
    unittest.main()
