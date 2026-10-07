"""The test tree selects by its own imports (S38 R6, AC-S38-10 fixture, -11): an edited module runs, an edited helper
runs exactly its importers (through other helpers too), a deleted module breaks nothing, a fixture file runs its
readers.

What ran is read from the stand-ins' log; the reasons from a probe of `select_tests.choose.choose`.
"""
from __future__ import annotations

import json
import sys

from select_fixture import STAND_IN
from select_fixture_declare import DeclarationCase

sys.dont_write_bytecode = True

REASONS = ("from select_tests import choose, declarations, rules\n"
           "root = __import__('pathlib').Path('.').resolve()\n"
           "catalog = rules.load_catalog(root)\n"
           "verdicts = choose.choose(declarations.scan(root, catalog), {paths!r}, catalog)\n"
           "print(json.dumps({{v.module: [r.text for r in v.reasons] or v.skip for v in verdicts}}))\n")
GO = '{"configurations": {"backend": ["go"]}}'
PYTHON = '{"configurations": {"backend": ["python"]}}'


class ImportCase(DeclarationCase):
    def importing(self, name: str, *helpers: str, selection: str = "{}") -> None:
        """A declared stand-in that imports `helpers`, which are written as declared helpers where they do not exist."""
        for helper in helpers:
            if not (self.repo / f"tests/{helper}.py").exists():
                self.write(f"tests/{helper}.py", f"TEST_SELECTION = {{}}\nVALUE = {len(helper)}\n")
        imports = "".join(f"import {helper}\n" for helper in helpers)
        self.write(f"tests/{name}.py", f"TEST_SELECTION = {selection}\n{imports}" + STAND_IN.format(name=name))

    def reasons(self, *paths: str) -> dict[str, object]:
        done = self.probe(REASONS.format(paths=list(paths)))
        self.assertEqual(done.returncode, 0, done.stderr)
        found: dict[str, object] = json.loads(done.stdout)
        return found


class TestAnImportThroughThePackage(ImportCase):
    """`from tests.support import X` and `import tests.support` import `support` (S38 T056, B4)."""

    def test_a_helper_imported_through_tests_runs_its_importers(self) -> None:
        self.write("tests/helper.py", "TEST_SELECTION = {}\nVALUE = 1\n")
        for statement in ("from tests.helper import VALUE", "import tests.helper", "from tests import helper"):
            with self.subTest(statement):
                self.write("tests/test_a.py", f"TEST_SELECTION = {{}}\n{statement}\n" + STAND_IN.format(name="test_a"))
                self.declare(test_b=PYTHON)
                self.slice_changing()
                self.assertEqual(self.reasons("tests/helper.py")["test_a"], ["imports `tests/helper.py`"])
                self.assertEqual(self.reasons("tests/helper.py")["test_b"], "reads none of the changed files")


class TestAnEditedModule(ImportCase):
    def test_runs_and_every_other_declared_module_is_skipped(self) -> None:
        self.declare(test_a=GO, test_b=PYTHON, test_c="")
        self.slice_changing()
        self.write("tests/test_a.py", (self.repo / "tests/test_a.py").read_text(encoding="utf-8") + "\n# edited\n")
        ran, skipped = self.selected()
        self.assertEqual(ran, ["test_a", "test_c"])
        self.assertEqual(skipped, ["skipped test_b: reads none of the changed files"])
        self.assertEqual(self.reasons("tests/test_a.py")["test_a"], ["`tests/test_a.py` changed"])

    def test_a_module_that_imports_it_runs_too(self) -> None:
        self.declare(test_a=GO, test_c=PYTHON)
        self.importing("test_b", "test_a")
        self.slice_changing()
        self.assertEqual(self.reasons("tests/test_a.py")["test_b"], ["imports `tests/test_a.py`"])


class TestAnEditedHelper(ImportCase):
    def test_runs_exactly_the_modules_that_import_it_directly_or_through_another_helper(self) -> None:
        self.declare(test_a=GO, test_d=PYTHON)
        self.importing("test_b", "helper_x")
        self.write("tests/helper_y.py", "TEST_SELECTION = {}\nimport helper_x\n")
        self.importing("test_c", "helper_y")
        self.slice_changing()
        self.write("tests/helper_x.py", "TEST_SELECTION = {}\nVALUE = 2\n")
        ran, skipped = self.selected()
        self.assertEqual(ran, ["test_b", "test_c"])
        self.assertEqual(skipped, ["skipped test_a: reads none of the changed files",
                                   "skipped test_d: reads none of the changed files"])
        self.assertEqual(self.reasons("tests/helper_x.py")["test_c"], ["imports `tests/helper_x.py`"])

    def test_an_importer_of_a_helper_that_is_gone_still_runs(self) -> None:
        self.importing("test_b", "helper_x")
        self.declare(test_a=GO)
        self.commit("declarations")
        self.branch("slice/x")
        (self.repo / "tests/helper_x.py").unlink()
        found = self.reasons("tests/helper_x.py")
        self.assertEqual(found["test_b"], ["imports `tests/helper_x.py`"])
        self.assertEqual(found["test_a"], "reads none of the changed files")


class TestADeletedModule(ImportCase):
    def test_is_not_listed_and_the_run_does_not_fail_on_its_name(self) -> None:
        self.declare(test_a=GO, test_gone=PYTHON, test_c="")
        self.slice_changing()
        (self.repo / "tests/test_gone.py").unlink()
        done = self.selector()
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertEqual(self.modules_run(), ["test_c"])
        self.assertNotIn("test_gone", done.stdout + done.stderr)
        self.assertEqual([line for line in done.stdout.splitlines() if line.startswith("skipped")],
                         ["skipped test_a: reads none of the changed files"])


class TestAFixtureFile(ImportCase):
    def test_runs_the_modules_whose_reads_name_it_or_a_directory_holding_it(self) -> None:
        self.write("tests/fixtures/forge/a.txt", "a\n")
        self.write("tests/fixtures/other.txt", "o\n")
        self.declare(test_a='{"reads": ["tests/fixtures/forge"]}', test_b='{"reads": ["tests/fixtures/other.txt"]}',
                     test_c='{"reads": ["tests/fixtures/forge/a.txt"]}', test_d="{}")
        self.slice_changing()
        self.write("tests/fixtures/forge/a.txt", "changed\n")
        ran, skipped = self.selected()
        self.assertEqual(ran, ["test_a", "test_c"])
        self.assertEqual(skipped, ["skipped test_b: reads none of the changed files",
                                   "skipped test_d: reads none of the changed files"])
        self.assertEqual(self.reasons("tests/fixtures/forge/a.txt")["test_a"], ["reads `tests/fixtures/forge`"])
