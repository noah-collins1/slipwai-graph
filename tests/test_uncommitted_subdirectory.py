"""The refusal where the project sits in a subdirectory of its git repository (S23; brownfield adoption, experimental).

`git status` spells a path from the repository's top (`sub/delivery/docs/convergence.md`); a run spells what it
writes from the project (`delivery/docs/convergence.md`). Nothing matched, so a person's uncommitted edit was
written over at exit 0. The refusal is the one `tests/test_uncommitted.py` pins at the top of a repository,
named by the project's own spelling.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from support import FactoryTestCase
from test_adopt import repository, slipwai
from test_adopt_next import in_terminal
from test_candidates import MONOREPO
from test_replay import git

PAGE = "delivery/docs/convergence.md"


def placed(parent: Path, at: str = "sub") -> tuple[Path, Path]:
    """A repository holding a project in `at` and an `other/` beside it, the adoption committed by the run itself;
    returns the repository's top and the project directory, where commands run."""
    files = {f"{at}/{name}": text for name, text in MONOREPO.items()}
    top = repository(parent, "shop", {**files, "other/note.txt": "x\n"})
    project = top / at
    output = in_terminal(project, "adopt", "--no-init")
    assert (project / "project.json").is_file(), output
    assert git(top, "status", "--porcelain").stdout == "", "the adoption is committed"
    return top, project


class RefusalInSubdirectoryTest(FactoryTestCase):
    def refused(self, project: Path, *arguments: str, naming: str = PAGE) -> str:
        result = slipwai(project, "adopt", *arguments)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn(f"`{naming}`", result.stderr)
        self.assertNotIn("sub/delivery", result.stderr, "named as the project spells it, not from the top")
        return result.stderr

    def test_a_hand_edit_to_a_file_a_refresh_writes_is_refused_by_the_projects_name_for_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            top, project = placed(Path(directory))
            page = project / PAGE
            page.write_text(page.read_text() + "\nA note of mine.\n")
            self.refused(project, "--refresh")
            self.assertIn("A note of mine.", page.read_text(), "and nothing was written over it")
            self.assertEqual(git(top, "status", "--porcelain").stdout.split(), ["M", f"sub/{PAGE}"], "no other file")

    def test_the_same_edit_refuses_confirm_and_leaves_project_json_as_it_was(self) -> None:
        self.assert_answer_refused("--confirm", "sub")

    def test_the_same_edit_refuses_decline_and_leaves_project_json_as_it_was(self) -> None:
        self.assert_answer_refused("--decline", "themes")

    def assert_answer_refused(self, *answer: str) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project = placed(Path(directory))
            (project / PAGE).write_text("mine\n")
            before = (project / "project.json").read_bytes()
            self.refused(project, *answer)
            self.assertEqual((project / "project.json").read_bytes(), before)

    def test_a_listed_file_deleted_and_not_committed_is_refused_by_name(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project = placed(Path(directory))
            (project / PAGE).unlink()
            self.refused(project, "--refresh")
            self.assertFalse((project / PAGE).exists(), "and it was not written back")

    def test_a_path_the_run_writes_that_is_present_and_untracked_is_refused_by_name(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            top, project = placed(Path(directory))
            git(top, "rm", "-q", "--cached", f"sub/{PAGE}")
            git(top, "-c", "user.name=t", "-c", "user.email=t@local", "commit", "-q", "-m", "untrack")
            self.assertTrue((project / PAGE).is_file())
            self.refused(project, "--refresh")
