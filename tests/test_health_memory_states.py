"""Every drift state of S01 answers as `health()` without a memory does (S02, R5, e36).

For each state — AC-S01-13, -14, -15, -16, -17, -18, -23, -24 and the no-row state of -21 — the project is brought to
the state after a whole comparison has left its memory, `health()` runs on it narrowed, the index and the memory are put
back as they were, the memory is deleted, and `health()` runs again on the same tree and index. The two states must
be equal.

None of these was seen failing: before `health()` narrowed there was only the whole comparison, which agrees with
itself, and `health()` narrows through the gate's own memory, which S01's tests hold to its states. They are holds on
the narrowing, in the plan's words "a state that already agrees is written as a hold with the reason"; teeth are shown
by a `compare()` that hashes nothing, which this table fails.
"""
from __future__ import annotations

import json
import os
import sqlite3
import tempfile
from collections.abc import Callable

from support import FactoryTestCase
from test_codegraph_narrowed import Project
from test_health_narrowed import Health

Step = Callable[[Project], None]
GARBAGE = b"garbage " * 1000


def nothing(project: Project) -> None:
    return None


def dirty_then_reverted(project: Project) -> Step:
    """A file dirty when the memory was written, with the index holding the dirty content, reverted afterwards."""
    edited = project.edit()
    project.resync()

    def revert(later: Project) -> None:
        later.git("checkout", "--", edited)

    return revert


def row_rewritten(project: Project) -> None:
    with sqlite3.connect(project.database) as connection:
        connection.execute("UPDATE files SET content_hash = ? WHERE path = ?", ("0" * 64, project.source()))


def row_deleted(project: Project) -> None:
    with sqlite3.connect(project.database) as connection:
        connection.execute("DELETE FROM files WHERE path = ?", (project.source(),))


def row_added(project: Project) -> None:
    with sqlite3.connect(project.database) as connection:
        connection.execute("INSERT OR REPLACE INTO files VALUES ('extra.py', ?, 1.0)", ("0" * 64,))


def another_database(project: Project) -> None:
    copy = project.database.with_name("copy.db")
    copy.write_bytes(project.database.read_bytes())
    os.replace(copy, project.database)


def flagged(flag: str) -> Step:
    def edit(project: Project) -> None:
        path = project.source()
        project.git("update-index", flag, path)
        project.edit(path)
    return edit


def scripts_changed(project: Project) -> None:
    with (project.repo / "scripts/check-codegraph.py").open("a") as handle:
        handle.write("# one more byte\n")
    project.resync()


def unreadable_memory(project: Project) -> None:
    project.memory.write_text("{")


def commit_gone(project: Project) -> None:
    project.memory.write_text(json.dumps({**json.loads(project.memory.read_text()), "commit": "0" * 40}))


def no_memory(project: Project) -> None:
    project.memory.unlink()


def files_table_moved_on(project: Project) -> None:
    with sqlite3.connect(project.database) as connection:
        connection.execute("ALTER TABLE files RENAME TO files_moved_on")


def corrupt(project: Project) -> None:
    project.database.write_bytes(GARBAGE)


def crlf(project: Project) -> None:
    path = project.repo / project.source()
    path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))


def same_size_with_its_time_restored(project: Project) -> None:
    target = project.repo / project.source()
    before = target.stat()
    data = target.read_bytes()
    target.write_bytes(data.replace(data[:1], b"#" if data[:1] != b"#" else b"!", 1))
    os.utime(target, ns=(before.st_atime_ns, before.st_mtime_ns))


def touched_declined_file(project: Project) -> None:
    os.utime(project.repo / "declined.py")


def declined(project: Project) -> None:
    """A tracked `.py` file the index holds no row for, older than the index's last `indexed_at`."""
    target = project.repo / "declined.py"
    target.write_text("x = 1\n")
    project.commit("a file the index declined")
    os.utime(target, (0, 0))


def recent_then_rewritten(project: Project) -> Step | None:
    """AC-S01-24: a committed, indexed file written within two seconds of the run that records the memory, so the
    memory cannot vouch for it; it is rewritten in place afterwards (see `RECENT`: that run is not settled)."""
    project.settle()
    project.edit()
    project.resync()
    project.commit("a file written just before the whole comparison")
    return None


