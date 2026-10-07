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
)
HELPERS: tuple[str, ...] = ("gate_rules", "render_fixture")  # the helper files this slice declares


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


class TestAMovedHelperIsOneObjectByBothPaths(unittest.TestCase):
    def test_the_gate_readers_are_the_same_objects_from_gate_rules_and_from_test_verify_stamp_pinned(self) -> None:
        for name in ("gate_target_name", "gate_prerequisites", "gate_rule"):
            with self.subTest(name=name):
                self.assertIs(getattr(gate_rules, name), getattr(test_verify_stamp_pinned, name))


if __name__ == "__main__":
    unittest.main()
