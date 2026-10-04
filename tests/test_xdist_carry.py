"""R4 of S05-xdist: what exists keeps its answer — a replay, a `migrate` and an `add-service` carry the project's
own `parallelSafe` (a boolean as written, or nothing where there is no key), and `adopt` writes none.

A project "made before this release" is a generated project with the key removed and the root commit amended, so
it is the base the next merge measures against. A missing mark is serial, and no tool adds one (D102).
"""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from support import FactoryTestCase
from test_add_service import add_service
from test_candidates import adopted, record
from test_migrate import migrate
from test_replay import git, newer_factory, replay

from slipwai.assets import ROOT
from slipwai.scaffold import NO_MAINTENANCE

KEY = "parallelSafe"


def document(repo: Path) -> dict:
    return json.loads((repo / "project.json").read_text(encoding="utf-8"))


def own_mark(repo: Path, value: object) -> None:
    """Make the project's `project.json` say `value` (`...` for no key) and amend the root commit to it."""
    current = document(repo)
    current.pop(KEY, None)
    if value is not ...:
        current[KEY] = value
    (repo / "project.json").write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
    git(repo, "add", "project.json")
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@local", *NO_MAINTENANCE, "commit", "-q", "--amend",
         "--no-edit"], cwd=repo, check=True,
    )


MARKS = {"made before (no key)": ..., "false": False, "true": True}


class ReplayAndMigrateCarryTheProjectsOwnMark(FactoryTestCase):
    def test_a_replay_writes_the_projects_own_mark_or_none(self) -> None:
        for label, mark in MARKS.items():
            with self.subTest(mark=label), tempfile.TemporaryDirectory() as directory:
                repo = self.generate(directory, "shop", "event-modelling", "python")
                own_mark(repo, mark)
                twin = Path(directory) / "twin"

                result = replay(repo, ROOT, "--into", str(twin))

                self.assertEqual(result.returncode, 0, result.stderr)
                if mark is ...:
                    self.assertNotIn(KEY, document(twin))
                else:
                    self.assertIs(document(twin).get(KEY, "missing"), mark)

    def test_migrate_carries_the_mark_the_project_has_and_never_adds_one(self) -> None:
        for label, mark in MARKS.items():
            with self.subTest(mark=label), tempfile.TemporaryDirectory() as directory:
                repo = self.generate(directory, "shop", "event-modelling", "python")
                own_mark(repo, mark)
                factory = newer_factory(Path(directory), "\n## A section a newer factory added\n")

                result = migrate(repo, factory)

                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(git(repo, "status", "--porcelain").stdout, "")
                if mark is ...:
                    self.assertNotIn(KEY, document(repo))
                else:
                    self.assertIs(document(repo).get(KEY, "missing"), mark)


class AddServiceKeepsItsAnswer(FactoryTestCase):
    def test_add_service_keeps_false_and_adds_no_key_where_there_is_none(self) -> None:
        """A hold: `add-service` writes the entry into the project's own document, so the mark rides along."""
        for label, mark in MARKS.items():
            with self.subTest(mark=label), tempfile.TemporaryDirectory() as directory:
                repo = self.generate(directory, "shop", "event-modelling", "python")
                own_mark(repo, mark)

                result = add_service(repo, "payments")

                self.assertEqual(result.returncode, 0, result.stderr)
                if mark is ...:
                    self.assertNotIn(KEY, document(repo))
                else:
                    self.assertIs(document(repo).get(KEY, "missing"), mark)
                self.assertIn("payments", document(repo)["deployables"])


class AdoptWritesNone(FactoryTestCase):
    def test_adopt_and_its_refresh_record_no_mark_and_leave_every_command_as_recorded(self) -> None:
        """A hold: an adopted repository's applications are the project's own, and nothing here is parallel."""
        with tempfile.TemporaryDirectory() as directory:
            repo = adopted(Path(directory))
            self.assertNotIn(KEY, record(repo))
            before = record(repo)["deployables"]

            result = subprocess.run(
                [str(ROOT / "slipwai"), "adopt", "--refresh"],
                cwd=repo, text=True, capture_output=True, stdin=subprocess.DEVNULL,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn(KEY, record(repo))
            self.assertEqual(record(repo)["deployables"], before)
