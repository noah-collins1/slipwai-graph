"""A backend's change narrows the matrix (S38 R7, AC-S38-9): the modules only a backend's own assets reached run with
`FACTORY_BACKENDS` set to that backend, the rest in a second process with it unset, and the run fails when either fails.

The stand-ins log the `FACTORY_BACKENDS` each saw; the lines are read from the output.
"""
from __future__ import annotations

import sys

from select_fixture import STAND_IN
from select_fixture_declare import GO, DeclarationCase

sys.dont_write_bytecode = True

EVERY_BACKEND = '{"configurations": {"backend": ["typescript", "python", "go", "java-quarkus", "java-spring"]}}'
FAILING = ("import unittest\n\n\nclass Case(unittest.TestCase):\n    def test_it(self):\n        self.fail('forced')\n")
LEFT_OUT = "(java-quarkus, java-spring, python, typescript unaffected)"


class NarrowCase(DeclarationCase):
    def seen(self) -> dict[str, str]:
        """Each stand-in module that ran, with the `FACTORY_BACKENDS` it saw."""
        lines = [line.split("\t") for line in self.ran() if line.startswith("module\t")]
        return {fields[1]: fields[3].removeprefix("FACTORY_BACKENDS=") for fields in lines}

    def declared_matrix(self) -> None:
        self.declare(test_matrix=EVERY_BACKEND, test_other="")


class TestAGoChangeNarrowsTheMatrix(NarrowCase):
    def test_the_matrix_runs_with_go_only_and_the_rest_with_it_unset(self) -> None:
        self.declared_matrix()
        self.slice_changing(GO)
        done = self.selector()
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertEqual(self.seen(), {"test_matrix": "go", "test_other": ""})
        self.assertIn(f"narrowed test_matrix: backend go only {LEFT_OUT}", done.stdout.splitlines())

    def test_two_processes_run_and_the_matrix_does_not_see_the_other_modules(self) -> None:
        self.declared_matrix()
        self.slice_changing(GO)
        self.selector()
        self.assertEqual(sorted(self.pythonpaths()), ["PYTHONPATH=src:tests"])

    def test_the_run_fails_when_the_narrowed_process_fails(self) -> None:
        self.declared_matrix()
        self.slice_changing(GO)
        self.write("tests/test_matrix.py", "TEST_SELECTION = " + EVERY_BACKEND + "\n" + FAILING)
        done = self.selector()
        self.assertNotEqual(done.returncode, 0)
        self.assertEqual(self.seen(), {"test_other": ""}, "the other process ran although the narrowed one failed")

    def test_the_run_fails_when_the_other_process_fails_and_the_narrowed_one_still_ran(self) -> None:
        self.declared_matrix()
        self.slice_changing(GO)
        self.write("tests/test_other.py", FAILING)
        done = self.selector()
        self.assertNotEqual(done.returncode, 0)
        self.assertEqual(self.seen(), {"test_matrix": "go"})

    def test_two_backends_are_named_together(self) -> None:
        self.declared_matrix()
        self.slice_changing(GO, "assets/languages/python/app.py")
        done = self.selector()
        self.assertEqual(self.seen()["test_matrix"], "go,python")
        self.assertIn("narrowed test_matrix: backends go, python only "
                      "(java-quarkus, java-spring, typescript unaffected)", done.stdout.splitlines())

    def test_a_family_directory_names_every_backend_of_the_family(self) -> None:
        self.declared_matrix()
        self.slice_changing("assets/languages/java/flags/Flags.java")
        done = self.selector()
        self.assertEqual(self.seen()["test_matrix"], "java-quarkus,java-spring")
        self.assertIn("narrowed test_matrix: backends java-quarkus, java-spring only "
                      "(go, python, typescript unaffected)", done.stdout.splitlines())


class TestWhereTheMatrixIsNotNarrowed(NarrowCase):
    def test_a_toolkit_change_beside_a_backend_change_runs_it_whole(self) -> None:
        self.declared_matrix()
        self.slice_changing(GO, "assets/toolkit/scripts/x.py")
        done = self.selector()
        self.assertEqual(self.seen(), {"test_matrix": "", "test_other": ""})
        self.assertFalse([line for line in done.stdout.splitlines() if line.startswith("narrowed")])

    def test_a_module_selected_for_a_file_it_reads_is_not_narrowed(self) -> None:
        self.declare(test_matrix='{"configurations": {"backend": ["go"]}, "reads": ["README.md"]}')
        self.write("README.md", "read\n")
        self.slice_changing(GO)
        self.write("README.md", "changed\n")
        self.selector()
        self.assertEqual(self.seen(), {"test_matrix": ""})

    def test_a_module_reached_through_a_cross_read_is_not_narrowed_to_the_backend(self) -> None:
        self.declare(test_matrix='{"configurations": {"backend": ["typescript"], "frontend": ["react-vite"]}}')
        self.slice_changing("assets/languages/typescript/biome/biome.jsonc")
        self.selector()
        self.assertEqual(self.seen(), {"test_matrix": ""})

    def test_a_backend_reached_by_another_directorys_cross_read_is_not_narrowed(self) -> None:
        self.declare(test_matrix='{"configurations": {"backend": ["typescript"], "frontend": ["none"]}}')
        self.slice_changing("assets/frontends/react-vite/app/package.json")
        done = self.selector()
        self.assertEqual(self.seen(), {"test_matrix": ""})
        self.assertFalse([line for line in done.stdout.splitlines() if line.startswith("narrowed")])

    def test_the_java_build_is_read_by_adoption_so_a_module_that_may_run_it_is_not_narrowed(self) -> None:
        self.declared_matrix()
        self.slice_changing("assets/languages/java/build/pom.xml")
        self.selector()
        self.assertEqual(self.seen(), {"test_matrix": "", "test_other": ""})

    def test_an_undeclared_module_is_never_narrowed(self) -> None:
        self.write("tests/test_matrix.py", STAND_IN.format(name="test_matrix"))
        self.slice_changing(GO)
        self.selector()
        self.assertEqual(self.seen(), {"test_matrix": ""})

    def test_nothing_narrowed_means_one_process_as_before(self) -> None:
        self.declare(test_a=EVERY_BACKEND.replace('"go", ', ""), test_other="")
        self.slice_changing(GO)
        done = self.selector()
        self.assertEqual(self.seen(), {"test_other": ""})
        self.assertFalse([line for line in done.stdout.splitlines() if line.startswith("narrowed")])
