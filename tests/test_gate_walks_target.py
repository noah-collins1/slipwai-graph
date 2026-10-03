"""`target` is Maven's build output only at a recorded Java root, beside its `pom.xml` (S01-gate-walks, R3, D52).

A Java service's `target/` holds compiled copies of its own sources, which the gates must not read twice. A
directory called `target` anywhere else is somebody's source: a bounded context, a package, a folder of migrations.
The examples after the first are holds, green before the change and after it, written to stop it widening into
"skip every `target`".
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from support import FactoryTestCase
from test_gate_walks import GATES, reported, run_gate


class GateWalkTargetTest(FactoryTestCase):
    def two_contexts(self, directory: str) -> Path:
        """A Python service recording the contexts `orders` and `target`."""
        repo = self.generate(directory, "contexts", "event-modelling", "python")
        manifest = json.loads((repo / "project.json").read_text())
        manifest["deployables"]["service"]["contexts"] = ["orders", "target"]
        (repo / "project.json").write_text(json.dumps(manifest, indent=2) + "\n")
        return repo

    def test_maven_output_beside_a_pom_is_not_read(self) -> None:
        """R3e1: a migration and a domain file under `target/` are neither read nor reported; the dir is one entry."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "java", "event-modelling", "java-quarkus")
            self.assertTrue((repo / "apps/service/pom.xml").is_file())
            before = {script: reported(run_gate(repo, script), line) for script, line in GATES.items()}
            build = repo / "apps/service/target"
            (build / "classes/db/migration").mkdir(parents=True)
            (build / "classes/db/migration/V2__drop.sql").write_text("DROP TABLE events;\n")
            (build / "generated-sources/domain").mkdir(parents=True)
            (build / "generated-sources/domain/Bad.java").write_text("import jakarta.inject.Inject;\n")
            for script, line in GATES.items():
                with self.subTest(script=script):
                    self.assertEqual(reported(run_gate(repo, script), line), before[script] + 1)

    def test_hold_a_context_called_target_is_still_read(self) -> None:
        """R3e2, a hold: no `pom.xml` beside it, so a domain file there is held to rule 1."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.two_contexts(directory)
            domain = repo / "apps/service/src/target/domain"
            domain.mkdir(parents=True)
            (domain / "bad.py").write_text("from ..adapters.store import save\n")
            result = run_gate(repo, "scripts/check-imports.py")
            self.assertEqual(result.returncode, 1)
            self.assertIn("apps/service/src/target/domain/bad.py:1: domain imports an outer layer", result.stderr)

    def test_hold_a_context_called_target_is_still_held_to_rule_5(self) -> None:
        """R3e3, a hold: a file under `src/target/` reaching into `orders` is a context seam finding."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.two_contexts(directory)
            (repo / "apps/service/src/target").mkdir()
            (repo / "apps/service/src/target/handler.py").write_text("from orders.domain import Order\n")
            result = run_gate(repo, "scripts/check-imports.py")
            self.assertEqual(result.returncode, 1)
            self.assertIn("apps/service/src/target/handler.py:1: target reaches into orders", result.stderr)

    def test_hold_migrations_under_a_directory_called_target_are_still_read(self) -> None:
        """R3e4, a hold."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.two_contexts(directory)
            migrations = repo / "apps/service/src/target/migrations"
            migrations.mkdir(parents=True)
            (migrations / "0002_drop.sql").write_text("DROP TABLE events;\n")
            result = run_gate(repo, "scripts/check-migrations.py")
            self.assertEqual(result.returncode, 1)
            self.assertIn("apps/service/src/target/migrations/0002_drop.sql: drops a table", result.stderr)

    def test_hold_a_java_package_called_target_beside_no_pom_is_still_read(self) -> None:
        """R3e5, a hold: the `pom.xml` is in `apps/service`, not beside this `target`."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "java", "event-modelling", "java-quarkus")
            package = repo / "apps/service/src/main/java/com/example/domain/target"
            package.mkdir(parents=True)
            (package / "Bad.java").write_text("package com.example.domain.target;\nimport jakarta.inject.Inject;\n")
            result = run_gate(repo, "scripts/check-imports.py")
            self.assertEqual(result.returncode, 1)
            self.assertIn("Bad.java:2: domain imports a framework or driver package: jakarta.inject", result.stderr)
