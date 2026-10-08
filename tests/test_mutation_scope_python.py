"""S42 T007 (rule 6 · AC-S42-2, -3, -8, -11): `make mutation` for a Python service.

The project is the Go one `mutation_scope_fixture` cuts, with the wrapper and a `[tool.mutmut]` table per Python service
committed on `main` (the base), so a change on `slice/S1` is the change under test. The tool is the recording `Runner`
`test_mutation_scope_typescript` writes, which plans with the script's own `Tools` (the table and the wrapper's matching
are real) and runs nothing: the real wrapper behind a fake `uv` is `test_mutmut_verdict`'s.
"""
from __future__ import annotations

import contextlib
import io
import os
import sys
from typing import Any

from stamp_fixture import git
from test_mutation_borders import clean_environment, loaded
from test_mutation_scope_typescript import Planned
from test_mutation_sweeps import Recorded

from slipwai.assets import LANGUAGE_ROOT

sys.dont_write_bytecode = True
WRAPPER = LANGUAGE_ROOT / "python" / "scripts/mutmut-mutation.py"
TABLE = '[tool.mutmut]\nsource_paths = ["src"]\n'
HEALTH = "apps/service/src/pkg/health.py"
OUTSIDE = "outside mutmut's configured targets"
TWO = ("python:apps/service", "python:apps/second")
GO_AND = ("go:apps/service", "python:apps/second")
QUARKUS_AND = ("java-quarkus:apps/service", "python:apps/second")
SOURCE = "def health() -> int:\n    return 1\n"


class Mixed(Planned):
    """As `Planned`, except that a placeholder's run is the script's own: the refusal is the real one."""

    def run(self, backend: str, path: str, files: list[str]) -> Any:
        return self.tools.run(backend, path, files) if backend == "java-quarkus" else super().run(backend, path, files)


class PythonCase(Recorded):
    """`apps/service` and `apps/second` are Python services at the base: a table each, the wrapper too."""

    def setUp(self) -> None:
        super().setUp()
        self.on_main("scripts/mutmut-mutation.py", text=WRAPPER.read_text(encoding="utf-8"))
        self.on_main("apps/service/pyproject.toml", "apps/second/pyproject.toml", text=TABLE)
        self.on_main(".gitignore", text=(self.repo / ".gitignore").read_text(encoding="utf-8") + "mutants/\n")

    def reset(self) -> None:
        """Back to the base: no change from an earlier example of the same test."""
        git(self.repo, "checkout", "-q", "--", ".")
        git(self.repo, "clean", "-qfd", "apps", "packages", "docs")

    def table(self, text: str, root: str = "apps/service") -> None:
        self.on_main(f"{root}/pyproject.toml", text=text)

    def run_planned(self, *services: str, env: dict[str, str] | None = None) -> tuple[int, list[str], Mixed]:
        self.fit_recipe(services)
        module = loaded(self.repo / "scripts/mutation-scope.py")
        recording = Mixed(module)
        wanted, saved, here = (clean_environment() if env is None else env), dict(os.environ), os.getcwd()
        os.environ.clear()
        os.environ.update(wanted)
        os.chdir(self.repo)
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                status = module.main(["--make", str(self.make), "--makefile", "Makefile", *services], recording)
        finally:
            os.chdir(here)
            os.environ.clear()
            os.environ.update(saved)
        return status, out.getvalue().splitlines(), recording


