"""S42 T032 (D223 item 1 · AC-S42-4 amended, AC-S42-11): all of a project's Python services share one `mutation-full`
line, `python3 scripts/mutmut-mutation.py <service> <service> …`, at the place the first Python line sits; every other
backend's lines stay byte for byte, and `factory_recipe` (the scope script's "the recipe the factory wrote") says the
same line.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

from support import FactoryTestCase, commit_all
from test_mutation_borders import loaded
from test_mutation_scope_python import QUARKUS_AND, SOURCE, TWO, PythonCase
from test_mutation_targets import SCRIPT, full_recipe, recipe_of
from test_mutmut_generated import add_service

sys.dont_write_bytecode = True
WRAPPER = "python3 scripts/mutmut-mutation.py"
GO = "python3 scripts/go-mutation.py {} $(if $(SINCE),--since $(SINCE))"
# the shapes the rule names: the order of the services is the order of the words
SHAPES = {
    "two python": ["python:apps/service", "python:apps/billing"],
    "three python": ["python:apps/service", "python:apps/billing", "python:apps/ledger"],
    "go, python, go, python": ["go:apps/a", "python:apps/b", "go:apps/c", "python:apps/d"],
    "python, go, python": ["python:apps/a", "go:apps/b", "python:apps/c"],
    "typescript between python": ["python:apps/a", "typescript:apps/b", "python:apps/c"],
}
NOT_FACTORY = "recipe is not the one the factory wrote"


class OneLineTest(FactoryTestCase):
    def test_e1_two_python_services_share_one_line_in_service_order(self) -> None:
        self.assertEqual(full_recipe(SHAPES["two python"]), [f"{WRAPPER} apps/service apps/billing"])
        self.assertEqual(full_recipe(SHAPES["three python"]), [f"{WRAPPER} apps/service apps/billing apps/ledger"])

    def test_e2_go_before_and_after_python_keeps_every_go_line_and_the_one_python_line_at_the_first_python_place(
            self) -> None:
        self.assertEqual(full_recipe(SHAPES["go, python, go, python"]), [
            GO.format("apps/a"), f"{WRAPPER} apps/b apps/d", GO.format("apps/c")])
        self.assertEqual(full_recipe(SHAPES["python, go, python"]), [f"{WRAPPER} apps/a apps/c", GO.format("apps/b")])

    def test_e3_another_backends_line_is_never_collapsed(self) -> None:
        self.assertEqual(full_recipe(SHAPES["typescript between python"]), [
            f"{WRAPPER} apps/a apps/c", "python3 scripts/stryker-mutation.py apps/b"])

    def test_e4_factory_recipe_is_the_generated_recipe_for_every_shape(self) -> None:
        module = loaded(SCRIPT)
        for name, words in SHAPES.items():
            with self.subTest(shape=name):
                services = [tuple(word.split(":", 1)) for word in words]
                self.assertEqual(module.factory_recipe(services), full_recipe(words))


class AddedOneAtATimeTest(FactoryTestCase):
    """D223's *would reverse if*: a project whose Python services were added one at a time renders the line the factory
    writes for them all at once."""

    def test_e5_add_service_renders_the_same_line_byte_for_byte_after_each_service(self) -> None:
        parent = Path(tempfile.mkdtemp(prefix="mutmut-recipe-"))
        self.addCleanup(shutil.rmtree, parent, ignore_errors=True)
        project = self.generate(parent, "oneatatime", "standard", "python", "none", http="none")
        words = ["python:apps/service"]
        self.assertEqual(recipe_of((project / "Makefile").read_text(encoding="utf-8"), "mutation-full"),
                         full_recipe(words))
        for name in ("billing", "ledger"):
            add_service(project, name, "python")
            commit_all(project, f"after {name}")
            words.append(f"python:apps/{name}")
            with self.subTest(added=name):
                written = recipe_of((project / "Makefile").read_text(encoding="utf-8"), "mutation-full")
                self.assertEqual(written, full_recipe(words))
                self.assertEqual(len(written), 1)


class ScopedRunTest(PythonCase):
    def test_e6_a_two_python_project_on_a_slice_branch_is_scoped_and_the_recipe_is_the_factory_s(self) -> None:
        self.write("apps/service/src/pkg/health.py", SOURCE)
        status, lines, recording = self.run_planned(*TWO)
        self.assertEqual(recording.scoped, [("apps/service", ["src/pkg/health.py"])], lines)
        self.assertEqual((status, [line for line in lines if NOT_FACTORY in line]), (0, []))

    def test_e7_a_quarkus_project_with_python_beside_it_is_still_the_factory_s_recipe(self) -> None:
        self.write("apps/second/src/pkg/health.py", SOURCE)
        status, lines, recording = self.run_planned(*QUARKUS_AND)
        self.assertEqual([line for line in lines if NOT_FACTORY in line], [])


if __name__ == "__main__":
    import unittest
    unittest.main()
