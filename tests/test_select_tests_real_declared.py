"""The modules and helpers that carry `TEST_SELECTION` are the ones the `real_*` tests hold (S38 T030, AC-S38-8).

A declaration is a completeness claim and only the tests named below read the code behind it. A new `TEST_SELECTION`
anywhere else would be held for existence alone, so adding one must edit a selector test, which is itself full and
reviewed. The set is the union of the lists those tests already carry; nothing is re-listed here but the helpers they
leave undeclared on purpose.
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest

from test_select_tests_real_backends import DECLARED as BACKEND_MODULES
from test_select_tests_real_helpers import HELPERS
from test_select_tests_real_loaders import READS as LOADER_MODULES

from slipwai.assets import ROOT

sys.dont_write_bytecode = True

# `test_select_tests_real_helpers` holds these undeclared (they import a test module, sit at the size budget, or load a
# script by `importlib`, which D164 rule 4 holds a generating declaration to naming)
LEFT_UNDECLARED = ("scoped_fixture", "mutation_scope_fixture", "parallel_gate", "stamp_fixture")
PROBE = """
import ast, json, sys
sys.path.insert(0, 'scripts')
from pathlib import Path
from select_tests import declarations
root = Path('.').resolve()
tree = declarations.scan(root)
carrying = [name for name in sorted(tree.sources)
            if declarations.assignments(ast.parse((root / 'tests' / (name + '.py')).read_text(encoding='utf-8')))]
print(json.dumps(carrying))
"""


class TestTheDeclaredSetIsPinned(unittest.TestCase):
    def test_what_carries_a_declaration_is_what_the_real_tests_hold(self) -> None:
        done = subprocess.run(["python3", "-B", "-c", PROBE], cwd=ROOT, text=True, capture_output=True, timeout=180)
        self.assertEqual(done.returncode, 0, done.stderr)
        held = {*BACKEND_MODULES, *LOADER_MODULES, *(name for name in HELPERS if name not in LEFT_UNDECLARED)}
        self.assertEqual(sorted(json.loads(done.stdout)), sorted(held),
                         "a new TEST_SELECTION needs a real_* test that reads the code behind it")


if __name__ == "__main__":
    unittest.main()
