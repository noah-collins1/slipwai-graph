"""R8 (AC-S06-11, R10 e2): obligations a person declares.

`verification.obligations` in `project.json` — read at the base — is a list of `{name, components, checks}`: a change
under any component's path runs the obligation's checks, named with it, which the record also lists. A key that is
missing is no obligation; one that is present and not that shape is one line naming the entry, then the full gate.
`metadata()` never writes the key. Each project here has the key committed on `main` and the slice branch cut from it.
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from typing import Any

from scoped_fixture import EVENTS, FULL, LINE, SLICE, ShapeCase, shape_template
from stamp_fixture import commit_all

sys.dont_write_bytecode = True

DRY: dict[str, str | None] = {"STANDIN_DRY": "1"}
BROADENED = FULL + "dependency knowledge was incomplete"
WHERE = "in project.json's verification.obligations"
CHECKOUT: dict[str, Any] = {"name": "checkout", "components": ["service", "second"],
                            "checks": ["test-second", "test-service"]}


class Declared(ShapeCase):
    """A project whose `main` carries `verification` as the example gives it, and a slice branch cut from it."""

    shape = "java-go"

    def declare(self, verification: object) -> None:
        self.checkout("main")
        path = self.repo / "project.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        document["verification"] = verification
        path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        commit_all(self.repo, "declare verification")
        self.checkout("-q", "-B", SLICE, "main")

    def fresh(self) -> None:
        """The state before a run: a full gate leaves a stamp and a baseline, which the next must not meet."""
        self.reset()
        for left in (self.repo / ".git" / "slipwai").iterdir():
            left.unlink()
        self.write_baseline()

    def record(self) -> dict[str, Any]:
        run = subprocess.run([sys.executable, "-B", "scripts/verify-scoped.py", "record"], cwd=self.repo,
                             env=self.environment(), text=True, capture_output=True, timeout=120)
        self.assertEqual(run.returncode, 0, run.stderr)
        found: dict[str, Any] = json.loads(run.stdout)
        return found

    def assert_broadened(self, fault: str) -> None:
        run = self.scoped(DRY)
        self.assertEqual(self.scoped_lines(run), [LINE + fault, BROADENED], run.stdout + run.stderr)
        self.assertEqual(len(self.verify_calls()), 1, "`make verify` was not run exactly once")
        self.assertEqual(self.lines(run), [], "a unit line was said beside the full gate")


class ObligationTest(Declared):
    def test_e1_a_change_under_one_component_runs_the_checks_of_the_other_with_the_obligations_name(self) -> None:
        self.declare({"obligations": [{**CHECKOUT, "checks": ["test-second"]}]})
        self.edit("apps/service/extra.txt")
        ran, skipped = self.decided(self.scoped(DRY))
        self.assertEqual(ran["test-second"], "obligation checkout (apps/service/extra.txt)")
        self.assertEqual(ran["lint-second"], "shares a build directory with test-second")
        self.assertEqual(ran["test-service"], "apps/service/extra.txt changed")
        self.assertNotIn("lint-second", skipped)

    def test_e1_the_record_lists_the_obligation_with_its_checks_sorted(self) -> None:
        self.declare({"obligations": [{**CHECKOUT, "checks": ["test-service", "test-second", "test-service"]}]})
        self.assertEqual(self.record()["obligations"], [CHECKOUT])

    def test_e1_a_gate_name_means_all_its_units(self) -> None:
        self.declare({"obligations": [{**CHECKOUT, "checks": ["test"]}]})
        self.assertEqual(self.record()["obligations"], [CHECKOUT])
        self.edit("apps/service/extra.txt")
        ran, _ = self.decided(self.scoped(DRY))
        self.assertEqual(ran["test-second"], "obligation checkout (apps/service/extra.txt)")

    def test_e3_other_keys_in_an_entry_are_ignored(self) -> None:
        self.declare({"obligations": [{**CHECKOUT, "why": "they share a table", "owner": 4}], "other": True})
        self.assertEqual(self.record()["obligations"], [CHECKOUT])

    def test_e4_nothing_declared_is_no_obligation_and_no_line(self) -> None:
        empty: list[object] = [{}, {"obligations": []}]
        for verification in empty:
            with self.subTest(verification=verification):
                self.declare(verification)
                self.fresh()
                self.edit("apps/service/extra.txt")
                run = self.scoped(DRY)
                self.assertNotIn("obligation", run.stdout)
                self.assertEqual(self.record()["obligations"], [])

    def test_e4_no_verification_key_at_all_is_the_same(self) -> None:
        self.edit("apps/service/extra.txt")
        run = self.scoped(DRY)
        self.assertNotIn("obligation", run.stdout)
        self.assertEqual(self.record()["obligations"], [])

    def test_e4_it_is_read_at_the_base_and_a_branch_that_changes_project_json_is_the_full_gate(self) -> None:
        path = self.repo / "project.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        document["verification"] = {"obligations": [CHECKOUT]}
        path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        self.assertEqual(self.record()["obligations"], [], "the branch's own project.json was read")
        said = self.scoped_lines(self.scoped(DRY))
        self.assertEqual(said, [f"{LINE}dependency knowledge was incomplete for project.json — it is project.json",
                                BROADENED])


class FaultTest(Declared):
    def broken(self, verification: object, fault: str) -> None:
        self.declare(verification)
        self.fresh()
        self.edit("apps/service/extra.txt")
        self.assert_broadened(fault)
        run = subprocess.run([sys.executable, "-B", "scripts/verify-scoped.py", "record"], cwd=self.repo,
                             env=self.environment(), text=True, capture_output=True, timeout=120)
        self.assertEqual((run.returncode, run.stdout), (1, ""), "the record was printed for a fault")
        self.assertEqual(len(run.stderr.strip().splitlines()), 1, run.stderr)
        self.assertIn(fault, run.stderr)

    def test_e2_a_check_the_record_does_not_hold_names_the_entry_and_the_check(self) -> None:
        self.broken({"obligations": [{**CHECKOUT, "checks": ["test-nope"]}]},
                    f"obligation 1 (`checkout`) {WHERE} names the check `test-nope`, which the record does not hold")

    def test_e2_the_position_is_the_entrys_in_the_list(self) -> None:
        other = {**CHECKOUT, "name": "other", "checks": ["test-gone"]}
        self.broken({"obligations": [CHECKOUT, other]},
                    f"obligation 2 (`other`) {WHERE} names the check `test-gone`, which the record does not hold")

    def test_e3_obligations_that_is_not_a_list(self) -> None:
        self.broken({"obligations": {}}, "verification.obligations in project.json is not a list")

    def test_e3_verification_that_is_not_an_object(self) -> None:
        self.broken([], "verification in project.json is not an object")

    def test_e3_a_name_used_twice(self) -> None:
        self.broken({"obligations": [CHECKOUT, {**CHECKOUT, "checks": ["test"]}]},
                    f"obligation 2 (`checkout`) {WHERE} repeats the name of obligation 1")

    def test_e3_fewer_than_two_distinct_components(self) -> None:
        for components in (["service"], ["service", "service"], []):
            with self.subTest(components=components):
                self.broken({"obligations": [{**CHECKOUT, "components": components}]},
                            f"obligation 1 (`checkout`) {WHERE} names fewer than two distinct components")

    def test_e3_a_component_that_is_not_a_deployable(self) -> None:
        self.broken({"obligations": [{**CHECKOUT, "components": ["service", "ghost"]}]},
                    f"obligation 1 (`checkout`) {WHERE} names the component `ghost`, "
                    "which is not among the deployables")

    def test_e3_an_entry_that_is_no_object_or_has_no_name_or_no_checks(self) -> None:
        for entry, fault in (
            ("checkout", f"obligation 1 (unnamed) {WHERE} is not an object"),
            ({**CHECKOUT, "name": ""}, f"obligation 1 (unnamed) {WHERE} has no name"),
            ({**CHECKOUT, "checks": []}, f"obligation 1 (`checkout`) {WHERE} names no checks"),
            ({**CHECKOUT, "checks": "test"}, f"obligation 1 (`checkout`) {WHERE} names no checks"),
            ({**CHECKOUT, "checks": [3]}, f"obligation 1 (`checkout`) {WHERE} names a check that is not a name"),
        ):
            with self.subTest(entry=entry):
                self.broken({"obligations": [entry]}, fault)


class ReasonOrderTest(ShapeCase):
    shape = EVENTS

    def test_e1_the_obligation_is_named_before_the_recipe_the_unit_shares(self) -> None:
        self.checkout("main")
        path = self.repo / "project.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        document["verification"] = {"obligations": [
            {"name": "ledger", "components": ["service", "billing"], "checks": ["test-service"]}]}
        path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        commit_all(self.repo, "declare verification")
        self.checkout("-q", "-B", SLICE, "main")
        self.edit("apps/billing/src/billing/extra.py", "x = 1\n")
        ran, _ = self.decided(self.scoped(DRY))
        self.assertEqual(ran["test-service"], "obligation ledger (apps/billing/src/billing/extra.py)")
        self.assertEqual(ran["lint-service"], "shares one recipe with lint-billing")


class MetadataTest(unittest.TestCase):
    def test_e5_hold_a_generated_project_json_has_no_verification_key(self) -> None:
        """HOLD (teeth: make `metadata()` write `verification` and this fails)."""
        for shape in ("model-typescript-web", "two-python"):
            with self.subTest(shape=shape):
                document = json.loads((shape_template(shape) / "project.json").read_text(encoding="utf-8"))
                self.assertNotIn("verification", document)


if __name__ == "__main__":
    unittest.main()
