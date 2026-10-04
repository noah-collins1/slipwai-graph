"""What `make verify` runs, and what a wrapped application's gate says, pinned before S03-verify-stamp changes it.

The slice is about to move the checks of a generated project's `verify` to a `verify-checks` target and put a
two-step recipe on `verify`. Which checks a full run makes, in which order, and the closing line must not move with
it, and a project with a wrapped application keeps its gate (and the refusal while nothing is confirmed) byte for
byte. These are holds: green against the generator as it was, and after the change. The gate's prerequisites are
read through `gate_prerequisites`, which follows `verify` to `verify-checks` once that target exists, so the same
test passes on both sides. That `verify` itself carries the prerequisites is deliberately not pinned.
"""
from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

from support import FactoryTestCase
from test_candidates import adopted, slipwai

CLOSING = "\t@echo\n\t@echo 'verify: all gates passed'\n"
HEADING = "## Full deterministic pre-commit gate"


def gate_target_name(makefile: str) -> str:
    """The target a full run's checks hang on: `verify-checks` where the stamp's recipe has split them off."""
    return "verify-checks" if re.search(r"^verify-checks:", makefile, re.M) else "verify"


def gate_prerequisites(makefile: str) -> list[str]:
    """Every prerequisite the gate target is given, in the order its rules appear, `##` descriptions removed."""
    name = gate_target_name(makefile)
    found: list[str] = []
    for line in makefile.splitlines():
        match = re.match(rf"^{name}:(?!=)(.*)$", line)
        if match:
            found += match.group(1).split("##")[0].split()
    return found


def gate_rule(makefile: str) -> str:
    """The main rule of the gate target as written: its first line and the recipe lines under it."""
    lines = makefile.splitlines(keepends=True)
    head = f"{gate_target_name(makefile)}:"
    start = next(i for i, line in enumerate(lines) if line.startswith(head) and "check-openapi" not in line)
    end = start + 1
    while end < len(lines) and lines[end].startswith("\t"):
        end += 1
    return "".join(lines[start:end])


GENERATED = [
    "check-python", "lint", "typecheck", "check-imports", "check-migrations", "check-slice-scope",
    "check-extensions", "check-agents", "check-speckit", "check-codegraph", "check-ux-gates",
    "check-constitution", "check-benchmark", "check-decisions", "test",
    "check-model", "check-drawio",
]
STANDARD = [name for name in GENERATED if name not in ("check-model", "check-drawio")]
WRAPPED = [
    "check-python", "lint", "typecheck", "check-imports", "check-migrations", "check-slice-scope",
    "check-extensions", "check-agents", "check-speckit", "check-codegraph", "check-ux-gates",
    "check-constitution", "check-benchmark", "check-decisions", "test",
    "check-convergence",
]
NOTHING_CONFIRMED_RULE = (
    "verify: ## Refuses until a candidate has been confirmed as an application\n"
    "\t@echo 'verify: nothing is confirmed as an application here, so there is nothing to hold to a gate.'\n"
    "\t@echo '  project.json lists what the survey found under `candidates`; confirming one makes it an'\n"
    "\t@echo '  application and regenerates this Makefile with its build in the gate.'\n"
    "\t@echo '  /ground, in the agent, asks about each; `slipwai adopt --confirm <name>` does it without one.'\n"
    "\t@exit 1\n"
)


class GeneratedGatePinnedTest(FactoryTestCase):
    def test_a_project_with_a_transport_runs_its_checks_in_order_then_the_published_document(self) -> None:
        """Hold (pin 1): the checks, their order, `check-openapi` inside the transport's markers, the closing line."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "pinned", "event-modelling", "typescript", http="fastify")
            makefile = (repo / "Makefile").read_text()
            self.assertEqual(gate_prerequisites(makefile), GENERATED + ["check-openapi"])
            self.assertIn("# backing-service:fastify:begin\n" + f"{gate_target_name(makefile)}: check-openapi\n"
                          "# backing-service:fastify:end\n", makefile)
            self.assertTrue(gate_rule(makefile).endswith(CLOSING), gate_rule(makefile))
            # The description `make help` lists stays on `verify`, the name a developer types.
            self.assertIn(HEADING, makefile)

    def test_a_project_without_a_transport_has_no_document_check(self) -> None:
        """Hold (pin 1): the same checks with no `check-openapi` and no marker for it."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "pinned", "event-modelling", "typescript", http="none")
            makefile = (repo / "Makefile").read_text()
            self.assertEqual(gate_prerequisites(makefile), GENERATED)
            self.assertIsNone(re.search(r"^verify(-checks)?: check-openapi", makefile, re.M))
            self.assertTrue(gate_rule(makefile).endswith(CLOSING))

    def test_a_standard_python_project_runs_the_checks_without_the_model_gates(self) -> None:
        """Hold (pin 1): the standard profile has no model gates; its checks are the rest, then `check-openapi`."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "pinned", "standard", "python", http="fastapi")
            makefile = (repo / "Makefile").read_text()
            self.assertEqual(gate_prerequisites(makefile), STANDARD + ["check-openapi"])
            self.assertTrue(gate_rule(makefile).endswith(CLOSING))

    def test_answering_the_transport_with_none_leaves_a_gate_with_no_document_check(self) -> None:
        """Hold (pin 1): the `--http none` answer `./init` hands to `scripts/backing-services.py` cuts the
        transport's line, and what is left is the gate without `check-openapi`, still closing on its line."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "pinned", "event-modelling", "typescript", http="fastify")
            self.assertIn("check-openapi", gate_prerequisites((repo / "Makefile").read_text()))
            subprocess.run(["python3", "scripts/backing-services.py", "--http", "none"], cwd=repo, check=True,
                           stdout=subprocess.DEVNULL)
            makefile = (repo / "Makefile").read_text()
            self.assertEqual(gate_prerequisites(makefile), GENERATED)
            self.assertIsNone(re.search(r"^verify(-checks)?: check-openapi", makefile, re.M))
            self.assertTrue(gate_rule(makefile).endswith(CLOSING))


class WrappedGatePinnedTest(FactoryTestCase):
    def test_the_gate_refuses_while_nothing_is_confirmed_byte_for_byte(self) -> None:
        """Hold (pin 2, `NOTHING_CONFIRMED`): the rule as written, no prerequisite, and the closing line absent."""
        with tempfile.TemporaryDirectory() as directory:
            repo = adopted(Path(directory))
            makefile = (repo / "delivery/Makefile").read_text()
            self.assertIn(".PHONY: verify ci\n" + NOTHING_CONFIRMED_RULE + "ci: verify ", makefile)
            self.assertNotIn("verify: all gates passed", makefile)

    def test_a_confirmed_application_gets_the_gate_byte_for_byte(self) -> None:
        """Hold (pin 2, `GATE`): the rule as written, `check-convergence` last, the closing line."""
        with tempfile.TemporaryDirectory() as directory:
            repo = adopted(Path(directory))
            self.assertEqual(slipwai(repo, "adopt", "--confirm", "shop").returncode, 0)
            makefile = (repo / "delivery/Makefile").read_text()
            rule = f"verify: {' '.join(WRAPPED)} {HEADING}\n" + CLOSING
            self.assertIn(".PHONY: verify ci\n" + rule + "ci: verify ", makefile)
            self.assertNotIn("verify-checks", makefile)
