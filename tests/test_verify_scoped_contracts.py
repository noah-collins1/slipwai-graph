"""R4 (AC-S06-3, -4), the contracts: a change selects its consumers as well as its readers.

A change under a service runs the type check and the tests of every browser app whose `api` names it; one under an npm
package runs those of every npm-family deployable; one under a service that produces an event runs those of every
service that reads it, the model read at the base and in the working tree. And `choose` itself: a deployable that builds
in one directory runs its three units together.
"""
from __future__ import annotations

import importlib
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

from scoped_fixture import EVENTS, ShapeCase, events_project
from stamp_fixture import commit_all, git
from test_verify_scoped_record import RecordCase, loaded

from slipwai.assets import ROOT

sys.dont_write_bytecode = True

MODEL = "docs/event-model/model.yaml"
ADR = ROOT / "delivery/docs/adr/0004-verification-dependency-record.md"
DATA_MODEL = ROOT / "specs/001-faster-slipwai/slices/S06-scoped-gate/data-model.md"
# a key the text gives a value: `key: true`, `key` false, `key` is also present, and true
VALUED = re.compile(r"`(\w+)(?:: |`\s+(?:is\s+(?:also\s+)?(?:present,\s+and\s+)?)?`?)(?:true|false|null)\b")
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


sys.path.insert(0, str(ROOT / "assets" / "toolkit" / "scripts"))


def choose_module() -> Any:
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


def published(heading: str) -> str:
    """The text of data-model.md from the `## ` heading that begins with `heading` to the next one."""
    text = DATA_MODEL.read_text(encoding="utf-8")
    start = text.index("\n## " + heading) + 1
    end = text.find("\n## ", start + 1)
    return text[start:] if end < 0 else text[start:end]


def keys_of(built: dict[str, Any]) -> set[str]:
    """Every key of a record that is a name of the contract, at every depth: not the names of deployables or checks,
    which are the project's own."""
    found = set(built)
    for item in built["deployables"].values():
        found |= set(item)
    for check in built["checks"].values():
        found |= set(check)
        found |= set(check["inputs"] or {})
    for item in [*built["contracts"], *built["obligations"]]:
        found |= set(item)
    return found


def row_of(token: str) -> str:
    """A table token as data-model.md writes it: `{dep}` is `<dep>/`, `{npm}` is `packages/<p>/`."""
    spelled = {"{dep}": "<dep>/", "{web}": "<web>/", "{svc}": "<svc>/", "{npm}": "packages/<p>/", "{own}": "<dep>/"}
    return spelled.get(token, token)


def tool_of(token: str) -> str:
    return token.replace("{own}", "<dep>/").replace("{svc}", "<svc>")