class ScopeTest(PythonCase):
    def test_e1_one_changed_module_is_scoped_to_that_file_in_that_service(self) -> None:
        self.write(HEALTH, SOURCE)
        status, lines, recording = self.run_planned("python:apps/service")
        self.assertEqual(status, 0, lines)
        self.assertTrue(lines[0].startswith("mutation: scoped to 1 changed file(s) since `main` at "), lines)
        self.assertTrue(lines[0].endswith(f": {HEALTH}"), lines[0])
        self.assertIn("mutation: scope apps/service — src/pkg/health.py", lines)
        self.assertEqual(lines[-1], "mutation: 1 scoped, 0 swept, 0 skipped, 0 refused; passed")
        self.assertEqual(recording.scoped, [("apps/service", ["src/pkg/health.py"])])

    def test_e2_the_other_service_starts_no_tool_and_keeps_no_earlier_mutants(self) -> None:
        for services, other, changed in ((TWO, "apps/second", HEALTH), (GO_AND, "apps/second", "apps/service/x/x.go")):
            with self.subTest(services=services):
                self.reset()
                earlier = self.repo / other / "mutants/src/pkg/a.py.meta"
                earlier.parent.mkdir(parents=True, exist_ok=True)
                earlier.write_text("{}", encoding="utf-8")
                self.write(changed, SOURCE)
                status, lines, recording = self.run_planned(*services)
                self.assertEqual(status, 0, lines)
                self.assertIn(f"mutation: skip {other} — no changed production file", lines)
                self.assertEqual([path for path, _ in recording.scoped], ["apps/service"])
                self.assertFalse((self.repo / other / "mutants").exists(), "an earlier run's mutants/ is left behind")
        self.reset()
        gremlins = self.repo / "apps/service/gremlins.json"
        gremlins.write_text("{}", encoding="utf-8")
        self.write("apps/second/src/pkg/b.py", SOURCE)
        _, lines, recording = self.run_planned(*GO_AND)
        self.assertEqual(recording.scoped, [("apps/second", ["src/pkg/b.py"])])
        self.assertIn("mutation: skip apps/service — no changed production file", lines)
        self.assertFalse(gremlins.exists())

    def test_e3_a_test_alone_and_a_deleted_module_alone_are_s08_s_lines(self) -> None:
        self.write("apps/service/tests/test_x.py", SOURCE)
        status, lines, recording = self.run_planned("python:apps/service")
        self.assertEqual((status, recording.scoped), (0, []), lines)
        self.assertTrue(lines[0].startswith("mutation: no mutant to run — only tests changed: "), lines)
        self.reset()
        self.on_main("apps/service/src/pkg/old.py", text=SOURCE)
        (self.repo / "apps/service/src/pkg/old.py").unlink()
        status, lines, recording = self.run_planned("python:apps/service")
        self.assertEqual((status, recording.scoped), (0, []), lines)
        self.assertIn("mutation: not mutated apps/service/src/pkg/old.py — deleted, no mutants", lines)

    def test_e3_a_module_the_table_leaves_out_is_named_and_starts_nothing(self) -> None:
        tables = {
            "only_mutate that does not match": '[tool.mutmut]\nsource_paths = ["src"]\nonly_mutate = ["src/other/*"]\n',
            "do_not_mutate that matches": '[tool.mutmut]\nsource_paths = ["src"]\ndo_not_mutate = ["src/pkg/*"]\n',
            "a file outside source_paths": '[tool.mutmut]\nsource_paths = ["src/other"]\n',
        }
        for name, text in tables.items():
            with self.subTest(table=name):
                self.table(text)
                self.write(HEALTH, SOURCE)
                status, lines, recording = self.run_planned("python:apps/service")
                self.assertEqual(status, 0, lines)
                self.assertIn(f"mutation: not mutated {HEALTH} — {OUTSIDE}", lines)
                self.assertEqual(lines[0], "mutation: no mutant to run — every changed production file is outside "
                                           "the tools' targets")
                self.assertEqual(recording.scoped, [])
                self.reset()
        self.table('[tool.mutmut]\nsource_paths = ["src"]\ndo_not_mutate = ["src/other.py"]\n')
        self.write(HEALTH, SOURCE)
        self.write("apps/service/src/other.py", SOURCE)
        status, lines, recording = self.run_planned("python:apps/service")
        self.assertEqual(recording.scoped, [("apps/service", ["src/pkg/health.py"])])
        self.assertIn(f"mutation: not mutated apps/service/src/other.py — {OUTSIDE}", lines)
        self.assertEqual(status, 0)

    def test_e6_hold_the_borders_since_and_an_empty_change_set_behave_as_for_go(self) -> None:
        """HOLD (teeth: make the empty change set sweep and see the last example fail)."""
        self.fit_recipe(("python:apps/service",))
        self.write(HEALTH, SOURCE)
        self.commit("health")
        since = {**clean_environment(), "SINCE": "HEAD~1"}
        _, lines, recording = self.run_planned("python:apps/service", env=since)
        self.assertEqual(recording.scoped, [("apps/service", ["src/pkg/health.py"])], lines)
        git(self.repo, "checkout", "-q", "main")
        _, lines, _ = self.run_planned("python:apps/service")
        self.assertTrue(any(line.startswith("mutation: the sweep runs — ") for line in lines), lines)
        git(self.repo, "checkout", "-q", "-B", "slice/S2", "main")
        status, lines, recording = self.run_planned("python:apps/service")
        self.assertEqual((status, lines[0], recording.scoped, recording.swept),
                         (0, "mutation: no mutant to run — no production file changed", [], []))
        module = loaded(self.repo / "scripts/mutation-scope.py")
        self.assertEqual(module.factory_recipe([("python", "apps/service")]),
                         ["python3 scripts/mutmut-mutation.py apps/service"])

    def test_e7_a_table_the_script_cannot_read_is_that_service_s_sweep(self) -> None:
        forms = {f"source_paths {value}": f'[tool.mutmut]\nsource_paths = ["{value}"]\n'
                 for value in ("./src", "src/./pkg", ".", "src/app.py", "src//pkg")}
        for name, text in (("a glob in source_paths", '[tool.mutmut]\nsource_paths = ["s*"]\n'),
                           ("no table", '[project]\nname = "x"\n'), *forms.items()):
            with self.subTest(table=name):
                self.table(text)
                self.write(HEALTH, SOURCE)
                status, lines, recording = self.run_planned("python:apps/service")
                self.assertEqual(status, 0, lines)
                sweep = next((line for line in lines if line.startswith("mutation: sweep apps/service — ")), "")
                self.assertTrue(sweep, lines)
                self.assertIn("apps/service/pyproject.toml", sweep)
                self.assertEqual((recording.swept, recording.scoped), (["apps/service"], []))
                self.reset()

    def test_e7_no_tomllib_is_that_service_s_sweep(self) -> None:
        self.write(HEALTH, SOURCE)
        saved = sys.modules.get("tomllib")
        sys.modules["tomllib"] = None  # type: ignore[assignment]
        try:
            status, lines, recording = self.run_planned("python:apps/service")
        finally:
            if saved is None:
                del sys.modules["tomllib"]
            else:
                sys.modules["tomllib"] = saved
        self.assertEqual(status, 0, lines)
        self.assertEqual((recording.swept, recording.scoped), (["apps/service"], []), lines)


