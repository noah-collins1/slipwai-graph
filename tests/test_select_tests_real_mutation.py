"""Two real-toolchain mutation modules stay undeclared, and a reading says why; the third is declared (S38 T014, S43).

`test_mutation_scope_real_go` and `test_mutation_stamp_untouched` run one backend's real toolchain, but each imports
`test_mutation_borders`, which imports
`test_parallel_gate_adopted` and through it the adopt, layout, migrate and replay modules, and `parallel_gate`: none
declares anything. A module whose import closure holds an undeclared helper is undeclared, so a `TEST_SELECTION`
here would be void, and the selector would run the module whatever the change. Read over the real tree by the
selector's own scan, with `choose` fed paths directly, so no git is involved. When those helpers are declared, this
test is the place a declaration for them becomes a decision. S43 T008 made it for `test_mutation_scope_real_spring`:
`clean_environment` moved to the declared `mutation_env` and `git` to `stamp_names`, so its closure no longer holds
`test_mutation_borders`; it declares the java-spring configuration it generates, a spring path runs it narrowed to
java-spring, and a go or typescript path skips it.
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from typing import Any

from slipwai.assets import ROOT

sys.dont_write_bytecode = True

MODULES = ("test_mutation_scope_real_go", "test_mutation_stamp_untouched")
DECLARED = "test_mutation_scope_real_spring"
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
       "effective": {m: tree.effective(m)[0] is not None for m in modules},
       "narrowed": {},
       "why": {m: tree.effective(m)[1] for m in modules},
       "closure": {m: sorted(tree.closures[m]) for m in modules},
       "ran": {}}
for name, path in paths.items():
    selection = choose.select(tree, [path], catalog)
    out["ran"][name] = {v.module: v.runs for v in selection.verdicts if v.module in modules}
    out["narrowed"][name] = [v.module for v in selection.narrowed() if v.module in modules], list(selection.backends)
print(json.dumps(out))
"""


class ReadOnce(unittest.TestCase):
    """The selector's reading of the real tree, made once per class."""

    found: dict[str, Any]

    @classmethod
    def setUpClass(cls) -> None:
        done = subprocess.run(["python3", "-B", "-c", PROBE, json.dumps(PATHS), *MODULES, DECLARED], cwd=ROOT,
                              text=True, capture_output=True, timeout=180)
        assert done.returncode == 0, done.stderr
        cls.found = json.loads(done.stdout)


class TestTheMutationModulesStayUndeclared(ReadOnce):

    def test_none_of_the_three_carries_a_declaration_of_its_own(self) -> None:
        self.assertEqual({m: self.found["own"][m] for m in MODULES}, dict.fromkeys(MODULES, False))

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
            self.assertEqual({m: self.found["ran"][backend][m] for m in MODULES}, dict.fromkeys(MODULES, True), backend)


class TestTheSpringModuleIsDeclaredAndNarrows(ReadOnce):
    """S43 T008's decision: declared, held by nothing, and a spring change runs it narrowed to java-spring alone."""

    def test_it_carries_a_declaration_that_holds(self) -> None:
        self.assertTrue(self.found["own"][DECLARED])
        self.assertTrue(self.found["effective"][DECLARED], self.found["why"][DECLARED])
        self.assertNotIn("test_mutation_borders", self.found["closure"][DECLARED])

    def test_a_spring_path_runs_it_narrowed_to_spring_and_go_or_typescript_skip_it(self) -> None:
        self.assertTrue(self.found["ran"]["java-spring"][DECLARED])
        self.assertEqual(self.found["narrowed"]["java-spring"], [[DECLARED], ["java-spring"]])
        self.assertFalse(self.found["ran"]["go"][DECLARED])
        self.assertFalse(self.found["ran"]["typescript"][DECLARED])


if __name__ == "__main__":
    unittest.main()
