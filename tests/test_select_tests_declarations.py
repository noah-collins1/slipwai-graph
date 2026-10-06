"""A module reads what it declares; an undeclared one always runs (S38 R5 first half, AC-S38-8).

Stand-in modules carry `TEST_SELECTION` declarations in a temporary repository; what ran is read from their log, the
skips from the output, and the held-declarations check from a probe of `select_tests.declarations.held`.
"""
from __future__ import annotations

import json
import subprocess
import sys

from select_fixture_declare import GO, HELD, DeclarationCase

from slipwai.assets import ROOT

sys.dont_write_bytecode = True


class TestWhatARunReaches(DeclarationCase):
    def test_a_go_change_runs_the_go_declarers_the_every_declarers_and_the_undeclared(self) -> None:
        self.declare(test_a='{"configurations": {"backend": ["go"]}}',
                     test_b='{"configurations": "every"}',
                     test_c="",
                     test_d='{"configurations": {"backend": ["typescript", "python"]}}',
                     test_e='{"configurations": {"backend": ["java-spring"], "frontend": ["react-vite"]}}',
                     test_f='{"reads": ["README.md"]}',
                     test_g="{}",
                     test_h='{"configurations": {"frontend": ["none"]}}')
        self.write("README.md", "read\n")
        self.slice_changing(GO)
        ran, skipped = self.selected()
        # `test_h` names no backend, so it admits every one; `test_g` generates nothing and reads nothing
        self.assertEqual(ran, ["test_a", "test_b", "test_c", "test_h"])
        self.assertEqual(skipped, [f"skipped {name}: reads no go configuration" for name in
                                   ("test_d", "test_e", "test_f", "test_g")])

    def test_a_module_that_reads_a_changed_file_runs(self) -> None:
        self.declare(test_a='{"reads": ["README.md"]}', test_b='{"reads": ["docs"]}', test_c="{}")
        self.write("README.md", "read\n")
        self.write("docs/guide.md", "g\n")
        self.slice_changing("docs/guide.md")
        ran, skipped = self.selected()
        self.assertEqual(ran, ["test_b"])
        self.assertEqual(skipped, ["skipped test_a: reads none of the changed files",
                                   "skipped test_c: reads none of the changed files"])

    def test_a_config_change_and_a_file_change_join_their_reasons(self) -> None:
        self.declare(test_a='{"configurations": {"backend": ["python"]}}', test_b='{"reads": ["README.md"]}')
        self.write("README.md", "read\n")
        self.slice_changing(GO, "docs/guide.md")
        ran, skipped = self.selected()
        self.assertEqual(ran, [])
        self.assertEqual(skipped, ["skipped test_a: reads no go configuration and none of the changed files",
                                   "skipped test_b: reads no go configuration and none of the changed files"])

    def test_a_toolkit_change_reaches_every_module_that_generates_a_project(self) -> None:
        self.declare(test_a='{"configurations": {"backend": ["go"]}}', test_b='{"reads": ["README.md"]}')
        self.write("README.md", "read\n")
        self.slice_changing("assets/toolkit/scripts/x.py")
        ran, skipped = self.selected()
        self.assertEqual(ran, ["test_a"])
        self.assertEqual(skipped, ["skipped test_b: reads no configuration and none of the changed files"])

    def test_the_same_run_on_the_tree_the_base_names_shows_the_one_path_only(self) -> None:
        # AC-S38-2 and -3 through the log: a slice cut from `adopt-method` compared with its tree
        self.declare(test_a='{"configurations": {"backend": ["go"]}}',
                     test_b='{"configurations": {"backend": ["python"]}}')
        self.write("assets/languages/python/x.py", "p\n")
        self.commit("declarations")
        self.branch("adopt-method")
        self.write("assets/languages/python/y.py", "adopted\n")
        self.commit("adopt")
        self.branch("slice/x")
        self.write(GO, "go\n")
        ran, skipped = self.selected(SINCE="adopt-method")
        self.assertEqual(ran, ["test_a"])
        self.assertEqual(skipped, ["skipped test_b: reads no go configuration"])


