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
import re
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
ORDER = "ifeq ($(origin VERIFY_ORDER),command line)"
BASE = (".PHONY: verify verify-checks zz-grow zz-base\nverify: verify-checks\nverify-checks: zz-grow\nzz-base:\n"
        "\t@true\nzz-grow:\n\t{recipe}\n")
AUTOMATIC = re.compile(r"\$[(\{]?[\^+<?|]")


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
        """The four conditions, each as what make printed: the scoped call, the full gate's sub-make, the script, and
        the scoped goals without `VERIFY_ORDER`."""
        _, record = self.modules()
        return {
            "the scoped call": record.database(make, makefile, words=(*units, "VERIFY_ORDER=1")),
            "the full gate's sub-make": record.database(make, makefile, record.FULL_GATE_GOAL, "1", SUBMAKE,
                                                        ("VERIFY_ORDER=1",)),
            "the database read": record.database(make, makefile),
            "the scoped goals alone": record.database(make, makefile, words=tuple(units)),
        }

    def shape_of(self, data: Any) -> dict[str, Any]:
        """Every rule, recipe and variable the database holds for a unit or a named check, and every variable."""
        rules, _ = self.modules()
        return {"needs": data.needs, "order_only": data.order_only, "recipes": data.recipes,
                "target_vars": data.target_vars, "variables": rules.compared_variables(data)}

    def reached(self, make: str, makefile: str) -> tuple[list[str], list[str]]:  # (goals, reached)
        """The goals a scoped run names, and every target `verify`, `verify-checks` and those goals wait for
        (`rules.reach`) in any of the reads: what a scoped run can run, prerequisites of prerequisites included."""
        rules, record = self.modules()
        base = record.database(make, makefile)
        units = sorted(name for name in base.needs if name.split("-")[0] in GATES and "-" in name)
        goals = sorted({*units, *base.needs["verify-checks"]})  # the units and the named checks
        starts = ["verify", "verify-checks", *goals]
        found: dict[str, None] = {}
        for data in (base, *self.reads(make, makefile, goals).values()):
            found.update(dict.fromkeys(rules.reach(rules.from_database_parsed(data, goals), starts)))
        return goals, list(found)

    def held(self, shape: dict[str, Any], keys: set[str]) -> dict[str, Any]:
        return {part: {key: value for key, value in found.items() if part == "variables" or key in keys}
                for part, found in shape.items()}

    def why_not_ordering(self, reads: list[Any], reached: list[str], key: str) -> str | None:
        """Why a target that gained prerequisites is not the factory's ordering and nothing else, or None where it is
        (D140 point 4). Three conditions make the exception sound, and each is asserted: no recipe of the target names
        an automatic variable; neither it nor a target that reaches it has a target-specific variable in any read; a
        file target (not in `.PHONY`) gains only order-only prerequisites."""
        rules, _ = self.modules()
        if any(AUTOMATIC.search(line) for data in reads for line in data.recipes.get(key, [])):
            return "its recipe names an automatic variable"
        parsed = [rules.from_database_parsed(data, []) for data in reads]
        above = [name for name in reached if any(key in rules.reach(each, [name]) for each in parsed)]
        if any(data.target_vars.get(name) for data in reads for name in above):
            return "it or a target that reaches it has a target-specific variable"
        return None

    def differences(self, make: str, makefile: str) -> list[str]:
        """What differs between the reads, for every target `verify` and the units reach; empty where none does. The
        one exception is the factory's own `ifeq ($(origin VERIFY_ORDER),command line)` block, which `gate_order` and
        `order_rules` write: under `VERIFY_ORDER=1` a rule gains prerequisites that order two targets which exist, and
        nothing else (`why_not_ordering` holds what makes that sound). It can run a unit that was not chosen, never
        skip one. The scoped call's goals without `VERIFY_ORDER` are a fourth read that must equal the database read
        exactly, so that any growth is the block's and no other conditional's."""
        _, record = self.modules()
        base = record.database(make, makefile)
        goals, reached = self.reached(make, makefile)
        reads = self.reads(make, makefile, goals)
        found = {name: self.held(self.shape_of(data), set(reached)) for name, data in reads.items()}
        plain = found["the database read"]
        said = []
        for name, shape in found.items():
            for part, mine in shape.items():
                for key in sorted({*mine, *plain[part]}):
                    here, there = mine.get(key), plain[part].get(key)
                    if here == there:
                        continue
                    grown = part in ("needs", "order_only") and name != "the scoped goals alone" \
                        and set(there or []) <= set(here or []) and set(here or []) - set(there or []) <= {
                            *base.needs, *base.order_only}
                    why = self.why_not_ordering(list(reads.values()), reached, key) if grown else None
                    if grown and part == "needs" and key not in set(base.needs.get(".PHONY", [])):
                        why = why or "it is a file target that gained a normal prerequisite"
                    if not grown or why:
                        said.append(f"{name}: {part} of `{key}`" + (f" — {why}" if why else ""))
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
                    goals, reached = self.reached(make, str(project / "Makefile"))
                    lf, crlf = (self.reads(make, str(where / "Makefile"), goals) for where in (project, folder))
                    for name in lf:
                        self.assertEqual(self.held(self.shape_of(crlf[name]), set(reached)),
                                         self.held(self.shape_of(lf[name]), set(reached)), name)

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

    def minimal(self, extra: str, recipe: str = "@true") -> list[str]:
        folder = self.parent / "ordering"
        folder.mkdir(exist_ok=True)
        (folder / "Makefile").write_text(BASE.format(recipe=recipe) + extra, encoding="utf-8")
        return self.differences("make", str(folder / "Makefile"))

    def test_e2_ordering_that_adds_an_existing_target_to_a_phony_one_is_admitted(self) -> None:
        self.assertEqual(self.minimal(f"{ORDER}\nzz-grow: zz-base\nendif\n"), [])

    def test_e2_an_order_only_prerequisite_of_a_file_target_is_admitted(self) -> None:
        extra = f"verify-checks: zz.txt\nzz.txt:\n\t@true\n{ORDER}\nzz.txt: | zz-base\nendif\n"
        self.assertEqual(self.minimal(extra), [])

    def test_e2_i_a_recipe_naming_an_automatic_variable_is_not_admitted(self) -> None:
        for variable in ("$^", "$+", "$<", "$?", "$|", "$(^)"):
            with self.subTest(variable):
                found = self.minimal(f"{ORDER}\nzz-grow: zz-base\nendif\n", f"@echo {variable}")
                self.assertTrue(any("automatic variable" in line for line in found), found)

    def test_e2_ii_a_target_specific_variable_on_the_target_or_one_that_reaches_it_is_not_admitted(self) -> None:
        for where in ("zz-grow", "verify-checks", "verify"):
            with self.subTest(where):
                found = self.minimal(f"{where}: ZZ := 1\n{ORDER}\nzz-grow: zz-base\nendif\n")
                self.assertTrue(any("target-specific variable" in line for line in found), found)

    def test_e2_iii_a_file_target_that_gains_a_normal_prerequisite_is_not_admitted(self) -> None:
        extra = f"verify-checks: zz.txt\nzz.txt:\n\t@true\n{ORDER}\nzz.txt: zz-base\nendif\n"
        found = self.minimal(extra)
        self.assertTrue(any("file target" in line for line in found), found)

    def real(self, extra: str) -> list[str]:
        folder = self.parent / "real-mutation"
        folder.mkdir(exist_ok=True)
        text = (self.project("model-typescript-web") / "Makefile").read_text(encoding="utf-8")
        (folder / "Makefile").write_text(f"{text}\n{extra}", encoding="utf-8")
        return self.differences("make", str(folder / "Makefile"))

    def test_e1_a_variable_on_a_prerequisite_of_a_unit_is_held_as_a_named_check_is(self) -> None:
        for target in ("check-python", "node_modules/.package-lock.json"):
            with self.subTest(target):
                found = self.real(f"{ORDER}\n{target}: VERIFY_HIDDEN := 1\nendif\n")
                self.assertNotEqual(found, [])

    def test_e3_growth_under_the_scoped_goals_alone_is_a_difference_and_under_verify_order_is_not(self) -> None:
        goals = "ifneq ($(filter lint-web,$(MAKECMDGOALS)),)"
        found = self.real(f"{goals}\ncheck-drawio: lint-web\nendif\n")
        self.assertTrue(any("the scoped goals alone" in line for line in found), found)
        self.assertEqual(self.real(f"{ORDER}\ncheck-drawio: lint-web\nendif\n"), [])