def extra(project: Project) -> None:
    """A tracked file the index never saw, older than the index, as the added-row state needs it."""
    target = project.repo / "extra.py"
    target.write_text("x = 1\n")
    project.commit("a file the index never saw")
    os.utime(target, (0, 0))


# Rides on the AC-S01-23 row above it: the rewrite moves the change time, which makes the file a candidate with or
# without the two-second rule, so removing that rule turns no assertion of this row red. Nothing here can isolate
# the rule: a file whose every fact stood would have to be rewritten with its change time put back.
RECENT_ROW = "AC-S01-24 a file not safely older than the run that vouched for it (rides on AC-S01-23's row)"

# (name, what happens before the whole comparison that writes the memory, what happens after it)
Before = Callable[[Project], Step | None]
STATES: list[tuple[str, Before, Step]] = [
    ("AC-S01-13 dirty at the memory, reverted since", dirty_then_reverted, nothing),
    ("AC-S01-14 a row rewritten", lambda p: None, row_rewritten),
    ("AC-S01-14 a row deleted", lambda p: None, row_deleted),
    ("AC-S01-14 a row added", extra, row_added),
    ("AC-S01-14 another database", lambda p: None, another_database),
    ("AC-S01-15 assume-unchanged and edited", lambda p: None, flagged("--assume-unchanged")),
    ("AC-S01-15 skip-worktree and edited", lambda p: None, flagged("--skip-worktree")),
    ("AC-S01-16 a gate script changed", lambda p: None, scripts_changed),
    ("AC-S01-17 no memory", lambda p: None, no_memory),
    ("AC-S01-17 an unreadable memory", lambda p: None, unreadable_memory),
    ("AC-S01-17 its commit gone", lambda p: None, commit_gone),
    ("AC-S01-18 a files table that cannot be read", lambda p: None, files_table_moved_on),
    ("AC-S01-18 a corrupt database", lambda p: None, corrupt),
    ("AC-S01-23 CRLF written over LF", lambda p: None, crlf),
    ("AC-S01-23 a same-size rewrite with its time restored", lambda p: None, same_size_with_its_time_restored),
    ("AC-S01-21 a tracked file with no row, touched", declined, touched_declined_file),
    (RECENT_ROW, recent_then_rewritten, same_size_with_its_time_restored),
]
# The states whose whole comparison runs at once, without waiting for the files to age: that is the state.
RECENT = {RECENT_ROW}


class EveryStateAnswersAsTheWholeComparisonDoesTest(FactoryTestCase):
    def both(self, directory: str, before: Before, after: Step, settled: bool = True) -> tuple[Health, Health]:
        project = Project(self, directory)
        project.git("config", "core.trustctime", "false")
        project.git("config", "core.checkStat", "minimal")
        reverts = before(project)
        project.whole(settled)
        after(project)
        if reverts is not None:
            reverts(project)
        index = project.database.read_bytes() if project.database.exists() else None
        narrowed = Health(project)
        if index is not None:  # the same index again: written into the file, not over it
            project.database.write_bytes(index)
        project.memory.unlink(missing_ok=True)
        return narrowed, Health(project)

    def test_e36_each_state_gives_the_state_the_whole_comparison_gives(self) -> None:
        for name, before, after in STATES:
            with self.subTest(name), tempfile.TemporaryDirectory() as directory:
                narrowed, whole = self.both(directory, before, after, name not in RECENT)
                self.assertNotEqual(whole.state, "", whole.result.stderr)
                self.assertEqual(narrowed.state, whole.state, f"{narrowed.detail} | {whole.detail}")
                self.assertTrue(narrowed.state in ("current", "synced", "rebuilt"), narrowed.detail)

    def test_e36_the_states_the_table_names_are_not_all_the_same_state(self) -> None:
        """The table is not vacuous: it reaches `current`, `synced` and `rebuilt`, each by a state that means it."""
        reached = set()
        for name in ("AC-S01-13 dirty at the memory, reverted since", "AC-S01-17 no memory",
                     "AC-S01-18 a corrupt database"):
            before, after = next((b, a) for n, b, a in STATES if n == name)
            with tempfile.TemporaryDirectory() as directory:
                reached.add(self.both(directory, before, after)[0].state)
        self.assertEqual(reached, {"synced", "current", "rebuilt"})