class PrintedRecordTest(RecordCase):
    """T031: one test holds the published shape against the emitted one, so the next change to the record changes its
    contract in the same commit."""

    keys: set[str] | None = None

    def emitted(self) -> set[str]:
        """Every key some example's record prints, taken once for the class."""
        keys = type(self).keys
        if keys is None:
            keys = type(self).keys = self.collect()
        return keys

    def collect(self) -> set[str]:
        found: set[str] = set()
        plain = self.project("model-typescript-web")
        found |= keys_of(loaded(plain))
        makefile = self.project("model-typescript-web") / "Makefile"
        text = makefile.read_text(encoding="utf-8")  # a line a project added to `lint:` makes the gate whole
        heading = next(line for line in text.splitlines() if line.startswith("lint:"))
        makefile.write_text(text.replace(heading + "\n", heading + "\n\t@echo added\n", 1), encoding="utf-8")
        found |= keys_of(loaded(makefile.parent))
        same = self.project("model-typescript-web") / "Makefile"  # the sum holds and the factory's rule does not
        text = same.read_text(encoding="utf-8")
        unit = next(line for line in text.splitlines() if line.startswith("lint-web:"))
        gate = next(line for line in text.splitlines() if line.startswith("lint:"))
        added = "\n\t@echo added\n"
        text = text.replace(unit + "\n", unit + added, 1).replace(gate + "\n", gate + added, 1)
        same.write_text(text, encoding="utf-8")
        found |= keys_of(loaded(same.parent))
        events = self.project_copy(events_project(self.parent))
        (events / MODEL).write_text(EDGE, encoding="utf-8")
        document = json.loads((events / "project.json").read_text(encoding="utf-8"))
        document["verification"] = {"obligations": [
            {"name": "billing", "components": ["service", "billing"], "checks": ["test"]}]}
        (events / "project.json").write_text(json.dumps(document), encoding="utf-8")
        found |= keys_of(loaded(events))
        return found

    def project_copy(self, project: Any) -> Any:
        copy = Path(tempfile.mkdtemp(prefix="copy-", dir=self.parent)) / "project"
        shutil.copytree(project, copy, symlinks=True)
        return copy

    def test_e1_every_key_a_record_emits_is_named_in_the_published_shape(self) -> None:
        section = published("The printed record")
        emitted = self.emitted()
        self.assertGreaterEqual(len(emitted), 20)
        for key in ("whole", "event", "api"):
            self.assertIn(key, emitted, "the examples no longer produce a key the contract must name")
        for key in sorted(emitted):
            self.assertTrue(f'"{key}"' in section or f"`{key}`" in section, f"data-model.md does not name `{key}`")

    def test_e1_every_key_the_texts_give_a_value_is_a_key_some_record_prints(self) -> None:
        """T041: ADR 0004's record bullets and data-model's *printed record* describe keys, and a reader built from them
        looks for each. `differs` and a charge for a Makefile difference went with D140 (point 3)."""
        adr = ADR.read_text(encoding="utf-8")
        texts = {"ADR 0004": adr[adr.index("\n## Decision"):adr.index("\n## Consequences")],
                 "data-model.md": published("The printed record")}
        emitted = self.emitted()
        for name, text in texts.items():
            with self.subTest(name):
                valued = set(VALUED.findall(text))
                self.assertTrue(valued, "no key is given a value")
                self.assertEqual(valued - emitted, set(), "a key no record prints")
                self.assertNotIn("charged difference", text)

    def test_e2_each_row_of_the_published_table_is_the_row_the_script_holds(self) -> None:
        table = importlib.import_module("verify_scoped.table")
        families = {"npm": "typescript", "Python": "python", "Go": "go", "Java": "java"}
        shown = published("The table").split("**Contracts**")[0]  # the table of checks, not the contracts' below it
        rows = [line for line in shown.splitlines() if line.startswith("| ") and "---" not in line][1:]
        seen: set[str] = set()
        for line in rows:
            first, files, tools, variables, claims, always = [cell.strip() for cell in line.strip("|").split(" | ")]
            names = re.findall(r"`([^`]+)`", first)
            if "lint-<n>" in first or first.startswith("the same"):
                family = next(word for word in families if re.search(rf"\b{word}\b", first))
                held = {f"unit:{families[family]}": table.UNITS[families[family]]}
            else:
                held = {name: table.CHECKS[name] for name in names if name in table.CHECKS}
                self.assertTrue(held or all(name not in table.CHECKS for name in names), line)
                if not held:  # a check the table does not name: no recorded inputs, whatever else the row says
                    self.assertNotIn("`", files + tools + variables, line)
                    continue
            for name, row in held.items():
                seen.add(name)
                self.assertEqual(re.findall(r"`([^`]+)`", files), [row_of(item) for item in row.files], name)
                self.assertEqual(re.findall(r"`([^`]+)`", tools), [tool_of(item) for item in row.tools], name)
                self.assertEqual(re.findall(r"`([^`]+)`", variables), list(row.variables), name)
                self.assertEqual(claims, "yes" if row.claims else "no", name)
                self.assertEqual(always, row.always or "—", name)
        self.assertEqual(seen - {f"unit:{family}" for family in families.values()}, set(table.CHECKS))
        self.assertEqual({name for name in seen if name.startswith("unit:")}, {f"unit:{key}" for key in table.UNITS})


if __name__ == "__main__":
    unittest.main()