def words(file: str, char: str) -> str:
    return (f"`apps/service/{file}` holds `{char}`, which mutmut reads as a pattern over mutant names; "
            "rename it, or run `make mutation-full`")


class RefusalTest(PythonCase):
    """A changed path `mutmut run` would read as a pattern over mutant names refuses its service and starts no tool."""

    def test_e4_a_star_question_mark_or_bracket_refuses_the_service_and_runs_and_sweeps_nothing(self) -> None:
        for file, char in (("a*.py", "*"), ("a?.py", "?"), ("[a].py", "[")):
            with self.subTest(file=file):
                self.write(f"apps/service/src/pkg/{file}", SOURCE)
                status, lines, recording = self.run_planned("python:apps/service")
                self.assertEqual(status, 2, lines)
                self.assertIn("mutation: refuse apps/service — " + words(f"src/pkg/{file}", char), lines)
                self.assertEqual(lines[-1], "mutation: 0 scoped, 0 swept, 0 skipped, 1 refused; failed: apps/service")
                self.assertEqual((recording.scoped, recording.swept), ([], []))
                self.reset()

    def test_e4_a_space_dollar_bang_comma_or_brace_is_not_refused(self) -> None:
        """HOLD (teeth: add `$` to the wrapper's openers and see it fail)."""
        for file in ("a b.py", "a$b.py", "a!b.py", "a,b.py", "a{b}.py"):
            with self.subTest(file=file):
                self.write(f"apps/service/src/pkg/{file}", SOURCE)
                status, lines, recording = self.run_planned("python:apps/service")
                self.assertEqual(status, 0, lines)
                self.assertFalse([line for line in lines if "refuse " in line], lines)
                self.assertEqual(recording.scoped, [("apps/service", [f"src/pkg/{file}"])])
                self.reset()

    def test_e4_a_refused_file_refuses_the_whole_service_and_another_service_still_runs(self) -> None:
        self.write("apps/service/src/pkg/a*.py", SOURCE)
        self.write(HEALTH, SOURCE)
        self.write("apps/second/src/pkg/b.py", SOURCE)
        status, lines, recording = self.run_planned(*TWO)
        self.assertEqual(status, 2, lines)
        self.assertEqual(recording.scoped, [("apps/second", ["src/pkg/b.py"])])
        self.assertEqual(lines[-1], "mutation: 1 scoped, 0 swept, 0 skipped, 1 refused; failed: apps/service")

    def test_e4_the_refusal_is_louder_than_outside_targets(self) -> None:
        self.table('[tool.mutmut]\nsource_paths = ["src"]\ndo_not_mutate = ["src/pkg/*"]\n')
        self.write("apps/service/src/pkg/a*.py", SOURCE)
        _, lines, _ = self.run_planned("python:apps/service")
        self.assertIn("mutation: refuse apps/service — " + words("src/pkg/a*.py", "*"), lines)
        self.assertFalse([line for line in lines if OUTSIDE in line], lines)

    def test_e4_a_dry_run_says_would_fail_and_leaves_the_earlier_mutants(self) -> None:
        earlier = self.repo / "apps/service/mutants/src/pkg/a.py.meta"
        earlier.parent.mkdir(parents=True)
        earlier.write_text("{}", encoding="utf-8")
        self.write("apps/service/src/pkg/a*.py", SOURCE)
        status, lines, recording = self.run_planned("python:apps/service", env=clean_environment(MAKEFLAGS="n"))
        self.assertEqual(status, 0, lines)
        self.assertEqual(lines[-1], "mutation: 0 scoped, 0 swept, 0 skipped, 1 refused; "
                                    "dry run — would fail: apps/service")
        self.assertEqual((recording.scoped, recording.swept), ([], []))
        self.assertTrue(earlier.exists(), "the run did not happen, so the earlier mutants/ is not this run's to remove")

    def test_e4_a_refused_service_keeps_its_earlier_mutants(self) -> None:
        earlier = self.repo / "apps/service/mutants/src/pkg/a.py.meta"
        earlier.parent.mkdir(parents=True)
        earlier.write_text("{}", encoding="utf-8")
        self.write("apps/service/src/pkg/a*.py", SOURCE)
        self.run_planned("python:apps/service")
        self.assertTrue(earlier.exists())


class QuarkusTest(PythonCase):
    def test_e5_quarkus_still_refuses_with_its_setup_message_and_python_beside_it_runs(self) -> None:
        self.write("apps/service/src/main/java/com/x/Foo.java", "package com.x;\nclass Foo {}\n")
        self.write("apps/second/src/pkg/b.py", SOURCE)
        status, lines, runner = self.run_planned(*QUARKUS_AND)
        refusal = next(line for line in lines if line.startswith("mutation: refuse apps/service — "))
        self.assertIn("Configure PIT for the domain packages only", refusal)
        self.assertNotIn("mutmut", refusal)
        self.assertIn("mutation: scope apps/second — src/pkg/b.py", lines)
        self.assertEqual(status, 2, lines)
        self.assertEqual(lines[-1], "mutation: 1 scoped, 0 swept, 0 skipped, 1 refused; failed: apps/service")
        self.assertEqual(runner.scoped, [("apps/second", ["src/pkg/b.py"])])
