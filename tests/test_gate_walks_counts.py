"""A count or a finding is asserted on a tree that reaches the code (S01-gate-walks, T024 and T025).

`under()` reuses an earlier listing only on a tree with a browser app or a service holding several contexts, and a
pass line is only the sum D47 defines if every directory is listed once. So the counts here are taken on those
trees, exactly, and the findings with the four pruned directories planted beside them are the pinned bytes.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

from gate_audit import Audited
from support import FactoryTestCase, commit_all
from test_gate_walks import GATES, IMPORTS_LINE, MIGRATIONS_LINE, entries, reported, run_gate
from test_gate_walks_pinned import (
    IMPORT_FINDINGS,
    MIGRATION_FINDINGS,
    plant_import_violations,
    plant_migration_violations,
)


def plant_pruned(repo: Path) -> None:
    """The four directories nobody reads, with a violation inside each, beside every kind of code."""
    for under in ("apps/service", "apps/service/src/domain", "apps/service/migrations", "apps/web", "apps/web/src"):
        base = repo / under
        (base / ".venv/lib/domain").mkdir(parents=True)
        (base / ".venv/lib/domain/bad.py").write_text("from ..adapters.store import save\n")
        (base / "node_modules/pkg/application").mkdir(parents=True)
        (base / "node_modules/pkg/application/bad.py").write_text("from ..composition.x import y\n")
        (base / "node_modules/pkg/src").mkdir(parents=True, exist_ok=True)
        (base / "node_modules/pkg/src/x.ts").write_text("import { y } from '../../../../service/src/domain/z';\n")
        (base / "node_modules/pkg/migrations").mkdir(parents=True, exist_ok=True)
        (base / "node_modules/pkg/migrations/0001_drop.sql").write_text("DROP TABLE events;\n")
        (base / "__pycache__").mkdir()
        (base / "__pycache__/x.py").write_text("x = 1\n")
        (base / ".git/hooks").mkdir(parents=True)
        (base / ".git/hooks/x").write_text("")


class CountOnATreeThatReachesTheCodeTest(FactoryTestCase):
    def test_a_project_with_a_browser_app_counts_exactly_what_it_lists(self) -> None:
        """T024: the reference skeleton (Python, `react-vite`) — `under()` is called for the web app."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "counted-web", "event-modelling", "python", frontend="react-vite")
            for script, line in GATES.items():
                with self.subTest(script=script):
                    self.assertEqual(reported(run_gate(repo, script), line), entries(repo))

    def test_a_service_with_two_contexts_counts_exactly_what_it_lists(self) -> None:
        """T024: `under()` is called for the service as well as for the web app."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "counted-contexts", "event-modelling", "python", frontend="react-vite")
            manifest = json.loads((repo / "project.json").read_text())
            manifest["deployables"]["service"]["contexts"] = ["orders", "billing"]
            (repo / "project.json").write_text(json.dumps(manifest, indent=2) + "\n")
            self.assertEqual(reported(run_gate(repo, "scripts/check-imports.py"), IMPORTS_LINE), entries(repo))

    def test_pruned_directories_planted_beside_violations_leave_the_findings_byte_for_byte(self) -> None:
        """T024: the four names planted beside the pinned violations — the pinned stderr, exit 1, empty stdout."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "counted-pinned", "event-modelling", "python", frontend="react-vite")
            plant_import_violations(repo)
            plant_migration_violations(repo)
            plant_pruned(repo)
            for script, findings in (("scripts/check-imports.py", IMPORT_FINDINGS),
                                     ("scripts/check-migrations.py", MIGRATION_FINDINGS)):
                with self.subTest(script=script):
                    result = subprocess.run(["python3", script], cwd=repo, text=True, capture_output=True)
                    self.assertEqual((result.returncode, result.stdout), (1, ""))
                    self.assertEqual(result.stderr, findings)


class EachDirectoryIsListedOnceTest(FactoryTestCase):
    """T025: under the audit hook, `check-migrations` lists no directory twice, and its count is the names the
    listings returned — on the reference skeleton, with a marked contraction, and on a Go project."""

    def assert_listed_once_and_counted(self, repo: Path) -> None:
        audited = Audited(repo, "scripts/check-migrations.py")
        self.assertEqual(audited.result.returncode, 0, audited.result.stderr)
        self.assertEqual(sorted(set(audited.listed)), sorted(audited.listed), "a directory was listed twice")
        names = sum(len(os.listdir(repo / path)) for path in audited.listed)
        self.assertEqual(reported(audited.result, MIGRATIONS_LINE), names)

    def test_the_reference_skeleton(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "once-web", "event-modelling", "python", frontend="react-vite")
            self.assert_listed_once_and_counted(repo)

    def test_a_marked_contraction(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "once-contract", "event-modelling", "python", frontend="react-vite")
            migrations = repo / "apps/service/migrations"
            (migrations / "001_add_status.sql").write_text("ALTER TABLE events ADD COLUMN status text;\n")
            commit_all(repo, "expand")
            (migrations / "002_drop_state.sql").write_text(
                "-- contract: 001_add_status\nALTER TABLE events DROP COLUMN state;\n")
            self.assert_listed_once_and_counted(repo)

    def test_a_go_project(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "once-go", language="go", target="aws", event_store="postgres",
                                 http="net-http", auth="none")
            self.assert_listed_once_and_counted(repo)
            (repo / "apps/service/migrations/0001_init.sql").write_text("CREATE TABLE events (id int);\n")
            self.assert_listed_once_and_counted(repo)
