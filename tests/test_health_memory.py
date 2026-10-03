"""What `health()` does with the gate's memory (S02, R5 and R6).

R5: a memory `health()` cannot use is the whole comparison, said in one clause of `detail`, and a rebuilt database is
compared whole (e37, e39). R6, the memory `health()` writes, joins at T008. The project and `Health` are those of
`test_health_narrowed`; the per-state table of e36 is `test_health_memory_states`.
"""
from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Callable

from support import FactoryTestCase
from test_codegraph_narrowed import Project
from test_health_narrowed import Health

THE_CLAUSES = "compared everything: "


def none(project: Project) -> None:
    project.memory.unlink()


def unreadable(project: Project) -> None:
    project.memory.write_text("{")


def commit_gone(project: Project) -> None:
    project.memory.write_text(json.dumps({**json.loads(project.memory.read_text()), "commit": "0" * 40}))


def scripts_changed(project: Project) -> None:
    with (project.repo / "scripts/check-codegraph.py").open("a") as handle:
        handle.write("# one more byte\n")
    project.resync()


def another_database(project: Project) -> None:
    copy = project.database.with_name("copy.db")
    copy.write_bytes(project.database.read_bytes())
    os.replace(copy, project.database)


def git_silent(project: Project) -> None:
    commit = project.git("rev-parse", "HEAD").strip()
    tree = project.git("rev-parse", f"{commit}^{{tree}}").strip()
    loose = project.repo / ".git/objects" / tree[:2] / tree[2:]
    assert loose.is_file(), "a fresh repository keeps its tree loose"
    loose.rename(project.repo / "tree-object-moved-away")


REASONS: list[tuple[str, Callable[[Project], None], str]] = [
    ("none", none, "no earlier whole comparison is recorded"),
    ("unreadable", unreadable, "the record of the last whole comparison could not be read"),
    ("commit gone", commit_gone, "the commit it was taken at is gone"),
    ("scripts changed", scripts_changed, "the gate's scripts changed since"),
    ("another database identity", another_database, "the index database is not the one it was compared against"),
    ("git unable to say what changed", git_silent, "git could not say what changed"),
]


class AMemoryHealthCannotUseTest(FactoryTestCase):
    def test_e37_each_reason_is_the_whole_comparison_with_one_clause_saying_why(self) -> None:
        for name, spoil, clause in REASONS:
            with self.subTest(name), tempfile.TemporaryDirectory() as directory:
                project = Project(self, directory)
                project.whole()
                spoil(project)
                done, opened = Health.audited(project)
                self.assertEqual(done.state, "current", done.detail)
                self.assertEqual(done.detail.count(THE_CLAUSES), 1, done.detail)
                self.assertIn(f"{THE_CLAUSES}{clause}", done.detail)
                self.assertNotIn("hashed", done.detail)
                self.assertEqual(set(project.rows()) - set(opened), set(), "every tracked file was hashed")

    def test_e39_a_corrupt_database_with_a_usable_memory_is_rebuilt_and_then_compared_whole(self) -> None:
        """A hold: the rebuilt file is not the database the memory compared (the gate's own identity check), so the
        comparison after the rebuild is whole; teeth are shown by narrowing it by the memory read before the rebuild."""
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.whole()
            project.database.write_bytes(b"garbage " * 1000)
            done, opened = Health.audited(project)
            self.assertEqual(done.state, "rebuilt", done.detail)
            self.assertIn("failed its integrity check", done.detail)
            self.assertEqual(done.calls(), ["init -y ."])
            self.assertEqual(len(list((project.repo / ".codegraph/corrupt").iterdir())), 1, "moved aside")
            self.assertNotIn("hashed", done.detail)
            self.assertEqual(set(project.rows()) - set(opened), set(), "every tracked file was hashed")
