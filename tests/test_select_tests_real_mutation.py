"""The three real-toolchain mutation modules stay undeclared, and a reading says why (S38 T014, AC-S38-8).

Each runs one backend's real toolchain, but each imports `test_mutation_borders`, which imports
`test_parallel_gate_adopted` and through it the adopt, layout, migrate and replay modules, and `parallel_gate`: none
declares anything. A module whose import closure holds an undeclared helper is undeclared, so a `TEST_SELECTION`
here would be void, and the selector would run the module whatever the change. Read over the real tree by the
selector's own scan, with `choose` fed paths directly, so no git is involved. When those helpers are declared, this
test is the place a declaration for the three becomes a decision.
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest

from slipwai.assets import ROOT

sys.dont_write_bytecode = True

MODULES = ("test_mutation_scope_real_go", "test_mutation_scope_real_spring", "test_mutation_stamp_untouched")
PATHS = {"go": "assets/languages/go/Makefile", "java-spring": "assets/languages/java-spring/pom.xml",
         "typescript": "assets/languages/typescript/package.json"}
PROBE = """
import json, sys
sys.dont_write_bytecode = True
sys.path.insert(0, 'scripts')
from pathlib import Path
from select_tests import choose, declarations
root = Path('.').resolve()
catalog = json.loads((root / 'catalog.json').read_text(encoding='utf-8'))
tree = declarations.scan(root, catalog)
paths = json.loads(sys.argv[1])
modules = sys.argv[2:]
out = {"own": {m: tree.sources[m].declaration is not None for m in modules},
       "why": {m: tree.effective(m)[1] for m in modules},
       "closure": {m: sorted(tree.closures[m]) for m in modules},
       "ran": {}}
for name, path in paths.items():
    out["ran"][name] = {v.module: v.runs for v in choose.choose(tree, [path], catalog) if v.module in modules}
print(json.dumps(out))
"""


class TestTheMutationModulesStayUndeclared(unittest.TestCase):
    found: dict[str, dict[str, object]]

    @classmethod
    def setUpClass(cls) -> None:
        done = subprocess.run(["python3", "-B", "-c", PROBE, json.dumps(PATHS), *MODULES], cwd=ROOT, text=True,
                              capture_output=True, timeout=180)
        assert done.returncode == 0, done.stderr
        cls.found = json.loads(done.stdout)

    def test_none_of_the_three_carries_a_declaration_of_its_own(self) -> None:
        self.assertEqual(self.found["own"], dict.fromkeys(MODULES, False))

    def test_each_is_undeclared_because_a_helper_in_its_closure_declares_nothing(self) -> None:
        for name in MODULES:
            why = self.found["why"][name]
            assert isinstance(why, str)
            self.assertTrue(why, name)
            closure = self.found["closure"][name]
            assert isinstance(closure, list)
            self.assertIn("test_mutation_borders", closure)
            self.assertIn("parallel_gate", closure)

    def test_a_go_a_spring_and_a_typescript_path_each_run_all_three(self) -> None:
        for backend in PATHS:
            self.assertEqual(self.found["ran"][backend], dict.fromkeys(MODULES, True), backend)


if __name__ == "__main__":
    unittest.main()
