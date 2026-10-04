"""R5 of S05-xdist: the words are true — the gates page says what the mark does and what each runner already does,
and the changelog fragment's catch-up note stands alone.

Generation alone: the page is read from a generated project, the fragment from `changelog.d/`.
"""
from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

from support import FactoryTestCase, commit_all
from test_candidates import adopted, slipwai

from slipwai.assets import ROOT
from slipwai.catalog import CATALOG

# What each backend's runner already does, in the words the page uses; a page names a runner only where the
# project has the backend.
RUNNERS = {
    "typescript": "Vitest runs test files in parallel, by file",
    "go": "`go test` runs packages in parallel, by package",
    "java": "Maven's Surefire runs tests one at a time",
}
FAMILY = {"typescript": "typescript", "python": "python", "go": "go", "java-quarkus": "java", "java-spring": "java"}
MARK_WORDS = ("parallelSafe", "-n auto --maxprocesses 4", "A missing mark is serial", "`false`")


def squashed(text: str) -> str:
    return " ".join(text.split())


class TheGatesPageSaysWhatTheMarkDoes(FactoryTestCase):
    def page(self, parent: str, backend: str) -> str:
        repo = self.generate(parent, "shop", language=backend)
        return squashed((repo / "docs/gates.md").read_text(encoding="utf-8"))

    def test_a_python_projects_page_carries_the_marks_paragraph(self) -> None:
        with tempfile.TemporaryDirectory() as parent:
            page = self.page(parent, "python")
            for word in MARK_WORDS:
                self.assertIn(word, page)
            self.assertIn("`\"parallelSafe\": true`, which every new project has", page)
            self.assertIn("after the `\"target\"` line", page)
            self.assertIn("written twice is serial", page)
            self.assertIn("Only the JSON `true` turns it on", page)
            self.assertIn("a string `\"true\"` is serial", page)
            for sharing in ("a file", "a port", "a database", "module-level state"):
                self.assertIn(sharing, page)

    def test_each_backend_says_what_its_runner_does_and_nothing_of_one_the_project_lacks(self) -> None:
        for backend in CATALOG["backends"]:
            with self.subTest(backend=backend), tempfile.TemporaryDirectory() as parent:
                page = self.page(parent, backend)
                for family, sentence in RUNNERS.items():
                    if family == FAMILY[backend]:
                        self.assertIn(sentence, page)
                    else:
                        self.assertNotIn(sentence, page)
                        self.assertNotIn("Surefire" if family == "java" else sentence, page)

    def test_a_project_with_several_backends_names_each_runner_once(self) -> None:
        with tempfile.TemporaryDirectory() as parent:
            repo = self.generate(parent, "shop", language="typescript", frontend="react-vite")
            for name, language in (("second", "go"), ("third", "java")):
                added = subprocess.run([str(ROOT / "slipwai"), "add-service", name, "--language", language],
                                       cwd=repo, capture_output=True, text=True, timeout=120)
                self.assertEqual(added.returncode, 0, added.stderr)
                commit_all(repo, f"add {name}")
            page = squashed((repo / "docs/gates.md").read_text(encoding="utf-8"))
            for sentence in RUNNERS.values():
                self.assertEqual(page.count(sentence), 1, sentence)

    def test_a_project_with_no_python_service_says_what_the_mark_does_and_that_it_does_nothing_yet(self) -> None:
        """G1 (D105): the key is written whatever the backend, so the page says one sentence of it."""
        for backend in CATALOG["backends"]:
            if FAMILY[backend] == "python":
                continue
            with self.subTest(backend=backend), tempfile.TemporaryDirectory() as parent:
                page = self.page(parent, backend)
                self.assertIn("`\"parallelSafe\": true`", page)
                self.assertIn("changes nothing until a Python service is added", page)
                self.assertNotIn("The other runners", page)

    def test_a_python_project_with_another_backend_still_says_the_other_runners(self) -> None:
        with tempfile.TemporaryDirectory() as parent:
            repo = self.generate(parent, "shop", language="python")
            added = subprocess.run([str(ROOT / "slipwai"), "add-service", "second", "--language", "go"],
                                   cwd=repo, capture_output=True, text=True, timeout=120)
            self.assertEqual(added.returncode, 0, added.stderr)
            page = squashed((repo / "docs/gates.md").read_text(encoding="utf-8"))
            self.assertIn("The other runners", page)
            self.assertNotIn("changes nothing until a Python service is added", page)

    def test_the_sentence_on_false_says_the_mark_needs_the_plugin(self) -> None:
        """G3 (D105): a service that removed `pytest-xdist` fails on an argument error, so say what the mark needs."""
        with tempfile.TemporaryDirectory() as parent:
            page = self.page(parent, "python")
            self.assertIn("needs `pytest-xdist` in each Python service's development tools", page)

    def test_hold_an_adopted_repositorys_page_gains_nothing_about_a_stamp(self) -> None:
        """A hold: the adopted page may carry the mark's words, never the stamp's."""
        with tempfile.TemporaryDirectory() as directory:
            repo = adopted(Path(directory))
            self.assertEqual(slipwai(repo, "adopt", "--confirm", "shop").returncode, 0)
            page = (repo / "delivery/docs/gates.md").read_text(encoding="utf-8")
            for word in ("stamp", "VERIFY_FORCE"):
                self.assertNotIn(word, page)


class TheFragmentsCatchUpNoteStandsAlone(FactoryTestCase):
    def test_the_fragment_is_minor_and_its_one_catch_up_paragraph_names_the_line(self) -> None:
        text = (ROOT / "changelog.d/xdist.md").read_text(encoding="utf-8")
        self.assertEqual(text.splitlines()[0], "MINOR")
        paragraphs = [p for p in re.split(r"\n\s*\n", text) if p.startswith("**Catch-up.**")]
        self.assertEqual(len(paragraphs), 1)
        note = squashed(paragraphs[0]).lower()
        self.assertIn("a project made before", note)
        self.assertIn("stays serial", note)
        self.assertIn('"parallelsafe": true', note)
        self.assertIn("make verify", note)

    def test_the_fragment_says_what_the_gate_does_the_cap_the_pin_and_each_runner(self) -> None:
        text = squashed((ROOT / "changelog.d/xdist.md").read_text(encoding="utf-8"))
        for words in ("-n auto --maxprocesses 4", "pytest-xdist==3.8.0", "integration", "never", "Vitest", "`go test`",
                      "Surefire"):
            self.assertIn(words, text)

    def paragraph(self) -> str:
        text = (ROOT / "changelog.d/xdist.md").read_text(encoding="utf-8")
        return squashed([p for p in re.split(r"\n\s*\n", text) if p.startswith("**Catch-up.**")][0])

    def test_the_note_says_where_the_line_goes_and_what_twice_does(self) -> None:
        """T014: where `generate` writes it, so a later `migrate` meets the same line in the same place."""
        note = self.paragraph()
        self.assertIn('right after the `"target"` line', note)
        self.assertIn("written twice is serial", note)

    def test_the_note_says_what_to_do_when_migrate_stops_on_a_services_lock(self) -> None:
        """T015: a project with a dependency of its own meets a conflict on `uv.lock`."""
        note = self.paragraph()
        for words in ("apps/<service>/uv.lock", "either side", "uv lock --project apps/<service>", "git add",
                      "commit", "once by hand", "a dependency of its own, dev or not"):
            self.assertIn(words, note)
