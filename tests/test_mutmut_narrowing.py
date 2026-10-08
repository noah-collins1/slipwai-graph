"""S42 Phase 4 (T038, T040, T041, T044; the adversary's findings A3, A5, A6, B5; D227, D228): what narrows the tests or
the mutants, and the words that say so.

The harness is `test_mutmut_adversary`'s. Undeclared, as that module is: it reads the fragment and the generated
starter's table.
"""
from __future__ import annotations

import subprocess
import sys
import tomllib
import unittest
from pathlib import Path

from test_mutmut_adversary import CLI_ARGS, SELECTION, PhaseCase, narrowed, narrowing
from test_mutmut_config import loaded
from test_mutmut_verdict import KEY, SCRIPT, lines_of

from slipwai.assets import LANGUAGE_ROOT
from slipwai.project.mutmut import PYTHON_MUTATION_NOTE

sys.dont_write_bytecode = True



FRAGMENT = Path(__file__).resolve().parent.parent / "changelog.d" / "mutmut-mutation.md"






class TestSelectionTest(PhaseCase):
    """T038 (A3 · D227 items 1-3): the selection is the generated one, and the shell cannot narrow it either."""

    def run_table(self, text: str) -> subprocess.CompletedProcess[str]:
        (self.service / "pyproject.toml").write_text(text, encoding="utf-8")
        return self.run_wrapper("apps/service", meta={"src/pkg/a.py": {KEY: None}}, results={"src/pkg/a.py": {KEY: 1}})

    def test_a3_the_held_values_are_the_ones_the_starter_is_generated_with(self) -> None:
        generated = tomllib.loads((LANGUAGE_ROOT / "python" / "app" / "pyproject.toml").read_text(encoding="utf-8"))
        table = generated["tool"]["mutmut"]
        module = loaded(SCRIPT)
        for setting, held in module.HELD.items():
            self.assertEqual(held, table[setting], setting)
        self.assertNotIn("tests_dir", table)

    def test_a3_the_generated_selection_passes(self) -> None:
        done = self.run_table(narrowed())
        self.assertEqual(done.returncode, 0, lines_of(done))

    def test_a3_each_narrowing_fails_the_run_with_one_line_before_anything_runs(self) -> None:
        held_selection, held_args = SELECTION, CLI_ARGS
        cases = (
            (narrowed('["tests"]'), narrowing("pytest_add_cli_args_test_selection", '["tests"]', held_selection)),
            (narrowed('["tests/unit", "--ignore=tests/integration"]'),
             narrowing("pytest_add_cli_args_test_selection", '["tests/unit", "--ignore=tests/integration"]',
                       held_selection)),
            (narrowed(None), narrowing("pytest_add_cli_args_test_selection", "missing", held_selection)),
            (narrowed(cli_args='["-p", "no:xdist", "-k", "not slow"]'),
             narrowing("pytest_add_cli_args", '["-p", "no:xdist", "-k", "not slow"]', held_args)),
            (narrowed(cli_args='["-p", "no:xdist", "--deselect", "tests/test_a.py::test_b"]'),
             narrowing("pytest_add_cli_args", '["-p", "no:xdist", "--deselect", "tests/test_a.py::test_b"]',
                       held_args)),
            (narrowed(cli_args=None), narrowing("pytest_add_cli_args", "missing", held_args)),
            (narrowed(extra='tests_dir = ["tests/unit"]\n'), narrowing("tests_dir", '["tests/unit"]', "absent")),
            (narrowed(extra='tests_dir = []\n'), narrowing("tests_dir", "[]", "absent")),
        )
        for text, line in cases:
            with self.subTest(line=line):
                done = self.run_table(text)
                self.assertEqual(done.returncode, 1)
                self.assertEqual([found for found in lines_of(done) if "narrows" in found], [line])

    def test_a3_a_narrowing_is_decided_before_a_file_with_no_mutant_to_run_exits(self) -> None:
        (self.service / "pyproject.toml").write_text(narrowed('["tests"]'), encoding="utf-8")
        done = self.run_wrapper("apps/service", "--file", "src/pkg/types.py", meta={"src/pkg/types.py": {}})
        self.assertEqual(done.returncode, 1)
        done = self.run_wrapper("apps/service", "--file", "src/pkg/other.py", meta={})
        self.assertEqual(done.returncode, 1)

    def test_a3_every_pytest_variable_is_stripped_from_every_call_with_a_line_each_and_the_rest_passes(self) -> None:
        extra = {"PYTEST_CURRENT_TEST": "x", "PYTEST_PLUGINS": "evil", "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
                 "PYTHONPATH": "/some/path"}
        done = self.run_with("apps/service", extra=extra, meta={"src/pkg/a.py": {KEY: None}},
                             results={"src/pkg/a.py": {KEY: 1}})
        said = [line for line in lines_of(done) if "is not passed to mutmut" in line]
        tail = ("is not passed to mutmut (it would change how every mutant's tests run); [tool.mutmut] "
                "pytest_add_cli_args is where this service adds pytest options")
        self.assertEqual(said, [f"mutation: {name} {tail}" for name in
                                ("PYTEST_CURRENT_TEST", "PYTEST_DISABLE_PLUGIN_AUTOLOAD", "PYTEST_PLUGINS")])
        self.assertGreaterEqual(len(self.calls()), 2)
        for call in self.calls():
            self.assertEqual(call["env"], {})

    def test_a3_the_note_and_the_fragment_each_say_what_the_wrapper_does_not_read(self) -> None:
        sentence = ("The wrapper does not read pytest's own configuration (`addopts` in `[tool.pytest.ini_options]`, "
                    "`pytest.ini`, `tox.ini`, `setup.cfg`, `conftest.py` hooks): a `--deselect`, `-k` or `-m` there, "
                    "or a collection hook, narrows `make test` and `make mutation` alike, and those mutants show as "
                    "`no tests`.")
        note = " ".join(line.removeprefix("# ").removeprefix("#") for line in PYTHON_MUTATION_NOTE.splitlines())
        self.assertIn(sentence, " ".join(note.split()))
        self.assertIn(sentence, " ".join(FRAGMENT.read_text(encoding="utf-8").split()))


