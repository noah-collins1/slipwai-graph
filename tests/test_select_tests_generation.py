"""A declared module that generates is held to what its source generates (S38 T038, D164, AC-S38-8, AC-S38-16).

The selector's scan binds every `generate(` call to `FactoryTestCase.generate`'s signature and resolves each axis: a
literal, or a loop over a literal sequence, to its values, and anything else to every option of the axis. A call that
fixes an option the declaration lacks, a computed argument on an axis the declaration narrows, another route to a
generated project, or an in-process reach into the repository that `reads` does not name, voids the declaration: the
module runs and `held` names it. Stand-in modules in a temporary repository; nothing here runs a generator.
"""
from __future__ import annotations

import sys

from select_fixture_declare import DeclarationCase

sys.dont_write_bytecode = True

SUPPORT = ("import unittest\n\nTEST_SELECTION = {}\n\n\nclass FactoryTestCase(unittest.TestCase):\n"
           "    def generate(self, parent, name, profile='event-modelling', language='typescript', frontend='none',\n"
           "                 **axes):\n        return parent\n\n    def refuse(self, parent, name, **options):\n"
           "        return ''\n")
GO_ONLY = '{"configurations": {"backend": ["go"], "frontend": ["none"], "profile": ["standard"]}}'
EVERY_BACKEND = ('{"configurations": {"backend": ["go", "java-quarkus", "java-spring", "python", "typescript"], '
                 '"frontend": ["none"]}}')


class GenerationCase(DeclarationCase):
    def module(self, selection: str, body: str, head: str = "") -> None:
        self.write("tests/support.py", SUPPORT)
        self.write("tests/test_a.py", f"import support\n{head}\nTEST_SELECTION = {selection}\n\n\n"
                   f"class C(support.FactoryTestCase):\n    def test_x(self):\n"
                   + "".join(f"        {line}\n" for line in body.splitlines()))

    def voided(self) -> str:
        found = self.held()
        self.assertEqual([line.split(":")[0] for line in found], ["tests/test_a.py"], found)
        return found[0]


class TestACallThatGoesBeyondItsDeclaration(GenerationCase):
    def test_a_call_that_fixes_an_option_the_declaration_lacks_voids_it(self) -> None:
        self.module(GO_ONLY, 'self.generate("d", "n", "standard", "go", "react-vite")')
        self.assertIn("generates the frontend react-vite", self.voided())

    def test_the_same_by_keyword_and_the_default_of_an_omitted_argument(self) -> None:
        by_keyword = 'self.generate("d", "n", "standard", language="go", frontend="react-vite")'
        for body, option in ((by_keyword, "react-vite"),
                             ('self.generate("d", "n", "standard", "python")', "python"),
                             ('self.generate("d", "n")', "typescript")):
            with self.subTest(body):
                self.module(GO_ONLY, body)
                self.assertIn(option, self.voided())

    def test_a_loop_over_a_literal_sequence_is_every_value_in_it(self) -> None:
        self.module(GO_ONLY, 'for front in ("none", "react-vite"):\n'
                             '    self.generate("d", "n", "standard", "go", front)')
        self.assertIn("react-vite", self.voided())
        self.module(GO_ONLY, 'for front, name in (("none", "a"), ("react-vite", "b")):\n'
                             '    self.generate("d", name, "standard", "go", front)')
        self.assertIn("react-vite", self.voided())

    def test_a_computed_argument_on_an_axis_the_declaration_narrows_voids_it(self) -> None:
        self.module(GO_ONLY, 'self.generate("d", "n", "standard", pick())')
        self.assertIn("computed backend", self.voided())

    def test_a_call_to_a_command_the_declaration_does_not_name_voids_it(self) -> None:
        self.module('{"configurations": {"command": ["adopt"]}}', 'self.generate("d", "n")')
        self.assertIn("commands lack", self.voided())

    def test_calls_inside_the_declaration_leave_it_whole(self) -> None:
        self.module(GO_ONLY, 'self.generate("d", "n", "standard", "go")\n'
                             'for front in ("none",):\n    self.generate("d", "n", "standard", "go", front)')
        self.assertEqual(self.held(), [])

    def test_a_computed_argument_on_an_axis_the_declaration_names_whole_is_the_control(self) -> None:
        self.module(EVERY_BACKEND, 'self.generate("d", "n", "standard", pick(), "none")')
        self.assertEqual(self.held(), [])
        self.module(GO_ONLY.replace('"profile": ["standard"]', '"profile": ["standard", "event-modelling"]'),
                    'self.generate("d", "n", pick(), "go")')
        self.assertEqual(self.held(), [])


