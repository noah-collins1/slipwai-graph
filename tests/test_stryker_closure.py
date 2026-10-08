"""S41 T044 (B4 · D222, D215 b): a move in the instrumenter's dependency closure is a move of the lock comparison.

`@stryker-mutator/instrumenter` resolves `@babel/*` (which parses the source) and `weapon-regex` (which makes the regex
mutants) through ranges, so either can move in the lock while every `@stryker-mutator/*` version stands, and which
mutants exist changes with it. `versions(lock_text=…)` therefore also holds every entry the instrumenter resolves,
transitively, as npm resolves it (the package's own `node_modules`, then each parent's), keyed by lock path.
"""
from __future__ import annotations

import json
import sys

from test_stryker_list import Case

sys.dont_write_bytecode = True
TEST_SELECTION = {"reads": ["assets/languages/typescript/scripts/stryker-mutation.py",
                            "assets/toolkit/scripts/check-styles.py"]}
INSTRUMENTER = "node_modules/@stryker-mutator/instrumenter"


def lock(**moved: str) -> str:
    """A lock in which the instrumenter needs `@babel/core` and `weapon-regex`, `@babel/core` needs `@babel/parser`
    (hoisted) and a nested `semver`, and nothing else is the instrumenter's; `moved` overrides a path's version."""
    entries: dict[str, dict] = {
        "": {"name": "x"},
        INSTRUMENTER: {"version": "10.0.0", "dependencies": {"@babel/core": "^7.0.0", "weapon-regex": "~1.0.0"}},
        "node_modules/@babel/core": {"version": "7.1.0", "optionalDependencies": {"fsevents": "*"},
                                     "dependencies": {"@babel/parser": "^7.1.0", "semver": "^6.0.0"}},
        "node_modules/@babel/parser": {"version": "7.1.0"},
        "node_modules/@babel/core/node_modules/semver": {"version": "6.3.1"},
        "node_modules/semver": {"version": "7.0.0"},
        "node_modules/weapon-regex": {"version": "1.0.0"},
        "node_modules/vitest": {"version": "4.1.11"},
    }
    for path, version in moved.items():
        entries[path.replace("__", "/")] = {**entries.get(path.replace("__", "/"), {}), "version": version}
    return json.dumps({"packages": entries})


class ClosureTest(Case):
    def test_e1_every_entry_the_instrumenter_resolves_is_in_the_map_keyed_by_lock_path(self) -> None:
        self.assertEqual(self.module.versions(lock_text=lock()), {
            INSTRUMENTER: "10.0.0", "node_modules/@babel/core": "7.1.0", "node_modules/@babel/parser": "7.1.0",
            "node_modules/@babel/core/node_modules/semver": "6.3.1", "node_modules/weapon-regex": "1.0.0"})

    def test_e2_a_move_of_the_parser_alone_changes_the_map_and_so_does_a_move_of_the_regex_mutator(self) -> None:
        before = self.module.versions(lock_text=lock())
        for path in ("node_modules__@babel__parser", "node_modules__weapon-regex",
                     "node_modules__@babel__core__node_modules__semver"):
            with self.subTest(path=path):
                self.assertNotEqual(self.module.versions(lock_text=lock(**{path: "9.9.9"})), before)

    def test_e3_a_move_outside_the_closure_changes_nothing(self) -> None:
        before = self.module.versions(lock_text=lock())
        moved = lock(node_modules__vitest="5.0.0", node_modules__semver="8.0.0")
        self.assertEqual(self.module.versions(lock_text=moved), before)

    def test_e4_a_dependency_the_lock_does_not_hold_is_not_an_error_and_a_cycle_ends(self) -> None:
        document = json.loads(lock())
        document["packages"]["node_modules/@babel/parser"]["dependencies"] = {"@babel/core": "*", "absent": "*"}
        found = self.module.versions(lock_text=json.dumps(document))
        self.assertEqual(found["node_modules/@babel/parser"], "7.1.0")
        self.assertNotIn("node_modules/absent", found)
