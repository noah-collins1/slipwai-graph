"""What ships: every project the factory generates, wrapped applications aside, takes the stamped `verify`.

R12 (AC-S03-29): the gate is the gate it was — the prerequisites of `verify-checks` are the ones `verify` had, in the
same order, with the same closing line, for every backend the catalog offers, with a transport and without, with a
browser app, and with several services (one gate, one `--environment` per Python service); `./init --http none` cuts
the transport's line and leaves no `check-openapi`. The starter matrix's own gates are the host's full gate; here the
Makefile each starter gets is held against what the gate ran before.
"""
from __future__ import annotations

import re
import subprocess
import tempfile

from support import FactoryTestCase
from test_add_service import add_service
from test_verify_stamp_pinned import CLOSING, STANDARD, gate_prerequisites, gate_rule

from slipwai.catalog import CATALOG

TOOLS = {
    "typescript": ["make", "git", "python3", "node", "npm"],
    "python": ["make", "git", "python3", "uv"],
    "go": ["make", "git", "python3", "go"],
    "java-quarkus": ["make", "git", "python3", "java"],
    "java-spring": ["make", "git", "python3", "java"],
}


def stamp_variable(makefile: str) -> list[str]:
    match = re.search(r"^VERIFY_STAMP := (.*)$", makefile, re.M)
    assert match, "no VERIFY_STAMP in the Makefile"
    return match.group(1).split()


def tools_asked(makefile: str) -> list[str]:
    words = stamp_variable(makefile)
    return [words[i + 1] for i, word in enumerate(words) if word == "--tool"]


def environments_asked(makefile: str) -> list[str]:
    words = stamp_variable(makefile)
    return [words[i + 1] for i, word in enumerate(words) if word == "--environment"]


class EveryStarterTakesTheStampedGateTest(FactoryTestCase):
    def assert_stamped_gate(self, makefile: str, expected: list[str]) -> None:
        self.assertEqual(len(re.findall(r"^verify:", makefile, re.M)), 1, "one rule named verify")
        self.assertEqual(len(re.findall(r"^verify-checks:(?!.*check-openapi)", makefile, re.M)), 1)
        self.assertIn("verify-stamp.py reuse", makefile)
        self.assertEqual(gate_prerequisites(makefile), expected)
        self.assertTrue(gate_rule(makefile).endswith(CLOSING), gate_rule(makefile))

    def test_every_backend_the_catalog_offers_keeps_its_prerequisites_with_and_without_a_transport(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            for backend in CATALOG["backends"]:
                for http in (None, "none"):
                    with self.subTest(backend=backend, http=http):
                        axes = {} if http is None else {"http": http}
                        repo = self.generate(directory, f"{backend}-{http or 'with'}", "standard", backend, **axes)
                        makefile = (repo / "Makefile").read_text()
                        # Only the backends that can write a document out of the app itself have a line to cut.
                        transport = http is None and backend in ("typescript", "python")
                        self.assert_stamped_gate(makefile, STANDARD + (["check-openapi"] if transport else []))
                        if transport:
                            self.assertRegex(
                                makefile,
                                r"# backing-service:[a-z-]+:begin\nverify-checks: check-openapi\n"
                                r"# backing-service:[a-z-]+:end\n",
                            )
                        else:
                            self.assertNotRegex(makefile, r"(?m)^verify(-checks)?: check-openapi")
                        self.assertEqual(tools_asked(makefile), TOOLS[backend])
                        expected_environments = ["apps/service/.venv"] if backend == "python" else []
                        self.assertEqual(environments_asked(makefile), expected_environments)

    def test_a_project_with_a_browser_app_asks_the_machine_for_node_and_keeps_its_style_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "web", "standard", "python", "react-vite", http="none")
            makefile = (repo / "Makefile").read_text()
            self.assert_stamped_gate(makefile, STANDARD + ["check-styles"])
            self.assertEqual(tools_asked(makefile), ["make", "git", "python3", "uv", "node", "npm"])

    def test_init_answering_the_transport_with_none_leaves_no_document_check_anywhere(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "cut", "event-modelling", "typescript", http="fastify")
            self.assertIn("check-openapi", (repo / "Makefile").read_text())
            subprocess.run(["python3", "scripts/backing-services.py", "--http", "none"], cwd=repo, check=True,
                           stdout=subprocess.DEVNULL)
            makefile = (repo / "Makefile").read_text()
            self.assertNotIn("check-openapi", gate_prerequisites(makefile))
            self.assertNotRegex(makefile, r"(?m)^verify(-checks)?: check-openapi")
            self.assertIn("verify-stamp.py reuse", makefile)
            self.assertTrue(gate_rule(makefile).endswith(CLOSING))

    def test_several_services_are_one_gate_with_one_environment_each(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            for flags, environments, tools in (
                ((), ["apps/service/.venv", "apps/payments/.venv"], TOOLS["python"]),
                (("--language", "go"), ["apps/service/.venv"], TOOLS["python"] + ["go"]),
            ):
                with self.subTest(added=flags):
                    repo = self.generate(directory, f"grown{len(flags)}", "standard", "python", http="none")
                    result = add_service(repo, "payments", *flags)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    makefile = (repo / "Makefile").read_text()
                    self.assert_stamped_gate(makefile, STANDARD)
                    self.assertEqual(environments_asked(makefile), environments)
                    self.assertEqual(tools_asked(makefile), tools)