class TestOtherRoutesToAProject(GenerationCase):
    def test_refuse_and_the_launcher_are_every_option_of_every_axis(self) -> None:
        for body, head in (('self.refuse("d", "n")', ""),
                           ("run(['./slipwai', 'generate', 'p'])", "from x import run\n"),
                           ("main(['generate', 'p'])", "from slipwai.cli import main\n")):
            with self.subTest(body):
                self.module(GO_ONLY, body, head)
                self.assertIn("every option of every axis", self.voided())

    def test_a_module_that_declares_every_may_take_them(self) -> None:
        self.module('{"configurations": "every"}', 'self.refuse("d", "n")')
        self.assertEqual(self.held(), [])


class TestAReachIntoTheRepository(GenerationCase):
    def test_a_reach_reads_only_what_it_declares(self) -> None:
        self.write("README.md", "read\n")
        head = "from slipwai.assets import ROOT\n"
        for body in ('(ROOT / "README.md").read_text()', "(ROOT / name).read_text()", "ROOT.parent", "__file__",
                     "importlib.util.find_spec(name)", "sys.path.insert(0, p)", "exec(code)", 'self.load("README.md")',
                     "self.module.load(name)"):
            with self.subTest(body):
                self.module(GO_ONLY, body, head)
                self.assertIn("reaches the repository in-process", self.voided())

    def test_a_reach_that_reads_names_is_held(self) -> None:
        self.write("README.md", "read\n")
        self.module(GO_ONLY.replace("}}", '}, "reads": ["README.md"]}'),
                    '(ROOT / "README.md").read_text()\nself.load("README.md")', "from slipwai.assets import ROOT\n")
        self.assertEqual(self.held(), [])

    def test_the_launcher_path_is_a_route_and_not_also_a_reach(self) -> None:
        self.module(GO_ONLY, 'self.generate("d", "n", "standard", "go")', "from slipwai.assets import ROOT\n"
                    'LAUNCHER = ROOT / "slipwai"\n')
        self.assertIn("generates through the launcher", self.voided())


class TestAReadsEntryHoldsWhereTheSelectorMatchesIt(GenerationCase):
    """`reads` entries are matched by prefix, so only a bare-name `.load(` may be held by a longer entry (T054, B2)."""

    HEAD = "from slipwai.assets import ROOT\n"

    def test_a_suffix_of_an_entry_does_not_hold_a_root_path(self) -> None:
        self.write("README.md", "read\n")
        self.write("assets/README.md", "other\n")
        self.module(GO_ONLY.replace("}}", '}, "reads": ["assets/README.md"]}'), '(ROOT / "README.md").read_text()',
                    self.HEAD)
        self.assertIn("reaches the repository in-process", self.voided())

    def test_a_bare_name_load_is_held_by_the_entry_that_ends_in_it(self) -> None:
        self.write("assets/README.md", "other\n")
        self.module(GO_ONLY.replace("}}", '}, "reads": ["assets/README.md"]}'), 'self.load("README.md")', self.HEAD)
        self.assertEqual(self.held(), [])

    def test_a_load_of_a_path_is_not_held_by_a_suffix(self) -> None:
        self.write("assets/docs/README.md", "other\n")
        self.write("docs/README.md", "other\n")
        self.module(GO_ONLY.replace("}}", '}, "reads": ["assets/docs/README.md"]}'),
                    'self.load("docs/README.md")', self.HEAD)
        self.assertIn("reaches the repository in-process", self.voided())


