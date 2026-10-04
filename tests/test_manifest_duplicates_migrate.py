"""D107 (T023) for `migrate`: refuses a `project.json` that already writes a key twice, and after a clean merge says
so when the merge made one — the line, the catch-up sentence, exit 0, the merge kept (T018)."""
from __future__ import annotations

import tempfile
from pathlib import Path

from support import FactoryTestCase
from test_manifest_duplicates import KEY, Untouched, after_name, gate_reads_serial
from test_migrate import migrate
from test_replay import git, newer_factory
from test_xdist_carry import lines_of_key, mark_later, own_mark

from slipwai.assets import NOTES

CHANGE = "\n## A section a newer factory added\n"


def old_project(test: FactoryTestCase, directory: str) -> Path:
    """A project made before this slice: no mark in the root commit, so the next replay measures against that."""
    repo = test.generate(directory, "shop", "event-modelling", "python")
    own_mark(repo, ...)
    return repo


class MigrateRefusesBeforeTheReplay(FactoryTestCase):
    def test_a_file_that_already_writes_a_key_twice_is_refused_and_nothing_merges(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = old_project(self, directory)
            after_name(repo, f'  "{KEY}": false,')
            after_name(repo, f'  "{KEY}": true,')
            untouched = Untouched(self, repo)

            result = migrate(repo, newer_factory(Path(directory), CHANGE))

            untouched.check(result)
            self.assertFalse((repo / NOTES).exists())


class MigrateSaysWhenItsMergeMadeAKeyTwice(FactoryTestCase):
    def say(self, where: str) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = old_project(self, directory)
            mark_later(repo, False, after=where)

            result = migrate(repo, newer_factory(Path(directory), CHANGE))

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(lines_of_key(repo), 2)
            said = [line for line in result.stdout.splitlines() if 'project.json has "parallelSafe" twice' in line]
            self.assertEqual(len(said), 1, result.stdout)
            self.assertIn("serial", said[0])
            self.assertIn("keep one copy", said[0])
            self.assertIn(said[0], (repo / NOTES).read_text(encoding="utf-8"))
            self.assertTrue(gate_reads_serial(repo))
            self.assertEqual(git(repo, "status", "--porcelain").stdout, "")

    def test_a_mark_added_after_name(self) -> None:
        self.say("name")

    def test_a_mark_added_at_the_end(self) -> None:
        self.say("deployables")

    def test_a_mark_added_after_target_is_one_key_and_no_line(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = old_project(self, directory)
            mark_later(repo, False, after="target")

            result = migrate(repo, newer_factory(Path(directory), CHANGE))

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(lines_of_key(repo), 1)
            self.assertNotIn("twice", result.stdout)
            self.assertNotIn("twice", (repo / NOTES).read_text(encoding="utf-8"))
