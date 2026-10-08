"""S42 T012 (rule 11 · AC-S42-1, -2, -4, -5 end to end): the one real mutmut run — heavy, S43's list.

The minimal starter (`--profile standard --http none --event-store memory`, so no transport and no store and nothing red
on day one) on a slice branch with files changed, run through the project's own `make mutation` and `make
mutation-full`, with the real `uv sync --locked` and the real mutmut 3.8.0 (libcst 1.9.0, pytest 9.1.1). It is the one
place the fake `uv` of `test_mutmut_verdict` and the recording runner of `test_mutation_scope_python` are checked
against the tool: the generation snippet, the `.meta` files and the exit-code table are mutmut's, read here.

Gated as `tests/test_mutation_scope_real_typescript.py` is, by `backends_under_test()` and the tool on `PATH`
(here `uv`, and the network the first `uv sync` needs), and only where `FACTORY_BACKENDS` is set: a run of the whole
matrix on a laptop does not start a sweep nobody asked for. Skipped, not failed, without it.
"""
from __future__ import annotations

import importlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from stamp_fixture import git, key_of
from support import FactoryTestCase, backends_under_test, commit_all
from test_mutation_borders import clean_environment

from slipwai.assets import ROOT

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "assets" / "toolkit" / "scripts"))
SERVICE = "apps/service"
PACKAGE = "real"
SRC = f"{SERVICE}/src/{PACKAGE}"
ARITH = f"{SRC}/arith.py"
SHAPES = f"{SRC}/shapes.py"
INIT = f"{SRC}/__init__.py"
ARITH_TEST = f"{SERVICE}/tests/test_arith.py"
META = f"{SERVICE}/mutants/src/{PACKAGE}"
ARITH_SOURCE = "def double(n: int) -> int:\n    return n * 2\n"
# A file that declares types only: nothing in it for mutmut to mutate.
SHAPES_SOURCE = "from dataclasses import dataclass\n\n\n@dataclass(frozen=True)\nclass Point:\n    x: int\n    y: int\n"
KILLING = ("from real.arith import double\n\n\ndef test_double_doubles() -> None:\n    assert double(3) == 6\n"
           "    assert double(0) == 0\n    assert double(-2) == -4\n")
WEAK = "from real.arith import double\n\n\ndef test_double_is_positive() -> None:\n    assert double(3) > 0\n"
FIRST_LINE = r"^mutation: scoped to 1 changed file\(s\) since `main` at [0-9a-f]+: "


def enabled() -> bool:
    chosen = bool(os.environ.get("FACTORY_BACKENDS")) and "python" in backends_under_test()
    return chosen and shutil.which("uv") is not None


