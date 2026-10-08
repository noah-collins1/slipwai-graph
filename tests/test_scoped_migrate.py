"""R13 (AC-S06-17, -18): what a project made before the scoped gate gets, and the fragment that says so.

A project generated at the last release has no `verify-scoped` and no per-deployable targets; `slipwai migrate` brings
them, and writes nothing under `verification` in `project.json`, because the obligations key is the project's own. The
fragment `changelog.d/scoped-gate.md` carries one **Catch-up.** paragraph that stands alone, since `migrate` copies it
and nothing else into a project, and it quotes the constitution template's new sentence word for word.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from collections.abc import Mapping
from pathlib import Path

from support import FactoryTestCase
from test_migrate import migrate
from test_replay import git, newer_factory

from slipwai.assets import ROOT
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
# What the slice added first: the oldest commit that adds any of these is where the factory stops being "before".
SLICE_FILES = ("assets/toolkit/scripts/verify-scoped.py", "src/slipwai/project/scoped_targets.py",
               "assets/toolkit/scripts/verify_scoped")
CI_MARKERS = ("CI", "GITHUB_ACTIONS", "GITLAB_CI")
OLD_SENTENCE = "The whole suite MUST be green immediately before that first implementation push"


def squashed(text: str) -> str:
    return " ".join(text.split())


def made_by_the_factory_as_it_was(directory: str, name: str, frontend: str, added: tuple[str, ...] = (),
                                  backend: str = "typescript") -> Path:
    """A project the factory as it stood before this slice generated: `git archive` of that commit, its own
    `slipwai generate` (and `add-service` for each name in `added`), so every file is the one it wrote then."""
    old = Path(directory) / "factory-before"
    old.mkdir()
    archive = subprocess.run(["git", "archive", BEFORE or "HEAD"], cwd=ROOT, capture_output=True, check=True,
                             timeout=120).stdout
    subprocess.run(["tar", "-x", "-C", str(old)], input=archive, check=True, timeout=120)
    arguments = [str(old / "slipwai"), "generate", name, "--profile", "event-modelling", "--backend", backend,
                 "--frontend", frontend, "--output", directory, "--skip-checks"]
    subprocess.run(arguments, check=True, capture_output=True, timeout=300)
    repo = Path(directory) / name
    for service in added:
        subprocess.run([str(old / "slipwai"), "add-service", service, "--language", "python"], cwd=repo, check=True,
                       capture_output=True, timeout=300)
        git(repo, "add", "-A")
        git(repo, "-c", "user.name=t", "-c", "user.email=t@local", *NO_MAINTENANCE, "commit", "-q", "-m", service)
    return repo


def targets_of(repo: Path) -> str:
    return subprocess.run(["make", "-npq", "-f", "Makefile", ".DEFAULT"], cwd=repo, text=True, capture_output=True,
                          timeout=120).stdout


def catch_up_paragraphs(text: str) -> list[str]:
    return [block for block in text.split("\n\n") if block.startswith("**Catch-up.**")]


def factory_before() -> str | None:
    """The factory as it stood before the scoped gate: the parent of the oldest commit in this clone's history that adds
    one of the gate's files. It comes from the history every clone that runs the suite holds, never from a hash on a
    branch, so it is the same commit after a rebase and the commit before a squash; None where the clone is too
    shallow to hold it, or the history never adds the files."""
    added = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H", "--", *SLICE_FILES], cwd=ROOT, text=True,
                           capture_output=True, check=False, timeout=60).stdout.split()
    if not added:
        return None
    parent = subprocess.run(["git", "rev-parse", "--verify", "-q", f"{added[-1]}^{{commit}}^"], cwd=ROOT, text=True,
                            capture_output=True, check=False, timeout=60)
    return parent.stdout.strip() or None


def absence(found: str | None, environment: Mapping[str, str]) -> tuple[str, str] | None:
    """What a missing base means: `("fail", why)` under a CI marker, where nothing may pass by being skipped, and
    `("skip", why)` on a machine whose clone is shallow; None where there is a base."""
    if found is not None:
        return None
    why = "the factory as it stood before the scoped gate is not in this clone's history"
    return ("fail" if any(environment.get(marker) for marker in CI_MARKERS) else "skip", why)


BEFORE = factory_before()


class AProjectMadeBeforeGainsTheScopedGateTest(FactoryTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        missing = absence(BEFORE, os.environ)
        if missing is not None and missing[0] == "fail":
            raise AssertionError(missing[1] + ": the migrate example would pass by being skipped")
        if missing is not None:
            raise unittest.SkipTest(missing[1])

    def migrated(self, directory: str, frontend: str, added: tuple[str, ...], units: tuple[str, ...],
                 backend: str = "typescript") -> Path:
        repo = made_by_the_factory_as_it_was(directory, "product", frontend, added, backend)
        before = targets_of(repo)
        self.assertNotIn("\nverify-scoped:", before)
        self.assertFalse((repo / "scripts/verify_scoped").exists(), "the factory as it was had no such scripts")
        root = git(repo, "rev-parse", "HEAD").stdout.strip()
        factory = newer_factory(Path(directory), "\n## A section a newer factory added\n")
        shutil.copytree(ROOT / "changelog.d", factory / "changelog.d")  # the fragments are the unreleased entry

        result = migrate(repo, factory)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        after = targets_of(repo)
        for target in ("verify-scoped", *units):
            self.assertRegex(after, rf"(?m)^{target}:", f"{target} arrives with migrate")
        for module in ("choose", "record", "rules", "table", "__init__"):
            self.assertTrue((repo / f"scripts/verify_scoped/{module}.py").is_file(), module)
        self.assertTrue((repo / "scripts/verify-scoped.py").is_file())
        self.assertTrue((repo / "scripts/verify_scoped/rules.json").is_file(), "rules.json arrives with the Makefile")
        project = json.loads((repo / "project.json").read_text(encoding="utf-8"))
        self.assertNotIn("verification", project, "the obligations key is the project's own, never written")
        self.assertEqual(git(repo, "status", "--porcelain").stdout, "")
        history = git(repo, "merge-base", "--is-ancestor", root, "HEAD", check=False)
        self.assertEqual(history.returncode, 0, "the migration sits on the project's own history")
        note = squashed((repo / ".slipwai/catch-up.md").read_text(encoding="utf-8"))
        (paragraph,) = catch_up_paragraphs(FRAGMENT.read_text(encoding="utf-8"))
        owed = squashed(paragraph).removeprefix("**Catch-up.**").strip()
        self.assertIn(owed, note, "the Catch-up paragraph reaches the project, whole")
        return repo

    def test_a_project_the_last_factory_made_gains_the_scoped_gate_and_its_catch_up_note(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.migrated(directory, "react-vite", (), ("lint-service", "typecheck-web", "test-web"))

    def test_the_same_for_two_python_services(self) -> None:
        # Two Python services, as the name says. A TypeScript project with a service added by hand now conflicts on the
        # `mutation` recipe under `migrate` (S41 rewrote the line `add-service` appends beside); `test_stryker_migrate`
        # holds that conflict and the fragment's words for it.
        with tempfile.TemporaryDirectory() as directory:
            self.migrated(directory, "none", ("billing",), ("lint-service", "lint-billing", "test-billing"), "python")


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

    def test_the_note_says_the_makefile_is_held_by_its_text_in_the_words_d140_gives(self) -> None:
        for words in (
            "`make verify-scoped` scopes only the `Makefile` the factory wrote.",
            "or if make would also read a `GNUmakefile`, a `makefile` or a file named in `MAKEFILES`, every scoped run "
            "is the full gate, `make verify`, and says so on its first line, until the file is the factory's text "
            "again.",
            "`slipwai migrate` carries the factory's changes into your `Makefile` but never makes your edits count as "
            "the factory's.",
            "To keep scoping, put targets of your own in a file `make verify` does not read and run them with "
            "`make -f deploy.mk <target>`. Your merge root and CI run `make verify` either way.",
        ):
            self.assertIn(words, self.note)
        retired = ("set it on the rule", "which runs every time with no recorded inputs", "check run on every")
        for words in retired:
            self.assertNotIn(words, self.note)

    def test_the_note_stands_alone_in_one_paragraph(self) -> None:
        for reference in ("T0", "AC-S06", "D12", "above", "the page"):
            self.assertNotIn(reference, self.note)

    def test_the_fragment_carries_the_measurement_with_its_commands_and_machine(self) -> None:
        for words in ("make verify-scoped", "VERIFY_FORCE=1 make verify", "median", "nproc", "three runs each"):
            self.assertIn(words, self.text)


class TheMigrateExampleCannotPassBySkippingTest(unittest.TestCase):
    def test_the_base_is_found_in_this_clone_and_lacks_the_gate(self) -> None:
        found = factory_before()
        self.assertIsNotNone(found, "no base: the history here never adds the gate, or the clone is shallow")
        listed = subprocess.run(["git", "ls-tree", "-r", "--name-only", found or "", "--", *SLICE_FILES], cwd=ROOT,
                                text=True, capture_output=True, check=False, timeout=60).stdout
        self.assertEqual(listed.strip(), "", "the base already has the scoped gate")
        ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", found or "", "HEAD"], cwd=ROOT, check=False,
                                  timeout=60)
        self.assertEqual(ancestor.returncode, 0)

    def test_no_base_fails_under_a_ci_marker_and_skips_outside_one(self) -> None:
        for marker in CI_MARKERS:
            self.assertEqual((absence(None, {marker: "true"}) or ("",))[0], "fail", marker)
        self.assertEqual((absence(None, {}) or ("",))[0], "skip")
        self.assertEqual((absence(None, {"CI": ""}) or ("",))[0], "skip")
        self.assertIsNone(absence("abc123", {"CI": "true"}))

    def test_sweep_no_scoped_test_skips_on_a_condition_a_ci_clone_always_or_never_meets(self) -> None:
        """Every skip in the scoped modules is this module's, and `absence` makes it fail under a CI marker."""
        found = {}
        for path in sorted((ROOT / "tests").glob("test_*scoped_*.py")) + [ROOT / "tests/scoped_fixture.py"]:
            hits = re.findall(r"skipUnless|skipIf|skipTest|SkipTest|unittest\.skip\b", path.read_text(encoding="utf-8"))
            if hits and path.name != "test_scoped_migrate.py" and path.name != Path(__file__).name:
                found[path.name] = hits
        self.assertEqual(found, {})
