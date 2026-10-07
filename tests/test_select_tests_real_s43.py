"""S43's own `real_*` list: the modules and helpers it declares are held and reached (AC-S43-2, AC-S43-3).

`DECLARED` and `HELPERS` start empty and each declaring task appends its names. Over the real tree: the selector's
`held()` names none of them and each carries a `TEST_SELECTION`; and for every (axis, option) a declaration names, one
real path that pair claims is the change set, and every module whose closure's `generation.facts` generate that option,
or whose declared `reads` match the path, is selected. The expectation is derived from the facts, never typed.
`pairs`, `path_claiming` and `unselected` are what a later task's list runs through; with the lists empty the checks are
vacuous by design, so one test runs them over a module already declared in `test_select_tests_real_backends`.
"""
from __future__ import annotations

import subprocess
import sys
import unittest
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import gate_rules
import mutation_env
import stamp_case
import stamp_fixture
import stamp_names
import test_mutation_borders
import test_verify_stamp_pinned
from test_select_tests_real_backends import DECLARED as BACKEND_MODULES

from slipwai.assets import ROOT

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "scripts"))

from select_tests import choose, declarations, rules  # noqa: E402

DECLARED: tuple[str, ...] = (  # the test modules this slice declares
    "test_codegraph_memory", "test_health_memory", "test_health_memory_states", "test_codegraph_races",
    "test_health_narrowed", "test_codegraph_narrowed", "test_cruise_runner", "test_cruise_index",
    "test_code_index_health",
    "test_render_browser", "test_render_current", "test_render_failures", "test_render_files",
    "test_render_files_report", "test_render_links", "test_render_once", "test_render_pinned",
    "test_factory_gate_stamp", "test_verify_stamp_key", "test_verify_stamp_working", "test_verify_stamp_reuse",
    "test_verify_stamp_stored", "test_verify_stamp_two_runs",
    "test_mutation_scope_real_spring",
    "test_select_tests_make", "test_select_tests_paths", "test_select_tests_makefile", "test_gate_walks_pom",
    "test_gate_walks", "test_drawio_canvas", "test_design_extensions", "test_parallel_slices", "test_event_model",
    # S26's, declared after S26 merged (D188 item 2)
    "test_decisions_scope", "test_decisions_scope_edges", "test_decisions_scope_spelling", "test_decisions_scope_calls",
    "test_decisions_scope_gate", "test_hand_backs_record", "test_reversibility_gate", "test_reversibility_versions",
    "test_reversibility_labels", "test_reversibility_list", "test_reversibility_paths", "test_reversibility_score",
    "test_reversibility_written", "test_measures_fenced_tier",
)
# the helper files this slice declares
HELPERS: tuple[str, ...] = ("gate_rules", "render_fixture", "stamp_names", "stamp_case", "mutation_env",
           "select_fixture", "select_fixture_declare", "hand_backs_fixture", "reversibility_fixture")


def pairs(tree: declarations.Tree, names: Iterable[str]) -> set[tuple[str, str]]:
    """The `(axis, option)` pairs the effective declarations of these files name: an axis left unnamed names none."""
    found: set[tuple[str, str]] = set()
    for name in names:
        declaration, _ = tree.effective(name)
        if declaration is not None and declaration.generates and not declaration.every:
            found.update((axis, option) for axis, options in declaration.axes.items() for option in options)
    return found


def assets(root: Path) -> list[str]:
    done = subprocess.run(["git", "ls-files", "assets"], cwd=root, text=True, capture_output=True, timeout=60,
                          check=True)
    return sorted(done.stdout.splitlines())


def path_claiming(files: Iterable[str], catalog: Any, pair: tuple[str, str]) -> str | None:
    """The first real file whose own asset claim names the pair, or None where no asset path reaches it."""
    for path in files:
        found = rules.own_asset_claim(path, catalog)
        if found is not None and pair in found.configs:
            return path
    return None


def generates(tree: declarations.Tree, module: str, pair: tuple[str, str]) -> bool:
    """Whether the facts of the module's closure generate the option: a call that names it, or computes the axis."""
    axis, option = pair
    for member in {module, *tree.closures[module]}:
        facts = tree.sources[member].facts
        if facts.routes:
            return True
        for call in facts.calls:
            if axis in call.axes and (call.axes[axis] is None or option in (call.axes[axis] or ())):
                return True
    return False


