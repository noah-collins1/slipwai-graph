"""S42 T003 (rule 2 · AC-S42-6 half, AC-S42-8 half): the configuration `mutmut-mutation.py` reads, and what it refuses.

The wrapper is loaded as a module (bytecode off) for `targets`, `matched`, `refused` and `versions`, and run as a
subprocess in a temporary project with a fake `uv` first on `PATH`, written here, that fails the example if it is ever
called: every example of this module is decided before mutmut would start.
"""
from __future__ import annotations

import importlib.util
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

from slipwai.assets import LANGUAGE_ROOT

sys.dont_write_bytecode = True
SCRIPT = LANGUAGE_ROOT / "python" / "scripts/mutmut-mutation.py"
TEST_SELECTION = {"reads": ["assets/languages/python/scripts/mutmut-mutation.py"]}
FAKE_UV = """#!/bin/sh
echo "uv $*" >> "$FAKE_LOG"
exit 99
"""
TABLE = """[tool.mutmut]
source_paths = ["src"]
pytest_add_cli_args_test_selection = ["tests", "--ignore=tests/integration"]
pytest_add_cli_args = ["-p", "no:xdist"]
"""


def loaded(script: Path) -> Any:
    """The wrapper as a module, loaded by path with bytecode off."""
    spec = importlib.util.spec_from_file_location("mutmut_mutation_under_test", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def table(**keys: Any) -> str:
    """A `[tool.mutmut]` table with the given keys, TOML-written by `repr` (lists of strings and strings only)."""
    return "[tool.mutmut]\n" + "".join(f"{key} = {value!r}\n".replace("'", '"') for key, value in keys.items())


class Case(unittest.TestCase):
    def setUp(self) -> None:
        self.module = loaded(SCRIPT)
        self.root = Path(tempfile.mkdtemp(prefix="mutmut-config-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        (self.bin / "uv").write_text(FAKE_UV, encoding="utf-8")
        (self.bin / "uv").chmod(0o755 | stat.S_IXUSR)
        self.log = self.root / "uv.log"
        self.tree = self.root / "tree"
        self.tree.mkdir()

    def service(self, text: str | None, path: str = "apps/service") -> Path:
        directory = self.tree / path
        directory.mkdir(parents=True, exist_ok=True)
        if text is not None:
            (directory / "pyproject.toml").write_text(text, encoding="utf-8")
        return directory

    def run_wrapper(self, *arguments: str, prelude: str = "") -> subprocess.CompletedProcess[str]:
        env = {**os.environ, "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}", "FAKE_LOG": str(self.log)}
        for marker in ("CI", "GITHUB_ACTIONS", "GITLAB_CI"):
            env.pop(marker, None)
        if prelude:
            code = f"{prelude}\nimport runpy, sys\nsys.argv = [{str(SCRIPT)!r}, *{list(arguments)!r}]\n" \
                   f"runpy.run_path({str(SCRIPT)!r}, run_name='__main__')"
            command = [sys.executable, "-B", "-c", code]
        else:
            command = [sys.executable, "-B", str(SCRIPT), *arguments]
        return subprocess.run(command, cwd=self.tree, env=env, text=True, capture_output=True, timeout=60)

    def assertUvNeverCalled(self) -> None:
        self.assertFalse(self.log.exists(), self.log.read_text(encoding="utf-8") if self.log.exists() else "")


class TargetsAndMatchedTest(Case):
    def test_e1_the_generated_table_is_read(self) -> None:
        config = self.module.targets(self.service(TABLE))
        self.assertEqual(config.get("source_paths"), ["src"])
        self.assertEqual(config.get("only_mutate"), [])
        self.assertEqual(config.get("do_not_mutate"), [])
        self.assertEqual(config.get("pytest_add_cli_args"), ["-p", "no:xdist"])

    def test_e1_the_deprecated_name_is_read_alone_and_ignored_beside_the_new_one(self) -> None:
        self.assertEqual(self.module.targets(self.service(table(paths_to_mutate=["lib"]))).get("source_paths"), ["lib"])
        both = self.service(table(paths_to_mutate=["lib"], source_paths=["src"]))
        self.assertEqual(self.module.targets(both).get("source_paths"), ["src"])

    def test_e1_matched_is_mutmuts_should_mutate_for_a_file_under_source_paths(self) -> None:
        config = self.module.targets(self.service(TABLE))
        for name in ("src/pkg/a.py", "src/a.py", "src/pkg/sub/b.py", "src/pkg/__init__.py"):
            with self.subTest(file=name):
                self.assertTrue(self.module.matched(config, name))
        for name in ("src/pkg/a.pyi", "src/pkg/data.txt", "tests/test_a.py", "scripts/x.py", "srcx/a.py"):
            with self.subTest(file=name):
                self.assertFalse(self.module.matched(config, name))

    def test_e1_only_mutate_and_do_not_mutate_are_fnmatch_patterns_over_the_path(self) -> None:
        only = self.module.targets(self.service(table(source_paths=["src"], only_mutate=["src/pkg/a*"])))
        self.assertTrue(self.module.matched(only, "src/pkg/a.py"))
        self.assertTrue(self.module.matched(only, "src/pkg/abc.py"))
        self.assertFalse(self.module.matched(only, "src/pkg/b.py"))
        skipped = self.module.targets(self.service(table(source_paths=["src"], do_not_mutate=["*/gen_*"])))
        self.assertFalse(self.module.matched(skipped, "src/pkg/gen_x.py"))
        self.assertTrue(self.module.matched(skipped, "src/pkg/x.py"))

    def test_e1_two_source_paths_match_under_either(self) -> None:
        config = self.module.targets(self.service(table(source_paths=["src", "lib"])))
        self.assertTrue(self.module.matched(config, "lib/x.py"))
        self.assertTrue(self.module.matched(config, "src/x.py"))
        self.assertFalse(self.module.matched(config, "other/x.py"))

    def test_e6_hold_a_nested_service_and_a_trailing_slash_read_the_same_table(self) -> None:
        """HOLD (teeth: read `<service>/pyproject.toml` from the working directory and see it fail)."""
        self.service(TABLE, "apps/billing")
        for spelled in (str(self.tree / "apps/billing"), str(self.tree / "apps/billing") + "/"):
            self.assertEqual(self.module.targets(spelled).get("source_paths"), ["src"], spelled)
        done = self.run_wrapper("apps/billing/", "--file", "src/pkg/a*.py")
        self.assertEqual(done.returncode, 2)
        self.assertIn("apps/billing/src/pkg/a*.py", done.stdout)


class UnreadableTest(Case):
    def assertUnreadable(self, text: str | None, mentions: str, path: str = "apps/service") -> None:
        with self.assertRaises(self.module.Unreadable) as raised:
            self.module.targets(self.service(text, path))
        self.assertIn(mentions, str(raised.exception))

    def test_e2_each_value_outside_the_subset_is_unreadable_and_named(self) -> None:
        for value in ([], ["../x"], ["/abs"], ["s*"], ["s?"], ["s[ab]"], "src", [1]):
            with self.subTest(source_paths=value):
                text = "[tool.mutmut]\nsource_paths = " + (
                    "[]" if value == [] else str(value).replace("'", '"') if value != "src" else '"src"') + "\n"
                with self.assertRaises(self.module.Unreadable) as raised:
                    self.module.targets(self.service(text))
                self.assertIn("source_paths", str(raised.exception))
        for key, value in (("only_mutate", "x"), ("do_not_mutate", [1])):
            with self.subTest(key=key):
                with self.assertRaises(self.module.Unreadable) as raised:
                    self.module.targets(self.service(table(source_paths=["src"], **{key: value})))
                self.assertIn(key, str(raised.exception))

    def test_e2_a_source_path_matched_cannot_place_as_mutmut_walks_it_is_unreadable_and_named(self) -> None:
        """mutmut reads each entry as `Path(entry)` and walks it, a file included; `matched` places a file by the prefix
        of the entry as written. An entry that is not the canonical relative directory form is not read at all."""
        for value in ("./src", "src/./pkg", ".", "./", "src/app.py", "src//pkg", "src/.", "", "src\\pkg", "//src"):
            with self.subTest(source_paths=value):
                self.assertUnreadable(table(source_paths=[value]), repr(value))
                self.assertUnreadable(table(source_paths=["src", value]), repr(value))

    def test_e2_hold_the_canonical_directory_forms_are_read_and_place_their_files(self) -> None:
        """HOLD (teeth: refuse a trailing slash, or any nested entry, and see it fail)."""
        for value, inside in (("src", "src/pkg/a.py"), ("src/", "src/pkg/a.py"), ("lib/sub", "lib/sub/a.py"),
                              ("lib/sub/", "lib/sub/a.py")):
            with self.subTest(source_paths=value):
                config = self.module.targets(self.service(table(source_paths=[value])))
                self.assertTrue(self.module.matched(config, inside))
                self.assertFalse(self.module.matched(config, "other/a.py"))

    def test_e2_a_missing_table_file_or_toml_is_unreadable(self) -> None:
        self.assertUnreadable("[tool.other]\nx = 1\n", "no [tool.mutmut] table")
        self.assertUnreadable(None, "cannot be read", "apps/absent")
        self.assertUnreadable("[tool.mutmut\n", "TOML")

    def test_e2_no_tomllib_says_which_python_reads_the_table(self) -> None:
        self.service(TABLE)
        done = self.run_wrapper("apps/service", prelude="import sys; sys.modules['tomllib'] = None")
        self.assertEqual(done.returncode, 2)
        self.assertEqual(done.stdout.strip(),
                         "mutation: apps/service/pyproject.toml: no tomllib: Python 3.11 or newer reads [tool.mutmut]")
        self.assertUvNeverCalled()


class RefusedTest(Case):
    def test_e3_a_fnmatch_opener_in_a_path_is_refused_in_the_data_models_words(self) -> None:
        for char in "*?[":
            with self.subTest(char=char):
                self.assertEqual(
                    self.module.refused("apps/service", f"src/pkg/a{char}.py"),
                    f"`apps/service/src/pkg/a{char}.py` holds `{char}`, which mutmut reads as a pattern over mutant "
                    "names; rename it, or run `make mutation-full`")

    def test_e3_hold_only_the_three_openers_are_refused(self) -> None:
        """HOLD (teeth: refuse every non-alphanumeric and see it fail)."""
        for name in ("src/pkg/a.py", "src/a b.py", "src/a$b.py", "src/a#b.py", "src/a!b.py", "src/a,b.py",
                     "src/a{b}.py", "src/été.py", "src/a]b.py"):
            with self.subTest(name=name):
                self.assertIsNone(self.module.refused("apps/service", name))


class VersionsTest(Case):
    LOCK = """version = 1
[[package]]
name = "mutmut"
version = "3.8.0"
dependencies = [{ name = "libcst" }, { name = "pytest" }, { name = "textual" }]
[[package]]
name = "libcst"
version = "1.9.0"
dependencies = [{ name = "pyyaml", marker = "python_full_version < '3.13'" },
                { name = "pyyaml-ft", marker = "python_full_version >= '3.13'" }]
[[package]]
name = "pyyaml"
version = "6.0.3"
[[package]]
name = "pyyaml-ft"
version = "8.0.0"
[[package]]
name = "pytest"
version = "9.1.1"
[[package]]
name = "coverage"
version = "7.0.0"
[[package]]
name = "textual"
version = "1.0.0"
"""

    def test_e4_a_manifest_gives_its_table_and_every_mutmut_requirement(self) -> None:
        text = '[dependency-groups]\ndev = ["mutmut==3.8.0", "ruff==0.16.3"]\n' + TABLE
        found = self.module.versions(text)
        self.assertEqual(found.get("requirement"), ["mutmut==3.8.0"])
        self.assertEqual((found.get("tool.mutmut") or {}).get("source_paths"), ["src"])
        two = self.module.versions('[project]\ndependencies = ["mutmut>=3"]\n[dependency-groups]\n'
                                   'dev = ["mutmut==3.8.0"]\n[project.optional-dependencies]\nx = ["mutmut"]\n')
        self.assertEqual(sorted(two.get("requirement", [])), ["mutmut", "mutmut==3.8.0", "mutmut>=3"])
        self.assertEqual(self.module.versions('[project]\nname = "x"\n'), {"tool.mutmut": None, "requirement": []})

    def test_e4_a_lock_gives_mutmut_and_libcst_s_closure_by_name_and_nothing_else(self) -> None:
        """The closure is libcst's (D222's reason as R6 reads it); HOLD (teeth: add pytest and see it fail)."""
        found = self.module.versions(None, self.LOCK)
        self.assertEqual(found, {"mutmut": ["3.8.0"], "libcst": ["1.9.0"], "pyyaml": ["6.0.3"],
                                 "pyyaml-ft": ["8.0.0"]})
        for name in ("pytest", "coverage", "textual"):
            self.assertNotIn(name, found)

    def test_e4_two_versions_of_one_name_are_both_listed(self) -> None:
        lock = self.LOCK + '[[package]]\nname = "pyyaml"\nversion = "6.0.2"\n'
        self.assertEqual(sorted(self.module.versions(None, lock).get("pyyaml", [])), ["6.0.2", "6.0.3"])

    def test_e4_text_that_does_not_parse_or_is_not_a_lock_is_unreadable(self) -> None:
        for args in (("[dependency-groups\n", None), (None, "not = [toml"), (None, "version = 1\n")):
            with self.subTest(args=args), self.assertRaises(self.module.Unreadable):
                self.module.versions(*args)


class MainTest(Case):
    def test_e5_a_refused_file_is_exit_two_in_one_line_and_nothing_is_touched(self) -> None:
        service = self.service(TABLE)
        (service / "mutants").mkdir()
        (service / "mutants" / "old.meta").write_text("{}", encoding="utf-8")
        done = self.run_wrapper("apps/service", "--file", "src/pkg/a.py", "--file", "src/pkg/a*.py")
        self.assertEqual(done.returncode, 2)
        lines = (done.stdout + done.stderr).strip().splitlines()
        self.assertEqual(lines, ["mutation: `apps/service/src/pkg/a*.py` holds `*`, which mutmut reads as a pattern "
                                 "over mutant names; rename it, or run `make mutation-full`"])
        self.assertTrue((service / "mutants" / "old.meta").is_file())
        self.assertUvNeverCalled()

    def test_e5_a_service_with_no_table_is_exit_two_and_uv_is_never_called(self) -> None:
        self.service("[project]\nname = 'x'\n")
        done = self.run_wrapper("apps/service")
        self.assertEqual(done.returncode, 2)
        self.assertEqual(done.stdout.strip(), "mutation: apps/service/pyproject.toml: no [tool.mutmut] table")
        self.assertUvNeverCalled()

    def test_e5_a_valid_invocation_reaches_the_next_task_s_seam(self) -> None:
        """The seam is the setup (T004): the fake `uv` that fails every call is first reached by `uv sync`."""
        self.service(TABLE)
        done = self.run_wrapper("apps/service", "--file", "src/pkg/a.py")
        self.assertEqual(done.returncode, 2)
        self.assertIn("uv.lock does not agree", done.stdout)
        self.assertEqual(self.log.read_text(encoding="utf-8").splitlines(), [
            "uv sync --project apps/service --locked --quiet"])


if __name__ == "__main__":
    unittest.main()
