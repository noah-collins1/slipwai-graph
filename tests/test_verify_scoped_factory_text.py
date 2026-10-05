"""T036 + T037 hold (R4, R5 · AC-S06-2, -5; D140 point 4): the one thing still argued by enumeration is finite.

A project's `Makefile` is held by its text, so the scoped gate is only as right as the factory's own text is
unconditional. For every shape in `test_scoped_targets.SHAPES`, plus a two-service project, the factory's `Makefile`
must give the same rule, recipe and variable for every unit and named check under three conditions: as the scoped
call reads it (every unit as a goal, `VERIFY_ORDER=1`), as the full gate's sub-make reads it
(`verify-checks VERIFY_ORDER=1`, one level deeper, with its options), and as the script's database read sees it.
It runs under the make on the machine and, where present, 3.81. A construct `makefile()` gains later must pass it
before the factory ships. The CRLF normalisation of the digest stands only because a CRLF copy of each shape passes
it too.
"""
from __future__ import annotations

import importlib
import shutil
import sys
from pathlib import Path
from typing import Any

from scoped_fixture import EVENTS, events_project
from test_scoped_targets import SHAPES
from test_verify_scoped_record import RecordCase

from slipwai.assets import ROOT

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "assets" / "toolkit" / "scripts"))

GATES = ("lint", "typecheck", "test")
SUBMAKE = ("--no-print-directory",)


class FactoryTextHoldTest(RecordCase):
    longMessage = False

    def modules(self) -> tuple[Any, Any]:
        return importlib.import_module("verify_scoped.rules"), importlib.import_module("verify_scoped.record")

    def shapes(self) -> dict[str, Path]:
        found = {name: self.project(name) for name in SHAPES}
        if EVENTS not in self.projects:
            self.projects[EVENTS] = events_project(self.parent)
        found[EVENTS] = self.projects[EVENTS]
        return found

    def makes(self) -> list[str]:
        return ["make", *[path for name in ("make-3.81", "make3.81", "gmake-3.81") if (path := shutil.which(name))]]

    def reads(self, make: str, makefile: str, units: list[str]) -> dict[str, Any]:
        """The three conditions, each as what make printed: the scoped call, the full gate's sub-make, the script."""
        _, record = self.modules()
        return {
            "the scoped call": record.database(make, makefile, words=(*units, "VERIFY_ORDER=1")),
            "the full gate's sub-make": record.database(make, makefile, record.FULL_GATE_GOAL, "1", SUBMAKE,
                                                        ("VERIFY_ORDER=1",)),
            "the database read": record.database(make, makefile),
        }

    def shape_of(self, data: Any) -> dict[str, Any]:
        """Every rule, recipe and variable the database holds for a unit or a named check, and every variable."""
        rules, _ = self.modules()
        return {"needs": data.needs, "order_only": data.order_only, "recipes": data.recipes,
                "target_vars": data.target_vars, "variables": rules.compared_variables(data)}

    def reached(self, data: Any) -> set[str]:
        """The units, the named checks, `verify` and `verify-checks`: what a scoped run can run."""
        units = [name for name in data.needs if name.split("-")[0] in GATES and "-" in name]
        return {*units, *data.needs["verify-checks"], "verify", "verify-checks"}

    def held(self, shape: dict[str, Any], keys: set[str]) -> dict[str, Any]:
        return {part: {key: value for key, value in found.items() if part == "variables" or key in keys}
                for part, found in shape.items()}

    def differences(self, make: str, makefile: str) -> list[str]:
        """What differs between the three conditions, for the units and checks `verify` reaches; empty where none does.
        The one exception is the factory's own `ifeq ($(origin VERIFY_ORDER),command line)` block, which `gate_order`
        and `order_rules` write: under `VERIFY_ORDER=1` a rule gains prerequisites that order two targets which exist,
        and nothing else. It can run a unit that was not chosen, never skip one, and it is named here so that a second
        kind of difference is not allowed in by the same words."""
        _, record = self.modules()
        base = record.database(make, makefile)
        reached = self.reached(base)
        found = {name: self.held(self.shape_of(data), reached)
                 for name, data in self.reads(make, makefile, sorted(reached - {"verify", "verify-checks"})).items()}
        scoped, sub = found["the scoped call"], found["the full gate's sub-make"]
        said = [f"the scoped call and the full gate's sub-make: {part} of `{key}`" for part in scoped
                for key in sorted({*scoped[part], *sub[part]}) if scoped[part].get(key) != sub[part].get(key)]
        plain = found["the database read"]
        for name, shape in found.items():
            for part, mine in shape.items():
                for key in sorted({*mine, *plain[part]}):
                    here, there = mine.get(key), plain[part].get(key)
                    ordering = part in ("needs", "order_only") and set(there or []) <= set(here or []) \
                        and set(here or []) - set(there or []) <= {*base.needs, *base.order_only}
                    if here != there and not ordering:
                        said.append(f"{name}: {part} of `{key}`")
        return said

    def test_e6_hold_every_shape_reads_the_same_under_the_three_conditions(self) -> None:
        for make in self.makes():
            for shape, project in self.shapes().items():
                with self.subTest(make=make, shape=shape):
                    self.assertEqual(self.differences(make, str(project / "Makefile")), [])

    def test_e6_hold_a_crlf_copy_of_each_shape_reads_the_same_as_its_lf_text(self) -> None:
        for make in self.makes():
            for shape, project in self.shapes().items():
                with self.subTest(make=make, shape=shape):
                    folder = self.parent / f"crlf-{shape}"
                    folder.mkdir(exist_ok=True)
                    (folder / "Makefile").write_bytes((project / "Makefile").read_bytes().replace(b"\n", b"\r\n"))
                    self.assertEqual(self.differences(make, str(folder / "Makefile")), [])
                    units = sorted(self.reached(self.modules()[1].database(make, str(project / "Makefile"))))
                    lf, crlf = (self.reads(make, str(where / "Makefile"), units) for where in (project, folder))
                    for name in lf:
                        self.assertEqual(self.held(self.shape_of(crlf[name]), set(units)),
                                         self.held(self.shape_of(lf[name]), set(units)), name)

    def test_e6_the_hold_has_teeth_a_conditional_on_the_goals_is_a_difference(self) -> None:
        """A rule that exists only under the scoped call's goals, or under the full gate's, shows in the three reads."""
        folder = self.parent / "teeth"
        folder.mkdir(exist_ok=True)
        text = (self.project("model-typescript-web") / "Makefile").read_text(encoding="utf-8")
        for what, condition in (("a unit as a goal", "ifneq ($(filter lint-web,$(MAKECMDGOALS)),)"),
                                ("the full gate's goal", "ifneq ($(filter verify-checks,$(MAKECMDGOALS)),)"),
                                ("VERIFY_ORDER", "ifeq ($(origin VERIFY_ORDER),command line)")):
            with self.subTest(what):
                edited = f"{text}\n{condition}\ncheck-drawio: lint-docs\nendif\n"
                (folder / "Makefile").write_text(edited, encoding="utf-8")
                self.assertNotEqual(self.differences("make", str(folder / "Makefile")), [])