def reads_path(tree: declarations.Tree, module: str, path: str) -> bool:
    declaration, _ = tree.effective(module)
    return declaration is not None and any(choose.reads_match(path, entry) for entry in declaration.reads)


def unselected(tree: declarations.Tree, catalog: Any, path: str, pair: tuple[str, str]) -> list[str]:
    """The modules the facts say `path` reaches that `choose.select` leaves out; empty is the claim holding."""
    ran = {v.module for v in choose.select(tree, [path], catalog).verdicts if v.runs}
    return sorted(name for name in tree.sources if declarations.is_module(name) and name not in ran
                  and (generates(tree, name, pair) or reads_path(tree, name, path)))


class TestTheDeclarationsOfThisSliceAreHeldAndReached(unittest.TestCase):
    tree: declarations.Tree
    catalog: Any
    files: list[str]

    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = rules.load_catalog(ROOT)
        cls.tree = declarations.scan(ROOT, cls.catalog)
        cls.files = assets(ROOT)

    def test_held_names_none_of_them_and_each_carries_a_declaration(self) -> None:
        held = declarations.held(ROOT)
        for name in (*DECLARED, *HELPERS):
            with self.subTest(file=name):
                self.assertEqual([line for line in held if f"tests/{name}.py" in line], [])
                self.assertIsNotNone(self.tree.sources[name].declaration, f"tests/{name}.py has no TEST_SELECTION")

    def test_a_path_each_named_pair_claims_selects_what_generates_it_or_reads_it(self) -> None:
        for axis, option in sorted(pairs(self.tree, (*DECLARED, *HELPERS))):
            path = path_claiming(self.files, self.catalog, (axis, option))
            if path is None:
                continue
            with self.subTest(pair=f"{axis}={option}", path=path):
                self.assertEqual(unselected(self.tree, self.catalog, path, (axis, option)), [])

    def test_the_derivation_runs_over_a_module_declared_before_this_slice(self) -> None:
        named = pairs(self.tree, ("test_matrix", "test_postgres"))
        reachable = {pair: path for pair in sorted(named) if (path := path_claiming(self.files, self.catalog, pair))}
        self.assertIn(("backend", "go"), reachable)
        for pair, path in reachable.items():
            with self.subTest(pair=pair, path=path):
                self.assertEqual(unselected(self.tree, self.catalog, path, pair), [])
        # the modules the facts derive for the go pair are not an empty list, or the check above holds nothing
        go = reachable[("backend", "go")]
        self.assertIn("test_matrix", {v.module for v in choose.select(self.tree, [go], self.catalog).verdicts
                                      if v.runs})
        self.assertTrue(set(BACKEND_MODULES) >= {"test_matrix", "test_postgres"})


# A reads-only module's `reads` is the whole of what it depends on. A child probe run with `cwd=ROOT` that scans the
# real tree depends on every declared module's `reads` targets existing and on git's tracked set: neither is a `reads`
# entry, so a deleted path some declaration reads skips the module while running it fails (S43 gaps report, LOW 4).
# Such a module stays undeclared and always runs.
SCANS_THE_REAL_TREE: tuple[str, ...] = ("test_select_tests_go_app", "test_select_tests_declarations")
TREE_PROBES = ("declarations.scan(", "choose.select(", "declarations.held(", "HELD")


S26_MODULES: tuple[str, ...] = DECLARED[DECLARED.index("test_decisions_scope"):]  # declared after S26 merged (D188)


