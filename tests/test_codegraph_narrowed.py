"""`check-codegraph` on a `slice/<id>` branch hashes what changed (S01-gate-walks, R6 and R7).

The project is the indexed one of `test_code_index_health` — a generated Python project whose index was built by the
fake `codegraph` CLI, which keeps a real SQLite database. *A whole comparison* is one run of the gate on `main` that
passed; `NARROW` is checked out on `slice/S1` with none of the CI markers set. R6 is a set of holds: off a slice
branch, and in CI, the run is today's, to the byte. R7 is the change: on `NARROW` the gate hashes only what changed
and says so.
"""
from __future__ import annotations

import hashlib
import os
import re
import sqlite3
import subprocess
import tempfile

from gate_audit import Audited
from support import FactoryTestCase, commit_all
from test_code_index_health import indexed

GATE = "scripts/check-codegraph.py"
CI_MARKERS = ("CI", "GITHUB_ACTIONS", "GITLAB_CI")
# The gate's own two scripts are opened by any run (it is one of them, and it loads the other); everything else the
# index holds is a file the run either needed to hash or did not.
OWN = {"scripts/check-codegraph.py", "scripts/agents/code_index.py"}
CURRENT = re.compile(r"^check-codegraph: index current — (\d+) file\(s\), indexed \d{4}-\d\d-\d\d \d\d:\d\d:\d\d\n$")
HASHED = (r"^check-codegraph: {synced}index current — hashed {hashed} of (\d+) file\(s\), only what changed since the "
          r"last whole comparison \(\d{{4}}-\d\d-\d\d \d\d:\d\d:\d\d\); the integrity check was not run here and runs "
          r"in the full gate\n$")


def narrowed_line(hashed: int, synced: str = "") -> str:
    return HASHED.format(synced=re.escape(synced), hashed=hashed)


class Project:
    """An indexed project and the ways a test moves it: branches, edits, an index that follows or does not."""

    def __init__(self, case: FactoryTestCase, directory: str, name: str = "narrowed") -> None:
        self.case = case
        self.repo, self.tools, self.log = indexed(case, directory, name)
        self.memory = self.repo / ".codegraph/gate-memory.json"
        self.database = self.repo / ".codegraph/codegraph.db"

    def env(self, **extra: str | None) -> dict[str, str]:
        base = {key: value for key, value in os.environ.items() if key not in CI_MARKERS}
        merged = {**base, **self.tools, **extra}
        return {key: value for key, value in merged.items() if value is not None}

    def run(self, **extra: str | None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["python3", GATE], cwd=self.repo, env=self.env(**extra), text=True,
                              capture_output=True)

    def audited(self, **extra: str | None) -> Audited:
        return Audited(self.repo, GATE, env=self.env(**extra))

    def git(self, *arguments: str) -> str:
        done = subprocess.run(["git", *arguments], cwd=self.repo, text=True, capture_output=True, check=True)
        return done.stdout

    def whole(self) -> subprocess.CompletedProcess[str]:
        """A whole comparison: the gate on `main`, passing."""
        self.git("checkout", "-q", "main")
        done = self.run()
        self.case.assertEqual(done.returncode, 0, done.stderr)
        return done

    def slice(self) -> None:
        self.git("checkout", "-q", "-B", "slice/S1")

    def source(self) -> str:
        return next(path for path in self.rows() if path not in OWN and not path.startswith("scripts/"))

    def rows(self) -> dict[str, str]:
        with sqlite3.connect(self.database) as connection:
            return dict(connection.execute("SELECT path, content_hash FROM files").fetchall())

    def edit(self, path: str | None = None) -> str:
        path = path or self.source()
        target = self.repo / path
        target.write_text(target.read_text() + f"\n# edited {len(target.read_text())}\n")
        return path

    def resync(self) -> None:
        """The index follows the tree, in place — the way CodeGraph's own watcher writes it, not a new file."""
        with sqlite3.connect(self.database) as connection:
            for path in self.rows():
                digest = hashlib.sha256((self.repo / path).read_bytes()).hexdigest()
                connection.execute("UPDATE files SET content_hash = ? WHERE path = ?", (digest, path))

    def commit(self, message: str = "change") -> None:
        commit_all(self.repo, message)

    def remembered(self) -> bytes | None:
        return self.memory.read_bytes() if self.memory.exists() else None


class WholeRunIsTodaysTest(FactoryTestCase):
    """R6: every example is a hold — green before the narrowing exists, and it must stay green after."""

    def test_hold_the_trunk_prints_todays_line_and_opens_every_indexed_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            audited = project.audited()
            self.assertEqual(audited.result.returncode, 0, audited.result.stderr)
            self.assertRegex(audited.result.stdout, CURRENT)
            self.assertEqual(set(project.rows()) - set(audited.opened), set(), "every indexed file was hashed")

    def test_hold_in_ci_on_a_slice_branch_the_run_is_whole_and_leaves_the_memory_alone(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            today = project.whole().stdout
            project.slice()
            for marker in CI_MARKERS:
                before = project.remembered()
                audited = project.audited(**{marker: "true"})
                self.assertEqual(audited.result.stdout, today, marker)
                self.assertEqual(set(project.rows()) - set(audited.opened), set(), marker)
                self.assertEqual(project.remembered(), before, f"{marker}: the memory is neither read nor written")

    def test_hold_another_branch_and_a_detached_head_are_whole(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            today = project.whole().stdout
            project.git("checkout", "-q", "-b", "feature/x")
            self.assertEqual(project.run().stdout, today)
            project.git("checkout", "-q", "--detach")
            self.assertEqual(project.run().stdout, today)

    def test_hold_a_corrupt_database_is_rebuilt_or_failed_as_today_off_the_narrowed_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.whole()
            garbage = b"garbage " * 1000
            for where, extra in (("main", {}), ("slice/S1", {"CI": "true"})):
                project.git("checkout", "-q", *(["-B", where] if where != "main" else [where]))
                project.database.write_bytes(garbage)
                rebuilt = project.run(**extra)
                self.assertEqual(rebuilt.returncode, 0, rebuilt.stderr)
                self.assertRegex(rebuilt.stdout, r"^check-codegraph: rebuilt a corrupt database first \([\d.]+s\); "
                                 r"index current")
                project.database.write_bytes(garbage)
                refused = project.run(CODEGRAPH_GATE_NO_SYNC="1", **extra)
                self.assertEqual(refused.returncode, 1)
                self.assertIn("fails SQLite's integrity check", refused.stderr)
