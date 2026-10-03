"""The gate's own record is trustworthy (S01-gate-walks, T032 and T033: the adversary's F1, F2 and F3).

T032: one comparison judges, and the record keeps, one read of the index's rows. A `git` wrapper first on `PATH`
rewrites a row's hash at the moment the gate asks `git diff`, which is between the two reads a narrowed run used to
make. T033: the record is written through a file the gate creates for itself, never through a path already there.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

from support import FactoryTestCase
from test_codegraph_narrowed import Project

FAKE = "0" * 64
WRAPPER = """#!{python}
import os, sqlite3, sys
args = sys.argv[1:]
here = os.path.dirname(os.path.abspath(__file__))
marker = os.path.join(here, "rewritten")
log = os.environ["FAKE_CODEGRAPH_LOG"]
after_sync = os.path.exists(log) and "sync" in open(log).read()
if args[:1] == ["diff"] and not os.path.exists(marker) and (after_sync or not {when_synced}):
    open(marker, "w").close()
    with sqlite3.connect(".codegraph/codegraph.db") as connection:
        connection.execute("UPDATE files SET content_hash = ? WHERE path = ?", ({fake!r}, {path!r}))
os.execv({git!r}, [{git!r}, *args])
"""


def rewriting(project: Project, directory: str, path: str, when_synced: bool = False) -> dict[str, str]:
    """A `git` first on the PATH that rewrites `path`'s row in the index the first time the gate runs `git diff`
    (the first one after a sync, where `when_synced`)."""
    wrapper = Path(directory) / "wrapper"
    wrapper.mkdir()
    (wrapper / "git").write_text(WRAPPER.format(python=sys.executable, git=shutil.which("git"), fake=FAKE,
                                                path=path, when_synced=when_synced))
    (wrapper / "git").chmod(0o755)
    return {"PATH": f"{wrapper}:{project.tools['PATH']}"}


def sources(project: Project) -> list[str]:
    return [path for path in project.rows() if not path.startswith("scripts/")]


class OneReadOfTheRowsTest(FactoryTestCase):
    """T032 (F1): a row that changes while a narrowed run reads is judged as the whole run judges it."""

    def test_a_row_rewritten_between_the_reads_fails_and_is_not_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.whole()
            project.slice()
            moved = sources(project)[0]
            env = rewriting(project, directory, moved)
            failed = project.run(CODEGRAPH_GATE_NO_SYNC="1", **env)
            self.assertEqual(failed.returncode, 1, f"narrowed passed where the whole run fails: {failed.stdout}")
            self.assertIn(f"- {moved}", failed.stderr)
            kept = project.remembered()
            self.assertTrue(kept is None or FAKE not in kept.decode(), "the record holds a hash nobody verified")
            again = project.run(CODEGRAPH_GATE_NO_SYNC="1")
            self.assertEqual(again.returncode, 1, "a later run passes on the rewritten row")

    def test_a_row_rewritten_after_a_sync_is_judged_by_the_comparison_after_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.in_place()
            project.whole()
            project.slice()
            first, second = sources(project)[:2]
            project.edit(first)
            env = rewriting(project, directory, second, when_synced=True)
            failed = project.run(**env)
            self.assertEqual(failed.returncode, 1, f"the comparison after the sync passed: {failed.stdout}")
            self.assertIn(f"- {second}", failed.stderr)
            kept = project.remembered()
            self.assertTrue(kept is None or FAKE not in kept.decode())
