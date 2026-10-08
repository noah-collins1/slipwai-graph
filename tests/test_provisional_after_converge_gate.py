"""S27's after-converge gate gaps (D204-D206, AC-S27-19..21): the paths a provisional entry may not write to, the
ratified entry held like a provisional one, the ratify-by date, and the reading a lone `Revert:` leaves unchanged.

Each case writes a log into a scratch project holding the three toolkit scripts and runs the gate as a `python3 -B`
subprocess, the way a generated project holds it.
"""
from __future__ import annotations

import ast
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path, PurePosixPath
from typing import Any

from provisional_fixture import EASY_LINE, NAMES, entry, run
from reversibility_fixture import SCRIPTS, scratch

from slipwai.assets import ROOT

sys.dont_write_bytecode = True

PROVISIONAL = "provisional · ratify by 2026-10-14"


def writing(path: str, text: str) -> str:
    """`text` with its `Written to` line naming `path` (a whole value, backticks and all, if it has any)."""
    value = path if "`" in path else f"`{path}`"
    return text.replace("- **Written to:** `README.md`", f"- **Written to:** {value}")


def gate(log: str) -> subprocess.CompletedProcess[str]:
    """The gate over `log` in a scratch project that holds every path a `Written to` line names (it must exist);
    `.github` is a directory."""
    with tempfile.TemporaryDirectory() as directory:
        repo = scratch(directory, log, names=NAMES, listed=("scripts/check-decisions.py",))
        for name in re.findall(r"^- \*\*Written to:\*\* (.*)$", log, re.M):
            for path in re.findall(r"`([^`]+)`", name):
                if path == ".github":
                    (repo / path).mkdir(exist_ok=True)
                elif not (repo / path).exists():
                    (repo / path).parent.mkdir(parents=True, exist_ok=True)
                    (repo / path).write_text("x\n", encoding="utf-8")
        return run(repo, "check-decisions")


def provisional(number: int = 1, **keywords: str | None) -> str:
    fields: dict[str, str | None] = {"status_line": PROVISIONAL, "revert": "own", "reversibility": EASY_LINE,
                                     **keywords}
    return entry(number, **fields)  # type: ignore[arg-type]


class GateCase(unittest.TestCase):
    def findings(self, log: str) -> list[str]:
        result = gate(log)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        return [row for row in result.stderr.splitlines() if row.startswith("  ")]

    def passes(self, log: str) -> None:
        result = gate(log)
        self.assertEqual((0, ""), (result.returncode, result.stderr), result.stdout)

    def refused(self, log: str, *words: str) -> None:
        found = self.findings(log)
        self.assertEqual(1, len(found), found)
        for word in words:
            self.assertIn(word, found[0])


class WrittenToIsNotAGateTest(GateCase):
    """T027 (D204, AC-S27-19): `Written to` is read for a path a person must see change, whatever the facts say."""

    def test_t027_e1_a_workflow_a_control_and_a_gate_configuration_are_each_refused_naming_entry_and_path(self) -> None:
        for path in (".github/workflows/verify.yml", ".gitea/workflows/ci.yml", ".gitlab-ci.yml", "Makefile",
                     "scripts/other.py", "delivery/scripts/x.py", ".claude/settings.json", "tools/a",
                     "biome.jsonc", "apps/service/tsconfig.json", "apps/service/pyproject.toml",
                     "apps/service/pom.xml", "apps/service/config/checkstyle.xml", "apps/service/go.mod"):
            for text in (provisional(), entry(1, "ratified 2026-10-09", reversibility=EASY_LINE)):
                self.refused(writing(path, text), "D1", f"`{path}`", "`Written to`")

    def test_t027_e2_a_declared_no_is_not_enough(self) -> None:
        workflow = ".github/workflows/verify.yml"
        self.refused(writing(workflow, provisional()), f"`{workflow}`", "`Written to`")

    def test_t027_e3_a_directory_holding_a_protected_path_is_refused_and_one_finding_names_every_path(self) -> None:
        self.refused(writing(".github", provisional()), "D1", "`.github`")
        self.refused(writing("`biome.jsonc`, `README.md`, `Makefile`", provisional()), "`biome.jsonc`", "`Makefile`")

    def test_t027_e4_ordinary_files_and_a_standing_entry_pass(self) -> None:
        for path in ("README.md", "src/app.ts", "docs/gates.md", "apps/service/src/config.ts"):
            self.passes(writing(path, provisional()))
        self.passes(writing(".github/workflows/verify.yml", entry(1)))
        self.passes(writing("biome.jsonc", entry(1, "reverted 2026-10-09")))


