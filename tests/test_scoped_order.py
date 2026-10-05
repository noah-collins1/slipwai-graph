"""T055 (adversary C2 · D96): the scoped ordering of a family with a shared root.

Go's `lint` resolves the workspace and writes `go.work.sum`, so the gate runs every lint before any typecheck or test
(D96). The scoped section orders one service's typecheck and test after that service's lint; with two Go services, a
chosen lint of the other must finish before them too, or one service's `go vet` reads `go.work.sum` while the other's
staticcheck writes it. Only a lint that is chosen: an unchosen one is a check that was skipped, not run for its order.
Read from `make -n` over the generated `Makefile`, in the order make would run the recipes serially.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from support import FactoryTestCase
from test_scoped_targets import build

sys.dont_write_bytecode = True

LINT = {name: f"cd apps/{name} && go tool staticcheck ./..." for name in ("service", "second")}
TYPECHECK = {name: f"cd apps/{name} && go test -run '^$' ./..." for name in ("service", "second")}
TEST = {name: f"cd apps/{name} && go test -coverpkg=./... -coverprofile=coverage.out ./..."
        for name in ("service", "second")}


class GoOrderTest(FactoryTestCase):
    parent: Path
    project: Path

    @classmethod
    def setUpClass(cls) -> None:
        cls.parent = Path(tempfile.mkdtemp(prefix="scoped-order-"))
        cls.addClassCleanup(shutil.rmtree, cls.parent, ignore_errors=True)
        cls.project = build(cls.parent, "two-go", cls())

    def order(self, *goals: str) -> list[str]:
        """The recipe lines make would run, in order, for `goals` typed in that order under the gate's order."""
        done = subprocess.run(["make", "-n", "--no-print-directory", *goals, "VERIFY_ORDER=1"], cwd=self.project,
                              text=True, capture_output=True, timeout=60, check=True)
        return done.stdout.splitlines()

    def before(self, lines: list[str], first: str, second: str) -> None:
        self.assertIn(first, lines)
        self.assertIn(second, lines)
        self.assertLess(lines.index(first), lines.index(second), f"`{first}` must run before `{second}`")

    def test_c2_a_chosen_lint_of_the_other_service_runs_before_a_typecheck_or_test(self) -> None:
        for check, lines in (("typecheck", TYPECHECK), ("test", TEST)):
            with self.subTest(check=check):
                self.before(self.order(f"{check}-service", "lint-second"), LINT["second"], lines["service"])

    def test_c2_it_holds_the_other_way_round(self) -> None:
        self.before(self.order("test-second", "lint-service"), LINT["service"], TEST["second"])

    def test_c2_every_chosen_lint_precedes_every_typecheck_and_test(self) -> None:
        lines = self.order("test-service", "typecheck-second", "lint-second", "lint-service")
        for lint in LINT.values():
            for later in (TEST["service"], TYPECHECK["second"]):
                self.before(lines, lint, later)

    def test_c2_an_unchosen_lint_is_not_run_for_its_order(self) -> None:
        lines = self.order("typecheck-service")
        self.assertEqual([line for line in lines if "apps/second &&" in line], [])

    def test_c2_without_the_gates_order_nothing_waits(self) -> None:
        """A target typed alone is what it was whatever a shell exports (`$(origin)` is `command line` only)."""
        done = subprocess.run(["make", "-n", "--no-print-directory", "typecheck-service", "lint-second"],
                              cwd=self.project, text=True, capture_output=True, timeout=60, check=True)
        lines = done.stdout.splitlines()
        self.assertLess(lines.index(TYPECHECK["service"]), lines.index(LINT["second"]))
