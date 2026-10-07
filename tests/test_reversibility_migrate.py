"""R10 (AC-S26-16; D65): a project made before the Reversibility line gets the verb and the committed list from
`migrate`, its decisions log still passes, its owner brief is left alone, and the fragment says so."""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from reversibility_fixture import EASY, entry
from support import FactoryTestCase
from test_benchmark import clean
from test_migrate import migrate
from test_replay import git, newer_factory

from slipwai.assets import ROOT

sys.dont_write_bytecode = True

BEFORE = "063c187"  # the factory as it was before the line: no verb, no committed list
FRAGMENT = ROOT / "changelog.d/reversibility-line.md"
OWNER = ".specify/product-owner.md"


def squashed(text: str) -> str:
    return " ".join(text.split())


def catch_up_paragraphs(text: str) -> list[str]:
    return [block for block in text.split("\n\n") if block.startswith("**Catch-up.**")]


def old_factory(directory: str) -> Path:
    old = Path(directory) / "factory-before"
    old.mkdir()
    archive = subprocess.run(["git", "archive", BEFORE], cwd=ROOT, capture_output=True, check=True, timeout=120).stdout
    subprocess.run(["tar", "-x", "-C", str(old)], input=archive, check=True, timeout=120)
    return old


def make(repo: Path, target: str, *arguments: str, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["make", target, *arguments], cwd=repo, env=clean(HOME=str(repo / ".home-none")),
                          text=True, capture_output=True, timeout=timeout)


def commit(repo: Path, message: str) -> None:
    git(repo, "add", "-A")
    git(repo, "-c", "user.name=t", "-c", "user.email=t@local", "commit", "-q", "-m", message)


def made_before(directory: str) -> Path:
    """A project the factory at `BEFORE` made, with a decisions log written then (no line), committed."""
    old = old_factory(directory)
    subprocess.run([str(old / "slipwai"), "generate", "product", "--profile", "event-modelling", "--backend",
                    "typescript", "--frontend", "none", "--output", directory, "--skip-checks"],
                   check=True, capture_output=True, timeout=300)
    repo = Path(directory) / "product"
    assert not (repo / "scripts/reversibility.py").exists(), "the factory as it was had no verb"
    assert not (repo / ".slipwai/propagated").exists(), "nor a committed list"
    (repo / "specs/shop").mkdir(parents=True, exist_ok=True)
    (repo / "specs/shop/decisions.md").write_text("# Decisions\n\n" + entry(1) + "\n" + entry(2), encoding="utf-8")
    commit(repo, "a log written before the line")
    return repo


def migrated(directory: str, repo: Path) -> subprocess.CompletedProcess[str]:
    factory = newer_factory(Path(directory), "\n## A section a newer factory added\n")
    shutil.copytree(ROOT / "changelog.d", factory / "changelog.d")
    return migrate(repo, factory)


class AProjectMadeBeforeKeepsItsLogAfterMigrateTest(FactoryTestCase):
    def test_e1_migrate_brings_the_verb_and_the_list_and_the_old_log_still_passes(self) -> None:
        """Passes once T002-T008 stand: kept as the guard."""
        with tempfile.TemporaryDirectory() as directory:
            repo = made_before(directory)
            log = repo / "specs/shop/decisions.md"
            before = make(repo, "check-decisions")
            self.assertEqual(before.returncode, 0, before.stdout + before.stderr)

            result = migrated(directory, repo)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue((repo / "scripts/reversibility.py").is_file(), "the verb arrives with migrate")
            self.assertTrue((repo / ".slipwai/propagated").is_file(), "so does the committed list")
            after = make(repo, "check-decisions")
            self.assertEqual(after.returncode, 0, after.stdout + after.stderr)
            self.assertEqual(after.stdout, before.stdout, "the gate prints nothing it did not print before")
            self.assertIn("Reversibility:", (repo / OWNER).read_text(encoding="utf-8"),
                          "a brief the project never edited takes the new entry shape through the merge")
            scored = subprocess.run(
                ["python3", "-B", "scripts/reversibility.py", "--scope", "S1",
                 *[f"{key}={value}" for key, value in EASY.items()]],
                cwd=repo, text=True, capture_output=True, timeout=60)
            self.assertEqual(scored.returncode, 0, scored.stderr)
            line = scored.stdout.strip()
            self.assertTrue(line.startswith("- **Reversibility:**"), line)
            log.write_text(log.read_text(encoding="utf-8") + "\n" + entry(3, line), encoding="utf-8")
            appended = make(repo, "check-decisions")
            self.assertEqual(appended.returncode, 0, appended.stdout + appended.stderr)
            notes = squashed((repo / ".slipwai/catch-up.md").read_text(encoding="utf-8"))
            self.assertIn("`Reversibility:`", notes)
            self.assertIn("`scripts/reversibility.py`", notes)

    def test_e1_the_migrated_project_passes_its_whole_gate(self) -> None:
        """AC-S26-16: after `migrate`, `make verify` passes. Passes once written (a guard, not a RED).

        The gate is run whole: on this starter it takes about nine seconds, and it holds `lint`, `check-decisions`,
        `check-agents` and `check-speckit`, which read the files `migrate` brought (the verb, the committed list,
        the command, the owner brief). `VERIFY_FORCE=1` so a stamp from before the merge cannot stand in for it.
        """
        with tempfile.TemporaryDirectory() as directory:
            repo = made_before(directory)
            result = migrated(directory, repo)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            gate = make(repo, "verify", "VERIFY_FORCE=1", timeout=400)

            self.assertEqual(gate.returncode, 0, gate.stdout[-3000:] + gate.stderr[-3000:])
            self.assertIn("verify: all gates passed", gate.stdout)
            for check in ("lint", "check-decisions"):
                self.assertEqual(make(repo, check).returncode, 0, check)

    def test_e1_an_owner_brief_the_project_edited_keeps_its_paragraph(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = made_before(directory)
            brief = repo / OWNER
            brief.write_text(brief.read_text(encoding="utf-8") + "\n## Taste\n\nSmall, boring, mine.\n",
                             encoding="utf-8")
            commit(repo, "An owner brief the project edited")

            result = migrated(directory, repo)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("## Taste\n\nSmall, boring, mine.\n", brief.read_text(encoding="utf-8"))
            self.assertEqual(git(repo, "status", "--porcelain").stdout, "")


class TheFragmentIsMinorAndItsCatchUpStandsAloneTest(FactoryTestCase):
    def setUp(self) -> None:
        self.text = FRAGMENT.read_text(encoding="utf-8")
        paragraphs = catch_up_paragraphs(self.text)
        self.assertEqual(len(paragraphs), 1, "exactly one paragraph begins **Catch-up.**")
        self.note = squashed(paragraphs[0])

    def test_e2_the_level_is_minor_and_a_blank_line_follows(self) -> None:
        lines = self.text.splitlines()
        self.assertEqual(lines[0], "MINOR")
        self.assertEqual(lines[1], "")

    def test_e2_the_catch_up_names_the_line_the_verb_the_list_the_note_and_the_owner_brief(self) -> None:
        for words in ("`Reversibility:`", "`scripts/reversibility.py`", "`.slipwai/propagated`", "pass unchanged",
                      "`note:`", "never a refusal", "`.specify/product-owner.md`", "by hand", "keeps its own edits",
                      "`commands/cruise.md`"):
            self.assertIn(words, self.note)

    def test_e2_the_catch_up_stands_alone(self) -> None:
        for reference in ("T0", "AC-S26", "D65", "above", "R10"):
            self.assertNotIn(reference, self.note)