def provisional_module() -> Any:
    spec = importlib.util.spec_from_file_location("provisional_under_test", SCRIPTS / "provisional.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# What a starter ships that no generated gate reads: held here so a new shipped file has to be sorted, one way or
# the other, by whoever adds it.
NOT_A_GATE_INPUT = {"openapi.json", "openapi.yaml", "docker-compose.yml", ".env.example", ".gitattributes",
                    ".gitignore", "LICENSE", "renovate.json", "project.json", "Procfile", "project.toml",
                    "application.properties", "mvnw", "mvnw.cmd", "init", ".gitkeep", "NOTICE"}
SOURCE_SUFFIXES = {".ts", ".tsx", ".py", ".go", ".java", ".md", ".svg", ".css", ".html", ".sql", ".js", ".tf",
                   ".tfvars", ".grit"}
NOT_SCANNED = {"specs", "delivery", "skills", "commands", "agents", "docs", ".claude", ".specify", "scripts",
               "node_modules", ".git", "infra", ".slipwai"}


def shipped_files(directory: Path, backend: str) -> set[str]:
    """Every file of a generated project that is not source, a document or the toolkit, by relative path."""
    subprocess.run([str(ROOT / "slipwai"), "generate", "p", "--profile", "standard", "--backend", backend,
                    "--frontend", "react-vite", "--target", "aws", "--skip-checks", "--no-install", "--output",
                    str(directory)], check=True, capture_output=True, text=True, encoding="utf-8")
    base = directory / "p"
    return {path.relative_to(base).as_posix() for path in base.rglob("*") if path.is_file()
            and not NOT_SCANNED & set(path.relative_to(base).parts[:-1])
            and path.suffix not in SOURCE_SUFFIXES}


class TheClosedListIsHeldAgainstWhatTheStartersShipTest(unittest.TestCase):
    """T027: every configuration file a starter ships is on the list or named here as no gate's input."""

    def test_t027_e5_every_shipped_file_of_every_backend_is_a_gate_input_or_said_not_to_be(self) -> None:
        module = provisional_module()
        catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
        unsorted: set[str] = set()
        with tempfile.TemporaryDirectory() as directory:
            for backend in catalog["backends"]:
                shipped = shipped_files(Path(directory) / backend, backend)
                self.assertIn(".github/workflows/verify.yml", shipped, backend)
                unsorted |= {path for path in shipped if not module.protected(path)
                             and PurePosixPath(path).name not in NOT_A_GATE_INPUT}
        self.assertEqual(set(), unsorted, "a shipped file neither on provisional.py's list nor in NOT_A_GATE_INPUT")

    def test_t027_e6_the_two_sorts_do_not_overlap(self) -> None:
        module = provisional_module()
        self.assertEqual([], [name for name in NOT_A_GATE_INPUT if module.protected(name)])

    def test_t027_e7_every_control_path_the_runner_parks_on_is_refused_at_either_layout(self) -> None:
        tree = ast.parse((SCRIPTS / "agents/cruise.py").read_text(encoding="utf-8"))
        assigned = next(node for node in ast.walk(tree) if isinstance(node, ast.Assign)
                        and getattr(node.targets[0], "id", "") == "CONTROL_PATHS")
        source = ast.unparse(assigned.value)
        module = provisional_module()
        for delivery in ("delivery", "."):
            controls = eval(source, {"DELIVERY": PurePosixPath(delivery), "ROOT": PurePosixPath(".")})  # noqa: S307
            self.assertGreaterEqual(len(controls), 7)
            for control in controls:
                name = control.as_posix()
                self.assertTrue(module.protected(name), name)
                self.assertTrue(module.protected(name + "/inside.txt") or name.endswith((".json", "Makefile")), name)
