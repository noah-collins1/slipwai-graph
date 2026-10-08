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

from provisional_fixture import EASY_LINE, HARD_LINE, NAMES, entry, run, status
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


class ReversibilityIsReadAsS26ReadsItTest(GateCase):
    """T028: a near-miss label or a fenced line is no `Reversibility:` line to the provisional checks either."""

    def test_t028_e1_a_near_miss_label_is_no_line_so_the_entry_is_missing_one(self) -> None:
        for label in ("Reversibility :", "reversibility:"):
            line = EASY_LINE.replace("Reversibility:", label)
            self.refused(provisional(reversibility=line), "D1", "`Reversibility`", "missing")

    def test_t028_e2_a_fenced_line_is_no_line_so_the_entry_is_missing_one(self) -> None:
        self.refused(provisional(reversibility=f"```\n{EASY_LINE}\n```"), "D1", "`Reversibility`", "missing")

    def test_t028_e3_a_real_line_beside_a_fenced_one_is_the_real_one(self) -> None:
        hard = EASY_LINE.replace("easy", "hard", 1)
        self.passes(provisional(reversibility=f"{EASY_LINE}\n```\n{hard}\n```"))


def at(text: str, when: str) -> str:
    return text.replace("**When:** 2026-10-07T21:17:49Z", f"**When:** {when}")


def by(date: str) -> str:
    return f"provisional · ratify by {date}"


class RatifiedAndTheRatifyByDateTest(GateCase):
    """T030 (D205, AC-S27-20): a ratified entry is held to FR-033; the ratify-by date is `When` plus seven days, UTC."""

    def test_t030_e1_a_ratified_entry_with_hard_facts_is_refused_as_a_provisional_one_is(self) -> None:
        found = self.findings(entry(1, "ratified 2026-10-09", reversibility=HARD_LINE))
        self.assertEqual(3, len(found), found)
        self.assertTrue(all("D1" in row and "`Reversibility`" in row for row in found), found)

    def test_t030_e2_a_ratified_entry_without_a_reversibility_line_is_refused_naming_it(self) -> None:
        self.refused(entry(1, "ratified 2026-10-09"), "D1", "`Reversibility`", "missing")

    def test_t030_e3_a_reverted_entry_is_not_held_to_it(self) -> None:
        self.passes(entry(1, "reverted 2026-10-09", reversibility=HARD_LINE))
        self.passes(entry(1, "reverted 2026-10-09"))

    def test_t030_e4_a_ratify_by_date_other_than_when_plus_seven_is_refused_naming_status(self) -> None:
        for date in ("2026-10-15", "2026-10-13", "2099-12-31"):
            self.refused(provisional(status_line=by(date)), "D1", "`Status`", "2026-10-14", date)

    def test_t030_e5_the_date_is_counted_in_utc(self) -> None:
        late = at(provisional(status_line=by("2026-10-15")), "2026-10-07T23:30:00-05:00")
        self.passes(late)
        self.refused(at(provisional(), "2026-10-07T23:30:00-05:00"), "D1", "`Status`", "2026-10-15")
        self.passes(at(provisional(status_line=by("2026-10-14")), "2026-10-07"))

    def test_t030_e6_a_when_that_cannot_be_read_is_refused_naming_status(self) -> None:
        self.refused(at(provisional(), "tomorrow"), "D1", "`Status`", "`When`")

    def test_t032_e1_a_when_with_a_space_separator_or_any_offset_form_is_read(self) -> None:
        for when in ("2026-10-07 23:30:00-05:00", "2026-10-07T23:30:00-0500", "2026-10-07T23:30-05",
                     "2026-10-08T04:30:00+00:00", "2026-10-08 04:30:00Z"):
            self.passes(at(provisional(status_line=by("2026-10-15")), when))
            self.refused(at(provisional(status_line=by("2026-10-14")), when), "D1", "`Status`", "2026-10-15")

    def test_t032_e2_the_verb_reads_the_same_whens_and_refuses_what_it_cannot_read(self) -> None:
        for when, until in (("2026-10-07 23:30:00-05:00", "2026-10-15"), ("2026-10-07T23:30:00-0500", "2026-10-15"),
                            ("2026-10-07 21:17:49", "2026-10-14"), ("2026-10-07", "2026-10-14")):
            result = status("provisional", line=EASY_LINE, when=when)
            self.assertEqual((0, f"- **Status:** provisional · ratify by {until}"),
                             (result.returncode, result.stdout.splitlines()[0]), (when, result.stderr))
        for when in ("2026-10-07T25:00:00Z", "2026-10-07 soon", "2026-10-07T21:00:00+99:99"):
            result = status("provisional", line=EASY_LINE, when=when)
            self.assertEqual(2, result.returncode, (when, result.stdout))
            self.assertIn("--when", result.stderr)