class ExcludedFilesTest(PhaseCase):
    """T040 (A5 · D227 item 4): every file `[tool.mutmut]` leaves out is named, with its reason, and counted."""

    def table(self, extra: str, root: str = "src") -> None:
        (self.service / "pyproject.toml").write_text(
            narrowed(extra=extra).replace('source_paths = ["src"]', f'source_paths = ["{root}"]'), encoding="utf-8")

    def tree_of(self, *names: str) -> None:
        for name in names:
            (self.service / name).parent.mkdir(parents=True, exist_ok=True)
            (self.service / name).write_text("x = 1\n", encoding="utf-8")

    def sweep(self) -> subprocess.CompletedProcess[str]:
        return self.run_wrapper("apps/service", meta={"src/pkg/a.py": {KEY: None}}, results={"src/pkg/a.py": {KEY: 1}})

    def test_a5_each_dropped_file_is_named_with_its_reason_and_the_last_line_counts_them(self) -> None:
        self.table('do_not_mutate = ["src/pkg/skip*", "*/gen.py"]\nonly_mutate = ["src/pkg/*.py"]\n')
        self.tree_of("src/pkg/a.py", "src/pkg/skip_me.py", "src/pkg/gen.py", "src/other/b.py",
                     "src/pkg/__pycache__/c.py", "tests/test_a.py", "src/pkg/notes.txt")
        done = self.sweep()
        self.assertEqual(done.returncode, 0, lines_of(done))
        lines = lines_of(done)
        self.assertEqual([line for line in lines if "not mutated" in line], [
            "mutation: not mutated apps/service/src/other/b.py \u2014 excluded by [tool.mutmut] only_mutate (no "
            "pattern matches)",
            'mutation: not mutated apps/service/src/pkg/gen.py \u2014 excluded by [tool.mutmut] do_not_mutate '
            '"*/gen.py"',
            'mutation: not mutated apps/service/src/pkg/skip_me.py \u2014 excluded by [tool.mutmut] do_not_mutate '
            '"src/pkg/skip*"'])
        self.assertLess(lines.index(next(line for line in lines if "gen.py" in line)),
                        lines.index(next(line for line in lines if line.startswith("mutation: mutmut exited"))))
        self.assertEqual(lines[-1], "mutation: 1 mutants: 1 killed, 0 no tests (reported, never failed); passed \u2014 "
                                    "report apps/service/mutants/, 3 file(s) excluded by [tool.mutmut]")

    def test_a5_a_file_outside_the_source_roots_is_named_with_the_roots(self) -> None:
        self.table("", root="src/pkg")
        self.tree_of("src/pkg/a.py", "src/other/b.py")
        done = self.sweep()
        self.assertIn("mutation: not mutated apps/service/src/other/b.py \u2014 excluded by [tool.mutmut] source_paths "
                      "(not under src/pkg)", lines_of(done))

    def test_a5_nothing_excluded_adds_nothing_and_changes_no_line(self) -> None:
        self.table("")
        self.tree_of("src/pkg/a.py")
        done = self.sweep()
        self.assertEqual(lines_of(done)[-1], "mutation: 1 mutants: 1 killed, 0 no tests (reported, never failed); "
                                             "passed \u2014 report apps/service/mutants/")
        self.assertFalse([line for line in lines_of(done) if "not mutated" in line])

    def test_a5_exclusions_do_not_change_the_status_and_a_sweep_of_only_excluded_files_still_fails(self) -> None:
        self.table('do_not_mutate = ["src/pkg/*"]\n')
        self.tree_of("src/pkg/a.py")
        done = self.run_wrapper("apps/service", meta={})
        self.assertEqual(done.returncode, 1)
        self.assertEqual(lines_of(done)[-1], "mutation: mutmut found nothing to mutate in apps/service; a pass on "
                                             "nothing is not a pass, 1 file(s) excluded by [tool.mutmut]")

    def test_a5_the_note_and_the_fragment_say_it(self) -> None:
        sentence = ("A `.py` file under `src/` that the table leaves out (`do_not_mutate`, `only_mutate`, "
                    "`source_paths`) is named on a line of its own with the reason, and the sweep's last line counts "
                    "them")
        note = " ".join(line.removeprefix("# ").removeprefix("#") for line in PYTHON_MUTATION_NOTE.splitlines())
        self.assertIn(sentence, " ".join(note.split()))
        self.assertIn(sentence, " ".join(FRAGMENT.read_text(encoding="utf-8").split()))

    def test_a5_a_scoped_run_gives_the_reason_for_a_file_it_was_handed(self) -> None:
        self.table('do_not_mutate = ["src/pkg/skip*"]\n')
        done = self.run_wrapper("apps/service", "--file", "src/pkg/skip_me.py", "--file", "scripts/x.py", "--file",
                                "README.md")
        self.assertEqual(done.returncode, 0)
        self.assertEqual(lines_of(done)[:3], [
            'mutation: not mutated apps/service/src/pkg/skip_me.py \u2014 excluded by [tool.mutmut] do_not_mutate '
            '"src/pkg/skip*"',
            "mutation: not mutated apps/service/scripts/x.py \u2014 excluded by [tool.mutmut] source_paths (not "
            "under src)",
            "mutation: not mutated apps/service/README.md \u2014 outside mutmut's configured targets"])


