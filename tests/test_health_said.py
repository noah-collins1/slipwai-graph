"""`health()` says what it did and writes what a gate would; its guard clauses are seen red or gone (S02; AC-S02-87,
-88; D63; adversary B2, B3; hand's notes T020, T021).

The project and `Health` are those of `test_health_narrowed`. The guards are exercised with a stand-in `tooling` written
here, a class with the gate's names whose methods raise, so that removing an `except` arm turns the example red:

- `compare()`: the narrowed read raises, or the narrowed `drift()` does; the answer is the whole comparison.
- `memory_of()`: the gate's `remembered()` raises; the answer is the gate's own `UNREADABLE`.
- `renew()`: the gate's `remember()` raises; `renew()` returns, since an index that cannot take notes is compared again.
- `stream_use()`'s identity clause: a stream replaced by a copy with the same bytes at the marker's byte is another
  file, and is read whole.
"""
from __future__ import annotations

import importlib.util
import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

from support import FactoryTestCase
from test_codegraph_narrowed import Project
from test_health_narrowed import Health

from slipwai.assets import TOOLKIT_ROOT

AGENTS = TOOLKIT_ROOT / "scripts/agents"


def loaded(name: str, path: Path) -> ModuleType:
    sys.dont_write_bytecode = True  # no __pycache__/ beside the toolkit's scripts (AC-S02-45)
    sys.path.insert(0, str(path.parent))
    try:
        specification = importlib.util.spec_from_file_location(name, path)
        assert specification is not None and specification.loader is not None
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
    finally:
        sys.path.remove(str(path.parent))
    return module


class Tooling:
    """The gate as `code_index` reaches it, as far as its guards go; each member that can raise is told to."""

    CI_MARKERS: tuple[str, ...] = ()
    UNREADABLE = "the record could not be read"
    HASHED = [0]

    def __init__(self, raises: set[str] | frozenset[str] = frozenset()) -> None:
        self.raises = raises
        self.drifts: list[Any] = []
        self.remembered_calls = 0

    def moment_of(self, whole: float) -> str:
        return "then"

    def read_once(self, memory: dict[str, Any]) -> Any:
        if "read_once" in self.raises:
            raise ValueError("the memory held something the gate cannot use")
        return {"a.py": ("h", 1.0)}, {"a.py"}

    def drift(self, candidates: Any = None, rows: Any = None) -> Any:
        self.drifts.append(candidates)
        if candidates is not None and "narrowed drift" in self.raises:
            raise KeyError("a row the memory did not describe")
        return {"a.py": ("h", 1.0)}, [], []

    def remembered(self) -> Any:
        raise OSError("the memory cannot be read")

    def remember(self, *arguments: Any) -> None:
        self.remembered_calls += 1
        raise OSError("the memory cannot be written")


class TheIndexBeingEmptyOrUnreadableTest(FactoryTestCase):
    def test_e87_an_index_with_no_row_ends_current_and_writes_no_record_as_no_gate_run_would(self) -> None:
        """AC-S02-87: the gate refuses an index that holds no files at all, and writes no record for it."""
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.whole(settled=False)
            project.memory.unlink()
            with sqlite3.connect(project.database) as connection:
                connection.execute("DELETE FROM files")
            done = Health(project)
            self.assertEqual(done.state, "current", done.detail)
            self.assertFalse(project.memory.exists(), "a record was written for an index with no row")

    def test_e87_hold_an_index_with_rows_still_renews_the_record(self) -> None:
        """AC-S02-87 (hold): the guard is for an empty index only."""
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.whole(settled=False)
            project.memory.unlink()
            done = Health(project)
            self.assertEqual(done.state, "current", done.detail)
            self.assertTrue(project.memory.exists())

    def test_e87_a_comparison_that_gives_no_answer_does_not_say_it_compared_everything(self) -> None:
        """AC-S02-87: not a checkout, and a database with no `files` table; `detail` says nothing was compared."""
        for name in ("not a checkout", "no files table"):
            with self.subTest(name), tempfile.TemporaryDirectory() as directory:
                project = Project(self, directory)
                project.whole(settled=False)
                project.memory.unlink()
                if name == "not a checkout":
                    shutil.move(str(project.repo / ".git"), str(Path(directory) / "git-aside"))
                else:
                    with sqlite3.connect(project.database) as connection:
                        connection.execute("DROP TABLE files")
                done = Health(project)
                self.assertEqual(done.state, "current", done.detail)
                self.assertIn("compared nothing", done.detail)
                self.assertNotIn("compared everything", done.detail)


