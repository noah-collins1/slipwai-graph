"""The adopted-repository rules at a root deployable: the repository's own migration names and layout (D21).

At the root deployable of an adopted repository a new migration carries the name the repository's own tool
wrote, and the events rule holds only where the record says `"layout": "hexagonal"`. Both refusals stay for
a deployable under a subdirectory and for the host's own paths. The fixtures are `test_slice_scope_root`'s.
"""
from __future__ import annotations

from pathlib import Path

from test_slice_scope_root import SliceScopeFixtures, git


class SliceScopeAdoptedRulesTest(SliceScopeFixtures):
    ROOT_MIGRATIONS = ("shop/migrations/0002_add_field.py", "db/migrations/20261003120000_add.js")
    SHIPPED = {"db/migrations/0001_init.py": "a\n", "domain/events.py": "a\nb\n"}

    def test_a_new_migration_at_the_root_carries_the_repositorys_own_name(self) -> None:
        """T013 (AC-S20-17, D21): Django's numbering and a 14-digit stamp are green under the root deployable."""
        self.green(self.repo(self.root()), *self.ROOT_MIGRATIONS)

    def test_an_existing_migration_at_the_root_is_still_refused_without_a_stamp_in_the_message(self) -> None:
        """T013 (AC-S20-17, D21): an edit is refused and says to add a new one with the repository's own tool."""
        result = self.verdict(self.repo(self.root(), existing=self.SHIPPED), "db/migrations/0001_init.py")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("existing migration was edited", result.stderr)
        self.assertIn("repository's own tool", result.stderr)
        self.assertNotIn("timestamped", result.stderr)

    def test_the_events_rule_holds_at_the_root_only_where_the_record_says_hexagonal(self) -> None:
        """T013 (AC-S20-18, D21): a removed events line is green with no `layout`, refused with `hexagonal`."""
        self.green(self.repo(self.root(), existing=self.SHIPPED), "domain/events.py")
        record = {"shop": {"kind": "service", "path": ".", "layout": "hexagonal"}}
        result = self.verdict(self.repo(record, existing=self.SHIPPED), "domain/events.py")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("the events module is the contract", result.stderr)

    def test_a_deployable_under_a_subdirectory_keeps_both_rules(self) -> None:
        """T013 (AC-S20-19, D21), held: recorded `generated: false` or generated under `apps/`, beside a root one."""
        for record in ({"kind": "service", "path": "legacy", "generated": False},
                       {"kind": "service", "path": "legacy"}):
            with self.subTest(record=record):
                shipped = {"legacy/domain/events.py": "a\nb\n", "legacy/db/migrations/0001_x.py": "a\n"}
                repo = self.repo({**self.root(), "legacy": record}, existing=shipped)
                for path in ("legacy/db/migrations/0002_add_field.py", "legacy/migrations/20261003120000_add.js"):
                    result = self.verdict(repo, path)
                    self.assertNotEqual(result.returncode, 0, path)
                    self.assertIn("timestamped", result.stderr, path)
                result = self.verdict(repo, "legacy/domain/events.py")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("the events module is the contract", result.stderr)
                result = self.verdict(repo, "legacy/db/migrations/0001_x.py")
                self.assertIn("existing migration was edited", result.stderr)

    def test_a_migration_shaped_path_on_the_host_surface_is_still_refused(self) -> None:
        """T013 (AC-S20-19, D21), held: the host's paths are not opened by the migration answer."""
        repo = self.repo(self.root())
        for path in (".github/migrations/0002_x.sql", "delivery/migrations/0002_x.sql", ".claude/migration/0002_x.py"):
            with self.subTest(path=path):
                self.assertNotEqual(self.verdict(repo, path).returncode, 0)

    def quiet(self, repo: Path, path: str = "tests/test_x.py") -> None:
        """The gate answers green on a path the slice owns, and no input ends it on a traceback."""
        result = self.verdict(repo, path)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_a_written_ledger_that_is_not_utf8_adds_nothing(self) -> None:
        """T014 (D22, AC-S20-19): the host surface reads `.written` tolerantly; the fixed names still answer."""
        repo = self.repo(self.root(), written=b"\xff\xfe\x00lib/x.py\n")
        self.quiet(repo)
        self.refused(repo, "project.json")

    def test_a_registry_nested_past_the_recursion_limit_adds_nothing(self) -> None:
        """T014 (D22, AC-S20-19): the registry is read tolerantly, and a pathological one is no harness row."""
        repo = self.repo(self.root(), registry="[" * 200000)
        self.quiet(repo)
        self.refused(repo, "project.json")

    def test_a_project_record_nested_past_the_recursion_limit_owns_nothing(self) -> None:
        """T014 (D22): `project.json` that cannot be parsed has no deployables, so nothing is the slice's."""
        repo = self.repo(self.root())
        (repo / "project.json").write_text("[" * 200000)
        git(repo, "commit", "-qam", "nested")
        result = self.verdict(repo, "tests/test_x.py")
        self.assertNotIn("Traceback", result.stderr)

    def test_a_model_that_is_not_utf8_is_no_model(self) -> None:
        """T014 (D22): an undecodable `model.yaml` names no slice, and the gate still answers."""
        self.quiet(self.repo(self.root(), existing={"delivery/docs/event-model/model.yaml": b"\xff\xfe"}))

    def test_a_written_line_with_trailing_whitespace_names_its_path(self) -> None:
        """T014 (D22, G5): `lib/generated.py  ` and a CRLF line are the paths they name."""
        repo = self.repo(self.root(), written="lib/generated.py  \nlib/other.py\r\n")
        self.refused(repo, "lib/generated.py", "lib/other.py")
        self.green(repo, "lib/own.py")
