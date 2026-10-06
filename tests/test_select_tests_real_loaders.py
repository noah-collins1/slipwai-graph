"""Modules that generate nothing and load a script by path say what they load (S38 T015, AC-S38-8, AC-S38-16).

Read over the real tree by the selector's own scan, with `choose` fed paths directly, so no git is involved. A
declaration is a completeness claim; the claims below are what a reading of each module proves, and the modules that
stay undeclared are held undeclared, so a later declaration is a decision. The last class is AC-S38-16's subject: a
fault in a toolkit script a declared module loads selects that module, and one no declared module loads does not.
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from typing import Any

from slipwai.assets import ROOT

sys.dont_write_bytecode = True

SCRIPTS = "assets/toolkit/scripts/"
GO = "assets/languages/go/"
# module -> every path its reading proves it opens, copies, runs or loads by path (a directory is everything under it)
READS = {
    "test_assets_bytecode": ["assets", "tests"],
    "test_gitea_pages": ["scripts/gitea-pages.py", "scripts/install-gitea-pages"],
    "test_go_mutation_file": [GO + "scripts/go-mutation.py"],
    "test_migration_script": ["scripts/test-migration.py"],
    "test_mutation": [GO + "app/.gremlins.yaml", GO + "scripts/go-coverage.py", GO + "scripts/go-mutation.py"],
    "test_pit_globs": [SCRIPTS + "mutation-scope.py"],
    "test_release": [".github/workflows/release.yml", "scripts/gitea-askpass", "scripts/tag-release.py"],
    "test_versions": ["scripts/publish-wheel.py", "scripts/snapshot-version.py", "src/slipwai/versions.py"],
}
# the modules the reading leaves undeclared: each generates a project, or imports a test module that does
UNDECLARED = (
    "test_aws_flags", "test_aws_forge", "test_deploy_role", "test_runner_controls", "test_design_stage",
    "test_cruise_start", "test_health_said", "test_runner_stream", "test_skill_capabilities", "test_slice_scope_root",
    "test_runner_between_park", "test_shared_packages", "test_mutation_borders", "test_mutation_targets",
    "test_verify_scoped_baseline", "test_verify_scoped_borders", "test_verify_scoped_ignored", "test_ux_gates_scale",
    "test_codegraph_bytes",
)
# a directory entry is probed through one file inside it
INSIDE = {"assets": SCRIPTS + "check-styles.py", "tests": "tests/support.py"}
PROBE = """
import json, sys
sys.dont_write_bytecode = True
sys.path.insert(0, 'scripts')
from pathlib import Path
from select_tests import choose, declarations
root = Path('.').resolve()
catalog = json.loads((root / 'catalog.json').read_text(encoding='utf-8'))
tree = declarations.scan(root, catalog)
modules = json.loads(sys.argv[1])
out = {"held": declarations.held(root), "own": {}, "effective": {}, "ran": {}}
for name in modules:
    own = tree.sources[name].declaration
    out["own"][name] = None if own is None else {
        "generates": own.generates, "axes": {a: sorted(o) for a, o in own.axes.items()}, "reads": sorted(own.reads)}
    out["effective"][name] = tree.effective(name)[1]
for path in json.loads(sys.argv[2]):
    found = {}
    for verdict in choose.select(tree, [path], catalog).verdicts:
        if verdict.module in json.loads(sys.argv[3]) and verdict.runs:
            found[verdict.module] = [reason.text for reason in verdict.reasons]
    out["ran"][path] = found
print(json.dumps(out))
"""


def probe(paths: list[str]) -> dict[str, Any]:
    done = subprocess.run(["python3", "-B", "-c", PROBE, json.dumps([*READS, *UNDECLARED]), json.dumps(paths),
                           json.dumps(list(READS))],
                          cwd=ROOT, text=True, capture_output=True, timeout=180)
    assert done.returncode == 0, done.stderr
    found: dict[str, Any] = json.loads(done.stdout)
    return found


def through(entry: str) -> str:
    return INSIDE.get(entry, entry)


class TestWhatTheLoadersDeclare(unittest.TestCase):
    found: dict[str, Any]

    @classmethod
    def setUpClass(cls) -> None:
        paths = ["README.md", SCRIPTS + "verify-stamp.py", SCRIPTS + "mutation-scope.py", GO + "scripts/go-mutation.py"]
        cls.found = probe(sorted({through(entry) for reads in READS.values() for entry in reads} | set(paths)))

    def test_each_declared_module_generates_nothing_and_reads_exactly_what_it_loads(self) -> None:
        for name, reads in READS.items():
            self.assertEqual(self.found["own"][name], {"generates": False, "axes": {}, "reads": sorted(reads)}, name)
            self.assertEqual(self.found["effective"][name], "", name)

    def test_every_path_read_exists_and_no_declaration_among_them_is_void(self) -> None:
        for reads in READS.values():
            for entry in reads:
                self.assertTrue((ROOT / entry).exists(), entry)
        mine = [line for line in self.found["held"] if any(f"tests/{name}.py" in line for name in READS)]
        self.assertEqual(mine, [])

    def test_a_change_to_each_path_a_module_reads_selects_it(self) -> None:
        for name, reads in READS.items():
            for entry in reads:
                reasons = self.found["ran"][through(entry)].get(name)
                self.assertIsNotNone(reasons, f"{name} is skipped when {entry} changes")
                self.assertEqual(reasons, [f"reads `{entry}`"], f"{name} {entry}")

    def test_a_change_none_of_them_reads_skips_the_modules_that_read_files_only(self) -> None:
        # README.md is read by none of the eight; the bytecode scan reads `assets` and `tests`, which it is not under
        self.assertEqual(self.found["ran"]["README.md"], {})

    def test_the_modules_that_generate_a_project_or_load_what_cannot_be_listed_stay_undeclared(self) -> None:
        for name in UNDECLARED:
            self.assertIsNone(self.found["own"][name], name)


class TestAToolkitScriptFaultStillReachesItsLoaders(unittest.TestCase):
    """AC-S38-16: of the declared modules, only those that load a toolkit script by path are selected by its change."""

    found: dict[str, Any]

    @classmethod
    def setUpClass(cls) -> None:
        cls.found = probe([SCRIPTS + "mutation-scope.py", SCRIPTS + "verify-stamp.py", GO + "scripts/go-mutation.py"])

    def test_the_mutation_scope_script_selects_the_module_that_loads_it_and_the_bytecode_scan(self) -> None:
        self.assertEqual(sorted(self.found["ran"][SCRIPTS + "mutation-scope.py"]),
                         ["test_assets_bytecode", "test_pit_globs"])

    def test_a_toolkit_script_no_declared_module_loads_selects_only_the_bytecode_scan(self) -> None:
        self.assertEqual(sorted(self.found["ran"][SCRIPTS + "verify-stamp.py"]), ["test_assets_bytecode"])

    def test_the_go_mutation_script_selects_the_two_modules_that_load_it(self) -> None:
        self.assertEqual(sorted(self.found["ran"][GO + "scripts/go-mutation.py"]),
                         ["test_assets_bytecode", "test_go_mutation_file", "test_mutation"])


if __name__ == "__main__":
    unittest.main()
