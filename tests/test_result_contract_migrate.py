"""R10 (AC-S14-17): what a project made before the result contract gets, and the fragment that says so.

A project made by the factory as it stood at `c3c760b` has no `scripts/hand_backs.py`, no `docs/result-contract.md` and
no result-contract paragraph in its agents; `slipwai migrate` brings them, re-projects the agent files, and the
project's own decision and demo records, written before there was a hand-back, are not touched and still pass.
Both layouts: the root, and an adopted repository whose method lives under `delivery/`. The fragment
`changelog.d/result-contract.md` has one **Catch-up.** paragraph that stands alone, since `migrate` copies it and
nothing else into a project.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from hand_backs_fixture import decision
from support import FactoryTestCase
from test_adopt import node_repository
from test_migrate import migrate
from test_replay import git, newer_factory

from slipwai.assets import ROOT

BEFORE = "c3c760b"  # the commit before the result contract: the last factory that wrote no hand-back
FRAGMENT = ROOT / "changelog.d/result-contract.md"
HEADING = "## What you hand back"
SECTION = "## What every delegate hands back"
OWN = "specs/f"


def squashed(text: str) -> str:
    return " ".join(text.split())


def catch_up_paragraphs(text: str) -> list[str]:
    return [block for block in text.split("\n\n") if block.startswith("**Catch-up.**")]


def old_factory(directory: str) -> Path:
    """`git archive` of the commit before the slice, so every file the old project has is the one it wrote then."""
    old = Path(directory) / "factory-before"
    old.mkdir()
    archive = subprocess.run(["git", "archive", BEFORE], cwd=ROOT, capture_output=True, check=True, timeout=120).stdout
    subprocess.run(["tar", "-x", "-C", str(old)], input=archive, check=True, timeout=120)
    return old


def own_records(repo: Path) -> None:
    """What a project wrote before there was a hand-back: a decision log, and a slice with no `hand-backs.md`."""
    (repo / OWN / "slices/S1").mkdir(parents=True)
    (repo / OWN / "decisions.md").write_text("# Decisions\n\n" + "".join(decision(n) for n in (1, 2, 3)),
                                             encoding="utf-8")
    (repo / OWN / "slices/S1/spec.md").write_text("# S1\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "-c", "user.name=t", "-c", "user.email=t@local", "commit", "-q", "-m", "records")


def specs_digest(repo: Path) -> dict[str, str]:
    return {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((repo / "specs").rglob("*")) if p.is_file()}


def install_claude(repo: Path) -> None:
    (repo / ".specify").mkdir(exist_ok=True)
    (repo / ".specify/integration.json").write_text(json.dumps({"installed_integrations": ["claude"]}))


class AProjectMadeBeforeGainsTheResultContractTest(FactoryTestCase):
    def migrated(self, directory: str, repo: Path, base: str, make: list[str]) -> Path:
        """Migrate `repo` with a newer factory and check what arrived; `base` is where the method lives."""
        prefix = "" if not base else base + "/"
        for name in ("scripts/hand_backs.py", "docs/result-contract.md"):
            self.assertFalse((repo / prefix / name).exists(), f"{name}: the factory as it was had no such file")
        install_claude(repo)
        own_records(repo)
        before = specs_digest(repo)
        old_checker = (repo / prefix / "scripts/check-decisions.py").read_text(encoding="utf-8")
        factory = newer_factory(Path(directory), "\n## A section a newer factory added\n")
        shutil.copytree(ROOT / "changelog.d", factory / "changelog.d")  # the fragments are the unreleased entry

        result = migrate(repo, factory)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for name in ("scripts/hand_backs.py", "docs/result-contract.md"):
            self.assertTrue((repo / prefix / name).is_file(), f"{name} arrives with migrate")
        self.assertNotEqual((repo / prefix / "scripts/check-decisions.py").read_text(encoding="utf-8"), old_checker)
        self.assertIn("--hand-back", (repo / prefix / "scripts/check-decisions.py").read_text(encoding="utf-8"))
        gaps = (repo / prefix / "agents/drive-gaps.md").read_text(encoding="utf-8")
        self.assertIn(HEADING, gaps)
        self.assertIn("`drive-gaps`", gaps.split(HEADING)[1])
        projected = (repo / ".claude/agents/drive-gaps.md").read_text(encoding="utf-8")
        self.assertIn(HEADING, projected, "the Claude Code projection was re-derived")
        for command in ("drive", "cruise"):
            self.assertIn("result-contract", (repo / prefix / f"commands/{command}.md").read_text(encoding="utf-8"))
        self.assertIn(SECTION, (repo / prefix / "commands/drive.md").read_text(encoding="utf-8"))
        self.assertEqual(specs_digest(repo), before, "the project's records are byte for byte what they were")
        self.assertEqual(git(repo, "status", "--porcelain").stdout, "")
        gate = subprocess.run(make, cwd=repo, text=True, capture_output=True, timeout=120)
        self.assertEqual(gate.returncode, 0, gate.stdout + gate.stderr)
        self.assertNotIn("hand-backs", gate.stdout + gate.stderr, "a slice with no hand-backs.md is not refused")
        note = squashed((repo / ".slipwai/catch-up.md").read_text(encoding="utf-8"))
        (paragraph,) = catch_up_paragraphs(FRAGMENT.read_text(encoding="utf-8"))
        owed = squashed(paragraph).removeprefix("**Catch-up.**").strip()
        self.assertIn(owed, note, "the paragraph reaches the project")
        return repo

    def test_e1_a_project_made_at_the_root_gains_the_result_contract_and_its_records_still_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            old = old_factory(directory)
            subprocess.run([str(old / "slipwai"), "generate", "product", "--profile", "event-modelling", "--backend",
                            "typescript", "--frontend", "none", "--output", directory, "--skip-checks"],
                           check=True, capture_output=True, timeout=300)
            self.migrated(directory, Path(directory) / "product", "", ["make", "check-decisions"])

    def test_e2_an_adopted_repository_gains_the_same_under_delivery(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            old = old_factory(directory)
            repo = node_repository(Path(directory))
            adopt = subprocess.run([str(old / "slipwai"), "adopt", "--yes"], cwd=repo, text=True, capture_output=True,
                                   stdin=subprocess.DEVNULL, timeout=300)
            self.assertEqual(adopt.returncode, 0, adopt.stderr)
            self.migrated(directory, repo, "delivery", ["make", "-f", "delivery/Makefile", "check-decisions"])


class TheFragmentIsMinorAndItsCatchUpStandsAloneTest(FactoryTestCase):
    def setUp(self) -> None:
        self.text = FRAGMENT.read_text(encoding="utf-8")
        paragraphs = catch_up_paragraphs(self.text)
        self.assertEqual(len(paragraphs), 1, "exactly one paragraph begins **Catch-up.**")
        self.note = squashed(paragraphs[0])

    def test_e3_the_first_line_is_minor(self) -> None:
        self.assertEqual(self.text.splitlines()[0], "MINOR")

    def test_e3_the_note_asks_nothing_of_existing_logs_and_does_not_refuse_a_slice_without_hand_backs(self) -> None:
        for words in ("decision log", "demo log", "nothing is asked", "hand-backs.md", "not refused"):
            self.assertIn(words, self.note.lower())
        self.assertNotIn("make agents", self.note, "migrate re-projects the agent files itself; nobody is asked to")

    def test_e3_the_note_stands_alone_in_one_paragraph(self) -> None:
        for reference in ("T0", "AC-S14", "D13", "above", "the page", "R10"):
            self.assertNotIn(reference, self.note)

    def test_e3_the_lead_says_what_agents_hand_back_where_it_is_kept_and_the_benchmark_line(self) -> None:
        lead = squashed(self.text.split("**Catch-up.**")[0])
        for words in ("result-contract", "hand-backs.md", "make benchmark", "check-decisions"):
            self.assertIn(words, lead)