class TestAPathLiteralIsAReach(GenerationCase):
    """The tests run at the repository's root, so a literal path reaches it without `ROOT` (S38 T053, B1)."""

    def test_a_literal_naming_an_existing_path_the_reads_lack_voids_the_declaration(self) -> None:
        self.write("README.md", "read\n")
        self.write("scripts/x.py", "x = 1\n")
        for body in ('Path("README.md").read_text()', 'subprocess.run(["python3", "scripts/x.py"])',
                     'open("scripts/x.py")'):
            with self.subTest(body):
                self.module(GO_ONLY, body)
                self.assertIn("reaches the repository in-process", self.voided())

    def test_the_same_literals_are_held_by_reads_naming_them_or_a_directory_above(self) -> None:
        self.write("README.md", "read\n")
        self.write("scripts/x.py", "x = 1\n")
        body = 'Path("README.md").read_text()\nsubprocess.run(["python3", "scripts/x.py"])'
        for reads in ('["README.md", "scripts"]', '["README.md", "scripts/x.py"]'):
            with self.subTest(reads):
                self.module(GO_ONLY.replace("}}", '}, "reads": ' + reads + "}"), body)
                self.assertEqual(self.held(), [])

    def test_a_literal_that_names_nothing_in_the_repository_is_not_a_reach(self) -> None:
        self.write("README.md", "read\n")
        self.module(GO_ONLY, 'name = "no-such-file.md"\nlabel = "README.md is read"')
        self.assertEqual(self.held(), [])

    def test_a_literal_naming_only_an_ignored_path_is_not_a_reach(self) -> None:
        """`build/` is on disk wherever `make starters` ran and nowhere else: a declaration holds or not by what git
        sees, the same in every checkout."""
        self.write(".gitignore", "/build/\n")
        self.write("build/out.txt", "made\n")
        self.module(GO_ONLY, 'subprocess.run(["make", "build"], cwd=project)')
        self.assertEqual(self.held(), [])

    def test_a_literal_that_is_compared_indexed_or_joined_to_another_base_is_not_a_path_handed_on(self) -> None:
        self.write("README.md", "read\n")
        self.write("tests/x.py", "x = 1\n")
        for body in ('"tests" in parts', 'table["README.md"]', 'project / "README.md"', 'where = "."'):
            with self.subTest(body):
                self.module(GO_ONLY, body)
                self.assertEqual(self.held(), [])

    def test_a_literal_joined_onto_from_the_left_is_a_path_handed_on(self) -> None:
        self.write("scripts/x.py", "x = 1\n")
        self.module(GO_ONLY, 'Path("scripts") / "x.py"')
        self.assertIn("reaches the repository in-process", self.voided())


class TestWhatTheSelectorDoesWithAVoidedDeclaration(GenerationCase):
    PYTHON = "assets/languages/python/main.py"

    def test_a_declared_module_whose_calls_fit_is_skipped_by_a_change_it_does_not_read(self) -> None:
        self.module(GO_ONLY, 'self.generate("d", "n", "standard", "go", "none")')
        self.slice_changing(self.PYTHON)
        self.assertIn("skipped test_a: reads no python configuration", self.selector().stdout)

    def test_a_react_vite_call_added_to_it_makes_it_run_and_held_names_it(self) -> None:
        self.module(GO_ONLY, 'self.generate("d", "n", "standard", "go", "none")\n'
                             'self.generate("d", "n", "standard", "go", "react-vite")')
        self.slice_changing(self.PYTHON)
        output = self.selector().stdout
        self.assertNotIn("skipped test_a", output)
        self.assertIn("selected 1 of 1 modules", output)
        self.assertIn("generates the frontend react-vite", self.voided())