class TestADeclarationThatCannotBeRead(DeclarationCase):
    BAD = {
        "an option the catalog has not": '{"configurations": {"backend": ["cobol"]}}',
        "an axis the catalog has not": '{"configurations": {"flavour": ["go"]}}',
        "a command that is neither": '{"configurations": {"command": ["upgrade"]}}',
        "a reads path that does not exist": '{"reads": ["docs/missing.md"]}',
        "a reads path outside the tree": '{"reads": ["../elsewhere"]}',
        "a value that is not a literal": "dict(configurations='every')",
        "a list": '["go"]',
        "an unknown key": '{"configure": "every"}',
        "reads that is a string": '{"reads": "README.md"}',
        "an option list that is a string": '{"configurations": {"backend": "go"}}',
        "an empty option list": '{"configurations": {"backend": []}}',
        "configurations other than every": '{"configurations": "go"}',
    }

    def test_the_module_runs_and_the_held_check_names_it(self) -> None:
        for what, selection in self.BAD.items():
            with self.subTest(what):
                self.declare(test_a=selection, test_b='{"configurations": {"backend": ["typescript"]}}')
                self.write("README.md", "read\n")
                self.slice_changing(GO)
                ran, _ = self.selected()
                self.assertEqual(ran, ["test_a"])
                problems = self.held()
                self.assertEqual([line.split(":")[0] for line in problems], ["tests/test_a.py"], problems)

    def test_a_module_assigning_the_declaration_twice_is_not_read(self) -> None:
        self.declare(test_a='{"reads": []}\nTEST_SELECTION = {"reads": []}')
        self.slice_changing(GO)
        self.assertEqual(self.selected()[0], ["test_a"])
        self.assertEqual([line.split(":")[0] for line in self.held()], ["tests/test_a.py"])

    def test_a_module_that_does_not_parse_always_runs(self) -> None:
        self.declare(test_a="", test_b='{"configurations": {"backend": ["typescript"]}}')
        self.write("tests/test_a.py", "def broken(:\n")
        self.slice_changing(GO)
        done = self.selector()
        self.assertNotEqual(done.returncode, 0, "the broken module ran, and failed")
        self.assertIn("test_a", done.stderr)
        self.assertEqual(self.modules_run(), [])  # `test_a` fails to import, so it logs nothing; `test_b` was skipped
        self.assertNotIn("test_b", done.stderr)

    def test_a_valid_declaration_is_held(self) -> None:
        self.declare(test_a='{"configurations": {"backend": ["go"], "command": ["adopt"]}, "reads": ["README.md"]}',
                     test_b='{"configurations": "every"}', test_c="{}")
        self.write("README.md", "read\n")
        self.slice_changing(GO)
        self.assertEqual(self.held(), [])


class TestAHelperVoidsADeclaration(DeclarationCase):
    def test_a_declared_module_importing_an_undeclared_helper_is_undeclared(self) -> None:
        self.write("tests/helper_x.py", "VALUE = 1\n")
        self.declare(test_a="", test_b='{"configurations": {"backend": ["typescript"]}}')
        self.write("tests/test_b.py", "import helper_x\n" + (self.repo / "tests/test_b.py").read_text(encoding="utf-8"))
        self.slice_changing(GO)
        ran, skipped = self.selected()
        self.assertEqual(ran, ["test_a", "test_b"])
        self.assertEqual(skipped, [])
        voided = self.held()
        self.assertEqual(len(voided), 1, voided)
        self.assertTrue(voided[0].startswith("tests/test_b.py: "), voided)
        self.assertIn("helper_x", voided[0])

    def test_the_declarations_of_a_modules_helpers_are_joined_with_its_own(self) -> None:
        self.write("tests/helper_x.py",
                   'TEST_SELECTION = {"configurations": {"backend": ["go"]}, "reads": ["README.md"]}\n')
        self.write("README.md", "read\n")
        self.declare(test_a="", test_b='{"configurations": {"backend": ["typescript"]}}')
        self.write("tests/test_b.py", "import helper_x\n" + (self.repo / "tests/test_b.py").read_text(encoding="utf-8"))
        self.slice_changing(GO)
        self.assertEqual(self.selected()[0], ["test_a", "test_b"])
        self.assertEqual(self.held(), [])
        self.branch("slice/x")
        self.write(GO, "go\n")
        self.write("assets/languages/python/x.py", "p\n")
        self.commit("python")
        self.write("README.md", "changed\n")
        ran, _ = self.selected()
        self.assertEqual(ran, ["test_a", "test_b"])

    def test_a_module_that_loads_a_module_by_a_name_it_computes_is_undeclared(self) -> None:
        self.declare(test_a='{"configurations": {"backend": ["typescript"]}}')
        computed = "import importlib\nimportlib.import_module(__import__('os').environ.get('X', 'os'))\n"
        self.write("tests/test_a.py", computed + (self.repo / "tests/test_a.py").read_text(encoding="utf-8"))
        self.slice_changing(GO)
        self.assertEqual(self.selected()[0], ["test_a"])


