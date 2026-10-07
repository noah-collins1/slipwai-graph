"""What `health()` does with the gate's memory (S02, R5 and R6).

R5: a memory `health()` cannot use is the whole comparison, said in one clause of `detail`, and a rebuilt database is
compared whole (e37, e39). R6: the memory `health()` writes, through the gate's own writer, and never in CI (e38, e40,
and the second half of e41). The project and `Health` are those of `test_health_narrowed`; the per-state table of e36 is
`test_health_memory_states`.
"""
from __future__ import annotations

import json
import os
import sqlite3
import tempfile
from collections.abc import Callable

from support import FactoryTestCase
from test_codegraph_narrowed import CI_MARKERS, Project
from test_cruise_index import bare_path
from test_health_narrowed import NARROWED, Health

# Generates nothing itself: the projects come from `Project`, imported from the modules above.
TEST_SELECTION: dict[str, object] = {}

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
        comparison after the rebuild is whole; teeth are shown by a whole comparison that hashes nothing."""
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


def record_of(project: Project) -> dict[str, object]:
    """The memory as a record, without the two moments that differ between any two runs: when the run began, which the
    memory keeps for the whole comparison and for each file it hashed."""
    record = json.loads(project.memory.read_text())
    return {**record, "whole": 0, "files": {path: [*seen[:4], 0] for path, seen in record["files"].items()}}


class TheMemoryHealthWritesTest(FactoryTestCase):
    """R6: written by a `health()` that ends current, or synced and clean, and in no other case."""

    def test_e38_in_ci_health_compares_everything_and_leaves_the_memory_as_it_was(self) -> None:
        """A hold: nothing reads or writes the memory under a CI marker. Teeth: `memory_of()` reading it in CI."""
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.whole()
            for marker in CI_MARKERS:
                with self.subTest(marker):
                    project.settle()
                    before, seen = project.memory.read_bytes(), project.memory.stat().st_mtime_ns
                    done, opened = Health.audited(project, **{marker: "true"})
                    self.assertEqual(done.state, "current", done.detail)
                    self.assertNotIn("hashed", done.detail)
                    self.assertEqual(set(project.rows()) - set(opened), set(), "every tracked file was hashed")
                    self.assertEqual(project.memory.read_bytes(), before)
                    self.assertEqual(project.memory.stat().st_mtime_ns, seen)

    def test_e38_in_ci_no_memory_is_made_where_there_was_none(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            for marker in CI_MARKERS:
                with self.subTest(marker):
                    done = Health(project, **{marker: "true"})
                    self.assertEqual(done.state, "current", done.detail)
                    self.assertFalse(project.memory.exists())

    def test_e40_a_current_health_leaves_what_a_passing_gate_run_leaves(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.settle()
            self.assertFalse(project.memory.exists())
            done = Health(project)
            self.assertEqual(done.state, "current", done.detail)
            self.assertTrue(project.memory.is_file(), "a health() that ends current writes the memory")
            written = record_of(project)
            project.memory.unlink()
            project.run()
            self.assertEqual(written, record_of(project), "what the gate writes on the same tree")

    def test_e40_a_narrowed_current_health_renews_the_memory_as_a_narrowed_gate_run_does(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.whole()
            os.utime(project.repo / project.source())
            project.settle()
            first = project.memory.read_bytes()
            done = Health(project)
            self.assertRegex(done.detail, NARROWED.format(hashed=1))
            renewed = project.memory.read_bytes()
            self.assertTrue(renewed != first, "the touched file's record was renewed")
            written = record_of(project)
            project.memory.write_bytes(first)
            project.slice()
            project.run()
            self.assertEqual(written, record_of(project), "what a narrowed gate run writes on the same tree")
            self.assertEqual(json.loads(renewed)["whole"], json.loads(first)["whole"], "the whole moment is kept")

    def test_e40_a_synced_health_with_a_clean_second_comparison_writes_the_memory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.edit()
            project.settle()
            done = Health(project)
            self.assertEqual(done.state, "synced", done.detail)
            self.assertTrue(project.memory.is_file())
            written = record_of(project)
            project.memory.unlink()
            self.assertEqual(project.run().returncode, 0)
            self.assertEqual(written, record_of(project), "what the gate writes on the same tree")

    def test_e41_a_touch_costs_one_hash_and_the_next_health_none(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.whole()
            os.utime(project.repo / project.source())
            project.settle()
            first = Health(project)
            self.assertEqual(first.state, "current", first.detail)
            self.assertRegex(first.detail, NARROWED.format(hashed=1))
            project.settle()
            second = Health(project)
            self.assertEqual(second.state, "current", second.detail)
            self.assertRegex(second.detail, NARROWED.format(hashed=0))

    def test_hold_e40_where_health_does_not_end_current_the_memory_is_as_it_was(self) -> None:
        """Each of these ends `failed` or `unreachable`, cannot open the database or gets no answer: the memory's
        bytes are the same afterwards. Green today; teeth: the writer called whatever the state."""
        def opened_by_nobody(project: Project) -> Health:
            project.database.chmod(0)
            return Health(project)

        def no_answer(project: Project) -> Health:
            with sqlite3.connect(project.database) as connection:
                connection.execute("ALTER TABLE files RENAME TO files_moved_on")
            return Health(project)

        def sync_fails(project: Project) -> Health:
            project.in_place()
            project.edit()
            return Health(project, FAKE_SYNC_FAILS="1")

        def unreachable(project: Project) -> Health:
            project.edit()
            return Health(project, PATH=str(bare_path(project.repo.parent)), HOME=str(project.repo.parent),
                          NVM_DIR="", VOLTA_HOME="", FNM_DIR="")

        cases = [("failed", sync_fails, "failed"), ("unreachable", unreachable, "unreachable"),
                 ("no answer from the comparison", no_answer, "current")]
        if hasattr(os, "geteuid") and os.geteuid() != 0:  # the owner can read a mode-0 file as root only
            cases.append(("the database cannot be opened", opened_by_nobody, "failed"))
        for name, make, state in cases:
            with self.subTest(name), tempfile.TemporaryDirectory() as directory:
                project = Project(self, directory)
                project.whole()
                project.settle()
                before, seen = project.memory.read_bytes(), project.memory.stat().st_mtime_ns
                done = make(project)
                project.database.chmod(0o644)
                self.assertEqual(done.state, state, done.detail)
                self.assertEqual(project.memory.read_bytes(), before)
                self.assertEqual(project.memory.stat().st_mtime_ns, seen)
