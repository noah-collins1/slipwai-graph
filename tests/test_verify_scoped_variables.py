"""T033 (R4, R5 · AC-S06-2, -5; D127 item 4, D133, D140): every variable and export line make can hand a recipe is held.

`override SHELL := …`, `export PATH := …`, `.SHELLFLAGS`, a `define`, a pattern-specific variable, an `unexport`, a
target-specific variable: each changes what a skipped check runs, and each is a `Makefile` the factory did not write, so
each is the full gate with the `Makefile` words (D140 point 6), wherever it sits. The comparison of variables and export
lines stays as a second check behind the text; its hold (e4) is the factory's own Makefile in every shape. The runs are
the real `make verify-scoped` on a slice branch, after the trunk changed the project's own `Makefile`.
"""
from __future__ import annotations

import importlib
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

from scoped_fixture import EVENTS, FULL, MAKEFILE_WORDS, events_project
from test_scoped_targets import SHAPES
from test_verify_scoped_record import RecordCase
from test_verify_scoped_sum import RuleCase

from slipwai.assets import ROOT

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "assets" / "toolkit" / "scripts"))

RULES = "scripts/verify_scoped/rules.json"
UNIT_GATES = ("lint", "typecheck", "test")


class FullGateCase(RuleCase):
    def assert_full(self, text: str) -> None:
        """The trunk's `Makefile` gains `text`; a branch that edits the web app runs the full gate, for the text."""
        self.trunk(lambda old: old + text)
        self.forbidden()
        run = self.scoped()
        self.assertEqual(self.scoped_lines(run)[0], FULL + MAKEFILE_WORDS, run.stdout)
        self.assertEqual(self.lines(run), [], "a unit line was said beside the full gate")
        self.assertEqual(len(self.verify_calls()), 1, "`make verify` was not run exactly once")


class UnwrittenVariableTest(FullGateCase):
    def test_e1_an_override_of_a_factory_variable_is_a_difference_in_that_variable(self) -> None:
        self.assert_full("\noverride SHELL := /bin/bash\n")

    def test_e2_an_exported_variable_the_factory_never_assigned_is_the_full_gate(self) -> None:
        self.assert_full("\nexport PATH := $(CURDIR)/tools/bin:$(PATH)\n")

    def test_e2_one_born_in_the_environment_and_reassigned_is_the_full_gate(self) -> None:
        self.assert_full("\nPATH := $(CURDIR)/tools/bin:$(PATH)\n")

    def test_e2_a_plain_variable_that_nothing_references_is_the_full_gate_too(self) -> None:
        self.assert_full("\nFOO := x\n")

    def test_e3_a_shellflags_the_factory_did_not_write_is_a_difference(self) -> None:
        self.assert_full("\n.SHELLFLAGS := -ec\n")

    def test_e3_so_is_a_special_variable_make_reads(self) -> None:
        self.assert_full("\nVPATH = tools\n")

    def test_e5_unexport_of_a_variable_is_the_full_gate(self) -> None:
        self.assert_full("\nunexport DATABASE_URL\n")

    def test_e5_export_all_variables_is_the_full_gate(self) -> None:
        self.assert_full("\n.EXPORT_ALL_VARIABLES:\n")

    def test_e5_a_pattern_specific_variable_is_the_full_gate(self) -> None:
        self.assert_full("\n%: SHELL := /bin/bash\n")

    def test_e6_a_define_variable_is_the_full_gate(self) -> None:
        self.assert_full("\ndefine BLOCK\none\ntwo\nendef\n")

    def test_e6_an_eval_that_can_write_any_of_the_above_is_the_full_gate(self) -> None:
        self.assert_full("\n$(eval export NODE_OPTIONS := --require ./tools/hook.js)\n")


class TargetVariableTest(FullGateCase):
    """A target-specific variable was charged by what it sat on (D127 item 4); the text is held now, so each is the
    full gate, including one on a rule `make verify` does not reach."""

    def test_e7_on_a_rule_verify_does_not_reach_is_the_full_gate(self) -> None:
        self.assert_full("\ndeploy: IMAGE := foo\n")

    def test_e7_on_a_named_check_is_the_full_gate(self) -> None:
        self.assert_full("\ncheck-drawio: IMAGE := foo\n")

    def test_e7_on_verify_is_the_full_gate(self) -> None:
        self.assert_full("\nverify: IMAGE := foo\n")


