"""S42 Phase 4 (T036-T044, the adversary's findings A1-A7, B3, B5; D227, D228): what `mutmut-mutation.py` holds against
a run that is not what it seems, reproduced through the wrapper's boundary.

The harness is `test_mutmut_verdict`'s: the wrapper runs as a subprocess against a fake `uv` first on `PATH`. The fake is
that module's, read for the changes these examples need (an orphaned child of `mutmut run`, files already in `mutants/`
when generation ends, the `PYTEST_*` environment, the probe's report on where mutmut was imported from).
"""
from __future__ import annotations

import json
import os
import signal
import stat
import subprocess
import sys
import tomllib
import unittest
from pathlib import Path
from typing import Any

from slipwai.assets import LANGUAGE_ROOT
from slipwai.project.mutmut import PYTHON_MUTATION_NOTE
from test_mutmut_config import loaded
from test_mutmut_verdict import FAKE_UV, KEY, SCRIPT, TABLE, Case, lines_of

sys.dont_write_bytecode = True
# `test_mutmut_verdict` imports `slipwai`, which reads this script on import (as `test_stryker_closure` does)
TEST_SELECTION = {"reads": ["assets/languages/python/scripts/mutmut-mutation.py",
                            "assets/toolkit/scripts/check-styles.py"]}

LOG_ENV = ('json.dumps({"argv": args, "cwd": os.getcwd()})',
           'json.dumps({"argv": args, "cwd": os.getcwd(), "env": {k: v for k, v in os.environ.items() '
           'if k.startswith("PYTEST_")}})')
ORPHAN = ('write(json.loads(os.environ.get("FAKE_RESULTS", "{}")))',
          '''if os.environ.get("FAKE_ORPHAN"):
    child = os.fork()
    if child == 0:
        os.setsid()
        null = os.open(os.devnull, os.O_RDWR)
        for descriptor in (0, 1, 2):
            os.dup2(null, descriptor)
        import time
        time.sleep(60)
        os._exit(0)
    open(os.environ["FAKE_ORPHAN"], "w").write(str(child))
write(json.loads(os.environ.get("FAKE_RESULTS", "{}")))''')


PROBE = ('    print("3.8.0")\n',
         '    print("3.8.0")\n    if os.environ.get("FAKE_SHADOW"):\n        print("shadowed " + os.environ["FAKE_SHADOW"])\n')


def fake_uv() -> str:
    text = FAKE_UV
    for old, new in (LOG_ENV, ORPHAN, PROBE):
        assert old in text, "test_mutmut_verdict's fake uv no longer reads as this expects"
        text = text.replace(old, new)
    return text


class PhaseCase(Case):
    def setUp(self) -> None:
        super().setUp()
        (self.bin / "uv").write_text(fake_uv(), encoding="utf-8")
        (self.bin / "uv").chmod(0o755 | stat.S_IXUSR)

    def run_with(self, *arguments: str, extra: dict[str, str] | None = None,
                 **keywords: Any) -> subprocess.CompletedProcess[str]:
        """`run_wrapper` with more variables in the wrapper's environment."""
        saved = dict(os.environ)
        os.environ.update(extra or {})
        try:
            return self.run_wrapper(*arguments, **keywords)
        finally:
            os.environ.clear()
            os.environ.update(saved)


class OrphanTest(PhaseCase):
    """T036 (A1): a `mutmut run` child that outlives the wrapper keeps the lock."""

    def test_a1_a_run_that_leaves_a_child_alive_keeps_its_service_locked_and_the_next_run_is_refused(self) -> None:
        pidfile = self.root / "orphan.pid"
        first = self.run_with("apps/service", "--file", "src/pkg/a.py", extra={"FAKE_ORPHAN": str(pidfile)},
                              meta={"src/pkg/a.py": {KEY: None}}, results={"src/pkg/a.py": {KEY: 1}})
        orphan = int(pidfile.read_text(encoding="utf-8"))
        self.addCleanup(self.kill, orphan)
        self.assertEqual(first.returncode, 0)
        second = self.run_wrapper("apps/service", "--file", "src/pkg/a.py", meta={"src/pkg/a.py": {KEY: None}},
                                  results={"src/pkg/a.py": {KEY: 1}})
        self.assertEqual(second.returncode, 2)
        self.assertEqual(lines_of(second), ["mutation: another mutmut run of apps/service holds "
                                            "apps/service/.venv/mutmut-run.lock; wait for it, then run this again"])
        self.kill(orphan)
        third = self.run_wrapper("apps/service", "--file", "src/pkg/a.py", meta={"src/pkg/a.py": {KEY: None}},
                                 results={"src/pkg/a.py": {KEY: 1}})
        self.assertEqual(third.returncode, 0, "the lock is free once the child is gone")

    @staticmethod
    def kill(pid: int) -> None:
        try:
            os.kill(pid, signal.SIGKILL)
            os.waitpid(pid, 0)
        except (ProcessLookupError, ChildProcessError):
            pass
        for _ in range(100):
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return
            import time
            time.sleep(0.05)


