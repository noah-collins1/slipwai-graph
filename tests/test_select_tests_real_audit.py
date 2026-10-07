"""A reads-only declared module opens only what it declares (S38 T038, D164, AC-S38-8, AC-S38-16).

Each declared module that generates nothing runs under an audit hook (`sys.addaudithook`: `open` events and the files
a `subprocess.Popen` is handed). Every path it opens in the repository outside `src/` (under `tests/`: outside the
imports it ran, so a fixture) must be named by its `reads` or be one a run-everything row claims; a path that is
neither is a read the selector does not know about, and a change to it would skip the module (adversary B3, T055).
The declarations are read from the real tree, so a later edit that adds a by-path load to a declared module fails
here. The teeth are a copy of `test_pit_globs` with the gaps pass's `self.module.load("verify-stamp.py")` added.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from slipwai.assets import ROOT

sys.dont_write_bytecode = True

SCRATCH = Path("/tmp/s38impl")
SELECTED = "SELECTED_TEST_MODULES"  # what a selected run hands down (D187 rule 4)
LISTING = """
import json, sys
sys.dont_write_bytecode = True
sys.path.insert(0, 'scripts')
from pathlib import Path
from select_tests import declarations
root = Path('.').resolve()
tree = declarations.scan(root)
print(json.dumps({name: sorted(source.declaration.reads) for name, source in sorted(tree.sources.items())
                  if declarations.is_module(name) and source.declaration is not None
                  and not tree.effective(name)[0] is None and not tree.effective(name)[0].generates}))
"""
# runs one module under the hook, then (the hook no longer recording) says which opened paths nothing accounts for
AUDIT = """
import json, os, shlex, sys, unittest
sys.dont_write_bytecode = True
root, module, reads = os.path.realpath('.'), sys.argv[1], json.loads(sys.argv[2])
opened, recording = set(), [True]


def hook(event, args):
    if not recording[0]:
        return
    if event in ("open", "os.listdir", "os.scandir") and isinstance(args[0], (str, bytes, os.PathLike)):
        opened.add((event, os.path.realpath(os.fsdecode(args[0]))))
    elif event == "subprocess.Popen":
        # what a child process is handed to run or read: an argument that names a file is read by the module
        argv = args[1] if isinstance(args[1], (list, tuple)) else shlex.split(str(args[1]))
        for argument in argv:
            if isinstance(argument, (str, bytes, os.PathLike)):
                try:
                    named = os.path.realpath(os.path.join(args[2] or ".", os.fsdecode(argument)))
                    if os.path.isfile(named):
                        opened.add(("open", named))
                except (ValueError, OSError):
                    pass


sys.addaudithook(hook)
with open(os.devnull, "w", encoding="utf-8") as sink:
    result = unittest.TextTestRunner(stream=sink, verbosity=0).run(unittest.defaultTestLoader.loadTestsFromName(module))
recording[0] = False
sys.path.insert(0, 'scripts')
from pathlib import Path
import ast
from select_tests import choose, declarations, loaded, rules
catalog = rules.load_catalog(Path(root))
# a module that imports `slipwai` runs what the generator reads on import (T037): those paths are accounted for
origin = Path(sys.modules[module].__file__)
imports = declarations.imported_names(ast.parse(origin.read_text(encoding="utf-8"))) or frozenset()
reads = reads + (sorted(loaded.scan(Path(root))) if "slipwai" in imports else [])
# an open relative to a directory descriptor (`shutil.rmtree`) reports a bare name, so an `open` of a path that no
# longer exists, or of a directory, is not a read of the repository; a directory is read by listing it
# a file under `tests/` is read when it is opened and is no module the run imported: a fixture, a data file
closure = {os.path.realpath(m.__file__) for m in list(sys.modules.values()) if getattr(m, "__file__", None)}
seen = sorted({os.path.relpath(path, root) for event, path in opened if path.startswith(root + os.sep)
               and os.path.exists(path) and (event != "open" or not os.path.isdir(path))})
def counts(path: str) -> bool:
    top = path.split(os.sep)[0]
    return top not in ("src", "tests", ".git") or (top == "tests" and os.path.join(root, path) not in closure)


outside = [path for path in seen if "__pycache__" not in path and not path.endswith((".pyc", ".pyo")) and counts(path)]
uncovered = [path for path in outside if not any(choose.reads_match(path, entry) for entry in reads)
             and not (rules.claim(path, catalog) or rules.Claim("", False)).full]
