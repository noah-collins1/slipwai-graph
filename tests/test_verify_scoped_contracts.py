"""R4 (AC-S06-3, -4), the contracts: a change selects its consumers as well as its readers.

A change under a service runs the type check and the tests of every browser app whose `api` names it; one under an npm
package runs those of every npm-family deployable; one under a service that produces an event runs those of every
service that reads it, the model read at the base and in the working tree. And `choose` itself: a deployable that builds
in one directory runs its three units together.
"""
from __future__ import annotations

import importlib
import sys
import unittest
from typing import Any

from scoped_fixture import EVENTS, ShapeCase
from stamp_fixture import commit_all, git

from slipwai.assets import ROOT

sys.dont_write_bytecode = True

MODEL = "docs/event-model/model.yaml"
EDGE = ("slices:\n  - id: Bill\n    service: billing\n    frames:\n      - {type: evt, name: Billed}\n"
        "  - id: Ship\n    service: service\n    reads: [Billed]\n")


class OpenapiAndPackagesTest(ShapeCase):
    def test_e2_a_change_under_the_service_runs_its_openapi_and_the_apps_that_consume_it(self) -> None:
        self.edit("apps/service/src/main.ts")
        ran, skipped = self.decided(self.scoped())
        for gate in ("lint", "typecheck", "test"):
            self.assertEqual(ran[f"{gate}-service"], "apps/service/src/main.ts changed")
        self.assertEqual(ran["check-openapi"], "apps/service/src/main.ts changed")
        for unit in ("typecheck-web", "test-web"):
            self.assertEqual(ran[unit], "consumes openapi:service (apps/service/src/main.ts)")
        self.assertEqual(skipped["lint-web"], "none of its inputs changed")

    def test_e2_a_committed_openapi_document_counts_as_a_change_under_the_service(self) -> None:
        self.edit("apps/service/openapi.json", "\n")
        ran, _ = self.decided(self.scoped())
        self.assertEqual(ran["typecheck-web"], "consumes openapi:service (apps/service/openapi.json)")

    def test_e3_a_change_under_an_npm_package_runs_every_npm_deployables_typecheck_and_test(self) -> None:
        self.edit("packages/api-client/src/index.ts")
        ran, skipped = self.decided(self.scoped())
        for name in ("service", "web"):
            for gate in ("typecheck", "test"):
                self.assertEqual(ran[f"{gate}-{name}"],
                                 "consumes package:api-client (packages/api-client/src/index.ts)")
            self.assertIn(f"lint-{name}", skipped)


class EventsTest(ShapeCase):
    shape = EVENTS

    def decided_for_billing(self) -> tuple[dict[str, str], dict[str, str]]:
        self.edit("apps/billing/src/billing/extra.py", "x = 1\n")
        return self.decided(self.scoped({"STANDIN_DRY": "1"}))

    def test_e6_an_edge_only_the_working_trees_model_has_counts(self) -> None:
        self.edit(MODEL, EDGE)
        ran, _ = self.decided_for_billing()
        reason = "consumes event:Billed (apps/billing/src/billing/extra.py)"
        self.assertEqual((ran["typecheck-service"], ran["test-service"]), (reason, reason))

    def test_e6_an_edge_the_base_had_counts_though_the_working_tree_lost_it(self) -> None:
        git(self.repo, "checkout", "-q", "main")
        (self.repo / MODEL).write_text(EDGE, encoding="utf-8")
        commit_all(self.repo, "an edge")
        git(self.repo, "checkout", "-q", "-B", "slice/S1", "main")
        (self.repo / MODEL).unlink()
        ran, _ = self.decided_for_billing()
        self.assertEqual(ran["test-service"], "consumes event:Billed (apps/billing/src/billing/extra.py)")

    def test_e6_with_no_edge_the_reader_runs_only_where_a_recipe_is_shared(self) -> None:
        ran, _ = self.decided_for_billing()
        self.assertEqual(ran["test-service"], "shares one recipe with test-billing")


def choose_module() -> Any:
    sys.path.insert(0, str(ROOT / "assets" / "toolkit" / "scripts"))
    return importlib.import_module("verify_scoped.choose")


class BuildDirectoryTest(unittest.TestCase):
    """A Go or Java deployable's three units run together: a change that chooses one of them (a consumed event reaches a
    type check and tests, never a lint) takes the others along. The function is pure; its record is written here."""

    def record(self, family: str) -> dict[str, Any]:
        def unit(gate: str, name: str) -> dict[str, Any]:
            files = [f"apps/{name}/"] if gate == "lint" else []
            return {"gate": gate, "components": [name], "inputs": {"files": files, "tools": [], "variables": []},
                    "claims": True, "always": None, "targets": [f"{gate}-{name}"]}

        checks = {f"{gate}-{name}": unit(gate, name) for name in ("orders", "billing")
                  for gate in ("lint", "typecheck", "test")}
        deployables = {name: {"kind": "service", "path": f"apps/{name}", "family": family}
                       for name in ("orders", "billing")}
        contract = {"id": "event:Billed", "kind": "event", "event": "Billed", "owner": "billing",
                    "paths": ["apps/billing/"], "consumers": ["orders"]}
        return {"deployables": deployables, "checks": checks, "contracts": [contract], "obligations": []}

    def test_e4_a_go_or_java_deployables_three_units_share_a_build_directory(self) -> None:
        module = choose_module()
        data = importlib.import_module("verify_scoped.record").Database({}, {}, {})
        for family in ("go", "java"):
            with self.subTest(family=family):
                found = {item.unit: item for item in module.choose(self.record(family), data, ["apps/billing/x.go"])}
                self.assertEqual(found["typecheck-orders"].reason, "consumes event:Billed (apps/billing/x.go)")
                self.assertEqual(found["lint-orders"].reason, "shares a build directory with typecheck-orders")
                self.assertTrue(found["lint-orders"].runs)

    def test_e4_other_families_do_not(self) -> None:
        data = importlib.import_module("verify_scoped.record").Database({}, {}, {})
        found = {item.unit: item for item in choose_module().choose(self.record("typescript"), data,
                                                                    ["apps/billing/x.ts"])}
        self.assertFalse(found["lint-orders"].runs)


if __name__ == "__main__":
    unittest.main()
