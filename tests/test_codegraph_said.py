"""What `check-codegraph` says on a `slice/<id>` branch when it cannot or may not narrow (S01-gate-walks, D51).

Helpers are those of `test_codegraph_narrowed`. A run that cannot narrow is the whole run, and says why in one clause.
"""
from __future__ import annotations

import tempfile

from support import FactoryTestCase
from test_codegraph_memory import whole_line
from test_codegraph_narrowed import Project


class GitUnableToListWhatChangedTest(FactoryTestCase):
    """AC-S01-17: git cannot say what changed since the memory's commit, so the run is the whole run."""

    def test_the_commits_tree_moved_away_gives_the_whole_run_and_says_why(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.whole()
            project.slice()
            commit = project.git("rev-parse", "HEAD").strip()
            tree = project.git("rev-parse", f"{commit}^{{tree}}").strip()
            loose = project.repo / ".git/objects" / tree[:2] / tree[2:]
            self.assertTrue(loose.is_file(), "a fresh repository keeps its tree loose")
            loose.rename(project.repo / "tree-object-moved-away")
            project.git("cat-file", "-e", f"{commit}^{{commit}}")  # the commit is there; only its tree is not
            run = project.run()
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertRegex(run.stdout, whole_line("git could not say what changed"))
            self.assertNotIn("hashed", run.stdout)
