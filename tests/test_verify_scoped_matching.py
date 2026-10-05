"""T036 + T037 (R4, R5 · AC-S06-2; D140 point 3): on matching text a difference the database finds is the full gate.

The per-rule fingerprints, the variables, `exports` and the `VERIFY_GROUP` table stay as a second check behind the text.
On the factory's own text a difference can only come from make or the reader, never from the project, so it is the full
gate with *dependency knowledge was incomplete*; nothing is charged to one check or one gate any more (D127 item 4's
narrower charges and `rules.used` are retired). Examples hand the comparison a database altered after it was read,
because a text that matches cannot be made to differ by editing the project.
"""
from __future__ import annotations

import importlib
import json
import shutil
import sys
from typing import Any

from test_verify_scoped_record import RecordCase
from test_verify_scoped_sum import INCOMPLETE as BROADENED
from test_verify_scoped_sum import RuleCase
from test_verify_scoped_text import nothing

from slipwai.assets import ROOT

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "assets" / "toolkit" / "scripts"))

RULES = "scripts/verify_scoped/rules.json"
UNITS = ["lint-service", "lint-web", "typecheck-service", "typecheck-web", "test-service", "test-web"]


class DifferenceTest(RecordCase):
    def setUp(self) -> None:
        super().setUp()
        self.rules = importlib.import_module("verify_scoped.rules")
        self.records = importlib.import_module("verify_scoped.record")
        self.root = self.project("model-typescript-web")
        self.held = json.loads((self.root / RULES).read_text(encoding="utf-8"))
        self.data = self.records.database("make", str(self.root / "Makefile"))

    def difference(self, data: Any | None = None, exports: list[str] | None = None) -> str | None:
        found = self.rules.project_exports(self.data, str(self.root)) if exports is None else exports
        return self.rules.difference(self.held, data or self.data, UNITS, found)

    def test_e3_hold_the_factorys_own_database_differs_in_nothing(self) -> None:
        self.assertIsNone(self.difference())

    def test_e3_a_rule_that_differs_is_named(self) -> None:
        recipes = {**self.data.recipes, "check-drawio": [*self.data.recipes["check-drawio"], "@false"]}
        self.assertEqual(self.difference(self.data._replace(recipes=recipes)),
                         "the Makefile's `check-drawio` rule is not the one the factory wrote")

    def test_e3_a_rule_in_verify_checks_and_one_in_verify_are_named_the_same_way(self) -> None:
        needs = {**self.data.needs, "verify": [*self.data.needs["verify"], "extra"]}
        self.assertIn("`verify` rule", self.difference(self.data._replace(needs=needs)) or "")

    def test_e3_a_variable_that_differs_is_named(self) -> None:
        variables = {**self.data.variables, "SHELL": "/bin/sh"}
        self.assertEqual(self.difference(self.data._replace(variables=variables)),
                         "the Makefile's variable `SHELL` is not the one the factory wrote")

    def test_e3_a_variable_the_factory_did_not_write_is_named(self) -> None:
        variables = {**self.data.variables, "EXTRA": "1"}
        origins = {**self.data.origins, "EXTRA": "file"}
        flavours = {**self.data.flavours, "EXTRA": "="}
        said = self.difference(self.data._replace(variables=variables, origins=origins, flavours=flavours))
        self.assertIn("`EXTRA`", said or "")

    def test_e3_export_lines_that_differ_are_named(self) -> None:
        self.assertEqual(self.difference(exports=["export X"]),
                         "the Makefile's export lines are not the ones the factory wrote")

    def test_e3_a_file_that_cannot_be_read_is_unreadable_not_a_pass(self) -> None:
        with self.assertRaises(self.rules.Unreadable):
            self.rules.difference(self.held, self.data, UNITS, None)

    def test_e3_the_charges_are_retired(self) -> None:
        for name in ("used", "Judgement", "judge", "changed_variables", "UNWRITTEN"):
            with self.subTest(name):
                self.assertFalse(hasattr(self.rules, name), f"rules.{name} charges a difference to one member")


class RunTest(RuleCase):
    """The script, with a `make` that prints one rule the Makefile does not have after its own database."""

    def lie(self) -> None:
        """The stand-in `make`, but its `-npq` read ends with one more rule than the Makefile has."""
        real = shutil.which("make") or "make"
        (self.bin / "make").write_text(
            "#!/bin/bash\n"
            "printf '%s\\t%s\\n' make \"$*\" >> \"$STANDIN_LOG\"\n"
            f"case \" $* \" in *\" -npq \"*) {real} \"$@\"; status=$?;"
            " printf '\\ncheck-drawio: lint-web\\n'; exit $status;; esac\n"
            f"exec -a make {real} \"$@\"\n", encoding="utf-8")

    def test_e3_a_difference_on_matching_text_is_the_full_gate_for_want_of_knowledge(self) -> None:
        self.trunk(change=nothing)
        self.lie()
        self.forbidden()
        run = self.scoped()
        lines = self.scoped_lines(run)
        self.assertEqual(lines[-1], BROADENED, run.stdout)
        self.assertIn("check-drawio", lines[0], run.stdout)
        self.assertEqual(len(self.verify_calls()), 1)
        self.assertEqual(self.lines(run), [])
