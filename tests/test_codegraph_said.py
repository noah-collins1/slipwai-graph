"""What `check-codegraph` says on a `slice/<id>` branch when it cannot or may not narrow (S01-gate-walks, D51).

Helpers are those of `test_codegraph_narrowed`. A run that cannot narrow is the whole run, and says why in one clause.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

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


UNKEPT = "the record cannot be kept here: git does not ignore `.codegraph/`"
ROOT = Path(__file__).resolve().parents[1]
SHIPPED = ("assets/toolkit/scripts/check-codegraph.py", "assets/toolkit/scripts/agents/code_index.py",
           "assets/toolkit/scripts/extensions/codegraph/init.py", "src/slipwai/project/docs.py")


class WhatThePagesSayOfWhereTheGateNarrowsTest(FactoryTestCase):
    """A developer is told where the gate compares only what changed, where it keeps its record, and how to reset it."""

    def test_each_text_that_describes_the_gate_says_so(self) -> None:
        for name in SHIPPED:
            with self.subTest(name):
                text = " ".join((ROOT / name).read_text().split())
                self.assertIn("`slice/<id>` branch", text)
                self.assertIn("`.codegraph/gate-memory.json`", text)
                self.assertIn("deleting that file makes the next run whole", text)
                self.assertIn("the trunk and CI", text)


class WhereGitDoesNotIgnoreTheIndexTest(FactoryTestCase):
    def test_the_clause_says_the_record_cannot_be_kept_and_why_not_that_none_is_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            ignore = project.repo / ".gitignore"
            ignore.write_text("".join(line for line in ignore.read_text().splitlines(keepends=True)
                                      if line.strip() != ".codegraph/"))
            project.commit("stop ignoring the index")
            project.whole()
            project.slice()
            run = project.run()
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertRegex(run.stdout, whole_line(UNKEPT))
            self.assertNotIn("no earlier whole comparison", run.stdout)

    def test_hold_on_the_trunk_the_line_is_todays(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            ignore = project.repo / ".gitignore"
            ignore.write_text("")
            project.commit("stop ignoring the index")
            done = project.whole()
            self.assertRegex(done.stdout, r"^check-codegraph: index current — \d+ file\(s\), indexed [\d: -]+\n$")
