"""A change to the go app narrows (S38 T044, AC-S38-8, -9, -16; demo 1's defect 1).

Importing `slipwai` reads three asset files (`prune.py`, `check-styles.py`, `install-tools.py`) and nothing under
`assets/languages/`: those are read when a project is generated, and a module that generates says which configuration
it generates. So a change under a backend's own assets reaches the modules that generate that backend, and not the
ones that merely import the generator. Read over the real tree by the selector's own `choose`, with no git involved.
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from typing import Any

from slipwai.assets import ROOT

sys.dont_write_bytecode = True

# No TEST_SELECTION, on purpose: the child probe below scans the whole real tree with `declarations.scan` and
# `choose.select`, so this module depends on every declared module's `reads` targets existing and on git's tracked
# set -- neither could be a `reads` entry. Declared, it was skipped on a tree where a path some declaration reads was
# deleted, while running it failed (S43 gaps report LOW 4). Undeclared, it always runs.

HEALTH = "assets/languages/go/app/health/health.go"
PROBE = """
import json, sys
sys.dont_write_bytecode = True
sys.path.insert(0, 'scripts')
from pathlib import Path
from select_tests import choose, declarations, rules
root = Path('.').resolve()
catalog = rules.load_catalog(root)
tree = declarations.scan(root, catalog)
chosen = choose.select(tree, [sys.argv[1]], catalog)
out = {"backends": list(chosen.backends), "narrowed": [v.module for v in chosen.narrowed()], "verdicts": {}, "go": []}
for v in chosen.verdicts:
    out["verdicts"][v.module] = {"runs": v.runs, "reasons": [r.text for r in v.reasons], "skip": v.skip}
    declaration = tree.effective(v.module)[0]
    if declaration is not None and "slipwai" in tree.imported[v.module] and declaration.admits("backend", "go"):
        out["go"].append(v.module)
print(json.dumps(out))
"""


def probe(path: str) -> dict[str, Any]:
    done = subprocess.run(["python3", "-B", "-c", PROBE, path], cwd=ROOT, text=True, capture_output=True, timeout=180)
    assert done.returncode == 0, done.stderr
    found: dict[str, Any] = json.loads(done.stdout)
    return found


class TestAGoAppChangeNarrows(unittest.TestCase):
    found: dict[str, Any]

    @classmethod
    def setUpClass(cls) -> None:
        cls.found = probe(HEALTH)

    def test_the_matrix_narrows_to_go_and_the_module_that_adds_a_service_still_runs(self) -> None:
        self.assertEqual(self.found["backends"], ["go"])
        self.assertIn("test_matrix", self.found["narrowed"])
        self.assertTrue(self.found["verdicts"]["test_add_service"]["runs"])

    def test_a_declared_module_that_only_imports_the_generator_is_skipped_with_its_reason(self) -> None:
        for module in ("test_gitea_pages", "test_migration_script", "test_pit_globs", "test_release", "test_versions"):
            verdict = self.found["verdicts"][module]
            self.assertFalse(verdict["runs"], f"{module}: {verdict['reasons']}")
            self.assertEqual(verdict["skip"], "reads no go configuration and none of the changed files", module)

    def test_every_module_importing_slipwai_that_admits_go_still_runs(self) -> None:  # AC-S38-16
        self.assertIn("test_matrix", self.found["go"])
        for module in self.found["go"]:
            self.assertTrue(self.found["verdicts"][module]["runs"], f"{module} is skipped on a go change")

    def test_a_module_that_reads_the_go_app_by_path_is_still_selected(self) -> None:
        self.assertTrue(probe("assets/languages/go/scripts/go-mutation.py")["verdicts"]["test_go_mutation_file"]["runs"])


class TestTheWordsOfASkip(unittest.TestCase):
    """T045: a module skipped on a change that reaches every configuration reads no configuration *and* none of the
    changed files, which is the whole of why it is skipped; one skipped on a go change reads no go configuration and,
    since it reads files of its own, none of the changed files either (T047)."""

    def test_a_toolkit_script_skips_the_modules_that_load_neither_it_nor_a_configuration(self) -> None:
        found = probe("assets/toolkit/scripts/verify-stamp.py")["verdicts"]["test_gitea_pages"]
        self.assertFalse(found["runs"])
        self.assertEqual(found["skip"], "reads no configuration and none of the changed files")

    def test_a_go_app_change_names_the_configuration_and_the_files(self) -> None:
        found = probe(HEALTH)["verdicts"]["test_gitea_pages"]["skip"]
        self.assertEqual(found, "reads no go configuration and none of the changed files")


if __name__ == "__main__":
    unittest.main()
