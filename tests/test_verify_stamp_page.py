"""C7 and the page after the adversary pass (AC-S03-40, -41; D83 items 1, 3, 9, 12, 14).

A project whose gate is not stamped has a gates page with nothing of a stamp in it, and a project whose gate is
stamped has a page whose every sentence that tells a developer to do something is followed as written, through the
generated project's own `make verify` with the fixture's stand-in tools.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from stamp_fixture import StampTestCase, git
from support import FactoryTestCase
from test_candidates import adopted, slipwai

from slipwai.assets import ROOT
from slipwai.layout import Layout
from slipwai.project.scoped_targets import adopted_scoped_sentence
from slipwai.scaffold import project_files
from slipwai.selection import Selection
from slipwai.services import default_apps

INTRO_END = "explicit end-of-phase/CI operations, not hidden costs in every local increment.\n\n"


def squashed(text: str) -> str:
    return " ".join(text.split())


class AnUnstampedProjectsPageSaysNothingOfAStampTest(FactoryTestCase):
    def assert_page_is_the_one_it_was(self, page: str) -> None:
        for word in ("stamp", "VERIFY_FORCE", "ci.branch", "CI=1"):
            self.assertNotIn(word, page)
        # R13's one sentence (`test_scoped_page.py`) sits between those two paragraphs
        sentence = adopted_scoped_sentence(Layout("delivery"))
        self.assertIn(INTRO_END + sentence + "`make check-codegraph` is in the gate", page)

    def test_an_adopted_repositorys_page_has_no_paragraph_about_a_stamp(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = adopted(Path(directory))
            self.assertEqual(slipwai(repo, "adopt", "--confirm", "shop").returncode, 0)
            self.assert_page_is_the_one_it_was((repo / "delivery/docs/gates.md").read_text(encoding="utf-8"))

    def test_a_moved_layouts_page_is_the_root_pages_without_the_paragraph(self) -> None:
        apps = default_apps("typescript", "none", Selection({"http": "fastify"}))
        stamped = project_files("same", "event-modelling", "none", apps, Layout("."))["docs/gates.md"]
        moved = project_files("same", "event-modelling", "none", apps, Layout("delivery"))["delivery/docs/gates.md"]
        self.assert_page_is_the_one_it_was(moved)
        before, _, rest = stamped.partition("A tree that already passed `make verify` is not judged again.")
        self.assertTrue(rest, "the stamped page has its paragraph")
        after = rest.partition("`make check-codegraph`")[2]
        sentence = adopted_scoped_sentence(Layout("delivery"))
        head = moved.split("`make check-codegraph`")[0].replace(sentence, "")
        self.assertEqual(head.replace("docs/", "delivery/docs/"),
                         before.replace("docs/", "delivery/docs/"))
        self.assertTrue(after)


class TheStampedPageNamesWhatTheKeyCoversAndWhatItCannotSeeTest(StampTestCase):
    def page(self) -> str:
        return squashed((self.repo / "docs/gates.md").read_text(encoding="utf-8"))

    def test_the_key_is_every_file_under_the_project_except_what_the_gate_rebuilds_or_never_reads(self) -> None:
        page = self.page()
        self.assertIn("every file under the project, tracked, untracked or ignored, except what the gate rebuilds or "
                      "never reads", page)
        self.assertIn("every ref and the repository's own git configuration", page)

    def test_it_names_gits_own_configuration_and_a_hand_edited_dependency_among_what_it_cannot_see(self) -> None:
        page = self.page()
        self.assertIn("Nor can it see git's own user-level or system configuration, or a file edited by hand inside "
                      "an installed dependency tree whose manifest did not move.", page)

    def test_a_pipeline_that_sets_no_marker_sets_ci_and_the_gate_then_runs_in_full(self) -> None:
        self.assertIn("A pipeline that sets none of the three sets `CI=1` itself.", self.page())
        self.assertEqual(self.run_gate().returncode, 0)
        self.forget_log()
        planted = self.stamp_path().read_bytes()  # type: ignore[union-attr]
        self.assertEqual(self.run_gate({"CI": "1"}).returncode, 0)
        self.assertTrue(self.checks(), "a pipeline with CI=1 ran no check on a tree that passed")
        self.assertEqual(self.stamp_path().read_bytes(), planted)  # type: ignore[union-attr]

    def test_make_ci_runs_every_check_and_records_nothing(self) -> None:
        self.assertIn("`make ci` runs every check and records nothing.", self.page())
        self.assertEqual(self.run_gate().returncode, 0)
        stamp = self.stamp_path()
        assert stamp is not None
        passed = stamp.read_bytes()
        stamp.unlink()
        for _ in range(2):
            self.forget_log()
            run = subprocess.run(["make", "ci"], cwd=self.repo, env=self.environment(), text=True,
                                 capture_output=True, timeout=180)
            self.assertTrue(self.checks(), run.stdout[-300:])
            self.assertIsNone(self.stamp_path(), "make ci recorded a stamp")
        self.assertTrue(passed)

    def record_ci_branch(self, name: str) -> None:
        record = self.repo / "project.json"
        document = json.loads(record.read_text(encoding="utf-8"))
        document.setdefault("ci", {})["branch"] = name
        record.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

    def test_a_ci_branch_the_gate_cannot_use_is_said_on_a_line_and_recording_a_usable_one_mends_it(self) -> None:
        self.assertIn("A `ci.branch` the gate cannot use, or a trunk it cannot find, is said on one line before the "
                      "first check, which tells what to fix", self.page())
        self.record_ci_branch("no-such-branch")
        run = self.run_gate()
        self.assertEqual(run.returncode, 0, run.stdout)
        lines = self.reuse_lines(run)
        self.assertEqual(len(lines), 1, run.stdout)
        self.assertEqual(run.stdout.splitlines()[0], lines[0])
        self.assertIn("record `ci.branch`", lines[0])
        self.assertTrue(self.checks())
        self.assertIsNone(self.stamp_path(), "a run that cannot tell the trunk recorded a stamp")
        self.record_ci_branch("main")  # what the line says to do
        self.forget_log()
        self.assertEqual(self.run_gate().returncode, 0)
        self.assertIsNotNone(self.stamp_path(), "once the trunk is recorded the run records")

    def test_a_trunk_the_gate_cannot_find_is_said_on_a_line_and_recording_ci_branch_mends_it(self) -> None:
        git(self.repo, "branch", "-m", "main", "develop")
        run = self.run_gate()
        lines = self.reuse_lines(run)
        self.assertEqual(len(lines), 1, run.stdout)
        self.assertIn("record `ci.branch`", lines[0])
        self.assertTrue(self.checks())
        self.assertIsNone(self.stamp_path())
        self.record_ci_branch("develop")
        self.forget_log()
        self.assertEqual(self.run_gate().returncode, 0)
        self.assertIsNotNone(self.stamp_path())


class TheFragmentSaysTheSameTest(FactoryTestCase):
    def test_the_catch_up_gains_make_ci_the_unusable_ci_branch_and_the_ci_sentence_and_stays_minor(self) -> None:
        raw = (ROOT / "changelog.d/verify-stamp.md").read_text(encoding="utf-8")
        text = squashed(raw)
        self.assertEqual(raw.splitlines()[0], "MINOR")
        for sentence in (
            "`make ci` runs every check and records nothing",
            "A `ci.branch` the gate cannot use, or a trunk it cannot find, is said on one line before the first check",
            "A pipeline that sets none of `CI`, `GITHUB_ACTIONS` or `GITLAB_CI` sets `CI=1` itself.",
            "every file under the project, tracked, untracked or ignored, except what the gate rebuilds or never reads",
            "git's own user-level or system configuration",
            "a file edited by hand inside an installed dependency tree whose manifest did not move",
        ):
            self.assertIn(sentence, text)