class FactoryHoldTest(RecordCase):
    """e4: the factory's own text gives no difference, in every shape, under every make the machine has."""

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

    def difference(self, make: str, project: Path) -> Any:
        rules, record = self.modules()
        data = record.database(make, str(project / "Makefile"))
        names = json.loads((project / "project.json").read_text(encoding="utf-8"))["deployables"]
        gates = {gate: [f"{gate}-{name}" for name in names if f"{gate}-{name}" in data.needs
                        and not name.startswith("integration")] for gate in UNIT_GATES}
        gates = {gate: units for gate, units in gates.items() if units}
        held = rules.load(str(project / RULES))
        return rules.difference(held, data, [unit for each in gates.values() for unit in each],
                                rules.project_exports(data, str(project)))

    def test_e4_hold_no_shape_the_factory_generates_has_a_difference(self) -> None:
        for make in self.makes():
            for shape, project in self.shapes().items():
                with self.subTest(make=make, shape=shape):
                    self.assertIsNone(self.difference(make, project))

    def test_e4_hold_the_factorys_own_override_dot_names_and_export_lines_are_held(self) -> None:
        rules, record = self.modules()
        project = self.project("model-typescript-web-cloud")
        text = (project / "Makefile").read_text(encoding="utf-8")
        data = record.database("make", str(project / "Makefile"))
        held = rules.from_text(text)
        compared = rules.compared_variables(data)
        self.assertEqual(compared["VERIFY_GROUP"], ("override simple", rules.OUTPUT_SYNC))
        self.assertIn(".DEFAULT_GOAL", compared)
        self.assertEqual(set(held["variables"]), set(compared))
        self.assertIn("export WEB_HOST", rules.export_lines(text))
        self.assertEqual(held["exports"], rules.from_database(data, [], str(project))["exports"])

    def test_e4_a_made_up_features_list_that_lacks_output_sync_still_holds(self) -> None:
        """The version-dependent override is held by its written text where the value is what the text expands to."""
        rules, record = self.modules()
        project = self.project("model-typescript-web")
        data = record.database("make", str(project / "Makefile"))
        features = {".FEATURES": "target-specific order-only", "VERIFY_GROUP": ""}
        older = data._replace(variables={**data.variables, **features})
        self.assertEqual(rules.compared_variables(older)["VERIFY_GROUP"], ("override simple", rules.OUTPUT_SYNC))
        wrong = data._replace(variables={**data.variables, "VERIFY_GROUP": "--output-sync=none"})
        self.assertNotEqual(rules.compared_variables(wrong)["VERIFY_GROUP"][1], rules.OUTPUT_SYNC)


class SweepTest(RecordCase):
    """e8 (the sweep): each origin the comparison does not read, with the reason, and the places `rules.py` and
    `record.database` decide a variable is not compared."""

    def compared(self, text: str, **env: str) -> set[str]:
        rules = importlib.import_module("verify_scoped.rules")
        record = importlib.import_module("verify_scoped.record")
        folder = self.parent / "sweep"
        folder.mkdir(exist_ok=True)
        (folder / "Makefile").write_text(text, encoding="utf-8")
        previous = dict(os.environ)
        os.environ.update(env)
        try:
            data = record.database("make", str(folder / "Makefile"))
        finally:
            os.environ.clear()
            os.environ.update(previous)
        return set(rules.compared_variables(data))

    def test_e8_environment_command_line_default_and_automatic_origins_are_left_out(self) -> None:
        found = self.compared("FROM_ENV ?= x\nverify:\n\t@true\n", FROM_ENV="given", HOME="/somewhere")
        self.assertEqual(found, set(), "environment: the baseline's (D116), D116 hashes the variables the stamp names")
        self.assertNotIn("CC", found)  # default: make's own value; an assignment in the Makefile makes it `file`
        self.assertEqual(self.compared("CC := mine\n"), {"CC"})
        self.assertNotIn("@", self.compared("verify:\n\t@true\n"))  # automatic

    def test_e8_environment_override_is_left_out(self) -> None:
        found = self.compared("FROM_ENV := x\nverify:\n\t@true\n", FROM_ENV="given", GNUMAKEFLAGS="-e")
        self.assertEqual(found, set(), "`make -e`: the environment wins, and that is the baseline's")

    def test_e8_curdir_makefile_list_and_make_own_flags_are_left_out_and_added_flags_are_not(self) -> None:
        # CURDIR, MAKEFILE_LIST, MAKEFLAGS and GNUMAKEFLAGS as make itself gives them
        self.assertEqual(self.compared("verify:\n\t@true\n"), set())
        self.assertEqual(self.compared("MAKEFLAGS += -r\n"), {"MAKEFLAGS"})

    def test_e8_the_specials_make_reads_and_dot_names_are_compared_when_the_makefile_gives_them(self) -> None:
        names = ["VPATH", "GPATH", "MAKEFILES", "MAKESHELL", ".SHELLFLAGS", ".RECIPEPREFIX", ".DEFAULT_GOAL",
                 ".EXTRA_PREREQS"]
        text = "".join(f"{name} := value\n" for name in names)
        self.assertEqual(self.compared(text), set(names))

    def test_e8_an_override_keeps_its_own_flavour_and_a_define_is_read(self) -> None:
        rules = importlib.import_module("verify_scoped.rules")
        record = importlib.import_module("verify_scoped.record")
        folder = self.parent / "flavour"
        folder.mkdir(exist_ok=True)
        text = "override A := one\noverride B = two\nC := three\ndefine D\nfour\nfive\nendef\nE := six\nseven\n"
        (folder / "Makefile").write_text(text, encoding="utf-8")
        held = rules.compared_variables(record.database("make", str(folder / "Makefile")))
        self.assertEqual(held["A"], ("override simple", "one"))
        self.assertEqual(held["B"], ("override recursive", "two"))
        self.assertEqual(held["C"], ("simple", "three"))
        self.assertEqual(held["D"], ("recursive", "four\nfive"))
