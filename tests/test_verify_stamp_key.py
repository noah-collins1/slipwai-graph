"""R3 (AC-S03-5): the key is history and position.

The working files are as they were in every example; what moves is where the checkout stands in its repository.
"""
from __future__ import annotations

from collections.abc import Callable

from stamp_fixture import StampTestCase, commit_all, git


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

    def test_an_unborn_branch_has_no_stamp_and_the_commit_that_follows_is_where_one_begins(self) -> None:
        """e5, brought to AC-S03-37 (D83 item 7a): a `HEAD` that names no commit reads and writes nothing, and says
        nothing; the first commit makes it a branch like any other, and the key holds what it names."""
        git(self.repo, "checkout", "-q", "--orphan", "fresh")
        first = self.run_gate()
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.assertIsNone(self.stamp_path(), "a pass on an unborn branch left a stamp")
        self.assertEqual(self.reuse_lines(first), [])
        commit_all(self.repo, "the first commit")
        self.assertEqual(self.run_gate().returncode, 0)
        self.assertIsNotNone(self.stamp_path())
        self.forget_log()
        self.run_gate()
        self.assertEqual(self.checks(), [], "the first commit's stamp was not reused")


class ScriptsTest(StampTestCase):
    """R4 (AC-S03-6): the `Makefile` and every covered file under `scripts/` are one named part, beside `tree`."""

    def comment_added_to(self, name: str) -> None:
        self.assertEqual(self.run_gate().returncode, 0)
        before = self.stamp()
        self.forget_log()
        path = self.repo / name
        path.write_text(path.read_text(encoding="utf-8") + "\n# a comment\n", encoding="utf-8")
        run = self.run_gate()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue(self.checks(), "no check started: the stamp was reused")
        after = self.stamp()
        self.assertNotEqual(after["scripts"], before["scripts"], "the scripts part did not move")
        self.assertNotEqual(after["tree"], before["tree"], "a covered file moved and the tree part did not")
        self.assertNotEqual(after["key"], before["key"])

    def test_a_comment_in_a_gate_script_runs_the_gate(self) -> None:
        """e6: a check script."""
        self.comment_added_to("scripts/check-imports.py")

    def test_a_comment_in_the_makefile_runs_the_gate(self) -> None:
        """e6: the file the gate ran from."""
        self.comment_added_to("Makefile")

    def test_a_script_deeper_under_scripts_is_in_the_part(self) -> None:
        """e6: at any depth."""
        self.comment_added_to("scripts/agents/project.py")

    def test_a_new_file_under_scripts_is_in_the_part(self) -> None:
        """e6: untracked, not ignored, so covered."""
        self.assertEqual(self.run_gate().returncode, 0)
        before = self.stamp()
        (self.repo / "scripts" / "added.py").write_text("print(1)\n", encoding="utf-8")
        self.assertEqual(self.run_gate().returncode, 0)
        self.assertNotEqual(self.stamp()["scripts"], before["scripts"])

    def test_a_file_elsewhere_moves_the_tree_and_not_the_scripts(self) -> None:
        """e6: hold — the part is its own digest and holds nothing but its own files."""
        self.assertEqual(self.run_gate().returncode, 0)
        before = self.stamp()
        (self.repo / "README.md").write_text("changed\n", encoding="utf-8")
        self.assertEqual(self.run_gate().returncode, 0)
        after = self.stamp()
        self.assertEqual(after["scripts"], before["scripts"])
        self.assertNotEqual(after["tree"], before["tree"])

    def test_an_ignored_file_under_scripts_is_not_covered(self) -> None:
        """e6: hold — what git ignores is not a covered file."""
        self.assertEqual(self.run_gate().returncode, 0)
        ignored = self.repo / "scripts" / "__pycache__"
        ignored.mkdir(exist_ok=True)
        (ignored / "x.pyc").write_bytes(b"\0")
        self.assertEqual(git(self.repo, "status", "--porcelain", "--", "scripts").strip(), "")
        self.forget_log()
        self.run_gate()
        self.assertEqual(self.checks(), [])
