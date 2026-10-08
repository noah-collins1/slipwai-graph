"""Modules that generate nothing and load a script by path say what they load (S38 T015, AC-S38-8, AC-S38-16).

Read over the real tree by the selector's own scan, with `choose` fed paths directly, so no git is involved. A
declaration is a completeness claim; the claims below are what a reading of each module proves, and the modules that
stay undeclared are held undeclared, so a later declaration is a decision. The last class is AC-S38-16's subject: a
fault in a toolkit script a declared module loads selects that module, and one no declared module loads does not.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from typing import Any

from slipwai.assets import ROOT

sys.dont_write_bytecode = True

SCRIPTS = "assets/toolkit/scripts/"
GO = "assets/languages/go/"
TS_WRAPPER = "assets/languages/typescript/scripts/stryker-mutation.py"
PY_WRAPPER = "assets/languages/python/scripts/mutmut-mutation.py"
STYLES = SCRIPTS + "check-styles.py"  # read by the `slipwai` import these modules reach through `test_stryker_list`
# module -> every path its reading proves it opens, copies, runs or loads by path (a directory is everything under it)
READS = {
    "test_assets_bytecode": ["assets", "tests"],
    "test_gitea_pages": ["scripts/gitea-pages.py", "scripts/install-gitea-pages"],
    "test_go_mutation_file": [GO + "scripts/go-mutation.py"],
    "test_migration_script": ["scripts/test-migration.py"],
    "test_mutmut_config": [PY_WRAPPER],
    "test_mutmut_lines": [PY_WRAPPER, STYLES, "tests"],
    "test_mutmut_services": [PY_WRAPPER, STYLES],
    "test_mutmut_setup": [PY_WRAPPER],
    "test_mutmut_silenced": [PY_WRAPPER, STYLES],
    "test_mutmut_verdict": [PY_WRAPPER],
    "test_mutation": [GO + "app/.gremlins.yaml", GO + "scripts/go-coverage.py", GO + "scripts/go-mutation.py"],
    "test_pit_globs": [SCRIPTS + "mutation-scope.py"],
    "test_stryker_closure": [TS_WRAPPER, STYLES],
    "test_stryker_edges": [TS_WRAPPER, STYLES],
    "test_stryker_ignored": [TS_WRAPPER, STYLES],
    "test_stryker_incomplete": [TS_WRAPPER, STYLES],
    "test_stryker_install": [TS_WRAPPER, STYLES],
    "test_stryker_list": [TS_WRAPPER],
    "test_stryker_report": [TS_WRAPPER, "assets/backing-services/typescript/read-models.ts"],
    "test_stryker_reuse": [TS_WRAPPER, STYLES],
    "test_stryker_run_lock": [TS_WRAPPER, STYLES],
    "test_stryker_statements": [TS_WRAPPER, STYLES],
    "test_stryker_verdict": [TS_WRAPPER, STYLES],
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
                self.assertEqual(reasons[0], f"reads `{entry}`", f"{name} {entry}")

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


ASSET_ALIAS = re.compile(r'^(\w+_ROOT) = ROOT / "assets/([\w-]+)"', re.M)
CHAIN = re.compile(r'(?:\b(\w+_ROOT)|\bROOT / "assets"|\bROOT)((?:\s*/\s*"[^"{}]+")+)(?!\s*/)')
LITERAL = re.compile(r'"(assets/(?:languages|backing-services|frontends|profiles|targets|toolkit|adoption)/[\w./-]+)"')
IMPORTERS = """
import json, sys
sys.dont_write_bytecode = True
sys.path.insert(0, 'scripts')
from pathlib import Path
from select_tests import choose, declarations, rules
root = Path('.').resolve()
catalog = json.loads((root / 'catalog.json').read_text(encoding='utf-8'))
tree = declarations.scan(root, catalog)
out = {"importers": sorted(m for m in tree.sources if declarations.is_module(m) and "slipwai" in tree.imported[m]
                           and tree.effective(m)[0] is not None),
       "paths": {}}
