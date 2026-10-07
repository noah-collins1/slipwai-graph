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
            "or merges it. The base is the newer of local `main` and `origin/main`. Where local `main` has commits "
            "`origin/main` does not, every file those commits changed counts as changed too, so a check is skipped "
            "only on the word of a commit the forge's trunk carries. With a remote but no `origin/main` it is the "
            "full gate. With no remote at all, local `main` is the word, and only the merge root's `make verify` "
            "stands behind it. Tools, variables and the files git ignores are compared with the baseline the "
            "branch's last green full run left."
        )
        self.assertIn(said, self.page)
        self.assertNotIn("since the branch last passed", self.page)
        self.assertNotIn("trunk's own full gate passed it there", self.page)

    def test_it_is_the_full_gate_wherever_it_cannot_tell_and_what_broadens_it(self) -> None:
        self.assertIn("everywhere else it is the full gate, `make verify`", self.page)
        for broadening in ("the trunk", "`VERIFY_FORCE`", "a changed `Makefile`", "`project.json`",
                           "no check or contract claims"):
            self.assertIn(broadening, self.page)

    def test_makefile_text_that_differs_from_the_factorys_makes_every_run_the_full_gate(self) -> None:
        for said in (
            "If your `Makefile` differs from the factory's in any way",
            "a `GNUmakefile`, a `makefile` or a file named in `MAKEFILES`",
            "every scoped run is the full gate",
            "put targets of your own in a file `make verify` does not read and run "
            "them with `make -f deploy.mk <target>`",
        ):
            self.assertIn(said, self.page)

    def test_a_make_option_that_adds_text_or_conditions_is_the_full_gate_and_writes_no_stamp(self) -> None:
        for said in (
            "`--eval`, `-I`, `-e`, a variable on the command line other than `VERIFY_FORCE`",
            "a `make verify` run that way writes no stamp and no baseline",
        ):
            self.assertIn(said, self.page)

    def test_a_deployable_reaching_into_another_is_the_full_gate_and_how_to_scope_again(self) -> None:
        for said in (
            "reaches into another deployable's path or names its package",
            "share through `packages/` or a published contract",
        ):
            self.assertIn(said, self.page)

    def test_the_obligation_example_is_a_service_pair_not_a_service_and_the_web_app(self) -> None:
        self.assertIn("such as two services that agree on a queue's message", self.page)
        self.assertNotIn("a service and the web app that calls it", self.page)

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


class TheStampedPageSaysWhatCheckUxGatesRendersTest(FactoryTestCase):
    """R10 (AC-S07-14, D171 item 6): the default, the override, and when to use it."""

    def setUp(self) -> None:
        self.page = page(Layout("."))

    def test_it_names_the_override_and_when_to_set_it(self) -> None:
        said = ("set `UX_GATES_SINCE=all` when a change the scope cannot follow, a script or asset a preview loads, "
                "a browser upgrade, a reinstalled ux-gates kit (`tools/ux-gates/`), could alter a preview")
        self.assertIn(said, self.page)

    def test_it_says_where_previews_are_scoped_and_where_every_one_renders(self) -> None:
        for said in (
            "`check-ux-gates` renders only the previews a slice branch changed",
            "every preview renders on the trunk, in CI, and wherever the base cannot be found",
            "`UX_GATES_SINCE=all` renders every preview anywhere",
        ):
            self.assertIn(said, self.page)

    def test_a_ref_named_all_is_passed_by_its_full_name(self) -> None:
        self.assertIn("a ref named `all` is passed as `refs/heads/all`", self.page)


class TheStampedPageSaysAMakeCheckTargetAlwaysRunsTest(FactoryTestCase):
    """T018 (D192, AC-S07-9): the scoped gate never skips a `make check-<name>`, and `check-ux-gates` scopes there."""

    def setUp(self) -> None:
        self.page = page(Layout("."))

    def test_make_check_name_always_runs_and_the_scoped_gate_never_skips_it(self) -> None:
        self.assertIn("`make check-<name>` always runs, and the scoped gate never skips it", self.page)

    def test_make_check_ux_gates_scopes_its_previews_on_a_slice_branch_outside_ci(self) -> None:
        self.assertIn("so `make check-ux-gates` on a `slice/<id>` branch outside CI scopes previews by default",
                      self.page)


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
