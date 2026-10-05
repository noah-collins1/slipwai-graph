"""No test leaves an interpreter cache under `assets/`, and nothing under `assets/` holds one (S33 T021, T028).

No one writes one, the product included: the verify stamp's key lists the paths of caches under `assets/` (D119), so
a pass recorded from a tree without one is never reused once a run writes one. `slipwai.assets` therefore loads the
pruner, as it loads the style checker, with bytecode writing off (D121).

Iteration 16's first converge pass over S33 loaded `assets/toolkit/scripts/verify-stamp.py` with `importlib` to read
its key, with bytecode writing on. That left `assets/toolkit/scripts/__pycache__/verify-stamp.cpython-314.pyc`, and
`test_toolkit`, which reads every file of the toolkit as text, died on it with a UnicodeDecodeError that read like a
broken asset. `asset_files` keeps a cache out of every generated project, so no user met it; the factory's gate did.
A test that loads a script from an asset tree turns `sys.dont_write_bytecode` on around the load, and a probe typed
by hand runs as `python3 -B`.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from slipwai.assets import BACKING_SERVICE_ROOT

ASSETS = BACKING_SERVICE_ROOT.parent
REPO = ASSETS.parent
TESTS = Path(__file__).resolve().parent
LOADER = re.compile(r"spec_from_file_location\(|run_path\(|SourceFileLoader\(")
ASSET_TREE = re.compile(r"\b(?:TOOLKIT|PROFILE|FRONTEND|LANGUAGE|BACKING_SERVICE|ADOPTION)_ROOT\b|[\"']assets/")
SWITCHED_OFF = re.compile(r"dont_write_bytecode\b[^\n]*\bTrue\b|PYTHONDONTWRITEBYTECODE|python3 -B\b")

# The probe iteration 16 ran, as it typed it.
THE_PROBE = (
    "import importlib.util\n"
    "s=importlib.util.spec_from_file_location('vs','assets/toolkit/scripts/verify-stamp.py');"
    "m=importlib.util.module_from_spec(s);s.loader.exec_module(m)\n"
)


def caches() -> list[str]:
    """Every interpreter cache under `assets/`, as a path from the repository root."""
    return sorted(
        path.relative_to(REPO).as_posix()
        for path in ASSETS.rglob("*")
        if path.name == "__pycache__" or path.suffix in {".pyc", ".pyo"}
    )


def leaves_bytecode(source: str) -> bool:
    """True where a test module loads a script, names an asset tree in its code, and never turns bytecode off.

    Held module by module, not call by call: a loader's path usually arrives through a variable, so a module that
    reaches into `assets/` at all and loads anything turns the switch on, which costs nothing where it was not needed.
    """
    return bool(LOADER.search(source)) and bool(ASSET_TREE.search(source)) and not SWITCHED_OFF.search(source)


class AssetsBytecodeTest(unittest.TestCase):
    def test_nothing_under_assets_holds_an_interpreter_cache(self) -> None:
        cached = caches()
        self.assertEqual(
            cached, [],
            "an interpreter cache under assets/, which test_toolkit reads as text and the verify stamp keys by path: "
            "something imported a script there with bytecode writing on (turn sys.dont_write_bytecode on around the "
            "load; run a probe as python3 -B); find what, then delete it",
        )

    def test_importing_slipwai_assets_in_a_fresh_interpreter_writes_no_cache(self) -> None:
        # The fresh interpreter writes whatever bytecode it would write under a prefix of its own, so the tree is
        # neither touched nor cleared: a cache for a file under assets/ appearing there is one it would have left.
        with tempfile.TemporaryDirectory() as prefix:
            env = {key: value for key, value in os.environ.items() if key != "PYTHONDONTWRITEBYTECODE"}
            env.update(PYTHONPATH=str(REPO / "src"), PYTHONPYCACHEPREFIX=prefix)
            subprocess.run([sys.executable, "-c", "import slipwai.assets"], env=env, check=True, cwd=REPO)
            mirrored = Path(prefix + str(ASSETS))
            written = sorted(path.relative_to(mirrored).as_posix() for path in mirrored.rglob("*.pyc"))
            source = sorted(path.relative_to(Path(prefix + str(REPO))).as_posix()
                            for path in Path(prefix + str(REPO / "src")).rglob("*.pyc"))
        self.assertNotEqual(source, [], "the probe wrote no bytecode at all, so it shows nothing")
        self.assertEqual(written, [], "importing slipwai.assets compiles a script under assets/ with bytecode on")

    def test_every_test_that_loads_a_script_from_an_asset_tree_turns_bytecode_off(self) -> None:
        modules = sorted(path for path in TESTS.glob("*.py") if path.name != Path(__file__).name)
        writing = [path.name for path in modules if leaves_bytecode(path.read_text(encoding="utf-8"))]
        self.assertEqual(writing, [], "loads a script from assets/ with bytecode writing on")

    def test_the_scan_names_the_probe_that_left_the_cache_and_passes_it_switched_off(self) -> None:
        self.assertTrue(leaves_bytecode(THE_PROBE))
        self.assertFalse(leaves_bytecode("import sys\nsys.dont_write_bytecode = True\n" + THE_PROBE))
        self.assertFalse(leaves_bytecode(
            "written, sys.dont_write_bytecode = sys.dont_write_bytecode, True\n" + THE_PROBE
        ))
        self.assertFalse(leaves_bytecode(THE_PROBE.replace("assets/toolkit/", "/tmp/project/")))
        self.assertFalse(leaves_bytecode('"""Imported from the project rather than from `assets/`."""\n'
                                         + THE_PROBE.replace("assets/toolkit/", "/tmp/project/")))


if __name__ == "__main__":
    unittest.main()
