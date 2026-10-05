"""T030 (R3, R4, R5 · AC-S06-2, -4, -5; D127, ADR 0005): the factory's text for every rule `make verify` reaches.

The factory writes `scripts/verify_scoped/rules.json` beside the `Makefile`: one digest per rule reachable from `verify`
and one per variable it assigns, over one canonical form that `scripts/verify_scoped/rules.py` defines and reads twice,
from the Makefile text (`from_text`) and from make's database (`from_database`). This module holds the two readings
equal for every shape the factory generates (e5) and sweeps the database for a rule held by nothing (e10); what the
script does with a difference is held by `test_verify_scoped_sum`.
"""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import Any

from scoped_fixture import EVENTS, events_project
from test_scoped_targets import SHAPES
from test_verify_scoped_record import RecordCase, loaded, record

from slipwai.assets import ROOT

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "assets" / "toolkit" / "scripts"))

RULES = "scripts/verify_scoped/rules.json"
WHY = "its rule is not the one the factory wrote (scripts/verify_scoped/rules.json)"
UNIT_GATES = ("lint", "typecheck", "test")


class EveryShapeTest(RecordCase):
    longMessage = False

    def rules(self) -> Any:
        return importlib.import_module("verify_scoped.rules")

    def records(self) -> Any:
        return importlib.import_module("verify_scoped.record")

    def units(self, project: Path, data: Any) -> list[str]:
        """The scoped units the project's deployables have, as the script finds them: a deployable called `integration`
        or beginning `integration-` has none, because `test-integration` is the gate's own."""
        names = json.loads((project / "project.json").read_text(encoding="utf-8"))["deployables"]
        return [f"{gate}-{name}" for gate in UNIT_GATES for name in names
                if f"{gate}-{name}" in data.needs and not name.startswith("integration")]

    def shapes(self) -> dict[str, Path]:
        found = {name: self.project(name) for name in SHAPES}
        if EVENTS not in self.projects:
            self.projects[EVENTS] = events_project(self.parent)
        found[EVENTS] = self.projects[EVENTS]
        return found

    def test_e5_hold_the_text_the_factory_wrote_and_the_database_make_prints_are_one_form(self) -> None:
        """Every shape, a two-service project and a cloud one: `from_text` of the Makefile equals `from_database` of
        `make -npq`, the file on disk is that same form, and no check carries the reason."""
        held = 0
        for shape, project in self.shapes().items():
            with self.subTest(shape=shape):
                text = (project / "Makefile").read_text(encoding="utf-8")
                checks = loaded(project)["checks"] if record(project).returncode == 0 else {}  # `integration`: none
                data = self.records().database("make", str(project / "Makefile"))
                units = self.units(project, data)
                written = self.rules().from_text(text)
                self.assertEqual(written, self.rules().from_database(data, units, str(project)), shape)
                self.assertEqual(json.loads((project / RULES).read_text(encoding="utf-8")), written, shape)
                self.assertEqual(written["schema"], 1)
                self.assertIn("verify", written["rules"])
                self.assertIn("verify-checks", written["rules"])
                if checks:
                    held += 1
                    self.assertNotIn(WHY, [check["always"] for check in checks.values()], shape)
        self.assertGreaterEqual(held, 12)

    def test_e5_hold_the_forms_the_generated_shapes_do_not_use_are_one_form_too(self) -> None:
        """Order-only prerequisites, rule lines repeated around one that has a recipe, `?=` and `+=`, and an `override`:
        a hand-written Makefile, because no generated shape has an order-only prerequisite outside a conditional."""
        text = (
            "SHELL := /bin/bash\nX ?= one\nX += two\nY := fixed\nZ = $(X) and $(Y)\nX ?= ignored\n"
            "override W := $(if $(filter output-sync,$(.FEATURES)),--output-sync=target)\n"
            ".PHONY: verify verify-checks a b\n"
            "verify:\n\t@echo $(Z)\n"
            "verify-checks: a\nverify-checks: | o1\nverify-checks: b\n\t@echo done\n# a comment inside the recipe\n"
            "\t@echo $(W)\nverify-checks: | o2 a\n"
            "a: | o3\n\t@echo a\nb: a | o3\n\t@echo b\n"
            "ifeq ($(origin VERIFY_ORDER),command line)\nb: | never\nendif\n"
        )
        folder = self.parent / "hand"
        folder.mkdir(exist_ok=True)
        (folder / "Makefile").write_text(text, encoding="utf-8")
        data = self.records().database("make", str(folder / "Makefile"))
        written = self.rules().from_text(text)
        self.assertEqual(written, self.rules().from_database(data, [], str(folder)))
        self.assertTrue({"verify", "verify-checks", "a", "b"} <= set(written["rules"]))
        self.assertEqual(set(written["variables"]), {"SHELL", "X", "Y", "Z", "W"})
        self.assertNotEqual(written, self.rules().from_text(text.replace("verify-checks: | o1\n", "")))

    def test_e5_the_file_holds_target_and_variable_names_and_digests_alone(self) -> None:
        written = self.rules().from_text((self.project("model-typescript-web") / "Makefile").read_text("utf-8"))
        self.assertEqual(set(written), {"schema", "rules", "variables", "exports"})
        self.assertRegex(written["exports"], r"^[0-9a-f]{64}$")
        for part in ("rules", "variables"):
            self.assertTrue(written[part])
            for name, digest in written[part].items():
                self.assertRegex(digest, r"^[0-9a-f]{64}$", name)
        self.assertNotIn("/home", json.dumps(written))

    def test_e10_sweep_every_rule_reachable_from_verify_is_held_by_the_sum_the_comparison_or_an_always_run_check(
        self,
    ) -> None:
        """The sweep: walk make's database from `verify` and `verify-checks`; a rule held by none of the three fails."""
        walked = 0
        for shape, project in self.shapes().items():
            with self.subTest(shape=shape):
                data = self.records().database("make", str(project / "Makefile"))
                held = json.loads((project / RULES).read_text(encoding="utf-8"))["rules"]
                checks = loaded(project)["checks"] if record(project).returncode == 0 else {}
                always = {unit for unit, check in checks.items() if check["inputs"] is None}
                sums = {unit for unit, check in checks.items() if check["gate"] in UNIT_GATES}
                seen: set[str] = set()
                pending = ["verify", "verify-checks"]
                while pending:
                    target = pending.pop()
                    if target in seen:
                        continue
                    seen.add(target)
                    pending += [*data.needs.get(target, []), *getattr(data, "order_only", {}).get(target, [])]
                for target in sorted(seen):
                    if data.recipes.get(target) or data.needs.get(target) or data.order_only.get(target):
                        walked += 1
                        self.assertTrue(target in held or target in sums or target in always, f"{shape}: {target}")
        self.assertGreater(walked, 100)
