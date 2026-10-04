"""R4 of S05-xdist: what exists keeps its answer — a replay, a `migrate` and an `add-service` carry the project's
own `parallelSafe` (the JSON value as written, or nothing where there is no key), and `adopt` writes none.

A project "made before this release" is a generated project with the key removed and the root commit amended, so
it is the base the next merge measures against. A missing mark is serial, and no tool adds one (D102).
"""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from support import FactoryTestCase, commit_all
from test_add_service import add_service
from test_adopted_manifest import apps
from test_candidates import adopted, record
from test_migrate import migrate
from test_replay import git, newer_factory, replay

from slipwai.assets import ROOT
from slipwai.manifest import recorded_parallel_safe
from slipwai.scaffold import NO_MAINTENANCE, project_files

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


def project_json(parallel_safe: object) -> str:
    """`project.json` as a regeneration with the recorded mark writes it."""
    return project_files("brown", "event-modelling", "none", apps(), parallel_safe=parallel_safe)["project.json"]


MARKS = {"made before (no key)": ..., "false": False, "true": True}
# T016: whatever JSON value the project wrote is its own, and a tool never deletes or rewrites it.
ODD_MARKS = {"yes": "yes", "one": 1, "string true": "true", "null": None, "empty list": []}


def mark_later(repo: Path, value: object, after: str = "target") -> None:
    """Add the key in a commit after the root, as the catch-up tells a person to: right after `after`."""
    current = document(repo)
    current.pop(KEY, None)
    placed: dict = {}
    for name, held in current.items():
        placed[name] = held
        if name == after:
            placed[KEY] = value
    (repo / "project.json").write_text(json.dumps(placed, indent=2) + "\n", encoding="utf-8")
    commit_all(repo, "add the mark")


def lines_of_key(repo: Path) -> int:
    return (repo / "project.json").read_text(encoding="utf-8").count(f'"{KEY}"')


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


class TheLineTheCatchUpTellsAPersonToAddComesOutOnce(FactoryTestCase):
    """T014: a mark added in a commit after the root, where `generate` writes it, meets the same line from the
    factory and merges to one key with the person's value."""

    def test_a_mark_added_later_after_target_survives_migrate_as_one_key(self) -> None:
        for value in (True, False):
            with self.subTest(mark=value), tempfile.TemporaryDirectory() as directory:
                repo = self.generate(directory, "shop", "event-modelling", "python")
                own_mark(repo, ...)
                mark_later(repo, value)
                factory = newer_factory(Path(directory), "\n## A section a newer factory added\n")

                result = migrate(repo, factory)

                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(lines_of_key(repo), 1)
                self.assertIs(document(repo)[KEY], value)

    def test_an_edit_in_place_after_a_migrate_survives_the_next_one(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "shop", "event-modelling", "python")
            own_mark(repo, ...)
            mark_later(repo, True)
            self.assertEqual(migrate(repo, newer_factory(Path(directory), "\n## One\n")).returncode, 0)
            text = (repo / "project.json").read_text(encoding="utf-8")
            (repo / "project.json").write_text(text.replace(f'"{KEY}": true', f'"{KEY}": false'), encoding="utf-8")
            commit_all(repo, "turn it off")
            other = Path(directory) / "other"
            other.mkdir()

            result = migrate(repo, newer_factory(other, "\n## Two\n"))

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(lines_of_key(repo), 1)
            self.assertIs(document(repo)[KEY], False)


class AMarkThatIsNotABooleanIsCarriedAsWritten(FactoryTestCase):
    """T016: replay carries the project's own JSON value, in the base or added later, and never deletes it."""

    def test_a_replay_writes_the_value_as_written(self) -> None:
        for label, mark in ODD_MARKS.items():
            with self.subTest(mark=label), tempfile.TemporaryDirectory() as directory:
                repo = self.generate(directory, "shop", "event-modelling", "python")
                own_mark(repo, mark)
                twin = Path(directory) / "twin"

                self.assertEqual(replay(repo, ROOT, "--into", str(twin)).returncode, 0)

                self.assertEqual(document(twin).get(KEY, "missing"), mark)

    def test_migrate_keeps_it_whether_it_was_in_the_base_or_added_later(self) -> None:
        for label, mark in ODD_MARKS.items():
            for where in ("base", "later"):
                with self.subTest(mark=label, where=where), tempfile.TemporaryDirectory() as directory:
                    repo = self.generate(directory, "shop", "event-modelling", "python")
                    own_mark(repo, mark if where == "base" else ...)
                    if where == "later":
                        mark_later(repo, mark)
                    factory = newer_factory(Path(directory), "\n## A section a newer factory added\n")

                    result = migrate(repo, factory)

                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertEqual(lines_of_key(repo), 1)
                    self.assertEqual(document(repo).get(KEY, "missing"), mark)

    def test_add_service_keeps_it(self) -> None:
        for label, mark in ODD_MARKS.items():
            with self.subTest(mark=label), tempfile.TemporaryDirectory() as directory:
                repo = self.generate(directory, "shop", "event-modelling", "python")
                own_mark(repo, mark)

                self.assertEqual(add_service(repo, "payments").returncode, 0)

                self.assertEqual(document(repo).get(KEY, "missing"), mark)

    def test_the_before_and_after_pairs_of_converge_and_resurvey_carry_it_too(self) -> None:
        """Both take `recorded_parallel_safe(document)` into `project_files`, so the pair shows no difference."""
        for label, mark in ODD_MARKS.items():
            with self.subTest(mark=label):
                held = recorded_parallel_safe({KEY: mark})
                self.assertEqual(json.loads(project_json(held)).get(KEY, "missing"), mark)
        self.assertEqual(json.loads(project_json(recorded_parallel_safe({}))).get(KEY, "missing"), "missing")