class ForgedMetaTest(PhaseCase):
    """T037 (A2): after the wrapper's own generation every code is null, and only sources under `source_paths` are read."""

    FORGED = ("mutation: apps/service/src/pkg/a.py: mutmut's generation left an exit code on 1 mutant(s) before any "
              "test ran (a committed .meta file copied into mutants/?), so the verdict cannot be trusted")

    def test_a2_a_scoped_key_that_already_has_a_code_fails_the_run_naming_the_file(self) -> None:
        done = self.run_wrapper("apps/service", "--file", "src/pkg/a.py", meta={"src/pkg/a.py": {KEY: 1}},
                                results={"src/pkg/a.py": {KEY: 1}})
        self.assertEqual(done.returncode, 1)
        self.assertIn(self.FORGED, lines_of(done))
        self.assertEqual(self.started_mutmut(), [])

    def test_a2_a_sweep_of_a_forged_file_fails_the_same_way(self) -> None:
        done = self.run_wrapper("apps/service", meta={"src/pkg/a.py": {KEY: 1}}, results={"src/pkg/a.py": {KEY: 1}})
        self.assertEqual(done.returncode, 1)
        self.assertIn(self.FORGED, lines_of(done))

    def test_a2_a_meta_beside_a_test_or_outside_the_source_roots_is_never_a_verdict(self) -> None:
        meta = {"src/pkg/a.py": {KEY: None}, "tests/test_a.py": {"t.x_f__mutmut_1": 1},
                "scripts/b.py": {"b.x_f__mutmut_1": 0}, "src/pkg/readme.txt": {"r.x_f__mutmut_1": 0}}
        done = self.run_wrapper("apps/service", meta=meta, results={"src/pkg/a.py": {KEY: 1}})
        self.assertEqual(done.returncode, 0, lines_of(done))
        self.assertEqual(lines_of(done)[-1].split(" \u2014 ")[0], "mutation: 1 mutants: 1 killed, 0 no tests "
                                                                 "(reported, never failed); passed")

    def test_a2_a_ghost_meta_outside_the_roots_does_not_make_an_empty_sweep_pass(self) -> None:
        done = self.run_wrapper("apps/service", meta={"src/pkg/types.py": {}, "tests/ghost.py": {"g.x_f__mutmut_1": 1}})
        self.assertEqual(done.returncode, 1)
        self.assertEqual(lines_of(done)[-1], "mutation: mutmut found nothing to mutate in apps/service; a pass on "
                                             "nothing is not a pass")

    def test_a2_a_file_handed_over_that_the_table_does_not_take_is_not_run_on_a_copied_meta(self) -> None:
        done = self.run_wrapper("apps/service", "--file", "tests/test_a.py", meta={"tests/test_a.py": {KEY: None}},
                                results={"tests/test_a.py": {KEY: 0}})
        self.assertEqual(done.returncode, 0)
        self.assertEqual(self.started_mutmut(), [])


SELECTION = '["tests", "--ignore=tests/integration"]'
CLI_ARGS = '["-p", "no:xdist"]'
FRAGMENT = Path(__file__).resolve().parent.parent / "changelog.d" / "mutmut-mutation.md"


def narrowed(selection: str | None = SELECTION, cli_args: str | None = CLI_ARGS, extra: str = "") -> str:
    lines = ["[tool.mutmut]", 'source_paths = ["src"]']
    if selection is not None:
        lines.append(f"pytest_add_cli_args_test_selection = {selection}")
    if cli_args is not None:
        lines.append(f"pytest_add_cli_args = {cli_args}")
    return "\n".join(lines) + "\n" + extra


def narrowing(setting: str, found: str, held: str) -> str:
    return (f"mutation: apps/service/pyproject.toml {setting} is {found}, not {held}, which narrows what the tests "
            "reach without anyone looking at it")


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


class ShadowedPackageTest(PhaseCase):
    """T039 (A4): the mutmut and libcst the run imports are the environment's, not a copy found first on `PYTHONPATH`."""

    def test_a4_a_package_found_ahead_of_the_environments_exits_2_naming_where_it_was_found(self) -> None:
        for name in ("mutmut", "libcst"):
            with self.subTest(package=name):
                done = self.run_with("apps/service", extra={"FAKE_SHADOW": f"{name} /elsewhere/{name}"},
                                     meta={"src/pkg/a.py": {KEY: None}}, results={"src/pkg/a.py": {KEY: 1}})
                self.assertEqual(done.returncode, 2)
                self.assertEqual(lines_of(done), [
                    f"mutation: {name} is imported from /elsewhere/{name}, not from apps/service's environment; a "
                    "package on PYTHONPATH ahead of the environment's is refused: remove it from PYTHONPATH"])
                self.assertEqual(self.started_mutmut(), [])

    def test_a4_hold_the_probe_asks_where_the_packages_are_imported_from(self) -> None:
        """HOLD (teeth: drop the location check from the probe and see it fail)."""
        module = loaded(SCRIPT)
        for needle in ("find_spec", "locate_file", "'mutmut'", "'libcst'"):
            self.assertIn(needle, module.VERSION_CODE)


if __name__ == "__main__":
    unittest.main()