for path in json.loads(sys.argv[1]):
    claim = rules.claim(path, catalog)
    ran = {v.module: [r.text for r in v.reasons] for v in choose.select(tree, [path], catalog).verdicts if v.runs}
    generated = bool(claim and not claim.full and not claim.every and claim.configs)  # read when a project is generated
    owed = [m for m in out["importers"] if not generated
            or any(tree.effective(m)[0].admits(axis, option) for axis, option in claim.configs)]
    out["paths"][path] = {"full": bool(claim and claim.full), "ran": ran, "owed": owed}
print(json.dumps(out))
"""


def asset_paths_the_generator_reads() -> list[str]:
    """Every asset path `src/slipwai/` names, found by reading the source as text: the `<TREE>_ROOT / "..."` chains of
    `assets.py`'s roots, `ROOT / "assets/..."` and the literal `"assets/..."` strings. A directory is probed through
    a file in it."""
    found: set[str] = set()
    roots = dict(ASSET_ALIAS.findall((ROOT / "src/slipwai/assets.py").read_text(encoding="utf-8")))
    for file in sorted((ROOT / "src/slipwai").rglob("*.py")):
        text = file.read_text(encoding="utf-8")
        for alias, parts in CHAIN.findall(text):
            if alias and alias not in roots:
                continue  # a root another file composes from these: its own definition is a chain read here too
            head = f"assets/{roots[alias]}" if alias else ""
            rest = "/".join(part.strip().strip('"') for part in re.findall(r'"[^"]+"', parts))
            path = f"{head}/{rest}" if head else rest
            if path.startswith("assets/") and path.count("/") > 1:
                found.add(path)
        found.update(LITERAL.findall(text))
    return sorted(path if "." in path.rsplit("/", 1)[-1] else path.rstrip("/") + "/x" for path in found)


class TestWhatTheGeneratorReadsReachesEveryModuleThatImportsIt(unittest.TestCase):
    """AC-S38-10, AC-S38-16: a module that imports `slipwai` runs the generator's import-time and in-process reads, so a
    fault in any asset path `src/slipwai/` names selects it, or the run is whole."""

    def test_a_change_to_each_asset_path_the_generator_names_selects_every_module_importing_slipwai(self) -> None:
        paths = asset_paths_the_generator_reads()
        self.assertIn(SCRIPTS + "check-styles.py", paths)
        self.assertIn(SCRIPTS + "agents/registry.json", paths)
        self.assertGreater(len(paths), 25)
        done = subprocess.run(["python3", "-B", "-c", IMPORTERS, json.dumps(paths)], cwd=ROOT, text=True,
                              capture_output=True, timeout=180)
        self.assertEqual(done.returncode, 0, done.stderr)
        found = json.loads(done.stdout)
        self.assertGreater(len(found["importers"]), 5)
        # a path read only when a project is generated reaches the importers that generate it (T044): the rest import
        # `slipwai` and read none of it, which `test_select_tests_go_app` and the audit hold
        missed = {path: sorted(set(row["owed"]) - set(row["ran"])) for path, row in found["paths"].items()
                  if not row["full"] and set(row["owed"]) - set(row["ran"])}
        self.assertEqual(missed, {})

    def test_the_reason_says_what_the_module_imports_and_the_asset_it_reads(self) -> None:
        done = subprocess.run(["python3", "-B", "-c", IMPORTERS, json.dumps([SCRIPTS + "check-styles.py"])],
                              cwd=ROOT, text=True, capture_output=True, timeout=180)
        self.assertEqual(done.returncode, 0, done.stderr)
        found = json.loads(done.stdout)
        ran = found["paths"][SCRIPTS + "check-styles.py"]["ran"]
        self.assertTrue(found["importers"])
        for module in found["importers"]:
            self.assertIn(f"imports `slipwai`, which reads `{SCRIPTS}check-styles.py`", ran[module], module)


if __name__ == "__main__":
    unittest.main()
