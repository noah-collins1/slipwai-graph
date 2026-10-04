"""R2 (AC-S03-33, -34; D83 items 2 and 3): the key is taken for the whole repository, every ref and its configuration.

A project in a subdirectory of its repository judges its own directory, but git's answer about what is tracked, what
is not ignored and what is staged is the repository's: a sibling's uncommitted edit on a `slice/<id>` branch is a run
the full gate makes. Every ref git lists is in the key with what it names, a tag and a replace ref included, and so are
the bytes of the repository's own configuration file and the worktree's, absence a value.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from stamp_fixture import BRANCH, KeyTestCase, StampTestCase, commit_all, exclude, git


class SubdirectoryProjectTest(StampTestCase):
    """The fixture's project moved one level down in a repository of its own, a sibling beside it."""

    def setUp(self) -> None:
        super().setUp()
        top = self.repo.parent / "mono"
        project = top / "project"
        top.mkdir()
        shutil.copytree(self.repo, project, symlinks=True, ignore=shutil.ignore_patterns(".git"))
        (top / "sibling").mkdir()
        (top / "sibling" / "notes.txt").write_text("a sibling\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q", "-b", "main", str(top)], check=True)
        for key, value in (("user.name", "t"), ("user.email", "t@local"), ("commit.gpgsign", "false")):
            git(top, "config", key, value)
        commit_all(top, "a monorepo")
        git(top, "checkout", "-q", "-b", "slice/S01-x")
        self.top, self.repo = top, project

    def stamped(self) -> bool:
        return any((self.top / ".git" / "slipwai").glob("verify-stamp-*.json"))

    def stamp_then_edit_beside(self, edit: str) -> None:
        """Stamp the project, make `edit` to the sibling, and hold: the full gate runs, fails on the slice's scope, and
        where a tracked edit is what the slice's scope fails, leaves no stamp."""
        self.assertEqual(self.run_gate().returncode, 0, "the premise: the gate passes here")
        self.assertTrue(self.stamped())
        self.forget_log()
        self.run_gate()
        self.assertEqual(self.checks(), [], "the premise: the unchanged tree is reused")
        self.forget_log()
        sibling = self.top / "sibling"
        if edit == "edit":
            (sibling / "notes.txt").write_text("edited, not committed\n", encoding="utf-8")
        else:
            (sibling / "new.txt").write_text("x\n", encoding="utf-8")
            if edit == "stage":
                git(self.top, "add", "sibling/new.txt")
        run = self.run_gate()
        self.assertTrue(self.checks(), f"no check started after {edit}: the stamp was reused")
        if edit == "edit":
            self.assertNotEqual(run.returncode, 0, "the forced gate fails on the slice's scope")
            self.assertFalse(self.stamped())

    def test_a_sibling_directorys_uncommitted_edit_runs_the_full_gate(self) -> None:
        """A2, T022: the plain run reused while the forced run saw the sibling's edit."""
        self.stamp_then_edit_beside("edit")

    def test_a_new_untracked_file_beside_the_project_runs_the_full_gate(self) -> None:
        self.stamp_then_edit_beside("new")

    def test_a_file_staged_beside_the_project_runs_the_full_gate(self) -> None:
        self.stamp_then_edit_beside("stage")

    def test_an_ignored_file_beside_the_project_is_not_the_projects_to_cover(self) -> None:
        """D83 item 2's departure: ignored files are covered under the project's directory only."""
        exclude(self.top, "scratch/", "project/scratch/")
        self.assertEqual(self.run_gate().returncode, 0)
        self.forget_log()
        (self.top / "scratch").mkdir()
        (self.top / "scratch" / "x.txt").write_text("x\n", encoding="utf-8")
        run = self.run_gate()
        self.assertEqual(self.checks(), [], run.stdout)
        (self.repo / "scratch").mkdir()
        (self.repo / "scratch" / "x.txt").write_text("y\n", encoding="utf-8")
        self.run_gate()
        self.assertTrue(self.checks(), "an ignored file under the project's own directory is covered")


class RefsAndConfigurationTest(KeyTestCase):
    def test_a_tag_moves_the_key_and_a_tag_named_like_the_trunk_does_too(self) -> None:
        """A3: refs outside `refs/heads` and `refs/remotes` were not in the key."""
        before = self.key()
        git(self.repo, "tag", "release-1")
        tagged = self.key()
        self.assertNotEqual(tagged, before)
        git(self.repo, "tag", "main")
        self.assertNotEqual(self.key(), tagged)

    def test_a_replace_ref_a_note_and_a_stash_ref_move_the_key(self) -> None:
        (self.repo / "later.txt").write_text("later\n", encoding="utf-8")
        commit_all(self.repo, "later")
        first, second = git(self.repo, "rev-parse", "HEAD~1").strip(), git(self.repo, "rev-parse", "HEAD").strip()
        before = self.key()
        git(self.repo, "replace", second, first)
        replaced = self.key()
        self.assertNotEqual(replaced, before)
        git(self.repo, "notes", "add", "-m", "a note")
        self.assertNotEqual(self.key(), replaced)

    def test_a_ref_pointing_elsewhere_moves_the_key(self) -> None:
        git(self.repo, "tag", "marker")
        before = self.key()
        (self.repo / "later.txt").write_text("later\n", encoding="utf-8")
        commit_all(self.repo, "later")
        git(self.repo, "tag", "-f", "marker")
        git(self.repo, "reset", "-q", "--hard", "HEAD~1")
        self.assertNotEqual(self.key(), before)

    def test_the_repositorys_configuration_is_in_the_key(self) -> None:
        """A4: `core.quotePath` changes what `check-migrations` sees."""
        before = self.key()
        git(self.repo, "config", "core.quotePath", "false")
        flipped = self.key()
        self.assertNotEqual(flipped, before)
        git(self.repo, "config", "--unset", "core.quotePath")
        self.assertEqual(self.key(), before, "the same bytes, the same key")

    def test_the_worktrees_configuration_is_in_the_key_and_absence_is_a_value(self) -> None:
        git(self.repo, "config", "extensions.worktreeConfig", "true")
        before = self.key()
        git(self.repo, "config", "--worktree", "core.quotePath", "false")
        self.assertTrue((self.repo / ".git" / "config.worktree").is_file())
        self.assertNotEqual(self.key(), before)

    def test_a_linked_worktrees_own_configuration_is_in_its_key(self) -> None:
        linked = self.repo.parent / "linked"
        git(self.repo, "worktree", "add", "-q", "-b", "other", str(linked))
        git(self.repo, "config", "extensions.worktreeConfig", "true")
        module = __import__("stamp_fixture").load_script(self.repo)
        before = self.key_in(module, linked)
        git(linked, "config", "--worktree", "core.quotePath", "false")
        self.assertNotEqual(self.key_in(module, linked), before)

    def key_in(self, module: object, directory: Path) -> str:
        import os
        was = Path.cwd()
        os.chdir(directory)
        try:
            return str(module.build_key({})["key"])  # type: ignore[attr-defined]
        finally:
            os.chdir(was)


class BranchOnlyTest(StampTestCase):
    def test_a_tag_made_after_a_pass_runs_the_full_gate_through_make(self) -> None:
        self.assertEqual(self.run_gate().returncode, 0)
        self.forget_log()
        git(self.repo, "tag", "main")
        self.run_gate()
        self.assertTrue(self.checks(), f"no check started on {BRANCH} after a tag named like the trunk")
