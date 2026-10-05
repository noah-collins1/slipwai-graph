"""No test leaves an interpreter cache under `assets/`, and the toolkit holds none (S33 T021).

The product itself may: `slipwai.assets` loads the pruner with bytecode writing on, so
`assets/backing-services/__pycache__/` is the gate's own doing, and the verify stamp's key lists it (D119).

Iteration 16's first converge pass over S33 loaded `assets/toolkit/scripts/verify-stamp.py` with `importlib` to read
its key, with bytecode writing on. That left `assets/toolkit/scripts/__pycache__/verify-stamp.cpython-314.pyc`, and
`test_toolkit`, which reads every file of the toolkit as text, died on it with a UnicodeDecodeError that read like a
broken asset. `asset_files` keeps a cache out of every generated project, so no user met it; the factory's gate did.
A test that loads a script from an asset tree turns `sys.dont_write_bytecode` on around the load, and a probe typed
by hand runs as `python3 -B`.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

from slipwai.assets import TOOLKIT_ROOT

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


def leaves_bytecode(source: str) -> bool:
    """True where a test module loads a script, names an asset tree in its code, and never turns bytecode off.

    Held module by module, not call by call: a loader's path usually arrives through a variable, so a module that
    reaches into `assets/` at all and loads anything turns the switch on, which costs nothing where it was not needed.
    """
    return bool(LOADER.search(source)) and bool(ASSET_TREE.search(source)) and not SWITCHED_OFF.search(source)


class AssetsBytecodeTest(unittest.TestCase):
    def test_the_toolkit_tree_holds_no_interpreter_cache(self) -> None:
        cached = sorted(
            path.relative_to(TOOLKIT_ROOT.parent.parent).as_posix()
            for path in TOOLKIT_ROOT.rglob("*")
            if path.name == "__pycache__" or path.suffix in {".pyc", ".pyo"}
        )
        self.assertEqual(
            cached, [],
            "an interpreter cache under the toolkit, which test_toolkit reads as text: something imported a script "
            "there with bytecode writing on (a test turns sys.dont_write_bytecode on; a probe runs as python3 -B); "
            "find what, then delete it",
        )

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
