"""R13 (AC-S06-17, -18): what a project made before the scoped gate gets, and the fragment that says so.

A project generated at the last release has no `verify-scoped` and no per-deployable targets; `slipwai migrate` brings
them, and writes nothing under `verification` in `project.json`, because the obligations key is the project's own. The
fragment `changelog.d/scoped-gate.md` carries one **Catch-up.** paragraph that stands alone, since `migrate` copies it
and nothing else into a project, and it quotes the constitution template's new sentence word for word.
"""
from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path

from support import FactoryTestCase
from test_migrate import migrate
from test_replay import git, newer_factory

from slipwai.assets import ROOT
from slipwai.project.scoped_targets import HEADER
from slipwai.scaffold import NO_MAINTENANCE

FRAGMENT = ROOT / "changelog.d/scoped-gate.md"
TEMPLATES = (
    "assets/profiles/standard/.specify/presets/standard/templates/constitution-template.md",
    "assets/profiles/event-modelling/.specify/presets/event-modelling/templates/constitution-template.md",
)
NEW_SENTENCE = (
    "The branch's scoped gate MUST be green immediately before that first implementation push: it runs every check "
    "that reads a file changed since the trunk commit the branch is built on, or a tool, a variable or an ignored "
    "file that differs from the branch's last green full gate, and it is the full gate wherever it cannot tell; a "
    "check it skips is taken as passing because the trunk passed it. The full gate MUST be green at the merge root "
    "and in CI before anything lands on trunk."
)
OLD_SENTENCE = "The whole suite MUST be green immediately before that first implementation push"


def squashed(text: str) -> str:
    return " ".join(text.split())


def made_before_the_slice(repo: Path) -> None:
    """The project as the last release made it: no scoped section at the end of the `Makefile`, no script for it, and
    the root commit amended so it is the base the next migration measures against."""
    makefile = repo / "Makefile"
    text = makefile.read_text(encoding="utf-8")
    assert text.count(HEADER) == 1, "the generated Makefile ends with the scoped section"
    makefile.write_text(text.split(HEADER)[0], encoding="utf-8")
    (repo / "scripts/verify-scoped.py").unlink()
    for module in (repo / "scripts/verify_scoped").iterdir():
        module.unlink()
    (repo / "scripts/verify_scoped").rmdir()
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True, timeout=60)
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@local", *NO_MAINTENANCE,
                    "commit", "-q", "--amend", "--no-edit"], cwd=repo, check=True, timeout=60)


def catch_up_paragraphs(text: str) -> list[str]:
    return [block for block in text.split("\n\n") if block.startswith("**Catch-up.**")]


class AProjectMadeBeforeGainsTheScopedGateTest(FactoryTestCase):
    def test_a_migrated_project_has_verify_scoped_the_units_and_no_verification_key(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "product", "event-modelling", "typescript", "react-vite")
            made_before_the_slice(repo)
            before = subprocess.run(["make", "-npq", "-f", "Makefile", ".DEFAULT"], cwd=repo, text=True,
                                    capture_output=True, timeout=120).stdout
            self.assertNotIn("\nverify-scoped:", before)
            factory = newer_factory(Path(directory), "\n## A section a newer factory added\n")

            result = migrate(repo, factory)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            after = subprocess.run(["make", "-npq", "-f", "Makefile", ".DEFAULT"], cwd=repo, text=True,
                                   capture_output=True, timeout=120).stdout
            for target in ("verify-scoped", "lint-service", "typecheck-web", "test-web"):
                self.assertRegex(after, rf"(?m)^{target}:", f"{target} arrives with migrate")
            self.assertTrue((repo / "scripts/verify-scoped.py").is_file())
            self.assertTrue((repo / "scripts/verify_scoped/choose.py").is_file())
            project = json.loads((repo / "project.json").read_text(encoding="utf-8"))
            self.assertNotIn("verification", project, "the obligations key is the project's own, never written")
            self.assertEqual(git(repo, "status", "--porcelain").stdout, "")


class TheFragmentIsMinorAndItsCatchUpStandsAloneTest(FactoryTestCase):
    def setUp(self) -> None:
        self.text = FRAGMENT.read_text(encoding="utf-8")
        paragraphs = catch_up_paragraphs(self.text)
        self.assertEqual(len(paragraphs), 1, "exactly one paragraph begins **Catch-up.**")
        self.note = squashed(paragraphs[0])

    def test_the_first_line_is_minor(self) -> None:
        self.assertEqual(self.text.splitlines()[0], "MINOR")

    def test_the_note_names_the_target_the_merge_root_and_ci_and_the_obligations_key(self) -> None:
        self.assertIn("`make verify-scoped`", self.note)
        self.assertRegex(self.note, r"merge root and CI (still )?run `make verify`")
        self.assertIn("`verification.obligations`", self.note)

    def test_the_note_leaves_a_ratified_constitution_alone_and_quotes_the_templates_sentence(self) -> None:
        self.assertIn("`slipwai migrate` never touches a constitution you ratified", self.note)
        self.assertIn(OLD_SENTENCE, self.note)
        self.assertIn("nothing breaks", self.note)
        for name in TEMPLATES:
            template = squashed((ROOT / name).read_text(encoding="utf-8"))
            sentence = re.search(r"The branch's scoped gate MUST be green.*?before anything lands on trunk\.", template)
            self.assertIsNotNone(sentence, "the template carries the new sentence")
            self.assertIn(sentence.group(0) if sentence else "", self.note, "quoted in full, word for word")

    def test_both_templates_carry_the_sentence_and_the_note_quotes_it_word_for_word(self) -> None:
        for name in TEMPLATES:
            self.assertIn(NEW_SENTENCE, squashed((ROOT / name).read_text(encoding="utf-8")))
        self.assertIn(NEW_SENTENCE, self.note)
        self.assertNotIn("since the branch last passed", self.note)

    def test_the_note_stands_alone_in_one_paragraph(self) -> None:
        for reference in ("T0", "AC-S06", "D12", "above", "the page"):
            self.assertNotIn(reference, self.note)

    def test_the_fragment_says_where_the_measurement_will_be_written(self) -> None:
        self.assertIn("AC-S06-19", self.text)
        self.assertIn("quickstart.md", self.text)
