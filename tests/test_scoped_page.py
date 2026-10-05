"""R13 (AC-S06-18, D124 item 3): the gates page says what the scoped gate does, stamped or adopted.

The stamped page has the scoped paragraph: where `make verify-scoped` scopes, where it is the full gate, what broadens
it, the baseline, the obligations key with its default and when to declare one, and what `-j` does to it. An adopted
repository's page has one sentence, because its scoped target is the full gate, and no word about a stamp.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from support import FactoryTestCase
from test_candidates import adopted, slipwai

from slipwai.layout import Layout
from slipwai.scaffold import project_files
from slipwai.selection import Selection
from slipwai.services import default_apps

NO_RECORD = "this layout has no verification-dependency record yet"


def squashed(text: str) -> str:
    return " ".join(text.split())


def page(layout: Layout) -> str:
    apps = default_apps("typescript", "none", Selection({"http": "fastify"}))
    name = "delivery/docs/gates.md" if layout.moved else "docs/gates.md"
    return squashed(project_files("same", "event-modelling", "none", apps, layout)[name])


class TheStampedPageSaysWhatTheScopedGateDoesTest(FactoryTestCase):
    def setUp(self) -> None:
        self.page = page(Layout("."))

    def test_it_scopes_on_a_slice_branch_with_a_usable_base_outside_ci(self) -> None:
        self.assertIn("`make verify-scoped` runs only the checks whose inputs changed", self.page)
        self.assertIn("`slice/<id>` branch with a usable base, outside CI", self.page)

    def test_the_first_sentences_name_what_files_and_what_tools_variables_and_ignored_files_meet(self) -> None:
        said = (
            "`make verify-scoped` runs only the checks whose inputs changed, and prints a line for each check, "
            "run or skipped, with the reason. It compares two things. Files, committed or not, are compared "
            "with the trunk commit the branch is built on, the one its last line names "
            "(`compared with `main` at <short>`); that commit moves when the branch is rebased onto the trunk "
            "or merges it, and a check it skips is taken as passing because the trunk's own full gate passed it "
            "there. Tools, variables and the files git ignores are compared with the baseline the branch's "
            "last green full run left."
        )
        self.assertIn(said, self.page)
        self.assertNotIn("since the branch last passed", self.page)

    def test_it_is_the_full_gate_wherever_it_cannot_tell_and_what_broadens_it(self) -> None:
        self.assertIn("everywhere else it is the full gate, `make verify`", self.page)
        for broadening in ("the trunk", "`VERIFY_FORCE`", "a changed `Makefile`", "`project.json`",
                           "no check or contract claims"):
            self.assertIn(broadening, self.page)

    def test_the_baseline_sits_beside_the_stamp_is_written_by_a_green_full_run_and_removed_by_any(self) -> None:
        self.assertIn("baseline beside the stamp", self.page)
        self.assertIn("written by a green full run on a `slice/<id>` branch", self.page)
        self.assertIn("removed by any full run", self.page)

    def test_the_obligations_key_has_its_default_and_one_sentence_on_when_to_declare_one(self) -> None:
        self.assertIn("`verification.obligations` in `project.json`", self.page)
        self.assertIn("default is none", self.page)
        self.assertIn("Declare one when", self.page)

    def test_dash_j_runs_the_chosen_checks_at_once_as_it_does_for_verify(self) -> None:
        said = "`make -j verify-scoped` runs the chosen checks at the same time, as `make -j verify` does"
        self.assertIn(said, self.page)


class AnUnstampedPageHasTheOneSentenceAndNothingOfAStampTest(FactoryTestCase):
    def check(self, text: str, command: str) -> None:
        self.assertIn(f"`{command} verify-scoped` is the full gate: {NO_RECORD}", text)
        self.assertEqual(text.count("verify-scoped"), 1, "one sentence and no paragraph")
        for word in ("stamp", "baseline", "VERIFY_FORCE", "ci.branch", "CI=1"):
            self.assertNotIn(word, text)

    def test_a_moved_layouts_page(self) -> None:
        self.check(page(Layout("delivery")), "make -f delivery/Makefile")

    def test_an_adopted_repositorys_page(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = adopted(Path(directory))
            self.assertEqual(slipwai(repo, "adopt", "--confirm", "shop").returncode, 0)
            text = squashed((repo / "delivery/docs/gates.md").read_text(encoding="utf-8"))
            self.check(text, "make -f delivery/Makefile")