print(json.dumps({"ok": result.wasSuccessful(), "ran": result.testsRun, "opened": outside, "uncovered": uncovered}))
"""


def audited(module: str, reads: list[str], tests: Path | None = None) -> dict[str, Any]:
    """Run `module` under the hook, from `tests` (the real test tree unless given) with `src` beside it."""
    path = os.pathsep.join([str(ROOT / "src"), str(tests or ROOT / "tests")])
    done = subprocess.run(["python3", "-B", "-c", AUDIT, module, json.dumps(reads)], cwd=ROOT, text=True,
                          capture_output=True, timeout=500, env={**os.environ, "PYTHONPATH": path})
    assert done.returncode == 0, done.stderr
    found: dict[str, Any] = json.loads(done.stdout.splitlines()[-1])
    return found


def reads_only() -> dict[str, list[str]]:
    done = subprocess.run(["python3", "-B", "-c", LISTING], cwd=ROOT, text=True, capture_output=True, timeout=180)
    assert done.returncode == 0, done.stderr
    found: dict[str, list[str]] = json.loads(done.stdout)
    return found


def to_audit(declared: dict[str, list[str]], environ: Mapping[str, str]) -> dict[str, list[str]]:
    """The declared modules this run audits: those in `SELECTED_TEST_MODULES`, or every one where it is absent or
    names no module (a broken handoff falls back to the full audit)."""
    chosen = {name for name in environ.get(SELECTED, "").split(",") if name.strip()}
    return {name: reads for name, reads in declared.items() if name in chosen} if chosen else declared


class TestEveryReadsOnlyModuleOpensWhatItDeclares(unittest.TestCase):
    declared: dict[str, list[str]]

    @classmethod
    def setUpClass(cls) -> None:
        cls.declared = reads_only()

    def test_the_declared_set_is_the_one_the_loaders_test_holds(self) -> None:
        self.assertGreaterEqual(len(self.declared), 8)
        self.assertIn("test_pit_globs", self.declared)  # the listing is whole; the audit below narrows it

    def test_no_module_opens_a_path_outside_src_and_tests_that_nothing_accounts_for(self) -> None:
        for module, reads in to_audit(self.declared, os.environ).items():
            with self.subTest(module):
                found = audited(module, reads)
                self.assertTrue(found["ok"] and found["ran"] > 0, f"{module} did not run clean under the hook: {found}")
                self.assertEqual(found["uncovered"], [], f"{module} opens what its reads do not name")


class TestTheAuditHasTeeth(unittest.TestCase):
    """The gaps pass's reproduction: `test_pit_globs` with `self.module.load("verify-stamp.py")` added."""

    def scratch(self, extra: str) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        SCRATCH.mkdir(exist_ok=True)
        directory = tempfile.TemporaryDirectory(dir=SCRATCH)
        source = (ROOT / "tests/test_pit_globs.py").read_text(encoding="utf-8")
        marker = "self.module = loaded()\n"
        self.assertIn(marker, source)
        (Path(directory.name) / "test_pit_globs.py").write_text(
            source.replace(marker, marker + extra), encoding="utf-8")
        return directory, Path(directory.name)

    def test_an_undeclared_load_of_a_sibling_script_is_named(self) -> None:
        directory, tests = self.scratch('        self.module.load("verify-stamp.py")\n')
        with directory:
            found = audited("test_pit_globs", ["assets/toolkit/scripts/mutation-scope.py"], tests)
        self.assertTrue(found["ok"], found)
        self.assertEqual(found["uncovered"], ["assets/toolkit/scripts/verify-stamp.py"])

    def test_the_unchanged_copy_opens_nothing_it_does_not_declare(self) -> None:
        directory, tests = self.scratch("")
        with directory:
            found = audited("test_pit_globs", ["assets/toolkit/scripts/mutation-scope.py"], tests)
        self.assertTrue(found["ok"], found)
        self.assertEqual(found["uncovered"], [])
        self.assertIn("assets/toolkit/scripts/mutation-scope.py", found["opened"])


class TestTheAuditSeesFixturesAndSubprocesses(unittest.TestCase):
    """Adversary B3: a fixture read through `__file__` and a script a child process runs are reads too."""

    def run_module(self, body: str) -> dict[str, Any]:
        SCRATCH.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=SCRATCH) as directory:
            (Path(directory) / "test_probe.py").write_text(
                "import subprocess, sys, unittest\nfrom pathlib import Path\nfrom slipwai.assets import ROOT\n\n\n"
                "class T(unittest.TestCase):\n    def test_it(self) -> None:\n" + body, encoding="utf-8")
            return audited("test_probe", [], Path(directory))

    def test_a_fixture_under_tests_outside_the_imports_is_named(self) -> None:
        found = self.run_module('        (ROOT / "tests/fixtures/adopt/go-module/go.mod").read_text()\n')
        self.assertTrue(found["ok"], found)
        self.assertIn("tests/fixtures/adopt/go-module/go.mod", found["uncovered"])

    def test_a_script_a_subprocess_runs_is_named(self) -> None:
        found = self.run_module(
            '        subprocess.run([sys.executable, str(ROOT / "scripts/publish-to-gitea.py"), "--help"],'
            " capture_output=True)\n")
        self.assertTrue(found["ok"], found)
        self.assertIn("scripts/publish-to-gitea.py", found["uncovered"])


if __name__ == "__main__":
    unittest.main()