class TestS26ModulesAreReadsOnlyAndSkippedOnAGoChange(unittest.TestCase):
    catalog: Any
    tree: declarations.Tree
    go: str

    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = rules.load_catalog(ROOT)
        cls.tree = declarations.scan(ROOT, cls.catalog)
        cls.go = next(path for path in assets(ROOT) if path.startswith("assets/languages/go/"))

    def test_each_is_declared_reads_only(self) -> None:
        for name in S26_MODULES:
            with self.subTest(module=name):
                declaration, why = self.tree.effective(name)
                self.assertIsNotNone(declaration, why)
                self.assertFalse(declaration is not None and declaration.generates)

    def test_a_go_asset_change_skips_every_one_of_them(self) -> None:
        ran = {v.module for v in choose.select(self.tree, [self.go], self.catalog).verdicts if v.runs}
        self.assertEqual(sorted(set(S26_MODULES) & ran), [])

    def test_a_change_to_a_path_a_module_reads_runs_it(self) -> None:
        for name in S26_MODULES:
            reads = self.tree.sources[name].declaration.reads  # type: ignore[union-attr]
            with self.subTest(module=name):
                # a file, as a change set names one: a read that is a directory is entered to its first file
                path = next(str(found.relative_to(ROOT)) for entry in sorted(reads) if (ROOT / entry).exists()
                            for found in ([ROOT / entry] if (ROOT / entry).is_file()
                                          else sorted(p for p in (ROOT / entry).rglob("*") if p.is_file())[:1]))
                chosen = choose.select(self.tree, [path], self.catalog)
                self.assertIn(name, {v.module for v in chosen.verdicts if v.runs})


class TestAModuleThatScansTheRealTreeIsNotDeclared(unittest.TestCase):
    tree: declarations.Tree

    @classmethod
    def setUpClass(cls) -> None:
        cls.tree = declarations.scan(ROOT, rules.load_catalog(ROOT))

    def test_the_two_probes_of_the_real_tree_stay_undeclared(self) -> None:
        for name in SCANS_THE_REAL_TREE:
            with self.subTest(module=name):
                self.assertIsNone(self.tree.sources[name].declaration, f"tests/{name}.py scans the real tree")

    def test_no_declared_reads_only_module_runs_the_selector_over_the_real_tree(self) -> None:
        found = []
        for name, source in sorted(self.tree.sources.items()):
            if not declarations.is_module(name) or source.declaration is None or source.declaration.generates:
                continue
            text = (ROOT / "tests" / f"{name}.py").read_text(encoding="utf-8")
            if "cwd=ROOT" in text and any(probe in text for probe in TREE_PROBES):
                found.append(name)
        self.assertEqual(found, [], "a reads-only module whose probe scans the real tree cannot state its reads")


class TestAMovedHelperIsOneObjectByBothPaths(unittest.TestCase):
    def test_clean_environment_is_the_same_object_from_mutation_env_and_from_test_mutation_borders(self) -> None:
        self.assertIs(mutation_env.clean_environment, test_mutation_borders.clean_environment)

    def test_the_gate_readers_are_the_same_objects_from_gate_rules_and_from_test_verify_stamp_pinned(self) -> None:
        for name in ("gate_target_name", "gate_prerequisites", "gate_rule"):
            with self.subTest(name=name):
                self.assertIs(getattr(gate_rules, name), getattr(test_verify_stamp_pinned, name))

    def test_the_stamp_names_and_cases_are_the_same_objects_from_stamp_fixture_and_from_their_new_homes(self) -> None:
        for name in ("CI_MARKERS", "MAKE_STATE", "GIT_STATE", "CLOSING", "REUSE_PREFIX", "BRANCH", "SERVICE",
                     "PYVENV_CFG", "INSTANT", "git", "commit_all", "exclude", "probe_path", "write_stand_ins",
                     "write_spaced_make", "checks_started"):
            with self.subTest(name=name):
                self.assertIs(getattr(stamp_names, name), getattr(stamp_fixture, name))
        for name in ("template",):
            with self.subTest(name=name):
                self.assertIs(getattr(stamp_case, name), getattr(stamp_fixture, name))
        # the one case the fixture adds to: it keeps `plant_stamp`, which loads the project's script with importlib
        self.assertTrue(issubclass(stamp_fixture.StampTestCase, stamp_case.StampTestCase))
        self.assertFalse(hasattr(stamp_case.StampTestCase, "plant_stamp"))
        self.assertTrue(hasattr(stamp_fixture.StampTestCase, "plant_stamp"))


if __name__ == "__main__":
    unittest.main()