class CatchUpConflictsTest(unittest.TestCase):
    """T044 (B5): the Catch-up names every file a `migrate` of a project with an added Python service conflicts in."""

    def test_b5_the_catch_up_names_all_five_files_and_the_side_to_take_in_the_makefile(self) -> None:
        text = FRAGMENT.read_text(encoding="utf-8")
        (paragraph,) = [block for block in text.split("\n\n") if block.startswith("**Catch-up.**")]
        squashed = " ".join(paragraph.split())
        for name in ("Makefile", "apps/<service>/pyproject.toml", "apps/<service>/uv.lock", "commands/mutation.md",
                     "scripts/verify_scoped/rules.json"):
            with self.subTest(file=name):
                self.assertIn(f"`{name}`", squashed)
        self.assertIn("take the factory's side of the `mutation-full` hunk in `Makefile`", squashed)



class WordsTest(unittest.TestCase):
    """D228 item 6: the note and the fragment quote the summary line."""

    def test_d228_the_note_and_the_fragment_quote_the_summary_line(self) -> None:
        quoted = "`<s> swept, <r> refused; passed`"
        note = " ".join(line.removeprefix("# ").removeprefix("#") for line in PYTHON_MUTATION_NOTE.splitlines())
        self.assertIn(quoted, " ".join(note.split()))
        self.assertIn(quoted, " ".join(FRAGMENT.read_text(encoding="utf-8").split()))


if __name__ == "__main__":
    unittest.main()