class RealPythonTest(FactoryTestCase):
    repo: Path
    key: str
    scoped: int

    @classmethod
    def setUpClass(cls) -> None:
        if not enabled():
            raise unittest.SkipTest("heavy: the Python slice of the matrix (FACTORY_BACKENDS), uv and a network")
        parent = Path(tempfile.mkdtemp(prefix="real-py-", dir="/tmp"))
        cls.addClassCleanup(shutil.rmtree, parent, ignore_errors=True)
        cls.repo = cls().generate(parent, PACKAGE, "standard", "python", "none", http="none", event_store="memory")
        for name, text in ((ARITH, ARITH_SOURCE), (SHAPES, SHAPES_SOURCE), (ARITH_TEST, KILLING)):
            (cls.repo / name).write_text(text, encoding="utf-8")
        commit_all(cls.repo, "a tested module, and one that declares types only")
        git(cls.repo, "checkout", "-q", "-b", "slice/S1")
        cls.scoped = 0

    def make(self, target: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["make", target], cwd=self.repo, env=clean_environment(), text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=900)

    def keys(self, relative: str) -> dict[str, int | None]:
        """What mutmut's `.meta` file for a source file holds: each mutant's exit code, `None` where it was not run."""
        meta = self.repo / SERVICE / "mutants" / (relative + ".meta")
        return dict(json.loads(meta.read_text(encoding="utf-8"))["exit_code_by_key"])

    def touch(self, relative: str) -> None:
        with (self.repo / relative).open("a", encoding="utf-8") as handle:
            handle.write("# touched\n")

    def test_e1_a_changed_module_with_a_killing_test_is_scoped_to_that_module_and_passes(self) -> None:
        self.touch(ARITH)
        done = self.make("mutation")
        self.assertEqual(done.returncode, 0, done.stdout[-4000:])
        lines = [line for line in done.stdout.splitlines() if line.startswith("mutation: ")]
        self.assertRegex(lines[0], FIRST_LINE + re.escape(ARITH) + "$")
        self.assertEqual(lines[-1], "mutation: 1 scoped, 0 swept, 0 skipped, 0 refused; passed")
        run = self.keys(f"src/{PACKAGE}/arith.py")
        self.assertEqual(len(run), 2)
        self.assertEqual({code for code in run.values()}, {1}, "mutmut's own code for a killed mutant")
        self.assertEqual({code for code in self.keys(f"src/{PACKAGE}/__init__.py").values()}, {None})
        self.assertEqual(self.keys(f"src/{PACKAGE}/shapes.py"), {})
        type(self).scoped = len(run)
        git(self.repo, "checkout", "-q", "--", ARITH)
        type(self).key = key_of(self.repo)  # the stamp's key with a scoped run's `mutants/` in a clean tree

    def test_e2_a_weakened_test_fails_naming_the_survivor_and_the_previous_mutants_are_replaced(self) -> None:
        marker = self.repo / SERVICE / "mutants" / "left-by-an-earlier-run"
        marker.write_text("stale", encoding="utf-8")
        (self.repo / ARITH_TEST).write_text(WEAK, encoding="utf-8")
        self.touch(ARITH)
        try:
            done = self.make("mutation")
        finally:
            git(self.repo, "checkout", "-q", "--", ARITH_TEST, ARITH)
        self.assertNotEqual(done.returncode, 0, done.stdout[-4000:])
        self.assertRegex(done.stdout, rf"mutation: survived {SERVICE} {PACKAGE}\.arith\.x_double__mutmut_\d+ "
                                      rf"\(mutmut show {PACKAGE}\.arith\.x_double__mutmut_\d+ in {SERVICE}; "
                                      rf"report {SERVICE}/mutants/\)")
        self.assertFalse(marker.exists(), "the previous `mutants/` was not replaced")
        survivors = [code for code in self.keys(f"src/{PACKAGE}/arith.py").values() if code == 0]
        self.assertEqual(len(survivors), 2, "mutmut's own code for a survivor is 0, and the verdict is the wrapper's")

    def test_e3_a_types_only_module_has_no_mutant_to_run_and_an_init_mutates_its_functions_only(self) -> None:
        self.touch(SHAPES)
        done = self.make("mutation")
        self.assertEqual(done.returncode, 0, done.stdout[-4000:])
        self.assertIn(f"mutation: no mutant to run — src/{PACKAGE}/shapes.py: mutmut found no function to mutate in it",
                      done.stdout)
        self.assertNotIn("mutmut exited", done.stdout, "a `mutmut run` was started for a file with no mutant")
        self.assertEqual(self.keys(f"src/{PACKAGE}/shapes.py"), {})
        git(self.repo, "checkout", "-q", "--", SHAPES)
        self.touch(INIT)
        done = self.make("mutation")
        self.assertEqual(done.returncode, 0, done.stdout[-4000:])
        run = self.keys(f"src/{PACKAGE}/__init__.py")
        self.assertTrue(run and all(name.startswith(f"{PACKAGE}.x_health__mutmut_") for name in run), run)
        self.assertEqual({code for code in run.values()}, {1})
        self.assertEqual({code for code in self.keys(f"src/{PACKAGE}/arith.py").values()}, {None})
        git(self.repo, "checkout", "-q", "--", INIT)

    def test_e4_the_sweep_mutates_the_table_s_list_and_nothing_it_excludes(self) -> None:
        done = self.make("mutation-full")
        self.assertEqual(done.returncode, 0, done.stdout[-4000:])
        sources = sorted(path.relative_to(self.repo / SERVICE) for path in (self.repo / SERVICE / "src").rglob("*.py")
                         if "__pycache__" not in path.parts)
        self.assertEqual(len(sources), 3)
        total = 0
        for path in sources:
            run = self.keys(path.as_posix())
            total += len(run)
            self.assertNotIn(None, run.values(), f"{path}: a mutant mutmut never ran")
        self.assertGreater(total, self.scoped, "the sweep is not larger than the scoped run")
        self.assertRegex(done.stdout, rf"mutation: {total} mutants: {total} killed, 0 no tests "
                                      rf"\(reported, never failed\); passed — report {SERVICE}/mutants/")

    def test_e5_afterwards_git_is_clean_the_scoped_gate_is_not_broadened_and_the_import_check_passes(self) -> None:
        self.assertEqual(git(self.repo, "status", "--short").strip(), "")
        self.assertEqual(key_of(self.repo), type(self).key, "a run moved what the stamp compares, so the scoped gate")
        rules = importlib.import_module("verify_scoped.rules")
        self.assertIsNone(rules.text_problem(str(self.repo / "Makefile"),
                                             str(self.repo / "scripts/verify_scoped/rules.json"), {}))
        done = subprocess.run(["python3", "scripts/check-imports.py"], cwd=self.repo, text=True, capture_output=True,
                              timeout=120)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)


if __name__ == "__main__":
    unittest.main()
