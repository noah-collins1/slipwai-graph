"""R3 (AC-S03-5): the key is history and position.

The working files are as they were in every example; what moves is where the checkout stands in its repository.
"""
from __future__ import annotations

from collections.abc import Callable

from stamp_fixture import StampTestCase, git


class HistoryTest(StampTestCase):
    def runs_in_full(self, change: Callable[[], object]) -> None:
        """Stamp the tree, apply `change`, and hold that the next run starts the checks and leaves a new stamp."""
        self.assertEqual(self.run_gate().returncode, 0)
        before = self.stamp()["key"]
        self.forget_log()
        change()
        run = self.run_gate()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue(self.checks(), "no check started: the stamp was reused")
        self.assertNotEqual(self.stamp()["key"], before)
        self.forget_log()
        self.run_gate()
        self.assertEqual(self.checks(), [], "the new stamp was not written for the position the run judged")

    def other_commit(self) -> str:
        """A commit that no ref names yet, with the files `HEAD` has."""
        return git(self.repo, "commit-tree", "HEAD^{tree}", "-p", "HEAD", "-m", "elsewhere").strip()

    def test_an_empty_commit_runs_the_gate(self) -> None:
        """e5: `HEAD` names another commit and the files are the same."""
        self.runs_in_full(lambda: git(self.repo, "commit", "-q", "--allow-empty", "-m", "nothing"))

    def test_another_branch_at_the_same_commit_runs_the_gate(self) -> None:
        """e5: the branch name, with the commit and the files as they were."""
        self.runs_in_full(lambda: git(self.repo, "checkout", "-q", "-b", "other"))

    def test_a_remote_ref_naming_another_commit_runs_the_gate(self) -> None:
        """e5: a fetch moves `refs/remotes/origin/main` and nothing the checkout holds."""
        git(self.repo, "update-ref", "refs/remotes/origin/main", "HEAD")
        elsewhere = self.other_commit()
        self.runs_in_full(lambda: git(self.repo, "update-ref", "refs/remotes/origin/main", elsewhere))

    def test_a_remote_ref_appearing_runs_the_gate(self) -> None:
        """e5: every ref under the namespace is in the key, a new one among them."""
        self.runs_in_full(lambda: git(self.repo, "update-ref", "refs/remotes/origin/main", "HEAD"))

    def test_a_branch_the_checkout_is_not_on_runs_the_gate(self) -> None:
        """e5: every ref under `refs/heads`, not the checked-out one."""
        git(self.repo, "branch", "side", "HEAD")
        elsewhere = self.other_commit()
        self.runs_in_full(lambda: git(self.repo, "update-ref", "refs/heads/side", elsewhere))

    def test_a_new_branch_the_checkout_is_not_on_runs_the_gate(self) -> None:
        """e5: a ref appearing under `refs/heads`."""
        self.runs_in_full(lambda: git(self.repo, "branch", "side", "HEAD"))

    def test_a_shallow_boundary_appearing_runs_the_gate(self) -> None:
        """e5: the file `git rev-parse --git-path shallow` names."""
        head = git(self.repo, "rev-parse", "HEAD").strip()
        self.assertFalse((self.repo / ".git" / "shallow").exists())
        self.runs_in_full(lambda: (self.repo / ".git" / "shallow").write_text(head + "\n", encoding="utf-8"))

    def test_a_shallow_boundary_that_moves_runs_the_gate(self) -> None:
        """e5: a boundary already there, moved."""
        head = git(self.repo, "rev-parse", "HEAD").strip()
        shallow = self.repo / ".git" / "shallow"
        shallow.write_text(head + "\n", encoding="utf-8")
        self.runs_in_full(lambda: shallow.write_text(self.other_commit() + "\n", encoding="utf-8"))

    def test_an_unborn_branch_is_a_value_and_not_a_failure(self) -> None:
        """e5: `HEAD` that names no commit yet stamps like any other, and the commit that follows moves it."""
        git(self.repo, "checkout", "-q", "--orphan", "fresh")
        first = self.run_gate()
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.assertIsNotNone(self.stamp_path(), "a pass on an unborn branch left no stamp")
        self.forget_log()
        self.run_gate()
        self.assertEqual(self.checks(), [], "the unborn branch's stamp was not reused")