class TheGuardsAroundTheMemoryTest(FactoryTestCase):
    """AC-S02-88: each `except` arm in `code_index.py` is seen red when removed, by a stand-in `tooling`."""

    code_index = loaded("code_index_guards", AGENTS / "code_index.py")

    def test_e88_a_memory_the_gate_cannot_read_is_the_whole_comparison_whatever_it_raised(self) -> None:
        for raises in ({"read_once"}, {"narrowed drift"}):
            with self.subTest(sorted(raises)):
                tooling = Tooling(raises)
                compared = self.code_index.compare(tooling, {"commit": "x"})
                self.assertEqual(compared.said(), f"compared everything: {tooling.UNREADABLE}")
                self.assertIsNone(compared.record)
                self.assertEqual(tooling.drifts[-1], None, "the whole comparison ran")

    def test_e88_the_memory_the_gate_cannot_read_at_all_is_its_unreadable_and_never_an_exception(self) -> None:
        self.assertEqual(self.code_index.memory_of(Tooling()), Tooling.UNREADABLE)

    def test_e88_an_index_that_cannot_take_notes_is_not_an_error_and_was_asked_to(self) -> None:
        tooling = Tooling()
        compared = self.code_index.compare(tooling, None)
        self.assertIsNone(self.code_index.renew(tooling, compared))
        self.assertEqual(tooling.remembered_calls, 1, "the writer was reached, and its failure went no further")

    def test_e88_hold_a_comparison_in_ci_is_neither_read_nor_renewed(self) -> None:
        """A hold: under a CI marker nothing is read or written (the guard is not one of the three arms)."""
        tooling = Tooling()
        tooling.CI_MARKERS = ("S02_TEST_CI",)
        os.environ["S02_TEST_CI"] = "1"
        self.addCleanup(os.environ.pop, "S02_TEST_CI", None)
        self.assertIsNone(self.code_index.memory_of(tooling))
        self.code_index.renew(tooling, self.code_index.compare(tooling, None))
        self.assertEqual(tooling.remembered_calls, 0)


class TheStreamsIdentityTest(FactoryTestCase):
    def test_e88_a_stream_replaced_by_a_copy_with_the_marker_at_the_same_byte_is_read_whole(self) -> None:
        """The marker line stands at the byte the runner wrote it at, but the path is another file: the runner read
        the whole stream, as before the slice, and does not trust an offset into a file it did not write through."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "stream-identity", "standard", "python")
            cruise = loaded("cruise_identity", repo / "scripts/agents/cruise.py")
            stream = repo / ".specify/cruise-stream.jsonl"
            stream.parent.mkdir(exist_ok=True)
            marker = "# iteration 3 2026-10-03T10:00:00Z\n"
            earlier = "# iteration 2 2026-10-03T09:00:00Z\n" + "x" * 400 + "\n"
            stream.write_text(earlier + marker + "\n", encoding="utf-8")
            at = len(earlier.encode("utf-8"))
            status = os.stat(stream)
            cruise.MARKED[:] = [(3, at, marker, (status.st_dev, status.st_ino))]
            total = stream.stat().st_size
            self.assertEqual(cruise.stream_use(3)[1], total - at, "the file written through: read from its marker")
            copy = stream.with_name("copy")
            shutil.copyfile(stream, copy)
            os.replace(copy, stream)
            self.assertNotEqual(os.stat(stream).st_ino, status.st_ino)
            self.assertEqual(cruise.stream_use(3)[1], total, "another file at the path: read whole")