class TestAReadsOnlyDeclarationThatGenerates(DeclarationCase):
    """`support.generate` is reachable from every importer while `support` names no configuration, so a module that
    calls it and says only what it reads under-claims; `held` names it (T030, AC-S38-8)."""

    SUPPORT = ('TEST_SELECTION = {"reads": []}\n\n\nclass FactoryTestCase:\n'
               '    def generate(self, name):\n        return name\n\n'
               '    def refuse(self, name):\n        return name\n')
    CALLS = {
        "generate": "import support\n\n\nclass C(support.FactoryTestCase):\n    def test_x(self):\n"
                    "        self.generate('p')\n",
        "refuse": "import support\n\n\nclass C(support.FactoryTestCase):\n    def test_x(self):\n"
                  "        self.refuse('p')\n",
        "the launcher": "import subprocess\n\n\ndef test_x():\n    subprocess.run(['./slipwai', 'generate', 'p'])\n",
        "the launcher by path": "import subprocess\n\nROOT = None\n\n\ndef test_x():\n"
                                "    subprocess.run([str(ROOT / 'slipwai'), 'generate', 'p'])\n",
        "the command's own main": "from slipwai.cli import main\n\n\ndef test_x():\n    main(['generate', 'p'])\n",
        "the command module": "import slipwai.cli\n\n\ndef test_x():\n    slipwai.cli.main(['generate', 'p'])\n",
    }

    def module(self, call: str, selection: str) -> None:
        self.write("tests/support.py", self.SUPPORT)
        self.write("tests/test_a.py", f"TEST_SELECTION = {selection}\n" + self.CALLS[call])

    def test_a_reads_only_module_that_generates_is_named(self) -> None:
        for call in self.CALLS:
            with self.subTest(call):
                self.module(call, '{"reads": []}')
                self.commit("a reads-only generator")
                found = self.held()
                self.assertEqual([line.split(":")[0] for line in found], ["tests/test_a.py"], found)
                self.assertIn("declares no configurations", found[0])

    def test_a_helper_that_calls_generate_names_the_module_that_imports_it(self) -> None:
        self.write("tests/support.py", self.SUPPORT)
        self.write("tests/helper_x.py", 'TEST_SELECTION = {"reads": []}\nimport support\n\n\n'
                   "def build(case):\n    case.generate('p')\n")
        self.write("tests/test_a.py", 'TEST_SELECTION = {"reads": []}\nimport helper_x\n')
        self.commit("a helper that generates")
        self.assertEqual([line.split(":")[0] for line in self.held()], ["tests/test_a.py"])

    def test_a_helper_that_runs_the_launcher_names_the_module_that_imports_it(self) -> None:
        self.write("tests/support.py", self.SUPPORT)
        self.write("tests/gen_helper.py", 'TEST_SELECTION = {"reads": []}\nimport subprocess\n\n\n'
                   "def build():\n    subprocess.run(['./slipwai', 'generate', 'p'])\n")
        self.write("tests/test_a.py", 'TEST_SELECTION = {"reads": []}\nimport gen_helper\n')
        self.commit("a helper that runs the launcher")
        self.assertEqual([line.split(":")[0] for line in self.held()], ["tests/test_a.py"])

    def test_a_module_that_names_its_configurations_is_held(self) -> None:
        for call in self.CALLS:
            with self.subTest(call):
                self.module(call, '{"configurations": {"backend": ["go"]}}')
                self.commit("a generator that says what it generates")
                held = self.held()
                if call == "generate":  # a call the signature binds: `name` is no axis (T038)
                    self.assertIn("computed backend", held[0])
                else:  # a route the signature does not describe is every option of every axis
                    self.assertEqual([line.split(":")[0] for line in held], ["tests/test_a.py"], held)
                    self.assertIn("every option of every axis", held[0])

    def test_a_module_that_declares_every_may_take_any_route(self) -> None:
        for call in self.CALLS:
            with self.subTest(call):
                self.module(call, '{"configurations": "every"}')
                self.commit("a generator that says it generates everything")
                self.assertEqual(self.held(), [])

    def test_a_reads_only_module_that_generates_nothing_is_held(self) -> None:
        self.write("tests/support.py", self.SUPPORT)
        self.write("tests/test_a.py", 'TEST_SELECTION = {"reads": []}\nimport support\n\nX = support.FactoryTestCase\n')
        self.commit("imports support, calls nothing")
        self.assertEqual(self.held(), [])


class TestTheRealTree(DeclarationCase):
    def test_every_declaration_in_this_repository_is_held_and_none_is_void(self) -> None:
        done = subprocess.run(["python3", "-B", "-c", "import json, sys\nsys.path.insert(0, 'scripts')\n" + HELD],
                              cwd=ROOT, text=True, capture_output=True, timeout=180)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(json.loads(done.stdout), [])
